# Internacionalización y Documentación de API

## 🌍 Soporte Multiidioma (i18n)

### Configuración

El proyecto ahora soporta **Español** e **Inglés** con Español como idioma predeterminado.

**Idiomas disponibles:**
- 🇪🇸 Español (predeterminado)
- 🇬🇧 English

**Zona horaria:** America/Asuncion (Paraguay)

### Administración en Español

El panel de administración Django Jazzmin está ahora configurado en español:

- **Título del sitio:** Administración de Rifas
- **Encabezado:** Admin Rifas
- **Mensaje de bienvenida:** Bienvenido al Panel de Administración de Rifas
- **Selector de idioma:** Habilitado en la interfaz

### Bot de WhatsApp en Español

Todos los mensajes del bot están traducidos al español. Los usuarios pueden interactuar en español:

**Comandos aceptados:**
- `hola` / `hello` / `hi` → Menú principal
- `menu` / `inicio` → Menú principal
- `rifas` / `ver` → Ver rifas activas
- `volver` / `back` → Volver al listado
- `confirmar` / `confirm` → Confirmar pedido
- `cancelar` / `cancel` → Cancelar pedido
- `aleatorio 5` / `random 5` → Selección aleatoria
- `saltar` / `skip` → Saltar comprobante de pago

**Ejemplos de interacción:**

```
Usuario: hola
Bot: ¡Bienvenido!

1. Escribe 'rifas' para explorar rifas activas
2. Escribe 'pedidos' para ver tus pedidos
3. Escribe 'ayuda' para asistencia

Usuario: rifas
Bot: *Rifas Activas:*

1. *Rifa de Año Nuevo*
   Precio: USD 10.00
   Disponibles: 85/100

Responde con el número de rifa (1-1) para participar.

Usuario: 1
Bot: *Rifa de Año Nuevo*

💰 Precio: USD 10.00 por número
🎫 Números: 1 - 100
✅ Disponibles: 85/100
🔥 Vendidos: 15/100

¿Cómo te gustaría seleccionar tus números?

1. Escribe números específicos (ej: '5,12,99' o '5 12 99')
2. Escribe 'aleatorio X' para X números al azar (ej: 'aleatorio 5')
3. Escribe 'volver' para ver otras rifas

Usuario: aleatorio 3
Bot: ✅ *¡Pedido Creado!*

Rifa: Rifa de Año Nuevo
Números: 23, 45, 78
Cantidad: 3
Total: USD 30.00

⏰ Reservado por 15 minutos

¿Confirmas este pedido?
1. Escribe 'confirmar' para continuar
2. Escribe 'cancelar' para cancelar

Usuario: confirmar
Bot: 💳 *Instrucciones de Pago*

Monto: USD 30.00

Por favor realiza el pago y envía una captura de pantalla o foto del comprobante de pago.

¡Una vez verificado, tus números serán confirmados!

Pedido #1

[Usuario envía foto del comprobante]

Bot: ✅ ¡Comprobante de pago recibido!

Tu pedido está en revisión. Serás notificado una vez confirmado.

Escribe 'menu' para volver al menú principal.
```

### Mensajes Personalizables

Todos los mensajes están definidos en:
```
apps/whatsapp/services/messages_es.py
```

Puedes personalizar fácilmente cualquier mensaje editando este archivo.

## 📚 Documentación de API (Swagger)

### Acceso a la Documentación

La API ahora incluye documentación interactiva completa usando **drf-spectacular**:

**URLs disponibles:**
- **Swagger UI:** http://localhost:8000/api/docs/
- **ReDoc:** http://localhost:8000/api/redoc/
- **Esquema OpenAPI:** http://localhost:8000/api/schema/

### Características de Swagger

