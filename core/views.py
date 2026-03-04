import csv

from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from core.autenticacao import login_admin_obrigatorio
from core.forms import EmpresaFormulario, LoginAdminFormulario, PlanoFormulario, ProfissionalFormulario
from core.models import Empresa, Plano, Profissional, RegistroAuditoria, UsuarioAdmin


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
            ("Observações", ["observacoes", "criado_em", "atualizado_em"]),
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
            ("Identificação", ["nome", "slug", "documento", "email", "telefone"]),
            ("Assinatura", ["ativo", "plano", "status_assinatura", "inicio_assinatura", "fim_teste"]),
            ("Banco de Dados", ["motor_banco", "nome_banco", "usuario_banco", "senha_banco", "host_banco", "porta_banco"]),
        ],
        "secoes_detalhe": [
            ("Visão Geral", ["nome", "slug", "documento", "email", "telefone", "ativo"]),
            ("Assinatura", ["plano", "status_assinatura", "inicio_assinatura", "fim_teste"]),
            ("Banco", ["motor_banco", "nome_banco", "usuario_banco", "host_banco", "porta_banco", "criado_em", "atualizado_em"]),
        ],
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
            if formulario.cleaned_data["lembrar_me"]:
                request.session.set_expiry(60 * 60 * 24 * 30)
            else:
                request.session.set_expiry(0)
            usuario.registrar_login()
            _registrar_auditoria(request, RegistroAuditoria.Acao.LOGIN, "UsuarioAdmin", usuario)
            return redirect("core_dashboard")
        messages.error(request, "Credenciais inválidas.")
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
    if ordem.lstrip("-") in [c[0] for c in configuracao["colunas"]]:
        queryset = queryset.order_by(ordem)
    return queryset, busca, status, ordem


@login_admin_obrigatorio
def listagem(request, entidade):
    configuracao = _obter_configuracao(entidade)
    queryset = configuracao["modelo"].objects.all()
    queryset, busca, status, ordem = _filtrar_listagem(request, queryset, configuracao)
    pagina = Paginator(queryset, 10).get_page(request.GET.get("pagina"))
    contexto = {
        "configuracao": configuracao,
        "entidade": entidade,
        "pagina": pagina,
        "busca": busca,
        "status": status,
        "ordem": ordem,
    }
    template = "core/parciais/listagem_conteudo.html" if request.headers.get("HX-Request") else "core/listagem.html"
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
    return render(request, "core/formulario.html", {"configuracao": configuracao, "formulario": formulario, "entidade": entidade})


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
        "core/formulario.html",
        {"configuracao": configuracao, "formulario": formulario, "objeto": objeto, "entidade": entidade},
    )


@login_admin_obrigatorio
def detalhe(request, entidade, pk):
    configuracao = _obter_configuracao(entidade)
    objeto = get_object_or_404(configuracao["modelo"], pk=pk)
    abas = {
        "profissionais": [
            ("dados", "Dados Gerais"),
            ("permissoes", "Permissões"),
            ("auditoria", "Auditoria"),
        ],
        "planos": [
            ("geral", "Geral"),
            ("cobranca", "Cobrança"),
            ("limites", "Limites"),
            ("recursos", "Recursos"),
            ("auditoria", "Auditoria"),
        ],
        "empresas": [
            ("visao", "Visão Geral"),
            ("assinatura", "Assinatura"),
            ("banco", "Banco"),
            ("auditoria", "Auditoria"),
        ],
    }[entidade]
    aba_atual = request.GET.get("aba") or abas[0][0]
    auditorias = RegistroAuditoria.objects.filter(entidade=configuracao["singular"], objeto_id=objeto.pk)[:10]
    secoes_detalhe = _montar_secoes(objeto, configuracao.get("secoes_detalhe", []))
    if entidade == "profissionais":
        secoes_por_aba = {
            "dados": [secoes_detalhe[0], secoes_detalhe[1]],
            "permissoes": [("Permissões", [("Status do perfil", getattr(objeto, "cargo", "-")), ("Acesso administrativo", "Placeholder MVP")])],
            "auditoria": [],
        }
    elif entidade == "planos":
        secoes_por_aba = {
            "geral": [secoes_detalhe[0]],
            "cobranca": [("Cobrança", [("Preço", objeto.preco), ("Ciclo", objeto.ciclo_cobranca), ("Ativo", objeto.ativo)])],
            "limites": [secoes_detalhe[1]],
            "recursos": [("Recursos", [("Configuração JSON", objeto.recursos_json)])],
            "auditoria": [],
        }
    else:
        secoes_por_aba = {
            "visao": [secoes_detalhe[0]],
            "assinatura": [secoes_detalhe[1]],
            "banco": [secoes_detalhe[2]],
            "auditoria": [],
        }
    contexto = {
        "configuracao": configuracao,
        "objeto": objeto,
        "abas": abas,
        "auditorias": auditorias,
        "entidade": entidade,
        "secoes_detalhe": secoes_por_aba.get(aba_atual, secoes_detalhe),
        "aba_atual": aba_atual,
    }
    template = "core/parciais/detalhe_conteudo.html" if request.headers.get("HX-Request") else "core/detalhe.html"
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
        objeto.save(update_fields=[configuracao["campo_ativo"], "atualizado_em"] if hasattr(objeto, "atualizado_em") else [configuracao["campo_ativo"]])
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
        messages.success(request, f"{configuracao['singular']} excluído permanentemente.")
        if request.headers.get("HX-Request"):
            return HttpResponse("", headers={"HX-Redirect": reverse(f"core_{entidade}_lista")})
        return redirect(f"core_{entidade}_lista")
    messages.error(request, "Digite EXCLUIR para confirmar.")
    return redirect(f"core_{entidade}_lista")
