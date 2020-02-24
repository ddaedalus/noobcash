from collections import OrderedDict
from block import Block

import hashlib as hasher
from Crypto.Hash import SHA
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
import base64
import Crypto
import Crypto.Random

from Crypto.Hash import SHA384

import json

class Transaction:

    def __init__(self, sender_address, receiver_address, 
                    amount, transaction_inputs, 
                    transaction_outputs=[]):

        self.sender_address = sender_address
        self.receiver_address = receiver_address
        self.amount = amount
        self.transaction_inputs = transaction_inputs
        self.transaction_outputs = transaction_outputs
        self.signature = ''
        self.transaction_id = self.hash_transaction().hexdigest()


    def transaction_to_json(self):
        transactions = {
            'sender' : self.sender_address, 
		    'receiver' : self.receiver_address,  
		    'amount' : self.amount, 
            'inputs' : self.transaction_inputs, 
            'outputs' : self.transaction_outputs,
            'signature' : self.signature
        }
        string = json.dumps(transactions, sort_keys=True)
        return string 
    

    def hash_transaction(self):
        string = self.transaction_to_json()
        return SHA.new(string.encode())


    def sign_transaction(self, private_key):
        # Sign the transaction
        '''
            private_key:    String
        '''

        #encoded hash_obj
        hash_obj = self.transaction_to_json()
        hash_obj = SHA.new(str(hash_obj).encode())

        # Generate RSA key
        rsa_key = RSA.importKey(private_key)
        signer = PKCS1_v1_5.new(rsa_key)
        
        self.transaction_id = hash_obj.hexdigest()
        self.signature = (base64.b64encode(signer.sign(hash_obj)).decode())

        return


    def verify_signature(self,public_key):
        # Load public key and verify message

        hash_obj = self.transaction_to_json()
        hash_obj = json.loads(hash_obj)
        hash_obj['signature']=''
        hash_obj = json.dumps(hash_obj, sort_keys = True)
        hash_obj = SHA.new(str(hash_obj).encode())
        
        public_key = RSA.importKey(public_key)
        verifier = PKCS1_v1_5.new(public_key)

        return verifier.verify(hash_obj, base64.b64decode(self.signature))
        # assert verified, 'Signature verification failed'
        # print('Successfully verified message')





#t = Transaction(9,10,100,345,[])

#rsa_keypair = RSA.generate(2048)

#privkey = rsa_keypair.exportKey('PEM').decode()
#pubkey = rsa_keypair.publickey().exportKey('PEM').decode()

# random_gen = Crypto.Random.new().read
# priv = RSA.generate(1024, random_gen)
# pub = priv.publickey()
# privkey = priv.exportKey(format='DER')
# #print(priv.exportKey(format='DER'))
# #print(pub.exportKey(format='DER'))
# pubkey = pub.exportKey(format='DER')


#t.sign_transaction(privkey)
#print(t.verify_signature(pubkey))
#print(t.transaction_to_json())

    # def broadcast_transaction(active_nodes):
    #     # Broadcast the transaction to all active nodes in network 
    #     '''
    #         active nodes:   list of Node
    #     '''

    #     for node in active_nodes:
    #         node.receive_broadcast(self)

    #     return
    

    # def verify_signature(self):
    #     # Checks whether public key matches private key  
    #     '''
    #         Returns boolean
    #     '''

    #     # encoded hash_obj
    #     hash_obj = self.hash_transaction() 

    #     # Generate RSA key
    #     rsa_key = RSA.importKey(self.sender_address)
    #     verifier = PKCS1_v1_5.new(rsa_key)

    #     verification = verifier.verify(hash_obj, base64.b64decode(self.signature))

    #     return verification


    # def validate_transaction():
        
