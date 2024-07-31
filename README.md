bx_api is a Django Rest Framework (DRF) API designed to manage financial data. It supports operations for user profiles, transactions, investments, budgets, expenses, and savings goals. The API also includes endpoints for financial advice, balance checks, and statements. The project uses MySQL for its database and Twilio for SMS notifications.

Features
User Profiles: Manage user settings, notification preferences, and low balance thresholds.
Notifications: Send notifications via email and SMS.
Transactions: Track and manage deposits, withdrawals, transfers, and payments.
Investments: Record and manage user investments.
Budgets: Create and monitor budgets across various categories.
Expenses: Track and log user expenses.
Savings Goals: Set and track progress towards savings goals.
Financial Advice: Get financial advice based on user data.
Balance: Check account balances and receive alerts for low balances.
Statement: Retrieve financial statements.

To set up and run the bx_api project locally, follow these steps:

Clone the Repository https://github.com/Bax-dev/bx_api.git
Install the Required Packages: pip install -r requirements.txt
Configure MySQL Database

Update your settings.py with MySQL database configuration.

Configure Twilio :Set up your Twilio credentials in settings.py.
