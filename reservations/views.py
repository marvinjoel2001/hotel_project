from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
import odoorpc
from datetime import datetime
from .serializers import AvailabilitySerializer, ReservationSerializer
from .models import Reservation
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .whatsapp_bot import handle_incoming_message
import json

class OdooMixin:
    def get_odoo(self):
        odoo = odoorpc.ODOO(settings.ODOO_HOST, port=settings.ODOO_PORT)
        odoo.login(settings.ODOO_DB, settings.ODOO_USER, settings.ODOO_PASSWORD)
        return odoo

class RoomAvailability(OdooMixin, APIView):
    def post(self, request):
        serializer = AvailabilitySerializer(data=request.data)
        if serializer.is_valid():
            check_in = serializer.validated_data['check_in']
            check_out = serializer.validated_data['check_out']

            if check_in >= check_out:
                return Response({"error": "Check-out debe ser posterior a check-in"}, status=status.HTTP_400_BAD_REQUEST)

            if check_in < datetime.now().date():
                return Response({"error": "La fecha de check-in no puede ser en el pasado"}, status=status.HTTP_400_BAD_REQUEST)

            odoo = self.get_odoo()
            Product = odoo.env['product.product']
            
            room_products = Product.search([
                ('name', 'ilike', 'habitacion'),
                ('type', '=', 'product'),
            ])
            
            available_rooms = []
            for room_id in room_products:
                room = Product.browse(room_id)
                if room.qty_available > 0:
                    available_rooms.append({
                        'id': room.id,
                        'name': room.name,
                        'price': room.list_price,
                    })
            
            return Response({"available_rooms": available_rooms}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CreateReservation(OdooMixin, APIView):
    def post(self, request):
        serializer = ReservationSerializer(data=request.data)
        if serializer.is_valid():
            try:
                odoo = self.get_odoo()
                SaleOrder = odoo.env['sale.order']
                SaleOrderLine = odoo.env['sale.order.line']
                
                order_id = SaleOrder.create({
                    'partner_id': 1,  # Deberías tener una forma de obtener o crear clientes
                    'date_order': serializer.validated_data['check_in'],
                    'state': 'draft',
                })
                
                SaleOrderLine.create({
                    'order_id': order_id,
                    'product_id': serializer.validated_data['room_id'],
                    'product_uom_qty': 1,
                    'price_unit': serializer.validated_data['total_price'],
                })
                
                reservation = serializer.save(odoo_order_id=order_id)
                
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ProcessPayment(OdooMixin, APIView):
    def post(self, request, reservation_id):
        try:
            reservation = Reservation.objects.get(id=reservation_id)
        except Reservation.DoesNotExist:
            return Response({"error": "Reservation not found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            odoo = self.get_odoo()
            Payment = odoo.env['account.payment']
            SaleOrder = odoo.env['sale.order']

            payment_id = Payment.create({
                'amount': reservation.total_price,
                'payment_type': 'inbound',
                'partner_type': 'customer',
                'partner_id': 1,  # Asume un ID de cliente por defecto
            })

            order = SaleOrder.search([('name', '=', reservation.odoo_order_id)])
            if order:
                SaleOrder.write(order[0], {'state': 'paid'})

            reservation.is_paid = True
            reservation.save()

            return Response({"message": "Payment processed successfully"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
@csrf_exempt
def whatsapp_webhook(request):
    if request.method == 'GET':
        if request.GET.get('hub.verify_token') == settings.WHATSAPP_VERIFY_TOKEN:
            return HttpResponse(request.GET.get('hub.challenge'))
        else:
            return HttpResponse('Error de autenticación.', status=403)
    elif request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        try:
            for entry in data['entry']:
                for change in entry['changes']:
                    if change['field'] == 'messages':
                        for message in change['value']['messages']:
                            sender = message['from']
                            message_body = message['text']['body']
                            handle_incoming_message(sender, message_body)
            return HttpResponse('Evento recibido', status=200)
        except Exception as e:
            return HttpResponse(str(e), status=500)