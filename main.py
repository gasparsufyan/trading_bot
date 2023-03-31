from binance.client import Client
from binance.enums import *
from datetime import datetime
import time
import websocket
import json
import requests
import math
import config

global CryptoCurrency, margin, time_taken

client = Client(config.api_key, config.api_secret)

def round_decimals_down(number: float, decimals: int = 2):
    if decimals == 0:
        return math.floor(number)
    factor = 10 ** decimals
    return math.floor(number * factor) / factor


def get_time():
    dt_string = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(dt_string)
    return dt_string


def retrieve_messages(channelid, authorization):

    headers = {
        'authorization': authorization
    }
    r = requests.get(f'https://discord.com/api/v9/channels/{channelid}/messages', headers=headers)
    parse_json = json.loads(r.text)

    for value in parse_json:
        alert = value['content']
        alert = str(alert).upper().split()

        if len(alert[1]) != 3:
            print('Length of second item was not three characters')
            return None

        if len(alert) == 3:
            dict = {
                'protocol': alert[0],
                'side': alert[1],
                'ticker': alert[2]
            }
            return dict

        else:
            return alert


def asset_balance():
    quote = float(client.get_asset_balance(asset='BUSD')['free'])
    return quote


def separate(ticker):
    length = len(ticker) - 4
    dict = {
        'asset': ticker[0:length],
        'base': ticker[length: len(ticker)]
    }
    return dict


class Coin:

    def __init__(self, asset, base):
        self.ticker = asset + base
        self.asset = asset
        self.base = base
        self.initial_value = self.get_base_asset()
        self.precision = self.precision_step()
        self.start = self.initial_value
        self.start_price = self.get_price()

    def precision_step(self):
        sym_info = client.get_symbol_info(self.ticker)
        filters = sym_info['filters']
        for f in filters:
            if f['filterType'] == 'LOT_SIZE':
                step_size = float(f['stepSize'])
                precision = int(round(-math.log(step_size, 10), 0))
                return precision

    def get_coin_quantity(self):
        coin_quantity = round_decimals_down(float((self.get_budget() / self.get_price())), self.precision)
        return coin_quantity

    def get_bal(self):
        bal = float(client.get_asset_balance(asset=self.asset)['free'])
        return bal

    def get_base_asset(self):
        base_value = float(client.get_asset_balance(asset=self.base)['free'])
        return base_value

    def get_amount(self):
        amount = round_decimals_down(self.get_bal(), self.precision)
        return amount

    def get_budget(self):
        budget = round_decimals_down(float(client.get_asset_balance(asset=self.base)["free"]), self.precision)
        return budget

    def get_price(self):
        price = float(client.get_avg_price(symbol=self.ticker)['price'])
        return price

    def amend_start(self):
        self.start = self.get_bal() * self.get_price()

    def asset_value(self):
        current = float(self.get_bal() * self.get_price())
        return current

    def buy(self):
        try:
            order = client.order_market_buy(
                symbol=self.ticker,
                quantity=(self.get_coin_quantity()))
        except Exception as e:
            print("An exception occured - {}".format(e))
            return False
        print('Trade opened at BTC price of ${:,.2f}'.format(self.get_price()))
        self.start_price = self.get_price()

    def sell(self):
        try:
            order = client.order_market_sell(
                symbol=self.ticker,
                quantity=(self.get_amount()))
        except Exception as e:
            print("An exception occured - {}".format(e))
            return False
        print('Trade closed at BTC price of ${:,.2f}'.format(self.get_price()))
        print('Current value of asset is ${:,.2f}'.format(float(self.get_base_asset())))
        print('Current profit is {}'.format(self.get_profit()))

    def trade_open(self):

        if self.get_base_asset() > 10:
            return False
        return True

    def get_profit(self):
        prof = ((self.get_price() - self.start) / self.start) * 100
        prof = float(prof)
        prof = "{:.0%}".format(prof)
        return prof


def set_websocket(ticker, timeFrame):
    socket = f'wss://stream.binance.com:9443/ws/{ticker}@kline_{timeFrame}'
    ws = websocket.WebSocketApp(socket, on_open=on_open, on_close=on_close, on_message=on_message)
    return ws


def on_open(ws):
    print('Opened Connection')

def on_close(ws, close_status_code, close_msg):
    print("Connection Closed")


def on_message(ws, message):
    global start_price, token, sTime
    json_message = json.loads(message)
    candle = json_message['k']
    close = float(candle['c'])
    print(close)

    if asset_balance() > 10:
        CryptoCurrency.buy()
        start_price = close
        time.sleep(10)

    elif asset_balance() < 10:
        if close >= (start_price*margin):
            token.sell()
        elif (time.time()-sTime) > time_taken:
            token.sell()


while True:
    try:
        directory = retrieve_messages('915859059691888640', config.authorization)
        print('code is running')
        get_time()
    except Exception as e:
        print(f"An exception occurred - {e}")
        get_time()
        time.sleep(90)

    if directory is None:
        time.sleep(5)
        continue

    else:
        try:
            ordered = separate(directory['ticker'])
        except Exception as e:
            print(f"An exception occurred - {e}")
            get_time()
            continue

        directory.update(ordered)
        if directory['side'] == 'BUY' and asset_balance() > 10:
            CryptoCurrency = Coin(directory['asset'], directory['base'])
            if directory['protocol'] == 'PROTSCALP':
                margin = 1.005
                time_taken = 7200
            elif directory['protocol'] == 'PROTPORT':
                margin = 1.05
                time_taken = 28800

            ws = set_websocket(directory['ticker'].lower(), '1h')

            try:
                ws.run_forever()
            except Exception as e:
                print(f"An exception occurred - {e}")
                get_time()
                time.sleep(5)
                continue