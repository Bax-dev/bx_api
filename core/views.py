from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse
from django.db.models import Sum, F
from .models import Profile, Transaction, Investment, Budget, Expense, SavingsGoal
from .serializers import UserSerializer, ProfileSerializer, TransactionSerializer, InvestmentSerializer, BudgetSerializer, ExpenseSerializer, SavingsGoalSerializer
from .utils import standard_response
from django.utils.dateparse import parse_date
from .visualization_utils import generate_bar_chart, generate_pie_chart, generate_line_chart
from django.contrib.auth.models import User
from .twilio_utils import send_sms
from io import BytesIO
import csv
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny, IsAuthenticated

class CustomBaseViewSet(viewsets.ModelViewSet):
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = '__all__'
    search_fields = '__all__'
    ordering_fields = '__all__'
    ordering = ['id']

    def get_model_name(self):
        return self.queryset.model.__name__

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return standard_response(
            success=True,
            message=f"{self.get_model_name()} created successfully.",
            data=response.data,
            status=response.status_code
        )

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        return standard_response(
            success=True,
            message=f"{self.get_model_name()} updated successfully.",
            data=response.data,
            status=response.status_code
        )

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return standard_response(
            success=True,
            message=f"{self.get_model_name()} list retrieved successfully.",
            data=response.data,
            status=response.status_code
        )

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        return standard_response(
            success=True,
            message=f"{self.get_model_name()} details retrieved successfully.",
            data=response.data,
            status=response.status_code
        )

    def destroy(self, request, *args, **kwargs):
        super().destroy(request, *args, **kwargs)
        return standard_response(
            success=True,
            message=f"{self.get_model_name()} deleted successfully.",
            status=status.HTTP_204_NO_CONTENT
        )

