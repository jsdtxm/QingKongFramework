FROM python:3.12-alpine AS builder

RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apk/repositories
RUN pip config set global.index-url https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple

RUN apk add gcc musl-dev
RUN pip install wheel

WORKDIR /app/

RUN pip wheel asyncmy==0.2.9
RUN pip install /app/asyncmy-0.2.9-cp312-cp312-musllinux_1_2_x86_64.whl
RUN find /usr/local/lib/python3.12 -type d -name '__pycache__' -exec rm -r {} +

FROM python:3.12-alpine

LABEL maintainer="Xia Min <jsdtxm@gmail.com>"
RUN cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime

RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apk/repositories
RUN pip config set global.index-url https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple && \
    find /usr/local/lib/python3.12 -type d -name '__pycache__' -exec rm -r {} +

WORKDIR /app/
ENV PYTHONPATH=/app

COPY --from=builder /usr/local/lib/python3.12/site-packages/asyncmy  /usr/local/lib/python3.12/site-packages/asyncmy
COPY --from=builder /usr/local/lib/python3.12/site-packages/asyncmy-0.2.9.dist-info  /usr/local/lib/python3.12/site-packages/asyncmy-0.2.9.dist-info

COPY ./requirements.txt /app

RUN pip install --no-cache-dir -r requirements.txt && \
    find /usr/local/lib/python3.12 -type d -name '__pycache__' -exec rm -r {} +

COPY ./libs /app/libs
COPY ./common /app/common
COPY ./manage.py /app/

EXPOSE 8000

CMD ["python", "manage.py", "about"]
