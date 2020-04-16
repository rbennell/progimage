FROM python:3.8.2

RUN mkdir /code
RUN mkdir /images
WORKDIR /code

COPY requirements.txt /code/
RUN pip install -r requirements.txt

COPY /src /code/
COPY /images /images/

RUN python -m unittest discover