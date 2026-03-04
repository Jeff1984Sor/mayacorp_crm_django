from plataforma_saas.tenant import obter_slug_tenant, obter_tipo_tenant


def contexto_global(request):
    return {
        "tenant_slug": obter_slug_tenant(),
        "tenant_tipo": obter_tipo_tenant(),
        "usuario_admin_logado": getattr(request, "usuario_admin", None),
        "usuario_empresa_logado": getattr(request, "usuario_empresa", None),
    }
