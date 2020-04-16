import io
import os
import urllib.parse
import uuid

from flask import Flask, request, send_file
from PIL import Image
import requests

app = Flask(__name__)
app.config["IMAGES"] = "/images"
app.config["TMP"] = "/tmp"


TRANSFORMATIONS = {
    "filter": {"endpoint": "http://filter:5003/filter", "query_arg": "effect"},
    "mask": {"endpoint": "http://mask:5004/mask", "query_arg": "shape"},
    "rotate": {"endpoint": "http://rotate:5001/rotate", "query_arg": "degrees"},
    "thumbnail": {"endpoint": "http://thumbnail:5002/thumbnail", "query_arg": "size"},
}


# from the flask docs.
class InvalidUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv["message"] = self.message
        return rv


class BadPayload(InvalidUsage):
    pass


@app.route("/")
def hello_world():
    return "Hello, Heycar!"


@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        raise InvalidUsage(
            "The payload must contain a file in requestfiles with the key 'file'"
        )
    file = request.files["file"]
    if file.filename == "":
        raise BadPayload("There was no uploaded file")
    image_id = str(uuid.uuid4())
    file.save(os.path.join(app.config["IMAGES"], image_id))
    return image_id


@app.route("/image", methods=["GET"])
def get_image():
    """
    Uses the image id or url to obtain the image, and then applies effects.
    """
    buffer, file_format = convert_image(request)
    buffer = apply_transformations(request, buffer)
    return send_file(buffer, mimetype=f"image/{file_format}")


def convert_image(request):
    """
    Get a buffer containing the image, before applying any
    transformations.
    """
    in_path = get_in_path(request)

    # It does not make sense to have compression in its own microservice since it's
    # an attribute of saving, and we do our file format conversion here.
    with Image.open(in_path) as im:
        file_conversion_args = get_file_conversion_args(request, im)
        return save(im, **file_conversion_args), file_conversion_args["format"]


def get_in_path(request):
    """
    Using either the image_id or url, perform the appropriate action
    to get a path to the image.
    """
    image_id = request.args.get("image_id")
    url = request.args.get("url")
    if not (image_id or url):
        raise InvalidUsage("You must include an image_id or url get parameter.")

    if image_id:
        return os.path.join(app.config["IMAGES"], image_id)
    return io.BytesIO(requests.get(url).content)


def get_file_conversion_args(request, im):
    # if we have not specified a new format, retain the old format.
    file_format = request.args.get("format") or im.format
    file_conversion_args = {"format": file_format}
    # compress level for pngs, quality for jpegs.
    for attribute in ["compress_level", "quality"]:
        value = request.args.get(attribute)
        if value:
            file_conversion_args[attribute] = int(value)
    return file_conversion_args


def save(im, **file_conversion_args):
    buffer = io.BytesIO()
    try:
        im.save(buffer, **file_conversion_args)
    except OSError:
        # Trick for converting rgba type formats to jpeg.

        # credit: https://stackoverflow.com/a/9459208/2610613
        rgb = Image.new("RGB", im.size, (255, 255, 255))
        rgb.paste(im, mask=im.split()[3])
        rgb.save(buffer, **file_conversion_args)
    buffer.seek(0)
    return buffer


def apply_transformations(request, buffer):
    """
    Takes the existing buffer, and applies transformations in sequence,
    returning the final buffer
    """
    for transformation, details in TRANSFORMATIONS.items():
        param = request.args.get(transformation)
        if param:
            query_params = urllib.parse.urlencode({details["query_arg"]: param})
            url = f"{details['endpoint']}?{query_params}"
            buffer = io.BytesIO(requests.post(url, files={"file": buffer}).content)
    return buffer
