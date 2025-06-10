"""
Utility functions for the Credit Approval System.

This module provides:
- Loan eligibility calculation logic
- Customer validation helpers
- EMI calculation and related financial utilities

Business logic is separated from views and serializers for maintainability and reuse.
"""

from django.db.models import Sum
from django.db import DatabaseError
from decimal import Decimal
import math
from datetime import datetime
from rest_framework import status
from rest_framework.response import Response
from .models import Customer

def get_valid_customer(customer_id):
    """
    Retrieve a customer by ID and return a tuple of (customer, error_response).
    If the customer does not exist, error_response contains a DRF Response object.
    """
    try:
        customer = Customer.objects.get(customer_id=customer_id)
        if customer.monthly_income <= 0:
            return None, Response(
                {"error": "Customer's monthly income is invalid or zero."},
                status=status.HTTP_400_BAD_REQUEST
            )
        if customer.approved_limit <= 0:
            return None, Response(
                {"error": "Customer's approved limit is invalid or zero."},
                status=status.HTTP_400_BAD_REQUEST
            )
        return customer, None
    except Customer.DoesNotExist:
        return None, Response(
            {"error": "Customer not found."},
            status=status.HTTP_404_NOT_FOUND
        )

def calculate_emi(amount: Decimal, rate: Decimal, tenure: int) -> Decimal:
    """
    Calculate the monthly EMI for a loan.

    Args:
        amount (Decimal): Principal loan amount.
        rate (Decimal): Annual interest rate (percent).
        tenure (int): Tenure in months.

    Returns:
        Decimal: Monthly EMI amount.
    Raises:
        ValueError: If calculation parameters are invalid.
    """
    try:
        monthly_rate = rate / Decimal('100') / Decimal('12')
        if monthly_rate == 0:
            return amount / Decimal(str(tenure))
        term = (Decimal('1') + monthly_rate) ** tenure
        if term == 1:
            return amount / Decimal(str(tenure))
        emi = amount * monthly_rate * term / (term - Decimal('1'))
        return emi.quantize(Decimal('0.01'))
    except (OverflowError, ZeroDivisionError):
        raise ValueError("Error calculating EMI due to invalid parameters.")

def check_eligibility(customer, loan_amount, interest_rate, tenure):
    """
    Determine if a customer is eligible for a loan based on their credit score,
    current debt, and EMI-to-income ratio.
    """
    try:
        # Ensure all numbers are Decimal
        loan_amount = Decimal(str(loan_amount))
        interest_rate = Decimal(str(interest_rate))
        tenure = int(tenure)

        # Initialize
        credit_score = Decimal('0')
        approval = False
        corrected_interest_rate = Decimal(str(interest_rate))
        monthly_installment = Decimal('0')
        message = ""

        # Calculate credit score
        loans = customer.loans.all()
        if customer.current_debt > customer.approved_limit:
            credit_score = Decimal('0')
            message = "Loan rejected: Current debt exceeds approved limit."
        else:
            P = Decimal('0')
            if loans.exists():
                total_emis_paid = loans.aggregate(Sum('emi_paid_on_time'))['emi_paid_on_time__sum'] or 0
                total_tenure = loans.aggregate(Sum('tenure'))['tenure__sum'] or 1
                P = Decimal(str(total_emis_paid)) / Decimal(str(total_tenure))
            N = loans.count()
            N_norm = Decimal(str(math.exp(-0.1 * N)))
            current_year = datetime.now().year
            A = customer.loans.filter(start_date__year=current_year).count()
            A_norm = Decimal(str(math.exp(-0.2 * A)))
            V = loans.aggregate(Sum('loan_amount'))['loan_amount__sum'] or Decimal('0.00')
            V_norm = Decimal('1') / (Decimal('1') + Decimal('0.00001') * V)
            W1, W2, W3, W4 = Decimal('0.4'), Decimal('0.2'), Decimal('0.15'), Decimal('0.25')
            credit_score = Decimal('100') * (W1 * P + W2 * N_norm + W3 * A_norm + W4 * V_norm)
            credit_score = credit_score.quantize(Decimal('0.01'))
            message = "Loan eligibility calculated."

        # Determine eligibility
        try:
            if credit_score > 50:
                approval = True
            elif 30 < credit_score <= 50:
                approval = True
                if interest_rate <= 12:
                    corrected_interest_rate = Decimal('12.00')
                    message = "Loan approved with corrected interest rate of 12%."
            elif 10 < credit_score <= 30:
                approval = True
                if interest_rate <= 16:
                    corrected_interest_rate = Decimal('16.00')
                    message = "Loan approved with corrected interest rate of 16%."
            else:
                approval = False
                message = "Loan rejected: Credit score too low (<= 10)."

            monthly_installment = calculate_emi(loan_amount, corrected_interest_rate, tenure)
            if approval:
                current_emis = customer.loans.aggregate(Sum('monthly_payment'))['monthly_payment__sum'] or Decimal('0.00')
                emi_threshold = customer.monthly_income * Decimal('0.5')
                if current_emis + monthly_installment > emi_threshold:
                    approval = False
                    message = "Loan rejected: Total EMIs exceed 50% of monthly income."
        except ValueError as e:
            raise ValueError(str(e))

        return {
            'approval': approval,
            'corrected_interest_rate': corrected_interest_rate,
            'monthly_installment': monthly_installment,
            'message': message,
            'credit_score': credit_score
        }
    except DatabaseError:
        raise DatabaseError("Database error while calculating credit score.")