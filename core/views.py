import csv
from decimal import Decimal

from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from core.autenticacao import login_admin_obrigatorio
from core.forms import (
    CategoriaFinanceiraFormulario,
    ContaFinanceiraFormulario,
    ContaPagarFormulario,
    EmpresaFormulario,
    FornecedorFormulario,
    LoginAdminFormulario,
    PlanoFormulario,
    ProdutoFormulario,
    ProfissionalFormulario,
    ReceitaFormulario,
    ServicoFormulario,
    SubcategoriaFinanceiraFormulario,
    VendaCentralFormulario,
)
from core.models import (
    CategoriaFinanceira,
    ContaFinanceira,
    ContaPagar,
    Empresa,
    Fornecedor,
    Plano,
    Produto,
    Profissional,
    Receita,
    RegistroAuditoria,
    Servico,
    SubcategoriaFinanceira,
    UsuarioAdmin,
    VendaCentral,
)


CONFIGURACOES = {
    "profissionais": {
        "modelo": Profissional,
        "formulario": ProfissionalFormulario,
        "titulo": "Profissionais",
        "singular": "Profissional",
        "campos_busca": ["nome_completo", "email", "cargo"],
        "colunas": [("nome_completo", "Nome"), ("email", "E-mail"), ("cargo", "Cargo"), ("ativo", "Status")],
        "campo_ativo": "ativo",
        "secoes_formulario": [
            ("Dados Principais", ["nome_completo", "email", "telefone", "cargo"]),
            ("Controle", ["ativo", "observacoes"]),
        ],
        "secoes_detalhe": [
            ("Dados Gerais", ["nome_completo", "email", "telefone", "cargo", "ativo"]),
            ("Observacoes", ["observacoes", "criado_em", "atualizado_em"]),
        ],
    },
    "planos": {
        "modelo": Plano,
        "formulario": PlanoFormulario,
        "titulo": "Planos",
        "singular": "Plano",
        "campos_busca": ["nome", "descricao", "ciclo_cobranca"],
        "colunas": [("nome", "Nome"), ("preco", "Preco"), ("ciclo_cobranca", "Ciclo"), ("ativo", "Status")],
        "campo_ativo": "ativo",
        "secoes_formulario": [
            ("Estrutura do Plano", ["nome", "descricao", "preco", "ciclo_cobranca"]),
            ("Capacidade", ["ativo", "limite_usuarios", "limite_registros"]),
            ("Recursos", ["recursos_json"]),
        ],
        "secoes_detalhe": [
            ("Geral", ["nome", "descricao", "preco", "ciclo_cobranca", "ativo"]),
            ("Limites", ["limite_usuarios", "limite_registros"]),
            ("Recursos", ["recursos_json", "criado_em", "atualizado_em"]),
        ],
    },
    "empresas": {
        "modelo": Empresa,
        "formulario": EmpresaFormulario,
        "titulo": "Empresas",
        "singular": "Empresa",
        "campos_busca": ["nome", "slug", "email", "documento"],
        "colunas": [("nome", "Nome"), ("slug", "Slug"), ("status_assinatura", "Assinatura"), ("ativo", "Status")],
        "campo_ativo": "ativo",
        "secoes_formulario": [
            ("Identificacao", ["nome", "slug", "documento", "email", "telefone"]),
            ("Assinatura", ["ativo", "plano", "status_assinatura", "inicio_assinatura", "fim_teste"]),
            ("Banco de Dados", ["motor_banco", "nome_banco", "usuario_banco", "senha_banco", "host_banco", "porta_banco"]),
        ],
        "secoes_detalhe": [
            ("Visao Geral", ["nome", "slug", "documento", "email", "telefone", "ativo"]),
            ("Assinatura", ["plano", "status_assinatura", "inicio_assinatura", "fim_teste"]),
            ("Banco", ["motor_banco", "nome_banco", "usuario_banco", "host_banco", "porta_banco", "criado_em", "atualizado_em"]),
        ],
    },
    "fornecedores": {
        "modelo": Fornecedor,
        "formulario": FornecedorFormulario,
        "titulo": "Fornecedores",
        "singular": "Fornecedor",
        "campos_busca": ["nome", "documento", "email", "contato_principal"],
        "colunas": [("nome", "Nome"), ("contato_principal", "Contato"), ("telefone", "Telefone"), ("ativo", "Status")],
        "campo_ativo": "ativo",
        "secoes_formulario": [
            ("Cadastro", ["nome", "documento", "email", "telefone", "contato_principal"]),
            ("Controle", ["ativo", "observacoes"]),
        ],
        "secoes_detalhe": [
            ("Resumo", ["nome", "documento", "email", "telefone", "contato_principal", "ativo"]),
            ("Relacionamento", ["observacoes", "criado_em", "atualizado_em"]),
        ],
    },
    "produtos": {
        "modelo": Produto,
        "formulario": ProdutoFormulario,
        "titulo": "Produtos",
        "singular": "Produto",
        "campos_busca": ["nome", "sku", "fornecedor__nome"],
        "colunas": [("nome", "Nome"), ("sku", "SKU"), ("fornecedor", "Fornecedor"), ("ativo", "Status")],
        "campo_ativo": "ativo",
        "secoes_formulario": [
            ("Catalogo", ["nome", "sku", "fornecedor"]),
            ("Precificacao", ["valor_custo", "valor_venda", "ativo"]),
            ("Notas", ["observacoes"]),
        ],
        "secoes_detalhe": [
            ("Resumo", ["nome", "sku", "fornecedor", "ativo"]),
            ("Precificacao", ["valor_custo", "valor_venda", "observacoes"]),
            ("Auditoria", ["criado_em", "atualizado_em"]),
        ],
    },
    "servicos": {
        "modelo": Servico,
        "formulario": ServicoFormulario,
        "titulo": "Servicos",
        "singular": "Servico",
        "campos_busca": ["nome", "descricao"],
        "colunas": [("nome", "Nome"), ("valor_venda", "Venda"), ("valor_custo", "Custo"), ("ativo", "Status")],
        "campo_ativo": "ativo",
        "secoes_formulario": [
            ("Cadastro", ["nome", "descricao"]),
            ("Precificacao", ["valor_custo", "valor_venda", "ativo"]),
        ],
        "secoes_detalhe": [
            ("Resumo", ["nome", "descricao", "ativo"]),
            ("Precificacao", ["valor_custo", "valor_venda"]),
            ("Auditoria", ["criado_em", "atualizado_em"]),
        ],
    },
    "vendas": {
        "modelo": VendaCentral,
        "formulario": VendaCentralFormulario,
        "titulo": "Vendas",
        "singular": "Venda",
        "campos_busca": ["titulo", "cliente", "status"],
        "colunas": [("titulo", "Titulo"), ("cliente", "Cliente"), ("status", "Status"), ("valor_total", "Total")],
        "campo_ativo": "ativo",
        "secoes_formulario": [
            ("Comercial", ["titulo", "cliente", "data_venda", "status"]),
            ("Valores", ["valor_bruto", "desconto", "ativo"]),
            ("Notas", ["observacoes"]),
        ],
        "secoes_detalhe": [
            ("Resumo", ["titulo", "cliente", "data_venda", "status", "ativo"]),
            ("Financeiro", ["valor_bruto", "desconto", "valor_total", "observacoes"]),
            ("Auditoria", ["criado_em", "atualizado_em"]),
        ],
    },
    "receitas": {
        "modelo": Receita,
        "formulario": ReceitaFormulario,
        "titulo": "Receitas",
        "singular": "Receita",
        "campos_busca": ["descricao", "status", "conta_financeira__nome", "venda__titulo", "categoria__nome", "subcategoria__nome"],
        "colunas": [("descricao", "Descricao"), ("conta_financeira", "Conta"), ("status", "Status"), ("valor", "Valor")],
        "campo_ativo": "ativo",
        "secoes_formulario": [
            ("Lancamento", ["descricao", "venda", "conta_financeira", "categoria", "subcategoria", "data_recebimento"]),
            ("Financeiro", ["valor", "status", "ativo"]),
            ("Notas", ["observacoes"]),
        ],
        "secoes_detalhe": [
            ("Resumo", ["descricao", "venda", "conta_financeira", "categoria", "subcategoria", "data_recebimento", "ativo"]),
            ("Financeiro", ["valor", "status", "observacoes"]),
            ("Auditoria", ["criado_em", "atualizado_em"]),
        ],
    },
    "contas_pagar": {
        "modelo": ContaPagar,
        "formulario": ContaPagarFormulario,
        "titulo": "Contas a Pagar",
        "singular": "Conta a Pagar",
        "campos_busca": ["descricao", "status", "conta_financeira__nome", "fornecedor__nome", "categoria__nome", "subcategoria__nome"],
        "colunas": [("descricao", "Descricao"), ("fornecedor", "Fornecedor"), ("status", "Status"), ("valor", "Valor")],
        "campo_ativo": "ativo",
        "secoes_formulario": [
            ("Lancamento", ["descricao", "fornecedor", "conta_financeira", "categoria", "subcategoria", "data_vencimento"]),
            ("Financeiro", ["valor", "status", "ativo"]),
            ("Notas", ["observacoes"]),
        ],
        "secoes_detalhe": [
            ("Resumo", ["descricao", "fornecedor", "conta_financeira", "categoria", "subcategoria", "data_vencimento", "ativo"]),
            ("Financeiro", ["valor", "status", "observacoes"]),
            ("Auditoria", ["criado_em", "atualizado_em"]),
        ],
    },
    "contas_financeiras": {
        "modelo": ContaFinanceira,
        "formulario": ContaFinanceiraFormulario,
        "titulo": "Contas Financeiras",
        "singular": "Conta Financeira",
        "campos_busca": ["nome", "instituicao", "observacoes"],
        "colunas": [("nome", "Nome"), ("instituicao", "Instituicao"), ("saldo_inicial", "Saldo Inicial"), ("ativo", "Status")],
        "campo_ativo": "ativo",
        "secoes_formulario": [
            ("Estrutura", ["nome", "instituicao", "saldo_inicial", "ativo"]),
            ("Notas", ["observacoes"]),
        ],
        "secoes_detalhe": [
            ("Resumo", ["nome", "instituicao", "saldo_inicial", "ativo"]),
            ("Operacao", ["observacoes", "criado_em", "atualizado_em"]),
        ],
    },
    "categorias": {
        "modelo": CategoriaFinanceira,
        "formulario": CategoriaFinanceiraFormulario,
        "titulo": "Categorias",
        "singular": "Categoria",
        "campos_busca": ["nome", "observacoes"],
        "colunas": [("nome", "Nome"), ("ativo", "Status")],
        "campo_ativo": "ativo",
        "secoes_formulario": [("Estrutura", ["nome", "ativo"]), ("Notas", ["observacoes"])],
        "secoes_detalhe": [
            ("Resumo", ["nome", "ativo"]),
            ("Estrutura", ["observacoes", "criado_em", "atualizado_em"]),
        ],
    },
    "subcategorias": {
        "modelo": SubcategoriaFinanceira,
        "formulario": SubcategoriaFinanceiraFormulario,
        "titulo": "Subcategorias",
        "singular": "Subcategoria",
        "campos_busca": ["nome", "categoria__nome", "observacoes"],
        "colunas": [("nome", "Nome"), ("categoria", "Categoria"), ("ativo", "Status")],
        "campo_ativo": "ativo",
        "secoes_formulario": [("Estrutura", ["categoria", "nome", "ativo"]), ("Notas", ["observacoes"])],
        "secoes_detalhe": [
            ("Resumo", ["categoria", "nome", "ativo"]),
            ("Estrutura", ["observacoes", "criado_em", "atualizado_em"]),
        ],
    },
}

