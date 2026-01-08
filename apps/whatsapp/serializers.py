from rest_framework import serializers
from apps.whatsapp.models import WhatsAppContact

class WhatsAppContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = WhatsAppContact
        fields = [
            'id',
            'wa_id',
            'name',
            'state',
            'last_interaction_at',
            'created_at',
        ]
        read_only_fields = ['state', 'last_interaction_at', 'created_at']

class EnsureContactSerializer(serializers.Serializer):
    wa_id = serializers.CharField(max_length=50)
    name = serializers.CharField(max_length=255, required=False, allow_blank=True)
