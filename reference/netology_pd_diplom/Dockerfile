
FROM python:3.10

ENV PYTHONUNBUFFERED=1
WORKDIR /usr/src/app
COPY ./requirements.txt /usr/src/requirements.txt
RUN pip install -r /usr/src/requirements.txt
COPY . /usr/src/app