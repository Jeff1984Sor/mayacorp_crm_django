from django.contrib.auth.hashers import check_password, make_password
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class ModeloTemporal(models.Model):
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UsuarioAdmin(models.Model):
    class Perfil(models.TextChoices):
        SUPERADMIN = "SUPERADMIN", "Superadmin"
        SUPORTE = "SUPORTE", "Suporte"
        FINANCEIRO = "FINANCEIRO", "Financeiro"
        COMERCIAL = "COMERCIAL", "Comercial"

    nome = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    senha = models.CharField(max_length=255)
    perfil = models.CharField(max_length=20, choices=Perfil.choices, default=Perfil.SUPORTE)
    ativo = models.BooleanField(default=True)
    ultimo_login = models.DateTimeField(null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    def definir_senha(self, senha_plana):
        self.senha = make_password(senha_plana)

    def validar_senha(self, senha_plana):
        return check_password(senha_plana, self.senha)

    def registrar_login(self):
        self.ultimo_login = timezone.now()
        self.save(update_fields=["ultimo_login"])

    def __str__(self):
        return self.nome


class Profissional(ModeloTemporal):
    class Cargo(models.TextChoices):
        SUPORTE = "SUPORTE", "Suporte"
        COMERCIAL = "COMERCIAL", "Comercial"
        FINANCEIRO = "FINANCEIRO", "Financeiro"
        ADMINISTRADOR = "ADMINISTRADOR", "Administrador"

    nome_completo = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    telefone = models.CharField(max_length=30, blank=True)
    cargo = models.CharField(max_length=20, choices=Cargo.choices)
    ativo = models.BooleanField(default=True)
    observacoes = models.TextField(blank=True)

    def __str__(self):
        return self.nome_completo


class Plano(ModeloTemporal):
    class CicloCobranca(models.TextChoices):
        MENSAL = "MENSAL", "Mensal"
        TRIMESTRAL = "TRIMESTRAL", "Trimestral"
        SEMESTRAL = "SEMESTRAL", "Semestral"
        ANUAL = "ANUAL", "Anual"

    nome = models.CharField(max_length=120)
    descricao = models.TextField(blank=True)
    preco = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    ciclo_cobranca = models.CharField(max_length=20, choices=CicloCobranca.choices)
    ativo = models.BooleanField(default=True)
    limite_usuarios = models.PositiveIntegerField(default=1)
    limite_registros = models.PositiveIntegerField(default=100)
    recursos_json = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return self.nome


class Empresa(ModeloTemporal):
    class StatusAssinatura(models.TextChoices):
        ATIVA = "ATIVA", "Ativa"
        SUSPENSA = "SUSPENSA", "Suspensa"
        CANCELADA = "CANCELADA", "Cancelada"
        TESTE = "TESTE", "Teste"

    nome = models.CharField(max_length=150)
    slug = models.SlugField(unique=True)
    documento = models.CharField(max_length=30, blank=True)
    email = models.EmailField()
    telefone = models.CharField(max_length=30, blank=True)
    ativo = models.BooleanField(default=True)
    plano = models.ForeignKey(Plano, on_delete=models.PROTECT, related_name="empresas")
    status_assinatura = models.CharField(max_length=20, choices=StatusAssinatura.choices, default=StatusAssinatura.TESTE)
    inicio_assinatura = models.DateField(null=True, blank=True)
    fim_teste = models.DateField(null=True, blank=True)
    nome_banco = models.CharField(max_length=200, blank=True)
    usuario_banco = models.CharField(max_length=120, blank=True)
    senha_banco = models.CharField(max_length=200, blank=True)
    host_banco = models.CharField(max_length=120, blank=True)
    porta_banco = models.CharField(max_length=20, blank=True)
    motor_banco = models.CharField(max_length=20, default="sqlite", blank=True)

    def __str__(self):
        return self.nome


class RegistroAuditoria(models.Model):
    class Acao(models.TextChoices):
        CRIAR = "CRIAR", "Criar"
        EDITAR = "EDITAR", "Editar"
        EXCLUIR = "EXCLUIR", "Excluir"
        ATIVAR = "ATIVAR", "Ativar"
        INATIVAR = "INATIVAR", "Inativar"
        LOGIN = "LOGIN", "Login"

    usuario_admin = models.ForeignKey(UsuarioAdmin, on_delete=models.SET_NULL, null=True, blank=True)
    acao = models.CharField(max_length=20, choices=Acao.choices)
    entidade = models.CharField(max_length=120)
    objeto_id = models.PositiveBigIntegerField(null=True, blank=True)
    ip = models.CharField(max_length=60, blank=True)
    data = models.DateTimeField(auto_now_add=True)
    dados_json = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-data"]

    def __str__(self):
        return f"{self.entidade} - {self.acao}"
