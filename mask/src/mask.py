import io

from flask import Flask, request, redirect, send_file
from PIL import Image, ImageDraw

app = Flask(__name__)


@app.route("/")
def hello_world():
    return "Hello, mask!"


@app.route("/mask", methods=["POST"])
def mask():
    """
    Can be used to add a black mask with the specified shape to the image
    """
    shape = request.args.get("shape")
    if "file" not in request.files:
        print("No file part")
        return redirect(request.url)
    file = request.files["file"]
    if file.filename == "":
        print("No selected file")
        return redirect(request.url)

    file_format = None

    with Image.open(file) as im:
        file_format = im.format
        mask = get_mask(im, shape)
        im.putalpha(mask)
        buffer = save(im, file_format)
    return send_file(buffer, mimetype=f"image/{file_format}")


def save(im, file_format):
    buffer = io.BytesIO()
    try:
        im.save(buffer, format=file_format)
    except OSError:
        # Trick for converting rgba type formats to jpeg.

        # credit: https://stackoverflow.com/a/9459208/2610613
        rgb = Image.new("RGB", im.size, (255, 255, 255))
        rgb.paste(im, mask=im.split()[3])
        rgb.save(buffer, format=file_format)
    buffer.seek(0)
    return buffer


def get_mask(im, shape):
    mask = Image.new("L", im.size, color=10)
    draw = ImageDraw.Draw(mask)
    transparent_area = (
        im.width / 10,
        im.height / 10,
        im.width / 10 * 9,
        im.height / 10 * 9,
    )
    shape_function = getattr(draw, shape)
    shape_function(transparent_area, fill=255)
    return mask
