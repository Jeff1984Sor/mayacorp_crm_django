from datetime import datetime, time

from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from crm.autenticacao import login_empresa_obrigatorio
from crm.forms import (
    ClienteFormulario,
    ItemVendaFormulario,
    LoginEmpresaFormulario,
    ProdutoFormulario,
    ProfissionalEmpresaFormulario,
    ServicoFormulario,
    VendaFormulario,
)
from crm.models import Cliente, ItemVenda, Produto, ProfissionalEmpresa, RegistroAuditoriaEmpresa, Servico, UsuarioEmpresa, Venda
from plataforma_saas.tenant import obter_alias_banco, obter_tipo_tenant


CONFIGURACOES = {
    "profissionais": {
        "modelo": ProfissionalEmpresa,
        "formulario": ProfissionalEmpresaFormulario,
        "titulo": "Profissionais",
        "singular": "Profissional",
        "campos_busca": ["nome_completo", "email", "funcao"],
        "colunas": [("nome_completo", "Nome"), ("email", "E-mail"), ("funcao", "Funcao"), ("ativo", "Status")],
        "campo_ativo": "ativo",
        "secoes_formulario": [
            ("Dados Principais", ["nome_completo", "email", "telefone", "funcao"]),
            ("Controle", ["ativo", "observacoes"]),
        ],
        "secoes_detalhe": [
            ("Resumo", ["nome_completo", "email", "telefone", "funcao", "ativo"]),
            ("Notas", ["observacoes", "criado_em", "atualizado_em"]),
        ],
    },
    "clientes": {
        "modelo": Cliente,
        "formulario": ClienteFormulario,
        "titulo": "Clientes",
        "singular": "Cliente",
        "campos_busca": ["nome", "email", "documento"],
        "colunas": [("nome", "Nome"), ("status", "Status"), ("telefone", "Telefone"), ("ativo", "Ativo")],
        "campo_ativo": "ativo",
        "secoes_formulario": [
            ("Cadastro", ["nome", "documento", "email", "telefone", "status"]),
            ("Responsabilidade", ["responsavel_usuario", "responsavel_profissional", "ativo"]),
        ],
        "secoes_detalhe": [
            ("Resumo", ["nome", "documento", "email", "telefone", "status", "ativo"]),
            ("Relacionamento", ["responsavel_usuario", "responsavel_profissional", "criado_em", "atualizado_em"]),
        ],
    },
    "produtos": {
        "modelo": Produto,
        "formulario": ProdutoFormulario,
        "titulo": "Produtos",
        "singular": "Produto",
        "campos_busca": ["nome", "sku"],
        "colunas": [("nome", "Nome"), ("sku", "SKU"), ("preco", "Preco"), ("ativo", "Status")],
        "campo_ativo": "ativo",
        "secoes_formulario": [("Produto", ["nome", "sku", "preco", "ativo"])],
        "secoes_detalhe": [("Resumo", ["nome", "sku", "preco", "ativo", "criado_em", "atualizado_em"])],
    },
    "servicos": {
        "modelo": Servico,
        "formulario": ServicoFormulario,
        "titulo": "Servicos",
        "singular": "Servico",
        "campos_busca": ["nome"],
        "colunas": [("nome", "Nome"), ("preco", "Preco"), ("ativo", "Status")],
        "campo_ativo": "ativo",
        "secoes_formulario": [("Servico", ["nome", "preco", "ativo"])],
        "secoes_detalhe": [("Resumo", ["nome", "preco", "ativo", "criado_em", "atualizado_em"])],
    },
    "vendas": {
        "modelo": Venda,
        "formulario": VendaFormulario,
        "titulo": "Vendas",
        "singular": "Venda",
        "campos_busca": ["cliente__nome", "status"],
        "colunas": [("id", "Codigo"), ("cliente", "Cliente"), ("status", "Status"), ("total", "Total")],
        "campo_ativo": None,
        "secoes_formulario": [
            ("Comercial", ["cliente", "vendedor_usuario", "vendedor_profissional", "data", "status"]),
            ("Financeiro", ["desconto", "observacoes"]),
        ],
        "secoes_detalhe": [
            ("Resumo", ["cliente", "vendedor_usuario", "vendedor_profissional", "data", "status"]),
            ("Totais", ["subtotal", "desconto", "total", "observacoes", "criado_em", "atualizado_em"]),
        ],
    },
}

