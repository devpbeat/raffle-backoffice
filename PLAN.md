# Multi-Tenant Backoffice + Appointment Scheduler - Implementation Plan

## Overview

Adding multi-tenancy and appointment scheduling to the Django raffle backoffice using a **shared database with tenant_id isolation** pattern.

### Key Decisions
- **Multi-tenancy**: Shared DB with `tenant` ForeignKey on all models
- **Tenant identification**: URL-based (`/tenant/{slug}/api/...`)
- **Scope**: Both raffles AND appointments are multi-tenant
- **Appointment features**: Services, customers, bookings, payment (Bancard mock), calendar sync (Google Calendar mock)
- **Payment integration**: Bancard mock for both appointments and raffles

---

## Phase 1: Core Multi-Tenancy Foundation ✅ COMPLETED

### What Was Done

#### 1.1 Core App with Tenant Model ✅
- Created `apps/core/` Django app
- Implemented `Tenant` model with:
  - `slug` (URL identifier)
  - `name`, `is_active`, `settings` (JSON)
  - Contact info: `contact_email`, `contact_phone`, `logo_url`
  - Plan limits: `plan`, `max_appointments_per_month`, `max_raffles`
- Admin interface for Tenant management (superuser only)
- Jazzmin integration with icon

**Files:**
- `apps/core/models.py`
- `apps/core/admin.py`
- `apps/core/apps.py`

#### 1.2 Default Tenant Creation ✅
- Data migration to create "default" tenant
- All existing data assigned to this tenant
- Backward compatibility maintained

**Files:**
- `apps/core/migrations/0002_create_default_tenant.py`

#### 1.3 Tenant ForeignKey Added to Existing Models ✅
- **Raffle** model: Added `tenant` FK with index
- **Order** model: Added `tenant` FK with index
- **WhatsAppContact** model: Added `tenant` FK with index
- Compound indexes added: `(tenant, status, -created_at)`, `(tenant, -created_at)`

**Files Modified:**
- `apps/raffles/models.py`
- `apps/whatsapp/models.py`

#### 1.4 Migrations ✅
All migrations created and applied successfully:
- `core.0001_initial` - Create Tenant model
- `core.0002_create_default_tenant` - Create default tenant
- `raffles.0002_*` - Add nullable tenant FK to Raffle and Order
- `whatsapp.0002_*` - Add nullable tenant FK to WhatsAppContact
- `raffles.0003_set_default_tenant` - Assign default tenant to existing data
- `whatsapp.0003_set_default_tenant` - Assign default tenant to existing data
- `raffles.0004_*` - Make tenant non-nullable, add indexes
- `whatsapp.0004_*` - Make tenant non-nullable, add indexes

**Result:** Zero data loss. All 28.5 MB of existing data preserved.

#### 1.5 Tenant Middleware ✅
Implemented URL-based tenant identification middleware.

**Features:**
- Extracts tenant slug from URL: `/tenant/{slug}/api/...`
- Attaches `request.tenant` and `request.tenant_slug` to all requests
- Returns 404 if tenant not found or inactive

**Files:**
- `apps/core/middleware.py`
- `core/settings.py` (middleware added after AuthenticationMiddleware)

#### 1.6 URL Configuration ✅
Updated URL routing to support tenant-scoped endpoints.

**Structure:**
```
/admin/                                    # Global admin (superuser)
/tenant/{slug}/api/raffles/               # Tenant-scoped raffles API
/tenant/{slug}/api/whatsapp/              # Tenant-scoped whatsapp API
/api/raffles/                             # Backward compatible (global)
/whatsapp/webhook/                        # Webhook (tenant-agnostic)
```

**Files:**
- `core/urls.py`

---

## Phase 2: Appointment Scheduler Module 🚧 IN PROGRESS

### 2.1 Create Appointments App

**Models to Create:**

#### Service Model
```python
class Service(models.Model):
    tenant = ForeignKey('core.Tenant')
    name = CharField(max_length=255)
    description = TextField(blank=True)
    duration_minutes = IntegerField()
    price = DecimalField(max_digits=10, decimal_places=2)
    currency = CharField(max_length=3, default='USD')
    is_active = BooleanField(default=True)

    # Scheduling constraints
    buffer_time_minutes = IntegerField(default=0)
    max_bookings_per_day = IntegerField(default=20)
    advance_booking_days = IntegerField(default=30)

    created_at, updated_at
```

