from __future__ import annotations

import json

from datetime import datetime, timezone
from pathlib import Path

from agents.config import PIPELINE_STATUS_DIR
from agents.shared_models import PipelineState


class PipelineManager:

    @staticmethod
    def _state_path(entity_id: str) -> Path:
        return (
            PIPELINE_STATUS_DIR /
            f"{entity_id}.json"
        )

    @classmethod
    def create_state(
        cls,
        entity_id: str,
        entity_type: str
    ) -> PipelineState:

        state = PipelineState(
            entity_id=entity_id,
            entity_type=entity_type,
            status="pending"
        )

        cls.save_state(state)

        return state

    @classmethod
    def save_state(
        cls,
        state: PipelineState
    ) -> None:

        state.updated_at = datetime.now(timezone.utc)

        path = cls._state_path(
            state.entity_id
        )

        path.write_text(
            json.dumps(
                state.model_dump(
                    mode="json"
                ),
                ensure_ascii=False,
                indent=2
            ),
            encoding="utf-8"
        )

    @classmethod
    def load_state(
        cls,
        entity_id: str
    ) -> PipelineState:

        path = cls._state_path(
            entity_id
        )

        if not path.exists():
            raise FileNotFoundError(
                f"Pipeline state not found: {entity_id}"
            )

        data = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )

        return PipelineState(
            **data
        )