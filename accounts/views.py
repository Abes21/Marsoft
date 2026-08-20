from audit.services import log_action
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

# Create your views here.


from .decorators import admin_required
from .models import User
from .forms import AdminUserCreateForm, AdminUserEditForm


@admin_required
def user_list(request):
    """Lista kont - tylko administrator (RF-06)."""

    users = User.objects.order_by("username")
    return render(request, "accounts/users_list.html", {"users": users})


@admin_required
def user_create(request):
    """Dodanie konta - tylko administrator (RF-06)."""

    form = AdminUserCreateForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        user = form.save()
        # wpis do rejestru działań tworzy sygnał on_user_created
        messages.success(request, f"Utworzono konto {user.username}.")
        return redirect("users")

    return render(
        request,
        "accounts/user_form.html",
        {"form": form, "title": "Dodaj użytkownika"},
    )


@admin_required
def user_update(request, pk):
    """Edycja danych i roli konta - tylko administrator (RF-06)."""

    user = get_object_or_404(User, pk=pk)
    form = AdminUserEditForm(request.POST or None, instance=user)

    if request.method == "POST" and form.is_valid():
        form.save()
        log_action("user_updated", f"Zmieniono dane konta „{user.username}”")
        messages.success(request, "Zapisano zmiany.")
        return redirect("users")

    return render(
        request,
        "accounts/user_form.html",
        {"form": form, "title": f"Edycja: {user.username}"},
    )


@admin_required
def user_toggle_active(request, pk):
    """Blokada / odblokowanie konta - tylko administrator (RF-06)."""

    if request.method != "POST":
        return redirect("users")

    target = get_object_or_404(User, pk=pk)

    if target == request.user:
        messages.error(request, "Nie możesz zablokować własnego konta.")
        return redirect("users")

    target.is_active = not target.is_active
    target.save(update_fields=["is_active"])

    stan = "Zablokowano" if not target.is_active else "Odblokowano"
    log_action("user_updated", f"{stan} konto „{target.username}”")
    messages.success(request, f"{stan} konto {target.username}.")
    return redirect("users")


from django.contrib.auth.forms import AdminPasswordChangeForm


@admin_required
def user_set_password(request, pk):
    """Administrator ustawia nowe hasło użytkownika (reset bez e-maila)."""

    user = get_object_or_404(User, pk=pk)
    form = AdminPasswordChangeForm(user, request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        log_action("user_updated", f"Zresetowano hasło konta „{user.username}”")
        messages.success(request, f"Hasło dla {user.username} zostało ustawione.")
        return redirect("users")

    return render(
        request,
        "accounts/user_password.html",
        {"form": form, "target": user},
    )
