from functools import wraps

from django.shortcuts import redirect


def login_admin_obrigatorio(view_func):
    @wraps(view_func)
    def interno(request, *args, **kwargs):
        if not getattr(request, "usuario_admin", None):
            return redirect("core_login")
        return view_func(request, *args, **kwargs)

    return interno
