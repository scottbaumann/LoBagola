from bidihi_IBapi import *
from bidihi_functions import *

info = {"stop": False}
account = {"prod": "U3005079", "paper": "DU2186704"}  # switch this to prod account when needed
socket = {"prod": 7496, "paper": 7497}  # paper socket is 7497, prod socket is 7496


def run_loop():
    app.run()


# Connect to IB -----------------------------> configure prod vs paper here (1 of 2)
app = IBapi()
app.connect('127.0.0.1', socket['paper'], random.randint(1, 50000))

# Set nextOrderId to one
app.nextorderId = 1

# Start the socket in a thread
api_thread = threading.Thread(target=run_loop, daemon=True)
api_thread.start()

# Request contract details
app.reqContractDetails(1004, es_contract)

# Request pnl updates ----------------------> configure prod vs paper here (2 of 2)
app.reqPnL(1009, account['paper'], "")

# Request Market Data
app.reqMktData(1, es_contract, '', False, False, [])
time.sleep(2)

user_input = input("Press enter to trigger market buy order")

if user_input == "":
    order_quantity = app.order_quantity
    # Call the order_thread_function to place an order and start the order thread
    order_thread_function(es_contract, "BUY", "MKT", order_quantity, app)
    # Set start_time to current time
    app.start_time = datetime.now()

while not info["stop"]:
    time.sleep(1)  # Sleep interval to allow time for incoming price data

app.disconnect()