TEMPLATES_CRM = {
    "clientes": {
        "listagem": "crm/clientes_listagem.html",
        "listagem_hx": "crm/parciais/clientes_listagem_conteudo.html",
        "formulario": "crm/cliente_formulario.html",
        "detalhe": "crm/cliente_detalhe.html",
        "detalhe_hx": "crm/parciais/cliente_detalhe_conteudo.html",
    },
    "vendas": {
        "listagem": "crm/vendas_listagem.html",
        "listagem_hx": "crm/parciais/vendas_listagem_conteudo.html",
        "formulario": "crm/venda_formulario.html",
        "detalhe": "crm/venda_detalhe.html",
        "detalhe_hx": "crm/parciais/venda_detalhe_conteudo.html",
    },
    "produtos": {
        "listagem": "crm/produtos_listagem.html",
        "listagem_hx": "crm/parciais/produtos_listagem_conteudo.html",
        "formulario": "crm/produto_formulario.html",
        "detalhe": "crm/produto_detalhe.html",
        "detalhe_hx": "crm/parciais/produto_detalhe_conteudo.html",
    },
    "servicos": {
        "listagem": "crm/servicos_listagem.html",
        "listagem_hx": "crm/parciais/servicos_listagem_conteudo.html",
        "formulario": "crm/servico_formulario.html",
        "detalhe": "crm/servico_detalhe.html",
        "detalhe_hx": "crm/parciais/servico_detalhe_conteudo.html",
    }
}


def _qs(modelo):
    return modelo.objects.using(obter_alias_banco())


def _registrar_auditoria(request, acao, entidade, objeto=None, dados=None):
    RegistroAuditoriaEmpresa.objects.using(obter_alias_banco()).create(
        usuario_empresa=getattr(request, "usuario_empresa", None),
        acao=acao,
        entidade=entidade,
        objeto_id=getattr(objeto, "pk", None),
        ip=request.META.get("REMOTE_ADDR", ""),
        dados_json=dados or {},
    )


def _montar_secoes(objeto, secoes):
    retorno = []
    for titulo, campos in secoes:
        itens = []
        for campo in campos:
            field = objeto._meta.get_field(campo)
            itens.append((field.verbose_name or campo, getattr(objeto, campo)))
        retorno.append((titulo, itens))
    return retorno


def _montar_timeline_cliente(cliente):
    eventos = []
    for auditoria in (
        _qs(RegistroAuditoriaEmpresa)
        .filter(entidade="Cliente", objeto_id=cliente.pk)
        .order_by("-data")[:20]
    ):
        eventos.append(
            {
                "data": auditoria.data,
                "titulo": f"{auditoria.get_acao_display()} no cadastro",
                "descricao": auditoria.dados_json or "Movimentação registrada no CRM.",
                "tipo": "auditoria",
            }
        )
    for venda in cliente.vendas.order_by("-criado_em")[:10]:
        eventos.append(
            {
                "data": timezone.make_aware(datetime.combine(venda.data, time.min)),
                "titulo": f"Venda #{venda.pk} {venda.get_status_display().lower()}",
                "descricao": f"Total de R$ {venda.total}",
                "tipo": "venda",
            }
        )
    eventos.sort(key=lambda item: item["data"], reverse=True)
    return eventos[:20]


def _montar_timeline_profissional(profissional):
    eventos = []
    for auditoria in (
        _qs(RegistroAuditoriaEmpresa)
        .filter(entidade="Profissional", objeto_id=profissional.pk)
        .order_by("-data")[:20]
    ):
        eventos.append(
            {
                "data": auditoria.data,
                "titulo": f"{auditoria.get_acao_display()} no cadastro",
                "descricao": auditoria.dados_json or "Movimentação registrada no CRM.",
                "tipo": "auditoria",
            }
        )
    vendas_relacionadas = _qs(Venda).filter(vendedor_profissional=profissional).order_by("-criado_em")[:10]
    for venda in vendas_relacionadas:
        eventos.append(
            {
                "data": timezone.make_aware(datetime.combine(venda.data, time.min)),
                "titulo": f"Venda #{venda.pk} {venda.get_status_display().lower()}",
                "descricao": f"Cliente {venda.cliente} | total de R$ {venda.total}",
                "tipo": "venda",
            }
        )
    eventos.sort(key=lambda item: item["data"], reverse=True)
    return eventos[:20]


