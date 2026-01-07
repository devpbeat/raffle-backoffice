# Agents Guide — Raffle Tickets Bot
(Meta WhatsApp Cloud API + Django + DRF + Jazzmin)

## Goal
Build a deterministic (no-AI) WhatsApp chatbot for selling raffle tickets using Meta WhatsApp Cloud API.

Django is the single source of truth for:
- conversation state
- ticket inventory
- orders and payment proof

Django Admin (Jazzmin) is the backoffice.
Django REST Framework exposes internal APIs for n8n automation.

---

## Tech Stack (Locked)
- Python **3.12**
- Django **6.0**
- Django REST Framework
- SQLite (initial MVP / local dev)
- Jazzmin (admin UI)
- UV (environment + dependency management)
- Gunicorn (later)
- Celery + Redis (planned, optional in MVP)

> PostgreSQL will be introduced later for concurrency optimizations (SELECT FOR UPDATE SKIP LOCKED).
> For now, code must be written in a DB-agnostic way where possible.

---

## Environment Management (IMPORTANT)
- **UV manages the virtual environment and dependencies**
- No pip, no poetry, no pipenv
- Dependencies are declared in `pyproject.toml`
- Lockfile: `uv.lock`

Agents must:
- Assume `uv sync` is used to install deps
- Not generate `requirements.txt`
- Not reference pip commands in docs or scripts

---

## Non-Goals
- No LLM / AI logic
- No Stripe or automatic payments
- No frontend web UI
- No multi-language complexity in MVP
- No WhatsApp templates initially (24h window only)

---

## Core Concepts

### Conversation State Machine
State is stored per WhatsApp contact.

States:
- MENU
- CHOOSE_MODE
- ASK_QTY
- ASK_PICK_NUMBERS
- CONFIRM_RESERVATION
- WAIT_PROOF
- DONE

Global commands (available in all states):
- MENU → reset to MENU
- CANCEL → cancel active order & release reservations
- HELP → show menu again

Temporary conversation data is stored in:
`WhatsAppContact.context` (JSONField)

Example keys:
- raffle_id
- mode (RANDOM | PICK)
- qty
- draft_order_id
- picked_numbers

---

### Ticket Reservation Rules
The system must support:
1) User picks specific ticket numbers
2) User requests random ticket assignment

Rules:
- Reservations are atomic
- Tickets move through states:
  AVAILABLE → RESERVED → SOLD
- Reservations expire after TTL (default 30 minutes)
- Expired reservations return tickets to AVAILABLE

SQLite limitations are acceptable for MVP; logic must be written cleanly to allow PostgreSQL upgrade later.

---

### Orders
Order lifecycle:
- DRAFT
- PENDING_PAYMENT
- PAID
- CANCELLED
- EXPIRED

Payment is manual:
- User sends payment proof image
- Admin confirms via Django Admin or DRF API
- Confirmation marks tickets as SOLD

---

### Webhook Requirements (Meta WhatsApp)
Implement:
- GET webhook verification (hub.challenge)
- POST webhook receiver
- Message deduplication using `wa_message_id`
- Signature validation using `X-Hub-Signature-256`

Outbound messages:
- Sent via Meta Graph API `/messages` endpoint

---

### DRF APIs (Internal)
Used by n8n and admin automation.

Required endpoints:
- POST `/api/orders/{id}/confirm-payment`
- POST `/api/orders/{id}/cancel`
- GET `/api/orders?status=PENDING_PAYMENT`
- GET `/api/raffles/{id}/availability`

Auth:
- Token-based or simple admin token (no OAuth)

---

## Django Apps

### apps.whatsapp
- Models: WhatsAppContact, InboundMessage
- Services:
  - meta_client.py (send WhatsApp messages)
  - security.py (signature verification)
  - flow.py (conversation router)
- Views:
  - webhook GET/POST

### apps.raffles
- Models: Raffle, TicketNumber, Order, OrderTicket
- Services:
  - reservations.py
  - availability.py
- Admin:
  - Jazzmin-optimized admin
  - Admin actions for confirming and cancelling orders

### apps.core
- Enums
- Constants
- Shared utilities

---

## Quality Rules
- Idempotent webhook processing
- Explicit state transitions
- Strong input validation (qty range, number formats)
- Timezone-aware datetimes
- Logging for webhook events
- No business logic in views
- No hard-coded secrets

---

## Deliverables
- Django project scaffold (Django 6.0)
- Admin configured with Jazzmin
- Working WhatsApp webhook endpoints
- Deterministic state machine
- DRF APIs for n8n
- SQLite-compatible MVP
