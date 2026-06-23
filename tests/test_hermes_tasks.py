from unittest.mock import MagicMock

import pytest

from hermes_tasks import HermesTaskRunner


class DummyArticle:
    def __init__(self, article_id):
        self.id = article_id
        self.offer_id = "offer_test"
        self.title = "Test"
        self.status = "draft"
        self.html_path = None
        self.obsidian_path = None


class DummyOffer:
    def __init__(self):
        self.id = "offer_test"
        self.name = "Test Offer"
        self.bank = "TestBank"
        self.category = "test"
        self.target_audience = "test"
        self.description = "test"
        self.key_terms = []


class DummyLLM:
    pass


@pytest.fixture()
def runner():
    return HermesTaskRunner(llm_client=DummyLLM())


def test_run_full_pipeline_skeleton(runner, monkeypatch):
    calls = []

    def fake_keywords(offer):
        calls.append("keywords")
        return []

    def fake_clusters(keywords):
        calls.append("clusters")
        return []

    def fake_articles(offer, keywords, clusters):
        calls.append("articles")
        return [DummyArticle("article_001")]

    def fake_fact(articles, offer):
        calls.append("fact_check")
        return articles

    def fake_render(articles, offer):
        for a in articles:
            a.html_path = "Obsidian/Articles/html/article_001.html"
        calls.append("render")
        return articles

    def fake_pin(article):
        calls.append("pin")
        dummy = MagicMock()
        dummy.obsidian_path = "Obsidian/Pins/pin_001.md"
        return dummy

    def fake_telegram(article):
        calls.append("telegram")
        return MagicMock(obsidian_path="Obsidian/Telegram/tg_001.md")

    def fake_youtube(article):
        calls.append("youtube")
        return MagicMock()

    def fake_email(article):
        calls.append("email")
        return MagicMock()

    monkeypatch.setattr(runner, "_load_offer", lambda oid: DummyOffer())
    monkeypatch.setattr(runner, "_run_keyword_research", fake_keywords)
    monkeypatch.setattr(runner, "_run_clustering", fake_clusters)
    monkeypatch.setattr(runner, "_run_article_generation", fake_articles)
    monkeypatch.setattr(runner, "_run_fact_checking", fake_fact)
    monkeypatch.setattr(runner, "_run_html_rendering", fake_render)
    monkeypatch.setattr(runner, "_run_pinterest_design", fake_pin)
    monkeypatch.setattr(runner, "_run_telegram", fake_telegram)
    monkeypatch.setattr(runner, "_run_youtube", fake_youtube)
    monkeypatch.setattr(runner, "_run_email", fake_email)
    monkeypatch.setattr(runner, "_submit_all_for_review", lambda *a, **kw: None)

    report = runner.run_full_pipeline("offer_test")
    assert report["status"] == "success"
    assert "load_offer" in [s["stage"] for s in report["steps"]]
    assert "article_001" in report["created"].get("articles", [])
    assert "keywords" in calls
    assert "clusters" in calls
    assert "articles" in calls
    assert "fact_check" in calls
    assert "render" in calls


def test_process_publication_queue_structure(runner):
    report = runner.process_publication_queue()
    assert "processed" in report
    assert "failed" in report
