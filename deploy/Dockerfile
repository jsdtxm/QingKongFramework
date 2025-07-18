FROM python:3.12-slim-bookworm AS builder

RUN sed -e 's|^URIs: http://deb.debian.org/debian-security|URIs: http://mirrors.tuna.tsinghua.edu.cn/debian-security|g' \
    -e 's|^URIs: http://deb.debian.org/debian|URIs: http://mirrors.tuna.tsinghua.edu.cn/debian|g' \
    -i  /etc/apt/sources.list.d/debian.sources

RUN pip config set global.index-url https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple

RUN apt update
RUN apt install -y gcc wget

RUN pip install wheel

WORKDIR /app/

RUN wget --user-agent="pip/23.3.1 python/3.10" \
    https://mirrors.tuna.tsinghua.edu.cn/pypi/web/packages/50/1e/67ec08cde59222d275909a508ad2db1ac8c20a72404a189dca31e242179b/asyncmy-0.2.9.tar.gz && \
    tar -xzf asyncmy-0.2.9.tar.gz

RUN sed -i '/def build(setup_kwargs):/a \    extra_compile_args = ["-Os", "-flto", "-ffast-math"]' /app/asyncmy-0.2.9/build.py && \
    sed -i '/compiler_directives={"language_level": 3},/a \                compile_time_env={"EXTRA_COMPILE_ARGS": extra_compile_args},' /app/asyncmy-0.2.9/build.py && \
    echo '    for ext in setup_kwargs["ext_modules"]:' >> /app/asyncmy-0.2.9/build.py && \
    echo '        ext.extra_compile_args.extend(extra_compile_args)' >> /app/asyncmy-0.2.9/build.py && \
    echo '        ext.extra_link_args.extend(["-flto", "-s"])' >> /app/asyncmy-0.2.9/build.py

WORKDIR /app/asyncmy-0.2.9
RUN pip install .
RUN find /usr/local/lib/python3.12 -type d -name '__pycache__' -exec rm -r {} +

FROM python:3.12-slim-bookworm

LABEL maintainer="Xia Min <jsdtxm@gmail.com>"
RUN cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime

RUN sed -e 's|^URIs: http://deb.debian.org/debian-security|URIs: http://mirrors.tuna.tsinghua.edu.cn/debian-security|g' \
    -e 's|^URIs: http://deb.debian.org/debian|URIs: http://mirrors.tuna.tsinghua.edu.cn/debian|g' \
    -i  /etc/apt/sources.list.d/debian.sources

RUN pip config set global.index-url https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple && \
    find /usr/local/lib/python3.12 -type d -name '__pycache__' -exec rm -r {} +

WORKDIR /app/
ENV PYTHONPATH=/app

COPY --from=builder /usr/local/lib/python3.12/site-packages/asyncmy  /usr/local/lib/python3.12/site-packages/asyncmy
COPY --from=builder /usr/local/lib/python3.12/site-packages/asyncmy-0.2.9.dist-info  /usr/local/lib/python3.12/site-packages/asyncmy-0.2.9.dist-info

COPY ./deploy/remove_dev_requirements.sh /usr/local/bin/remove-dev-requirements
COPY ./requirements.txt /app

RUN remove-dev-requirements requirements.txt requirements.txt.clean && \
    pip install --no-cache-dir -r requirements.txt.clean && \
    find /usr/local/lib/python3.12 -type d -name '__pycache__' -exec rm -r {} + && \
    rm requirements.txt.clean

COPY ./fastapp /app/fastapp
COPY ./common /app/common
COPY ./manage.py /app/

EXPOSE 8000

CMD ["python", "manage.py", "about"]
