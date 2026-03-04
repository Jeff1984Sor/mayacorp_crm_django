# Plataforma SaaS

Projeto Django 5.x com `core` (Admin Central) e `crm` (Portal da Empresa), usando Django Templates, HTMX, Tailwind CDN e Alpine.js CDN.

## Requisitos

- Python 3.12
- pip

## Instalação

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Como rodar

```bash
python manage.py migrate
python manage.py seed
python manage.py runserver
```

## Subdomínios locais

Adicione no arquivo `hosts`:

```txt
127.0.0.1 admin.localhost
127.0.0.1 empresa.localhost
```

## Acesso

- Admin Central: `http://admin.localhost:8000/login`
- Portal da Empresa: `http://empresa.localhost:8000/login`

## Credenciais de teste

- Admin Central
  - usuário: `admin@local`
  - senha: `admin123`
- Portal da Empresa
  - usuário: `dono@empresa`
  - senha: `empresa123`

## Estrutura

- `core`: autenticação do admin central, dashboard, profissionais, planos, empresas e auditoria.
- `crm`: autenticação do tenant, dashboard, profissionais, clientes, produtos, serviços, vendas e itens de venda.
- `plataforma_saas`: configuração, roteamento e middleware multi-tenant por subdomínio.

## Multi-tenant

- Banco `default`: dados centrais do `core`.
- Banco do tenant: carregado dinamicamente pelo subdomínio.
- No MVP com SQLite, cada empresa usa um arquivo como `tenant_empresa.sqlite3`.
- A empresa demo criada pelo seed usa o slug `empresa`.

## Migrations

As migrations já estão incluídas em:

- `core/migrations`
- `crm/migrations`

Para recriar:

```bash
python manage.py makemigrations core crm
python manage.py migrate
```

## Seed

O comando abaixo cria:

- 1 `UsuarioAdmin`
- 3 `Plano`
- 1 `Empresa` demo
- banco SQLite do tenant demo
- 1 `UsuarioEmpresa`
- dados de exemplo de CRM

```bash
python manage.py seed
```

## Regras importantes

- Exclusão padrão é arquivamento/inativação.
- `SUPERADMIN` pode fazer exclusão permanente digitando `EXCLUIR` no modal de confirmação.
- Em vendas, cancelar substitui exclusão física.
- Cliente com vendas é apenas inativado.
- O `crm` mantém auditoria de login, criação, edição, inativação, cancelamento e itens de venda.

## Postgres por tenant

O campo `motor_banco` da `Empresa` aceita `sqlite` ou `postgres`. Quando estiver em `postgres`, o middleware monta o alias dinâmico usando:

- `nome_banco`
- `usuario_banco`
- `senha_banco`
- `host_banco`
- `porta_banco`

Para usar Postgres real, instale as dependências e preencha esses campos no cadastro da empresa.
