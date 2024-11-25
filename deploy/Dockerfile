FROM python:3.12-alpine as builder

RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apk/repositories
RUN pip config set global.index-url https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple

RUN apk add gcc musl-dev
RUN pip install wheel

WORKDIR /app/

RUN pip wheel asyncmy==0.2.9

FROM python:3.12-alpine

LABEL maintainer="Xia Min <jsdtxm@gmail.com>"
RUN cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime

RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apk/repositories
RUN pip config set global.index-url https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple

WORKDIR /app/
ENV PYTHONPATH=/app

COPY --from=builder /app/asyncmy-0.2.9-cp312-cp312-musllinux_1_2_x86_64.whl /app/
RUN pip install /app/asyncmy-0.2.9-cp312-cp312-musllinux_1_2_x86_64.whl

COPY ./requirements.txt /app

RUN pip install --no-cache-dir -r requirements.txt

COPY ./libs /app/libs
COPY ./common /app/common
COPY ./manage.py /app/

CMD ["python", "manage.py", "about"]
