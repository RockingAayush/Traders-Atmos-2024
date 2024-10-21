from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Player,News,Stock,Transaction,SiteSetting,Leaderboard,AllowedEmail
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q
from decimal import Decimal
from django.urls import reverse
from django.http import JsonResponse
from django.contrib.auth import logout
from allauth.account.signals import user_logged_in
from django.dispatch import receiver

MINIMUM_TRANSACTIONS = 12

# Login page
def login(request):
    return render(request, 'login.html')

# Dashboard
@login_required(login_url='/login/')
def dashboard(request):
    try:
        # Get the AllowedEmail entry that matches the current user's email
        allowed_email = AllowedEmail.objects.get(email=request.user.email)
        
        # Fetch the corresponding Player based on the allowed_email
        player = Player.objects.get(user=allowed_email)
    except AllowedEmail.DoesNotExist:
        # If the user's email is not in the AllowedEmail list, redirect or show an error
        return render(request, 'email_not_allowed.html')
    
    stocks = Stock.objects.all()  # Fetch all stocks from the Stock model
    recipients = Player.objects.exclude(user=allowed_email)
    print(recipients)
    if (MINIMUM_TRANSACTIONS - player.number_of_orders) < 0:
        minimum_remaining_orders = 0
    else:
        minimum_remaining_orders = MINIMUM_TRANSACTIONS - player.number_of_orders   
    
    context = {
        'player': player,
        'recipients': recipients,
        'balance': player.balance,
        'number_of_orders': player.number_of_orders,
        'minimum_remaining_orders': minimum_remaining_orders,
        'stocks': stocks,  # Pass the list of stocks to the template
        'user_code': player.user_code,           
    }
    return render(request, 'dashboard.html', context)

# News
@login_required(login_url='/login/')
def news_page(request):
    # Get the allowed email from the user
    allowed_email = AllowedEmail.objects.get(email=request.user.email)
    # Retrieve the Player instance using the allowed email
    player = Player.objects.get(user=allowed_email)
    # Fetch all news ordered by time
    news = News.objects.all().order_by('-time')
    context = {
        'news': news,
        'user_code': player.user_code,
    }  
    return render(request, 'news.html', context)


# Display pending requests page
@login_required(login_url='/login/')
def pending_requests(request):
    """View to show all pending requests for the logged-in receiver."""
    # Get the allowed email from the user
    allowed_email = AllowedEmail.objects.get(email=request.user.email)
    # Retrieve the Player instance using the allowed email
    player = get_object_or_404(Player, user=allowed_email)
    
    # Fetch the pending transactions for the logged-in user
    pending_transactions = Transaction.objects.filter(receiver=player, status='PENDING')

    return render(request, 'pending_requests.html', {
        'user_code': player.user_code,
        'pending_transactions': pending_transactions
    })


