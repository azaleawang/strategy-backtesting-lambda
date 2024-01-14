import ccxt
import pandas as pd

def history_data(
    exch="binance",
    symbols=["BTC/USDT"],
    t_frame="4h",
    since="2017-01-01T00:00:00Z",
    default_type="future",
):
    # Initialize exchange
    try:
        exchange = getattr(ccxt, exch)(
            {
                "enableRateLimit": True,
                "options": {
                    "defaultType": default_type,
                },
            }
        )
        
    except AttributeError:
        print(f'Exchange "{exch}" not found.')
        quit()

    # Check for OHLCV support
    if not exchange.has["fetchOHLCV"]:
        print(f"{exch} does not support OHLCV data.")
        quit()

    # Load markets
    exchange.load_markets()

    # Define header for DataFrame
    header = ["Timestamp", "Open", "High", "Low", "Close", "Volume"]
    ohlcv_all = pd.DataFrame()
    from_timestamp = exchange.parse8601(since)
    now = exchange.milliseconds()

    # Fetch data for each symbol
    for symbol in symbols:
        while from_timestamp < now:
            ohlcvs = exchange.fetch_ohlcv(symbol, t_frame, from_timestamp)
            if not len(ohlcvs):
                break
            ohlcv_all = pd.concat(
                [ohlcv_all, pd.DataFrame(ohlcvs, columns=header).set_index("Timestamp")]
            )
            from_timestamp = ohlcvs[-1][0] + exchange.parse_timeframe(t_frame) * 1000

    # Convert timestamp to datetime
    ohlcv_all.index = pd.to_datetime(ohlcv_all.index, unit="ms")
    
    return ohlcv_all
