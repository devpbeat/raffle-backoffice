# Quick Start Guide

Get your raffle backoffice up and running in 5 minutes!

## Prerequisites

- Python 3.12+
- UV package manager installed
- Meta WhatsApp Cloud API credentials (optional for initial setup)

## Setup Steps

### 1. Install Dependencies

```bash
uv sync
```

This will install all required packages including Django, DRF, Jazzmin, and more.

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and update at minimum:
```env
SECRET_KEY=your-secret-key-here
DEBUG=True
WHATSAPP_VERIFY_TOKEN=your-verify-token
```

**Note**: You can skip WhatsApp credentials initially and configure them later.

### 3. Initialize Database

```bash
# Migrations are already created
python manage.py migrate
```

### 4. Create Superuser

```bash
python manage.py createsuperuser
```

Follow the prompts to create your admin account.

### 5. Start Development Server

```bash
python manage.py runserver
```

Your server will be running at `http://localhost:8000`

## Quick Test

### Access Admin Interface

1. Go to `http://localhost:8000/admin/`
2. Login with your superuser credentials
3. You'll see the beautiful Jazzmin admin interface!

### Create Your First Raffle

1. In admin, click **Raffles** → **Add Raffle**
2. Fill in:
   - Title: "My First Raffle"
   - Description: "Test raffle"
   - Ticket Price: 10.00
   - Currency: USD
   - Min Number: 1
   - Max Number: 100
   - Is Active: ✓
3. Save

### Generate Tickets

1. Go to **Raffles** list
2. Select your raffle
3. Choose action: "Generate tickets for selected raffles"
4. Click "Go"
5. You'll see "100 ticket(s) generated"

### View Tickets

1. Click **Ticket Numbers** in the sidebar
2. You'll see tickets 1-100, all marked as "Available" (green)

## Test the API

### Get API Token

```bash
python manage.py drf_create_token <your_username>
```

### Test Endpoints

**List Raffles**:
```bash
curl -H "Authorization: Token YOUR_TOKEN" http://localhost:8000/api/raffles/
```

**Check Availability**:
```bash
curl -H "Authorization: Token YOUR_TOKEN" http://localhost:8000/api/raffles/1/availability/
```

**List Orders**:
```bash
curl -H "Authorization: Token YOUR_TOKEN" http://localhost:8000/api/orders/
```

## Configure WhatsApp (Optional)

### 1. Get WhatsApp Credentials

1. Go to [Meta for Developers](https://developers.facebook.com/)
2. Create a new app or use existing
3. Add WhatsApp product
4. Get your credentials:
   - Access Token
   - Phone Number ID
   - App Secret

### 2. Update .env

```env
WHATSAPP_ACCESS_TOKEN=your_access_token
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
WHATSAPP_APP_SECRET=your_app_secret
WHATSAPP_VERIFY_TOKEN=your_custom_verify_token
```

### 3. Configure Webhook

In Meta for Developers:
- Webhook URL: `https://your-domain.com/whatsapp/webhook/`
- Verify Token: Same as `WHATSAPP_VERIFY_TOKEN` in `.env`
- Subscribe to: `messages`

**For local testing**, use ngrok:
```bash
ngrok http 8000
```

Then use the ngrok URL: `https://xyz.ngrok.io/whatsapp/webhook/`

## Next Steps

### Explore Admin Features

- **View Contacts**: See WhatsApp users and their conversation states
- **Monitor Messages**: View all inbound messages
- **Manage Orders**: Confirm payments, cancel orders
- **Generate Reports**: Use filters to find specific orders

### Test the Chatbot

Send a message to your WhatsApp number:
```
menu
```

The bot will respond with options to browse raffles!

### Admin Actions

**Confirm Payment**:
1. Go to **Orders**
2. Filter by "Pending Payment"
3. Select order(s)
4. Choose action: "Confirm payment for selected orders"
5. Click "Go"

**Cancel Order**:
1. Select order(s)
2. Choose action: "Cancel selected orders"
3. Tickets will be released automatically

## Common Commands

```bash
# Create migrations after model changes
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver

# Run tests
python manage.py test

# Django shell
python manage.py shell

# Collect static files
python manage.py collectstatic
```

## Troubleshooting

### "No module named X"
```bash
uv sync  # Reinstall dependencies
```

### Database errors
```bash
rm db.sqlite3
python manage.py migrate
```

### WhatsApp webhook not working
- Check your verify token matches
- Verify URL is accessible (use ngrok for local)
- Check server logs: `python manage.py runserver`

### Can't login to admin
```bash
python manage.py createsuperuser
```

## Development Tips

1. **Use Django Debug Toolbar** (optional):
   ```bash
   uv add django-debug-toolbar
   ```

2. **View Logs**:
   ```bash
   tail -f *.log
   ```

3. **Test WhatsApp Messages Locally**:
   Use the Django shell to simulate messages:
   ```python
   python manage.py shell
   >>> from apps.whatsapp.models import WhatsAppContact, InboundMessage
   >>> contact = WhatsAppContact.objects.create(wa_id="1234567890", name="Test User")
   >>> message = InboundMessage.objects.create(
   ...     wa_message_id="test123",
   ...     contact=contact,
   ...     msg_type="text",
   ...     text="menu"
   ... )
   >>> from apps.whatsapp.services import process_message
   >>> process_message(message)
   ```

## Production Deployment

See README.md for full production deployment guide including:
- PostgreSQL migration
- Gunicorn setup
- Nginx configuration
- SSL/HTTPS setup
- Environment variables security

---

**Ready to go!** 🎉

For detailed documentation, see [README.md](README.md)
