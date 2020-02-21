import hashlib as hasher
import time
import datetime as date

class Block:

	def __init__(self, index, transactions, nonce, prev_hash, timestamp=None):
		self.index = index
		self.timestamp = timestamp or time.time()
		self.transactions = transactions
		self.nonce = nonce
		self.prev_hash = prev_hash
		self.current_hash = self.hash_block()
        
        
	def hash_block(self):
		block_to_string = (str(self.index) + 
		           		   str(self.timestamp) + 
		           		   str(self.transactions) + 
		           		   str(self.prev_hash)
						  )
		return hasher.sha256(block_to_string.encode()).hexdigest()
		
		
bl = Block(0,'GENESIS','1','0',date.datetime.now(),)

print(bl.current_hash)
