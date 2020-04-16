import glob
from io import BytesIO
import shutil
import tempfile
import unittest

from unittest import mock

from PIL import Image

from progimage import (
    app,
    apply_transformations,
    convert_image,
    get_file_conversion_args,
    get_in_path,
    save,
    BadPayload,
    InvalidUsage,
)


class TestProgImage(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        app.config["IMAGES"] = tempfile.mkdtemp()
        self.client = app.test_client()


class TestHelloWorld(TestProgImage):
    def test_hello_world(self):
        rv = self.client.get("/")
        self.assertEqual(rv.data, b"Hello, Heycar!")


class TestUpload(TestProgImage):
    empty_file = (BytesIO(), "")
    test_file = (BytesIO(b"contents"), "test.file")

    def test_upload_without_files(self):
        with self.assertRaises(InvalidUsage):
            self.client.post(
                "/upload", content_type="multipart/form-data", data={},
            )

    def test_upload_without_file(self):
        """
        By add the tuple with no second part, the server
        is tricked in to thinking we have uploaded a payload
        with 'file' empty
        """
        with self.assertRaises(BadPayload):
            self.client.post(
                "/upload",
                content_type="multipart/form-data",
                data={"file": self.empty_file},
            )

    @mock.patch("uuid.uuid4", return_value="fake_uuid")
    def test_upload(self, uuid_mock):
        resp = self.client.post(
            "/upload",
            content_type="multipart/form-data",
            data={"file": self.test_file},
        )
        uploaded_files = glob.glob(f"{app.config['IMAGES']}/*")
        self.assertEqual(resp.data, b"fake_uuid")
        self.assertEqual(uploaded_files, [f"{app.config['IMAGES']}/fake_uuid"])


class TestGetImage(TestProgImage):
    def setUp(self):
        super().setUp()
        shutil.copyfile("fixtures/steve.png", f"{app.config['IMAGES']}/test")

    def test_get_test_image(self):
        resp = self.client.get("/image?image_id=test")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp.mimetype, "image/PNG", "Assert that the response contains a png"
        )

    def test_get_non_existant_image(self):
        with self.assertRaises(FileNotFoundError):
            self.client.get("/image?image_id=bla")

    @mock.patch("progimage.apply_transformations", return_value=BytesIO())
    def test_transformations_applied(self, apply_mock):
        resp = self.client.get("/image?image_id=test&rotate=90")
        self.assertEqual(resp.status_code, 200)
        apply_mock.assert_called_once()


class TestGetInPath(TestProgImage):
    def test_without_image_args(self):
        "Without an image id or url, an exception should be raised."
        request = mock.MagicMock(args={})

        with self.assertRaises(InvalidUsage):
            get_in_path(request)

    def test_with_image_id(self):
        request = mock.MagicMock(args={"image_id": "fake_id"})
        path = get_in_path(request)
        self.assertEqual(path, f"{app.config['IMAGES']}/fake_id")

    @mock.patch("requests.get")
    def test_with_url(self, get_mock):
        mock_return_value = mock.MagicMock()
        mock_return_value.content = b"some content"
        get_mock.return_value = mock_return_value
        request = mock.MagicMock(args={"url": "https://images.com/an_image"})
        path = get_in_path(request)
        get_mock.assert_called_with("https://images.com/an_image")
        self.assertEqual(type(path).__name__, "BytesIO")
        self.assertEqual(path.read(), b"some content")


