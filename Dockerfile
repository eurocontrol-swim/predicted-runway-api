FROM python:3.9-buster

LABEL maintainer="francisco-javier.crabiffosse.ext@eurocontrol.int"

ADD ./app /predicted_runway/app
ADD app.py /predicted_runway/app.py
ADD app.ini /predicted_runway/app.ini
ADD requirements.txt /predicted_runway/requirements.txt

RUN mkdir "/data" && mkdir "/data/met" && mkdir "/data/models"
VOLUME ["/data/met", "/data/models"]

WORKDIR /predicted_runway
RUN pip install -r ./requirements.txt

ENV PYTHONPATH /predicted_runway
EXPOSE 5000

CMD ["uwsgi", "./app.ini"]
