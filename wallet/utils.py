import uuid
TRANSACTION_ID_LENGTH = 12
def create_short_uuid4():
    return uuid.uuid4().hex[:TRANSACTION_ID_LENGTH]