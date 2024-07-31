from django.urls import path, include
from rest_framework_nested import routers
from .views import UserViewSet, ProfileViewSet, TransactionViewSet, InvestmentViewSet, BudgetViewSet, ExpenseViewSet, SavingsGoalViewSet, FinancialAdviceView, BalanceView, StatementView

router = routers.DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'profiles', ProfileViewSet)
router.register(r'transactions', TransactionViewSet)
router.register(r'investments', InvestmentViewSet)
router.register(r'budgets', BudgetViewSet)
router.register(r'expenses', ExpenseViewSet)  
router.register(r'savings-goals', SavingsGoalViewSet)  

# Define nested routes
users_router = routers.NestedDefaultRouter(router, r'users', lookup='user')
users_router.register(r'profiles', ProfileViewSet, basename='user-profiles')
users_router.register(r'transactions', TransactionViewSet, basename='user-transactions')
users_router.register(r'investments', InvestmentViewSet, basename='user-investments')
users_router.register(r'budgets', BudgetViewSet, basename='user-budgets')
users_router.register(r'expenses', ExpenseViewSet, basename='user-expenses')  
users_router.register(r'savings-goals', SavingsGoalViewSet, basename='user-savings-goals') 

urlpatterns = [
    path('', include(router.urls)),
    path('', include(users_router.urls)),
    path('financial-advice/', FinancialAdviceView.as_view(), name='financial-advice'),
    path('balance/', BalanceView.as_view(), name='balance'),
    path('statement/', StatementView.as_view(), name='statement'),
]
