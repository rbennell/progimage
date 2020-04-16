import io

from flask import Flask, request, redirect, send_file
from PIL import Image, ImageFilter

app = Flask(__name__)


@app.route("/")
def hello_world():
    return "Hello, filter!"


@app.route("/filter", methods=["POST"])
def filter():
    effect = request.args.get("effect")
    if "file" not in request.files:
        print("No file part")
        return redirect(request.url)
    file = request.files["file"]
    if file.filename == "":
        print("No selected file")
        return redirect(request.url)
    f = io.BytesIO()
    file_format = None

    filter_class = getattr(ImageFilter, effect.upper())
    with Image.open(file) as im:
        file_format = im.format
        im.filter(filter_class).save(f, format=file_format)
        f.seek(0)
    return send_file(f, mimetype=f"image/{file_format}")
