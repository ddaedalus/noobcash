from block import Block
from transaction import Transaction
import json, requests, time
import threading
import node


CHAIN_CAPACITY = 1
headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}

class Blockchain():
	def __init__(self): # constructor of chain
		self.list_of_blocks = []
		self.list_of_trans = []
		self.miner = threading.Event() #local thread of chain to control mining
		
	
	def set_copy_params(self, addresses, identity): # set params representing that this chain is representative of a specific node
		self.id = identity
		self.ring = [adr for adr in addresses]
		return
		
	
	def create_genesis(self, participants, master_node):
		address = master_node.public_key
		money = 100 * (participants + 1)
		trans = Transaction('0', address, money, [])
		trans_dict = json.loads(trans.transaction_to_json())
		trans_dict['trans_id'] = 0
		trans_dict = json.dumps(trans_dict)
		gene = Block(0, trans_dict, 0, 1) # create genesis block
		#gene.cur_hash = gene.hash_block() # update cur hash of new block
		self.list_of_blocks.append(gene) # append 1st block
		
		
	def add_trans(self, trans):
		self.list_of_trans.append(trans)
		if(len(self.list_of_trans) == CHAIN_CAPACITY): # max capacity reached so create new block, do mine
			node.no_mine.clear() # start mining cuz max capacity reached
			ind = len(self.list_of_blocks)
			trans_dict =[json.loads(i.transaction_to_json()) for i in self.list_of_trans] # list of jsons for all trans that are going to be in the block
			prev_hash = self.list_of_blocks[-1].cur_hash # get hash of last block in order to use it as prev hash for the next block
			self.list_of_trans = [] # clear trans buffer
			new_bl = Block(ind, trans_dict, 0, prev_hash)
			self.miner.clear()
			mine = threading.Thread(name='mine', target=self.mine_job, args=(new_bl, ))
			mine.start()
			print('Returned')
			return
			
	def mine_job(self, new_bl):
		print('Start mining')
		new_bl.mine_block(self.miner) # start mining with the local lock
		if(not self.miner.isSet() and len(threading.enumerate()) <= 2):
			self.list_of_blocks.append(new_bl)
			print('Mined block')#, time.time(),threading.enumerate())
			#print('DDD', self.list_of_blocks[0].block_to_json(), time.time())
			for adr in self.ring: # found valid nonce broadcast new block to all except u
				if(adr != self.ring[self.id]):
					mes = {'last_block': self.list_of_blocks[-1].block_to_json()} #message that sends last block in json format
					final_msg = adr + '/all/mined_block'
					requests.post(final_msg, json=mes, headers=headers)
					node.no_mine.set() # set the lock in order to inform all others to stop mining cuz I found a valid block
		return
			
		
	
