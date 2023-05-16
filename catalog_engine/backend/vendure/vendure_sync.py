import pprint 

class VendureSync(object):
    def __init__(self, vendure_client):
        self.vendure_client = vendure_client

    def sync_merchant(self, cat_list):
        print('Sync Merchant')
        # get collections
        # get listings
        # iterate collections / generate listings
        pprint.pprint(cat_list)
        print('Sync Merchant Done')
