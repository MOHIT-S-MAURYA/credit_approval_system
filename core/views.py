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

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import CustomerRegisterSerializer, LoanDetailSerializer, CustomerLoanListSerializer, CheckEligibilityRequestSerializer, CheckEligibilityResponseSerializer, CreateLoanRequestSerializer, CreateLoanResponseSerializer
from .utils import check_eligibility
from django.db import transaction
from datetime import timedelta
from .models import Customer, Loan
from datetime import datetime
from decimal import Decimal
from django.db import DatabaseError


# Register a new Customer
class RegisterCustomerView(APIView):
    """
    API endpoint to register a new customer.
    """
    def post(self, request):
        """
        Create a new customer with the provided data.
        """
        serializer = CustomerRegisterSerializer(data=request.data)
        if serializer.is_valid():
            customer = serializer.save()
            return Response(serializer.to_representation(customer), status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Check Customer Eligibility for a Loan
class CheckEligibilityView(APIView):
    """
    API endpoint to check a customer's eligibility for a loan.
    """
    def post(self, request):
        """
        Validate customer and loan data, check eligibility, and return result.
        """
        try:
            # Validate request data
            serializer = CheckEligibilityRequestSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    {"errors": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Extract validated data
            data = serializer.validated_data
            customer_id = data['customer_id']
            loan_amount = Decimal(str(data['loan_amount']))
            interest_rate = Decimal(str(data['interest_rate']))
            tenure = data['tenure']

            # Fetch customer
            try:
                customer = Customer.objects.get(customer_id=customer_id)
            except Customer.DoesNotExist:
                return Response(
                    {"error": "Customer not found."},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Validate customer data
            if customer.monthly_income <= 0:
                return Response(
                    {"error": "Customer's monthly income is invalid or zero."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if customer.approved_limit <= 0:
                return Response(
                    {"error":  "Customer's approved limit is invalid or zero."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Check eligibility
            try:
                result = check_eligibility(customer, loan_amount, interest_rate, tenure)
            except DatabaseError:
                return Response(
                    {"error": "Database error while calculating credit score."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            except ValueError as e:
                return Response(
                    {"error": str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Prepare response
            response_data = {
                'customer_id': customer_id,
                'approval': result['approval'],
                'interest_rate': float(interest_rate),
                'corrected_interest_rate': float(result['corrected_interest_rate']),
                'tenure': tenure,
                'monthly_installment': float(result['monthly_installment'])
            }
            response_serializer = CheckEligibilityResponseSerializer(data=response_data)
            if not response_serializer.is_valid():
                return Response(
                    {"error": "Error formatting response data."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            return Response(response_serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": f"Unexpected error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        

# View Loan Detail by loan_id
class ViewLoanDetail(APIView):
    """
    API endpoint to retrieve details of a specific loan by loan_id.
    """
    def get(self, request, loan_id):
        """
        Return loan details for the given loan_id.
        """
        try:
            loan = Loan.objects.select_related('customer').get(loan_id=loan_id)
            serializer = LoanDetailSerializer(loan)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Loan.DoesNotExist:
            return Response({'error': 'Loan not found'}, status=status.HTTP_404_NOT_FOUND)


# View Loans by Customer ID
class ViewLoansByCustomer(APIView):
    """
    API endpoint to list all loans for a specific customer.
    """
    def get(self, request, customer_id):
        """
        Return all loans associated with the given customer_id.
        """
        try:
            customer = Customer.objects.get(pk=customer_id)
            loans = Loan.objects.filter(customer=customer)
            if not loans.exists():
                return Response({"message": "No loans found."}, status=status.HTTP_200_OK)
            serializer = CustomerLoanListSerializer(loans, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Customer.DoesNotExist:
            return Response({"error": "Customer not found."}, status=status.HTTP_404_NOT_FOUND)

# Create a new Loan
class CreateLoanView(APIView):
    """
    API endpoint to create a new loan for a customer if eligible.
    """
    def post(self, request):
        """
        Validate request, check eligibility, and create loan if approved.
        """
        try:
            # Validate request data
            serializer = CreateLoanRequestSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    {"errors": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Extract validated data
            data = serializer.validated_data
            customer_id = data['customer_id']
            loan_amount = Decimal(str(data['loan_amount']))
            interest_rate = Decimal(str(data['interest_rate']))
            tenure = data['tenure']

            # Fetch customer
            try:
                customer = Customer.objects.get(customer_id=customer_id)
            except Customer.DoesNotExist:
                return Response(
                    {"error": "Customer not found."},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Validate customer data
            if customer.monthly_income <= 0:
                return Response(
                    {"error": "Customer's monthly income is invalid or zero."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if customer.approved_limit <= 0:
                return Response(
                    {"error": "Customer's approved limit is invalid or zero."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Check eligibility
            try:
                result = check_eligibility(customer, loan_amount, interest_rate, tenure)
            except DatabaseError:
                return Response(
                    {"error": "Database error while calculating credit score."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            except ValueError as e:
                return Response(
                    {"error": str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Initialize response fields
            loan_id = None
            approval = result['approval']
            monthly_installment = result['monthly_installment']
            message = result['message']

            # Create loan if approved
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
                    return Response(
                        {"error": "Database error while creating loan."},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )

            # Prepare response
            response_data = {
                'loan_id': loan_id,
                'customer_id': customer_id,
                'loan_approved': approval,
                'message': message,
                'monthly_installment': float(monthly_installment)
            }
            response_serializer = CreateLoanResponseSerializer(data=response_data)
            if not response_serializer.is_valid():
                return Response(
                    {"error": "Error formatting response data."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            return Response(response_serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": f"Unexpected error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )