# AI_FINANCE_FACTORY — PROJECT STATE

## Общий статус проекта

Проект завершен. Все 6 фаз реализованы и покрыты тестами.

Архитектура утверждена и считается закрытой.

Новые архитектурные решения допускаются только при обнаружении реальной технической проблемы.

---

## Цель проекта

Построить автономный контентный конвейер для финансовых офферов:

Offer → Research → Cluster → Article → Fact Check → HTML → Pinterest/Telegram/YouTube/Email → Review Queue → Publish → Analytics

---

## Реализованная архитектура

### Ядро (Phase 1)
- `agents/shared_models.py` — Pydantic-модели (Offer, Keyword, Cluster, Article, Pin, TelegramPost, EmailSequence, YouTubeScript, Report, PipelineState, LockFile)
- `agents/offer_loader.py` — загрузчик офферов из Obsidian
- `agents/idempotency.py` — защита от дублирования
- `agents/lock_manager.py` — файловые блокировки
- `agents/pipeline_manager.py` — управление состоянием пайплайна

### Мост Obsidian (Phase 2)
- `agents/obsidian_parser.py` — чтение/запись MD+YAML ↔ Pydantic
- Папка `Obsidian/` с подпапками: Offers, Keywords, Clusters, Articles/drafts, Articles/html, Pins, Telegram, YouTube, Email, Reports
- Шаблоны YAML для всех сущностей

### Ядро агентов (Phase 3)
- `agents/keyword_researcher.py` — генерация ключевых слов (10-15 шт.) с разделением по intent
- `agents/cluster_manager.py` — кластеризация ключей, определение Pillar Page
- `agents/article_generator.py` — генерация SEO-статей (Markdown)
- `agents/fact_checker.py` — валидация финансовых цифр (проценты, суммы, возраст)
- `agents/html_renderer.py` — рендеринг Markdown → HTML с Jinja2 + Schema.org
- `agents/pinterest_designer.py` — метаданные для Pinterest (title, description, tags, image_prompt)
- `agents/telegram_publisher.py` — генерация постов для Telegram с UTM
- `agents/youtube_script_generator.py` — сценарии YouTube (Hook, Intro, Main, CTA)
- `agents/email_sequence_generator.py` — серии email-писем (3 письма, UTM)

### Проверка и публикация (Phase 4)
- `agents/review_manager.py` — очередь ручной проверки (submit/approve/reject)
- `agents/github_publisher.py` — атомарная публикация HTML на GitHub Pages
- `agents/pinterest_uploader.py` — загрузка пинов на Pinterest API v5
- `agents/publication_orchestrator.py` — единый оркестратор Human Review flow

### Интеграция с Hermes (Phase 5)
- `hermes_tasks.py` — точка входа для Hermes Desktop
- `hermes_config.yaml` — конфигурация задач и канбан-доски
- `HERMES_SETUP.md` — инструкция по подключению

### Аналитика и память (Phase 6)
- `agents/analytics_agent.py` — сбор метрик, ТОП-5/weak5, рекомендации
- `agents/knowledge_memory_agent.py` — проверка уникальности тем (cannibalization check)
- `scripts/generate_mock_metrics.py` — генерация фейковых метрик для тестов

---

## Статус фаз

| Фаза | Статус | Тесты |
|------|--------|-------|
| Phase 0: Audit & Cleanup | ✅ DONE | — |
| Phase 1: Foundation | ✅ DONE | 4 passed |
| Phase 2: Data Contracts & Obsidian | ✅ DONE | 7 passed |
| Phase 3: Core Agents | ✅ DONE | 32 passed |
| Phase 4: Review & Publishing | ✅ DONE | 44 passed |
| Phase 5: Hermes Integration | ✅ DONE | 46 passed |
| Phase 6: Analytics & Memory | ✅ DONE | 50 passed |

**Итого: 50+ тестов, все проходят.**

---

## Правила проекта

1. Файлы офферов в `Obsidian/Offers/` — источник истины. Не генерировать автоматически.
2. Все сущности — через Pydantic модели из `shared_models.py`.
3. Все операции записи — через `LockManager`.
4. Идемпотентность — через `IdempotencyManager`.
5. Human Review — обязательна перед любой публикацией.
6. Финансовые цифры — всегда `requires_manual_verification: True`.

---

## Последнее обновление

2026-06-23 — Project Complete. All 6 phases implemented. Full automation pipeline ready.
