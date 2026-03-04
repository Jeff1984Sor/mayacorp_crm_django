from pathlib import Path

from django.core.management import call_command
from django.db import ProgrammingError, connections

from crm.models import Cliente, ItemVenda, Produto, ProfissionalEmpresa, RegistroAuditoriaEmpresa, Servico, UsuarioEmpresa, Venda
from plataforma_saas.banco_tenant import configuracao_banco_empresa


MODELOS_TENANT = [Produto, ProfissionalEmpresa, Servico, UsuarioEmpresa, Cliente, Venda, ItemVenda, RegistroAuditoriaEmpresa]


def provisionar_tenant(empresa):
    alias = f"tenant_{empresa.slug}"
    if alias not in connections.databases:
        connections.databases[alias] = configuracao_banco_empresa(empresa)
    configuracao = connections.databases[alias]
    if "postgresql" in configuracao["ENGINE"]:
        _garantir_banco_postgres(configuracao)
    else:
        caminho = Path(configuracao["NAME"])
        if not caminho.exists():
            caminho.touch()
    _garantir_tabelas_tenant(alias)
    return alias


def _garantir_banco_postgres(configuracao):
    base_admin = configuracao.copy()
    base_admin["NAME"] = "postgres"
    alias_admin = "__provisionamento_postgres__"
    connections.databases[alias_admin] = base_admin
    conexao = connections[alias_admin]
    nome_banco = configuracao["NAME"]
    with conexao.cursor() as cursor:
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", [nome_banco])
        existe = cursor.fetchone()
        if not existe:
            cursor.execute(f'CREATE DATABASE "{nome_banco}"')
    connections.close_all()


def _garantir_tabelas_tenant(alias):
    try:
        call_command("migrate", database=alias, interactive=False, verbosity=0)
    except Exception:
        pass
    conexao = connections[alias]
    try:
        tabelas = set(conexao.introspection.table_names())
    except ProgrammingError:
        tabelas = set()
    with conexao.schema_editor() as editor:
        for modelo in MODELOS_TENANT:
            if modelo._meta.db_table not in tabelas:
                editor.create_model(modelo)
                tabelas.add(modelo._meta.db_table)
