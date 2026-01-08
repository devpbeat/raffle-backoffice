from datetime import datetime, timedelta
from django.utils import timezone
from apps.appointments.models import Appointment, AppointmentStatus


def get_available_slots(tenant, service, date, duration_minutes=None):
    """
    Get available time slots for a service on a given date.

    Args:
        tenant: Tenant instance
        service: Service instance
        date: datetime.date object or datetime object
        duration_minutes: Optional custom duration (defaults to service duration)

    Returns:
        List of available datetime objects
    """
    if duration_minutes is None:
        duration_minutes = service.duration_minutes

    # Get business hours from tenant settings (default: 9 AM to 6 PM)
    business_hours = tenant.settings.get('business_hours', {
        'start': 9,  # 9 AM
        'end': 18,   # 6 PM
    })

    start_hour = business_hours.get('start', 9)
    end_hour = business_hours.get('end', 18)

    # Convert date to datetime if needed
    if isinstance(date, datetime):
        date = date.date()

    # Generate potential slots (every 30 minutes by default)
    slot_interval_minutes = tenant.settings.get('slot_interval_minutes', 30)
    slots = []

    # Create timezone-aware datetime for the start of the day
    current = timezone.make_aware(
        datetime.combine(date, datetime.min.time()).replace(hour=start_hour)
    )
    end_time = timezone.make_aware(
        datetime.combine(date, datetime.min.time()).replace(hour=end_hour)
    )

    # Generate all possible slots
    while current + timedelta(minutes=duration_minutes) <= end_time:
        slots.append(current)
        current += timedelta(minutes=slot_interval_minutes)

    # Filter out unavailable slots
    from apps.appointments.services.bookings import is_slot_available
    available_slots = []

    for slot in slots:
        # Skip past slots
        if slot <= timezone.now():
            continue

        # Check availability
        if is_slot_available(tenant, service, slot):
            available_slots.append(slot)

    return available_slots


def get_next_available_slot(tenant, service, start_from=None):
    """
    Get the next available time slot for a service.

    Args:
        tenant: Tenant instance
        service: Service instance
        start_from: Optional datetime to start searching from (defaults to now)

    Returns:
        datetime: Next available slot, or None if no slots available in next 30 days
    """
    if start_from is None:
        start_from = timezone.now()

    # Search for next 30 days
    for day_offset in range(30):
        search_date = (start_from + timedelta(days=day_offset)).date()
        available_slots = get_available_slots(tenant, service, search_date)

        if available_slots:
            # Return first available slot of the day
            return available_slots[0]

    return None


def get_availability_calendar(tenant, service, start_date, end_date):
    """
    Get availability calendar for a service across a date range.

    Args:
        tenant: Tenant instance
        service: Service instance
        start_date: Start date for the calendar
        end_date: End date for the calendar

    Returns:
        dict: {
            'date': {
                'available_count': int,
                'booked_count': int,
                'slots': [list of available datetimes]
            }
        }
    """
    calendar = {}
    current_date = start_date

    while current_date <= end_date:
        # Get available slots for this date
        available_slots = get_available_slots(tenant, service, current_date)

        # Count booked appointments for this date
        day_start = timezone.make_aware(datetime.combine(current_date, datetime.min.time()))
        day_end = day_start + timedelta(days=1)

        booked_count = Appointment.objects.filter(
            tenant=tenant,
            service=service,
            scheduled_at__gte=day_start,
            scheduled_at__lt=day_end,
            status__in=[AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED]
        ).count()

        calendar[current_date.isoformat()] = {
            'available_count': len(available_slots),
            'booked_count': booked_count,
            'slots': available_slots
        }

        current_date += timedelta(days=1)

    return calendar


def is_service_available_on_date(tenant, service, date):
    """
    Check if a service has any availability on a specific date.

    Args:
        tenant: Tenant instance
        service: Service instance
        date: datetime.date object

    Returns:
        bool: True if service has at least one available slot on the date
    """
    available_slots = get_available_slots(tenant, service, date)
    return len(available_slots) > 0
