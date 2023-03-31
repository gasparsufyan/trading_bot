from binance import Client
from binance.enums import *
import time
import config
import requests
import json

client = Client(config.api_key, config.api_secret)
pTime = time.time()

if client.ping() == {}:
    print('connection successful')

print(client.get_asset_balance(asset='BUSD')['free'])

#print(help(client.create_order(symbol='BTCUSDC')))

print(f'time passed is {time.time() - pTime}')


def retrieve_messages(channelid, authorization):

    headers = {
        'authorization': authorization
    }
    r = requests.get(f'https://discord.com/api/v9/channels/{channelid}/messages', headers=headers)
    parse_json = json.loads(r.text)

    for value in parse_json:
        alert = value['content']
        alert = str(alert).upper().split()
        return alert


message = retrieve_messages('915859059691888640', config.authorization)

