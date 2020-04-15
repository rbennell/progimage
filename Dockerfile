FROM python:3.8.2

RUN mkdir /code
RUN mkdir /images
WORKDIR /code

COPY src/requirements.txt /code/
RUN pip install --no-cache-dir -r requirements.txt

COPY /src /code/
COPY /images /images/