TEMPLATES_CORE = {
    "fornecedores": {
        "listagem": "core/fornecedores_listagem.html",
        "listagem_hx": "core/parciais/fornecedores_listagem_conteudo.html",
        "formulario": "core/fornecedor_formulario.html",
        "detalhe": "core/fornecedor_detalhe.html",
        "detalhe_hx": "core/parciais/fornecedor_detalhe_conteudo.html",
    },
    "produtos": {
        "listagem": "core/produtos_listagem.html",
        "listagem_hx": "core/parciais/produtos_listagem_conteudo.html",
        "formulario": "core/produto_formulario.html",
        "detalhe": "core/produto_detalhe.html",
        "detalhe_hx": "core/parciais/produto_detalhe_conteudo.html",
    },
    "servicos": {
        "listagem": "core/servicos_listagem.html",
        "listagem_hx": "core/parciais/servicos_listagem_conteudo.html",
        "formulario": "core/servico_formulario.html",
        "detalhe": "core/servico_detalhe.html",
        "detalhe_hx": "core/parciais/servico_detalhe_conteudo.html",
    },
}


def _registrar_auditoria(request, acao, entidade, objeto=None, dados=None):
    RegistroAuditoria.objects.create(
        usuario_admin=getattr(request, "usuario_admin", None),
        acao=acao,
        entidade=entidade,
        objeto_id=getattr(objeto, "id", None),
        ip=request.META.get("REMOTE_ADDR", ""),
        dados_json=dados or {},
    )


