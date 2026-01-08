from django.db import models
from django.utils.translation import gettext_lazy as _


class Tenant(models.Model):
    """
    Tenant model for multi-tenancy support.
    Each tenant represents a separate organization/business entity.
    """
    slug = models.SlugField(
        _('slug'),
        max_length=50,
        unique=True,
        db_index=True,
        help_text=_('Identificador único del tenant (usado en URLs)')
    )
    name = models.CharField(_('nombre'), max_length=255)
    is_active = models.BooleanField(_('activo'), default=True, db_index=True)
    settings = models.JSONField(
        _('configuración'),
        default=dict,
        blank=True,
        help_text=_('Configuraciones personalizadas del tenant')
    )

    # Contact information
    contact_email = models.EmailField(_('email de contacto'), blank=True)
    contact_phone = models.CharField(_('teléfono de contacto'), max_length=50, blank=True)
    logo_url = models.URLField(_('URL del logo'), blank=True)

    # Plan and limits (for future use)
    plan = models.CharField(_('plan'), max_length=50, default='basic')
    max_appointments_per_month = models.IntegerField(
        _('máximo de citas por mes'),
        default=1000,
        help_text=_('Límite de citas que puede crear por mes')
    )
    max_raffles = models.IntegerField(
        _('máximo de rifas'),
        default=10,
        help_text=_('Límite de rifas activas simultaneas')
    )

    # Timestamps
    created_at = models.DateTimeField(_('fecha de creación'), auto_now_add=True)
    updated_at = models.DateTimeField(_('fecha de actualización'), auto_now=True)

    class Meta:
        verbose_name = _('Tenant')
        verbose_name_plural = _('Tenants')
        ordering = ['name']
        indexes = [
            models.Index(fields=['slug', 'is_active']),
            models.Index(fields=['is_active', '-created_at']),
        ]

    def __str__(self):
        return f"{self.name} ({self.slug})"
