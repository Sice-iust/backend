class PaymentGateway:
    def __init__(self, name, description, callback_url, request_url, verify_url):
        self.name = name
        self.description = description
        self.callback_url = callback_url
        self.request_url = request_url
        self.verify_url = verify_url

    def reqirect_url(self):
        raise NotImplementedError()

    def request(self, user, amount, description, merchant_id):
        raise NotImplementedError()

    def verify(self, status_query, authority, merchant_id):
        raise NotImplementedError()