def login(request):
    if getattr(request, "usuario_admin", None):
        return redirect("core_dashboard")
    formulario = LoginAdminFormulario(request.POST or None)
    if request.method == "POST" and formulario.is_valid():
        usuario = UsuarioAdmin.objects.filter(email=formulario.cleaned_data["email"], ativo=True).first()
        if usuario and usuario.validar_senha(formulario.cleaned_data["senha"]):
            request.session["usuario_admin_id"] = usuario.id
            request.session.set_expiry(60 * 60 * 24 * 30 if formulario.cleaned_data["lembrar_me"] else 0)
            usuario.registrar_login()
            _registrar_auditoria(request, RegistroAuditoria.Acao.LOGIN, "UsuarioAdmin", usuario)
            return redirect("core_dashboard")
        messages.error(request, "Credenciais invalidas.")
    return render(request, "core/login.html", {"formulario": formulario})


def logout(request):
    request.session.pop("usuario_admin_id", None)
    return redirect("core_login")


@login_admin_obrigatorio
def dashboard(request):
    contexto = {
        "titulo_pagina": "Painel Central",
        "cards": [
            ("Profissionais", Profissional.objects.count()),
            ("Planos", Plano.objects.count()),
            ("Empresas", Empresa.objects.count()),
            ("Fornecedores", Fornecedor.objects.count()),
            ("Produtos", Produto.objects.count()),
            ("Servicos", Servico.objects.count()),
            ("Vendas", VendaCentral.objects.count()),
            ("Receitas", Receita.objects.count()),
            ("Contas a Pagar", ContaPagar.objects.count()),
            ("Contas Financeiras", ContaFinanceira.objects.count()),
            ("Categorias", CategoriaFinanceira.objects.count()),
            ("Subcategorias", SubcategoriaFinanceira.objects.count()),
            ("Auditorias", RegistroAuditoria.objects.count()),
        ],
    }
    return render(request, "core/dashboard.html", contexto)


