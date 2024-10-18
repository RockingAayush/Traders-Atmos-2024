from django.shortcuts import redirect
from django.urls import reverse
from .models import SiteSetting
from django.contrib.auth import logout

class MaintenanceModeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        login_url = reverse('login')
        admin_url = reverse('admin:index')
        maintenance_url = reverse('maintenance_page')

        try:
            site_setting = SiteSetting.objects.first()

            if site_setting and site_setting.maintenance_mode:
                if request.path.startswith(admin_url) or request.path == login_url:
                    return self.get_response(request)

                if request.user.is_superuser:
                    return self.get_response(request)

                if request.user.is_authenticated:
                    logout(request)
                    return redirect(login_url)

                if request.path != maintenance_url:
                    return redirect(maintenance_url)

            else:
                # Redirect users on the maintenance page to login if maintenance is disabled
                if request.path == maintenance_url:
                    return redirect(login_url)

        except SiteSetting.DoesNotExist:
            pass

        return self.get_response(request)
