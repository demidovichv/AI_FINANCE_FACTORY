AI_FINANCE_FACTORY
Technical Project State (for AI Assistant)
Current Status
PROJECT STATUS: ACTIVE

Phase 1: COMPLETE
Phase 2: NOT STARTED
Phase 3: NOT STARTED
Phase 4: NOT STARTED
PROJECT PURPOSE

AI_FINANCE_FACTORY is a content automation system for affiliate financial offers.

Pipeline:

Offer
  v
Article
  v
Pinterest Content
  v
Pins
  v
Reports

Main goal:

One offer file
> many articles
> many Pinterest pins
> automated content factory
COMPLETED COMPONENTS
agents/shared_models.py

Implemented Pydantic models:

Offer

Fields:

id
name
bank
offer_url
affiliate_url
status
created_at
Article

Fields:

id
offer_id
status
markdown_path
html_path
PipelineHistoryItem

Fields:

stage
status
timestamp
message
PipelineState

Fields:

entity_id
entity_type

created_at
updated_at

current_stage
status

parent_ids
child_ids

retry_count
max_retries

last_error

human_review_needed

history
LockFile

Fields:

entity_type
entity_id

lock_id

locked_by

locked_at

hostname

pid

expires_at
agents/offer_loader.py

Implemented.

Responsibilities:

Load markdown offer file
Extract YAML block
Validate using Offer model
Return Offer object
agents/idempotency.py

Implemented.

Responsibilities:

Prevent duplicate article creation
Check existing pipeline status files
Detect already processed offer

Method:

article_exists(offer_id)
agents/lock_manager.py

Implemented.

Responsibilities:

Prevent parallel execution
Create lock files
Release lock files
Remove expired locks

Methods:

acquire_lock()
release_lock()
cleanup_expired_locks()
TESTS

Passing:

tests/test_models.py
tests/test_offer_loader.py
tests/test_idempotency.py
tests/test_lock_manager.py

Current result:

4 passed
DATA STRUCTURE

Existing folders:

data/

Offers/
Articles/
Pipeline_Status/
Logs/

Offer example:

data/Offers/offer_alfa_kids.md

Contains:

id:
name:
bank:
offer_url:
affiliate_url:
status:
created_at:
IMPORTANT ARCHITECTURAL RULES

Rule 1:

Offer files are source of truth.

Never generate offers automatically.

Rule 2:

OfferLoader is mandatory.

All offer reads must go through OfferLoader.

Rule 3:

All entities must use Pydantic models.

No raw dictionaries.

Rule 4:

All pipeline operations must be idempotent.

Before creating anything:

IdempotencyManager.article_exists()

must be checked.

Rule 5:

All write operations must use LockManager.

Before generating content:

acquire_lock()

After completion:

release_lock()

Rule 6:

Do not modify Phase 1 architecture unless bug is confirmed.

Phase 1 is considered stable.

NEXT IMPLEMENTATION TARGET

Phase 2.

agents/article_generator.py

To be created.

Responsibilities:

Offer
> Article Draft

Input:

Offer

Output:

Article

Files:

data/Articles/drafts/
templates/

To be created:

article_prompt.md
seo_prompt.md
pinterest_prompt.md
Pipeline Integration

Must update:

PipelineState

Stages:

init
processing
success
failed
Tests To Create
tests/test_article_generator.py

Must verify:

Article generated
File saved
Pipeline state updated
Idempotency respected
FORBIDDEN CHANGES

Do NOT:

Rewrite LockManager
Rewrite OfferLoader
Replace Pydantic
Replace YAML format
Change Offer schema
Change folder structure

unless explicitly requested.

DEFINITION OF DONE FOR PHASE 2
Given:

offer_alfa_kids.md

System generates:

article_xxx.md

Article object created

Pipeline state updated

Tests passing

Success criteria:

pytest

5+ tests passing