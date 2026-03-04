from threading import local

estado_tenant = local()


def definir_tenant(slug=None, alias="default", tipo="central"):
    estado_tenant.slug = slug
    estado_tenant.alias = alias
    estado_tenant.tipo = tipo


def obter_alias_banco():
    return getattr(estado_tenant, "alias", "default")


def obter_tipo_tenant():
    return getattr(estado_tenant, "tipo", "central")


def obter_slug_tenant():
    return getattr(estado_tenant, "slug", None)