@login_admin_obrigatorio
def auditoria(request):
    queryset = RegistroAuditoria.objects.select_related("usuario_admin").all()
    usuario_id = request.GET.get("usuario")
    acao = request.GET.get("acao")
    data_inicial = request.GET.get("data_inicial")
    data_final = request.GET.get("data_final")
    if usuario_id:
        queryset = queryset.filter(usuario_admin_id=usuario_id)
    if acao:
        queryset = queryset.filter(acao=acao)
    if data_inicial:
        queryset = queryset.filter(data__date__gte=data_inicial)
    if data_final:
        queryset = queryset.filter(data__date__lte=data_final)
    if request.GET.get("exportar") == "csv":
        resposta = HttpResponse(content_type="text/csv")
        resposta["Content-Disposition"] = 'attachment; filename="auditoria_central.csv"'
        escritor = csv.writer(resposta)
        escritor.writerow(["Data", "Usuario", "Acao", "Entidade", "Objeto", "IP"])
        for item in queryset.order_by("-data"):
            escritor.writerow(
                [
                    item.data.strftime("%Y-%m-%d %H:%M:%S"),
                    item.usuario_admin.nome if item.usuario_admin else "",
                    item.acao,
                    item.entidade,
                    item.objeto_id or "",
                    item.ip,
                ]
            )
        return resposta
    pagina = Paginator(queryset, 20).get_page(request.GET.get("pagina"))
    return render(
        request,
        "core/auditoria.html",
        {
            "titulo_pagina": "Auditoria Central",
            "pagina": pagina,
            "usuarios": UsuarioAdmin.objects.filter(ativo=True).order_by("nome"),
            "acoes": RegistroAuditoria.Acao.choices,
            "filtros": {
                "usuario": usuario_id or "",
                "acao": acao or "",
                "data_inicial": data_inicial or "",
                "data_final": data_final or "",
            },
        },
    )


