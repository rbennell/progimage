import urllib

import requests


class BadRequest(Exception):
    pass


class ProgImageApi:
    endpoint = "localhost:5000"

    def _build_url(self, path, query_args=None):
        url = self.endpoint + path
        if query_args:
            url += f"?{urllib.parse.urlencode(query_args)}"
        return url

    def _get(self, path, query_args):
        url = self._build_url(path, query_args)
        return requests.get(url)

    def _post(self, path, query_args, files=None):
        url = self._build_url(path, query_args)
        return requests.post(url, files=files)

    def upload_from_file(self, path):
        """
        Uploads the image at the given path to progimage.
        """
        with open(path, "rb") as buffer:
            return self.upload_from_buffer(buffer)

    def upload_from_buffer(self, buffer):
        """
        Uploads the image held in memory to progimage.
        """
        return self._post("/upload", files={"file": buffer})

    def get_image(self, image_id=None, url=None, **transform_effects):
        get_image_kwargs = transform_effects
        if image_id:
            get_image_kwargs["image_id"] = image_id
        elif url:
            get_image_kwargs["url"] = url

        if not (image_id or url):
            raise BadRequest("Must include an image_id or url when using get_image")
        return self._get("/get_image", get_image_kwargs)
