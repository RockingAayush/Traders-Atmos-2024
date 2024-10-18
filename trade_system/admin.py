from django.contrib import admin
from .models import Player, News, Stock, Transaction, SiteSetting, Leaderboard
from django.contrib import messages
from django.utils.translation import gettext_lazy as _

# Register your models here.
admin.site.register(Player)
admin.site.register(News)
admin.site.register(Stock)
admin.site.register(Transaction)

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