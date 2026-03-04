from django.db import connections
from django.utils.deprecation import MiddlewareMixin

from core.models import Empresa, UsuarioAdmin
from crm.models import UsuarioEmpresa
from plataforma_saas.provisionamento import provisionar_tenant
from plataforma_saas.tenant import definir_tenant


class MiddlewareTenant(MiddlewareMixin):
    def process_request(self, request):
        host = request.get_host().split(":")[0]
        subdominio = host.split(".")[0] if "." in host else "admin"
        if subdominio == "admin":
            definir_tenant(None, "default", "central")
            self._vincular_usuario_admin(request)
            return

        empresa = Empresa.objects.filter(slug=subdominio, ativo=True).first()
        if not empresa:
            definir_tenant(None, "default", "central")
            return

        alias = provisionar_tenant(empresa)
        definir_tenant(empresa.slug, alias, "empresa")
        request.empresa_atual = empresa
        self._vincular_usuario_empresa(request)

    def _vincular_usuario_admin(self, request):
        request.usuario_admin = None
        usuario_id = request.session.get("usuario_admin_id")
        if usuario_id:
            request.usuario_admin = UsuarioAdmin.objects.filter(id=usuario_id, ativo=True).first()

    def _vincular_usuario_empresa(self, request):
        request.usuario_empresa = None
        usuario_id = request.session.get("usuario_empresa_id")
        if usuario_id:
            alias = connections.databases and request.empresa_atual and f"tenant_{request.empresa_atual.slug}"
            if alias:
                request.usuario_empresa = UsuarioEmpresa.objects.using(alias).filter(id=usuario_id, ativo=True).first()
