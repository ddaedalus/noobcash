import hashlib as hasher
import time
import datetime as date
import json

MINING_DIFFICULTY = 4

class Block:

	def __init__(self, index, transactions, nonce, prev_hash, timestamp=time.time()):
		self.index = index
		self.timestamp = timestamp
		self.transactions = transactions
		self.nonce = nonce
		self.prev_hash = prev_hash
		self.cur_hash = -1 #self.hash_block()
        
        
	def hash_block(self):
		block_to_dict = self.block_to_json()
		bb = json.loads(block_to_dict)
		del bb['cur_hash']
		block_to_string = json.dumps(bb)
		block_to_string = block_to_dict.encode()
		res = hasher.sha256(block_to_string).hexdigest()
		return res #update and return current hash of block

	
	def block_to_json(self):
		result = json.dumps(dict(index = self.index,
		timestamp = self.timestamp.__str__(),
		transactions = self.transactions,
		nonce = self.nonce,
		cur_hash = self.cur_hash,
		prev_hash = self.prev_hash
		), sort_keys = True)
		return(result)
		
	
	def add_trans_to_block(self, trans):
		self.transactions.append(trans)
		self.hash_block() #update hash cuz u add trans
		return self
		
	def mine_block(self, e):
		while self.valid_proof() is False and not e.isSet():
			self.nonce += 1
		self.cur_hash = self.hash_block()
		return self
		
	def valid_proof(self, difficulty = MINING_DIFFICULTY):
		guess_hash = self.hash_block()
		return guess_hash[:difficulty] == '0'*difficulty
	
		
	
	def create_genesis(trans):
		genesis = Block(0, trans, 0, 1, date.datetime.now())
		return genesis


	


'''bl = Block(0,['GENESIS'], 1,'0',date.datetime.now())

print(bl.block_to_json())
bl.add_trans_to_block('0')
print(bl.block_to_json())
bl.mine_block(False)
print(bl.block_to_json())'''