✅ **Interfaz interactiva** - Prueba endpoints directamente desde el navegador
✅ **Autenticación integrada** - Soporta Token Auth y Session Auth
✅ **Esquemas detallados** - Modelos de request/response completamente documentados
✅ **Deep linking** - URLs directas a endpoints específicos
✅ **Persistencia de autenticación** - Token guardado en el navegador
✅ **Multiidioma** - Documentación en Español e Inglés

### Uso de Swagger UI

1. **Acceder a la documentación:**
   ```
   http://localhost:8000/api/docs/
   ```

2. **Autenticarse:**
   - Clic en botón "Authorize" (esquina superior derecha)
   - Ingresar token: `Token YOUR_API_TOKEN`
   - Clic en "Authorize"

3. **Probar endpoints:**
   - Expandir un endpoint (ej: GET /api/raffles/)
   - Clic en "Try it out"
   - Completar parámetros si es necesario
   - Clic en "Execute"
   - Ver respuesta

### Generar Token de API

```bash
python manage.py drf_create_token <username>
```

O crear manualmente en el admin Django:
```
Admin > Auth Token > Tokens > Add Token
```

### Endpoints Documentados

**Rifas:**
```
GET    /api/raffles/                    # Listar rifas
POST   /api/raffles/                    # Crear rifa
GET    /api/raffles/{id}/               # Detalle de rifa
PUT    /api/raffles/{id}/               # Actualizar rifa completa
PATCH  /api/raffles/{id}/               # Actualizar rifa parcial
DELETE /api/raffles/{id}/               # Eliminar rifa
GET    /api/raffles/{id}/availability/  # Disponibilidad
GET    /api/raffles/{id}/tickets/       # Listar números
```

**Pedidos:**
```
GET    /api/orders/                        # Listar pedidos
POST   /api/orders/                        # Crear pedido
GET    /api/orders/{id}/                   # Detalle de pedido
GET    /api/orders/pending-payment/        # Pedidos pendientes
POST   /api/orders/{id}/confirm-payment/   # Confirmar pago
POST   /api/orders/{id}/cancel/            # Cancelar pedido
```

### Filtros Disponibles

**Rifas:**
- `?is_active=true` - Solo rifas activas
- `?is_active=false` - Solo rifas inactivas

**Pedidos:**
- `?status=PENDING_PAYMENT` - Pedidos pendientes
- `?status=PAID` - Pedidos pagados
- `?raffle=1` - Pedidos de rifa específica
- `?contact=1` - Pedidos de contacto específico

### Paginación

Todos los endpoints de listado están paginados:
- **Tamaño de página:** 50 items
- **Parámetros:**
  - `?page=2` - Obtener página 2
  - `?page_size=100` - Cambiar tamaño (máximo 100)

**Respuesta:**
```json
{
  "count": 150,
  "next": "http://localhost:8000/api/orders/?page=2",
  "previous": null,
  "results": [...]
}
```

### Ejemplos de Uso

**1. Obtener rifas activas:**
```bash
curl -H "Authorization: Token YOUR_TOKEN" \
  "http://localhost:8000/api/raffles/?is_active=true"
```

**2. Ver disponibilidad de rifa:**
```bash
curl -H "Authorization: Token YOUR_TOKEN" \
  "http://localhost:8000/api/raffles/1/availability/"
```

**Respuesta:**
```json
{
  "raffle_id": 1,
  "total_tickets": 100,
  "available_count": 85,
  "sold_count": 15,
  "reserved_count": 0,
  "available_numbers": [1, 2, 3, 4, 5, ...]
}
```

**3. Listar pedidos pendientes:**
```bash
curl -H "Authorization: Token YOUR_TOKEN" \
  "http://localhost:8000/api/orders/pending-payment/"
```

**4. Confirmar pago de pedido:**
```bash
curl -X POST \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"payment_proof_media_id": "optional_media_id"}' \
  "http://localhost:8000/api/orders/1/confirm-payment/"
```

**5. Cancelar pedido:**
```bash
curl -X POST \
  -H "Authorization: Token YOUR_TOKEN" \
  "http://localhost:8000/api/orders/1/cancel/"
```

