# Project File Structure

```
raffle-backoffice/
│
├── core/                           # Django project configuration
│   ├── __init__.py
│   ├── asgi.py                    # ASGI configuration
│   ├── settings.py                # Main settings (Jazzmin, DRF, WhatsApp config)
│   ├── urls.py                    # Root URL configuration
│   └── wsgi.py                    # WSGI configuration
│
├── apps/                           # Django applications
│   ├── __init__.py
│   │
│   ├── whatsapp/                  # WhatsApp integration app
│   │   ├── __init__.py
│   │   ├── apps.py                # App configuration
│   │   ├── models.py              # WhatsAppContact, InboundMessage
│   │   ├── admin.py               # Admin interface configuration
│   │   ├── views.py               # Webhook endpoints (verify, receive)
│   │   ├── urls.py                # WhatsApp URL routing
│   │   ├── migrations/            # Database migrations
│   │   │   ├── __init__.py
│   │   │   └── 0001_initial.py
│   │   └── services/              # Business logic
│   │       ├── __init__.py
│   │       ├── meta_client.py     # WhatsApp Cloud API client
│   │       ├── security.py        # Webhook signature verification
│   │       └── flow.py            # Message routing & conversation flow
│   │
│   └── raffles/                   # Raffle management app
│       ├── __init__.py
│       ├── apps.py                # App configuration
│       ├── models.py              # Raffle, TicketNumber, Order, OrderTicket
│       ├── admin.py               # Admin interface with actions
│       ├── api_views.py           # DRF ViewSets
│       ├── serializers.py         # DRF serializers
│       ├── urls.py                # API URL routing
│       ├── migrations/            # Database migrations
│       │   ├── __init__.py
│       │   └── 0001_initial.py
│       └── services/              # Business logic
│           ├── __init__.py
│           └── reservations.py    # Ticket reservation logic
│
├── manage.py                      # Django management script
├── pyproject.toml                 # UV/Python project configuration
├── uv.lock                        # UV lockfile
├── .env.example                   # Environment variables template
├── .gitignore                     # Git ignore rules
├── README.md                      # Main documentation
├── PROJECT_STRUCTURE.md           # This file
└── agents.md                      # (Your existing file)
```

## Key Files Description

### Core Configuration
- **core/settings.py**: Django settings with Jazzmin, DRF, and WhatsApp configuration
- **core/urls.py**: Routes for admin, webhook, and API endpoints

### WhatsApp App
- **models.py**:
  - `WhatsAppContact`: Contact state machine
  - `InboundMessage`: Message storage and deduplication
- **services/meta_client.py**: Send text, buttons, and interactive messages
- **services/security.py**: HMAC signature verification
- **services/flow.py**: Deterministic conversation routing
- **views.py**: Webhook verification and message receiving

### Raffles App
- **models.py**:
  - `Raffle`: Raffle configuration
  - `TicketNumber`: Individual tickets with status
  - `Order`: Purchase orders
  - `OrderTicket`: Order-ticket relationship
- **services/reservations.py**:
  - `reserve_specific()`: Reserve chosen numbers
  - `reserve_random()`: Reserve random tickets
  - `confirm_paid()`: Mark as paid
  - `release_order_reservations()`: Cancel and release
- **api_views.py**: REST API endpoints
- **admin.py**: Admin with bulk actions

## Database Models

### WhatsApp Models
```python
WhatsAppContact
├── wa_id (unique)
├── name
├── state (IDLE, BROWSING, SELECTING_NUMBERS, etc.)
├── context (JSON)
└── timestamps

InboundMessage
├── wa_message_id (unique)
├── contact (FK)
├── msg_type
├── text
├── media_id
├── raw_payload (JSON)
└── processed flag
```

### Raffle Models
```python
Raffle
├── title, description
├── ticket_price, currency
├── min_number, max_number
├── is_active
└── timestamps

TicketNumber
├── raffle (FK)
├── number
├── status (AVAILABLE/RESERVED/SOLD)
├── reserved_by_order (FK, nullable)
└── reserved_until

Order
├── raffle (FK)
├── contact (FK)
├── qty, total_amount
├── status (DRAFT/PENDING_PAYMENT/PAID/CANCELLED/EXPIRED)
├── payment_proof_media_id
└── timestamps

OrderTicket
├── order (FK)
└── ticket (FK)
```

## API Endpoints

### Webhooks
- `GET /whatsapp/webhook/` - Webhook verification
- `POST /whatsapp/webhook/` - Receive messages

### REST API
- `GET/POST /api/raffles/` - List/create raffles
- `GET /api/raffles/{id}/availability/` - Get available tickets
- `GET /api/raffles/{id}/tickets/` - Get all ticket statuses
- `GET/POST /api/orders/` - List/create orders
- `GET /api/orders/pending-payment/` - Pending payment orders
- `POST /api/orders/{id}/confirm-payment/` - Confirm payment
- `POST /api/orders/{id}/cancel/` - Cancel order

### Admin
- `/admin/` - Django Admin (Jazzmin theme)

## Configuration Files

- **pyproject.toml**: Python dependencies managed by UV
- **.env**: Environment variables (not committed)
- **.env.example**: Template for environment setup
- **uv.lock**: Dependency lockfile

## Generated Files (not in repo)
- `db.sqlite3` - SQLite database
- `staticfiles/` - Collected static files
- `__pycache__/` - Python bytecode
- `.venv/` - Virtual environment