class TestConvertImage(TestProgImage):
    @mock.patch("progimage.get_in_path")
    def test_calls_get_in_path(self, get_in_path_mock):
        request = mock.MagicMock(args={})
        with open("fixtures/steve.png", "rb") as test_image:
            get_in_path_mock.return_value = test_image
            convert_image(request)
        get_in_path_mock.assert_called_with(request)

    @mock.patch("progimage.get_file_conversion_args", return_value={"format": "png"})
    @mock.patch("progimage.get_in_path")
    def test_calls_get_file_conversion_args_correctly(
        self, get_in_path_mock, get_file_conversion_args_mock
    ):
        request = mock.MagicMock()
        with open("fixtures/steve.png", "rb") as test_image:
            get_in_path_mock.return_value = test_image
            convert_image(request)
        request_arg, im_arg = get_file_conversion_args_mock.call_args[0]
        self.assertEqual(request_arg, request)
        self.assertEqual(
            type(im_arg).__name__,
            "PngImageFile",
            "Assert we are using a png image file, as the image we uploaded was a png.",
        )

    @mock.patch("progimage.save", return_value="buffer")
    @mock.patch("progimage.get_file_conversion_args", return_value={"format": "png"})
    @mock.patch("progimage.get_in_path")
    def test_calls_save_correctly(
        self, get_in_path_mock, get_file_conversion_args_mock, save_mock
    ):
        request = mock.MagicMock(args={})
        with open("fixtures/steve.png", "rb") as test_image:
            get_in_path_mock.return_value = test_image
            buffer, file_format = convert_image(request)
        save_arg = save_mock.call_args[0][0]
        conversion_kwargs = save_mock.call_args[1]
        self.assertEqual(
            type(save_arg).__name__,
            "PngImageFile",
            "Assert we are using a png image file, as the image we uploaded was a png.",
        )
        self.assertEqual(conversion_kwargs, {"format": "png"})
        self.assertEqual(
            buffer, "buffer", "Assert convert image is returning the output of save"
        )
        self.assertEqual(
            file_format, "png", "PILLOW should determine this image to be a png."
        )


class TestGetFileConversionArgs(TestProgImage):
    def test_without_specified_conversion_format(self):
        request = mock.MagicMock(args={})
        with open("fixtures/steve.png", "rb") as test_image:
            im = Image.open(test_image)
            file_conversion_args = get_file_conversion_args(request, im)
        self.assertEqual(
            file_conversion_args,
            {"format": "PNG"},
            "As we are not specifying a conversion format, save the image retaining the original format.",
        )

    def test_with_specified_args(self):
        request = mock.MagicMock(args={"format": "JPEG", "quality": "75"})
        file_conversion_args = get_file_conversion_args(
            request, None
        )  # im is not used in this case
        self.assertEqual(
            file_conversion_args, {"format": "JPEG", "quality": 75},
        )


class TestSave(TestProgImage):
    def test_convert_rgba_to_jpeg(self):
        """
        Without proper handling this conversion can cause OS errors.
        """
        with open("fixtures/steve.png", "rb") as test_image:
            im = Image.open(test_image)
            self.assertEqual(im.format, "PNG", "We test that the input image is a png")
            buffer = save(im, format="jpeg")
        self.assertEqual(
            Image.open(buffer).format, "JPEG", "We test that the output image is a JPEG"
        )

    def test_conversion_args(self):
        """
        Test that save is called with the file conversion args
        """
        im = mock.MagicMock()
        save(im, format="PNG", compress_level=8)
        file_conversion_kwargs = im.save.call_args[1]
        self.assertEqual(file_conversion_kwargs, {"format": "PNG", "compress_level": 8})


class TestApplyTransformations(TestProgImage):
    def test_no_transformations_in_request(self):
        request = mock.MagicMock(args={})
        buffer = "buffer"
        self.assertEqual(
            apply_transformations(request, buffer),
            "buffer",
            "As no transformations are applied the buffer should be unchanged",
        )

    @mock.patch("requests.post")
    def test_rotation(self, post_mock):
        post_mock.return_value.content = b"bar"
        request = mock.MagicMock(args={"rotate": "90"})
        buffer = BytesIO(b"foo")
        new_buffer = apply_transformations(request, buffer)
        self.assertEqual(new_buffer.read(), b"bar")
        post_mock.assert_called_with(
            "http://rotate:5001/rotate?degrees=90", files={"file": buffer}
        )
