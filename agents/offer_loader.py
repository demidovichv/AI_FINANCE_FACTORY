from pathlib import Path

import yaml

from agents.shared_models import Offer


class OfferLoader:

    @staticmethod
    def load(file_path: str) -> Offer:

        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(
                f"Offer file not found: {file_path}"
            )

        content = path.read_text(
            encoding="utf-8"
        )

        parts = content.split("---")

        if len(parts) < 3:
            raise ValueError(
                "Invalid offer format. YAML block not found."
            )

        yaml_data = yaml.safe_load(parts[1])

        return Offer(**yaml_data)