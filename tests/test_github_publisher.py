from pathlib import Path

import pytest

from agents.github_publisher import GitHubPublisher
from agents.lock_manager import LockManager


@pytest.fixture()
def temp_roots(tmp_path: Path):
    ready = tmp_path / "Ready_To_Publish"
    ready.mkdir(parents=True)
    blog_repo = tmp_path / "blog_repo"
    blog_repo.mkdir()
    import subprocess
    subprocess.run(["git", "init"], cwd=str(blog_repo), check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=str(blog_repo), check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=str(blog_repo), check=True, capture_output=True)
    return ready, blog_repo, tmp_path


def test_publish_approved_articles_moves_files(temp_roots) -> None:
    ready, blog_repo, tmp_path = temp_roots
    html_file = ready / "article_001.html"
    html_file.write_text("<html><body>Article 1</body></html>", encoding="utf-8")
    
    publisher = GitHubPublisher(
        ready_dir=str(ready),
        blog_repo_dir=str(blog_repo),
        lock_manager=LockManager(lock_dir=str(tmp_path / ".locks"))
    )
    published = publisher.publish_approved_articles()
    
    assert "article_001" in published
    assert not html_file.exists()
    assert (blog_repo / "article_001.html").exists()


def test_publish_empty_ready_dir(temp_roots) -> None:
    ready, blog_repo, tmp_path = temp_roots
    publisher = GitHubPublisher(
        ready_dir=str(ready),
        blog_repo_dir=str(blog_repo),
        lock_manager=LockManager(lock_dir=str(tmp_path / ".locks"))
    )
    published = publisher.publish_approved_articles()
    assert published == []
