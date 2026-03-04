from unittest.mock import patch

from django.test import Client, RequestFactory, TestCase

from core.models import Empresa, Plano, Profissional, RegistroAuditoria, UsuarioAdmin
from crm.models import UsuarioEmpresa
from plataforma_saas.middleware import MiddlewareTenant
from plataforma_saas.tenant import definir_tenant
from plataforma_saas.tenant import obter_alias_banco, obter_tipo_tenant


class AutenticacaoModelosTestes(TestCase):
    def test_usuario_admin_valida_senha_com_hash(self):
        usuario = UsuarioAdmin(nome="Admin", email="admin@local", perfil=UsuarioAdmin.Perfil.SUPERADMIN)
        usuario.definir_senha("admin123")
        self.assertTrue(usuario.validar_senha("admin123"))
        self.assertFalse(usuario.validar_senha("errada"))

    def test_usuario_empresa_valida_senha_com_hash(self):
        usuario = UsuarioEmpresa(nome="Dono", email="dono@empresa", perfil=UsuarioEmpresa.Perfil.ADMIN)
        usuario.definir_senha("empresa123")
        self.assertTrue(usuario.validar_senha("empresa123"))
        self.assertFalse(usuario.validar_senha("outra"))


class TenantMiddlewareTestes(TestCase):
    def tearDown(self):
        definir_tenant(None, "default", "central")

    def test_subdominio_admin_mantem_contexto_central(self):
        request = RequestFactory().get("/", HTTP_HOST="admin.localhost")
        request.session = {}
        MiddlewareTenant(lambda req: None).process_request(request)
        self.assertEqual(obter_tipo_tenant(), "central")
        self.assertEqual(obter_alias_banco(), "default")

    @patch("plataforma_saas.middleware.provisionar_tenant", return_value="tenant_empresa")
    def test_subdominio_empresa_define_alias_do_tenant(self, provisionar_mock):
        plano = Plano.objects.create(
            nome="Base",
            descricao="Plano base",
            preco=10,
            ciclo_cobranca=Plano.CicloCobranca.MENSAL,
            limite_usuarios=5,
            limite_registros=100,
        )
        Empresa.objects.create(nome="Empresa", slug="empresa", email="empresa@local", plano=plano)
        request = RequestFactory().get("/", HTTP_HOST="empresa.localhost")
        request.session = {}
        MiddlewareTenant(lambda req: None).process_request(request)
        self.assertEqual(obter_tipo_tenant(), "empresa")
        self.assertEqual(obter_alias_banco(), "tenant_empresa")
        provisionar_mock.assert_called_once()


class CrudEFluxoHtmxTestes(TestCase):
    def setUp(self):
        self.usuario = UsuarioAdmin.objects.create(nome="Admin", email="admin@local", perfil=UsuarioAdmin.Perfil.SUPERADMIN, senha="x")
        self.client = Client(HTTP_HOST="admin.localhost")
        sessao = self.client.session
        sessao["usuario_admin_id"] = self.usuario.id
        sessao.save()
        self.plano = Plano.objects.create(
            nome="Plano Teste",
            descricao="Base",
            preco=10,
            ciclo_cobranca=Plano.CicloCobranca.MENSAL,
            limite_usuarios=5,
            limite_registros=100,
        )
        self.profissional = Profissional.objects.create(
            nome_completo="Profissional Teste",
            email="prof@local",
            cargo=Profissional.Cargo.SUPORTE,
        )

    def test_listagem_profissionais_carrega(self):
        resposta = self.client.get("/admin/profissionais")
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "Profissional Teste")

    def test_listagem_profissionais_htmx_retorna_partial(self):
        resposta = self.client.get("/admin/profissionais", HTTP_HX_REQUEST="true")
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'id="lista-conteudo"')

    def test_detalhe_com_aba_htmx_retorna_partial(self):
        resposta = self.client.get(f"/admin/profissionais/{self.profissional.pk}?aba=auditoria", HTTP_HX_REQUEST="true")
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'id="detalhe-conteudo"')

    def test_auditoria_exporta_csv(self):
        RegistroAuditoria.objects.create(usuario_admin=self.usuario, acao=RegistroAuditoria.Acao.LOGIN, entidade="UsuarioAdmin", ip="127.0.0.1")
        resposta = self.client.get("/admin/auditoria?exportar=csv")
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta["Content-Type"], "text/csv")
        self.assertIn("attachment; filename=\"auditoria_central.csv\"", resposta["Content-Disposition"])
