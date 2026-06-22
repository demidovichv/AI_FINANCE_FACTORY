# AI_FINANCE_FACTORY — PROJECT STATE

## Общий статус проекта

Проект находится в стадии активной разработки.

Архитектура утверждена и считается закрытой.

Новые архитектурные решения допускаются только при обнаружении реальной технической проблемы.

---

# Финальная цель проекта

Построить автономный контентный конвейер для финансовых офферов:

Offer
→ Research
→ Article
→ HTML
→ Pinterest
→ Analytics
→ Reports

---

# Phase 0 — Infrastructure

Статус: ✅ DONE

Результат:

* Git и репозиторий инициализированы
* Virtual Environment настроен
* requirements.txt создан
* pytest настроен
* базовая структура проекта создана

Выполнено:

* .gitignore
* requirements.txt
* pytest.ini
* структура каталогов

---

# Phase 1 — Foundation Layer

Статус: ✅ DONE

Цель:

Создать базовые строительные блоки системы.

Реализовано:

agents/config.py

Ответственность:

* пути проекта
* директории данных
* переменные окружения
* настройки системы

agents/shared_models.py

Ответственность:

* Pydantic-модели
* Offer
* LockFile
* PipelineState

agents/lock_manager.py

Ответственность:

* acquire_lock()
* release_lock()
* cleanup_expired_locks()

agents/idempotency.py

Ответственность:

* защита от повторной обработки

agents/offer_loader.py

Ответственность:

* загрузка Offer из Markdown/YAML

---

# Тесты Foundation Layer

Статус: ✅ PASSED

Пройдены:

* test_models.py
* test_lock_manager.py
* test_idempotency.py
* test_offer_loader.py

Текущий результат:

4 passed

---

# Phase 2 — Pipeline Core

Статус: ⏳ IN PROGRESS

Следующий этап разработки.

Цель:

Построить управляющий слой пайплайна.

Необходимо реализовать:

agents/pipeline_manager.py

Функции:

* create_pipeline_state()
* load_pipeline_state()
* save_pipeline_state()
* update_status()
* append_history()

Также необходимо создать:

tests/test_pipeline_manager.py

После этого создать:

scripts/pipeline.py

Команды:

python scripts/pipeline.py run --offer offer_test

python scripts/pipeline.py doctor

---

# Цель завершения Phase 2

После выполнения команды:

python scripts/pipeline.py run --offer offer_test

должны автоматически создаваться:

data/Articles/drafts/article_001.md

data/Articles/html/article_001.html

data/Pipeline_Status/article_001.json

Даже если контент пока является заглушкой.

Главная цель:

Проверить работоспособность полного конвейера.

---

# Phase 3 — Content Layer

Статус: 🔒 LOCKED

Не начинать до полного завершения Phase 2.

Планируемые модули:

agents/content_generator.py

agents/template_engine.py

agents/html_renderer.py

Цель:

Offer
→ Markdown
→ HTML

---

# Phase 4 — AI Layer

Статус: 🔒 LOCKED

Не начинать до полного завершения Phase 3.

Планируемые интеграции:

* Gemini
* OpenAI
* Claude

Цель:

Генерация реального контента.

---

# Phase 5 — Pinterest Layer

Статус: 🔒 LOCKED

Планируемые модули:

* pin_generator.py
* image_generator.py
* pinterest_publisher.py

Цель:

Автоматическая публикация контента в Pinterest.

---

# Phase 6 — Analytics Layer

Статус: 🔒 LOCKED

Планируемые функции:

* CTR
* EPC
* RPC
* ROI
* отчёты

---

# Правила проекта

1. Не перескакивать через фазы.

2. Каждый новый модуль сначала покрывается тестами.

3. Любой этап считается завершённым только после прохождения pytest.

4. После завершения каждой фазы обновлять PROJECT_STATE.md.

5. NEXT_TASKS.md всегда содержит только ближайшие задачи.

---

# Последние завершённые этапы

✅ Infrastructure

✅ Foundation Layer

Текущая активная задача:

➡ Phase 2 — Pipeline Core
