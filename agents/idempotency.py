from pathlib import Path


class IdempotencyManager:
    def __init__(
        self,
        pipeline_dir: str = "data/Pipeline_Status"
    ):
        self.pipeline_dir = Path(pipeline_dir)

        self.pipeline_dir.mkdir(
            parents=True,
            exist_ok=True
        )

    def article_exists(
        self,
        offer_id: str
    ) -> bool:

        for file in self.pipeline_dir.glob("*.json"):

            try:
                content = file.read_text(
                    encoding="utf-8"
                )

                if offer_id in content:
                    return True

            except Exception:
                continue

        return False