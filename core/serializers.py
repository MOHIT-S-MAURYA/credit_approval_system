"""
Serializers for the Credit Approval System API.

This module defines serializers for:
- Customer registration and detail
- Loan detail and creation
- Eligibility checks
- Listing loans for a customer

Serializers handle validation and transformation between model instances and JSON representations.
"""

# core/serializers.py

from rest_framework import serializers
from .models import Customer, Loan

# Serializer for registering a new customer
class CustomerRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['first_name', 'last_name', 'age', 'phone_number', 'monthly_income']

    def create(self, validated_data):
        income = validated_data['monthly_income']
        approved_limit = round(36 * income, -5)  # round to nearest lakh
        validated_data['approved_limit'] = approved_limit
        return super().create(validated_data)

    def to_representation(self, instance):
        return {
            "customer_id": instance.customer_id,
            "name": f"{instance.first_name} {instance.last_name}",
            "age": instance.age,
            "monthly_income": instance.monthly_income,
            "approved_limit": instance.approved_limit,
            "phone_number": instance.phone_number
        }

# Serializer for checking customer eligibility for a loan
class CheckEligibilityRequestSerializer(serializers.Serializer):
    customer_id = serializers.IntegerField(
        min_value=1,
        error_messages={
            "min_value": "Customer ID must be a positive integer.",
            "required": "Customer ID is required.",
            "invalid": "Customer ID must be an integer."
        }
    )
    loan_amount = serializers.FloatField(
        min_value=0.01,
        error_messages={
            "min_value": "Loan amount must be greater than 0.",
            "required": "Loan amount is required.",
            "invalid": "Loan amount must be a valid number."
        }
    )
    interest_rate = serializers.FloatField(
        min_value=0.0,
        error_messages={
            "min_value": "Interest rate cannot be negative.",
            "required": "Interest rate is required.",
            "invalid": "Interest rate must be a valid number."
        }
    )
    tenure = serializers.IntegerField(
        min_value=1,
        error_messages={
            "min_value": "Tenure must be at least 1 month.",
            "required": "Tenure is required.",
            "invalid": "Tenure must be an integer."
        }
    )

    def validate_customer_id(self, value):
        if not Customer.objects.filter(customer_id=value).exists():
            raise serializers.ValidationError("Customer with this ID does not exist.")
        return value

class CheckEligibilityResponseSerializer(serializers.Serializer):
    customer_id = serializers.IntegerField()
    approval = serializers.BooleanField()
    interest_rate = serializers.FloatField()
    corrected_interest_rate = serializers.FloatField()
    tenure = serializers.IntegerField()
    monthly_installment = serializers.FloatField()

# Serializer for viewing loan details    
class CustomerBriefSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='customer_id')

    class Meta:
        model = Customer
        fields = ['id', 'first_name', 'last_name', 'phone_number', 'age']

class LoanDetailSerializer(serializers.ModelSerializer):
    customer = CustomerBriefSerializer()
    monthly_installment = serializers.DecimalField(
        source='monthly_payment',
        max_digits=12,
        decimal_places=2
    )

    class Meta:
        model = Loan
        fields = [
            'loan_id',
            'customer',
            'loan_amount',
            'interest_rate',
            'monthly_installment',  # This will show in API response
            'tenure',
        ]

# Serializer for listing loans for a customer
class CustomerLoanListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing loans associated with a customer.
    Includes monthly installment and repayments left.
    """
    monthly_installment = serializers.DecimalField(
        source='monthly_payment',
        max_digits=12,
        decimal_places=2
    )
    repayments_left = serializers.SerializerMethodField()

    class Meta:
        model = Loan
        fields = [
            'loan_id',
            'loan_amount',
            'interest_rate',
            'monthly_installment',
            'repayments_left',
        ]

    def get_repayments_left(self, obj):
        """
        Calculate the number of repayments left for the loan.
        """
        return obj.tenure - obj.emi_paid_on_time
    
# Serializer for creating a new loan
class CreateLoanRequestSerializer(serializers.Serializer):
    customer_id = serializers.IntegerField(
        min_value=1,
        error_messages={
            "min_value": "Customer ID must be a positive integer.",
            "required": "Customer ID is required.",
            "invalid": "Customer ID must be an integer."
        }
    )
    loan_amount = serializers.FloatField(
        min_value=0.01,
        error_messages={
            "min_value": "Loan amount must be greater than 0.",
            "required": "Loan amount is required.",
            "invalid": "Loan amount must be a valid number."
        }
    )
    interest_rate = serializers.FloatField(
        min_value=0.0,
        error_messages={
            "min_value": "Interest rate cannot be negative.",
            "required": "Interest rate is required.",
            "invalid": "Interest rate must be a valid number."
        }
    )
    tenure = serializers.IntegerField(
        min_value=1,
        error_messages={
            "min_value": "Tenure must be at least 1 month.",
            "required": "Tenure is required.",
            "invalid": "Tenure must be an integer."
        }
    )

    def validate_customer_id(self, value):
        if not Customer.objects.filter(customer_id=value).exists():
            raise serializers.ValidationError("Customer with this ID does not exist.")
        return value

class CreateLoanResponseSerializer(serializers.Serializer):
    loan_id = serializers.IntegerField(allow_null=True)
    customer_id = serializers.IntegerField()
    loan_approved = serializers.BooleanField()
    message = serializers.CharField()
    monthly_installment = serializers.FloatField()