# Generated by Django 5.1.2 on 2024-10-13 10:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trade_system', '0002_remove_player_stock10_remove_player_stock11_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='player',
            name='user_code',
            field=models.CharField(blank=True, max_length=10, unique=True),
        ),
    ]
