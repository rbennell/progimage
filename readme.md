This is progimage, as specced in the heycar senior engineer interview challenge.

usage:

`$ docker-compose build` - to set the project up and run tests

`$ docker-compose run` - to start the services running. This will also run the main method of api, and put a picture in the api/out directory.

### uploading

curl -F ‘file=@path/to/local/file’ localhost:5000/upload

### getting files by id

curl localhost:5000/image?image_id={image id}

### getting files by url

curl localhost:5000/image?url={url}

### get a picture from the internet and transform it a lot

(i cheated and used postman to generate this)
curl --location --request GET 'localhost:5000/image?format=png&thumbnail=200,200&filter=blur&mask=ellipse&rotate=45&url=https://media.wired.com/photos/5cdefc28b2569892c06b2ae4/master/w_2560%2Cc_limit/Culture-Grumpy-Cat-487386121-2.jpg'
