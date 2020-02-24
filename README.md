## noobcash
Distributed Systems, NTUA, 2019-2020  

## Team  
[Kelesis Dimitrios](https://github.com/jim113)  
[Kontogiannis Andreas](https://github.com/ddaedalus)  
[Peppas Panagiotis](https://github.com/TakisPep)  

## Description  
The project is about a blockchain system developed in command-line interface (cli) with Restful API.  
  
Noobcash consists of two main parts; a server and a client. Client sends commands to the server via REST API calls.  
One participant is the master, and the others are  the clients (children). In the beginning, all clients connect to the master.
After everyone has been connected, the master creates the genesis block, which
gives him 100*(num_children+1) coins. Then, he creates a transaction that gives
100 coins to each participant. Therefore, master ends up with 100 coins.  

When receiving block_capacity valid transactions, the participant starts mining
a new block, by calculating a nonce such that the first difficulty digits of the
block SHA are zeros. The miner is a separate process, so that the participant
can still handle other incoming requests or blocks. When a correct nonce value
is found, the miner notifies the participant, who creates the new block and
sends it to all other participants as well.   
  
When receiving a valid block, child compares its previous_hash with
the hash of the latest block in the chain. If they are equal, then the block is
accepted. Otherwise, it is assumed that a different chain has been created, so
the participant asks all other participants for their blockchains, adopting
the largest one.
