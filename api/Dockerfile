FROM python:3.8.2

RUN mkdir /code
RUN mkdir /out
WORKDIR /code

COPY requirements.txt /code/
RUN pip install -r requirements.txt

COPY /src /code/

RUN python -m unittest discover