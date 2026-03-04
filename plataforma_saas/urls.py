from django.urls import include, path

from plataforma_saas import views

urlpatterns = [
    path("login", views.login_dispatch, name="login"),
    path("logout", views.logout_dispatch, name="logout"),
    path("", include("core.urls_publicas")),
    path("", include("crm.urls_publicas")),
]
