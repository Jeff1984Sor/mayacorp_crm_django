from django.core.management import BaseCommand
from django.utils import timezone

from core.models import Empresa, Plano, UsuarioAdmin
from crm.models import Cliente, ItemVenda, Produto, ProfissionalEmpresa, Servico, UsuarioEmpresa, Venda
from plataforma_saas.provisionamento import provisionar_tenant


class Command(BaseCommand):
    help = "Cria dados iniciais do sistema."

    def handle(self, *args, **options):
        admin = UsuarioAdmin.objects.filter(email="admin@local").first()
        if not admin:
            admin = UsuarioAdmin(nome="Administrador", email="admin@local", perfil=UsuarioAdmin.Perfil.SUPERADMIN)
            admin.definir_senha("admin123")
            admin.save()

        planos = [
            ("Essencial", 99, Plano.CicloCobranca.MENSAL),
            ("Profissional", 249, Plano.CicloCobranca.TRIMESTRAL),
            ("Premium", 799, Plano.CicloCobranca.ANUAL),
        ]
        for nome, preco, ciclo in planos:
            Plano.objects.get_or_create(
                nome=nome,
                defaults={
                    "descricao": f"Plano {nome}",
                    "preco": preco,
                    "ciclo_cobranca": ciclo,
                    "limite_usuarios": 20,
                    "limite_registros": 5000,
                    "recursos_json": {"whatsapp": True, "api": nome != "Essencial", "relatorios": True},
                },
            )

        plano_demo = Plano.objects.order_by("id").first()
        empresa, _ = Empresa.objects.get_or_create(
            slug="empresa",
            defaults={
                "nome": "Empresa Demo",
                "documento": "00.000.000/0001-00",
                "email": "contato@empresa.local",
                "telefone": "(11) 99999-0000",
                "plano": plano_demo,
                "status_assinatura": Empresa.StatusAssinatura.ATIVA,
                "inicio_assinatura": timezone.localdate(),
                "nome_banco": "tenant_empresa.sqlite3",
                "motor_banco": "sqlite",
            },
        )

        alias = provisionar_tenant(empresa)

        usuario_empresa = UsuarioEmpresa.objects.using(alias).filter(email="dono@empresa").first()
        if not usuario_empresa:
            usuario_empresa = UsuarioEmpresa(nome="Dono da Empresa", email="dono@empresa", perfil=UsuarioEmpresa.Perfil.ADMIN)
            usuario_empresa.definir_senha("empresa123")
            usuario_empresa.save(using=alias)

        for indice in range(1, 4):
            ProfissionalEmpresa.objects.using(alias).get_or_create(
                email=f"profissional{indice}@empresa.local",
                defaults={"nome_completo": f"Profissional {indice}", "telefone": f"1199999000{indice}", "funcao": "Consultor"},
            )

        for indice in range(1, 11):
            Cliente.objects.using(alias).get_or_create(
                nome=f"Cliente {indice}",
                defaults={
                    "documento": f"000{indice}",
                    "email": f"cliente{indice}@mail.com",
                    "telefone": f"119888800{indice}",
                    "status": Cliente.Status.CLIENTE,
                },
            )

        for indice in range(1, 6):
            Produto.objects.using(alias).get_or_create(
                sku=f"SKU-{indice}",
                defaults={"nome": f"Produto {indice}", "preco": 100 + indice * 10},
            )

        for indice in range(1, 4):
            Servico.objects.using(alias).get_or_create(
                nome=f"Servico {indice}",
                defaults={"preco": 150 + indice * 20},
            )

        clientes = list(Cliente.objects.using(alias).all()[:3])
        produtos = list(Produto.objects.using(alias).all()[:3])
        servicos = list(Servico.objects.using(alias).all()[:3])
        for indice in range(3):
            venda, criada = Venda.objects.using(alias).get_or_create(
                cliente=clientes[indice],
                data=timezone.localdate(),
                defaults={"vendedor_usuario": usuario_empresa, "status": Venda.Status.RASCUNHO, "desconto": 10},
            )
            if criada:
                ItemVenda.objects.using(alias).create(
                    venda=venda,
                    tipo_item=ItemVenda.TipoItem.PRODUTO,
                    produto=produtos[indice],
                    quantidade=2,
                    valor_unitario=produtos[indice].preco,
                )
                ItemVenda.objects.using(alias).create(
                    venda=venda,
                    tipo_item=ItemVenda.TipoItem.SERVICO,
                    servico=servicos[indice],
                    quantidade=1,
                    valor_unitario=servicos[indice].preco,
                )

        self.stdout.write(self.style.SUCCESS("Seed concluído com sucesso."))
