from backtesting import Backtest
from history import history_data
from RsiOscillator import RsiOscillator
from config import res_attributes
import json
def lambda_handler(event, context):   
    df = history_data(symbols=['BTC/USDT'], t_frame='4h', since='2022-01-01T00:00:00Z')
    if df.empty:
        raise ValueError("No data found")
    else:
        print("Data found")
        print(df.tail())

    result_json = run_strategy(df, RsiOscillator)
    return result_json

def run_strategy(data, strategy):
    bt = Backtest(data, strategy, cash=1_000_000, commission=.002)
    backtest_result = bt.run()
    print(backtest_result)

    result_dict = {attr: getattr(backtest_result, attr, None) for attr in res_attributes}
    result_json = json.dumps(result_dict, default=str, indent=4)
    return result_json
    
# lambda_handler(1,2)