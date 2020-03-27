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
import datetime, time

master_port = 5000
bootstrap_ip = 'http://192.168.1.1:'      #127.0.0.1:'   #

no_mine = threading.Event()
no_mine.set()

headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}

# all_chains_here = {} #every node put his chain here in case of conflict
# all_trans_dicts_here = {} #all trans dict
# all_utxos_here = {} # dict of all utxos of each player
consensus = threading.Event()  # if set then do consensus
consensus.clear()  # clear at the beginning cuz no consensus is needed

skata = threading.Event()  # if set then do consensus
skata.clear()  # clear at the beginning cuz no consensus is needed


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
        self.ring = [bootstrap_ip + str(master_port)]  # contains each node address
        self.all_public_keys = []
        self.ip = my_ip
        self.children = children
        self.unspent = []  # list of dicts of outputs[1]
        self.trans_dict = {}
        self.buffer = []  # list of input stream
        self.all_chains_here = {}  # every node put his chain here in case of conflict
        self.all_trans_dicts_here = {}  # all trans dict
        self.all_utxos_here = {}  # dict of all utxos of each player
        self.rep = threading.Event()
        self.rep.clear()
        thread1 = threading.Thread(target=self.receiver_repeater)
        thread1.start()
        #########################################################
        # self.start_cons = threading.Event()
        # self.start_cons.clear()
        # thread2 = threading.Thread(target=self.inform_friends) #target to infrom friends about my data
        # thread2.start()
        #########################################################
        self.auto_run = threading.Event()
        self.auto_run.clear()
        thread3 = threading.Thread(target=self.run_all_trans)  # target to auto run trans
        thread3.start()
        #########################################################

        if bootstrap == "yes":
            # Case that current node is bootstrap
            self.id = 0
            self.seen = 0  # number of children that have participated
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
        # print(self.ring[0] + "/bootstrap/register", data)
        return requests.post(self.ring[0] + "/bootstrap/register", data=data, headers=headers)

    def register_node(self, ring, public_key):
        # Register nodes
        # Bootstrap's code
        '''
            ring:           String, ring of new registered node
            public_key:     String
        '''
        # print(1000000000000000000000000000000000)

        self.ring.append(ring)
        self.all_public_keys.append(public_key)
        self.seen += 1
        if (self.seen == self.children):
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
        for identity, ring in enumerate(self.ring[1:]):
            # Send initial information to children
            identity += 1  # bootstrap id = 0
            self.send(ring, identity)
        time.sleep(2)

        self.chain.set_copy_params(self.ring, self.id)

        print("father balance:", self.balance())

        self.trans_dict = {}  # a dict of (key, value) = (public_key, list of trans of same sender)
        for public_key in self.all_public_keys:
            self.trans_dict[public_key] = []

        for child, ring in enumerate(self.ring[1:]):
            if not no_mine.isSet():
                no_mine.wait()
            # Sending 100 nbc to children
            self.create_transaction(1 + child, 100)
        self.rep.set()  # facther activate his buffer
        # self.start_cons.set() # father activate his consensus
        # self.auto_run.set() # father activate his auto run
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
            'genesis': self.chain.list_of_blocks[0].block_to_json()  ## ??
        }


        # print(data)
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
        # node_block.hash_block()
        self.chain.list_of_blocks.append(node_block)
        trans_block_list = json.loads(genesis['transactions'])  # list
        trans = trans_block_list  # only one trans per child

        current_trans = {
            'trans_id': trans['trans_id'],
            'amount': trans['amount'],
            'receiver': trans['receiver']
        }

        # Adding the father's transanction to trans_dict (father is the sender)
        self.trans_dict[self.all_public_keys[0]].append(current_trans)
        self.rep.set()  # child activate his buffer
        # self.start_cons.set() # child activate his consensus
        # self.auto_run.set() # child activate his auto run
        return

    def balance(self):
        # Current node computes balance of current node by adding all unspent transactions

        balance = 0
        # print(self.unspent, 'BDSSBDS')
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

        for i, unspent_tr in enumerate(self.unspent):
            # Find the critical point that unspent reaches.
            t_sum += unspent_tr['amount']
            receiver_inputs.append(unspent_tr['trans_id'])
            if t_sum >= amount:
                result = t_sum - amount
                critical_point = i
                break

        # Check if current node can afford the requested transaction
        if t_sum < amount:
            print("Deal falls")
            return



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
        d = d.copy()
        d["trans_id"] = new_trans.transaction_id
        d["target"] = new_trans.sender_address
        d["amount"] = result  # remaining money from used unspent
        transaction_outputs.append(d)
        # print(d)

        # print(d)

        # Update current's node unspent
        if critical_point == len(self.unspent) - 1:
            self.unspent = [transaction_outputs[1]]
        else:
            self.unspent = self.unspent[critical_point + 1:]
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
        # print(self.balance(), 'fdfs')

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

        # print(sender_id)
        return all([i in local_ids for i in t.transaction_inputs]) and validate_signature

    def receive_trans1(self, sender_key, receiver_key, amount, inputs, outputs, signature, trans_id):
        self.buffer.append(
            [sender_key, receiver_key, amount, inputs, outputs, signature, trans_id])  # put raw data in buffer
        print(len(self.chain.list_of_blocks), 'BOO')
        return

    def receiver_repeater(self):
        self.rep.wait()  # w8 till trigger
        # time.sleep(5)
        # if not no_mine.isSet():
        #     no_mine.wait()
        vvgg = 1
        while (True):
            if not no_mine.isSet():
                no_mine.wait()
            if consensus.isSet():
                consensus.wait()

            if (len(self.buffer) != 0 and no_mine.isSet() and consensus.isSet() is False):
                # receive if we have transfer and we neither mine nor are we in consensus mode
                fd = open('res/trans_times' + str(self.id) + '.txt', 'a')
                start_time = time.time()
                ###########################################
                i = self.buffer.pop(0)
                self.receive_trans(i[0], i[1], i[2], i[3], i[4], i[5], i[6])
                # print('GIVE ME MORE')
                #############################
                fd.write(str(time.time() - start_time) + '\n')  # append time taken to complete trans
                start_time = time.time()  # refresh start
                fd.close()
                #############################
                time.sleep(1)
                if (vvgg == 1):
                    if (self.id == self.children):
                        self.start_friends()
                        vvgg = 23
            # print('XOROS',len(self.buffer), end=' ')
        print('I AM DONE HERE')
        return

    def start_friends(self):
        for ring in self.ring:
            requests.post(ring + "/all/start_now", headers=headers)
        return

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
            self.trans_dict[sender_key].append(t.transaction_outputs[1])

            if receiver_key == self.public_key:
                self.unspent.append(t.transaction_outputs[0])

            #print("my balance:", self.balance())

        #print(self.unspent)

        return

    def after_mine_verify_block(self, b, mine_time):
        '''
            b:  dict, dictionary of a block
        '''
        if consensus.isSet():
            consensus.wait()
        fd = open('res/mine_times' + str(self.id) + '.txt', 'a')  # file for mine times for each node
        # Check whether the block is valid using previous hash of the last block in blockchain
        b = json.loads(b)
        ttt = [i for i in b['transactions']]
        # print('gggg', b['prev_hash'], self.chain.list_of_blocks[-1].cur_hash)
        if not b['prev_hash'] == self.chain.list_of_blocks[-1].cur_hash:
            self.chain.miner.set()
            #no_mine.set()  # stop minig cuz someone found block and now we consensus
            print('About to start consensus..')
            consensus.set()  # start the process
            self.send_consensus_signal()  # infrom buddies we will consensus
            print('ALERT! WE START CONSENSUS!')
            self.chain.list_of_blocks = self.resolve_conf()  # update my data cuz i could not verify block
            fd.write(str(time.time() - float(mine_time)) + '\n')  # write mine time in file and close
            fd.close()
            consensus.clear()  # clear lock cuz all friends have informed about their data
            print('CONSENSUS DONE', consensus.isSet(), len(self.buffer))
            return False

        # Valid case
        block1 = Block(int(b['index']), ttt, int(b['nonce']), b['prev_hash'],
                       float(b['timestamp']))  # create a new block

        # block.hash_block()
        # print('VVVVVVVVVVVVVVV', json.loads(block1.block_to_json())['cur_hash'])
        # print((block1.hash_block()))
        # print(block1.hash_block(), b['cur_hash'])
        # Check whether the given nonce is valid
        if block1.hash_block() == b['cur_hash']:
            self.chain.miner.set()
            block1.cur_hash = b['cur_hash']
            self.chain.list_of_blocks.append(block1)
            fd.write(str(time.time() - float(mine_time)) + '\n')
            fd.close()
            return True
        # if we reached this point then we need consensus
        # self.chain.miner.set()
        # no_mine.set()  # stop minig cuz someone found block and now we consensus
        # print('About to start consensus..')
        # consensus.set()  # start the process
        # self.send_consensus_signal()  # infrom buddies we will consensus
        # print('ALERT! WE START CONSENSUS!')
        # self.chain.list_of_blocks = self.resolve_conf()  # update my data cuz i could not verify block
        # fd.write(str(time.time() - float(mine_time)) + '\n')
        # fd.close()
        # consensus.clear()  # clear lock cuz all friends have informed about their data
        # print('CONSENSUS DONE', consensus.isSet(), len(self.buffer))
        return False

    def send_consensus_signal(self):
        msg = {'address': self.ring[self.id]}
        for ring in self.ring:
            if not (ring == self.ring[self.id]):
                requests.post(ring + "/all/consensus", json=msg, headers=headers)  # attach my address

        return

    def inform_friends(self, address):
        # global all_chains_here, all_trans_dicts_here, all_utxos_here
        # self.start_cons.wait() # w8 until thread is triggered
        # while(True): # loop foerver and inform friends ONLY if consensus is set
        # if(consensus.isSet()): # time to inform friends about my data
        # all_chains_here[self.public_key] = self.chain # my chain in dict with my pub.key as key
        # all_trans_dicts_here[self.public_key] = self.trans_dict # my dict
        # all_utxos_here[self.public_key] = self.unspent # my unspent
        msg = {'pub_key': self.public_key, 'chain': self.chain.output(), 'trans_dict': self.trans_dict,
               'utxos': self.unspent}
        requests.post(address + '/all/receive_consensus_data', json=msg, headers=headers)
        print('I info', str(self.id))
        return

    def update_consunsus_data(self, public_key, chain, trans_dict, unspent):
        self.all_chains_here[public_key] = chain  # my chain in dict with my pub.key as key
        self.all_trans_dicts_here[public_key] = trans_dict  # my dict
        self.all_utxos_here[public_key] = unspent  # my unspent
        print('EDO exo', len(self.all_chains_here))
        return

    def resolve_conf(self):
        all_chains_here, all_trans_dicts_here, all_utxos_here = self.all_chains_here, self.all_trans_dicts_here, self.all_utxos_here
        while (True):
            # global all_chains_here, all_trans_dicts_here, all_utxos_here
            #print(len(all_utxos_here), len(all_chains_here), len(all_chains_here.values()), len(all_chains_here.items()), len(all_utxos_here))
            if (len(all_chains_here) == self.children and len(all_utxos_here) == self.children):  # if all go in
                new_chain = max(all_chains_here.values(),
                                key=lambda x: len(x))  # check length of all chain and pick grater
                break
        #         winner = -1
        #         for k, v in all_chains_here.items():  # find trans dict of winner in order to inform my unspent
        #             if (v == new_chain):
        #                 winner = k
        #                 break
        #         info = all_trans_dicts_here[winner]  # get trans dict of winner
        #         new_unspent = copy.deepcopy(
        #             info[self.public_key])  # in order to know my new unspent use winners trans dict
        #         break
        # new_trans_dict = copy.deepcopy(info)
        # del new_trans_dict[self.public_key]  # remove my data cuz i have them in new utxos
        # new_trans_dict[winner] = all_utxos_here[winner]  # updata my dict to have winners utxos
        self.all_chains_here = {}
        self.all_trans_dicts_here = {}  # reset dicts again
        self.all_utxos_here = {}

        new_blocks = []
        for i in new_chain.values():
            b = json.loads(i)
            ttt = [i for i in b['transactions']]
            block = Block(int(b['index']), ttt, int(b['nonce']), b['prev_hash'], float(b['timestamp']))
            new_blocks.append(block)
        print('OKE')
        # new_blocks = copy.deepcopy(new_chain.list_of_blocks)
        # new_trans = copy.deepcopy(new_chain.list_of_trans)
        return (new_blocks)  # return results

    def run_all_trans(self):
        self.auto_run.wait()  # w8 until trigger
        time.sleep(5)
        print('Check if genesis got in..')
        if not no_mine.isSet():
            no_mine.wait()
        print('Starting auto...')
        with open('5nodes/transactions' + str(self.id) + '.txt', 'r') as fd:
            for line in fd:  # go through all lines and make transactions
                rec, ammount = (line.strip('\n')).split(' ')
                url = 'http://' + str(self.ip) + ':' + str(self.port) + "/create_transaction"
                payload = {'address': rec[2], 'amount': ammount}  # give data as in cli form, [id, ammount]
                payload = json.dumps(payload)
                response = requests.post(url, data=payload,
                                         headers={'Content-type': 'application/json',
                                                  'Accept': 'text/plain'})  # hit API
                # print(response.json())
                time.sleep(1)  # sleep 1 sec and repeat

        return


