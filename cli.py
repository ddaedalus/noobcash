import sys
import signal
import requests
import json
from flask import jsonify

# case of asynchronous termination
def signal_handler(sig, frame):

    print("Forced Termination")
    # exiting python, 0 means "successful termination"
    sys.exit(0)


port = int(sys.argv[1])

# chech if we have exactly one port
if(len(sys.argv)<2 or len(sys.argv)>2):
    print("Please enter the port you want to work with")
    print("Write the following \n")
    print("python3 cli.py <port> ")
    print("where <port> the port number you want")
    sys.exit(0)

print("")
print("Welcome! How can i help you ?")

base_url = "http://0.0.0.0:"+str(port)+"/"

flag=1

while(1):

    print("\n")

    # flag = 1 correct action
    # flag = 0 invalid action
    if(flag==0):
        flag = 1
        print(" Invalid action, type help! ")
        action = input()
    else:
        print("You can provide an action. Press help for available actions")
        action = input()

    # case of create a transaction
    if (action[0] == 't'):

        print("##################### \n")
        url = base_url + "create_transaction"
        inputs = action.split()

        # inputs form: id"number" amount
        # we take number and amount
        payload = {'address': inputs[1][2::],'amount': inputs[2]}
        payload = json.dumps(payload)

        response = requests.post(url,data=payload,headers={'Content-type': 'application/json', 'Accept': 'text/plain'})
        print(response.json())   

    # case of show balance or view
    elif (action == 'balance' or action == 'view'):

        print("##################### \n")

        if(action == 'balance'):
            url = base_url + "show_balance"
        else:
            url = base_url + "view_transactions"

        response = requests.get(url)
        print(response.json())
    
    #case of help
    elif (action == 'help'):

        print("##################### \n")
        print("Here is the 5 available actions \n")

        # case for add transaction
        print("Type: << t <recipient_address> <amount> >> in order to create a new transaction")
        print("first argument of t is the recipient's address in form : <idX> where X is the receiver id")
        print("second argument is the amount of nbc to transfer \n")

        # case of view
        print("Type: << view >> in order to view all transactions contained in the last validated block \n")

        # case of balance
        print("Type: << balance >> in order to view this node account balance \n")

        # case of help 
        print("Type: << help >> in order to view the possible actions \n")

        # case of exit
        print("Type: << exit >> in order to exit from the cli... \n")

    elif (action == 'exit'):

        print("##################### \n")
        print("Exiting...")
        print("Byeee")
        sys.exit(0)
    
    else:
        flag = 0
