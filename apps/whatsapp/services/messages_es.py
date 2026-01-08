"""
Spanish messages for WhatsApp bot
Mensajes en español para el bot de WhatsApp
"""

# Welcome messages
MSG_WELCOME = "¡Bienvenido! Escribe 'menu' para ver las opciones disponibles o 'rifas' para explorar rifas activas."

MSG_MAIN_MENU = "¿Qué te gustaría hacer?"

# Raffle browsing
MSG_NO_ACTIVE_RAFFLES = "No hay rifas activas en este momento. ¡Vuelve pronto!"

MSG_ACTIVE_RAFFLES_HEADER = "*Rifas Activas:*\n"

MSG_SELECT_RAFFLE = "\nResponde con el número de rifa (1-{count}) para participar."

# Raffle details
MSG_RAFFLE_DETAILS = """*{title}*

{description}

💰 Precio: {currency} {price} por número
🎫 Números: {min_number} - {max_number}
✅ Disponibles: {available}/{total}
🔥 Vendidos: {sold}/{total}

¿Cómo te gustaría seleccionar tus números?

1. Escribe números específicos (ej: '5,12,99' o '5 12 99')
2. Escribe 'aleatorio X' para X números al azar (ej: 'aleatorio 5')
3. Escribe 'volver' para ver otras rifas"""

# Number selection
MSG_INVALID_NUMBER_FORMAT = "Formato inválido. Por favor ingresa números separados por comas o espacios (ej: '5,12,99')"

MSG_TRY_DIFFERENT_NUMBERS = "\nPor favor intenta con números diferentes o escribe 'volver'."

MSG_TRY_DIFFERENT_QUANTITY = "\nPor favor intenta con una cantidad diferente o escribe 'volver'."

# Order confirmation
MSG_ORDER_CREATED = """✅ *¡Pedido Creado!*

Rifa: {raffle_title}
Números: {numbers}
Cantidad: {qty}
Total: {currency} {total}

⏰ Reservado por {timeout} minutos

¿Confirmas este pedido?
1. Escribe 'confirmar' para continuar
2. Escribe 'cancelar' para cancelar"""

MSG_ORDER_CANCELLED = "Pedido cancelado. Tus números han sido liberados."

MSG_CONFIRM_OR_CANCEL = "Por favor escribe 'confirmar' para continuar o 'cancelar' para cancelar el pedido."

# Payment
MSG_PAYMENT_INSTRUCTIONS = """💳 *Instrucciones de Pago*

Monto: {currency} {amount}

Por favor realiza el pago y envía una captura de pantalla o foto del comprobante de pago.

¡Una vez verificado, tus números serán confirmados!

Pedido #{order_id}"""

MSG_PAYMENT_PROOF_RECEIVED = """✅ ¡Comprobante de pago recibido!

Tu pedido está en revisión. Serás notificado una vez confirmado.

Escribe 'menu' para volver al menú principal."""

MSG_PAYMENT_PROOF_REQUEST = """Por favor envía una foto o captura de pantalla de tu comprobante de pago.

Escribe 'saltar' si deseas enviar sin comprobante."""

MSG_PAYMENT_SKIPPED = """Pedido guardado sin comprobante de pago. El administrador se pondrá en contacto contigo.

Escribe 'menu' para volver al menú principal."""

MSG_CHECK_ORDER_STATUS = """Por favor sube tu comprobante de pago (foto/captura).

Escribe 'estado' para verificar el estado de tu pedido."""

# Errors and session
MSG_SESSION_EXPIRED = "Sesión expirada. Escribe 'rifas' para comenzar de nuevo."

MSG_RAFFLE_NOT_AVAILABLE = "Rifa ya no disponible. Escribe 'rifas' para ver rifas activas."

MSG_ERROR_OCCURRED = "Ocurrió un error. Por favor intenta de nuevo o escribe 'menu'."

MSG_SOMETHING_WENT_WRONG = "Lo siento, algo salió mal. Escribe 'menu' para comenzar de nuevo."

MSG_INVALID_SELECTION = "Selección inválida. Por favor ingresa un número de rifa o escribe 'menu'."

# Button/menu options
BTN_BROWSE_RAFFLES = "Ver Rifas"
BTN_MY_ORDERS = "Mis Pedidos"
BTN_HELP = "Ayuda"

# Helper text
TXT_MENU_OPTIONS = """¡Bienvenido!

1. Escribe 'rifas' para explorar rifas activas
2. Escribe 'pedidos' para ver tus pedidos
3. Escribe 'ayuda' para asistencia"""

# Payment confirmation (sent when admin confirms payment)
MSG_PAYMENT_CONFIRMED = """🎉 *¡PAGO CONFIRMADO!*

¡Felicidades {name}! Tu pago ha sido verificado.

*Rifa:* {raffle_title}
*Números:* {numbers}
*Cantidad:* {qty} boleto(s)
*Total Pagado:* {currency} {total}

Tus números están confirmados para el sorteo.

¡Mucha suerte! 🍀

Escribe 'menu' si necesitas algo más."""
