FROM python:3.11
ENV PYTHONUNBUFFERED 1
RUN apt-get update && \
    apt-get install -y nginx postgresql-client && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /code
COPY requirements.txt manage.py election docker/entrypoint.sh .
COPY nginx.conf /etc/nginx/conf.d/default.conf

RUN python -m pip install -U pip && \
    python -m pip install -r requirements.txt

EXPOSE 8877
CMD bash entrypoint.sh
