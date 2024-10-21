"""
URL configuration for pit_trading project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path, include
from trade_system import views
from django.contrib import admin
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),

    # URL for the login page with Google button
    path('login/', views.login , name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # URL for the dashboard page after login
    path('dashboard/',views.dashboard, name='dashboard'),

    # URL for the news page
    path('news/',views.news_page, name='news'),

    # URL for transactions handeling
    path('transaction-request/<int:stock_id>/', views.transaction_request, name='transaction_request'),
    path('pending-requests/', views.pending_requests, name='pending_requests'),
    path('accept-transaction/<int:transaction_id>/', views.accept_transaction, name='accept_transaction'),
    path('reject-transaction/<int:transaction_id>/', views.reject_transaction, name='reject_transaction'),

    # URL for transactions history
    path('transaction-history/', views.transaction_history, name='transaction_history'),

    # URL for portfolio
    path('portfolio/', views.portfolio, name='portfolio'),
    path('portfolio_data/', views.portfolio_data, name='portfolio_data'),

    # URL for maintenance page
    path('maintenance/', views.maintenance_page, name='maintenance_page'),

    # URL to check allowed users
    path('email-not-allowed/', views.email_not_allowed, name='email_not_allowed'),
]
