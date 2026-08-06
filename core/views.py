from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def dashboard(request):
    return render(request, 'core/dashboard.html')


@login_required
def devices(request):
    return render(request, 'core/devices.html')


@login_required
def logs_list(request):
    return render(request, 'core/logs.html')


@login_required
def alerts(request):
    return render(request, 'core/alerts.html')


@login_required
def rules(request):
    return render(request, 'core/rules.html')


@login_required
def settings_view(request):
    return render(request, 'core/settings.html')
