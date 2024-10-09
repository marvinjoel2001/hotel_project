from django.urls import path
from .views import RoomAvailability, CreateReservation, ProcessPayment, whatsapp_webhook

urlpatterns = [
    path('availability/', RoomAvailability.as_view(), name='room_availability'),
    path('reservations/', CreateReservation.as_view(), name='create_reservation'),
    path('payments/<int:reservation_id>/', ProcessPayment.as_view(), name='process_payment'),
    path('whatsapp-webhook/', whatsapp_webhook, name='whatsapp_webhook'),
]