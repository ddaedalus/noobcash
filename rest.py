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
# CORS(app)
# user should provide rest api's ports
if (len(sys.argv) == 1):
    print("Usage is python3 rest.py port ip num_of_children yes/no(father or no) !")
    sys.exit(0)

if len(sys.argv) != 5:
    print("Usage is python3 rest.py port ip num_of_children yes/no(father or no) !")
    sys.exit(0)

# port, my ip, number of children, father or no father
start = Node(int(sys.argv[1]), sys.argv[2], int(sys.argv[3]), sys.argv[4])


# ................ .......................................................................

@app.route('/show_balance', methods=['GET'])
def get_bal():
    bal = start.balance()
    print('POSA EXO', len(start.chain.list_of_blocks), len(start.buffer))
    response = {
        'Balance': bal
    }
    return jsonify(response), 200


@app.route('/view_transactions', methods=['GET'])
def get_trans():
    last_transactions = start.chain.list_of_blocks[-1].transactions


    response = {

        'List of transactions in the last verified block': last_transactions
    }
    return jsonify(response), 200


@app.route('/create_transaction', methods=['POST'])
def create():
    data = request.get_json()
    addr = data['address']
    # print ("Address is",addr)
    amount = data['amount']
    # print("Amount is",amount)
    # current balance
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
        print(bal)
        response = {
            'message': "Not enough money..."

        }
    else:
        # stall transaction till mining is done
        if not no_mine.isSet():
            no_mine.wait()

        sender = start.all_public_keys[start.id]
        receiver = start.all_public_keys[int(addr)]
        start.create_transaction(int(addr), int(amount))

        response = {
            'message': "Create transaction works !"
        }
    return jsonify(response), 200


@app.route('/all/mined_block', methods=['POST'])
def node_found():
    values = request.get_json()
    # print((values['last_block']))
    mine_time = values['mine_time']
    last_block = values['last_block']
    print("Last block of miner", len(start.chain.list_of_blocks))
    if start.after_mine_verify_block(last_block, mine_time):
        no_mine.set()
        print('OOOOOOOOKKKKKKKKKKKKKK')
        response = {
            'message': 'BLOCK ADDED TO BLOCKCHAIN'
        }
        return jsonify(response), 201
    else:
        no_mine.set()
        response = {
            'message': 'BLOCK VERIFICATION FAILED'
        }
        return jsonify(response), 400


@app.route('/child/register', methods=['POST'])
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



    data = request.get_json()
    myid = data['id']
    ring = data['ring']
    keys = data['all_public_keys']
    genesis = data['genesis']

    # print("genesis", genesis)
    # print("myid",myid)
    # print("gen_timestamp",gen_timestamp)
    # print("gen_transactions",gen_transactions)
    # print("gen_nonce",gen_nonce)
    # print("gen_previousHash",gen_previousHash)
    if myid is None:
        return "Error:No valid myid", 400
    if ring is None:
        return "Error:No valid ring", 400
    if keys is None:
        return "Error:No valid public keys", 400
    start.receive(myid, ring, keys, genesis)
    response = {'message': 'ok'}
    return jsonify(response), 200


@app.route('/bootstrap/register', methods=['POST'])
def reg():
    # print('FFFFFFFFFFFFFFFFFFF', request.json)
    a = request.json['address']
    mykey = request.json['public_key']
    if a is None:
        return "Error:No valid address", 400
    # print(a)
    # print(mykey, 'AAAA')
    start.register_node(a, mykey)
    response = {'message': 'ok'}
    return jsonify(response), 200


@app.route('/all/broadcast', methods=['POST'])
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
    sign = data['signature']


    # if not no_mine.isSet():
    #    no_mine.wait()

    start.receive_trans1(sender, receiver, value, in_list, out_list, sign, myid)

    print("BALANCE", start.balance())
    response = {'message': 'ok'}
    return jsonify(response), 200


@app.route('/all/consensus', methods=['POST'])
def go_for_consensus():
    # signal all that we will start consensus so infrom your data
    data = request.get_json()
    address = data['address']
    #start.chain.miner.set()  # i should stop mining we do consensus
    start.inform_friends(address)  # go in to inform ur buddies
    response = {'message': 'ok'}
    return jsonify(response), 200


@app.route('/all/start_now', methods=['POST'])
def go_for_repeat():
    # signal all that we will start consensus so infrom your data
    start.auto_run.set()
    response = {'message': 'ok'}
    return jsonify(response), 200


@app.route('/all/receive_consensus_data', methods=['POST'])
def cons_data():
    data = request.get_json()
    pub_key = data['pub_key']
    chain = data['chain']
    trans_dict = data['trans_dict']
    unspent = data['utxos']
    start.update_consunsus_data(pub_key, chain, trans_dict, unspent)
    response = {'message': 'ok'}
    return jsonify(response), 200


if __name__ == '__main__':
    app.run(host=sys.argv[2], port=int(sys.argv[1]))