import ccxt
import pandas as pd

def history_data(exch='binance', symbols=['BTC/USDT'], t_frame='1h', 
                    since='2023-01-01T00:00:00Z', default_type='future', sandbox_mode=False):        
    
    # Initialize exchange
    try:
        exchange = getattr(ccxt, exch)(
            {
                'enableRateLimit': True,
                'options': {
                    'defaultType': default_type,
                }
            }
        )

        if hasattr(exchange, 'set_sandbox_mode'):
            exchange.set_sandbox_mode(sandbox_mode)

    except AttributeError:
        print(f'Exchange "{exch}" not found.')
        quit()

    # Check for OHLCV support
    if not exchange.has["fetchOHLCV"]:
        print(f'{exch} does not support OHLCV data.')
        quit()

    # Load markets
    exchange.load_markets()

    # Define header for DataFrame
    header = ['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume']
    ohlcv_all = pd.DataFrame()
    from_timestamp = exchange.parse8601(since)
    now = exchange.milliseconds()
    # Function to fetch OHLCV

    # Fetch data for each symbol
    for symbol in symbols:
        while from_timestamp < now:
            print('Fetching candles starting from', exchange.iso8601(from_timestamp))
            ohlcvs = exchange.fetch_ohlcv(symbol, t_frame, from_timestamp)
            if not len(ohlcvs):
                break
            ohlcv_all = pd.concat([ohlcv_all, pd.DataFrame(ohlcvs, columns=header).set_index('Timestamp')])
            from_timestamp = ohlcvs[-1][0] + exchange.parse_timeframe(t_frame) * 1000


    # Convert timestamp to datetime
    ohlcv_all.index = pd.to_datetime(ohlcv_all.index, unit='ms')

    return ohlcv_all
    