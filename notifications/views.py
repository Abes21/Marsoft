from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .models import Notification


@login_required
def notification_list(request):
    """Lista powiadomień użytkownika."""
    
    notifications = Notification.objects.filter(user=request.user).select_related("alert")
    
    context = {
        "notifications": notifications,
        "unread_count": notifications.filter(is_read=False).count(),
    }
    return render(request, "notifications/list.html", context)


@login_required
@require_POST
def mark_as_read(request, pk):
    """Oznacza powiadomienie jako przeczytane (RF-73)."""
    
    notification = Notification.objects.filter(
        pk=pk,
        user=request.user,
    ).first()
    
    if notification:
        notification.is_read = True
        notification.save()
    
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"status": "ok"})
    
    return redirect("notification_list")


@login_required
@require_POST
def mark_all_as_read(request):
    """Oznacza wszystkie powiadomienia jako przeczytane."""
    
    Notification.objects.filter(
        user=request.user,
        is_read=False,
    ).update(is_read=True)
    
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"status": "ok"})
    
    return redirect("notification_list")
