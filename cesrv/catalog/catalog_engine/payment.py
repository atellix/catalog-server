import requests
from flask import current_app as app

class PaymentManager():
    def __init__(self, host):
        self.host = host

    def request_atellixpay_payment(self, amount, order_id):
        url = 'https://{}/payments/atellixpay'.format(self.host)
        rq = requests.post(url, json={
            'price_total': amount,
            'order_id': order_id,
        })
        if rq.status_code != 200:
            raise Exception('AtellixPay payment request failed: {}'.format(rq.text))
        res = rq.json()
        if res['result'] != 'ok':
            raise Exception('AtellixPay payment request error: {}'.format(res['error']))
        return res

    def request_authorizenet_payment(self, amount, order_id):
        url = 'https://{}/payments/authorizenet'.format(self.host)
        rq = requests.post(url, json={
            'amount': amount,
            'order_id': order_id,
        })
        if rq.status_code != 200:
            raise Exception('Request failed: {}'.format(rq.text))
        res = rq.json()
        if res['result'] != 'ok':
            raise Exception('Request error: {}'.format(res['error']))
        return res


