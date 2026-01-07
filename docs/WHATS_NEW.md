# What's New - Spanish Support & API Documentation

## 🎉 New Features Added

### 1. 🌍 Full Spanish Support (i18n)

**Admin Interface:**
- ✅ Jazzmin admin now in Spanish
- ✅ Site title: "Administración de Rifas"
- ✅ Welcome message in Spanish
- ✅ Language chooser enabled
- ✅ Paraguay timezone (America/Asuncion)

**WhatsApp Bot:**
- ✅ All messages translated to Spanish
- ✅ Spanish commands supported
- ✅ Dual-language support (es/en)

**Supported Commands:**
- Spanish: `hola`, `rifas`, `menu`, `inicio`, `ayuda`, `volver`, `confirmar`, `cancelar`, `aleatorio`, `saltar`
- English: `hello`, `raffles`, `menu`, `start`, `help`, `back`, `confirm`, `cancel`, `random`, `skip`

### 2. 📚 Interactive API Documentation (Swagger)

**New Endpoints:**
- `/api/docs/` - Swagger UI (interactive documentation)
- `/api/redoc/` - ReDoc (alternative documentation view)
- `/api/schema/` - OpenAPI schema (JSON)

**Features:**
- ✅ Try endpoints directly in browser
- ✅ Token authentication support
- ✅ Complete request/response schemas
- ✅ Filtering and pagination examples
- ✅ Bilingual support (Spanish/English)

## 📁 Files Added/Modified

### New Files Created:
```
apps/whatsapp/services/messages_es.py    # Spanish messages for bot
I18N_AND_API_DOCS.md                     # Complete i18n & API guide
WHATS_NEW.md                             # This file
```

### Modified Files:
```
core/settings.py                         # i18n + Swagger configuration
core/urls.py                             # Swagger endpoints
apps/whatsapp/services/flow.py          # Spanish message integration
pyproject.toml                           # Added drf-spectacular
.env.example                             # Language/timezone settings
```

## 🚀 Quick Start

### Access Swagger Documentation

1. Start server:
   ```bash
   python manage.py runserver
   ```

2. Open Swagger UI:
   ```
   http://localhost:8000/api/docs/
   ```

3. Authenticate:
   - Click "Authorize" button
   - Enter: `Token YOUR_API_TOKEN`
   - Click "Authorize"

4. Try any endpoint!

### Test Spanish Bot

Send WhatsApp message:
```
hola
```

Bot responds in Spanish:
```
¡Bienvenido!

1. Escribe 'rifas' para explorar rifas activas
2. Escribe 'pedidos' para ver tus pedidos
3. Escribe 'ayuda' para asistencia
```

## 🔧 Configuration Changes

### settings.py

**Before:**
```python
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
```

**After:**
```python
LANGUAGE_CODE = 'es'
TIME_ZONE = 'America/Asuncion'
LANGUAGES = [('es', 'Español'), ('en', 'English')]
```

### URLs Added

```python
# Swagger
path('api/docs/', SpectacularSwaggerView.as_view(), ...)
path('api/redoc/', SpectacularRedocView.as_view(), ...)
path('api/schema/', SpectacularAPIView.as_view(), ...)

# i18n
path('i18n/', include('django.conf.urls.i18n')),
```

## 📊 Dependencies Added

```toml
drf-spectacular>=0.27.0
```

**Installed packages:**
- drf-spectacular - 0.29.0
- inflection - 0.5.1
- jsonschema - 4.25.1
- pyyaml - 6.0.3
- uritemplate - 4.2.0
- + 5 more dependencies

## 🎯 For Paraguay/CDE Users

Perfect setup for Paraguay and Ciudad del Este:

✅ **Idioma:** Español predeterminado
✅ **Zona horaria:** America/Asuncion (GMT-4)
✅ **Bot WhatsApp:** Mensajes en español
✅ **Admin:** Interfaz en español
✅ **Documentación:** Bilingüe (ES/EN)

## 📖 Examples

### API Usage (Swagger)

**Get active raffles:**
```
GET /api/raffles/?is_active=true
```

**Check availability:**
```
GET /api/raffles/1/availability/
```

Response:
```json
{
  "raffle_id": 1,
  "total_tickets": 100,
  "available_count": 85,
  "sold_count": 15,
  "reserved_count": 0,
  "available_numbers": [1, 2, 3, ...]
}
```

### Bot Conversation (Spanish)

```
Usuario: hola
Bot: ¡Bienvenido! ...

Usuario: rifas
Bot: *Rifas Activas:*
     1. Rifa de Año Nuevo
     Precio: USD 10.00
     Disponibles: 85/100

Usuario: 1
Bot: [Detalles de la rifa en español]

Usuario: aleatorio 3
Bot: ✅ ¡Pedido Creado!
     Números: 23, 45, 78
     Total: USD 30.00

Usuario: confirmar
Bot: 💳 Instrucciones de Pago
     Monto: USD 30.00
     ...
```

## 🔗 Documentation Links

- **Full i18n Guide:** [I18N_AND_API_DOCS.md](I18N_AND_API_DOCS.md)
- **API Documentation:** http://localhost:8000/api/docs/
- **Admin Panel:** http://localhost:8000/admin/

## ✨ Benefits

**For End Users:**
- Native Spanish interface
- Paraguay timezone
- Familiar commands

**For Developers:**
- Interactive API testing
- Complete endpoint documentation
- OpenAPI schema export

**For Admins:**
- Spanish admin panel
- Language selector
- Easy content management

---

**¡Todo listo para Paraguay!** 🇵🇾

See [I18N_AND_API_DOCS.md](I18N_AND_API_DOCS.md) for complete documentation.
