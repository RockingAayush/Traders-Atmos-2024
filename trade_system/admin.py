from django.contrib import admin
from .models import Player, News, Stock, Transaction, SiteSetting, Leaderboard, AllowedEmail
from django.contrib import messages
from django.utils.translation import gettext_lazy as _

# Register your models here.
admin.site.register(Player)
admin.site.register(News)
admin.site.register(Stock)

admin.site.register(AllowedEmail)

@admin.register(SiteSetting)
class SiteSettingAdmin(admin.ModelAdmin):
    list_display = ('maintenance_mode',)

    def changelist_view(self, request, extra_context=None):
        site_setting = SiteSetting.objects.first()
        if site_setting and site_setting.maintenance_mode:
            messages.warning(request, _("The site is currently in maintenance mode."))
        return super().changelist_view(request, extra_context)
    

@admin.register(Leaderboard)
class LeaderboardAdmin(admin.ModelAdmin):
    list_display = ['player', 'net_worth', 'added_on']
    search_fields = ['player__user__username']



class UserCodeFilter(admin.SimpleListFilter):
    title = 'User Code'
    parameter_name = 'user_code'

    def lookups(self, request, model_admin):
        # Get unique user codes for the filter dropdown in admin
        user_codes = Player.objects.values_list('user_code', flat=True).distinct()
        return [(user_code, user_code) for user_code in user_codes]

    def queryset(self, request, queryset):
        # Filter transactions by user code
        if self.value():
            # Find the player with the entered user code
            try:
                player = Player.objects.get(user_code=self.value())
                # Filter transactions where the player is either sender or receiver
                return queryset.filter(sender=player) | queryset.filter(receiver=player)
            except Player.DoesNotExist:
                return queryset.none()
        return queryset

class TransactionAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver', 'stock', 'price', 'quantity', 'action', 'status', 'timestamp')
    list_filter = (UserCodeFilter,)

admin.site.register(Transaction,TransactionAdmin)    