#### Customer Model
```python
class Customer(models.Model):
    tenant = ForeignKey('core.Tenant')
    name = CharField(max_length=255)
    email = EmailField(blank=True)
    phone = CharField(max_length=50)
    notes = TextField(blank=True)

    created_at, updated_at
    last_appointment_at = DateTimeField(null=True)
```

#### Appointment Model
```python
class Appointment(models.Model):
    tenant = ForeignKey('core.Tenant')
    service = ForeignKey(Service)
    customer = ForeignKey(Customer)

    scheduled_at = DateTimeField()
    duration_minutes = IntegerField()

    # Status fields
    status = CharField(choices=AppointmentStatus)  # PENDING/CONFIRMED/CANCELLED/COMPLETED/NO_SHOW
    payment_status = CharField(choices=PaymentStatus)  # PENDING/PAID/REFUNDED

    total_amount = DecimalField()
    currency = CharField()

    # Integration IDs
    bancard_transaction_id = CharField(null=True)
    google_calendar_event_id = CharField(null=True)

    # Notes
    customer_notes = TextField(blank=True)
    internal_notes = TextField(blank=True)

    # Timestamps
    created_at, updated_at
    confirmed_at, cancelled_at, completed_at
```

**Files to Create:**
- `apps/appointments/models.py`
- `apps/appointments/apps.py`
- `apps/appointments/__init__.py`

**Actions:**
1. Create app structure
2. Define models with Spanish verbose_name
3. Add to `INSTALLED_APPS`
4. Create and run migrations

### 2.2 Implement Booking Service Layer

**Service Functions:**

```python
# apps/appointments/services/bookings.py

@transaction.atomic
def create_appointment(tenant, service_id, customer_data, scheduled_at, notes=''):
    """Create appointment with availability checking."""
    # Validate service exists and is active
    # Check slot availability
    # Get or create customer
    # Create appointment
    # Return Appointment instance
    pass

def is_slot_available(tenant, service, scheduled_at):
    """Check if time slot is available."""
    # Check for overlapping appointments
    # Check daily booking limit
    # Return bool
    pass

@transaction.atomic
def confirm_appointment(appointment, payment_transaction_id=None):
    """Confirm appointment after payment."""
    # Update status to CONFIRMED
    # Set payment_status to PAID
    # Set confirmed_at timestamp
    # Return updated Appointment
    pass

@transaction.atomic
def cancel_appointment(appointment, reason=''):
    """Cancel appointment."""
    # Update status to CANCELLED
    # Set cancelled_at timestamp
    # Add reason to internal_notes
    # Return updated Appointment
    pass
```

**Availability Service:**
```python
# apps/appointments/services/availability.py

def get_available_slots(tenant, service, date, duration_minutes=None):
    """Get available time slots for a service on a date."""
    # Get business hours from tenant.settings
    # Generate potential slots (every 30 minutes)
    # Filter out unavailable slots
    # Return list of datetime objects
    pass
```

**Files to Create:**
- `apps/appointments/services/__init__.py`
- `apps/appointments/services/bookings.py`
- `apps/appointments/services/availability.py`

### 2.3 DRF Serializers & ViewSets

**Serializers:**
```python
# apps/appointments/serializers.py

class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = '__all__'
        read_only_fields = ['tenant', 'created_at', 'updated_at']

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'
        read_only_fields = ['tenant', 'created_at', 'updated_at', 'last_appointment_at']

class AppointmentSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source='service.name', read_only=True)
    customer_name = serializers.CharField(source='customer.name', read_only=True)

    class Meta:
        model = Appointment
        fields = '__all__'
        read_only_fields = ['tenant', 'created_at', 'updated_at', 'confirmed_at', 'cancelled_at', 'completed_at']

class CreateAppointmentSerializer(serializers.Serializer):
    service = serializers.PrimaryKeyRelatedField(queryset=Service.objects.all())
    customer_data = serializers.DictField()
    scheduled_at = serializers.DateTimeField()
    customer_notes = serializers.CharField(required=False, allow_blank=True)
```

