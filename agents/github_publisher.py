from __future__ import annotations

import subprocess
import shutil
from pathlib import Path
from typing import List, Optional

from agents.lock_manager import LockManager


class GitHubPublisher:
    def __init__(
        self,
        ready_dir: str = "data/Exports/Ready_To_Publish",
        blog_repo_dir: Optional[str] = None,
        lock_manager: Optional[LockManager] = None
    ):
        self.ready_dir = Path(ready_dir)
        self.blog_repo_dir = Path(blog_repo_dir) if blog_repo_dir else Path("blog_repo")
        self.lock_manager = lock_manager or LockManager()
        self.blog_repo_dir.mkdir(parents=True, exist_ok=True)

    def publish_approved_articles(self) -> List[str]:
        if not self.ready_dir.exists():
            return []
        
        published: List[str] = []
        html_files = sorted(self.ready_dir.glob("*.html"))
        
        if not html_files:
            return []
        
        commit_message = "Auto-publish: " + ", ".join(
            [f.stem for f in html_files]
        )
        
        locked_id = None
        for html_file in html_files:
            acquired, msg = self.lock_manager.acquire_lock(
                "article", html_file.stem, "github_publisher"
            )
            if acquired:
                locked_id = html_file.stem
                lock_acquired = True
                break
        
        if not lock_acquired:
            raise RuntimeError("Не удалось захватить блокировку для публикации")
        
        try:
            for html_file in html_files:
                dest = self.blog_repo_dir / html_file.name
                shutil.copy2(html_file, dest)
            
            self._git_add_and_commit(commit_message)
            self._git_push()
            
            for html_file in html_files:
                html_file.unlink()
                published.append(html_file.stem)
        except Exception:
            raise
        finally:
            if locked_id:
                self.lock_manager.release_lock("article", locked_id)
        
        return published

    def _git_add_and_commit(self, message: str) -> None:
        try:
            subprocess.run(
                ["git", "add", "."],
                cwd=str(self.blog_repo_dir),
                check=True,
                capture_output=True
            )
            subprocess.run(
                ["git", "commit", "-m", message, "--allow-empty"],
                cwd=str(self.blog_repo_dir),
                check=True,
                capture_output=True
            )
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(
                f"Git commit failed: {exc.stderr.decode()}"
            ) from exc

    def _git_push(self) -> None:
        try:
            result = subprocess.run(
                ["git", "push"],
                cwd=str(self.blog_repo_dir),
                check=True,
                capture_output=True
            )
        except subprocess.CalledProcessError as exc:
            stderr = exc.stderr.decode() if exc.stderr else ""
            if "No configured push destination" in stderr:
                return
            if "fatal" in stderr.lower() or "error" in stderr.lower():
                raise RuntimeError(
                    f"Git push failed: {stderr}"
                ) from exc
