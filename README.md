# Raffle Backoffice

A deterministic (no-AI) raffle ticket chatbot backoffice system using Meta WhatsApp Cloud API.

## Features

- **WhatsApp Integration**: Full integration with Meta WhatsApp Cloud API
- **Raffle Management**: Create and manage multiple raffles with customizable ticket ranges
- **Ticket Reservations**: Automatic ticket reservation with timeout handling
- **Order Processing**: Complete order lifecycle from creation to payment confirmation
- **Admin Interface**: Beautiful Jazzmin-powered Django Admin for management
- **REST API**: DRF-based API for programmatic access
- **SQLite Ready**: Optimized for SQLite with PostgreSQL migration path

## Tech Stack

- **Python**: 3.12
- **Django**: 6.0
- **Database**: SQLite (MVP/dev) with PostgreSQL compatibility
- **Admin UI**: Django Admin with Jazzmin
- **API**: Django REST Framework
- **Dependency Manager**: UV
- **OS**: Linux/WSL compatible

## Project Structure

```
raffle-backoffice/
├── core/                   # Django project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   ├── whatsapp/          # WhatsApp integration
│   │   ├── models.py      # Contact & Message models
│   │   ├── views.py       # Webhook handlers
│   │   ├── admin.py       # Admin configuration
│   │   └── services/      # Business logic
│   │       ├── meta_client.py    # WhatsApp API client
│   │       ├── security.py       # Signature verification
│   │       └── flow.py           # Message routing & state machine
│   └── raffles/           # Raffle management
│       ├── models.py      # Raffle, Ticket, Order models
│       ├── admin.py       # Admin configuration
│       ├── api_views.py   # REST API endpoints
│       ├── serializers.py # DRF serializers
│       └── services/      # Business logic
│           └── reservations.py   # Ticket reservation logic
├── manage.py
├── pyproject.toml
└── .env.example
```

## Installation

### Prerequisites

- Python 3.12+
- UV package manager

### Setup

1. **Clone the repository** (if not already done)

2. **Install dependencies using UV**:
   ```bash
   uv sync
   ```

3. **Create environment file**:
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and configure your WhatsApp API credentials.

4. **Run migrations**:
   ```bash
   python manage.py migrate
   ```

5. **Create superuser**:
   ```bash
   python manage.py createsuperuser
   ```

6. **Run development server**:
   ```bash
   python manage.py runserver
   ```

## Configuration

### WhatsApp Cloud API Setup

