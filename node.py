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

master_port = 5000
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
        self.ip = my_ip
        self.children = children
        self.unspent = []   # list of dicts of outputs[1]
        self.trans_dict = {}

        if bootstrap == "yes":
            # Case that current node is bootstrap
            self.id = 0
            self.seen = 0 # number of children that have participated
            self.all_public_keys = [self.public_key]
            self.chain.create_genesis(children, self)
            self.unspent.append(json.loads(self.chain.list_of_blocks[0].transactions))  # bootstrap initial transactions
           
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
            'address': "http://" + self.ip + ":" + str(self.port), 
            'public_key': self.public_key 
        }
        data = json.dumps(data)
        print(self.ring[0] + "/bootstrap/register", data)
        return requests.post(self.ring[0] + "/bootstrap/register", data=data, headers=headers)


    def register_node(self, ring, public_key):
        # Register nodes
        # Bootstrap's code
        '''
            ring:           String, ring of new registered node
            public_key:     String
        '''
        print(1000000000000000000000000000000000)

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
        print("SAGAPO DIMITRI")

        time.sleep(2) 
        for identity,ring in enumerate(self.ring[1:]):
            # Send initial information to children
            identity += 1  # bootstrap id = 0 
            self.send(ring, identity)
        time.sleep(2)

        self.chain.set_copy_params(self.ring, self.id)

        print("father balance:", self.balance())

        self.trans_dict = {} # a dict of (key, value) = (public_key, list of trans of same sender)
        for public_key in self.all_public_keys:
            self.trans_dict[public_key] = []

        for child,ring in enumerate(self.ring[1:]):
            if not no_mine.isSet():
                no_mine.wait()
            # Sending 100 nbc to children
            self.create_transaction(1+child, 100)   

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
            'all_public_keys': self.all_public_keys,
            'genesis': self.chain.list_of_blocks[0].block_to_json()   ## ??
        }

        #print("PIPA")
        #print(data)
        data = json.dumps(data)
        #print("PIPIS")
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

        genesis = json.loads(genesis)

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
        trans_block_list = json.loads(genesis['transactions'])   # list
        trans = trans_block_list  # only one trans per child

        current_trans = {
            'trans_id': trans['trans_id'], 
            'amount' : trans['amount'], 
            'receiver' : trans['receiver']
        }

        # Adding the father's transanction to trans_dict (father is the sender)
        self.trans_dict[self.all_public_keys[0]].append(current_trans)

        return 


    def balance(self):
        # Current node computes balance of current node by adding all unspent transactions 

        balance = 0
        #print(self.unspent, 'BDSSBDS')
        for trans in self.unspent:
            balance += int(trans['amount'])

        return balance


    def create_transaction(self, receiver_key, amount):
        '''
            receiver_key:    String
            amount:         int
        '''

        # Find receiver id
        receiver_id = receiver_key

        t_sum = 0
        critical_point = -1
        receiver_inputs = []

        for i,unspent_tr in enumerate(self.unspent):
            # Find the critical point that unspent reaches.
            t_sum += unspent_tr['amount']
            receiver_inputs.append( unspent_tr['trans_id'] )
            if t_sum >= amount:
                result = t_sum - amount
                critical_point = i
                break

        # Check if current node can afford the requested transaction
        if t_sum < amount:
            print("Deal falls")
            return

        #print("makis")

        print(receiver_id)
        receiver_key = self.all_public_keys[receiver_id]
        new_trans = Transaction(self.public_key, receiver_key, amount, receiver_inputs)
        
        # Transaction outputs
        transaction_outputs = []
        d = dict()
        # output[0]
        d["trans_id"] = new_trans.transaction_id
        d["target"] = new_trans.receiver_address
        d["amount"] = new_trans.amount
        transaction_outputs.append(d)
        # output[1]
        d["trans_id"] = new_trans.transaction_id
        d["target"] = new_trans.sender_address
        d["amount"] = result   # remaining money from used unspent
        transaction_outputs.append(d)
        

        print(d)

        # Update current's node unspent
        if critical_point == len(self.unspent) - 1:
            self.unspent = [transaction_outputs[1]]
        else:
            self.unspent = self.unspent[critical_point+1:]
            self.unspent.append(transaction_outputs[1])

        # Set the transaction_outputs of the created transaction
        new_trans.transaction_outputs = transaction_outputs

        # Update trans_dict
        self.trans_dict[self.public_key] = self.unspent.copy()
        self.trans_dict[receiver_key].append(transaction_outputs[0])

        # Sign new signature and broadcast 
        new_trans.sign_transaction(self.private_key)
        self.broadcast(new_trans)

        # Add created transaction in block
        self.chain.add_trans(new_trans)
        #print(self.balance(), 'fdfs')

        return


    def broadcast(self, t):
        # Broadcast transaction to all nodes except current
        '''
            t:  Transaction
        '''
        
        print("Broadcasting...")
        
        # Create json message
        data = json.loads(t.transaction_to_json())
        data['trans_id'] = t.transaction_id

        for ring in self.ring:
            if not (ring == self.ring[self.id]):
                requests.post(ring + "/all/broadcast", json=data, headers=headers)
        
        return


    def validate_transaction(self, t, sender_id):
        # Validate the broadcasted transaction
        '''
            t:          Transaction
            sender_id:  int
        '''

        print("Validating transaction...")
        validate_signature = t.verify_signature(self.all_public_keys[sender_id])

        local_ids = [i['trans_id'] for i in self.trans_dict[self.all_public_keys[sender_id]]]
        
        # print(all([i in local_ids for i in t.transaction_inputs]))
        return all([i in local_ids for i in t.transaction_inputs]) and validate_signature


    def receive_trans(self, sender_key, receiver_key, amount, inputs, outputs, signature, trans_id):
        # Receive broadcasted message

        t = Transaction(sender_key, receiver_key, amount, inputs, outputs)
        t.signature = signature
        t.transaction_id = trans_id

    
        # Find sender_id and receiver_id from their respective public keys
        for i in range(len(self.all_public_keys)):
            if self.all_public_keys[i] == sender_key:
                sender_id = i

            elif self.all_public_keys[i] == receiver_key:
                receiver_id = i

        print(sender_key, sender_id, 'gdgfdfgd')
        # Check if the broadcasted transaction is valid 
        if self.validate_transaction(t, sender_id):
            
            # Update block 
            self.chain.add_trans(t)

            # Update corresponding trans_dict values
            for inputs in t.transaction_inputs:
                for idx, unspent_id in enumerate(self.trans_dict[sender_key]):
                    if inputs == unspent_id['trans_id']:
                        self.trans_dict[sender_key].remove(self.trans_dict[sender_key][idx])

            self.trans_dict[receiver_key].append(t.transaction_outputs[0])
            self.trans_dict[receiver_key].append(t.transaction_outputs[1])

            if receiver_key == self.public_key:
                self.unspent.append(t.transaction_outputs[0])

            print("my balance:", self.balance())

        print(self.unspent)

        return 


    def after_mine_verify_block(self, b):
        '''
            b:  dict, dictionary of a block
        '''

        # Check whether the block is valid using previous hash of the last block in blockchain
        if not b['prev_hash'] == self.chain.list_of_blocks[-1].cur_hash:
            return False

        # Valid case
        block = Block(b['index'], b['transactions'], b['nonce'], b['prev_hash'], b['timestamp']) # create a new block
        
        # Check whether the given nonce is valid
        if block.hash_block() == b['cur_hash']:
            self.chain.miner.set()
            self.chain.list_of_blocks.append(block)
        
            return True

        return False
        

