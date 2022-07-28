import requests
import time
import base64
import ecdsa
import json


def generate_ECDSA_keys():
    sk = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1)
    private_key = sk.to_string().hex()
    public_key = sk.get_verifying_key().to_string().hex()
    tmp = public_key.hex()
    public_key = base64.b64encode(bytes.fromhex(tmp))
    filename = input('Write the name of your new address: ') + '.txt'
    with open(filename, 'w') as f:
        f.write(f'Private key: {private_key}\nWallet address / Public key: {public_key.decode()}')
    print(f'Your new address and private key are now in the file {filename}')
    
    
def sign_move_ECDSA_msg(private_key, add_info):
    message = str(f'move_{round(time.time())}_{add_info["place_id"]}_{add_info["item_id"]}')
    bmessage = message.encode()
    sk = ecdsa.SigningKey.from_string(bytes.fromhex(private_key), curve=ecdsa.SECP256k1)
    signature = base64.b64encode(sk.sign(bmessage))
    return signature, message


def send_movement(addr_from, private_key, add_info):
    if len(private_key) == 64:
        signature, message = sign_move_ECDSA_msg(private_key, add_info)
        url = 'http://localhost:5000/txion'
        payload = {
            'from': addr_from,
            'place_id': add_info['place_id'],
            'product_id': add_info['product_id'],
            'signature': signature.decode(),
            'message': message
        }
        headers = {'Content-Type': 'application/json'}
        res = requests.post(url, json=payload, headers=headers)
        print(res.text)
    else:
        print('Wrong address or key length')
        
        
def check_transactions():
    try:
        res = requests.get('http://localhost:5000/blocks')
        parsed = json.loads(res.text)
        print(json.dumps(parsed, indent=4, sort_keys=True))
    except requests.ConnectionError:
        print('Connection error')
        

def sign_ECDSA_msg(private_key, add_info, msg):
    message = str(f'{msg}_{round(time.time())}_{add_info}')
    bmessage = message.encode()
    sk = ecdsa.SigningKey.from_string(bytes.fromhex(private_key), curve=ecdsa.SECP256k1)
    signature = base64.b64encode(sk.sign(bmessage))
    return signature, message
        

def create_new_place_id(addr_from, private_key, place_id):
    signature, message = sign_ECDSA_msg(private_key, place_id, 'place')
    url = 'http://localhost:5000/new_place'
    register = {
        'from': addr_from,
        'place_id': place_id,
        'signature': signature.decode(),
        'message': message
    }
    headers = {'Content-Type': 'application/json'}
    res = requests.post(url, json=register, headers=headers)
    print(res.text)
    
    
def create_new_item_id(addr_from, private_key, item_id):
    signature, message = sign_ECDSA_msg(private_key, item_id, 'item')
    url = 'http://localhost:5000/new_item'
    register = {
        'from': addr_from,
        'item_id': item_id,
        'signature': signature.decode(),
        'message': message
    }
    headers = {'Content-Type': 'application/json'}
    res = requests.post(url, json=register, headers=headers)
    print(res.text)
    

def create_new_product(addr_from, private_key, item_id, place_id):
    signature, message = sign_ECDSA_msg(private_key, item_id, 'product')
    url = 'http://localhost:5000/new_product'
    register = {
        'from': addr_from,
        'item_id': item_id,
        'place_id': place_id,
        'signature': signature.decode(),
        'message': message
    }
    headers = {'Content-Type': 'application/json'}
    res = requests.post(url, json=register, headers=headers)
    print(res.text)
        
        
def wallet():
    response = None
    addr_from, private_key = None, None
    
    while True:
        
        response = input("""What you want to do:
        1) Create wallet
        2) Login
        3) Check_movements
        4) Make logistic movement
        5) Create new product
        6) Create new item
        7) Create new place
        8) Check my products
        """)
        
        if response == '1':
            generate_ECDSA_keys()
        elif response == '2':
            # addr_from = input('From: introduce your wallet address (public key)\n')
            # private_key = input('Introduce your private key\n')
            
            addr_from = 'GNcSH4PN7V/8+WA9a1ZgJAgZI2SD7qrnMTFXzj3d0cz96jLAQF/mnOaouPoN5Ptvul0kBtUW9prlkRIUBX+YPQ=='
            private_key = 'e2a3647c0c8227d4d47e155b1fb5991bb4065e4a079c9a2a2630d2d850fc8dbb'
            print('public, private keys check complete')
            
        elif response == '3':
            check_transactions()
        elif response == '4' and addr_from is not None:
            product_id = input('Product id: ')
            place_id = input('Place id: ')
            send_movement(addr_from, private_key, {'product_id': product_id, 'place_id': place_id})
        elif response == '5' and addr_from is not None:
            item_id = input('Item id: ')
            place_id = input('Starting place: ')
            create_new_product(addr_from, private_key, item_id, place_id)
        elif response == '6' and addr_from is not None:
            item_id = input('new item id: ')
            create_new_item_id(addr_from, private_key, item_id)
        elif response == '7' and addr_from is not None:
            place_id = input('new place id: ')
            create_new_place_id(addr_from, private_key, place_id)
            

if __name__ == '__main__':
    wallet()
