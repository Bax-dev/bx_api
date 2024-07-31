from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Profile, Transaction, Investment, Budget, Expense, SavingsGoal

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Profile
        fields = ['user', 'phone_number']

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user = User.objects.create(**user_data)
        profile = Profile.objects.create(user=user, **validated_data)
        return profile

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        user = instance.user

        instance.phone_number = validated_data.get('phone_number', instance.phone_number)
        instance.save()

        if user_data:
            user.username = user_data.get('username', user.username)
            user.email = user_data.get('email', user.email)
            user.first_name = user_data.get('first_name', user.first_name)
            user.last_name = user_data.get('last_name', user.last_name)
            user.save()

        return instance

class TransactionSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = Transaction
        fields = ['id', 'user', 'amount', 'transaction_type', 'date', 'description']

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("The amount must be greater than zero.")
        return value

class InvestmentSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = Investment
        fields = ['id', 'user', 'investment_type', 'amount', 'date']

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("The amount must be greater than zero.")
        return value

class BudgetSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = Budget
        fields = ['id', 'user', 'category', 'amount', 'start_date', 'end_date']

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("The amount must be greater than zero.")
        return value

    def validate(self, data):
        if data['start_date'] > data['end_date']:
            raise serializers.ValidationError("Start date must be before end date.")
        return data

class ExpenseSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = Expense
        fields = ['id', 'user', 'category', 'amount', 'date', 'description']

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("The amount must be greater than zero.")
        return value

class SavingsGoalSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = SavingsGoal
        fields = ['id', 'user', 'goal_name', 'target_amount', 'current_amount', 'start_date', 'end_date']

    def validate_target_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("The target amount must be greater than zero.")
        return value