1. Go to [Meta for Developers](https://developers.facebook.com/)
2. Create a new app and enable WhatsApp
3. Get your credentials:
   - `WHATSAPP_ACCESS_TOKEN`: From WhatsApp API settings
   - `WHATSAPP_PHONE_NUMBER_ID`: Your WhatsApp phone number ID
   - `WHATSAPP_APP_SECRET`: App secret for signature verification
   - `WHATSAPP_VERIFY_TOKEN`: Create your own token for webhook verification

4. Configure webhook URL:
   - URL: `https://your-domain.com/whatsapp/webhook/`
   - Verify Token: Same as `WHATSAPP_VERIFY_TOKEN` in your `.env`

### Environment Variables

See `.env.example` for all available configuration options.

## Usage

### Admin Interface

Access the admin at `http://localhost:8000/admin/`

**Admin Features**:
- Create and manage raffles
- View and manage orders
- Confirm payments
- Cancel orders and release tickets
- Monitor WhatsApp contacts and messages
- Generate ticket numbers for raffles

**Admin Actions**:
- **Raffles**: Activate/deactivate, generate tickets
- **Orders**: Confirm payment, cancel orders

### REST API

Base URL: `http://localhost:8000/api/`

**Authentication**: Token-based or Session (admin only)

#### Endpoints

**Raffles**:
- `GET /api/raffles/` - List all raffles
- `GET /api/raffles/{id}/` - Get raffle details
- `GET /api/raffles/{id}/availability/` - Get ticket availability
- `GET /api/raffles/{id}/tickets/` - Get all tickets with status
- `POST /api/raffles/` - Create raffle (admin)
- `PUT/PATCH /api/raffles/{id}/` - Update raffle (admin)
- `DELETE /api/raffles/{id}/` - Delete raffle (admin)

**Orders**:
- `GET /api/orders/` - List all orders
- `GET /api/orders/{id}/` - Get order details
- `GET /api/orders/pending-payment/` - Get pending payment orders
- `POST /api/orders/{id}/confirm-payment/` - Confirm payment
  ```json
  {"payment_proof_media_id": "optional_media_id"}
  ```
- `POST /api/orders/{id}/cancel/` - Cancel order and release tickets

**Filters**:
- Orders: `?status=PENDING_PAYMENT`, `?raffle=1`, `?contact=1`
- Raffles: `?is_active=true`

### WhatsApp Bot Flow

**User Journey**:

1. **Start**: User sends "menu" or "hi"
2. **Browse Raffles**: View active raffles
3. **Select Raffle**: Choose a raffle by number
4. **Select Tickets**:
   - Specific numbers: "5,12,99" or "5 12 99"
   - Random: "random 5"
5. **Confirm Order**: Review and confirm
6. **Payment**: Upload payment proof (image/document)
7. **Confirmation**: Admin confirms payment in admin panel

**Bot Commands**:
- `menu` - Show main menu
- `raffles` - Browse active raffles
- `back` - Go back
- `cancel` - Cancel current order
- `confirm` - Confirm order

## Models

### WhatsApp App

**WhatsAppContact**:
- `wa_id`: WhatsApp ID (unique)
- `name`: Contact name
- `state`: Current conversation state
- `context`: JSON field for session data
- `last_interaction_at`: Last message timestamp

**InboundMessage**:
- `wa_message_id`: WhatsApp message ID (unique)
- `contact`: FK to WhatsAppContact
- `msg_type`: Message type (text, image, etc.)
- `text`: Message text
- `media_id`: Media ID for images/documents
- `raw_payload`: Full webhook payload

### Raffles App

**Raffle**:
- `title`: Raffle title
- `ticket_price`: Price per ticket
- `currency`: Currency code
- `is_active`: Active status
- `min_number`, `max_number`: Ticket range

**TicketNumber**:
- `raffle`: FK to Raffle
- `number`: Ticket number
- `status`: AVAILABLE/RESERVED/SOLD
- `reserved_by_order`: FK to Order (nullable)
- `reserved_until`: Reservation expiry

**Order**:
- `raffle`: FK to Raffle
- `contact`: FK to WhatsAppContact
- `qty`: Number of tickets
- `total_amount`: Total price
- `status`: DRAFT/PENDING_PAYMENT/PAID/CANCELLED/EXPIRED
- `payment_proof_media_id`: Payment proof

**OrderTicket**:
- `order`: FK to Order
- `ticket`: FK to TicketNumber

## Services

### Reservation Service

**Functions**:
- `reserve_specific(raffle_id, numbers, contact)` - Reserve specific tickets
- `reserve_random(raffle_id, qty, contact)` - Reserve random tickets
- `release_order_reservations(order)` - Release reserved tickets
- `confirm_paid(order, media_id)` - Confirm payment and mark tickets as sold

**SQLite Safety**:
- Uses `transaction.atomic` for consistency
- Validates availability before reserving
- Random selection in Python (not SQL)
- Automatic expiry cleanup

### WhatsApp Services

**meta_client.py**:
- `send_text(to, message)` - Send text message
- `send_interactive_buttons(to, body, buttons)` - Send button message
- `send_interactive_list(to, body, button_text, sections)` - Send list message

**security.py**:
- `verify_meta_signature(payload, signature)` - Verify webhook signature

**flow.py**:
- `process_message(inbound_message)` - Main message router
- State handlers for each conversation state

## Development

### Running Tests

```bash
python manage.py test
```

### Create Migrations

```bash
python manage.py makemigrations
```

### Collect Static Files

```bash
python manage.py collectstatic
```

### Shell Access

```bash
python manage.py shell
```

## Migration to PostgreSQL

To migrate from SQLite to PostgreSQL:

1. Install PostgreSQL adapter:
   ```bash
   uv add psycopg2-binary
   ```

2. Update `DATABASES` in `core/settings.py`:
   ```python
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.postgresql',
           'NAME': config('DB_NAME'),
           'USER': config('DB_USER'),
           'PASSWORD': config('DB_PASSWORD'),
           'HOST': config('DB_HOST', default='localhost'),
           'PORT': config('DB_PORT', default='5432'),
       }
   }
   ```

3. Run migrations on new database

## License

MIT

## Support

For issues and questions, please create an issue in the repository.
