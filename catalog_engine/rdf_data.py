import uuid
import json
from decimal import Decimal
from rdflib import URIRef, Namespace, Literal
from rdflib.namespace import RDF, RDFS, SKOS

SCH = Namespace('http://schema.org/')

class DataCoder(object):
    def __init__(self, schema, graph, base_uri):
        self.schema = schema
        self.graph = graph
        self.base_uri = base_uri
        self.class_uri = {}
        for sk in sorted(schema.keys()):
            self.class_uri[schema[sk]['uri']] = sk

    def encode_rdf(self, obj, obj_uri=None):
        if 'uuid' not in obj:
            data = obj.copy()
            data['uuid'] = str(uuid.uuid4())
        else:
            data = obj
        if obj_uri is None:
            obj_uri = URIRef(self.base_uri + '#' + data['uuid'])
        self._build_resource(data, data['type'], obj_uri)
        return obj_uri, data['uuid']

    # TODO: caching
    def _get_all_properties(self, rsrc_type):
        rsrc_def = self.schema[rsrc_type]
        #print(rsrc_type, rsrc_def)
        if 'extends' in rsrc_def and rsrc_def['extends'] != 'IObject':
            all_props = self._get_all_properties(rsrc_def['extends'])
        else:
            all_props = {}
        for k in rsrc_def['properties'].keys():
            all_props[k] = rsrc_def['properties'][k]
        return all_props

    # TODO: caching
    def _get_all_property_uris(self, rsrc_type):
        rsrc_def = self.schema[rsrc_type]
        if 'extends' in rsrc_def and rsrc_def['extends'] != 'IObject':
            all_props = self._get_all_property_uris(rsrc_def['extends'])
        else:
            all_props = {}
        for k in rsrc_def['propertyUris'].keys():
            all_props[k] = rsrc_def['propertyUris'][k]
        return all_props

    def _is_literal(self, val_type):
        return val_type == 'string' or val_type == 'number' or val_type == 'boolean' or val_type == 'Date'

    def _build_literal(self, rsrc, prop, val_type, k, dval):
        gr = self.graph
        if val_type == 'string' or val_type == 'number' or val_type == 'boolean':
            if k == 'uuid':
                gr.add( (rsrc, prop, URIRef('urn:uuid:' + str(dval).lower())) )
            elif isinstance(dval, Decimal):
                gr.add( (rsrc, prop, Literal(str(dval))) )
            else:
                gr.add( (rsrc, prop, Literal(dval)) )
        elif val_type == 'Date':
            gr.add( (rsrc, prop, Literal(dval)) )

    def _build_object(self, propSpec, dval):
        gr = self.graph
        if 'id' in dval:
            item_uri = URIRef(dval['id'])
        else:
            item_uri = URIRef(self.base_uri + '#' + str(uuid.uuid4()))
        sub_type = propSpec['type']
        if 'isMultiType' in propSpec and propSpec['isMultiType']:
            if 'type' not in dval:
                raise Exception(f"Unable to determine object type from {sub_type} without 'type'")
            sub_type = dval['type']
        self._build_resource(dval, sub_type, item_uri)
        return item_uri

    def _build_resource(self, obj, rsrc_type, rsrc_uri):
        rsrc_def = self.schema[rsrc_type]
        gr = self.graph
        rsrc = URIRef(rsrc_uri)
        gr.add( (rsrc, RDF['type'], URIRef(rsrc_def['uri'])) )
        all_props = self._get_all_properties(rsrc_type)
        for k in all_props.keys():
            val = all_props[k]
            if 'isOptional' in val and val['isOptional']:
                if k not in obj:
                    continue
            dval = obj[k]
            lit = self._is_literal(val['type'])
            if 'isArray' in val and len(dval) > 1:
                item_list = URIRef(self.base_uri + '#' + str(uuid.uuid4()))
                gr.add( (item_list, RDF['type'], SCH['ItemList']) )
                gr.add( (rsrc, URIRef(val['uri']), item_list) )
                for i in range(len(dval)):
                    item_uri = URIRef(self.base_uri + '#' + str(uuid.uuid4()))
                    gr.add( (item_list, SCH['itemListElement'], item_uri) )
                    gr.add( (item_uri, SCH['position'], Literal(i)) )
                    if lit:
                        self._build_literal(item_uri, SCH['item'], val['type'], k, dval[i])
                    else:
                        sub_item = self._build_object(val, dval[i])
                        gr.add( (item_uri, SCH['item'], sub_item) )
            else:
                if 'isArray' in val:
                    dval = dval[0]
                if lit:
                    self._build_literal(rsrc, URIRef(val['uri']), val['type'], k, dval)
                else:
                    sub_item = self._build_object(val, dval)
                    gr.add( (rsrc, URIRef(val['uri']), sub_item) )

    def decode_rdf(self, uri):
        return self._decode_resource(uri)

    def _is_itemlist(self, obj):
        if isinstance(obj, URIRef):
            gr = self.graph
            if (obj, RDF['type'], SCH['ItemList']) in gr:
                return True
        return False

    def _decode_literal(self, prop_type, prop_key, value):
        if prop_type == 'string':
            if prop_key == 'uuid':
                return uuid.UUID(str(value)[9:])
            return str(value)
        elif prop_type == 'Date':
            return value.toPython()
        elif prop_type == 'number':
            return Decimal(str(value))
        elif prop_type == 'boolean':
            return value.toPython()
        raise Exception(f'Invalid property type: {prop_type}')

    def _decode_array(self, node_uri, lit, prop_type, prop_key):
        gr = self.graph
        vals = gr.objects(node_uri, SCH['itemListElement'])
        output = []
        for list_item in vals:
            pos = int(gr.value(list_item, SCH['position']))
            item = gr.value(list_item, SCH['item'])
            output.append([pos, item])
        output_sorted = sorted(output, key=lambda rc: rc[0])
        output_final = []
        for r in output_sorted:
            if lit:
                output_final.append(self._decode_literal(prop_type, prop_key, r[1]))
            else:
                output_final.append(self._decode_resource(r[1]))
        return output_final

    def _decode_resource(self, node_uri, specify_type=''):
        gr = self.graph
        if isinstance(node_uri, URIRef):
            node = node_uri
        else:
            node = URIRef(node_uri)
        node_id = str(node)
        item = {'id': node_id, 'type': ''}
        types = gr.objects(node, RDF['type'])
        for ty in types:
            tys = str(ty)
            if tys in self.class_uri:
                item['type'] = self.schema[self.class_uri[tys]]['name']
        if len(item['type']) == 0:
            if specify_type != '':
                item['type'] = specify_type
            else:
                # Warning: unknown type
                return {}
        all_props = self._get_all_properties(item['type'])
        all_prop_uris = self._get_all_property_uris(item['type'])
        for s, p, o in gr.triples( (node, None, None) ):
            if str(p) in all_prop_uris:
                prop_key = all_prop_uris[str(p)]
                prop = all_props[prop_key]
                lit = self._is_literal(prop['type'])
                if 'isArray' in prop and prop['isArray'] and self._is_itemlist(o):
                    item[prop_key] = self._decode_array(o, lit, prop['type'], prop_key)
                else:
                    if lit:
                        newval = self._decode_literal(prop['type'], prop_key, o)
                    else:
                        if 'isMultiType' in prop and prop['isMultiType']:
                            newval = self._decode_resource(o)
                        else:
                            newval = self._decode_resource(o, prop['type'])
                    if 'isArray' in prop and prop['isArray']:
                        if prop_key in item:
                            item[prop_key].append(newval)
                        else:
                            item[prop_key] = [newval]
                    else:
                        item[prop_key] = newval
        return item

