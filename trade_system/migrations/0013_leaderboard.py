# Generated by Django 5.1.2 on 2024-10-17 14:22

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trade_system', '0012_alter_sitesetting_options'),
    ]

    operations = [
        migrations.CreateModel(
            name='Leaderboard',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('net_worth', models.DecimalField(decimal_places=2, max_digits=12)),
                ('added_on', models.DateTimeField(default=django.utils.timezone.now)),
                ('player', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='trade_system.player')),
            ],
        ),
    ]
