from .models import Leaderboard

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