def _obter_configuracao(chave):
    if chave not in CONFIGURACOES:
        raise Http404
    return CONFIGURACOES[chave]


def _obter_template(entidade, chave, padrao):
    return TEMPLATES_CORE.get(entidade, {}).get(chave, padrao)


def _montar_secoes(objeto, secoes):
    retorno = []
    for titulo, campos in secoes:
        itens = []
        for campo in campos:
            field = objeto._meta.get_field(campo)
            itens.append((field.verbose_name or campo, getattr(objeto, campo)))
        retorno.append((titulo, itens))
    return retorno


def _filtrar_listagem(request, queryset, configuracao):
    busca = request.GET.get("busca", "").strip()
    status = request.GET.get("status", "")
    ordem = request.GET.get("ordem") or configuracao["colunas"][0][0]
    if busca:
        consulta = Q()
        for campo in configuracao["campos_busca"]:
            consulta |= Q(**{f"{campo}__icontains": busca})
        queryset = queryset.filter(consulta)
    if status in {"ativo", "inativo"}:
        queryset = queryset.filter(**{configuracao["campo_ativo"]: status == "ativo"})
    if ordem.lstrip("-") in [coluna[0] for coluna in configuracao["colunas"]]:
        queryset = queryset.order_by(ordem)
    return queryset, busca, status, ordem


@login_admin_obrigatorio
def listagem(request, entidade):
    configuracao = _obter_configuracao(entidade)
    queryset = configuracao["modelo"].objects.all()
    queryset, busca, status, ordem = _filtrar_listagem(request, queryset, configuracao)
    pagina = Paginator(queryset, 10).get_page(request.GET.get("pagina"))
    contexto = {"configuracao": configuracao, "entidade": entidade, "pagina": pagina, "busca": busca, "status": status, "ordem": ordem}
    template = (
        _obter_template(entidade, "listagem_hx", "core/parciais/listagem_conteudo.html")
        if request.headers.get("HX-Request")
        else _obter_template(entidade, "listagem", "core/listagem.html")
    )
    return render(request, template, contexto)


