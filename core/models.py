from django.db import models
from decimal import Decimal

# Create your models here.

class Customer(models.Model):
    customer_id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    age = models.PositiveIntegerField()
    phone_number = models.CharField(max_length=15, unique=True)
    monthly_income = models.DecimalField(max_digits=10, decimal_places=2)
    approved_limit = models.DecimalField(max_digits=12, decimal_places=2)
    current_debt = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.customer_id})"

class Loan(models.Model):
    loan_id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="loans")
    loan_amount = models.DecimalField(max_digits=12, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    tenure = models.PositiveIntegerField(help_text="Tenure in months")
    monthly_payment = models.DecimalField(max_digits=12, decimal_places=2)
    emi_paid_on_time = models.PositiveIntegerField(default=0)
    start_date = models.DateField()
    end_date = models.DateField()

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        if not is_new:
            # Existing loan update — handle if needed
            return super().save(*args, **kwargs)

        # New loan: increase customer debt
        super().save(*args, **kwargs)
        self.customer.current_debt += self.loan_amount
        self.customer.save()

    def delete(self, *args, **kwargs):
        # Reduce customer's current debt before deleting
        self.customer.current_debt -= self.loan_amount
        if self.customer.current_debt < Decimal('0.0'):
            self.customer.current_debt = Decimal('0.0')
        self.customer.save()
        super().delete(*args, **kwargs)

    def __str__(self):
        return f"Loan {self.loan_id} for Customer {self.customer.customer_id}"