def _montar_timeline_item_catalogo(objeto_catalogo, tipo_item):
    entidade = "Produto" if tipo_item == "PRODUTO" else "Servico"
    eventos = []
    for auditoria in (
        _qs(RegistroAuditoriaEmpresa)
        .filter(entidade=entidade, objeto_id=objeto_catalogo.pk)
        .order_by("-data")[:20]
    ):
        eventos.append(
            {
                "data": auditoria.data,
                "titulo": f"{auditoria.get_acao_display()} no cadastro",
                "descricao": auditoria.dados_json or "Movimentação registrada no CRM.",
                "tipo": "auditoria",
            }
        )
    filtro_vendas = {"itens__produto": objeto_catalogo} if tipo_item == "PRODUTO" else {"itens__servico": objeto_catalogo}
    for venda in _qs(Venda).filter(**filtro_vendas).distinct().order_by("-criado_em")[:10]:
        eventos.append(
            {
                "data": timezone.make_aware(datetime.combine(venda.data, time.min)),
                "titulo": f"Usado na venda #{venda.pk}",
                "descricao": f"Cliente {venda.cliente} | status {venda.get_status_display()} | total R$ {venda.total}",
                "tipo": "venda",
            }
        )
    eventos.sort(key=lambda item: item["data"], reverse=True)
    return eventos[:20]


def login(request):
    if obter_tipo_tenant() != "empresa":
        return redirect("core_login")
    if getattr(request, "usuario_empresa", None):
        return redirect("crm_dashboard")
    formulario = LoginEmpresaFormulario(request.POST or None)
    if request.method == "POST" and formulario.is_valid():
        usuario = _qs(UsuarioEmpresa).filter(email=formulario.cleaned_data["email"], ativo=True).first()
        if usuario and usuario.validar_senha(formulario.cleaned_data["senha"]):
            request.session["usuario_empresa_id"] = usuario.id
            request.session.set_expiry(60 * 60 * 24 * 30 if formulario.cleaned_data["lembrar_me"] else 0)
            usuario.registrar_login()
            _registrar_auditoria(request, RegistroAuditoriaEmpresa.Acao.LOGIN, "UsuarioEmpresa", usuario)
            return redirect("crm_dashboard")
        messages.error(request, "Credenciais inválidas.")
    return render(request, "crm/login.html", {"formulario": formulario})


def logout(request):
    request.session.pop("usuario_empresa_id", None)
    return redirect("crm_login")


@login_empresa_obrigatorio
def dashboard(request):
    filtro_status_cliente = request.GET.get("status_cliente", "")
    filtro_status_venda = request.GET.get("status_venda", "")
    clientes = _qs(Cliente).all()
    vendas = _qs(Venda).all()
    if filtro_status_cliente in dict(Cliente.Status.choices):
        clientes = clientes.filter(status=filtro_status_cliente)
    if filtro_status_venda in dict(Venda.Status.choices):
        vendas = vendas.filter(status=filtro_status_venda)
    total_vendas = sum((v.total for v in vendas[:20]), 0)
    clientes_recentes = clientes.order_by("-atualizado_em")[:5]
    vendas_recentes = vendas.order_by("-criado_em")[:5]
    contexto = {
        "titulo_pagina": "Portal da Empresa",
        "cards": [
            ("Clientes", clientes.count()),
            ("Produtos", _qs(Produto).count()),
            ("Serviços", _qs(Servico).count()),
            ("Vendas", vendas.count()),
            ("Receita visível", f"R$ {total_vendas}"),
            ("Profissionais", _qs(ProfissionalEmpresa).count()),
        ],
        "clientes_recentes": clientes_recentes,
        "vendas_recentes": vendas_recentes,
        "filtros_dashboard": {
            "status_cliente": filtro_status_cliente,
            "status_venda": filtro_status_venda,
        },
        "opcoes_status_cliente": Cliente.Status.choices,
        "opcoes_status_venda": Venda.Status.choices,
    }
    template = "crm/parciais/dashboard_conteudo.html" if request.headers.get("HX-Request") else "crm/dashboard.html"
    return render(request, template, contexto)


