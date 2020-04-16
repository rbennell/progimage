import io

from flask import Flask, request, redirect, send_file
from PIL import Image

app = Flask(__name__)


@app.route("/")
def hello_world():
    return "Hello, rotate!"


@app.route("/rotate", methods=["POST"])
def rotate():
    degrees = request.args.get("degrees")
    if "file" not in request.files:
        print("No file part")
        return redirect(request.url)
    file = request.files["file"]
    if file.filename == "":
        print("No selected file")
        return redirect(request.url)
    # _, _, file_format = file.filename.partition(".")
    f = io.BytesIO()
    file_format = None
    with Image.open(file) as im:
        file_format = im.format
        im.rotate(int(degrees)).save(f, format=file_format)
        f.seek(0)
    return send_file(f, mimetype=f"image/{file_format}")
