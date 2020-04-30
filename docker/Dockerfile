FROM python:3.8
ENV PYTHONUNBUFFERED 1
RUN mkdir /code
WORKDIR /code
RUN apt-get update && apt-get install -y gettext
COPY requirements.txt /code/
RUN pip install -r requirements.txt
