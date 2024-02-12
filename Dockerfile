FROM python:3.6.12

WORKDIR /aoasisbot

COPY requirements.txt /aoasisbot/

RUN pip install -r requirements.txt

COPY . /aoasisbot
CMD python aoasisbot/main.py