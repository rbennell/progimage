import os
import uuid

from flask import Flask, request, send_from_directory, redirect

app = Flask(__name__)
app.config["IMAGES"] = "/images"


@app.route("/")
def hello_world():
    return "Hello, Heycar!"


@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        print("No file part")
        return redirect(request.url)
    file = request.files["file"]
    if file.filename == "":
        print("No selected file")
        return redirect(request.url)
    image_id = str(uuid.uuid4())
    file.save(os.path.join(app.config["IMAGES"], image_id + ".jpeg"))
    return image_id


@app.route("/image/<string:image_id>", methods=["GET"])
def get_image(image_id):
    return send_from_directory(app.config["IMAGES"], image_id + ".jpeg")
