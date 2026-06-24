# NEXT TASKS

## Текущий этап

Phase 2 — Pipeline Core

---

# Задача 1

Создать файл:

agents/pipeline_manager.py

Реализовать функции:

* create_pipeline_state()
* load_pipeline_state()
* save_pipeline_state()
* update_status()
* append_history()

---

# Задача 2

Создать тесты:

tests/test_pipeline_manager.py

Проверить:

* создание состояния
* сохранение состояния
* загрузку состояния
* обновление статуса
* историю изменений

Ожидаемый результат:

pytest проходит успешно.

---

# Задача 3

Создать:

scripts/pipeline.py

Поддерживаемые команды:

python scripts/pipeline.py run --offer offer_test

python scripts/pipeline.py doctor

---

# Задача 4

Реализовать первый рабочий сценарий

Команда:

python scripts/pipeline.py run --offer offer_test

должна создавать:

data/Articles/drafts/article_001.md

data/Articles/html/article_001.html

data/Pipeline_Status/article_001.json

Контент пока может быть тестовым.

---

# Критерий завершения Phase 2

Все тесты проходят.

Команда run выполняется без ошибок.

Создаются все три файла:

* article_001.md
* article_001.html
* article_001.json

После этого разрешается переход к Phase 3.

---

# Запрещено до завершения Phase 2

Не создавать:

* Pinterest-модули
* Gemini-интеграцию
* SEO-модули
* аналитику
* кластеризацию
* генерацию изображений

Сначала должен заработать базовый конвейер.

---

Следующая задача для реализации:

? agents/pipeline_manager.py
