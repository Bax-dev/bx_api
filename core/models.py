from django.db import models
from django.contrib.auth.models import User
from django.core.mail import send_mail
from twilio.rest import Client
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=15, blank=True)
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    low_balance_threshold = models.DecimalField(max_digits=10, decimal_places=2, default=0)

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    sent_via_email = models.BooleanField(default=False)
    sent_via_sms = models.BooleanField(default=False)

def send_email_notification(user, subject, message):
    try:
        profile = user.profile
    except ObjectDoesNotExist:
        return
    if profile.email_notifications:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )

def send_sms_notification(user, message):
    try:
        profile = user.profile
    except ObjectDoesNotExist:
        return
    if profile.sms_notifications and profile.phone_number:
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        client.messages.create(
            body=message,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=profile.phone_number
        )

def check_low_balance(user):
    try:
        profile = user.profile
    except ObjectDoesNotExist:
        return

    total_balance = sum(transaction.amount for transaction in Transaction.objects.filter(user=user, transaction_type=Transaction.DEPOSIT)) - sum(transaction.amount for transaction in Transaction.objects.filter(user=user, transaction_type=Transaction.WITHDRAWAL))
    
    if total_balance < profile.low_balance_threshold:
        subject = "Low Balance Alert"
        message = f"Your account balance is below your set threshold of {profile.low_balance_threshold}. Current balance: {total_balance}."
        send_email_notification(user, subject, message)
        send_sms_notification(user, message)

class Transaction(models.Model):
    DEPOSIT = 'DEPOSIT'
    WITHDRAWAL = 'WITHDRAWAL'
    TRANSFER = 'TRANSFER'
    PAYMENT = 'PAYMENT'

    TRANSACTION_TYPES = [
        (DEPOSIT, 'Deposit'),
        (WITHDRAWAL, 'Withdrawal'),
        (TRANSFER, 'Transfer'),
        (PAYMENT, 'Payment'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(
        max_length=20,
        choices=TRANSACTION_TYPES,
    )
    date = models.DateTimeField(auto_now_add=True)
    description = models.TextField()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        subject = f"New {self.get_transaction_type_display()} Transaction"
        message = f"A {self.get_transaction_type_display().lower()} of {self.amount} was made on your account."
        send_email_notification(self.user, subject, message)
        send_sms_notification(self.user, message)
        check_low_balance(self.user)

class Investment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    investment_type = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField(auto_now_add=True)

class Budget(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField()

class Expense(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    description = models.TextField(blank=True, null=True)

class SavingsGoal(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    goal_name = models.CharField(max_length=100)
    target_amount = models.DecimalField(max_digits=10, decimal_places=2)
    current_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    start_date = models.DateField()
    end_date = models.DateField()
