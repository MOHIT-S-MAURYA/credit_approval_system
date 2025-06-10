"""
Views for the Credit Approval System API.

This module contains API endpoints for:
- Registering customers
- Checking loan eligibility
- Viewing loan details
- Listing loans for a customer
- Creating new loans

Each view is implemented as a DRF APIView.
"""

# core/views.py

from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Customer, Loan
from .serializers import (
    CustomerRegisterSerializer, LoanDetailSerializer, CustomerLoanListSerializer,
    CheckEligibilityRequestSerializer, CheckEligibilityResponseSerializer,
    CreateLoanRequestSerializer, CreateLoanResponseSerializer
)
from .utils import check_eligibility, get_valid_customer
from django.db import transaction, DatabaseError, IntegrityError
from django.core.exceptions import ValidationError
from datetime import timedelta, datetime
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

def error_response(message, status_code=status.HTTP_400_BAD_REQUEST):
    return Response({"error": message}, status=status_code)

class RegisterCustomerView(generics.CreateAPIView):
    queryset = Customer.objects.all()
    serializer_class = CustomerRegisterSerializer

    def create(self, request, *args, **kwargs):
        try:
            return super().create(request, *args, **kwargs)
        except IntegrityError:
            logger.warning("Attempt to register duplicate phone number.")
            return error_response("A customer with this phone number already exists.", status.HTTP_400_BAD_REQUEST)
        except ValidationError as e:
            logger.warning(f"Validation error: {e}")
            return error_response(str(e), status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return error_response(f"Unexpected error: {str(e)}", status.HTTP_500_INTERNAL_SERVER_ERROR)

class CheckEligibilityView(APIView):
    def post(self, request):
        serializer = CheckEligibilityRequestSerializer(data=request.data)
        if not serializer.is_valid():
            logger.warning(f"Eligibility validation errors: {serializer.errors}")
            return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        data = serializer.validated_data
        customer, error_resp = get_valid_customer(data['customer_id'])
        if error_resp:
            return error_resp
        try:
            result = check_eligibility(customer, data['loan_amount'], data['interest_rate'], data['tenure'])
        except Exception as e:
            logger.error(f"Eligibility check failed: {e}")
            return error_response(str(e), status.HTTP_400_BAD_REQUEST)
        response_serializer = CheckEligibilityResponseSerializer(data={
            'customer_id': data['customer_id'],
            'approval': result['approval'],
            'interest_rate': float(data['interest_rate']),
            'corrected_interest_rate': float(result['corrected_interest_rate']),
            'tenure': data['tenure'],
            'monthly_installment': float(result['monthly_installment'])
        })
        if not response_serializer.is_valid():
            logger.error("Error formatting eligibility response data.")
            return error_response("Error formatting response data.", status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(response_serializer.data, status=status.HTTP_200_OK)

class ViewLoanDetail(APIView):
    def get(self, request, loan_id):
        try:
            loan = Loan.objects.select_related('customer').get(loan_id=loan_id)
            serializer = LoanDetailSerializer(loan)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Loan.DoesNotExist:
            logger.info(f"Loan not found: {loan_id}")
            return error_response('Loan not found', status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return error_response(str(e), status.HTTP_500_INTERNAL_SERVER_ERROR)

class ViewLoansByCustomer(APIView):
    def get(self, request, customer_id):
        try:
            customer = Customer.objects.get(pk=customer_id)
            loans = Loan.objects.filter(customer=customer)
            if not loans.exists():
                return Response({"message": "No loans found."}, status=status.HTTP_200_OK)
            serializer = CustomerLoanListSerializer(loans, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Customer.DoesNotExist:
            logger.info(f"Customer not found: {customer_id}")
            return error_response("Customer not found.", status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return error_response(str(e), status.HTTP_500_INTERNAL_SERVER_ERROR)

class CreateLoanView(APIView):
    def post(self, request):
        try:
            serializer = CreateLoanRequestSerializer(data=request.data)
            if not serializer.is_valid():
                logger.warning(f"Loan creation validation errors: {serializer.errors}")
                return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
            data = serializer.validated_data
            customer_id = data['customer_id']
            loan_amount = Decimal(str(data['loan_amount']))
            interest_rate = Decimal(str(data['interest_rate']))
            tenure = data['tenure']
            customer, error_resp = get_valid_customer(customer_id)
            if error_resp:
                return error_resp
            try:
                result = check_eligibility(customer, loan_amount, interest_rate, tenure)
            except DatabaseError:
                logger.error("Database error while calculating credit score.")
                return error_response("Database error while calculating credit score.", status.HTTP_500_INTERNAL_SERVER_ERROR)
            except ValueError as e:
                logger.warning(f"Value error: {e}")
                return error_response(str(e), status.HTTP_400_BAD_REQUEST)
            loan_id = None
            approval = result['approval']
            monthly_installment = result['monthly_installment']
            message = result['message']
            if approval:
                try:
                    with transaction.atomic():
                        start_date = datetime.now().date()
                        end_date = start_date + timedelta(days=tenure * 30)
                        loan = Loan.objects.create(
                            customer=customer,
                            loan_amount=loan_amount,
                            interest_rate=result['corrected_interest_rate'],
                            tenure=tenure,
                            monthly_payment=monthly_installment,
                            start_date=start_date,
                            end_date=end_date,
                            emi_paid_on_time=0
                        )
                        loan_id = loan.loan_id
                        message = "Loan approved and created successfully."
                except DatabaseError:
                    logger.error("Database error while creating loan.")
                    return error_response("Database error while creating loan.", status.HTTP_500_INTERNAL_SERVER_ERROR)
            response_data = {
                'loan_id': loan_id,
                'customer_id': customer_id,
                'loan_approved': approval,
                'message': message,
                'monthly_installment': float(monthly_installment)
            }
            response_serializer = CreateLoanResponseSerializer(data=response_data)
            if not response_serializer.is_valid():
                logger.error("Error formatting loan creation response data.")
                return error_response("Error formatting response data.", status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return error_response(f"Unexpected error: {str(e)}", status.HTTP_500_INTERNAL_SERVER_ERROR)