@login_admin_obrigatorio
def criar(request, entidade):
    configuracao = _obter_configuracao(entidade)
    formulario = configuracao["formulario"](request.POST or None)
    if request.method == "POST" and formulario.is_valid():
        objeto = formulario.save()
        _registrar_auditoria(request, RegistroAuditoria.Acao.CRIAR, configuracao["singular"], objeto)
        messages.success(request, f"{configuracao['singular']} criado com sucesso.")
        return redirect(f"core_{entidade}_detalhe", pk=objeto.pk)
    return render(
        request,
        _obter_template(entidade, "formulario", "core/formulario.html"),
        {"configuracao": configuracao, "formulario": formulario, "entidade": entidade},
    )


@login_admin_obrigatorio
def editar(request, entidade, pk):
    configuracao = _obter_configuracao(entidade)
    objeto = get_object_or_404(configuracao["modelo"], pk=pk)
    formulario = configuracao["formulario"](request.POST or None, instance=objeto)
    if request.method == "POST" and formulario.is_valid():
        objeto = formulario.save()
        _registrar_auditoria(request, RegistroAuditoria.Acao.EDITAR, configuracao["singular"], objeto)
        messages.success(request, f"{configuracao['singular']} atualizado com sucesso.")
        return redirect(f"core_{entidade}_detalhe", pk=objeto.pk)
    return render(
        request,
        _obter_template(entidade, "formulario", "core/formulario.html"),
        {"configuracao": configuracao, "formulario": formulario, "objeto": objeto, "entidade": entidade},
    )


