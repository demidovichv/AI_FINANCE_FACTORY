from __future__ import annotations

import json
import logging
import mimetypes
import os
import uuid
from pathlib import Path
from typing import Optional
from urllib.request import Request, urlopen
from urllib.error import HTTPError

from agents.lock_manager import LockManager
from agents.obsidian_parser import write
from agents.shared_models import Pin


logger = logging.getLogger(__name__)


class PinterestUploader:
    API_BASE = "https://api.pinterest.com/v5"
    MEDIA_UPLOAD_URL = f"{API_BASE}/media"

    def __init__(self, lock_manager: Optional[LockManager] = None):
        self.lock_manager = lock_manager or LockManager()

    def upload_pin(
        self,
        pin: Pin,
        image_path: Optional[str | Path] = None
    ) -> bool:
        token = os.getenv("PINTEREST_ACCESS_TOKEN")
        if not token:
            logger.warning(
                "Pinterest token not found. "
                "Set PINTEREST_ACCESS_TOKEN to enable uploads."
            )
            return False

        acquired, msg = self.lock_manager.acquire_lock(
            "pin", pin.id, "pinterest_uploader"
        )
        if not acquired:
            raise RuntimeError(f"Не удалось захватить блокировку: {msg}")
        try:
            success = self._call_pinterest_api(pin, token, image_path)
            if success:
                pin.status = "published"
            else:
                pin.status = "failed"
            path = write(pin, "pin")
            pin.obsidian_path = path
            return success
        finally:
            self.lock_manager.release_lock("pin", pin.id)

    def _call_pinterest_api(
        self,
        pin: Pin,
        token: str,
        image_path: Optional[str | Path]
    ) -> bool:
        media_id = self._upload_media_if_needed(pin, token, image_path)
        if not media_id:
            logger.error(
                "Failed to obtain media_id for pin %s. "
                "Provide a valid image_path or ensure Pinterest media upload works.",
                pin.id,
            )
            return False

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        payload = {
            "board_id": pin.board,
            "title": pin.title,
            "description": pin.description,
            "link": "",
            "alt_text": pin.description,
            "media_source": {
                "source_type": "media_id",
                "media_id": media_id,
            },
        }
        data = json.dumps(payload).encode("utf-8")
        req = Request(
            f"{self.API_BASE}/pins",
            data=data,
            headers=headers,
            method="POST",
        )
        try:
            with urlopen(req, timeout=30) as resp:
                body = resp.read().decode("utf-8")
                result = json.loads(body)
                pin_id = result.get("id") or result.get("pin", {}).get("id")
                if pin_id:
                    pin.media_id = media_id
                    pin.pinterest_url = (
                        f"https://www.pinterest.com/pin/{pin_id}/"
                    )
                    return True
                return False
        except HTTPError as exc:
            status = exc.code
            if status in (401, 403):
                logger.error("Pinterest auth failed: %s", exc)
            elif status == 429:
                logger.error("Pinterest rate limit: %s", exc)
            else:
                logger.error("Pinterest API error %s: %s", status, exc)
            return False
        except Exception as exc:
            logger.error("Pinterest request failed: %s", exc)
            return False

    def _upload_media_if_needed(
        self,
        pin: Pin,
        token: str,
        image_path: Optional[str | Path]
    ) -> Optional[str]:
        if pin.media_id:
            return pin.media_id
        if pin.image_url:
            return pin.image_url
        if not image_path:
            return None
        path = Path(image_path)
        if not path.exists():
            logger.error("Image file not found: %s", path)
            return None
        return self._upload_media(token, path)

    def _upload_media(self, token: str, image_path: Path) -> Optional[str]:
        media_type = mimetypes.guess_type(str(image_path))[0] or "application/octet-stream"
        boundary = f"----FormBoundary{uuid.uuid4().hex[:12]}"
        file_name = image_path.name.encode("utf-8")
        header = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="media_type"\r\n\r\n'
            f"{media_type}\r\n"
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="media"; filename="{file_name.decode("utf-8")}"\r\n'
            f"Content-Type: {media_type}\r\n\r\n"
        ).encode("utf-8")
        body = header + image_path.read_bytes() + f"\r\n--{boundary}--\r\n".encode("utf-8")
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Accept": "application/json",
        }
        req = Request(
            self.MEDIA_UPLOAD_URL,
            data=body,
            headers=headers,
            method="POST",
        )
        try:
            with urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return result.get("media_id")
        except HTTPError as exc:
            status = exc.code
            if status in (401, 403):
                logger.error("Pinterest auth failed during media upload: %s", exc)
            else:
                logger.error(
                    "Pinterest media upload error %s: %s", status, exc
                )
            return None
        except Exception as exc:
            logger.error("Pinterest media upload request failed: %s", exc)
            return None
