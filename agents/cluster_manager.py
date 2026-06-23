from __future__ import annotations

import uuid
from collections import defaultdict
from typing import List, Optional

from pydantic import BaseModel, Field

from agents.lock_manager import LockManager
from agents.obsidian_parser import write
from agents.shared_models import Cluster, Keyword


class ClusterManager:
    def __init__(self, llm_client=None, lock_manager: Optional[LockManager] = None):
        self.llm_client = llm_client
        self.lock_manager = lock_manager or LockManager()

    def build_clusters(self, keywords: List[Keyword]) -> List[Cluster]:
        groups = self._group_keywords(keywords)
        clusters: List[Cluster] = []
        for group_key, group_keywords in groups.items():
            pillar = max(group_keywords, key=lambda kw: kw.search_volume or 0)
            cluster = Cluster(
                id=f"cluster_{uuid.uuid4().hex[:8]}",
                name=group_key,
                pillar_keyword_id=pillar.id,
                related_keyword_ids=[kw.id for kw in group_keywords if kw.id != pillar.id],
            )
            saved = self._save_cluster(cluster)
            clusters.append(saved)
        return clusters

    def _group_keywords(self, keywords: List[Keyword]) -> dict[str, List[Keyword]]:
        if not keywords:
            return {}
        if self.llm_client is not None:
            return self._group_with_llm(keywords)
        return self._group_with_heuristic(keywords)

    def _group_with_heuristic(self, keywords: List[Keyword]) -> dict[str, List[Keyword]]:
        groups: dict[str, List[Keyword]] = defaultdict(list)
        for kw in keywords:
            words = kw.text.lower().split()
            core = words[0] if words else kw.text.lower()
            if core in {"детский", "детская", "дети"}:
                group_name = "Детские карты"
            elif core in {"кэшбэк", "cashback"}:
                group_name = "Кэшбэк карты"
            elif core in {"накопить", "сбережения", "вклад"}:
                group_name = "Сбережения и вклады"
            elif core in {"кредит", "кредитный"}:
                group_name = "Кредиты"
            elif core in {"ипотека"}:
                group_name = "Ипотека"
            elif core in {"инвестиции", "инвестировать"}:
                group_name = "Инвестиции"
            elif core in {"страхование", "страховка"}:
                group_name = "Страхование"
            else:
                group_name = f"Прочее: {core.capitalize()}"
            groups[group_name].append(kw)
        return dict(groups)

    def _group_with_llm(self, keywords: List[Keyword]) -> dict[str, List[Keyword]]:
        prompt = (
            "Сгруппируй ключевые слова по тематическим кластерам.\n"
            "Ключевые слова:\n"
            + "\n".join([f"- {kw.text} ({kw.intent})" for kw in keywords])
            + "\nВерни JSON с полем clusters: список {name: string, keyword_texts:[]}."
        )
        raw = self.llm_client.generate(prompt)
        import json, re
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            return self._group_with_heuristic(keywords)
        try:
            data = json.loads(match.group())
            groups: dict[str, List[Keyword]] = defaultdict(list)
            by_text = {kw.text: kw for kw in keywords}
            for item in data.get("clusters", []):
                for text in item.get("keyword_texts", []):
                    if text in by_text:
                        groups[item.get("name", "Прочее")].append(by_text[text])
            return dict(groups)
        except Exception:
            return self._group_with_heuristic(keywords)

    def _save_cluster(self, cluster: Cluster) -> Cluster:
        acquired, msg = self.lock_manager.acquire_lock("cluster", cluster.id, "cluster_manager")
        if not acquired:
            raise RuntimeError(f"Не удалось захватить блокировку: {msg}")
        try:
            path = write(cluster, "cluster")
            cluster.obsidian_path = path
            return cluster
        finally:
            self.lock_manager.release_lock("cluster", cluster.id)
