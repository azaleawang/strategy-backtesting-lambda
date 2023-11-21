from backtesting import Backtest
from history import history_data
from time import gmtime, strftime
import boto3
from config import res_attributes
import json, os, sys
import requests
import logging
import importlib.util

# event = {
#     "Records": [
#         {
#             "messageId": "19dd0b57-b21e-4ac1-bd88-01bbb068cb78",
#             "receiptHandle": "MessageReceiptHandle",
#             "body": '{"symbols": ["ETH/USDT"], "t_frame": "1h", "name": "SuperTrend", "s3_url": "https://my-trading-bot.s3.ap-northeast-1.amazonaws.com/backtest/strategy/"}',
#             "attributes": {
#                 "ApproximateReceiveCount": "1",
#                 "SentTimestamp": "1523232000000",
#                 "SenderId": "123456789012",
#                 "ApproximateFirstReceiveTimestamp": "1523232000001",
#             },
#             "messageAttributes": {},
#             "md5OfBody": "{{{md5_of_body}}}",
#             "eventSource": "aws:sqs",
#             "eventSourceARN": "arn:aws:sqs:us-east-1:123456789012:MyQueue",
#             "awsRegion": "us-east-1",
#         }
#     ]
# }


def lambda_handler(event, context):
    try:
        records = event["Records"]
        for record in records:
            body = json.loads(record.get("body"))
            print("record body", body)
            symbols = body.get("symbols", ["BTC/USDT"])
            t_frame = body.get("t_frame", "4h")
            since = body.get("since", "2018-01-01T00:00:00Z")
            default_type = body.get("default_type", "future")
            name = body.get("name", "RsiOscillator")
            s3_url = body.get("s3_url")
            strategy_path = download_file(s3_url + name + ".py", name)
            Strategy = import_class_from_source(strategy_path, name)
            params = body.get("params", {})

        # get history data
        df = history_data("binance", symbols, t_frame, since, default_type)

        if df.empty:
            raise ValueError("No data found")
        else:
            print("Data found", df.tail())

        result_json = run_strategy(df, Strategy, params, name, symbols, t_frame)
        url = "https://azaleasites.online/api/backtest/result"
        data = {"info": body, "result": result_json}
        response = requests.post(
            url, json=data, headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            try:
                print("server received backtest result\t", response.json())
            except ValueError as e:
                print("Response is not in JSON format:", e)
        else:
            print("Error:", response.status_code, response.text)
        return {"statusCode": 200, "data": data}

    except Exception as e:
        # log error到 CloudWatch
        logging.error("Error occurred during lambda execution", exc_info=True)

        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}


def run_strategy(data, strategy, params, name, symbols, t_frame):
    s3_fn = None
    bt = Backtest(data, strategy, cash=1_000_000, commission=0.002)
    backtest_result = bt.run(params = params)
    try:
        path = "/tmp/"
        filename = f"{name}_{'_'.join(symbols).replace('/', '-')}_{t_frame}_{strftime('%Y%m%d-%H%M%S', gmtime())}"
        bt.plot(filename=path + filename, resample=False, open_browser=False)
        print("plot ok")
        s3_fn = upload_s3(path=path, name=filename + ".html")
    except Exception as e:
        print(f"Error when potting or uploading plot: {e}")

    result_dict = {
        attr: getattr(backtest_result, attr, None) for attr in res_attributes
    }
    result_dict["plot"] = s3_fn
    result_json = json.dumps(result_dict, default=str, indent=4)
    return result_json


def download_file(url, local_filename):
    # Construct the full local path in the /tmp/ directory
    # local_path = os.path.join("/home/leah/lambda-upload/", local_filename + ".py")
    local_path = os.path.join("/tmp/", local_filename + ".py")
    # Send a GET request to the URL
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        # Write the file contents to a local file in /tmp/ directory
        with open(local_path, "wb") as f:
            f.write(response.content)
        print(f"File downloaded successfully to: {local_path}")
        return local_path
    else:
        logging.error(f"Failed to download file. Status code: {response.status_code}")


def import_class_from_source(path, classname):
    spec = importlib.util.spec_from_file_location(classname, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return getattr(module, classname)


def upload_s3(
    path: str = "/tmp/",
    name: str = "",
    s3_bucket: str = "my-trading-bot",
    s3_dir: str = "backtest/result/",
):
    s3 = boto3.resource("s3")
    with open(os.path.join(path, name), "rb") as data:
        s3.Bucket(s3_bucket).put_object(Key=s3_dir + name, Body=data)
        print(f"{s3_dir + name} uploaded!")
        return s3_dir + name


# lambda_handler(event, 2)