**ViewSets:**
```python
# apps/appointments/api_views.py

class ServiceViewSet(viewsets.ModelViewSet):
    serializer_class = ServiceSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['is_active']

    def get_queryset(self):
        return Service.objects.filter(tenant=self.request.tenant)

    def perform_create(self, serializer):
        serializer.save(tenant=self.request.tenant)

class AppointmentViewSet(viewsets.ModelViewSet):
    serializer_class = AppointmentSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        return Appointment.objects.filter(tenant=self.request.tenant)

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """POST /api/appointments/{id}/confirm/"""
        pass

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """POST /api/appointments/{id}/cancel/"""
        pass

    @action(detail=False, methods=['get'])
    def availability(self, request):
        """GET /api/appointments/availability/?service=1&date=2025-01-10"""
        pass
```

**Files to Create:**
- `apps/appointments/serializers.py`
- `apps/appointments/api_views.py`
- `apps/appointments/urls.py`

### 2.4 Admin Interface

**Jazzmin Admin Configuration:**
```python
# apps/appointments/admin.py

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['name', 'tenant', 'duration_minutes', 'price_display', 'is_active']
    list_filter = ['tenant', 'is_active', 'created_at']
    search_fields = ['name', 'description']

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['customer_name', 'service_name', 'scheduled_at', 'status_badge', 'payment_status_badge']
    list_filter = ['status', 'payment_status', 'tenant', 'service', 'scheduled_at']
    actions = ['confirm_appointments', 'cancel_appointments']

    def status_badge(self, obj):
        colors = {'PENDING': 'orange', 'CONFIRMED': 'green', 'CANCELLED': 'red'}
        return format_html('<span style="background-color: {}; color: white; padding: 3px 10px;">{}</span>',
                          colors.get(obj.status, 'gray'), obj.get_status_display())
```

**Update settings.py:**
```python
JAZZMIN_SETTINGS = {
    'search_model': [..., 'appointments.Service', 'appointments.Customer', 'appointments.Appointment'],
    'icons': {
        'appointments.Service': 'fas fa-concierge-bell',
        'appointments.Customer': 'fas fa-user-friends',
        'appointments.Appointment': 'fas fa-calendar-check',
    },
}
```

**Files to Create:**
- `apps/appointments/admin.py`

**Files to Update:**
- `core/settings.py`

### 2.5 URL Routing

Add to `core/urls.py`:
```python
path('tenant/<slug:tenant_slug>/', include([
    path('api/', include([
        path('appointments/', include('apps.appointments.urls')),  # NEW
    ])),
])),
```

---

## Phase 3: Payment Integration (Bancard Mock) 🔜 PENDING

### 3.1 Create Payments App

**Models:**
```python
class PaymentProvider(models.TextChoices):
    BANCARD = 'BANCARD'
    MANUAL = 'MANUAL'

class PaymentTransaction(models.Model):
    tenant = ForeignKey('core.Tenant')
    provider = CharField(choices=PaymentProvider)
    external_id = CharField(max_length=255, db_index=True)
    amount = DecimalField()
    currency = CharField()
    status = CharField(db_index=True)

    # Polymorphic linking to Order or Appointment
    content_type = ForeignKey(ContentType)
    object_id = PositiveIntegerField()
    content_object = GenericForeignKey()

    raw_response = JSONField()
    created_at, confirmed_at
```

**Files to Create:**
- `apps/payments/models.py`
- `apps/payments/apps.py`

### 3.2 Bancard Mock Service

```python
# apps/payments/services/bancard.py

class BancardMockClient:
    def __init__(self, merchant_id, api_key):
        self.merchant_id = merchant_id
        self.api_key = api_key

    def create_payment_request(self, amount, currency, order_id, description):
        """Returns: {transaction_id, payment_url, status}"""
        pass

    def check_payment_status(self, transaction_id):
        """Returns: {status: 'paid'|'pending'|'failed'}"""
        pass

    def process_webhook(self, payload, signature):
        """Verify and process webhook"""
        pass

def get_bancard_client(tenant):
    """Get configured Bancard client for tenant"""
    pass
```

**Files to Create:**
- `apps/payments/services/__init__.py`
- `apps/payments/services/bancard.py`

### 3.3 Webhook Endpoint

```python
# apps/payments/api_views.py

@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def bancard_webhook(request, tenant_slug):
    """POST /tenant/{slug}/api/payments/bancard/webhook/"""
    # Get tenant
    # Process webhook using BancardMockClient
    # Find appointment or order
    # Confirm payment
    # Return 200
    pass
```

