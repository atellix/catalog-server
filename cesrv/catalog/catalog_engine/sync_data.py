class DataSync(object):
    def load(self):
        raise Exception('Subclass must override the "load" method')

    def src_items(self):
        raise Exception('Subclass must override the "src_items" method')

    def src_has(self, item):
        raise Exception('Subclass must override the "src_has" method')

    def dst_items(self):
        raise Exception('Subclass must override the "dst_items" method')

    def dst_has(self, item):
        raise Exception('Subclass must override the "dst_has" method')

    def dst_add(self, item):
        raise Exception('Subclass must override the "dst_add" method')

    def dst_delete(self, item):
        raise Exception('Subclass must override the "dst_delete" method')

    def dst_eq(self, item):
        raise Exception('Subclass must override the "dst_eq" method')

    def dst_update(self, item):
        raise Exception('Subclass must override the "dst_update" method')

    def get_diff(self):
        """
        Calculates the difference between src_data and dst_data.
        Returns a tuple of added and removed items.
        """
        added_items = []
        removed_items = []
        updated_items = []

        # Find added items
        for item in self.src_items():
            if not(self.dst_has(item)):
                added_items.append(item)
            elif getattr(self, 'update', False):
                updated, orig_item = self.dst_eq(item)
                if updated:
                    updated_items.append((orig_item, item))
        # Find removed items
        for item in self.dst_items():
            if not(self.src_has(item)):
                removed_items.append(item)
        return added_items, removed_items, updated_items

    def apply_diff(self, added_items, removed_items, updated_items):
        """
        Applies the difference to dst_data.
        Modifies destination data in-place.
        """
        # Add items to destination
        for item in added_items:
            self.dst_add(item)
        # Update destination items
        for upd in updated_items:
            self.dst_update(upd[0], upd[1])
        # Remove items from destination
        for item in removed_items:
            self.dst_delete(item)
        

    def sync(self):
        self.load()
        added_items, removed_items, updated_items = self.get_diff()
        self.apply_diff(added_items, removed_items, updated_items)

