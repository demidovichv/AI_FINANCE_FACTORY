from __future__ import annotations

import json
import logging
import os
from typing import Optional
from urllib.request import Request, urlopen
from urllib.error import HTTPError

from agents.lock_manager import LockManager
from agents.obsidian_parser import write
from agents.shared_models import Pin


logger = logging.getLogger(__name__)


class PinterestUploader:
    API_BASE = "https://api.pinterest.com/v5"

    def __init__(self, lock_manager: Optional[LockManager] = None):
        self.lock_manager = lock_manager or LockManager()

    def upload_pin(self, pin: Pin, image_path: Optional[object] = None) -> bool:
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
        image_path: Optional[object]
    ) -> bool:
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
