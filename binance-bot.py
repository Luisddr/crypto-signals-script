import time
import pandas as pd
from binance.client import Client
from binance.exceptions import BinanceAPIException
import csv
import datetime
import requests

api_key = 'TU_API_KEY'
api_secret = 'TU_API_SECRET'
client = Client(api_key, api_secret)

def calculate_sma(data, window):
    return data.rolling(window=window).mean()

def write_to_csv(signal, price, sl, tp):
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    with open('signals.csv', 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([timestamp, signal, price, sl, tp])

while True:
    try:
        # Obtén los datos más recientes
        klines = client.get_historical_klines('XRPUSDT', Client.KLINE_INTERVAL_15MINUTE, "1 day ago UTC")
        df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

        if len(df) < 50:
            print(f"Solo se obtuvieron {len(df)} datos. No son suficientes para calcular las medias móviles. Intentando de nuevo...")
            time.sleep(2*60)  # espera un segundo antes de la siguiente solicitud
            continue

        # Calcula las medias móviles
        df['close'] = df['close'].astype(float)
        df['ma20'] = calculate_sma(df['close'], 20)
        df['ma50'] = calculate_sma(df['close'], 50)
        df['ma200'] = calculate_sma(df['close'], 200)

        
        buy_signals = (df['ma20'].shift(1) < df['ma50'].shift(1)) & (df['ma20'] > df['ma50'])
        sell_signals = (df['ma20'].shift(1) > df['ma50'].shift(1)) & (df['ma20'] < df['ma50'])

        current_price = df['close'].iloc[-1]
        stop_loss = current_price * 0.97  # 1.5% debajo del precio actual
        take_profit = current_price * 1.03 

        
        if buy_signals.iloc[-1]: #and float(client.get_asset_balance(asset='USDT')['free']) > some_value:  # Reemplaza "some_value" con la cantidad mínima que deseas mantener en USDT
            #order = client.order_market_buy(symbol='BTCUSDT', quantity=0.001)
            print("buy signal")
            stop_loss = round(current_price * 0.97, 4)  # 1.5% debajo del precio actual
            take_profit = round(current_price * 1.03, 4) 
            write_to_csv('buy', current_price, stop_loss, take_profit)
            response = requests.get(f'https://crypto-bot-production.up.railway.app/xrp-usdt?type=buy&price={current_price}')
            print(response.status_code)
        elif sell_signals.iloc[-1]: # and float(client.get_asset_balance(asset='BTC')['free']) > some_value:  # Reemplaza "some_value" con la cantidad mínima que deseas mantener en BTC
            #order = client.order_market_sell(symbol='BTCUSDT', quantity=0.001)
            print("sell signal")
            take_profit = round(current_price * 0.97, 4)  # 1.5% debajo del precio actual
            stop_loss = round(current_price * 1.03, 4) 
            write_to_csv('sell', current_price, stop_loss, take_profit)
            response = requests.get(f'https://crypto-bot-production.up.railway.app/xrp-usdt?type=sell&price={current_price}')
            print(response.status_code)
        else:
            print("no signals")
        # Duerme durante un minuto antes de volver a verificar
        time.sleep(2*60)

    except BinanceAPIException as e:
        if e.status_code == 429:
            # Si recibimos un HTTP 429, hemos alcanzado el límite de solicitudes.
            # Espera los segundos sugeridos en la cabecera 'Retry-After'
            retry_after = e.response_headers.get('Retry-After')
            if retry_after is not None:
                time.sleep(int(retry_after))
            else:
                # Si 'Retry-After' no está disponible, espera un tiempo predeterminado
                time.sleep(1)
        elif e.status_code == 418:
            # Si recibimos un HTTP 418, hemos sido baneados por hacer demasiadas solicitudes.
            # Espera un tiempo más largo antes de volver a intentar.
            time.sleep(60)
        else:
            raise  # Si es cualquier otra excepción, simplemente lánzala de nuevo