**Files to Create:**
- `apps/payments/api_views.py`
- `apps/payments/urls.py`

### 3.4 Add bancard_transaction_id to Order

**Update:**
- `apps/raffles/models.py` - Add `bancard_transaction_id` field to Order model
- Create migration

---

## Phase 4: Calendar Integration (Google Calendar Mock) 🔜 PENDING

### 4.1 Create Integrations App

**Models:**
```python
class IntegrationType(models.TextChoices):
    GOOGLE_CALENDAR = 'GOOGLE_CALENDAR'
    BANCARD = 'BANCARD'

class TenantIntegration(models.Model):
    tenant = ForeignKey('core.Tenant')
    integration_type = CharField(choices=IntegrationType)
    is_active = BooleanField(default=True)
    config = JSONField()  # Store credentials/settings
    created_at

    class Meta:
        unique_together = [['tenant', 'integration_type']]
```

**Files to Create:**
- `apps/integrations/models.py`
- `apps/integrations/apps.py`

### 4.2 Google Calendar Mock Service

```python
# apps/integrations/services/google_calendar.py

class GoogleCalendarMockClient:
    def __init__(self, calendar_id, credentials):
        self.calendar_id = calendar_id
        self.credentials = credentials

    def create_event(self, summary, start_time, end_time, description='', attendees=None):
        """Returns: {event_id, link, status}"""
        pass

    def update_event(self, event_id, **kwargs):
        """Returns: {event_id, updated}"""
        pass

    def delete_event(self, event_id):
        """Returns: bool"""
        pass

def sync_appointment_to_calendar(appointment):
    """Sync appointment to Google Calendar"""
    # Get client for tenant
    # Create or update calendar event
    # Store event_id in appointment.google_calendar_event_id
    pass
```

**Files to Create:**
- `apps/integrations/services/__init__.py`
- `apps/integrations/services/google_calendar.py`

### 4.3 Hook Calendar Sync

Update `apps/appointments/services/bookings.py`:
```python
@transaction.atomic
def confirm_appointment(appointment, payment_transaction_id=None):
    # ... existing logic ...

    # Sync to calendar
    from apps.integrations.services.google_calendar import sync_appointment_to_calendar
    sync_appointment_to_calendar(appointment)

    return appointment
```

---

## Phase 5: Tenant-Aware Admin with Role Permissions 👤 USER WILL IMPLEMENT

### Requirements

**User Types:**
1. **Superusers** - Full access across all tenants
2. **Tenant Admins** - Full access within their tenant(s)
3. **Staff Users** - Limited access (view + modify specific fields) within their tenant

### Features Needed

#### 5.1 User-Tenant Association
- Add `ManyToManyField` to User model or create `UserTenantRole` model
- Store which tenant(s) each user can access
- Store role per tenant (admin, staff, viewer)

#### 5.2 Admin Queryset Filtering
Update all admin classes to filter by user's tenant:
```python
def get_queryset(self, request):
    qs = super().get_queryset(request)
    if request.user.is_superuser:
        return qs
    # Filter by user's assigned tenants
    return qs.filter(tenant__in=request.user.tenants.all())
```

#### 5.3 Permission Customization
```python
def has_add_permission(self, request):
    if request.user.is_superuser:
        return True
    # Check if user is admin for any tenant
    return request.user.tenant_roles.filter(role='admin').exists()

def has_change_permission(self, request, obj=None):
    if request.user.is_superuser:
        return True
    if obj and obj.tenant not in request.user.tenants.all():
        return False
    return True
```

#### 5.4 Field-Level Permissions
For staff users, limit which fields they can edit:
```python
def get_readonly_fields(self, request, obj=None):
    if request.user.is_superuser:
        return []

    # Tenant admins can edit all fields
    if request.user.tenant_roles.filter(tenant=obj.tenant, role='admin').exists():
        return []

    # Staff can only edit certain fields
    return ['tenant', 'created_at', 'total_amount', 'status']
```

**Files to Update:**
- `apps/raffles/admin.py`
- `apps/whatsapp/admin.py`
- `apps/appointments/admin.py` (when created)
- `apps/core/admin.py`

**Models to Create:**
- `apps/core/models.py` - Add `UserTenantRole` model or similar

---

## Phase 6: Testing & Documentation 🔜 PENDING

### 6.1 Create Test Data Command

