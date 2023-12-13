FROM public.ecr.aws/lambda/python:3.8

# COPY requirements.txt ./
# 安裝 TA-Lib 的 dependencies
RUN yum -y install wget tar gcc-c++ gzip make

# 下載並安裝 TA-Lib
RUN wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz && \
    tar -xzf ta-lib-0.4.0-src.tar.gz && \
    cd ta-lib && \
    ./configure --prefix=/usr && \
    make && \
    make install

# 清理安裝檔案
RUN rm -R ta-lib ta-lib-0.4.0-src.tar.gz

COPY requirements.txt /var/task/

RUN pip3 install --no-cache-dir -r /var/task/requirements.txt

# 將修改的plot函數取代原本的檔案
COPY _plotting.py /var/lang/lib/python3.8/site-packages/backtesting/_plotting.py

# COPY lambda_function.py ./
COPY lambda_function.py history.py config.py /var/task/

CMD ["lambda_function.lambda_handler"]