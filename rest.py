import requests
from flask import Flask, jsonify, request, render_template

import sys
import json
from node import Node, no_mine
from transaction import Transaction
from blockchain import Blockchain  
from block import Block


### JUST A BASIC EXAMPLE OF A REST API WITH FLASK



app = Flask(__name__)
#CORS(app)
# user should provide rest api's ports
if(len(sys.argv)==1):
    print("Usage is python3 rest.py is_it_bootstrap? how_many_children? myPort ip_bootstrap myIP !")
    sys.exit(0)

if len(sys.argv) != 5:
    print("Usage is python3 rest.py is_it_bootstrap? how_many_children? myPort ip_bootstrap myIP !")
    sys.exit(0)

# orismata os exis : bootstrap? | arithmos_paidion | port pou trexeis | ip_bootstrap | ip_dikia_sou
start = Node(int(sys.argv[1]), sys.argv[2], int(sys.argv[3]), sys.argv[4])

#................ .......................................................................

@app.route('/show_balance', methods=['GET'])
def get_bal():
    bal = start.balance()
    response = {
        'Balance': bal
    }
    return jsonify(response), 200

@app.route('/view_transactions', methods=['GET'])
def get_trans():

    last_transactions = start.chain.list_of_blocks[-1].transactions
    
    # edo kati einai lathos
    response = {
        'reply': last_transactions,
        'List of transactions in the last verified block': last_transactions
    }
    return jsonify(response), 200

@app.route('/create_transaction', methods=['POST'])
def create():
    data = request.get_json()
    addr = data['address']
    #print ("Address is",addr)
    amount = data['amount']
    #print("Amount is",amount)
    #current balance
    bal = start.balance()
    if (not addr.isnumeric() or int(addr) < 0 or int(addr) > start.children):
        response = {
            'message': "Please provide a number between 0 and " + str(start.children) + " as address."
        }
    elif (int(addr) == start.id):
        response = {
            'message': "You cannot make a transaction with yourself..."
        }
    elif (not amount.isnumeric() or int(amount) <= 0):
        response = {
            'message': "Please provide a positive number as amount."
        }
    elif int(amount) > bal:
        response = {
            #'message': "Ena pitsiriki, einai mpatiraki...",
            'CLICK HERE': "https://www.youtube.com/watch?v=TeT0vNbjs5w"
        }
    else:
        # stall transaction till mining is done
        if not no_mine.isSet():
            no_mine.wait()

        sender = start.all_public_keys[start.id]
        receiver =  start.all_public_keys[int(addr)]
        start.create_transaction(int(addr), int(amount))

        response = {
            'message': "Create transaction works !"
        }
    return jsonify(response), 200

@app.route('/all/mined_block', methods = ['POST'])
def node_found():
    values = request.get_json()
    print((values['last_block']))
    last_block = values['last_block']   # isos to pairnei lathoss
    print("Last block of miner", len(start.chain.list_of_blocks))
    if start.after_mine_verify_block(last_block):
        no_mine.set()
        print('OOOOOOOOKKKKKKKKKKKKKK')
        response = {
            'message' : 'BLOCK ADDED TO BLOCKCHAIN'
        }
        return jsonify(response), 201
    else:
        response = {
            'message' : 'BLOCK VERIFICATION FAILED'
        }
        return jsonify(response), 400



@app.route('/child/register', methods = ['POST'])
def register():
    """
    myid = request.form['id']
    ring = request.form.getlist('ring')
    keys = request.form.getlist('public_key_list')
    gen_index = request.form['gen_index']
    gen_timestamp = request.form['gen_timestamp']
    gen_transactions = request.form.getlist('gen_transactions')
    gen_nonce = request.form['gen_nonce']
    gen_previousHash = request.form['gen_previous_hash']
    """

    #print(':pipapapapapapap')

    data = request.get_json()
    myid = data['id']
    ring = data['ring']
    keys = data['all_public_keys']
    genesis = data['genesis']

    #print("genesis", genesis)
    #print("myid",myid)
    #print("gen_timestamp",gen_timestamp)
    #print("gen_transactions",gen_transactions)
    #print("gen_nonce",gen_nonce)
    #print("gen_previousHash",gen_previousHash)
    if myid is None:
        return "Error:No valid myid",400
    if ring is None:
        return "Error:No valid ring",400
    if keys is None:
        return "Error:No valid public keys",400
    start.receive(myid, ring,keys,genesis)
    response = {'message': 'ok'}
    return jsonify(response), 200

@app.route('/bootstrap/register', methods = ['POST'])
def reg():
    #print('FFFFFFFFFFFFFFFFFFF', request.json)
    a = request.json['address']
    mykey = request.json['public_key']
    if a is None:
        return "Error:No valid address",400
    #print(a)
    #print(mykey, 'AAAA')
    start.register_node(a,mykey)
    response = {'message': 'ok'}
    return jsonify(response), 200

@app.route('/all/broadcast', methods = ['POST'])
def new_tran():
    """
    sender = request.form['sender_adress']
    receiver = request.form['receiver']
    value = request.form['value']
    myid = request.form['myid']
    in_list = request.form.getlist('inputs')
    out_list = request.form['outputs']
    sign = request.form['sign']
    """
    data = request.get_json()
    sender = data['sender']
    receiver = data['receiver']
    value = data['amount']
    myid = data['trans_id']
    in_list = data['inputs']
    out_list = data['outputs']
    sign =data['signature']

    # NOT SURE IF NEEDED
    if not no_mine.isSet():
        no_mine.wait()

    start.receive_trans(sender,receiver,value,in_list,out_list,sign,myid)

    print("BALANCE",start.balance())
    response = {'message': 'ok'}
    return jsonify(response), 200

if __name__ == '__main__':
    app.run(host=sys.argv[2], port = int(sys.argv[1]))
