from __future__ import annotations

import re
from typing import List, Optional

from pydantic import BaseModel, Field

from agents.lock_manager import LockManager
from agents.obsidian_parser import read, write
from agents.shared_models import Article, Offer


class FinancialClaim(BaseModel):
    raw: str
    type: str
    verified: bool
    note: str


class FactChecker:
    def __init__(self, lock_manager: Optional[LockManager] = None):
        self.lock_manager = lock_manager or LockManager()

    def check(self, article: Article, offer: Offer) -> Article:
        claims = self._extract_financial_claims(article.content or "")
        checked: List[str] = []
        for claim in claims:
            if self._is_verified(claim, offer):
                checked.append(
                    f"[Verified against Offer] {claim.raw}"
                )
            else:
                checked.append(
                    f"[Requires Manual Verification] {claim.raw}"
                )
        article.fact_check_notes = checked
        article.status = "fact_checking"
        article.requires_manual_verification = True
        acquired, msg = self.lock_manager.acquire_lock(
            "article", article.id, "fact_checker"
        )
        if not acquired:
            raise RuntimeError(f"Не удалось захватить блокировку: {msg}")
        try:
            path = write(article, "article")
            article.obsidian_path = path
            article.markdown_path = path
            return article
        finally:
            self.lock_manager.release_lock("article", article.id)

    def _extract_financial_claims(self, text: str) -> List[FinancialClaim]:
        claims: List[FinancialClaim] = []
        patterns = [
            (r"(?<!\w)\d+(?:[.,]\d+)?\s*%(?!\w)", "percentage"),
            (r"(?<!\w)\d+(?:[.,]\d+)?\s*(?:руб|рубл|₽)(?!\w)", "money"),
            (r"\bот\s+\d+\s+лет\b", "age"),
            (r"\b\d+\s*(?:год|года|лет)\b", "duration"),
            (r"(?<!\w)\d+(?:[.,]\d+)?\s*(?:бесплатн|платн)(?!\w)", "price"),
            (r"(?<!\w)\d+(?:[.,]\d+)?\s*(?:кэшбэк|cashback|балл|бонус)(?!\w)", "cashback"),
            (r"(?<!\w)\d+(?:[.,]\d+)?\s*(?:ставк|процент)(?!\w)", "rate"),
        ]
        for pattern, claim_type in patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                claims.append(
                    FinancialClaim(
                        raw=match.group(),
                        type=claim_type,
                        verified=False,
                        note="",
                    )
                )
        return claims

    def _is_verified(self, claim: FinancialClaim, offer: Offer) -> bool:
        haystack_parts = [
            offer.name,
            offer.bank,
            offer.category,
            offer.target_audience,
            offer.offer_url,
            offer.affiliate_url,
            offer.description,
        ]
        if offer.key_terms:
            haystack_parts.extend(offer.key_terms)
        
        haystack = " ".join(filter(None, haystack_parts))
        haystack_lower = haystack.lower()
        claim_lower = claim.raw.lower()

        if claim_lower in haystack_lower:
            return True

        numbers = re.findall(r"\d+(?:[.,]\d+)?", claim_lower)
        if numbers:
            verified_numbers = re.findall(r"\d+(?:[.,]\d+)?", haystack_lower)
            if any(num in verified_numbers for num in numbers):
                return True
        return False
