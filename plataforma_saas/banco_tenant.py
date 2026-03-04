from pathlib import Path

from django.conf import settings
from django.db import connections


def configuracao_banco_empresa(empresa):
    motor = (empresa.motor_banco or "sqlite").lower()
    if motor in {"postgres", "postgresql", "postgre"}:
        configuracao = connections.databases["default"].copy()
        configuracao.update(
            {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": empresa.nome_banco,
                "USER": empresa.usuario_banco,
                "PASSWORD": empresa.senha_banco,
                "HOST": empresa.host_banco or "localhost",
                "PORT": empresa.porta_banco or "5432",
            }
        )
        return configuracao

    nome_arquivo = empresa.nome_banco or f"tenant_{empresa.slug}.sqlite3"
    caminho = Path(nome_arquivo)
    if not caminho.is_absolute():
        caminho = settings.BASE_DIR / nome_arquivo
    configuracao = connections.databases["default"].copy()
    configuracao["ENGINE"] = "django.db.backends.sqlite3"
    configuracao["NAME"] = caminho
    return configuracao
