"""
Django models for the Credit Approval System.

Defines:
- Customer: Stores customer personal and financial information.
- Loan: Stores loan details and maintains customer debt consistency.

Includes logic to update customer debt on loan creation and deletion.
"""

from django.db import models, transaction
from decimal import Decimal
from django.core.exceptions import ValidationError

class Customer(models.Model):
    """
    Model representing a customer in the credit approval system.
    """
    customer_id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    age = models.PositiveIntegerField()
    phone_number = models.CharField(max_length=15, unique=True)
    monthly_income = models.DecimalField(max_digits=10, decimal_places=2)
    approved_limit = models.DecimalField(max_digits=12, decimal_places=2)
    current_debt = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)

    def __str__(self):
        """
        String representation of the customer.
        """
        return f"{self.first_name} {self.last_name} ({self.customer_id})"

    def clean(self):
        if self.monthly_income < 0:
            raise ValidationError("Monthly income cannot be negative.")
        if self.current_debt < 0:
            raise ValidationError("Current debt cannot be negative.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

class Loan(models.Model):
    """
    Model representing a loan taken by a customer.
    Automatically updates the customer's current debt on creation and deletion.
    """
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
        """
        On creation, increase the customer's current debt by the loan amount.
        On update, just save the loan.
        """
        self.full_clean()
        with transaction.atomic():
            is_new = self._state.adding
            super().save(*args, **kwargs)
            if is_new:
                self.customer.current_debt += self.loan_amount
                self.customer.save()

    def delete(self, *args, **kwargs):
        """
        On deletion, decrease the customer's current debt by the loan amount.
        """
        with transaction.atomic():
            self.customer.current_debt -= self.loan_amount
            if self.customer.current_debt < Decimal('0.0'):
                self.customer.current_debt = Decimal('0.0')
            self.customer.save()
            super().delete(*args, **kwargs)

    def clean(self):
        if self.loan_amount <= 0:
            raise ValidationError("Loan amount must be positive.")
        if self.interest_rate < 0:
            raise ValidationError("Interest rate cannot be negative.")
        if self.tenure <= 0:
            raise ValidationError("Tenure must be positive.")

    def __str__(self):
        """
        String representation of the loan.
        """
        return f"Loan {self.loan_id} for Customer {self.customer.customer_id}"