# Transaction sending mechanism and form validation
@login_required(login_url='/login/')
def transaction_request(request, stock_id):
    if request.method == 'POST':
        # Sender is the logged-in user (use `user_code` from the related `Player` model)
        allowed_email = AllowedEmail.objects.get(email=request.user.email)
        sender = Player.objects.get(user=allowed_email)
        sender_code = sender.user_code  # Get the `user_code` of the sender

        # Get the recipient (receiver) based on the `user_code` from the form input
        recipient_code = request.POST.get('recipient')
        
        # Check if user is requesting himself
        if sender_code == recipient_code:
            messages.error(request,"Invalid Recipient Code")
            return redirect('dashboard')
        
        try:
            recipient = Player.objects.get(user_code=recipient_code)
        except Player.DoesNotExist:
            messages.error(request, "Recipient does not exist.")
            return redirect('dashboard')  # Adjust this redirect to your actual view

        # Get the action (either 'BUY' or 'SELL')
        action = request.POST.get(f'action-{stock_id}').upper()  # Correctly handle 'BUY' or 'SELL'

        # Get quantity and price from the form
        quantity = int(request.POST.get('quantity'))
        price = float(request.POST.get('price'))

        if quantity < 0:
            messages.error(request,"Quantity cannot be negative.")
            return redirect('dashboard')
        
        # Fetch the stock being traded
        stock = get_object_or_404(Stock, id=stock_id)

        # Validate that the price is within the upper and lower cap for the stock
        if price < 0:
            messages.error(request,"Price cannot be negative.")
            return redirect('dashboard')
        
        if not (stock.lower_cap <= price <= stock.upper_cap):
            messages.error(request, f"Price must be between {stock.lower_cap} and {stock.upper_cap}.")
            return redirect('dashboard')

        # Validate sender's balance (if buying) or stock quantity (if selling)
        if action == 'BUY':
            total_cost = price * quantity
            if sender.balance < total_cost:
                messages.error(request, "You do not have enough balance to buy.")
                return redirect('dashboard')
        elif action == 'SELL':
            sender_stock_qty = getattr(sender, f'stock{stock.id}')  # Assuming stocks are stored in fields like 'stock1', 'stock2', etc.
            if sender_stock_qty < quantity:
                messages.error(request, "You do not have enough quantity of this stock to sell.")
                return redirect('dashboard')

        # Create a pending transaction request (use 'PENDING' as the default status)
        transaction = Transaction.objects.create(
            sender=sender,
            receiver=recipient,
            stock=stock,
            price=price,
            quantity=quantity,
            action=action,
            status='PENDING',
            timestamp=timezone.now()  # Current time for when the transaction request is created
        )

        # Save the transaction request
        transaction.save()

        messages.success(request, "Transaction request sent successfully.")
        return redirect('dashboard')

# Accepting a request
@login_required(login_url='/login/')
def accept_transaction(request, transaction_id):
    # Ensure the logged-in user's email is allowed
    try:
        allowed_email = AllowedEmail.objects.get(email=request.user.email)
    except AllowedEmail.DoesNotExist:
        messages.error(request, "Your email is not authorized to perform transactions.")
        return redirect('pending_requests')

    # Ensure the player associated with the allowed email exists
    try:
        receiver = Player.objects.get(user=allowed_email)
    except Player.DoesNotExist:
        messages.error(request, "Player associated with your email does not exist.")
        return redirect('pending_requests')

    # Get the transaction and verify the receiver is the correct one
    transaction = get_object_or_404(Transaction, id=transaction_id, receiver=receiver)

    # Check if the transaction is still pending
    if transaction.status != 'PENDING':
        messages.error(request, "Transaction is no longer pending.")
        return redirect('pending_requests')

    # Extract transaction details
    sender = transaction.sender
    stock = transaction.stock
    action = transaction.action
    quantity = transaction.quantity
    price = transaction.price

    print(sender)
    # Final validation - Check if sender and receiver meet the transaction requirements
    if action == 'BUY':
        total_cost = price * quantity
        # Check if the sender (BUYER) has enough balance
        if sender.balance < total_cost:
            messages.error(request, "Invalid transaction: sender does not have enough balance.")
            transaction.delete()  # Delete invalid transaction
            return redirect('pending_requests')

        # Check if the receiver (SELLER) has enough stock to sell
        receiver_stock_qty = getattr(receiver, f'stock{stock.id}', 0)
        if receiver_stock_qty < quantity:
            messages.error(request, "Invalid transaction: receiver does not have enough quantity of the stock to sell.")
            transaction.delete()  # Delete invalid transaction
            return redirect('pending_requests')

    elif action == 'SELL':
        # Check if the sender (SELLER) has enough stock to sell
        sender_stock_qty = getattr(sender, f'stock{stock.id}', 0)
        if sender_stock_qty < quantity:
            messages.error(request, "Invalid transaction: sender does not have enough quantity of the stock to sell.")
            transaction.delete()  # Delete invalid transaction
            return redirect('pending_requests')

        # Check if the receiver (BUYER) has enough balance to buy
        total_cost = price * quantity
        if receiver.balance < total_cost:
            messages.error(request, "Invalid transaction: receiver does not have enough balance.")
            transaction.delete()  # Delete invalid transaction
            return redirect('pending_requests')

    # If all validations pass, update the transaction status to ACCEPTED
    transaction.status = 'ACCEPTED'
    transaction.accepted_at = timezone.now()
    transaction.save()

    # Update the number of orders for both the sender and receiver
    sender.number_of_orders += 1
    receiver.number_of_orders += 1

    # Save the updated player models
    sender.save()
    receiver.save()

    # Update the balances and stock quantities for both the sender and receiver
    update_balances_and_stocks(transaction)

    messages.success(request, "Transaction accepted.")
    return redirect('pending_requests')

