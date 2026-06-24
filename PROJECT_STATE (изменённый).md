# PROJECT_STATE.md

# AI_FINANCE_FACTORY

Текущий статус проекта и дорожная карта.

---

# Общая информация

Проект: AI Finance Factory

Цель MVP:

Автоматизированный пайплайн создания финансовых статей:

Offer
> Markdown
> HTML

Без AI-генерации.

Без Pinterest.

Без аналитики.

Без внешних API.

Главная задача MVP — доказать работоспособность архитектуры и пайплайна.

---

# Статус проекта

Дата обновления: 2026-06-21

Текущая стадия:

Phase 1 Completed

---

# Финальная архитектура (зафиксирована)

```text
AI_FINANCE_FACTORY/

+-- .env
+-- .gitignore
+-- README.md
+-- requirements.txt
+-- PROJECT_STATE.md
+-- NEXT_TASKS.md
¦
+-- agents/
¦   +-- __init__.py
¦   +-- config.py
¦   +-- shared_models.py
¦   +-- lock_manager.py
¦   +-- idempotency.py
¦   +-- offer_loader.py
¦   L-- pipeline_manager.py
¦
+-- data/
¦   +-- Offers/
¦   +-- Articles/
¦   ¦   +-- drafts/
¦   ¦   L-- html/
¦   +-- Pipeline_Status/
¦   L-- Logs/
¦
+-- scripts/
¦   L-- pipeline.py
¦
+-- templates/
¦
L-- tests/
    +-- test_models.py
    +-- test_lock_manager.py
    +-- test_idempotency.py
    L-- test_offer_loader.py
```

---

# MVP Scope (зафиксирован)

Версия 0.1 умеет:

* Загружать оффер
* Валидировать оффер
* Проверять идемпотентность
* Управлять lock-файлами
* Создавать Markdown-статью
* Создавать HTML-версию статьи
* Создавать Pipeline State

---

# Что НЕ входит в MVP

Не реализуется до завершения MVP:

* Pinterest
* Gemini
* OpenAI
* Кластеризация
* Аналитика
* SEO-оптимизация
* Review Queue
* Fact Checking
* Auto Publishing
* Самообучение

Любые новые идеи откладываются до завершения MVP.

---

# Этап 0. Инфраструктура проекта

Статус:

COMPLETED

Сделано:

* Git
* Virtual Environment
* Requirements
* Pytest
* Структура репозитория

Результат:

Рабочее окружение готово.

---

# Этап 1. Foundation Layer

Статус:

COMPLETED

Реализовано:

config.py

Назначение:

* Централизованное хранение путей
* Конфигурация проекта
* Переменные окружения

---

shared_models.py

Реализованы модели:

* Offer
* LockFile
* PipelineState
* PipelineHistoryItem

---

lock_manager.py

Реализовано:

* acquire_lock()
* release_lock()
* cleanup_expired_locks()

Проверено тестами.

---

idempotency.py

Реализовано:

* article_exists()

Проверено тестами.

---

offer_loader.py

Реализовано:

* загрузка оффера
* YAML parsing
* валидация через Pydantic

Проверено тестами.

---

# Тесты

Текущий результат:

4 / 4 PASSED

Список тестов:

* test_models.py
* test_lock_manager.py
* test_idempotency.py
* test_offer_loader.py

Последний успешный запуск:

```bash
pytest -v
```

Результат:

```text
4 passed
```

---

# Текущее состояние данных

Существуют:

data/Offers/

Содержимое:

* offer_alfa_kids.md
* offer_test.md

---

Рабочие директории:

* data/Articles/
* data/Pipeline_Status/
* data/Logs/
* .locks/

---

# Следующий этап

Phase 2

Pipeline Core

Статус:

NOT STARTED

---

# Следующий файл

agents/pipeline_manager.py

Назначение:

* управление PipelineState
* создание статусов
* изменение статусов
* история выполнения
* ретраи
* обработка ошибок

---

# После него

scripts/pipeline.py

Команды:

```bash
python scripts/pipeline.py run --offer offer_test
```

```bash
python scripts/pipeline.py doctor
```

---

# Цель ближайшего этапа

Получить первый полностью рабочий сценарий:

```bash
python scripts/pipeline.py run --offer offer_test
```

Результат выполнения:

```text
data/

Articles/
+-- drafts/
¦   L-- article_001.md

Articles/
L-- html/
    L-- article_001.html

Pipeline_Status/
L-- article_001.json
```

---

# Критерий завершения MVP Core

Условия:

* Offer успешно загружается
* Создаётся Markdown
* Создаётся HTML
* Создаётся Pipeline Status
* Повторный запуск не создаёт дубликаты
* Все тесты проходят

---

# Правило проекта

Архитектура считается закрытой.

Новые подсистемы не добавляются до завершения MVP.

Приоритет:

1. Pipeline Manager
2. CLI Pipeline
3. Первый End-to-End запуск
4. Расширение функционала

Любые новые идеи фиксируются отдельно и не влияют на MVP.

---

# Последний завершённый коммит

```bash
git commit -m "Add project state documentation"
```

Commit:

fdf87d2

---

# Следующая контрольная точка

Успешное выполнение команды:

```bash
python scripts/pipeline.py run --offer offer_test
```

с созданием:

* article_001.md
* article_001.html
* article_001.json

После достижения этой точки проект переходит в стадию MVP Validation.