def _obter_configuracao(chave):
    if chave not in CONFIGURACOES:
        raise Http404
    return CONFIGURACOES[chave]


def _obter_template(entidade, chave, padrao):
    return TEMPLATES_CRM.get(entidade, {}).get(chave, padrao)


def _filtrar(request, queryset, configuracao):
    busca = request.GET.get("busca", "").strip()
    status = request.GET.get("status", "")
    ordem = request.GET.get("ordem") or configuracao["colunas"][0][0]
    if busca:
        consulta = Q()
        for campo in configuracao["campos_busca"]:
            consulta |= Q(**{f"{campo}__icontains": busca})
        queryset = queryset.filter(consulta)
    if configuracao["campo_ativo"] and status in {"ativo", "inativo"}:
        queryset = queryset.filter(**{configuracao["campo_ativo"]: status == "ativo"})
    if status and not configuracao["campo_ativo"] and status in dict(Venda.Status.choices):
        queryset = queryset.filter(status=status)
    if ordem.lstrip("-") in [c[0] for c in configuracao["colunas"]]:
        queryset = queryset.order_by(ordem)
    return queryset, busca, status, ordem


@login_empresa_obrigatorio
def listagem(request, entidade):
    configuracao = _obter_configuracao(entidade)
    queryset = _qs(configuracao["modelo"]).all()
    queryset, busca, status, ordem = _filtrar(request, queryset, configuracao)
    pagina = Paginator(queryset, 10).get_page(request.GET.get("pagina"))
    contexto = {"configuracao": configuracao, "entidade": entidade, "pagina": pagina, "busca": busca, "status": status, "ordem": ordem}
    template = (
        _obter_template(entidade, "listagem_hx", "crm/parciais/listagem_conteudo.html")
        if request.headers.get("HX-Request")
        else _obter_template(entidade, "listagem", "crm/listagem.html")
    )
    return render(request, template, contexto)


@login_empresa_obrigatorio
def criar(request, entidade):
    configuracao = _obter_configuracao(entidade)
    formulario = configuracao["formulario"](request.POST or None)
    if request.method == "POST" and formulario.is_valid():
        objeto = formulario.save(commit=False)
        objeto.save(using=obter_alias_banco())
        _registrar_auditoria(request, RegistroAuditoriaEmpresa.Acao.CRIAR, configuracao["singular"], objeto)
        messages.success(request, f"{configuracao['singular']} criado com sucesso.")
        return redirect(f"crm_{entidade}_detalhe", pk=objeto.pk)
    return render(
        request,
        _obter_template(entidade, "formulario", "crm/formulario.html"),
        {"configuracao": configuracao, "formulario": formulario, "entidade": entidade},
    )


@login_empresa_obrigatorio
def editar(request, entidade, pk):
    configuracao = _obter_configuracao(entidade)
    objeto = get_object_or_404(_qs(configuracao["modelo"]), pk=pk)
    formulario = configuracao["formulario"](request.POST or None, instance=objeto)
    if request.method == "POST" and formulario.is_valid():
        objeto = formulario.save(commit=False)
        objeto.save(using=obter_alias_banco())
        _registrar_auditoria(request, RegistroAuditoriaEmpresa.Acao.EDITAR, configuracao["singular"], objeto)
        messages.success(request, f"{configuracao['singular']} atualizado com sucesso.")
        return redirect(f"crm_{entidade}_detalhe", pk=objeto.pk)
    return render(
        request,
        _obter_template(entidade, "formulario", "crm/formulario.html"),
        {"configuracao": configuracao, "formulario": formulario, "entidade": entidade, "objeto": objeto},
    )


