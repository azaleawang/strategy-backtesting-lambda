from backtesting import Backtest
from history import history_data
from RsiOscillator import RsiOscillator
from config import res_attributes
import json
import requests
import logging
# event = {
#   "Records": [
#     {
#       "messageId": "19dd0b57-b21e-4ac1-bd88-01bbb068cb78",
#       "receiptHandle": "MessageReceiptHandle",
#       "body": "{\"symbols\": [\"ETH/USDT\"], \"t_frame\": \"1d\"}",
#       "attributes": {
#         "ApproximateReceiveCount": "1",
#         "SentTimestamp": "1523232000000",
#         "SenderId": "123456789012",
#         "ApproximateFirstReceiveTimestamp": "1523232000001"
#       },
#       "messageAttributes": {},
#       "md5OfBody": "{{{md5_of_body}}}",
#       "eventSource": "aws:sqs",
#       "eventSourceARN": "arn:aws:sqs:us-east-1:123456789012:MyQueue",
#       "awsRegion": "us-east-1"
#     }
#   ]
# }

def lambda_handler(event, context):   
    try:
        records = event['Records']
        for record in records:
            body = json.loads(record.get("body"))
            print("record body", body)
            symbols = body.get('symbols', ['BTC/USDT'])
            t_frame = body.get('t_frame', '4h')
            since = body.get('since', '2023-01-01T00:00:00Z')
            default_type = body.get('default_type', 'future')

        # get history data
        df = history_data('binance', symbols, t_frame, since, default_type, True)
        if df.empty:
            raise ValueError("No data found")
        else:
            print("Data found", df.tail())

        result_json = run_strategy(df, RsiOscillator)
        url = "https://azaleasites.online/api/backtest/result"
        data = { "info": body, "result": result_json }
        response = requests.post(url, json=data, headers={'Content-Type': 'application/json'})
        if response.status_code == 200:
            try:
                print("server received backtest result\t", response.json())
            except ValueError as e:
                print("Response is not in JSON format:", e)
        else:
            print("Error:", response.status_code, response.text)
        return {
            'statusCode': 200,
            'data': data
        }
    
    except Exception as e:
        # log error到 CloudWatch
        logging.error("Error occurred during lambda execution", exc_info=True)

        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def run_strategy(data, strategy):
    bt = Backtest(data, strategy, cash=1_000_000, commission=.002)
    backtest_result = bt.run()

    result_dict = {attr: getattr(backtest_result, attr, None) for attr in res_attributes}
    result_json = json.dumps(result_dict, default=str, indent=4)
    return result_json
    
# lambda_handler(event, 2)