from django.db import models

class Reservation(models.Model):
    room_id = models.IntegerField()
    guest_name = models.CharField(max_length=100)
    check_in = models.DateField()
    check_out = models.DateField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    is_paid = models.BooleanField(default=False)
    odoo_order_id = models.CharField(max_length=20, null=True, blank=True)

    def __str__(self):
        return f"{self.guest_name} - {self.check_in} to {self.check_out}"