import os
import time
import ccxt
import ta
import pandas as pd
from dotenv import load_dotenv

# Load API keys from environment variables
load_dotenv()
API_KEY = os.getenv('BYBIT_API_KEY')
API_SECRET = os.getenv('BYBIT_API_SECRET')

# Setup Bybit client
exchange = ccxt.bybit({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'options': {
        'defaultType': 'spot',  # Important! Use spot, not futures
    }
})

symbol = 'BTC/USDT'
timeframe = '1m'  # You can change to 5m, 15m, 1h
ma_period = 20
rsi_period = 14
rsi_overbought = 70
rsi_oversold = 30

def fetch_data(symbol, timeframe, limit=100):
    bars = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    return df

def calculate_indicators(df):
    df['MA'] = df['close'].rolling(ma_period).mean()
    df['RSI'] = ta.momentum.RSIIndicator(df['close'], window=rsi_period).rsi()
    return df

def check_candle_pattern(df):
    # Basic bullish engulfing pattern
    if len(df) < 2:
        return False

    prev = df.iloc[-2]
    current = df.iloc[-1]

    is_bullish_engulfing = (
        current['close'] > current['open'] and
        prev['close'] < prev['open'] and
        current['close'] > prev['open'] and
        current['open'] < prev['close']
    )

    return is_bullish_engulfing

def place_order(symbol, side, amount):
    try:
        order = exchange.create_order(
            symbol=symbol,
            type='market',
            side=side,
            amount=amount
        )
        print(f"Order successful: {order}")
    except Exception as e:
        print(f"Order failed: {e}")

def main():
    while True:
        try:
            df = fetch_data(symbol, timeframe)
            df = calculate_indicators(df)

            current_close = df['close'].iloc[-1]
            current_ma = df['MA'].iloc[-1]
            current_rsi = df['RSI'].iloc[-1]

            bullish_candle = check_candle_pattern(df)

            print(f"Price: {current_close}, MA: {current_ma}, RSI: {current_rsi}")

            # Example Strategy
            if current_close > current_ma and current_rsi < rsi_oversold and bullish_candle:
                print("Buy signal!")
                place_order(symbol, 'buy', 0.00017)  # Example amount
            elif current_close < current_ma and current_rsi > rsi_overbought:
                print("Sell signal!")
                place_order(symbol, 'sell', 0.00017)  # Example amount

            time.sleep(60)  # Wait 1 minute
        except Exception as e:
            print(f"Error in main loop: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()
