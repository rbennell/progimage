import io

from flask import Flask, request, redirect, send_file
from PIL import Image

app = Flask(__name__)


@app.route("/")
def hello_world():
    return "Hello, thumbnail!"


@app.route("/thumbnail", methods=["POST"])
def thumbnail():
    size = tuple(int(part) for part in request.args.get("size").split(","))
    if "file" not in request.files:
        print("No file part")
        return redirect(request.url)
    file = request.files["file"]
    if file.filename == "":
        print("No selected file")
        return redirect(request.url)
    f = io.BytesIO()
    file_format = None
    with Image.open(file) as im:
        file_format = im.format
        im.thumbnail(size)
        im.save(f, format=file_format)
        f.seek(0)
    return send_file(f, mimetype=f"image/{file_format}")
