from __future__ import annotations

import markdown
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from jinja2 import Environment, FileSystemLoader, Template

from agents.lock_manager import LockManager
from agents.obsidian_parser import read
from agents.shared_models import Article, Offer


class HTMLRenderer:
    def __init__(self, lock_manager: Optional[LockManager] = None):
        self.lock_manager = lock_manager or LockManager()
        self._template: Optional[Template] = None

    def render(self, article: Article, offer: Optional[Offer] = None) -> str:
        article_id = article.id
        acquired, msg = self.lock_manager.acquire_lock("article", article_id, "html_renderer")
        if not acquired:
            raise RuntimeError(f"Не удалось захватить блокировку: {msg}")
        try:
            html_content = self._render_html(article, offer)
            article.content_html = html_content
            article.status = "rendered"
            path = self._save_html(article, html_content)
            article.obsidian_path = path
            return path
        finally:
            self.lock_manager.release_lock("article", article_id)

    def _render_html(self, article: Article, offer: Optional[Offer] = None) -> str:
        md_content = article.content or ""
        body_html = markdown.markdown(md_content, extensions=["extra", "codehilite"])
        
        cta_button = None
        if offer and offer.affiliate_url:
            cta_button = {
                "href": offer.affiliate_url,
                "text": f"Оформить {offer.name}",
            }
        
        template = self._load_template()
        now = datetime.now(timezone.utc)
        return template.render(
            title=article.title or article.id,
            meta_description=article.meta_description or "",
            content=body_html,
            cta_button=cta_button,
            published_date=now.isoformat(),
            modified_date=now.isoformat(),
        )

    def _load_template(self) -> Template:
        if self._template is not None:
            return self._template
        
        template_dir = Path(__file__).resolve().parent.parent / "templates" / "html"
        if not template_dir.exists():
            template_dir.mkdir(parents=True, exist_ok=True)
        
        env = Environment(loader=FileSystemLoader(str(template_dir)))
        try:
            template = env.get_template("base.html")
        except Exception:
            template = env.from_string(self._fallback_template())
        
        self._template = template
        return template

    def _fallback_template(self) -> str:
        return """<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <meta name="description" content="{{ meta_description }}">
    <script type="application/ld+json">
    {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": "{{ title }}",
        "description": "{{ meta_description }}"
    }
    </script>
</head>
<body>
    <article>
        <header>
            <h1>{{ title }}</h1>
        </header>
        <div class="content">
            {{ content | safe }}
        </div>
        <footer>
            {% if cta_button %}
            <a href="{{ cta_button.href }}" class="cta-button">{{ cta_button.text }}</a>
            {% endif %}
        </footer>
    </article>
</body>
</html>"""

    def _save_html(self, article: Article, html_content: str) -> str:
        html_dir = Path(__file__).resolve().parent.parent / "Obsidian" / "Articles" / "html"
        html_dir.mkdir(parents=True, exist_ok=True)
        slug = article.slug or article.id
        target = html_dir / f"{slug}.html"
        target.write_text(html_content, encoding="utf-8")
        article.html_path = str(target)
        return str(target)