# Rejecting a request
@login_required(login_url='/login/')
def reject_transaction(request, transaction_id):
    """Reject and delete the transaction."""
    allowed_email = get_object_or_404(AllowedEmail, email=request.user.email)
    receiver = get_object_or_404(Player, user=allowed_email)
    transaction = get_object_or_404(Transaction, id=transaction_id, receiver=receiver)

    if transaction.status == 'PENDING':
        transaction.delete()
        messages.success(request, 'Transaction request rejected.')

    return redirect('pending_requests')

# Function to update balances and stock quantities after acceptance
def update_balances_and_stocks(transaction):
    sender = transaction.sender
    receiver = transaction.receiver
    stock = transaction.stock
    quantity = transaction.quantity
    price = transaction.price
    total_cost = price * quantity

    if transaction.action == 'BUY':
        # Deduct the total cost from the sender's balance
        sender.balance -= total_cost
        sender.save()

        # Increase the stock quantity for the sender
        sender_stock_qty = getattr(sender, f'stock{stock.id}', 0)
        setattr(sender, f'stock{stock.id}', sender_stock_qty + quantity)
        sender.save()

        # Reduce the stock quantity for the receiver
        receiver_stock_qty = getattr(receiver, f'stock{stock.id}', 0)
        setattr(receiver, f'stock{stock.id}', receiver_stock_qty - quantity)
        receiver.save()

        # Add the total cost to the receiver's balance
        receiver.balance += total_cost
        receiver.save()

    elif transaction.action == 'SELL':
        # Deduct the stock quantity from the sender
        sender_stock_qty = getattr(sender, f'stock{stock.id}', 0)
        setattr(sender, f'stock{stock.id}', sender_stock_qty - quantity)
        sender.save()

        # Add the total cost to the sender's balance
        sender.balance += total_cost
        sender.save()

        # Increase the stock quantity for the receiver
        receiver_stock_qty = getattr(receiver, f'stock{stock.id}', 0)
        setattr(receiver, f'stock{stock.id}', receiver_stock_qty + quantity)
        receiver.save()

        # Deduct the total cost from the receiver's balance
        receiver.balance -= total_cost
        receiver.save()

# Transaction History view
@login_required(login_url='/login/')
def transaction_history(request):
    """Show transaction history for the logged-in user."""
    allowed_email = AllowedEmail.objects.get(email=request.user.email)
    player = Player.objects.get(user=allowed_email)
    
    # Fetch all transactions where the user is the sender or receiver
    transactions = Transaction.objects.filter(
        (Q(sender=player) | Q(receiver=player))
    ).order_by('-accepted_at')
    
    context = {
        'transactions': transactions,
        'player': player,
    }
    return render(request, 'transaction_history.html', context)        

