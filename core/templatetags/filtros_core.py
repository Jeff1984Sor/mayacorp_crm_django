from django import template

register = template.Library()


@register.filter
def obter_atributo(objeto, caminho):
    valor = objeto
    for parte in caminho.split("__"):
        valor = getattr(valor, parte, "")
        if callable(valor):
            valor = valor()
    return valor


@register.simple_tag
def nome_rota(tenant_tipo, entidade, acao):
    prefixo = "core" if tenant_tipo == "central" else "crm"
    return f"{prefixo}_{entidade}_{acao}"


@register.filter
def campos_modelo(objeto):
    campos = []
    for campo in objeto._meta.fields:
        campos.append((campo.verbose_name or campo.name, getattr(objeto, campo.name)))
    return campos


@register.filter
def campo_formulario(formulario, nome_campo):
    return formulario[nome_campo]
