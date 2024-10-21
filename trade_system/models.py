from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.contrib.sessions.models import Session

import random , string
from decimal import Decimal

UPPER_LOWER_CAP_PERCENTAGE = 0.2

# Allowed Users Table
class AllowedEmail(models.Model):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=100)  # Add a name field to store the user's name

    def __str__(self):
        return self.email

# Table with Player Info
class Player(models.Model):
    user = models.OneToOneField(AllowedEmail, on_delete=models.CASCADE)  # Link to the User model
    balance = models.DecimalField(default=20000, max_digits=10, decimal_places=2)
    number_of_orders = models.PositiveIntegerField(default=0)
    stock1 = models.PositiveIntegerField(default=0)
    stock2 = models.PositiveIntegerField(default=0)
    stock3 = models.PositiveIntegerField(default=0)
    stock4 = models.PositiveIntegerField(default=0)
    stock5 = models.PositiveIntegerField(default=0)
    stock6 = models.PositiveIntegerField(default=0)
    stock7 = models.PositiveIntegerField(default=0)
    stock8 = models.PositiveIntegerField(default=0)
    user_code = models.CharField(max_length=10, unique=True, blank=True)

    def __str__(self):
        return self.user_code
    
    def calculate_net_worth(self):
        # Calculate total value of stocks held by player
        total_stock_value = (
            self.stock1 * Stock.objects.get(id=1).price +
            self.stock2 * Stock.objects.get(id=2).price +
            self.stock3 * Stock.objects.get(id=3).price +
            self.stock4 * Stock.objects.get(id=4).price +
            self.stock5 * Stock.objects.get(id=5).price +
            self.stock6 * Stock.objects.get(id=6).price +
            self.stock7 * Stock.objects.get(id=7).price +
            self.stock8 * Stock.objects.get(id=8).price
        )
        # Net worth is balance + stock value
        return self.balance + total_stock_value

# News that we will release
class News(models.Model):
    title = models.CharField(max_length=100, default="Title here")
    news_text = models.TextField()
    time = models.DateTimeField(auto_now_add=True) 

    def __str__(self):
        return self.title

# Stock list
class Stock(models.Model):
    stock_name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    upper_cap = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    lower_cap = models.DecimalField(max_digits=10, decimal_places=2, editable=False)

    def save(self, *args, **kwargs):
        # Automatically set the upper and lower caps as ± 20% of the price
        self.upper_cap = self.price * Decimal(1 + UPPER_LOWER_CAP_PERCENTAGE)
        self.lower_cap = self.price * Decimal(1 - UPPER_LOWER_CAP_PERCENTAGE)
        super(Stock, self).save(*args, **kwargs)

    def __str__(self):
        return self.stock_name


# Transaction list 
class Transaction(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('ACCEPTED', 'Accepted')
    ]

    sender = models.ForeignKey('Player', related_name='transactions_sent', on_delete=models.CASCADE)
    receiver = models.ForeignKey('Player', related_name='transactions_received', on_delete=models.CASCADE)
    stock = models.ForeignKey('Stock', on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()
    action = models.CharField(max_length=4, choices=[('BUY', 'BUY'), ('SELL', 'SELL')])
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    timestamp = models.DateTimeField(default=timezone.now)
    accepted_at = models.DateTimeField(null=True, blank=True) 

    def __str__(self):
        return f"{self.sender.user_code} {self.action} {self.quantity} of {self.stock.stock_name} at {self.price} to {self.receiver.user_code} - {self.status}"


# Maintenance
class SiteSetting(models.Model):
    maintenance_mode = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        # If maintenance mode is being enabled
        if self.maintenance_mode:
            # Invalidate all active sessions (log out all users)
            Session.objects.all().delete()

        super(SiteSetting, self).save(*args, **kwargs)


# Leaderboard
class Leaderboard(models.Model):
    player = models.OneToOneField(Player, on_delete=models.CASCADE)
    net_worth = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    added_on = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.player.user_code} - {self.net_worth}"
    

def generate_user_code(first_name):
    initials = ''.join([name[0] for name in first_name.split() if name]).upper()
    
    while True:
        # Generate a random 4-digit number
        random_number = ''.join(random.choices(string.digits, k=4))
        user_code = initials + random_number

        # Check if this user_code already exists
        if not Player.objects.filter(user_code=user_code).exists():
            return user_code

#@receiver(post_save, sender=User)
#def create_player(sender, instance, created, **kwargs):
#    if created:
#        first_name = instance.first_name
#        user_code = generate_user_code(first_name)
#        Player.objects.create(user=instance, user_code=user_code)


@receiver(post_save, sender=Player)
def check_leaderboard(sender, instance, **kwargs):
    
    # If the player's number of orders is 12 or more and they are not already in the leaderboard
    if instance.number_of_orders >= 12:
        # Calculate the player's net worth
        net_worth = instance.calculate_net_worth()
        
        # Get or create a leaderboard entry
        leaderboard_entry, created = Leaderboard.objects.get_or_create(player=instance)
        
        # Update the net worth in the leaderboard entry
        leaderboard_entry.net_worth = net_worth
        leaderboard_entry.save()

@receiver(post_save, sender=Stock)
def update_leaderboard_on_stock_change(sender, instance, **kwargs):
    # Fetch all players to recalculate their net worth
    players = Player.objects.all()
    
    # Loop through each player and update their net worth
    for player in players:
        update_leaderboard_for_player(player)        

def update_leaderboard_for_player(player):
    """
    Update the leaderboard for the given player if they meet the criteria.
    """
    if player.number_of_orders >= 12:
        # Calculate the player's net worth
        net_worth = player.calculate_net_worth()

        # Get or create a leaderboard entry
        leaderboard_entry, created = Leaderboard.objects.get_or_create(player=player)

        # Update the net worth in the leaderboard entry
        leaderboard_entry.net_worth = net_worth
        leaderboard_entry.save()
