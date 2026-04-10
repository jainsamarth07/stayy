"""Upload service tests (S3 client mocked)."""

from unittest.mock import MagicMock, patch

import pytest

from app.services.upload_service import delete_image, upload_image


@pytest.fixture
def mock_s3():
    """Provide a mocked S3 client."""
    with patch("app.services.upload_service.get_s3_client") as mock_factory:
        mock_client = MagicMock()
        mock_factory.return_value = mock_client
        yield mock_client


class TestUploadImage:
    """Tests for upload_image service function."""

    def test_upload_returns_url(self, mock_s3):
        """upload_image calls put_object and returns a URL string."""
        url = upload_image(b"fake-image-bytes", "image/jpeg")
        mock_s3.put_object.assert_called_once()
        assert url.endswith(".jpeg")
        assert "properties/" in url

    def test_upload_custom_folder(self, mock_s3):
        """upload_image uses the specified folder prefix."""
        upload_image(b"data", "image/png", folder="avatars")
        args = mock_s3.put_object.call_args
        assert "avatars/" in args.kwargs.get("Key", args[1].get("Key", ""))

    def test_upload_sets_content_type(self, mock_s3):
        """upload_image forwards the content type to S3."""
        upload_image(b"data", "image/webp")
        args = mock_s3.put_object.call_args
        assert args.kwargs.get("ContentType", args[1].get("ContentType")) == "image/webp"


class TestDeleteImage:
    """Tests for delete_image service function."""

    def test_delete_returns_true_on_success(self, mock_s3):
        """delete_image returns True when S3 call succeeds."""
        result = delete_image("http://localhost:9000/staynest-images/properties/abc.jpg")
        assert result is True
        mock_s3.delete_object.assert_called_once()

    def test_delete_returns_false_on_error(self, mock_s3):
        """delete_image returns False when S3 raises ClientError."""
        from botocore.exceptions import ClientError

        mock_s3.delete_object.side_effect = ClientError(
            {"Error": {"Code": "NoSuchKey", "Message": "Not found"}},
            "DeleteObject",
        )
        result = delete_image("http://localhost:9000/staynest-images/properties/missing.jpg")
        assert result is False
