from django.core.management.base import BaseCommand
from core.models import Customer, Loan  # Make sure app name is correct
from decimal import Decimal, ROUND_HALF_UP

class Command(BaseCommand):
    help = "Update the current_debt field of each customer based on active loans"

    def handle(self, *args, **kwargs):
        customers = Customer.objects.all()
        updated_count = 0

        for customer in customers:
            # Get all loans for this customer
            loans = Loan.objects.filter(customer=customer)

            # Calculate total debt: unpaid EMIs * monthly_payment
            total_debt = 0
            for loan in loans:
                emis_left = loan.tenure - loan.emi_paid_on_time
                if emis_left > 0:
                    total_debt += float(emis_left) * float(loan.monthly_payment)
            # Quantize to 2 decimal places
            customer.current_debt = Decimal(str(total_debt)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            customer.save()
            updated_count += 1
