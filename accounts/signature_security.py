from django.contrib.auth import authenticate


def verify_signature_reauthentication(request):
    """Verify the signed-in user's password for a critical approval action."""
    password = (request.POST.get('signature_password') or '').strip()
    if not password or not getattr(request.user, 'is_authenticated', False):
        return False
    user = authenticate(
        request,
        username=request.user.get_username(),
        password=password,
    )
    return bool(user and user.pk == request.user.pk and user.is_active)
