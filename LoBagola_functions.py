from ibapi.contract import Contract
from ibapi.tag_value import TagValue
from ibapi.order import *
import threading
import time
import random
from datetime import datetime


# determines if passed value is an even number
def is_even(val):
    """
    Returns True if passed value is an integer
    """
    if val % 2 == 0:
        return True
    return False


# Check if API is connected
def check_connection(price):
    """
    Checks if API is connected successfully
    """
    while True:
        if price > 1:
            print("connected")
            break
        else:
            print("waiting for connection...")
            time.sleep(1)  # Sleep interval to allow time for connection to server
    return


# creates a new contract
def create_contract(symbol, sec_type, exchange, trade_date):
    """
    Creates a new contract
    """
    # Create contract object
    contract = Contract()
    contract.symbol = symbol
    contract.secType = sec_type
    contract.exchange = exchange
    contract.currency = 'USD'
    contract.lastTradeDateOrContractMonth = trade_date

    return contract


# setup new thread to place an order
def order_thread_function(contract, action, order_type, quantity, app, stop_price=0, limit_price=0, order_id=""):
    """
    Creates an order in a new thread and increment number of orders made
    """
    new_order_thread = threading.Thread(target=make_order,
                                        args=(contract, action, order_type, quantity, app, stop_price,
                                              limit_price, order_id),
                                        daemon=True)
    app.is_order_filled = False
    new_order_thread.start()
    app.order_count += 1


# BUY order conditions

def create_buy_order(price, first_fill_price, last_fill_price, min_tick, is_order_filled,
                     es_contract, order_quantity, start_time,
                     wait_time, app):
    time_diff = datetime.now() - start_time

    """
    Places a BUY Stop limit order if current price is less than first fill price
    minus three times the minimum tick size, otherwise
    if the wait time is exceeded and price is greater than
    first fill price it makes a MKT BUY order

    it prints countdown timer to determine wait time
    """

    if price < (first_fill_price - (8 * min_tick)) and last_fill_price != 0:
        stop_price = (first_fill_price - (4 * min_tick))
        limit_price = first_fill_price

        if is_order_filled:
            order_thread_function(es_contract, "BUY", "STP LMT", order_quantity, app, stop_price, limit_price)
            print("++++++++++++++++++++++++++")
            print("BUY STP LMT conditions met")
            print("++++++++++++++++++++++++++")
    elif time_diff.total_seconds() >= wait_time and price > (first_fill_price + (2 * min_tick)):
        if is_order_filled:
            order_thread_function(es_contract, "BUY", "MKT", order_quantity, app)
            print("++++++++++++++++++++++")
            print("BUY MKT conditions met")
            print("++++++++++++++++++++++")
    else:
        if is_order_filled and time_diff.total_seconds() < wait_time:
            print("Elapsed time = ", int(time_diff.total_seconds()), "/", wait_time)


# SELL order conditions

def create_sell_order(price, first_fill_price, last_fill_price, min_tick, is_order_filled,
                      es_contract, order_quantity, start_time,
                      wait_time, app):
    time_diff = datetime.now() - start_time

    """
    Places a SELL Stop limit order if current price is less than first fill price
    minus three times the minimum tick size, otherwise
    if the wait time is exceeded and price is greater than
    first fill price it makes a MKT BUY order

    it prints countdown timer to determine wait time
    """

    if price > (first_fill_price + (8 * min_tick)) and last_fill_price != 0:
        stop_price = (first_fill_price + (4 * min_tick))
        limit_price = first_fill_price
        if is_order_filled:
            order_thread_function(es_contract, "SELL", "STP LMT", order_quantity, app, stop_price, limit_price)
            print("---------------------------")
            print("SELL STP LMT conditions met")
            print("---------------------------")
    elif time_diff.total_seconds() >= wait_time and price < first_fill_price:
        if is_order_filled:
            order_thread_function(es_contract, "SELL", "MKT", order_quantity, app)
            print("-----------------------")
            print("SELL MKT conditions met")
            print("-----------------------")
    else:
        if is_order_filled and time_diff.total_seconds() < wait_time:
            print("Elapsed time = ", int(time_diff.total_seconds()), "/", wait_time)


# Custom function to create and place an order
def make_order(contract, action, order_type, quantity, app, stop_price=0, limit_price=0, order_id=""):
    """
    This function creates and place a new order when called
    """
    # Create new order
    order = Order()
    order.action = action
    order.totalQuantity = quantity
    order.orderType = order_type

    """
    Conditions to check for the type of order being placed
    """
    if stop_price == 0:
        order.algoStrategy = 'Adaptive'
        order.algoParams = []
        order.algoParams.append(TagValue("adaptivePriority", "Patient"))
    elif order_type == "STP" and stop_price != 0:
        order.auxPrice = stop_price
    elif order_type == "STP LMT" and stop_price != 0 and limit_price != 0:
        order.auxPrice = stop_price
        order.lmtPrice = limit_price

    if order_id == "":
        order_id = app.nextorderId
    # This line places an order
    app.placeOrder(order_id, contract, order)
    # Increment nextOrderId by 1
    app.nextorderId += 1
