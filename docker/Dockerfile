FROM python:3.11
ENV PYTHONUNBUFFERED 1
RUN mkdir /code
WORKDIR /code
RUN apt-get update && apt-get install -y \
    gettext  \
    python3-pip \
    postgresql-client
COPY requirements.txt /code/
RUN pip install -U pip && \
    pip install -r requirements.txt
EXPOSE 5000
CMD bash entrypoint.sh

COPY app /app

WORKDIR /app
