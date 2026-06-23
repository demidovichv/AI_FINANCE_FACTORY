"""
Интеграционный слой для Hermes Desktop.
Точка входа для запуска всей фабрики контента одной командой.
"""

from __future__ import annotations

import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from agents.article_generator import ArticleGenerator
from agents.cluster_manager import ClusterManager
from agents.email_sequence_generator import EmailSequenceGenerator
from agents.fact_checker import FactChecker
from agents.html_renderer import HTMLRenderer
from agents.keyword_researcher import KeywordResearcher
from agents.lock_manager import LockManager
from agents.obsidian_parser import read
from agents.publication_orchestrator import PublicationOrchestrator
from agents.pinterest_designer import PinterestDesigner
from agents.shared_models import Article, Cluster, Keyword, Offer, Pin, TelegramPost, YouTubeScript
from agents.telegram_publisher import TelegramPublisher
from agents.youtube_script_generator import YouTubeScriptGenerator


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("data/Logs/hermes_tasks.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("hermes_tasks")


class HermesTaskRunner:
    def __init__(
        self,
        llm_client=None,
        lock_manager: Optional[LockManager] = None,
    ):
        self.llm_client = llm_client
        self.lock_manager = lock_manager or LockManager()

    def run_full_pipeline(self, offer_id: str) -> dict:
        start = datetime.now(timezone.utc).isoformat()
        report = {
            "offer_id": offer_id,
            "started_at": start,
            "status": "failed",
            "steps": [],
            "created": {},
        }
        try:
            logger.info("Fetching offer %s", offer_id)
            offer = self._load_offer(offer_id)
            report["steps"].append(self._step("load_offer", "success", offer_id))

            logger.info("Keyword research for %s", offer.name)
            keywords = self._run_keyword_research(offer)
            report["created"]["keywords"] = [k.id for k in keywords]

            logger.info("Clustering %d keywords", len(keywords))
            clusters = self._run_clustering(keywords)
            report["created"]["clusters"] = [c.id for c in clusters]

            logger.info("Article generation started")
            articles = self._run_article_generation(offer, keywords, clusters)
            report["created"]["articles"] = [a.id for a in articles]

            logger.info("Fact checking started")
            checked_articles = self._run_fact_checking(articles, offer)
            report["fact_checked"] = [a.id for a in checked_articles]

            logger.info("HTML rendering started")
            rendered = self._run_html_rendering(checked_articles, offer)
            report["rendered"] = [a.id for a in rendered]

            pins: List[Pin] = []
            for article in rendered:
                logger.info("Pinterest design for %s", article.id)
                pins.append(self._run_pinterest_design(article))

            telegram_posts: List[TelegramPost] = []
            for article in rendered:
                logger.info("Telegram post for %s", article.id)
                telegram_posts.append(self._run_telegram(article))

            youtube_scripts: List[YouTubeScript] = []
            for article in rendered:
                logger.info("YouTube script for %s", article.id)
                youtube_scripts.append(self._run_youtube(article))

            email_sequences = []
            for article in rendered:
                logger.info("Email sequence for %s", article.id)
                email_sequences.append(self._run_email(article))

            self._submit_all_for_review(
                articles=rendered,
                pins=pins,
                telegram_posts=telegram_posts,
            )

            report["status"] = "success"
            logger.info("Pipeline completed successfully for offer %s", offer_id)
        except Exception as exc:
            logger.error("Pipeline failed: %s", exc, exc_info=True)
            report["error"] = str(exc)
        finally:
            report["finished_at"] = datetime.now(timezone.utc).isoformat()
        return report

    def process_publication_queue(self) -> dict:
        from agents.review_manager import ReviewManager

        report = {
            "processed": [],
            "failed": [],
        }
        try:
            review_manager = ReviewManager()
            from agents.github_publisher import GitHubPublisher
            from agents.pinterest_uploader import PinterestUploader

            github = GitHubPublisher()
            pinterest = PinterestUploader()

            orchestrator = PublicationOrchestrator(
                review_manager=review_manager,
                github_publisher=github,
                pinterest_uploader=pinterest,
            )

            base = Path("data/Review_Queue")
            for sub in ["articles", "pinterest", "telegram"]:
                folder = base / sub
                if not folder.exists():
                    continue
                for status_file in folder.glob("*.json"):
                    try:
                        import json
                        data = json.loads(status_file.read_text(encoding="utf-8"))
                        if data.get("status") != "approved":
                            continue
                        entity_id = data["entity_id"]
                        entity_type = data["entity_type"]
                        logger.info("Processing publication for %s", entity_id)
                        result = orchestrator.process_approval(entity_id, entity_type)
                        if result["status"] == "success":
                            report["processed"].append(entity_id)
                        else:
                            report["failed"].append(entity_id)
                    except Exception as exc:
                        logger.error("Queue processing error: %s", exc, exc_info=True)
        except Exception as exc:
            logger.error("Publication queue processing failed: %s", exc, exc_info=True)
        return report

    # ------------------------------------------------------------------
    # Внутренние шаги конвейера
    # ------------------------------------------------------------------

    def _load_offer(self, offer_id: str) -> Offer:
        return read("offer", offer_id)

    def _run_keyword_research(self, offer: Offer) -> List[Keyword]:
        researcher = KeywordResearcher(llm_client=self.llm_client, lock_manager=self.lock_manager)
        return researcher.research(offer)

    def _run_clustering(self, keywords: List[Keyword]) -> List[Cluster]:
        manager = ClusterManager(llm_client=self.llm_client, lock_manager=self.lock_manager)
        return manager.build_clusters(keywords)

    def _run_article_generation(
        self,
        offer: Offer,
        keywords: List[Keyword],
        clusters: List[Cluster],
    ) -> List[Article]:
        by_cluster = {c.pillar_keyword_id: c for c in clusters if c.pillar_keyword_id}
        articles: List[Article] = []
        for kw in keywords:
            cluster = by_cluster.get(kw.id)
            generator = ArticleGenerator(llm_client=self.llm_client, lock_manager=self.lock_manager)
            articles.append(generator.generate(offer, kw, cluster))
        return articles

    def _run_fact_checking(self, articles: List[Article], offer: Offer) -> List[Article]:
        checker = FactChecker(lock_manager=self.lock_manager)
        return [checker.check(article, offer) for article in articles]

    def _run_html_rendering(self, articles: List[Article], offer: Optional[Offer] = None) -> List[Article]:
        renderer = HTMLRenderer(lock_manager=self.lock_manager)
        rendered: List[Article] = []
        for article in articles:
            html_path = renderer.render(article, offer)
            article.html_path = html_path
            article.status = "rendered"
            rendered.append(article)
        return rendered

    def _run_pinterest_design(self, article: Article) -> Pin:
        designer = PinterestDesigner(llm_client=self.llm_client, lock_manager=self.lock_manager)
        return designer.design(article)

    def _run_telegram(self, article: Article) -> TelegramPost:
        publisher = TelegramPublisher(llm_client=self.llm_client, lock_manager=self.lock_manager)
        return publisher.create_post(article)

    def _run_youtube(self, article: Article) -> YouTubeScript:
        generator = YouTubeScriptGenerator(llm_client=self.llm_client, lock_manager=self.lock_manager)
        return generator.generate_script(article)

    def _run_email(self, article: Article) -> EmailSequence:
        generator = EmailSequenceGenerator(llm_client=self.llm_client, lock_manager=self.lock_manager)
        return generator.generate_sequence(article)

    def _submit_all_for_review(
        self,
        articles: List[Article],
        pins: List[Pin],
        telegram_posts: List[TelegramPost],
    ) -> None:
        from agents.review_manager import ReviewManager

        review_manager = ReviewManager()
        for article in articles:
            if article.html_path and Path(article.html_path).exists():
                review_manager.submit_for_review(article.id, "article", Path(article.html_path))
                logger.info("Submitted article %s for review", article.id)
        for pin in pins:
            if pin.obsidian_path and Path(pin.obsidian_path).exists():
                review_manager.submit_for_review(pin.id, "pin", Path(pin.obsidian_path))
                logger.info("Submitted pin %s for review", pin.id)
        for post in telegram_posts:
            if post.obsidian_path and Path(post.obsidian_path).exists():
                review_manager.submit_for_review(post.id, "telegram_post", Path(post.obsidian_path))
                logger.info("Submitted telegram post %s for review", post.id)

    @staticmethod
    def _step(name: str, status: str, message: str = "") -> dict:
        return {
            "stage": name,
            "status": status,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


def main() -> None:
    """
    CLI-точка входа для Hermes Desktop.
    Пример:
        python hermes_tasks.py run offer_alfa_kids
        python hermes_tasks.py publish
    """
    import json

    if len(sys.argv) < 2:
        print("Usage: python hermes_tasks.py <run|publish> [offer_id]")
        sys.exit(1)

    command = sys.argv[1]
    runner = HermesTaskRunner()

    if command == "run":
        if len(sys.argv) < 3:
            print("Usage: python hermes_tasks.py run <offer_id>")
            sys.exit(1)
        offer_id = sys.argv[2]
        report = runner.run_full_pipeline(offer_id)
        print(json.dumps(report, ensure_ascii=False, indent=2))
    elif command == "publish":
        report = runner.process_publication_queue()
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
