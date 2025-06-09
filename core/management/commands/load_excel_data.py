import pandas as pd
from django.core.management.base import BaseCommand
from core.models import Customer, Loan
from decimal import Decimal, ROUND_HALF_UP


class Command(BaseCommand):
    help = 'Ingests data from customer_data.xlsx and loan_data.xlsx'

    def handle(self, *args, **kwargs):
        try:
            self.stdout.write("📥 Loading customer_data.xlsx...")
            customer_df = pd.read_excel('customer_data.xlsx')
            customer_df.columns = [col.strip().lower().replace(' ', '_') for col in customer_df.columns]

            for _, row in customer_df.iterrows():
                Customer.objects.update_or_create(
                    customer_id=row['customer_id'],
                    defaults={
                        'first_name': row['first_name'],
                        'last_name': row['last_name'],
                        'age': row['age'],
                        'phone_number': str(row['phone_number']),
                        'monthly_income': row['monthly_salary'],
                        'approved_limit': row['approved_limit'],
                        'current_debt': 0  # Assuming 0 if not present
                    }
                )

            self.stdout.write(self.style.SUCCESS("✅ Customers data ingested."))

            self.stdout.write("📥 Loading loan_data.xlsx...")
            loan_df = pd.read_excel('loan_data.xlsx')
            loan_df.columns = [col.strip().lower().replace(' ', '_') for col in loan_df.columns]

            for _, row in loan_df.iterrows():
                try:
                    customer = Customer.objects.get(customer_id=row['customer_id'])

                    # Ensure interest_rate has exactly 2 decimal places
                    interest_rate = Decimal(str(row['interest_rate'])).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

                    Loan.objects.update_or_create(
                        loan_id=row['loan_id'],
                        defaults={
                            'customer': customer,
                            'loan_amount': row['loan_amount'],
                            'interest_rate': interest_rate,
                            'tenure': row['tenure'],
                            'monthly_payment': row['monthly_payment'],
                            'emi_paid_on_time': row['emis_paid_on_time'],
                            'start_date': pd.to_datetime(row['date_of_approval']).date(),
                            'end_date': pd.to_datetime(row['end_date']).date(),
                        }
                    )
                except Customer.DoesNotExist:
                    self.stdout.write(self.style.WARNING(
                        f"⚠️ Skipped loan {row['loan_id']} (customer {row['customer_id']} not found)"
                    ))

            self.stdout.write(self.style.SUCCESS("✅ Loans data ingested."))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error occurred: {e}"))
