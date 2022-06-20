FROM python:3.10-bullseye

LABEL maintainer="francisco-javier.crabiffosse.ext@eurocontrol.int"

RUN mkdir "/data" && mkdir "/data/met" && mkdir "/data/models"

VOLUME ["/data/met", "/data/models"]

WORKDIR /app

COPY requirements.txt /app/requirements.txt

RUN pip install -r ./requirements.txt

COPY ./predicted_runway /app/predicted_runway

ENV PYTHONPATH /app
