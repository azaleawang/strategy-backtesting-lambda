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

COPY . /var/task/
RUN pip3 install -r /var/task/requirements.txt
# COPY lambda_function.py ./

CMD ["lambda_function.lambda_handler"]