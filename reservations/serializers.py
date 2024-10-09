from rest_framework import serializers
from .models import Reservation

class ReservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reservation
        fields = '__all__'

class AvailabilitySerializer(serializers.Serializer):
    check_in = serializers.DateField()
    check_out = serializers.DateField()