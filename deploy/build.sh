docker build -t qingkong_framework:latest-py3.12-alpine --progress plain -f deploy/Dockerfile .

docker build -t qingkong_framework:latest-py3.12-bookworm --progress plain -f deploy/Dockerfile.debian .