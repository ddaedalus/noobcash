from block import Block
from transaction import Transaction
from blockchain import Blockchain

from Crypto.PublicKey import RSA
import hashlib as hasher
import sys
import threading
import json
import time
import requests
import copy
import threading

master_port = 8000
bootstrap_ip = 'http://127.0.0.1:' 

no_mine = threading.Event()
no_mine.set()

headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}

class Node:

    def __init__(self, port, my_ip, children=1, bootstrap="no"):
        # Node constructor 
        '''
            port:       int, node port
            my_ip:      String, example: 127.0.0.1
            children:   int, number of children of current node
            bootstrap:  String, "yes" -> bootstrap, "no" -> child  
        '''

        self.chain = Blockchain()
        self.port = port
        self.public_key, self.private_key = self.generate_wallet()
        self.ring = [bootstrap_ip + str(master_port)] # contains each node address
        self.all_public_keys = []
        self.all_transactions = []
        self.ip = my_ip
        self.children = children

        if bootstrap == "yes":
            # Case that current node is bootstrap
            self.seen = 0 # number of children that have participated
            self.all_public_keys = [self.public_key]
            self.chain.create_genesis(children, self)
            self.all_transactions.append(self.chain.list_of_blocks[0].transactions)
           
            # Initialize threading of bootstrap 
            self.e = threading.Event()
            self.e.clear()
            thread = threading.Thread(target=self.target)
            thread.start()

        else:
            # Register child in bootstrap
            self.register()


    @staticmethod
    def generate_wallet():
        # A function that generates a public key and a private key

        rsa_keypair = RSA.generate(2048)
        privkey = rsa_keypair.exportKey('PEM').decode()
        pubkey = rsa_keypair.publickey().exportKey('PEM').decode()

        return (pubkey, privkey)


    def register(self):
    	# Register children in bootstrap
        # Child's code
        
        data = { 
            'address': "http://" + self.ip + ":" + self.port, 
            'public_key': self.public_key 
        }
        data = json.dumps(data)
        
        return requests.post(self.ring[0] + "/child/register", data=data, headers=headers)


    def register_node(self, ring, public_key):
        # Register nodes
        # Bootstrap's code
        '''
            ring:           String, ring of new registered node
            public_key:     String
        '''

        self.ring.append(ring)
        self.all_public_keys.append(public_key)
        self.seen += 1
        if(self.seen == self.children):
            self.e.set()
            print("All in")

        return


    def target(self):
        # target function threading
        # bootstrap's code

        # Wait for all children to participate
        self.e.wait()

        time.sleep(4) 
        for identity,ring in self.ring[1:]:
            # Send initial information to children
            identity += 1  # bootstrap id = 0 
            self.send(ring, identity)
        time.sleep(4)

        self.chain.set_copy_params(self.ring, self.id)

        for child, ring in enumerate(self.ring[1:]):
            if not no_mine.isSet():
                no_mine.wait()
            child += 1
            self.send_trans(child, ring, self.all_public_keys[child])   

        self.trans_dict = {} # a dict of (key, value) = (public_key, list of trans of same sender)
        for public_key in self.all_public_keys:
            self.trans_dict[public_key] = []

        return


    def send(self, ring, identity):
        # Send initial information to children
        # bootstap's code
        '''
            identity:   int
            ring:       String, ring of the node that the message is sent
        '''

        data = {
            'id': identity, 
            'ring': self.ring,
            'all_public_keys':self.all_public_keys,
            'genesis':self.chain.list_of_blocks[0]   ## ??
        }
        data = json.dumps(data)
        # print(requests.post(ring + '/child/register', data=data, headers=headers))
        
        return requests.post(ring + '/child/register', data=data, headers=headers)


    def receive(self, identity, ring, keys, genesis):
        # response to send
        # child's code
        '''
            identity:   int, child's ID
            ring:       String
            keys:       list of String, all public keys
            genesis:    Block
        '''

        self.id = identity
        self.ring = ring.copy()
        self.chain.set_copy_params(self.ring, self.id)
        self.all_public_keys = keys.copy()

        # Initialize dict of trans for each public key
        self.trans_dict = {}
        for public_key in self.all_public_keys:
            self.trans_dict[public_key] = []

        node_block = Block(genesis['index'], genesis['transactions'], 
                        genesis['nonce'], genesis['prev_hash'], genesis['timestamp'])
        node_block.hash_block()
        self.chain.list_of_blocks.append(node_block)
        trans_block_list = genesis['transactions']   # list

        trans = trans_block_list[0]  # only one trans per child
        print("transaction", trans)

        current_trans = {
            'transaction_id': trans['transaction_id'], 
            'value' : trans['value'], 
            'receiver' : trans['receiver_address']
        }

        # Adding the father's transanction to trans_dict (father is the sender)
        self.trans_dict[self.all_public_keys[0]].append(current_trans)

        return 


    def balance(self):
        # Computes balance of current node

        balance = 0
        for trans in self.all_transactions:
            balance += trans.amount

        return balance


    def create_transaction(self, receiver, amount):
        '''
            receiver:   Node
            amount:     int
        '''

        t = Transaction(self.public_key,receiver.public_key,amount)
        t.sign_transaction(self.private_key)
        # dedomeno active nodes, prepei na to ypologisoume
        t.broadcast_transaction(active_nodes)

    def receive_broadcast(t):
        t.validate_transaction()

    
    
    



    #def verify_transaction():

    #def broadcast_public_key():


n = Node(1)
print(n.generate_wallet())

