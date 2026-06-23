from pathlib import Path
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


def test_upload_success_updates_model(
    temp_obsidian: Path,
    temp_lock_dir: Path
) -> None:
    pin = _make_pin()
    lm = LockManager(lock_dir=str(temp_lock_dir))
    uploader = PinterestUploader(lock_manager=lm)
    
    mock_response = MagicMock()
    mock_response.read.return_value = b'{"id": "pin123"}'
    mock_response.__enter__ = MagicMock(return_value=mock_response)
    mock_response.__exit__ = MagicMock(return_value=False)
    
    with patch.dict("os.environ", {"PINTEREST_ACCESS_TOKEN": "fake_token"}):
        with patch("agents.pinterest_uploader.urlopen", return_value=mock_response):
            result = uploader.upload_pin(pin)
    
    assert result is True
    assert pin.status == "published"
    assert pin.pinterest_url == "https://www.pinterest.com/pin/pin123/"


def test_upload_saves_to_obsidian(
    temp_obsidian: Path,
    temp_lock_dir: Path
) -> None:
    pin = _make_pin()
    lm = LockManager(lock_dir=str(temp_lock_dir))
    uploader = PinterestUploader(lock_manager=lm)
    
    mock_response = MagicMock()
    mock_response.read.return_value = b'{"id": "pin456"}'
    mock_response.__enter__ = MagicMock(return_value=mock_response)
    mock_response.__exit__ = MagicMock(return_value=False)
    
    with patch.dict("os.environ", {"PINTEREST_ACCESS_TOKEN": "fake_token"}):
        with patch("agents.pinterest_uploader.urlopen", return_value=mock_response):
            uploader.upload_pin(pin)
    
    loaded = read("pin", pin.id)
    assert loaded.pinterest_url == "https://www.pinterest.com/pin/pin456/"
    assert loaded.status == "published"