@login_empresa_obrigatorio
def detalhe(request, entidade, pk):
    configuracao = _obter_configuracao(entidade)
    objeto = get_object_or_404(_qs(configuracao["modelo"]), pk=pk)
    abas = {
        "profissionais": [("resumo", "Resumo"), ("agenda", "Agenda"), ("vendas", "Vendas"), ("auditoria", "Auditoria")],
        "clientes": [("resumo", "Resumo"), ("atividades", "Atividades"), ("vendas", "Vendas"), ("auditoria", "Auditoria")],
        "produtos": [("resumo", "Resumo"), ("auditoria", "Auditoria")],
        "servicos": [("resumo", "Resumo"), ("auditoria", "Auditoria")],
        "vendas": [("itens", "Itens"), ("pagamento", "Pagamento"), ("resumo", "Resumo"), ("auditoria", "Auditoria")],
    }[entidade]
    aba_atual = request.GET.get("aba") or abas[0][0]
    auditorias = _qs(RegistroAuditoriaEmpresa).filter(entidade=configuracao["singular"], objeto_id=objeto.pk)[:12]
    secoes_detalhe = _montar_secoes(objeto, configuracao.get("secoes_detalhe", []))
    if entidade == "profissionais":
        secoes_por_aba = {
            "resumo": secoes_detalhe,
            "agenda": [("Agenda", [("Situação", "Placeholder MVP"), ("Próximo passo", "Sem agenda integrada")])],
            "vendas": [("Vendas", [("Situação", "Placeholder MVP"), ("Resumo", "Sem vínculo automático no MVP")])],
            "auditoria": [],
        }
    elif entidade == "clientes":
        secoes_por_aba = {
            "resumo": [secoes_detalhe[0]] if secoes_detalhe else [],
            "atividades": [("Atividades", [("Histórico", "Placeholder MVP"), ("Último contato", "Não registrado")])],
            "vendas": [("Vendas", [("Total de vendas", objeto.vendas.count()), ("Última venda", objeto.vendas.order_by("-criado_em").first() or "-")])],
            "auditoria": [],
        }
    elif entidade in {"produtos", "servicos"}:
        secoes_por_aba = {"resumo": secoes_detalhe, "auditoria": []}
    else:
        secoes_por_aba = {
            "itens": [("Itens", [("Quantidade de itens", objeto.itens.count()), ("Subtotal", objeto.subtotal), ("Total", objeto.total)])],
            "pagamento": [("Pagamento", [("Status", "Placeholder MVP"), ("Desconto aplicado", objeto.desconto)])],
            "resumo": secoes_detalhe,
            "auditoria": [],
        }
    contexto = {
        "configuracao": configuracao,
        "objeto": objeto,
        "abas": abas,
        "entidade": entidade,
        "auditorias": auditorias,
        "secoes_detalhe": secoes_por_aba.get(aba_atual, secoes_detalhe),
        "aba_atual": aba_atual,
    }
    if entidade == "clientes":
        contexto["timeline_atividades"] = _montar_timeline_cliente(objeto)
    if entidade == "profissionais":
        contexto["timeline_atividades"] = _montar_timeline_profissional(objeto)
    if entidade == "produtos":
        contexto["timeline_atividades"] = _montar_timeline_item_catalogo(objeto, "PRODUTO")
    if entidade == "servicos":
        contexto["timeline_atividades"] = _montar_timeline_item_catalogo(objeto, "SERVICO")
    template = (
        _obter_template(entidade, "detalhe_hx", "crm/parciais/detalhe_conteudo.html")
        if request.headers.get("HX-Request")
        else _obter_template(entidade, "detalhe", "crm/detalhe.html")
    )
    return render(request, template, contexto)


