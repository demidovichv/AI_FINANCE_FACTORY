# AI_FINANCE_FACTORY

## PROJECT STATE

Last Updated: 2026-06-21

---

# PROJECT OVERVIEW

AI_FINANCE_FACTORY is an automated content production system for affiliate financial offers.

Pipeline:

Offer
→ Article
→ Pinterest Content
→ Pins
→ Reports

Goal:

One affiliate offer should be transformed into multiple SEO articles, Pinterest articles, Pinterest pins and reports through a controlled automated pipeline.

---

# CURRENT STATUS

Phase 1: COMPLETE ✅

Phase 2: NOT STARTED ⏳

Phase 3: NOT STARTED ⏳

Phase 4: NOT STARTED ⏳

---

# COMPLETED WORK

## Phase 1 — Core Foundation

Status: COMPLETE

### Implemented Components

#### agents/shared_models.py

Implemented Pydantic models:

* Offer
* Article
* PipelineHistoryItem
* PipelineState
* LockFile

---

#### agents/offer_loader.py

Implemented.

Responsibilities:

* Load offer markdown files
* Extract YAML metadata
* Validate data using Offer model
* Return Offer object

---

#### agents/idempotency.py

Implemented.

Responsibilities:

* Detect already processed offers
* Prevent duplicate article generation

Main method:

```python
article_exists(offer_id)
```

---

#### agents/lock_manager.py

Implemented.

Responsibilities:

* Create lock files
* Prevent parallel execution
* Release locks
* Remove expired locks

Methods:

```python
acquire_lock()
release_lock()
cleanup_expired_locks()
```

---

# TESTS

Implemented:

* tests/test_models.py
* tests/test_offer_loader.py
* tests/test_idempotency.py
* tests/test_lock_manager.py

Current Result:

```text
4 passed
```

---

# DATA STRUCTURE

Current project structure:

```text
agents/
data/
tests/
templates/
scripts/
```

---

## Existing Data Directories

```text
data/Offers/
data/Articles/
data/Pipeline_Status/
data/Logs/
```

---

## Existing Offer

```text
data/Offers/offer_alfa_kids.md
```

Contains:

```yaml
id:
name:
bank:
offer_url:
affiliate_url:
status:
created_at:
```

---

# ARCHITECTURE RULES

## Rule 1

Offer files are the source of truth.

Never generate offer files automatically.

---

## Rule 2

All offer loading must use:

```python
OfferLoader.load()
```

---

## Rule 3

All entities must be represented by Pydantic models.

Avoid raw dictionaries whenever possible.

---

## Rule 4

All generation operations must be idempotent.

Before creating content:

```python
IdempotencyManager.article_exists()
```

must be checked.

---

## Rule 5

All write operations must use locking.

Before processing:

```python
acquire_lock()
```

After processing:

```python
release_lock()
```

---

## Rule 6

Phase 1 architecture is considered stable.

Do not refactor existing Phase 1 components unless a confirmed bug exists.

---

# NEXT TARGET

## Phase 2 — Article Generation

Status: NOT STARTED

---

## To Implement

### agents/article_generator.py

Input:

```python
Offer
```

Output:

```python
Article
```

Responsibilities:

* Generate article draft
* Save markdown file
* Create Article object
* Update PipelineState

---

### Prompt Templates

Create:

```text
templates/article_prompt.md
templates/seo_prompt.md
templates/pinterest_prompt.md
```

---

### Draft Storage

Directory:

```text
data/Articles/drafts/
```

---

### HTML Storage

Directory:

```text
data/Articles/html/
```

---

### Pipeline Integration

Required states:

```text
init
processing
success
failed
```

---

### Tests

Create:

```text
tests/test_article_generator.py
```

Required checks:

* article generated
* file saved
* pipeline updated
* idempotency respected

---

# PHASE 3 — PINTEREST FACTORY

Status: NOT STARTED

Planned:

* Pinterest titles
* Pinterest descriptions
* Pinterest keywords
* Pinterest image prompts
* Pinterest content packages

Output:

```text
Title
Description
Keywords
Image Prompt
```

---

# PHASE 4 — AUTOMATION

Status: NOT STARTED

Planned:

* Orchestrator
* Retry system
* Human review workflow
* Logging
* Metrics
* Reporting

Pipeline:

```text
Offer
 ↓
Article
 ↓
Pinterest Content
 ↓
Pins
 ↓
Report
```

---

# FORBIDDEN CHANGES

Do not:

* Replace Pydantic
* Replace YAML offer format
* Rewrite OfferLoader
* Rewrite LockManager
* Change Offer schema
* Change folder structure

Unless explicitly requested.

---

# DEFINITION OF DONE — PHASE 2

Given:

```text
data/Offers/offer_alfa_kids.md
```

System must:

1. Load offer
2. Generate article
3. Save article draft
4. Create Article object
5. Update pipeline state
6. Pass tests

Success criteria:

```text
pytest

5+ tests passing
```

---

# CURRENT PROJECT HEALTH

Architecture: Stable ✅

Tests: Passing ✅

Git Repository: Initialized ✅

Phase 1: Complete ✅

Ready For Phase 2: YES ✅
