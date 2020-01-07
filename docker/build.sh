DIR=$(dirname "$(readlink -f "$0")")
docker build -t drf-tdd:latest $DIR