@login_admin_obrigatorio
def detalhe(request, entidade, pk):
    configuracao = _obter_configuracao(entidade)
    objeto = get_object_or_404(configuracao["modelo"], pk=pk)
    abas = {
        "profissionais": [("dados", "Dados Gerais"), ("permissoes", "Permissoes"), ("auditoria", "Auditoria")],
        "planos": [("geral", "Geral"), ("cobranca", "Cobranca"), ("limites", "Limites"), ("recursos", "Recursos"), ("auditoria", "Auditoria")],
        "empresas": [("visao", "Visao Geral"), ("assinatura", "Assinatura"), ("banco", "Banco"), ("auditoria", "Auditoria")],
        "fornecedores": [("resumo", "Resumo"), ("produtos", "Produtos"), ("auditoria", "Auditoria")],
        "produtos": [("resumo", "Resumo"), ("fornecedor", "Fornecedor"), ("auditoria", "Auditoria")],
        "servicos": [("resumo", "Resumo"), ("auditoria", "Auditoria")],
        "vendas": [("resumo", "Resumo"), ("receitas", "Receitas"), ("auditoria", "Auditoria")],
        "receitas": [("resumo", "Resumo"), ("conta", "Conta Financeira"), ("auditoria", "Auditoria")],
        "contas_pagar": [("resumo", "Resumo"), ("conta", "Conta Financeira"), ("auditoria", "Auditoria")],
        "contas_financeiras": [("resumo", "Resumo"), ("entradas", "Entradas"), ("saidas", "Saidas"), ("auditoria", "Auditoria")],
        "categorias": [("resumo", "Resumo"), ("auditoria", "Auditoria")],
        "subcategorias": [("resumo", "Resumo"), ("auditoria", "Auditoria")],
    }[entidade]
    aba_atual = request.GET.get("aba") or abas[0][0]
    auditorias = RegistroAuditoria.objects.filter(entidade=configuracao["singular"], objeto_id=objeto.pk)[:10]
    secoes_detalhe = _montar_secoes(objeto, configuracao.get("secoes_detalhe", []))

    if entidade == "profissionais":
        secoes_por_aba = {
            "dados": [secoes_detalhe[0], secoes_detalhe[1]],
            "permissoes": [("Permissoes", [("Status do perfil", getattr(objeto, "cargo", "-")), ("Acesso administrativo", "Placeholder MVP")])],
            "auditoria": [],
        }
    elif entidade == "planos":
        secoes_por_aba = {
            "geral": [secoes_detalhe[0]],
            "cobranca": [("Cobranca", [("Preco", objeto.preco), ("Ciclo", objeto.ciclo_cobranca), ("Ativo", objeto.ativo)])],
            "limites": [secoes_detalhe[1]],
            "recursos": [("Recursos", [("Configuracao JSON", objeto.recursos_json)])],
            "auditoria": [],
        }
    elif entidade == "empresas":
        secoes_por_aba = {"visao": [secoes_detalhe[0]], "assinatura": [secoes_detalhe[1]], "banco": [secoes_detalhe[2]], "auditoria": []}
    elif entidade == "fornecedores":
        ultimo = objeto.produtos.order_by("-criado_em").first()
        secoes_por_aba = {
            "resumo": [secoes_detalhe[0], secoes_detalhe[1]],
            "produtos": [("Produtos vinculados", [("Quantidade", objeto.produtos.count()), ("Ultimo cadastro", ultimo or "-")])],
            "auditoria": [],
        }
    elif entidade == "produtos":
        secoes_por_aba = {
            "resumo": [secoes_detalhe[0], secoes_detalhe[1]],
            "fornecedor": [("Fornecedor", [("Nome", objeto.fornecedor.nome), ("Contato", objeto.fornecedor.contato_principal or "-"), ("E-mail", objeto.fornecedor.email or "-")])],
            "auditoria": [],
        }
    elif entidade == "vendas":
        total_receitas = sum((item.valor for item in objeto.receitas.all()), Decimal("0"))
        secoes_por_aba = {
            "resumo": [secoes_detalhe[0], secoes_detalhe[1]],
            "receitas": [("Receitas vinculadas", [("Quantidade", objeto.receitas.count()), ("Total", total_receitas)])],
            "auditoria": [],
        }
    elif entidade == "receitas":
        secoes_por_aba = {
            "resumo": [secoes_detalhe[0], secoes_detalhe[1]],
            "conta": [
                (
                    "Conta Financeira",
                    [
                        ("Nome", objeto.conta_financeira.nome),
                        ("Instituicao", objeto.conta_financeira.instituicao or "-"),
                        ("Saldo inicial", objeto.conta_financeira.saldo_inicial),
                        ("Categoria", objeto.categoria),
                        ("Subcategoria", objeto.subcategoria),
                    ],
                )
            ],
            "auditoria": [],
        }
    elif entidade == "contas_pagar":
        secoes_por_aba = {
            "resumo": [secoes_detalhe[0], secoes_detalhe[1]],
            "conta": [
                (
                    "Conta Financeira",
                    [
                        ("Nome", objeto.conta_financeira.nome),
                        ("Instituicao", objeto.conta_financeira.instituicao or "-"),
                        ("Saldo inicial", objeto.conta_financeira.saldo_inicial),
                        ("Categoria", objeto.categoria),
                        ("Subcategoria", objeto.subcategoria),
                    ],
                )
            ],
            "auditoria": [],
        }
    elif entidade == "contas_financeiras":
        total_entradas = sum((item.valor for item in objeto.receitas.filter(ativo=True)), Decimal("0"))
        total_saidas = sum((item.valor for item in objeto.contas_pagar.filter(ativo=True)), Decimal("0"))
        ultima_entrada = objeto.receitas.order_by("-data_recebimento").first()
        ultima_saida = objeto.contas_pagar.order_by("-data_vencimento").first()
        secoes_por_aba = {
            "resumo": [
                secoes_detalhe[0],
                ("Saldo Atual", [("Entradas", total_entradas), ("Saidas", total_saidas), ("Saldo calculado", objeto.saldo_inicial + total_entradas - total_saidas)]),
            ],
            "entradas": [
                (
                    "Entradas registradas",
                    [
                        ("Quantidade", objeto.receitas.filter(ativo=True).count()),
                        ("Total", total_entradas),
                        ("Ultima categoria", ultima_entrada.categoria if ultima_entrada else "-"),
                        ("Ultima subcategoria", ultima_entrada.subcategoria if ultima_entrada else "-"),
                    ],
                )
            ],
            "saidas": [
                (
                    "Saidas registradas",
                    [
                        ("Quantidade", objeto.contas_pagar.filter(ativo=True).count()),
                        ("Total", total_saidas),
                        ("Ultima categoria", ultima_saida.categoria if ultima_saida else "-"),
                        ("Ultima subcategoria", ultima_saida.subcategoria if ultima_saida else "-"),
                    ],
                )
            ],
            "auditoria": [],
        }
    else:
        secoes_por_aba = {"resumo": [secoes_detalhe[0], secoes_detalhe[1]], "auditoria": []}

    contexto = {
        "configuracao": configuracao,
        "objeto": objeto,
        "abas": abas,
        "auditorias": auditorias,
        "entidade": entidade,
        "secoes_detalhe": secoes_por_aba.get(aba_atual, secoes_detalhe),
        "aba_atual": aba_atual,
    }
    template = (
        _obter_template(entidade, "detalhe_hx", "core/parciais/detalhe_conteudo.html")
        if request.headers.get("HX-Request")
        else _obter_template(entidade, "detalhe", "core/detalhe.html")
    )
    return render(request, template, contexto)


