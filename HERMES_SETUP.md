# Настройка Hermes Desktop для AI_FINANCE_FACTORY

## Russian (Русский)

### Предварительные требования
- Python 3.12+
- Hermes Desktop (установлен и запущен)
- Git (для публикации на GitHub Pages)

### Быстрый старт

1. **Откройте Hermes Desktop.**

2. **Импортируйте конфигурацию задач:**
   - В Hermes Desktop перейдите в раздел "Tasks" / "Задачи"
   - Нажмите "Import" / "Импорт"
   - Выберите файл `hermes_config.yaml` в корне проекта
   - Задачи появятся в списке:
     - `task_full_pipeline` — полный конвейер
     - `task_publish_queue` — публикация из очереди
     - `task_review_list` — список на проверку

3. **Запустите полный конвейер:**
   - Выберите задачу `task_full_pipeline`
   - В поле `offer_id` введите ID оффера (например, `offer_alfa_kids`)
   - Нажмите "Run"
   - Hermes вызовет `python hermes_tasks.py run offer_alfa_kids`
   - Прогресс будет отображаться в консоли Hermes и логироваться в `data/Logs/hermes_tasks.log`

4. **Публикация одобренного контента:**
   - После ручной проверки в Hermes выберите `task_publish_queue`
   - Нажмите "Run"
   - Система переместит одобренные файлы на GitHub Pages / Pinterest

5. **Канбан-доска:**
   - В Hermes Desktop откройте раздел "Kanban"
   - Добавьте колонки: researching → writing → review → rendering → ready → published → failed
   - Обновляйте статусы через Pipeline State файлы в `data/Pipeline_Status/`

### Переменные окружения
Создайте файл `.env` в корне проекта или задайте переменные в Hermes:
```
PINTEREST_ACCESS_TOKEN=your_token_here  # опционально, для загрузки на Pinterest
```

### Интеграция LLM (Hermes AIAgent)
Hermes Desktop предоставляет AI-клиент (AIAgent). Чтобы использовать его вместо заглушек:

```python
from agents.hermes_tasks import HermesTaskRunner

# В коде Hermes или в кастомном скрипте:
runner = HermesTaskRunner(llm_client=hermes_ai_agent)
report = runner.run_full_pipeline("offer_alfa_kids")
```

Если `llm_client` не передан — используются встроенные моки (Mock-генерация).

---

## English

### Prerequisites
- Python 3.12+
- Hermes Desktop (installed and running)
- Git (for GitHub Pages publishing)

### Quick Start

1. **Open Hermes Desktop.**

2. **Import task configuration:**
   - Go to "Tasks" section in Hermes Desktop
   - Click "Import"
   - Select `hermes_config.yaml` in the project root
   - Tasks will appear:
     - `task_full_pipeline` — full content pipeline
     - `task_publish_queue` — publish from queue
     - `task_review_list` — list pending reviews

3. **Run full pipeline:**
   - Select `task_full_pipeline`
   - Enter `offer_id` (e.g., `offer_alfa_kids`)
   - Click "Run"
   - Hermes will execute: `python hermes_tasks.py run offer_alfa_kids`
   - Progress appears in Hermes console and is logged to `data/Logs/hermes_tasks.log`

4. **Publish approved content:**
   - After manual review, select `task_publish_queue`
   - Click "Run"
   - Approved files are moved to GitHub Pages / Pinterest

5. **Kanban Board:**
   - Open "Kanban" section in Hermes Desktop
   - Add columns: researching → writing → review → rendering → ready → published → failed
   - Update statuses via Pipeline State files in `data/Pipeline_Status/`

### Environment Variables
Create `.env` in the project root or set variables in Hermes:
```
PINTEREST_ACCESS_TOKEN=your_token_here  # optional, for Pinterest uploads
```

### LLM Integration (Hermes AIAgent)
Hermes Desktop provides an AI-agent client. To use it instead of mocks:

```python
from agents.hermes_tasks import HermesTaskRunner

runner = HermesTaskRunner(llm_client=hermes_ai_agent)
report = runner.run_full_pipeline("offer_alfa_kids")
```

If `llm_client` is not provided — built-in mocks are used.
