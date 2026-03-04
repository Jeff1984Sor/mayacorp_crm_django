from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import Mock, PropertyMock, patch

from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase

from crm import views
from crm.models import ItemVenda, Venda


class GerenciadorItensFalso:
    def __init__(self, itens):
        self._itens = itens

    def using(self, alias):
        return self

    def all(self):
        return self._itens


class VendaRegrasNegocioTestes(SimpleTestCase):
    def test_item_venda_exige_produto_ou_servico_conforme_tipo(self):
        item = ItemVenda(
            venda=Venda(),
            tipo_item=ItemVenda.TipoItem.PRODUTO,
            quantidade=1,
            valor_unitario=Decimal("10.00"),
        )
        with self.assertRaises(ValidationError):
            item.clean()

    def test_item_venda_calcula_total_no_save(self):
        item = ItemVenda(
            venda=Venda(pk=1),
            tipo_item=ItemVenda.TipoItem.PRODUTO,
            produto_id=1,
            quantidade=2,
            valor_unitario=Decimal("25.00"),
        )
        with patch("django.db.models.base.Model.save", autospec=True) as save_mock:
            with patch("crm.models.Venda.objects") as venda_manager:
                venda_manager.using.return_value.get.return_value = Mock(recalcular_totais=Mock())
                item.save(using="default")
        self.assertEqual(item.total, Decimal("50.00"))
        save_mock.assert_called()

    def test_venda_recalcula_total_a_partir_dos_itens(self):
        venda = Venda(subtotal=Decimal("0.00"), desconto=Decimal("5.00"), total=Decimal("0.00"))
        venda._state.db = "default"
        venda.save = Mock()
        with patch.object(Venda, "itens", new_callable=PropertyMock) as itens_mock:
            itens_mock.return_value = GerenciadorItensFalso(
                [
                    SimpleNamespace(total=Decimal("20.00")),
                    SimpleNamespace(total=Decimal("30.00")),
                ]
            )
            venda.recalcular_totais()
        self.assertEqual(venda.subtotal, Decimal("50.00"))
        self.assertEqual(venda.total, Decimal("45.00"))
        venda.save.assert_called_once()

    def test_venda_fechada_nao_pode_ser_editada(self):
        venda = Venda(status=Venda.Status.FECHADA)
        self.assertFalse(venda.pode_editar())


class TelasClientesEVendasTestes(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_listagem_clientes_usa_template_dedicado(self):
        request = self.factory.get("/app/clientes")
        request.usuario_empresa = object()
        pagina = SimpleNamespace(paginator=SimpleNamespace(count=1, num_pages=1), number=1)
        pagina.__iter__ = lambda self=pagina: iter([])
        pagina.__len__ = lambda self=pagina: 0
        queryset = Mock()
        queryset.all.return_value = queryset
        queryset.filter.return_value = queryset
        queryset.order_by.return_value = queryset
        with patch("crm.views._qs", return_value=queryset):
            with patch("crm.views.Paginator") as paginator_mock:
                paginator_mock.return_value.get_page.return_value = pagina
                with patch("crm.views.render", return_value=HttpResponse("ok")) as render_mock:
                    resposta = views.listagem.__wrapped__(request, "clientes")
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(render_mock.call_args[0][1], "crm/clientes_listagem.html")

    def test_modal_exclusao_venda_envia_texto_contextual(self):
        request = self.factory.get("/app/vendas/1/modal-excluir")
        request.usuario_empresa = object()
        venda = SimpleNamespace(pk=1, status="RASCUNHO")
        with patch("crm.views._obter_configuracao", return_value={"modelo": Mock()}):
            with patch("crm.views.get_object_or_404", return_value=venda):
                with patch("crm.views.render", return_value=HttpResponse("ok")) as render_mock:
                    resposta = views.modal_exclusao.__wrapped__(request, "vendas", 1)
        self.assertEqual(resposta.status_code, 200)
        contexto = render_mock.call_args[0][2]
        self.assertEqual(contexto["titulo_modal"], "Cancelar venda")

    def test_detalhe_venda_htmx_usa_partial_dedicado(self):
        request = self.factory.get("/app/vendas/1?aba=itens", HTTP_HX_REQUEST="true")
        request.usuario_empresa = object()
        venda = SimpleNamespace(
            pk=1,
            cliente="Cliente Teste",
            data=SimpleNamespace(),
            status="RASCUNHO",
            subtotal=Decimal("10.00"),
            desconto=Decimal("0.00"),
            total=Decimal("10.00"),
            criado_em=None,
            atualizado_em=None,
            vendedor_usuario=None,
            vendedor_profissional=None,
            itens=SimpleNamespace(count=lambda: 0),
        )
        with patch("crm.views._obter_configuracao", return_value={"modelo": Mock(), "singular": "Venda", "secoes_detalhe": []}):
            with patch("crm.views.get_object_or_404", return_value=venda):
                with patch("crm.views._qs") as qs_mock:
                    qs_mock.return_value.filter.return_value = []
                    with patch("crm.views._montar_secoes", return_value=[]):
                        with patch("crm.views.render", return_value=HttpResponse("ok")) as render_mock:
                            resposta = views.detalhe.__wrapped__(request, "vendas", 1)
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(render_mock.call_args[0][1], "crm/parciais/venda_detalhe_conteudo.html")
