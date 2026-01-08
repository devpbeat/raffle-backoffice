from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.whatsapp.models import WhatsAppContact
from apps.whatsapp.serializers import WhatsAppContactSerializer, EnsureContactSerializer

class WhatsAppContactViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = WhatsAppContact.objects.all()
    serializer_class = WhatsAppContactSerializer
    lookup_field = 'wa_id'

    @action(detail=False, methods=['post'])
    def ensure(self, request):
        """
        Get or create a WhatsApp contact by wa_id.
        """
        serializer = EnsureContactSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        wa_id = serializer.validated_data['wa_id']
        name = serializer.validated_data.get('name')

        contact, created = WhatsAppContact.objects.get_or_create(
            wa_id=wa_id,
            defaults={'name': name}
        )

        if not created and name and contact.name != name:
            contact.name = name
            contact.save(update_fields=['name'])

        return Response(
            WhatsAppContactSerializer(contact).data,
            status=status.HTTP_200_OK if not created else status.HTTP_201_CREATED
        )
