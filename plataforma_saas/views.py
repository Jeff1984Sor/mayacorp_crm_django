from core import views as views_core
from crm import views as views_crm

from plataforma_saas.tenant import obter_tipo_tenant


def login_dispatch(request):
    if obter_tipo_tenant() == "empresa":
        return views_crm.login(request)
    return views_core.login(request)


def logout_dispatch(request):
    if obter_tipo_tenant() == "empresa":
        return views_crm.logout(request)
    return views_core.logout(request)
