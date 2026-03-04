from django.urls import path

from core import views

urlpatterns = [
    path("acesso-admin", views.login, name="core_login"),
    path("sair-admin", views.logout, name="core_logout"),
    path("admin", views.dashboard, name="core_dashboard"),
    path("admin/auditoria", views.auditoria, name="core_auditoria"),
    path("admin/profissionais", views.listagem, {"entidade": "profissionais"}, name="core_profissionais_lista"),
    path("admin/profissionais/novo", views.criar, {"entidade": "profissionais"}, name="core_profissionais_novo"),
    path("admin/profissionais/<int:pk>", views.detalhe, {"entidade": "profissionais"}, name="core_profissionais_detalhe"),
    path("admin/profissionais/<int:pk>/editar", views.editar, {"entidade": "profissionais"}, name="core_profissionais_editar"),
    path("admin/profissionais/<int:pk>/modal-excluir", views.modal_exclusao, {"entidade": "profissionais"}, name="core_profissionais_modal_excluir"),
    path("admin/profissionais/<int:pk>/excluir", views.excluir, {"entidade": "profissionais"}, name="core_profissionais_excluir"),
    path("admin/profissionais/<int:pk>/excluir-permanente", views.excluir_permanente, {"entidade": "profissionais"}, name="core_profissionais_excluir_permanente"),
    path("admin/planos", views.listagem, {"entidade": "planos"}, name="core_planos_lista"),
    path("admin/planos/novo", views.criar, {"entidade": "planos"}, name="core_planos_novo"),
    path("admin/planos/<int:pk>", views.detalhe, {"entidade": "planos"}, name="core_planos_detalhe"),
    path("admin/planos/<int:pk>/editar", views.editar, {"entidade": "planos"}, name="core_planos_editar"),
    path("admin/planos/<int:pk>/modal-excluir", views.modal_exclusao, {"entidade": "planos"}, name="core_planos_modal_excluir"),
    path("admin/planos/<int:pk>/excluir", views.excluir, {"entidade": "planos"}, name="core_planos_excluir"),
    path("admin/planos/<int:pk>/excluir-permanente", views.excluir_permanente, {"entidade": "planos"}, name="core_planos_excluir_permanente"),
    path("admin/empresas", views.listagem, {"entidade": "empresas"}, name="core_empresas_lista"),
    path("admin/empresas/nova", views.criar, {"entidade": "empresas"}, name="core_empresas_novo"),
    path("admin/empresas/<int:pk>", views.detalhe, {"entidade": "empresas"}, name="core_empresas_detalhe"),
    path("admin/empresas/<int:pk>/editar", views.editar, {"entidade": "empresas"}, name="core_empresas_editar"),
    path("admin/empresas/<int:pk>/modal-excluir", views.modal_exclusao, {"entidade": "empresas"}, name="core_empresas_modal_excluir"),
    path("admin/empresas/<int:pk>/excluir", views.excluir, {"entidade": "empresas"}, name="core_empresas_excluir"),
    path("admin/empresas/<int:pk>/excluir-permanente", views.excluir_permanente, {"entidade": "empresas"}, name="core_empresas_excluir_permanente"),
]
