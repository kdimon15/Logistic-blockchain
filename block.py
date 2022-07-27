import hashlib
import json


class Block:
    def __init__(self, index, movements, timestamp, previous_hash, new_items, new_places):
        self.index = index
        self.timestamp = timestamp
        self.movements = movements
        self.previous_hash = previous_hash
        self.new_items = new_items
        self.new_places = new_places
        self.nonce = 0

    def compute_hash(self):
        block_string = json.dumps(self.__dict__, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()