# Portfolio
@login_required(login_url='/login/')
def portfolio(request):
    allowed_email = AllowedEmail.objects.get(email=request.user.email)    
    # Fetch the corresponding Player based on the allowed_email
    user = Player.objects.get(user=allowed_email)

    # List of stocks (assuming you have a Stock model with these stocks)
    stocks = Stock.objects.filter(id__in=range(1, 9))  # Fetch stocks with ids 1 to 8

    stocks_held = []
    player_stock_quantities = [
        user.stock1, user.stock2, user.stock3, user.stock4,
        user.stock5, user.stock6, user.stock7, user.stock8
    ]

    overall_total_value = Decimal(0)

    for i, stock in enumerate(stocks):
        total_quantity = player_stock_quantities[i]
        current_price = Decimal(stock.price)
        total_value = current_price * total_quantity
        overall_total_value += total_value

        stocks_held.append({
            'stock_name': stock.stock_name,
            'total_quantity': total_quantity,
            'current_price': current_price,
            'total_value': total_value,
        })

    stocks_held = [stock for stock in stocks_held if stock['total_quantity'] > 0]
    net_worth = user.balance + overall_total_value

    # If the request is an AJAX request (for polling)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'net_worth': float(net_worth),
            'balance': float(user.balance),
            'stocks_held': [
                {
                    'stock_name': stock['stock_name'],
                    'total_quantity': stock['total_quantity'],
                    'current_price': float(stock['current_price']),
                    'total_value': float(stock['total_value']),
                } for stock in stocks_held
            ]
        })

    # If it's a normal request, render the HTML template
    context = {
        'player': user,
        'stocks_held': stocks_held,
        'overall_total_value': overall_total_value,
        'net_worth': net_worth,
    }
    return render(request, 'portfolio.html', context)

# Portfolio data fetcher
@login_required(login_url='/login/')
def portfolio_data(request):
    allowed_email = AllowedEmail.objects.get(email=request.user.email)    
    # Fetch the corresponding Player based on the allowed_email
    user = Player.objects.get(user=allowed_email)
    
    stocks = Stock.objects.filter(id__in=range(1, 9))  # Assuming Stock model has these stocks

    stocks_held = []
    player_stock_quantities = [
        user.stock1, user.stock2, user.stock3, user.stock4,
        user.stock5, user.stock6, user.stock7, user.stock8
    ]

    overall_total_value = Decimal(0)

    for i, stock in enumerate(stocks):
        total_quantity = player_stock_quantities[i]
        current_price = Decimal(stock.price)
        total_value = current_price * total_quantity
        overall_total_value += total_value

        stocks_held.append({
            'stock_name': stock.stock_name,
            'total_quantity': total_quantity,
            'current_price': float(current_price),
            'total_value': float(total_value),
        })

    stocks_held = [stock for stock in stocks_held if stock['total_quantity'] > 0]

    net_worth = user.balance + overall_total_value

    data = {
        'net_worth': float(net_worth),
        'overall_total_value': float(overall_total_value),
        'balance': float(user.balance),
        'stocks_held': stocks_held
    }

    return JsonResponse(data)

# Maintenance
def maintenance_page(request):
    # Get the current site setting for maintenance mode
    try:
        site_setting = SiteSetting.objects.first()
        # If maintenance mode is disabled, redirect to the login page
        if not site_setting.maintenance_mode:
            return redirect(reverse('login'))  # Adjust this to your actual login URL

    except SiteSetting.DoesNotExist:
        # If the setting doesn't exist, proceed as if maintenance mode is off
        return redirect(reverse('login'))

    # Render the maintenance page if maintenance mode is still on
    return render(request, 'maintenance.html')

# Leaderboard
def leaderboard_view(request):
    leaderboard = Leaderboard.objects.all().order_by('-net_worth')  # Sort by net worth
    return render(request, 'leaderboard.html', {'leaderboard': leaderboard})

# Allowed emails
@receiver(user_logged_in)
def check_allowed_email(sender, request, user, **kwargs):
    # Check if the user's email is in the allowed list
    if not AllowedEmail.objects.filter(email=user.email).exists():
        # Log out the user if their email is not in the allowed list
        logout(request)
        # Redirect them to an error page or show a message
        return redirect(reverse('email_not_allowed'))
#from django.views.decorators.http import require_http_methods

def email_not_allowed(request):
    return render(request, 'email_not_allowed.html', {'message': 'Your email address is not allowed.'})
#@require_http_methods(['GET'])
#def check_pending_requests(request):
#    player = request.user.player
#    pending_requests = Transaction.objects.filter(receiver=player, status='PENDING').exists()
#    return JsonResponse({'pending_requests': pending_requests})
