FROM python:3.9-buster

LABEL maintainer="francisco-javier.crabiffosse.ext@eurocontrol.int"

RUN mkdir "/data" && mkdir "/data/met" && mkdir "/data/models"

VOLUME ["/data/met", "/data/models"]

WORKDIR /app

COPY ./predicted_runway /app/predicted_runway

COPY requirements.txt /app/requirements.txt

RUN pip install -r ./requirements.txt

ENV PYTHONPATH /app

COPY wsgi.ini /app/wsgi.ini

CMD ["uwsgi", "wsgi.ini"]
