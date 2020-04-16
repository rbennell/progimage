import tempfile
from unittest import mock, TestCase

from api import BadRequest, ProgImageApi


PATH = "/get_image"
QUERY_ARGS = {"rotate": 90, "filter": "blur"}


class TestApi(TestCase):
    def setUp(self):
        self.api = ProgImageApi()


class TestBuildUrl(TestApi):
    def test_url_with_path(self):
        url = self.api._build_url("/a/test/path")
        self.assertEqual(url, "localhost:5000/a/test/path")

    def test_url_with_path_and_query_args(self):
        url = self.api._build_url("/another/test/path", QUERY_ARGS)
        self.assertEqual(url, "localhost:5000/another/test/path?rotate=90&filter=blur")

    def test_url_with_new_endpoint(self):
        self.api.endpoint = "www.spacejam.com"
        url = self.api._build_url("/cmp/behind/chardevelopmentframes.html")
        self.assertEqual(url, "www.spacejam.com/cmp/behind/chardevelopmentframes.html")

    def test_encoding(self):
        url = "https://pbs.twimg.com/profile_images/3543879283/1509e34005183da5ea4eb29150f341e5_400x400.jpeg"
        url = self.api._build_url(PATH, {"url": url})
        self.assertEqual(
            url,
            "localhost:5000/get_image?url=https%3A%2F%2Fpbs.twimg.com%2Fprofile_images%2F3543879283%2F1509e34005183da5ea4eb29150f341e5_400x400.jpeg",
            "Assert the url is properly encoded",
        )


class TestGet(TestApi):
    @mock.patch("requests.get")
    def test_get(self, get_mock):
        self.api._get(PATH, QUERY_ARGS)
        get_mock.assert_called_with("localhost:5000/get_image?rotate=90&filter=blur")


class TestPost(TestApi):
    @mock.patch("requests.post")
    def test_post_without_files(self, post_mock):
        self.api._post(PATH, QUERY_ARGS)
        post_mock.assert_called_with(
            "localhost:5000/get_image?rotate=90&filter=blur", files=None
        )

    @mock.patch("requests.post")
    def test_post_with_files(self, post_mock):
        files = {"file": "buffer"}
        self.api._post(PATH, QUERY_ARGS, files=files)
        post_mock.assert_called_with(
            "localhost:5000/get_image?rotate=90&filter=blur", files={"file": "buffer"}
        )


class TestUploadFromFile(TestApi):
    @mock.patch("api.ProgImageApi.upload_from_buffer")
    def test_upload_from_file(self, upload_from_buffer_mock):
        handle, path = tempfile.mkstemp()
        self.api.upload_from_file(path)
        call_arg = upload_from_buffer_mock.call_args[0][0]
        self.assertEqual(
            type(call_arg).__name__,
            "BufferedReader",
            "Assert we are calling the upload from buffer method with a buffered reader instance",
        )
        self.assertEqual(
            call_arg.name,
            path,
            "Assert the path of the buffered reader is the path of the file",
        )

    def test_upload_from_non_existant_file(self):
        with self.assertRaises(FileNotFoundError):
            self.api.upload_from_file("/foo")


class TestUploadFromBuffer(TestApi):
    @mock.patch("api.ProgImageApi._post")
    def test_upload_from_buffer(self, post_mock):
        buffer = "i am a buffer"
        self.api.upload_from_buffer(buffer)
        post_mock.assert_called_with("/upload", files={"file": buffer})


class TestGetImage(TestApi):
    def test_bad_request(self):
        """
        A bad request is raised if there is no image_id or url
        """
        with self.assertRaises(BadRequest):
            self.api.get_image()

    @mock.patch("api.ProgImageApi._get")
    def test_get_image_with_id_and_no_effects(self, get_image_mock):
        self.api.get_image(image_id=1234)
        get_image_mock.assert_called_with("/get_image", {"image_id": 1234})

    @mock.patch("api.ProgImageApi._get")
    def test_get_image_with_url_and_no_effects(self, get_image_mock):
        self.api.get_image(url="http://images.com/image")
        get_image_mock.assert_called_with(
            "/get_image", {"url": "http://images.com/image"}
        )

    @mock.patch("api.ProgImageApi._get")
    def test_get_image_with_id_and_effects(self, get_image_mock):
        self.api.get_image(image_id=1234, **QUERY_ARGS)
        get_image_mock.assert_called_with(
            "/get_image", {"image_id": 1234, "rotate": 90, "filter": "blur"}
        )
