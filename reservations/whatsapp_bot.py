import requests
import json
from django.conf import settings
from .views import RoomAvailability, CreateReservation
from rest_framework.test import APIRequestFactory
from datetime import datetime, timedelta

WHATSAPP_API_URL = settings.WHATSAPP_API_URL
ACCESS_TOKEN = settings.WHATSAPP_ACCESS_TOKEN

def send_whatsapp_message(to, message):
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message}
    }
    
    response = requests.post(WHATSAPP_API_URL, headers=headers, data=json.dumps(data))
    return response.json()

def check_availability(check_in, check_out):
    factory = APIRequestFactory()
    request = factory.post('/availability/', {'check_in': check_in, 'check_out': check_out})
    view = RoomAvailability.as_view()
    response = view(request)
    if response.status_code == 200:
        return response.data['available_rooms']
    return None

def create_reservation(room_id, guest_name, check_in, check_out, total_price):
    factory = APIRequestFactory()
    data = {
        'room_id': room_id,
        'guest_name': guest_name,
        'check_in': check_in,
        'check_out': check_out,
        'total_price': total_price
    }
    request = factory.post('/reservations/', data)
    view = CreateReservation.as_view()
    response = view(request)
    return response.status_code == 201

def handle_incoming_message(sender, message_body):
    message_parts = message_body.lower().split()
    command = message_parts[0] if message_parts else ""

    if command == "disponibilidad":
        if len(message_parts) == 3:
            check_in = message_parts[1]
            check_out = message_parts[2]
            available_rooms = check_availability(check_in, check_out)
            if available_rooms:
                message = f"Habitaciones disponibles del {check_in} al {check_out}:\n"
                for room in available_rooms:
                    message += f"- {room['name']}: ${room['price']}/noche\n"
            else:
                message = "Lo siento, no hay habitaciones disponibles para esas fechas."
        else:
            message = "Por favor, especifica las fechas de entrada y salida. Ejemplo: disponibilidad 2023-06-01 2023-06-05"

    elif command == "reservar":
        if len(message_parts) == 5:
            room_id = int(message_parts[1])
            guest_name = message_parts[2]
            check_in = message_parts[3]
            check_out = message_parts[4]
            # Calcular precio total (ejemplo simple)
            days = (datetime.strptime(check_out, "%Y-%m-%d") - datetime.strptime(check_in, "%Y-%m-%d")).days
            total_price = days * 100  # Asumiendo un precio fijo de $100 por noche
            
            if create_reservation(room_id, guest_name, check_in, check_out, total_price):
                message = f"¡Reserva confirmada para {guest_name} del {check_in} al {check_out}! Total: ${total_price}"
            else:
                message = "Lo siento, no se pudo completar la reserva. Por favor, intenta de nuevo más tarde."
        else:
            message = "Para reservar, necesito: ID de habitación, tu nombre, fecha de entrada y salida. Ejemplo: reservar 1 JuanPerez 2023-06-01 2023-06-05"

    else:
        message = ("Bienvenido al Hotel Valle Grande. ¿En qué puedo ayudarte?\n"
                   "- Para verificar disponibilidad, escribe: disponibilidad YYYY-MM-DD YYYY-MM-DD\n"
                   "- Para hacer una reserva, escribe: reservar [ID_HABITACION] [TU_NOMBRE] YYYY-MM-DD YYYY-MM-DD\n"
                   "- Para más información, escribe: ayuda")

    send_whatsapp_message(sender, message)