@login_admin_obrigatorio
def modal_exclusao(request, entidade, pk):
    configuracao = _obter_configuracao(entidade)
    objeto = get_object_or_404(configuracao["modelo"], pk=pk)
    return render(
        request,
        "componentes/modal_confirmacao.html",
        {
            "objeto": objeto,
            "entidade": entidade,
            "tenant_tipo": "central",
            "pode_excluir_permanente": getattr(request.usuario_admin, "perfil", "") == UsuarioAdmin.Perfil.SUPERADMIN,
        },
    )


@login_admin_obrigatorio
def excluir(request, entidade, pk):
    configuracao = _obter_configuracao(entidade)
    objeto = get_object_or_404(configuracao["modelo"], pk=pk)
    if request.method == "POST":
        setattr(objeto, configuracao["campo_ativo"], False)
        campos = [configuracao["campo_ativo"]]
        if hasattr(objeto, "atualizado_em"):
            campos.append("atualizado_em")
        objeto.save(update_fields=campos)
        _registrar_auditoria(request, RegistroAuditoria.Acao.INATIVAR, configuracao["singular"], objeto)
        messages.success(request, f"{configuracao['singular']} arquivado com sucesso.")
        if request.headers.get("HX-Request"):
            return HttpResponse("", headers={"HX-Redirect": reverse(f"core_{entidade}_lista")})
        return redirect(f"core_{entidade}_lista")
    return redirect(f"core_{entidade}_lista")


@login_admin_obrigatorio
def excluir_permanente(request, entidade, pk):
    configuracao = _obter_configuracao(entidade)
    if getattr(request.usuario_admin, "perfil", "") != UsuarioAdmin.Perfil.SUPERADMIN:
        messages.error(request, "Apenas superadmin pode excluir permanentemente.")
        return redirect(f"core_{entidade}_lista")
    objeto = get_object_or_404(configuracao["modelo"], pk=pk)
    confirmacao = request.POST.get("confirmacao_exclusao", "").strip()
    if request.method == "POST" and confirmacao == "EXCLUIR":
        objeto_id = objeto.pk
        objeto.delete()
        _registrar_auditoria(
            request,
            RegistroAuditoria.Acao.EXCLUIR,
            configuracao["singular"],
            dados={"objeto_id": objeto_id, "modo": "permanente"},
        )
        messages.success(request, f"{configuracao['singular']} excluido permanentemente.")
        if request.headers.get("HX-Request"):
            return HttpResponse("", headers={"HX-Redirect": reverse(f"core_{entidade}_lista")})
        return redirect(f"core_{entidade}_lista")
    messages.error(request, "Digite EXCLUIR para confirmar.")
    return redirect(f"core_{entidade}_lista")