**Respuesta:**
```json
{
  "message": "Order cancelled successfully",
  "released_tickets": 3,
  "order": {...}
}
```

## 🔧 Configuración en settings.py

### Internacionalización

```python
# Idioma predeterminado
LANGUAGE_CODE = 'es'

# Idiomas disponibles
LANGUAGES = [
    ('es', 'Español'),
    ('en', 'English'),
]

# Directorio de traducciones
LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

# Zona horaria (Paraguay)
TIME_ZONE = 'America/Asuncion'

# Habilitar i18n y l10n
USE_I18N = True
USE_L10N = True
USE_TZ = True
```

### Swagger/OpenAPI

```python
# REST Framework
REST_FRAMEWORK = {
    ...
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# DRF Spectacular
SPECTACULAR_SETTINGS = {
    'TITLE': 'Raffle Backoffice API',
    'DESCRIPTION': 'API para gestión de rifas y tickets vía WhatsApp',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'SCHEMA_PATH_PREFIX': '/api/',
    'COMPONENT_SPLIT_REQUEST': True,
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'persistAuthorization': True,
        'displayOperationId': True,
    },
    'LANGUAGES': ['es', 'en'],
}
```

## 🚀 Uso en Producción

### Variables de Entorno

Actualiza tu `.env`:

```env
# Django
LANGUAGE_CODE=es
TIME_ZONE=America/Asuncion

# API
API_TITLE=Raffle Backoffice API
API_VERSION=1.0.0
```

### Cambiar Idioma

Para cambiar el idioma predeterminado, edita `core/settings.py`:

```python
LANGUAGE_CODE = 'en'  # Para inglés
```

O permite que los usuarios seleccionen en el admin (ya configurado):
```python
JAZZMIN_SETTINGS = {
    ...
    'language_chooser': True,  # Ya habilitado
}
```

### Despliegue

Asegúrate de que las traducciones estén compiladas:

```bash
# Si necesitas crear nuevas traducciones
python manage.py makemessages -l es
python manage.py makemessages -l en

# Compilar traducciones
python manage.py compilemessages
```

## 📝 Extender Traducciones

### Agregar Nuevos Mensajes en Español

Edita `apps/whatsapp/services/messages_es.py`:

```python
# Nuevo mensaje
MSG_CUSTOM_MESSAGE = "Tu mensaje personalizado aquí"
```

Usa en `flow.py`:

```python
from . import messages_es as msg

send_text(contact.wa_id, msg.MSG_CUSTOM_MESSAGE)
```

### Traducir Modelos Django

En tus modelos, usa `gettext_lazy`:

```python
from django.utils.translation import gettext_lazy as _

class Raffle(models.Model):
    title = models.CharField(_("título"), max_length=255)
    description = models.TextField(_("descripción"), blank=True)
    # ...
```

## 🎯 Beneficios

### Para Usuarios (Paraguay/CDE)
✅ Interfaz completamente en español
✅ Bot de WhatsApp en español nativo
✅ Zona horaria correcta (America/Asuncion)
✅ Formato de fechas local

### Para Desarrolladores
✅ API completamente documentada
✅ Pruebas interactivas en el navegador
✅ Esquemas OpenAPI estándar
✅ Fácil integración con otras aplicaciones

### Para Administradores
✅ Panel de administración en español
✅ Selector de idioma integrado
✅ Documentación de API accesible
✅ Fácil gestión de contenido bilingüe

## 🔗 Enlaces Útiles

- **Admin:** http://localhost:8000/admin/
- **Swagger UI:** http://localhost:8000/api/docs/
- **ReDoc:** http://localhost:8000/api/redoc/
- **Esquema OpenAPI:** http://localhost:8000/api/schema/

---

**¡Listo para usar en Paraguay y Ciudad del Este!** 🇵🇾
