from functools import wraps

from django.shortcuts import redirect

from plataforma_saas.tenant import obter_tipo_tenant


def login_empresa_obrigatorio(view_func):
    @wraps(view_func)
    def interno(request, *args, **kwargs):
        if obter_tipo_tenant() != "empresa" or not getattr(request, "usuario_empresa", None):
            return redirect("crm_login")
        return view_func(request, *args, **kwargs)

    return interno
