from ibapi.client import EClient
from ibapi.ticktype import TickTypeEnum
from ibapi.wrapper import EWrapper
from LoBagola_functions import *

info = {"stop": False}

# configurable contract
es_contract = create_contract('ES', 'FUT', 'CME', "20230317")


class IBapi(EWrapper, EClient):

    def __init__(self):
        EClient.__init__(self, self)
        self.order_count = 0
        self.loop_count = 0
        self.price_list = []
        self.min_tick = 0
        self.last_fill_price = 0
        self.first_fill_price = 0
        self.start_time = 0
        self.is_order_filled = False
        self.per_contract_pnl = 0
        self.last_order_type = ""
        self.last_order_action = ""
        self.current_price = ""
        # configurable variables
        self.target_pnl = 1000
        self.wait_time = 100000
        self.order_quantity = 1

    def tickPrice(self, reqId, tickType, price, attrib):
        if self.loop_count == 0:
            check_connection(price)

        if self.loop_count > 1:
            # save the realtime price updates to a global variable
            self.current_price = price

            if tickType == TickTypeEnum.ASK and reqId == 1:
                self.price_list.append(price)
                # print(f"ask is {price}")

                if is_even(self.order_count) and self.order_count != 0:
                    create_buy_order(price, self.first_fill_price,
                                     self.last_fill_price,
                                     self.min_tick, self.is_order_filled
                                     , es_contract,
                                     self.order_quantity * 2, self.start_time,
                                     self.wait_time,
                                     self)

            if tickType == TickTypeEnum.BID and reqId == 1:
                self.price_list.append(price)
                # print(f"bid is {price}")

                if not is_even(self.order_count):
                    create_sell_order(price, self.first_fill_price,
                                      self.last_fill_price,
                                      self.min_tick, self.is_order_filled,
                                      es_contract,
                                      self.order_quantity * 2,
                                      self.start_time, self.wait_time,
                                      self)

        self.loop_count += 1

    def nextValidId(self, orderId: int):
        super().nextValidId(orderId)
        self.nextorderId = orderId
        # print('The next valid order id is: ', self.nextorderId)

    def orderStatus(self, orderId, status, filled, remaining, avgFullPrice, permId, parentId, lastFillPrice, clientId,
                    whyHeld, mktCapPrice):
        print('orderStatus - orderid:', orderId, 'status:', status, 'filled', filled, 'remaining', remaining,
              'lastFillPrice', lastFillPrice)
        self.last_fill_price = lastFillPrice
        if self.order_count == 1:
            self.first_fill_price = lastFillPrice
            print(f'---------> axis price is {self.first_fill_price} <---------')
        if status == 'Filled':
            self.is_order_filled = True

            # print(self.is_order_filled)
            self.start_time = datetime.now()
            # print('start_time is ', self.start_time)

    def openOrder(self, orderId, contract, order, orderState):
        # save the order action i.e BUY or SELL and
        #  order type i.e MKT, STP LMT to global variables respectively
        self.last_order_action = order.action
        self.last_order_type = order.orderType

        print('openOrder id:', orderId, contract.symbol, contract.secType, '@', contract.exchange, ':', order.action,
              order.orderType, order.totalQuantity, orderState.status)

    def execDetails(self, reqId, contract, execution):
        print('Order Executed: ', reqId, contract.symbol, contract.secType, contract.currency, execution.execId,
              execution.orderId, execution.shares, execution.lastLiquidity)

    def contractDetails(self, reqId, contractDetails):
        # print(contractDetails.minTick)
        self.min_tick = contractDetails.minTick

    def contractDetailsEnd(self, reqId):
        print("Contract details found! - ", reqId)

    def pnl(self, reqId, dailyPnL, unrealizedPnL, realizedPnL):
        # @TODO
        # if pnl equals certain number,
        # cancel open order by calling
        # self.cancelOrder(orderId)
        # and making a new trade
        # alternatively, we can modify make_order function and order_thread_function
        # to accept an optional orderId argument which has a default value of app.nextorderId
        # and call order_thread_function with the parameters to be modified

        self.per_contract_pnl = dailyPnL / self.order_quantity
        current_order_id = self.nextorderId - 1

        if self.per_contract_pnl > self.target_pnl:
            if self.last_order_action == "BUY":
                stop_price = self.current_price + (4 * self.min_tick)
                limit_price = self.current_price + (8 * self.min_tick)
                print("+++++++++++++++++++++++++++++")
                print("BUY stop limit order modified")
                print("+++++++++++++++++++++++++++++")
            elif self.last_order_action == "SELL":
                stop_price = self.current_price - (4 * self.min_tick)
                limit_price = self.current_price - (8 * self.min_tick)
                print("------------------------------")
                print("SELL stop limit order modified")
                print("------------------------------")

            # modify the last order placed
            order_thread_function(es_contract, self.last_order_action, self.last_order_type, self.order_quantity, self,
                                  stop_price, limit_price, current_order_id)
            # exit program
            self.disconnect()

        elif self.per_contract_pnl < -5000:
            if self.current_price > self.first_fill_price:
                make_order(es_contract, "BUY", "MKT", self.order_quantity, self, 0, 0, "")
                print("BUY stop conditions met")
            elif self.current_price < self.first_fill_price:
                make_order(es_contract, "SELL", "MKT", self.order_quantity, self, 0, 0, "")
                print("SELL stop condition met")

            self.disconnect()

        print("daily pnl    = ", int(dailyPnL))
        print("contract pnl = ", int(self.per_contract_pnl), "/", int(self.target_pnl))
