import uuid

def create_short_uuid4(length):
    def func():
        return uuid.uuid4().hex[:length]
    return func