import uuid
import json
from rdflib import URIRef, Namespace, Literal
from rdflib.namespace import RDF, RDFS, SKOS

SCH = Namespace('http://schema.org/')

class DataCoder(object):
    def __init__(self, schema, graph, base_uri):
        self.schema = schema
        self.graph = graph
        self.base_uri = base_uri

    def encode_rdf(self, obj, obj_uri=None):
        if 'uuid' not in obj:
            data = obj.copy()
            data['uuid'] = str(uuid.uuid4())
        else:
            data = obj
        if obj_uri is None:
            obj_uri = URIRef(self.base_uri + '#' + data['uuid'])
        self._build_resource(data, data['type'], obj_uri)

    def _get_all_properties(self, rsrc_type):
        rsrc_def = self.schema[rsrc_type]
        if 'extends' in rsrc_def and rsrc_def['extends'] != 'IObject':
            all_props = self._get_all_properties(rsrc_def['extends'])
        else:
            all_props = {}
        for k in rsrc_def['properties'].keys():
            all_props[k] = rsrc_def['properties'][k]
        return all_props

    def _is_literal(self, val_type):
        return val_type == 'string' or val_type == 'number' or val_type == 'boolean' or val_type == 'Date'

    def _build_literal(self, rsrc, prop, val_type, k, dval):
        gr = self.graph
        if val_type == 'string' or val_type == 'number' or val_type == 'boolean':
            if k == 'uuid':
                gr.add( (rsrc, prop, URIRef('urn:uuid:' + str(dval).lower())) )
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
        print(propSpec)
        if 'isMultiType' in propSpec and propSpec['isMultiType']:
            print('Multi-type')
            if 'type' not in dval:
                raise Exception(f"Unable to determine object type from {sub_type} without 'type'")
            sub_type = dval['type']
        print(sub_type)
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
                    gr.add( (item_uri, URIRef(val['uri']), sub_item) )

#    def decode_rdf(self, uri):
#
