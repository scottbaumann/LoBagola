from LoBagola_IBapi import *
from LoBagola_functions import *
import random

info = {"stop": False}
account = input('IB account number: ')
socket = int(input('socket (7497 is paper, 7496 is prod): '))


def run_loop():
    app.run()


# Connect to IB -----------------------------> configure prod vs paper here (1 of 2)
app = IBapi()
app.connect('127.0.0.1', socket, random.randint(1, 50000))

# Set nextOrderId to one
app.nextorderId = 1

# Start the socket in a thread
api_thread = threading.Thread(target=run_loop, daemon=True)
api_thread.start()

# Request contract details
app.reqContractDetails(1004, fut_contract)

# Request pnl updates ----------------------> configure prod vs paper here (2 of 2)
app.reqPnL(1009, account, "")

# Request Market Data
app.reqMktData(1, fut_contract, '', False, False, [])
time.sleep(5)

user_input = input("Press enter to trigger market buy order")

if user_input == "":
    order_quantity = app.order_quantity
    # Call the order_thread_function to place an order and start the order thread
    order_thread_function(fut_contract, "BUY", "MKT", order_quantity, app)
    # Set start_time to current time
    app.start_time = datetime.now()

while not info["stop"]:
    time.sleep(1)  # Sleep interval to allow time for incoming price data

app.disconnect()
