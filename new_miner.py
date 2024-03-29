import time
import requests
from blockchain_cfg import MINER_ADDRESS, MINER_NODE_URL
import json
from flask import Flask, request
from multiprocessing import Process, Pipe
import base64
import ecdsa
from block import Block


def create_genesis_block():
    genesis_block = Block(0, [], time.time(), '0', [], [])
    genesis_block.hash = genesis_block.compute_hash()
    return genesis_block


def proof_of_work(block: Block):
    block.nonce = 0
    computed_hash = block.compute_hash()
    while not computed_hash.startswith('00'):
        block.nonce += 1
        computed_hash = block.compute_hash()
    return computed_hash


def mine(a, blockchain, node_pending_movements):

    BLOCKCHAIN = blockchain
    NODE_PENDING_MOVEMENTS = node_pending_movements

    while True:

        NODE_PENDING_MOVEMENTS = requests.get(url=MINER_NODE_URL+'/txion', params={'update': MINER_ADDRESS}).content
        NODE_PENDING_MOVEMENTS = json.loads(NODE_PENDING_MOVEMENTS)

        ADDR_TO_PLACES = requests.get(url=MINER_NODE_URL+'/new_place', params={'update': MINER_ADDRESS}).content
        ADDR_TO_PLACES = json.loads(ADDR_TO_PLACES)

        ADDR_TO_ITEMS = requests.get(url=MINER_NODE_URL+'/new_item', params={'update': MINER_ADDRESS}).content
        ADDR_TO_ITEMS = json.loads(ADDR_TO_ITEMS)

        if len(NODE_PENDING_MOVEMENTS)+len(ADDR_TO_PLACES)+len(ADDR_TO_ITEMS) > 0:
            
            for x in ADDR_TO_PRODUCTS:
                NODE_PENDING_MOVEMENTS.append(x)
            
            last_block = BLOCKCHAIN[-1]
            new_block = Block(index=last_block.index+1,
                            movements=NODE_PENDING_MOVEMENTS,
                            timestamp=time.time(),
                            previous_hash=last_block.hash,
                            new_items=ADDR_TO_ITEMS,
                            new_places=ADDR_TO_PLACES)
            new_block.hash = proof_of_work(new_block)
            BLOCKCHAIN.append(new_block)
            a.send(BLOCKCHAIN)
            requests.get(url=MINER_NODE_URL+'/blocks', params={'update': MINER_ADDRESS})

        time.sleep(5)




app = Flask(__name__)
BLOCKCHAIN = [create_genesis_block()]
NODE_PENDING_MOVEMENTS = []
ADDR_TO_ITEMS = []
ADDR_TO_PLACES = []
ADDR_TO_PRODUCTS = []

PRODUCTS_NOW = {}

@app.route('/product_id', methods=['GET'])
def get_product_id():
    addr = request.args.get('update')
    cur_id = 0
    
    for block in BLOCKCHAIN:
        for move in block.movements:
            if addr == move['from'] and int(move['product_id']) > cur_id:
                cur_id = int(move['product_id'])
                
    if addr in PRODUCTS_NOW: PRODUCTS_NOW[addr] += 1
    else: PRODUCTS_NOW[addr] = 1

    return str(cur_id + PRODUCTS_NOW[addr])


@app.route('/blocks', methods=['GET'])
def get_blocks():

    if request.args.get('update') == MINER_ADDRESS:
        global BLOCKCHAIN
        BLOCKCHAIN = pipe_input.recv()
        
        global PRODUCTS_NOW
        PRODUCTS_NOW = {}

    chain_to_send = BLOCKCHAIN

    chain_to_send_json = []
    for block in chain_to_send:
        block = {
            'index': str(block.index),
            'timestamp': str(block.timestamp),
            'movements': str(block.movements),
            'nonce': str(block.nonce),
            'hash': str(block.hash),
            'previous_hash': str(block.previous_hash),
            'new_places': str(block.new_places),
            'new_items': str(block.new_items)
        }
        chain_to_send_json.append(block)

    chain_to_send = json.dumps(chain_to_send_json, sort_keys=True)
    return chain_to_send


def validate_signature(public_key, signature, message):
    public_key = (base64.b64decode(public_key)).hex()
    signature = base64.b64decode(signature)
    vk = ecdsa.VerifyingKey.from_string(bytes.fromhex(public_key), curve=ecdsa.SECP256k1)

    try:
        return vk.verify(signature, message.encode())
    except:
        return False


@app.route('/txion', methods=['GET', 'POST'])
def transaction():
    if request.method == 'POST':
        new_txion = request.get_json()

        places_list = []
        products_list = []
        items_list = []
        for block in BLOCKCHAIN:
            for x in block.new_items:
                if new_txion['from'] == x['from']:
                    items_list.append(x['item_id'])
            for x in block.new_places:
                if new_txion['from'] == x['from']:
                    places_list.append(x['place_id'])
            for move in block.movements:
                if move['from'] == new_txion['from']:
                    products_list.append(move['product_id'])

        if ('item_id' in new_txion.keys() and (new_txion['item_id'] not in items_list or new_txion['place_id'] not in places_list)) or\
            ('item_id' not in new_txion.keys() and (new_txion['place_id'] not in places_list or new_txion['product_id'] not in products_list)):
                return 'Незарегистрированное место или предмет'
            
        if validate_signature(new_txion['from'], new_txion['signature'], new_txion['message']):
            NODE_PENDING_MOVEMENTS.append(new_txion)
            return 'Transaction submission successful\n'
        else:
            return 'Transaction submission failed. Wrong signature'

    elif request.method == 'GET' and request.args.get('update') == MINER_ADDRESS:
        pending = json.dumps(NODE_PENDING_MOVEMENTS, sort_keys=True)
        NODE_PENDING_MOVEMENTS[:] = []

        return pending


@app.route('/new_place', methods=['GET', 'POST'])
def new_place():
    if request.method == 'POST':
        
        new_txion = request.get_json()
        
        if validate_signature(new_txion['from'], new_txion['signature'], new_txion['message']):
            ADDR_TO_PLACES.append(new_txion)
                
            return 'Adding a place was ended successful\n'
        else:
            return 'Adding a place submission failed. Wrong signature'
        
    elif request.method == 'GET' and request.args.get('update') == MINER_ADDRESS:
        pending = json.dumps(ADDR_TO_PLACES, sort_keys=True)
        ADDR_TO_PLACES[:] = []

        return pending


@app.route('/new_item', methods=['GET', 'POST'])
def new_item():
    if request.method == 'POST':
        new_txion = request.get_json()

        if validate_signature(new_txion['from'], new_txion['signature'], new_txion['message']):
            ADDR_TO_ITEMS.append(new_txion)

            return 'Adding a item was ended successful\n'
        else:
            return 'Adding a item submission failed. Wrong signature'

    elif request.method == 'GET' and request.args.get('update') == MINER_ADDRESS:
        pending = json.dumps(ADDR_TO_ITEMS, sort_keys=True)
        ADDR_TO_ITEMS[:] = []

        return pending


if __name__ == '__main__':

    pipe_output, pipe_input = Pipe()

    miner_process = Process(target=mine, args=(pipe_output, BLOCKCHAIN, NODE_PENDING_MOVEMENTS))
    miner_process.start()

    transactions_process = Process(target=app.run(), args={'host': pipe_input, 'port': 5000, 'debug': True})
    transactions_process.start()