class UserViewSet(CustomBaseViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

class ProfileViewSet(CustomBaseViewSet):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer

    @action(detail=False, methods=['get'])
    def active(self, request):
        active_profiles = self.queryset.filter(is_active=True)
        serializer = self.get_serializer(active_profiles, many=True)
        return standard_response(
            success=True,
            message="Active profiles retrieved successfully.",
            data=serializer.data
        )


class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        transaction = self.get_object()
        user = transaction.user
        try:
            profile = user.profile
        except Profile.DoesNotExist:
            raise NotFound(detail="Profile does not exist for the user.")
        
        transaction.status = 'approved'
        transaction.save()
        return standard_response(
            success=True,
            message="Transaction approved successfully.",
            data=TransactionSerializer(transaction).data
        )

    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        serializer = self.get_serializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        self.perform_bulk_create(serializer)
        return standard_response(
            success=True,
            message="Bulk transactions created successfully.",
            data=serializer.data
        )

    def perform_bulk_create(self, serializer):
        transactions = [Transaction(**item) for item in serializer.validated_data]
        for transaction in transactions:
            try:
                profile = transaction.user.profile
            except Profile.DoesNotExist:
                raise NotFound(detail=f"Profile does not exist for the user {transaction.user.username}.")
        Transaction.objects.bulk_create(transactions)

    @action(detail=False, methods=['put'])
    def bulk_update(self, request):
        serializer = self.get_serializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        self.perform_bulk_update(serializer)
        return standard_response(
            {
                "success": True,
                "message": "Bulk transactions updated successfully.",
                "data": serializer.data
            }
        )

    def perform_bulk_update(self, serializer):
        for item in serializer.validated_data:
            transaction_id = item.get('id')
            try:
                transaction = Transaction.objects.get(pk=transaction_id)
                Transaction.objects.filter(pk=transaction_id).update(**item)
            except Transaction.DoesNotExist:
                raise NotFound(detail=f"Transaction with ID {transaction_id} does not exist.")

    @action(detail=False, methods=['get'])
    def filter_by_date(self, request):
        start_date = request.query_params.get('start_date', None)
        end_date = request.query_params.get('end_date', None)
        transactions = self.queryset.all()

        if start_date:
            transactions = transactions.filter(date__gte=start_date)
        if end_date:
            transactions = transactions.filter(date__lte=end_date)

        serializer = self.get_serializer(transactions, many=True)
        return standard_response(
            success=True,
            message="Transactions filtered by date successfully.",
            data=serializer.data
        )

    @action(detail=False, methods=['get'])
    def analytics(self, request):
        transactions = self.queryset.values('date', 'amount')
        data = [{'date': t['date'], 'amount': t['amount']} for t in transactions]
        bar_chart = generate_bar_chart(data, 'Transactions Over Time', 'date', 'amount')
        line_chart = generate_line_chart(data, 'Transactions Over Time', 'date', 'amount')
        return standard_response(
            success=True,
            message="Transaction analytics retrieved successfully.",
            data={'bar_chart': bar_chart, 'line_chart': line_chart}
        )

   
    @action(detail=False, methods=['get', 'post'], permission_classes=[AllowAny])
    def generate_statement(self, request):
        start_date = request.data.get('start_date') or request.query_params.get('start_date')
        end_date = request.data.get('end_date') or request.query_params.get('end_date')

        # Allow filtering by date range for all transactions
        transactions = self.queryset.all()
        if start_date:
            transactions = transactions.filter(date__gte=start_date)
        if end_date:
            transactions = transactions.filter(date__lte=end_date)
        
        if not transactions.exists():
            return Response(
                {"detail": "No transactions found for the specified date range."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response(
            {
                "success": True,
                "message": "Account statement generated successfully.",
                "data": TransactionSerializer(transactions, many=True).data
            }
        )

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def export_csv(self, request):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        # Filter transactions by date range if provided
        transactions = self.queryset.all()
        if start_date:
            transactions = transactions.filter(date__gte=start_date)
        if end_date:
            transactions = transactions.filter(date__lte=end_date)

        if not transactions.exists():
            return Response(
                {"detail": "No transactions found for the specified date range."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Create the CSV response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="transactions.csv"'

        writer = csv.writer(response)
        writer.writerow(['Date', 'Amount', 'Transaction Type', 'Description'])

        for transaction in transactions:
            writer.writerow([transaction.date, transaction.amount, transaction.transaction_type, transaction.description])

        return response



    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def export_pdf(self, request):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        # Ensure the date range is handled, default to the whole dataset if not specified
        transactions = self.queryset.all()
        if start_date:
            transactions = transactions.filter(date__gte=start_date)
        if end_date:
            transactions = transactions.filter(date__lte=end_date)

        if not transactions.exists():
            return Response(
                {"detail": "No transactions found for the specified date range."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Generate the PDF
        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=letter)
        pdf.drawString(100, 750, "Transaction Statement")
        pdf.drawString(100, 735, f"From {start_date} to {end_date}")

        y = 700
        pdf.drawString(100, y, "Date")
        pdf.drawString(200, y, "Amount")
        pdf.drawString(300, y, "Type")
        pdf.drawString(400, y, "Description")

        for transaction in transactions:
            y -= 15
            pdf.drawString(100, y, str(transaction.date))
            pdf.drawString(200, y, str(transaction.amount))
            pdf.drawString(300, y, transaction.transaction_type)
            pdf.drawString(400, y, transaction.description)

        pdf.showPage()
        pdf.save()
        buffer.seek(0)

        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="transactions.pdf"'
        return response

class InvestmentViewSet(CustomBaseViewSet):
    queryset = Investment.objects.all()
    serializer_class = InvestmentSerializer

    @action(detail=False, methods=['get'])
    def filter_by_date(self, request):
        start_date = request.query_params.get('start_date', None)
        end_date = request.query_params.get('end_date', None)
        investments = self.queryset.all()

        if start_date:
            investments = investments.filter(date__gte=start_date)
        if end_date:
            investments = investments.filter(date__lte=end_date)

        serializer = self.get_serializer(investments, many=True)
        return standard_response(
            success=True,
            message="Investments filtered by date successfully.",
            data=serializer.data
        )

    @action(detail=False, methods=['get'])
    def analytics(self, request):
        investments = self.queryset.values('date', 'amount')
        data = [{'date': i['date'], 'amount': i['amount']} for i in investments]
        bar_chart = generate_bar_chart(data, 'Investments Over Time', 'date', 'amount')
        line_chart = generate_line_chart(data, 'Investments Over Time', 'date', 'amount')
        return standard_response(
            success=True,
            message="Investment analytics retrieved successfully.",
            data={'bar_chart': bar_chart, 'line_chart': line_chart}
        )

class BudgetViewSet(CustomBaseViewSet):
    queryset = Budget.objects.all()
    serializer_class = BudgetSerializer

    @action(detail=False, methods=['get'])
    def analytics(self, request):
        total_budget = self.queryset.aggregate(total_amount=Sum('amount'))['total_amount']
        budget_by_category = self.queryset.values('category').annotate(total_amount=Sum('amount'))

        return standard_response(
            success=True,
            message="Budget analytics retrieved successfully.",
            data={
                "total_budget": total_budget,
                "budget_by_category": budget_by_category
            }
        )

class ExpenseViewSet(CustomBaseViewSet):
    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer

    @action(detail=False, methods=['get'])
    def filter_by_date(self, request):
        start_date = request.query_params.get('start_date', None)
        end_date = request.query_params.get('end_date', None)
        expenses = self.queryset.all()

        if start_date:
            expenses = expenses.filter(date__gte=start_date)
        if end_date:
            expenses = expenses.filter(date__lte=end_date)

        serializer = self.get_serializer(expenses, many=True)
        return standard_response(
            success=True,
            message="Expenses filtered by date successfully.",
            data=serializer.data
        )

class SavingsGoalViewSet(CustomBaseViewSet):
    queryset = SavingsGoal.objects.all()
    serializer_class = SavingsGoalSerializer

    @action(detail=False, methods=['get'])
    def active_goals(self, request):
        active_goals = self.queryset.filter(current_amount__lt=F('target_amount'))
        serializer = self.get_serializer(active_goals, many=True)
        return standard_response(
            success=True,
            message="Active savings goals retrieved successfully.",
            data=serializer.data
        )

class FinancialAdviceView(APIView):
    def get(self, request):
        advice = {
            "save_more": "Consider setting aside 20% of your income each month to increase your savings.",
            "reduce_expenses": "Review your monthly subscriptions and cancel any that are not necessary.",
            "invest_wisely": "Diversify your investments to reduce risk and improve returns.",
            "budgeting": "Create a monthly budget and stick to it to manage your finances effectively."
        }
        return standard_response(
            success=True,
            message="Financial advice retrieved successfully.",
            data=advice
        )

def notify_user_of_transaction(user_phone_number, transaction_details):
    message = f"Your recent transaction: {transaction_details}"
    send_sms(user_phone_number, message)

class BalanceView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        user = request.user

        if user.is_authenticated:
            try:
                profile = user.profile
            except Profile.DoesNotExist:
                return Response(
                    {"detail": "Profile does not exist for the user."},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Calculate total balance for authenticated users
            total_balance = (
                Transaction.objects.filter(user=user, transaction_type=Transaction.DEPOSIT).aggregate(total=Sum('amount'))['total'] or 0
            ) - (
                Transaction.objects.filter(user=user, transaction_type=Transaction.WITHDRAWAL).aggregate(total=Sum('amount'))['total'] or 0
            )

            return Response(
                {
                    "success": True,
                    "message": "Current balance retrieved successfully.",
                    "data": {'balance': total_balance}
                }
            )
        else:
            # Provide a generic response for anonymous users
            return standard_response(
                {
                    "success": True,
                    "message": "Current balance information is not available for anonymous users.",
                    "data": {'balance': 0}  # Default value or empty data
                }
            )
class StatementView(APIView):
    def get(self, request):
        # Access query parameters safely
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')

        # Parse dates and handle missing or invalid date inputs
        start_date = parse_date(start_date_str) if start_date_str else None
        end_date = parse_date(end_date_str) if end_date_str else None

        # Validate dates
        if not start_date or not end_date:
            return Response(
                {"detail": "Both start date and end date must be provided and be valid ISO format dates."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if start_date > end_date:
            return Response(
                {"detail": "Start date cannot be after end date."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Ensure the user is authenticated (optional, if required)
        user = request.user
        if not user.is_authenticated:
            return Response(
                {"detail": "Authentication credentials were not provided."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Fetch transactions within the date range
        transactions = Transaction.objects.filter(user=user, date__range=(start_date, end_date))

        # Determine response format
        response_format = request.query_params.get('format', 'json')
        if response_format == 'csv':
            return self.generate_csv_response(transactions)
        elif response_format == 'pdf':
            return self.generate_pdf_response(transactions)

        # Default JSON response
        serializer = TransactionSerializer(transactions, many=True)
        return standard_response(
            success=True,
            message="Account statement retrieved successfully.",
            data=serializer.data
        )

    def generate_csv_response(self, transactions):
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Date', 'Transaction Type', 'Amount', 'Description'])

        for transaction in transactions:
            writer.writerow([transaction.date, transaction.get_transaction_type_display(), transaction.amount, transaction.description])

        output.seek(0)
        response = HttpResponse(output, content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=statement.csv'
        return response

    def generate_pdf_response(self, transactions):
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer)

        p.drawString(100, 800, "Account Statement")
        y = 750
        for transaction in transactions:
            p.drawString(100, y, f"{transaction.date} - {transaction.get_transaction_type_display()} - {transaction.amount} - {transaction.description}")
            y -= 20

        p.showPage()
        p.save()

        pdf = buffer.getvalue()
        buffer.close()
        
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename=statement.pdf'
        return response