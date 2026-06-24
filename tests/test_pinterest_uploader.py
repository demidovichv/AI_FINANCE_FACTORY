from pathlib import Path
import json
from unittest.mock import MagicMock, patch

import pytest

from agents.lock_manager import LockManager
from agents.obsidian_parser import read
from agents.pinterest_uploader import PinterestUploader
from agents.shared_models import Pin


@pytest.fixture()
def temp_obsidian(tmp_path: Path) -> Path:
    root = tmp_path / "Obsidian"
    (root / "Articles" / "drafts").mkdir(parents=True)
    (root / "Articles" / "html").mkdir(parents=True)
    (root / "Offers").mkdir()
    (root / "Keywords").mkdir(parents=True)
    (root / "Clusters").mkdir()
    (root / "Pins").mkdir()
    (root / "Telegram").mkdir()
    (root / "YouTube").mkdir()
    (root / "Email").mkdir()
    (root / "Reports").mkdir()
    import agents.obsidian_parser as parser
    parser._OBSIDIAN_ROOT = root
    return root


@pytest.fixture()
def temp_lock_dir(tmp_path: Path) -> Path:
    return tmp_path / ".locks"


def _make_pin() -> Pin:
    return Pin(
        id="pin_001",
        article_id="article_001",
        title="Детская карта Альфа-Банк",
        description="Условия детской карты",
        image_prompt="infographic about kids finance",
        board="myfinq_articles",
        status="draft",
    )


def _make_image_path(tmp_path: Path) -> Path:
    img = tmp_path / "test_image.png"
    img.write_bytes(b"fake-image-data")
    return img


def _mock_media_response(media_id: str = "media_123"):
    resp = MagicMock()
    resp.read.return_value = json.dumps({"media_id": media_id}).encode("utf-8")
    resp.__enter__ = MagicMock(return_value=resp)
    resp.__exit__ = MagicMock(return_value=False)
    return resp


def _mock_pin_response(pin_id: str = "pin123"):
    resp = MagicMock()
    resp.read.return_value = json.dumps({"id": pin_id}).encode("utf-8")
    resp.__enter__ = MagicMock(return_value=resp)
    resp.__exit__ = MagicMock(return_value=False)
    return resp


def test_upload_without_token_returns_false(
    temp_obsidian: Path,
    temp_lock_dir: Path
) -> None:
    pin = _make_pin()
    lm = LockManager(lock_dir=str(temp_lock_dir))
    uploader = PinterestUploader(lock_manager=lm)

    with patch.dict("os.environ", {}, clear=True):
        result = uploader.upload_pin(pin)

    assert result is False


def test_upload_success_with_image(
    temp_obsidian: Path,
    temp_lock_dir: Path
) -> None:
    pin = _make_pin()
    lm = LockManager(lock_dir=str(temp_lock_dir))
    uploader = PinterestUploader(lock_manager=lm)
    image_path = _make_image_path(temp_lock_dir)

    media_resp = _mock_media_response("media_abc")
    pin_resp = _mock_pin_response("pin123")

    with patch.dict("os.environ", {"PINTEREST_ACCESS_TOKEN": "fake_token"}):
        with patch("agents.pinterest_uploader.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = [media_resp, pin_resp]
            result = uploader.upload_pin(pin, image_path=image_path)

    assert result is True
    assert pin.status == "published"
    assert pin.media_id == "media_abc"
    assert pin.pinterest_url == "https://www.pinterest.com/pin/pin123/"


def test_upload_saves_to_obsidian(
    temp_obsidian: Path,
    temp_lock_dir: Path
) -> None:
    pin = _make_pin()
    lm = LockManager(lock_dir=str(temp_lock_dir))
    uploader = PinterestUploader(lock_manager=lm)
    image_path = _make_image_path(temp_lock_dir)

    media_resp = _mock_media_response("media_xyz")
    pin_resp = _mock_pin_response("pin456")

    with patch.dict("os.environ", {"PINTEREST_ACCESS_TOKEN": "fake_token"}):
        with patch("agents.pinterest_uploader.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = [media_resp, pin_resp]
            uploader.upload_pin(pin, image_path=image_path)

    loaded = read("pin", pin.id)
    assert loaded.pinterest_url == "https://www.pinterest.com/pin/pin456/"
    assert loaded.status == "published"
    assert loaded.media_id == "media_xyz"


def test_upload_missing_image_returns_false(
    temp_obsidian: Path,
    temp_lock_dir: Path
) -> None:
    pin = _make_pin()
    lm = LockManager(lock_dir=str(temp_lock_dir))
    uploader = PinterestUploader(lock_manager=lm)

    with patch.dict("os.environ", {"PINTEREST_ACCESS_TOKEN": "fake_token"}):
        result = uploader.upload_pin(pin, image_path=None)

    assert result is False
    assert pin.status == "failed"


def test_upload_media_api_error(
    temp_obsidian: Path,
    temp_lock_dir: Path
) -> None:
    pin = _make_pin()
    lm = LockManager(lock_dir=str(temp_lock_dir))
    uploader = PinterestUploader(lock_manager=lm)
    image_path = _make_image_path(temp_lock_dir)

    error_resp = MagicMock()
    error_resp.code = 500
    error_resp.read.return_value = b'{"message": "Internal Server Error"}'
    error_resp.__enter__ = MagicMock(return_value=error_resp)
    error_resp.__exit__ = MagicMock(return_value=False)
    error_resp.headers = {}

    from urllib.error import HTTPError
    with patch.dict("os.environ", {"PINTEREST_ACCESS_TOKEN": "fake_token"}):
        with patch("agents.pinterest_uploader.urlopen", side_effect=HTTPError(
            url="https://api.pinterest.com/v5/media",
            code=500,
            msg="Internal Server Error",
            hdrs={},
            fp=None,
        )):
            result = uploader.upload_pin(pin, image_path=image_path)

    assert result is False
    assert pin.status == "failed"


def test_upload_releases_lock(
    temp_obsidian: Path,
    temp_lock_dir: Path
) -> None:
    pin = _make_pin()
    lm = LockManager(lock_dir=str(temp_lock_dir))
    uploader = PinterestUploader(lock_manager=lm)
    image_path = _make_image_path(temp_lock_dir)

    media_resp = _mock_media_response("media_rel")
    pin_resp = _mock_pin_response("pin_rel")

    with patch.dict("os.environ", {"PINTEREST_ACCESS_TOKEN": "fake_token"}):
        with patch("agents.pinterest_uploader.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = [media_resp, pin_resp]
            uploader.upload_pin(pin, image_path=image_path)

    assert not (temp_lock_dir / "pin_001.lock").exists()