@login_empresa_obrigatorio
def modal_exclusao(request, entidade, pk):
    configuracao = _obter_configuracao(entidade)
    objeto = get_object_or_404(_qs(configuracao["modelo"]), pk=pk)
    contexto = {
        "objeto": objeto,
        "entidade": entidade,
        "tenant_tipo": "empresa",
        "titulo_modal": "Confirmar ação",
        "texto_modal": f"Esta ação será aplicada em {objeto}.",
        "texto_botao_modal": "Confirmar",
    }
    if entidade == "vendas":
        contexto.update(
            {
                "titulo_modal": "Cancelar venda",
                "texto_modal": f"A venda #{objeto.pk} será cancelada e não poderá voltar para rascunho.",
                "texto_botao_modal": "Cancelar venda",
            }
        )
    elif entidade == "clientes" and objeto.vendas.exists():
        contexto.update(
            {
                "titulo_modal": "Inativar cliente",
                "texto_modal": "Este cliente possui vendas. A ação será convertida em inativação para preservar o histórico.",
                "texto_botao_modal": "Inativar cliente",
            }
        )
    return render(request, "componentes/modal_confirmacao.html", contexto)


@login_empresa_obrigatorio
def excluir(request, entidade, pk):
    configuracao = _obter_configuracao(entidade)
    objeto = get_object_or_404(_qs(configuracao["modelo"]), pk=pk)
    if request.method == "POST":
        if entidade == "clientes" and objeto.vendas.exists():
            objeto.ativo = False
            objeto.save(using=obter_alias_banco(), update_fields=["ativo", "atualizado_em"])
            _registrar_auditoria(request, RegistroAuditoriaEmpresa.Acao.INATIVAR, configuracao["singular"], objeto, {"motivo": "possui_vendas"})
            messages.warning(request, "Cliente possui vendas e foi apenas inativado.")
        elif configuracao["campo_ativo"]:
            setattr(objeto, configuracao["campo_ativo"], False)
            campos = [configuracao["campo_ativo"]]
            if hasattr(objeto, "atualizado_em"):
                campos.append("atualizado_em")
            objeto.save(using=obter_alias_banco(), update_fields=campos)
            _registrar_auditoria(request, RegistroAuditoriaEmpresa.Acao.INATIVAR, configuracao["singular"], objeto)
            messages.success(request, f"{configuracao['singular']} arquivado com sucesso.")
        elif entidade == "vendas":
            objeto.status = Venda.Status.CANCELADA
            objeto.save(using=obter_alias_banco(), update_fields=["status", "atualizado_em"])
            _registrar_auditoria(request, RegistroAuditoriaEmpresa.Acao.CANCELAR, configuracao["singular"], objeto)
            messages.success(request, "Venda cancelada com sucesso.")
        if request.headers.get("HX-Request"):
            return HttpResponse("", headers={"HX-Redirect": reverse(f"crm_{entidade}_lista")})
        return redirect(f"crm_{entidade}_lista")
    return redirect(f"crm_{entidade}_lista")


@login_empresa_obrigatorio
def adicionar_item_venda(request, pk):
    venda = get_object_or_404(_qs(Venda), pk=pk)
    if not venda.pode_editar():
        messages.error(request, "Venda fechada não pode ser editada.")
        return HttpResponse(status=400)
    formulario = ItemVendaFormulario(request.POST or None)
    if request.method == "POST" and formulario.is_valid():
        item = formulario.save(commit=False)
        item.venda = venda
        item.save(using=obter_alias_banco())
        _registrar_auditoria(request, RegistroAuditoriaEmpresa.Acao.CRIAR, "ItemVenda", item, {"venda_id": venda.pk})
        formulario = ItemVendaFormulario()
    itens = venda.itens.all()
    return render(request, "crm/parciais/itens_venda.html", {"venda": venda, "itens": itens, "formulario_item": formulario})


@login_empresa_obrigatorio
def remover_item_venda(request, pk, item_id):
    venda = get_object_or_404(_qs(Venda), pk=pk)
    item = get_object_or_404(venda.itens, pk=item_id)
    if request.method == "POST" and venda.pode_editar():
        item_pk = item.pk
        item.delete(using=obter_alias_banco())
        _registrar_auditoria(request, RegistroAuditoriaEmpresa.Acao.EXCLUIR, "ItemVenda", dados={"item_id": item_pk, "venda_id": venda.pk})
    venda = _qs(Venda).get(pk=pk)
    return render(request, "crm/parciais/itens_venda.html", {"venda": venda, "itens": venda.itens.all(), "formulario_item": ItemVendaFormulario()})
