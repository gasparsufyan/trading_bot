import websocket
import json
import time
from datetime import datetime


ticker = 'btcbusd'
timeFrame = '1h'

def get_time():
    dt_string = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return dt_string

def set_websocket(ticker, timeFrame):
    socket = f'wss://stream.binance.com:9443/ws/{ticker}@kline_{timeFrame}'
    ws = websocket.WebSocketApp(socket, on_open=on_open, on_close=on_close, on_message=on_message)
    return ws

def on_open(ws):
    print('Opened Connection')

def on_close(ws, close_status_code, close_msg):
    print("Connection Closed")

def on_message(ws, message):
    json_message = json.loads(message)
    candle = json_message['k']
    close = float(candle['c'])
    print(close)
    dTime = time.time() - sTime
    print(get_time())

    if dTime > 15:
        ws.close()


#ws = websocket.WebSocketApp(socket, on_open=on_open, on_close=on_close, on_message=on_message)
sTime = time.time()
ws = set_websocket(ticker, timeFrame)
ws.run_forever()
