from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from agents.github_publisher import GitHubPublisher
    from agents.pinterest_uploader import PinterestUploader
    from agents.review_manager import ReviewManager


logger = logging.getLogger(__name__)


class PublicationOrchestrator:
    def __init__(
        self,
        review_manager: "ReviewManager",
        github_publisher: Optional["GitHubPublisher"] = None,
        pinterest_uploader: Optional["PinterestUploader"] = None,
        log_path: str = "data/Logs/publication_log.md",
    ):
        self.review_manager = review_manager
        self.github_publisher = github_publisher
        self.pinterest_uploader = pinterest_uploader
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def process_approval(
        self,
        entity_id: str,
        entity_type: str,
        image_path: Optional[Path] = None,
    ) -> dict:
        result = {
            "entity_id": entity_id,
            "entity_type": entity_type,
            "status": "failed",
            "steps": [],
        }
        try:
            approved = self.review_manager.approve(entity_id, entity_type)
            result["steps"].append(
                {
                    "stage": "review_approve",
                    "status": "success",
                    "message": f"Approved {entity_type} {entity_id}",
                }
            )
        except Exception as exc:
            logger.error("Review approve failed: %s", exc)
            result["steps"].append(
                {
                    "stage": "review_approve",
                    "status": "failed",
                    "message": str(exc),
                }
            )
            self._log(result)
            return result

        try:
            if entity_type == "article":
                if self.github_publisher is None:
                    raise RuntimeError("GitHubPublisher not configured")
                published = self.github_publisher.publish_approved_articles()
                result["steps"].append(
                    {
                        "stage": "github_publish",
                        "status": "success",
                        "message": f"Published: {published}",
                    }
                )
            elif entity_type == "pin":
                if self.pinterest_uploader is None:
                    raise RuntimeError("PinterestUploader not configured")
                pin = self._load_pin_from_obsidian(entity_id)
                if pin is None:
                    raise RuntimeError(f"Pin {entity_id} not found in Obsidian")
                ok = self.pinterest_uploader.upload_pin(pin, image_path)
                if not ok:
                    raise RuntimeError("Pinterest upload returned False")
                result["steps"].append(
                    {
                        "stage": "pinterest_upload",
                        "status": "success",
                        "message": f"Uploaded pin {entity_id}",
                    }
                )
            elif entity_type == "telegram_post":
                logger.info(
                    "Telegram post %s is ready for Telegram API", entity_id
                )
                result["steps"].append(
                    {
                        "stage": "telegram_ready",
                        "status": "success",
                        "message": "Ready for Telegram API",
                    }
                )
            else:
                result["steps"].append(
                    {
                        "stage": "publish",
                        "status": "skipped",
                        "message": f"Unknown entity type: {entity_type}",
                    }
                )
            result["status"] = "success"
        except Exception as exc:
            logger.error("Publishing failed: %s", exc)
            result["steps"].append(
                {
                    "stage": "publish",
                    "status": "failed",
                    "message": str(exc),
                }
            )

        self._log(result)
        return result

    def _load_pin_from_obsidian(self, pin_id: str):
        try:
            from agents.obsidian_parser import read
            return read("pin", pin_id)
        except Exception:
            return None

    def _log(self, result: dict) -> None:
        timestamp = datetime.now(timezone.utc).isoformat()
        line = (
            f"- {timestamp} | {result['entity_type']} | "
            f"{result['entity_id']} | {result['status']} | "
            f"steps: {len(result['steps'])}\n"
        )
        with self.log_path.open("a", encoding="utf-8") as f:
            f.write(line)