```python
# apps/core/management/commands/create_test_tenants.py

class Command(BaseCommand):
    def handle(self, *args, **options):
        # Create test tenants
        salon = Tenant.objects.create(slug='salon-beauty', name='Beauty Salon')
        clinic = Tenant.objects.create(slug='clinic-health', name='Health Clinic')

        # Create services for salon
        Service.objects.create(tenant=salon, name='Haircut', duration_minutes=30, price=25.00)
        Service.objects.create(tenant=salon, name='Hair Coloring', duration_minutes=90, price=75.00)

        # Create services for clinic
        Service.objects.create(tenant=clinic, name='General Consultation', duration_minutes=30, price=50.00)
```

**Files to Create:**
- `apps/core/management/commands/create_test_tenants.py`

### 6.2 Unit Tests

Test files to create:
- `apps/appointments/tests/test_bookings.py` - Test booking service functions
- `apps/appointments/tests/test_api.py` - Test API endpoints
- `apps/core/tests/test_tenant_isolation.py` - Test cross-tenant access prevention

### 6.3 Integration Tests

Test payment webhook processing and calendar sync.

---

## API Endpoint Summary

### Appointments
```
GET    /tenant/{slug}/api/appointments/                       List appointments
POST   /tenant/{slug}/api/appointments/                       Create appointment
GET    /tenant/{slug}/api/appointments/{id}/                 Get appointment
PUT    /tenant/{slug}/api/appointments/{id}/                 Update appointment
DELETE /tenant/{slug}/api/appointments/{id}/                 Delete appointment
POST   /tenant/{slug}/api/appointments/{id}/confirm/         Confirm + pay
POST   /tenant/{slug}/api/appointments/{id}/cancel/          Cancel
GET    /tenant/{slug}/api/appointments/availability/         Available slots
```

### Services
```
GET    /tenant/{slug}/api/services/                          List services
POST   /tenant/{slug}/api/services/                          Create service
GET    /tenant/{slug}/api/services/{id}/                     Get service
PUT    /tenant/{slug}/api/services/{id}/                     Update service
DELETE /tenant/{slug}/api/services/{id}/                     Delete service
```

### Customers
```
GET    /tenant/{slug}/api/customers/                         List customers
POST   /tenant/{slug}/api/customers/                         Create customer
GET    /tenant/{slug}/api/customers/{id}/                    Get customer
PUT    /tenant/{slug}/api/customers/{id}/                    Update customer
DELETE /tenant/{slug}/api/customers/{id}/                    Delete customer
```

### Payments
```
POST   /tenant/{slug}/api/payments/bancard/webhook/          Bancard webhook
```

---

## Migration Commands Reference

```bash
# Phase 1 (COMPLETED)
uv run python manage.py makemigrations core
uv run python manage.py migrate core
uv run python manage.py makemigrations raffles whatsapp
uv run python manage.py migrate raffles
uv run python manage.py migrate whatsapp

# Phase 2 (Appointments)
uv run python manage.py makemigrations appointments
uv run python manage.py migrate appointments

# Phase 3 (Payments)
uv run python manage.py makemigrations payments
uv run python manage.py migrate payments

# Phase 4 (Integrations)
uv run python manage.py makemigrations integrations
uv run python manage.py migrate integrations
```

---

## Success Criteria

✅ Phase 1: Multi-tenant architecture with URL-based identification
⏳ Phase 2: Appointment scheduler with services, customers, bookings
⏳ Phase 3: Payment integration with Bancard mock service
⏳ Phase 4: Calendar sync with Google Calendar mock service
👤 Phase 5: Tenant-aware admin (user implements)
⏳ Phase 6: Testing and documentation

---

## Notes

- All models use Spanish `verbose_name` for consistency
- Service layer pattern used throughout (following existing `reservations.py`)
- Transaction atomicity for all data modifications
- Jazzmin admin with color-coded status badges
- UV package manager (no pip/requirements.txt)
- SQLite compatible (no PostgreSQL-specific features)

---

## Current Status

**Completed:** Phase 1 (Multi-tenancy foundation)
**In Progress:** Phase 2 (Appointment scheduler)
**User Task:** Phase 5 (Tenant-aware admin with Copilot)

**Database Status:** ✅ All existing data preserved, zero data loss
**Backward Compatibility:** ✅ Global API routes still work
**System Health:** ✅ Fully operational
