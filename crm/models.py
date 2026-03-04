from decimal import Decimal

from django.contrib.auth.hashers import check_password, make_password
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class ModeloTemporal(models.Model):
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UsuarioEmpresa(models.Model):
    class Perfil(models.TextChoices):
        ADMIN = "ADMIN", "Administrador"
        GERENTE = "GERENTE", "Gerente"
        VENDEDOR = "VENDEDOR", "Vendedor"
        FINANCEIRO = "FINANCEIRO", "Financeiro"

    nome = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    senha = models.CharField(max_length=255)
    perfil = models.CharField(max_length=20, choices=Perfil.choices, default=Perfil.VENDEDOR)
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


class ProfissionalEmpresa(ModeloTemporal):
    nome_completo = models.CharField(max_length=150)
    email = models.EmailField(blank=True)
    telefone = models.CharField(max_length=30, blank=True)
    funcao = models.CharField(max_length=120, blank=True)
    ativo = models.BooleanField(default=True)
    observacoes = models.TextField(blank=True)

    def __str__(self):
        return self.nome_completo


class Cliente(ModeloTemporal):
    class Status(models.TextChoices):
        LEAD = "LEAD", "Lead"
        PROSPECT = "PROSPECT", "Prospect"
        CLIENTE = "CLIENTE", "Cliente"
        PERDIDO = "PERDIDO", "Perdido"

    nome = models.CharField(max_length=150)
    documento = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    telefone = models.CharField(max_length=30, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.LEAD)
    responsavel_usuario = models.ForeignKey(UsuarioEmpresa, on_delete=models.SET_NULL, null=True, blank=True)
    responsavel_profissional = models.ForeignKey(ProfissionalEmpresa, on_delete=models.SET_NULL, null=True, blank=True)
    ativo = models.BooleanField(default=True)

    def __str__(self):
        return self.nome


class Produto(ModeloTemporal):
    nome = models.CharField(max_length=150)
    sku = models.CharField(max_length=60, unique=True)
    preco = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    ativo = models.BooleanField(default=True)

    def __str__(self):
        return self.nome


class Servico(ModeloTemporal):
    nome = models.CharField(max_length=150)
    preco = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    ativo = models.BooleanField(default=True)

    def __str__(self):
        return self.nome


class Venda(ModeloTemporal):
    class Status(models.TextChoices):
        RASCUNHO = "RASCUNHO", "Rascunho"
        FECHADA = "FECHADA", "Fechada"
        CANCELADA = "CANCELADA", "Cancelada"

    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name="vendas")
    vendedor_usuario = models.ForeignKey(UsuarioEmpresa, on_delete=models.SET_NULL, null=True, blank=True)
    vendedor_profissional = models.ForeignKey(ProfissionalEmpresa, on_delete=models.SET_NULL, null=True, blank=True)
    data = models.DateField(default=timezone.localdate)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.RASCUNHO)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    desconto = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    observacoes = models.TextField(blank=True)

    def recalcular_totais(self):
        alias = self._state.db or "default"
        subtotal = sum((item.total for item in self.itens.using(alias).all()), Decimal("0"))
        self.subtotal = subtotal
        self.total = subtotal - (self.desconto or Decimal("0"))
        self.save(using=alias, update_fields=["subtotal", "total", "atualizado_em"])

    def pode_editar(self):
        return self.status == self.Status.RASCUNHO

    def __str__(self):
        return f"Venda #{self.pk}"


class ItemVenda(models.Model):
    class TipoItem(models.TextChoices):
        PRODUTO = "PRODUTO", "Produto"
        SERVICO = "SERVICO", "Servico"

    venda = models.ForeignKey(Venda, on_delete=models.CASCADE, related_name="itens")
    tipo_item = models.CharField(max_length=20, choices=TipoItem.choices)
    produto = models.ForeignKey(Produto, on_delete=models.PROTECT, null=True, blank=True)
    servico = models.ForeignKey(Servico, on_delete=models.PROTECT, null=True, blank=True)
    quantidade = models.PositiveIntegerField(default=1)
    valor_unitario = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def clean(self):
        if self.tipo_item == self.TipoItem.PRODUTO and not self.produto:
            raise ValidationError("Selecione um produto.")
        if self.tipo_item == self.TipoItem.SERVICO and not self.servico:
            raise ValidationError("Selecione um serviço.")
        if self.tipo_item == self.TipoItem.PRODUTO and self.servico:
            raise ValidationError("Item de produto não pode ter serviço.")
        if self.tipo_item == self.TipoItem.SERVICO and self.produto:
            raise ValidationError("Item de serviço não pode ter produto.")

    def save(self, *args, **kwargs):
        alias = kwargs.get("using") or self._state.db
        self.total = (self.quantidade or 0) * (self.valor_unitario or Decimal("0"))
        super().save(*args, **kwargs)
        venda = Venda.objects.using(alias or "default").get(pk=self.venda_id)
        venda.recalcular_totais()

    def delete(self, *args, **kwargs):
        alias = kwargs.get("using") or self._state.db
        venda = Venda.objects.using(alias or "default").get(pk=self.venda_id)
        super().delete(*args, **kwargs)
        venda.recalcular_totais()

    def __str__(self):
        return f"Item {self.pk}"


class RegistroAuditoriaEmpresa(models.Model):
    class Acao(models.TextChoices):
        CRIAR = "CRIAR", "Criar"
        EDITAR = "EDITAR", "Editar"
        EXCLUIR = "EXCLUIR", "Excluir"
        INATIVAR = "INATIVAR", "Inativar"
        LOGIN = "LOGIN", "Login"
        CANCELAR = "CANCELAR", "Cancelar"

    usuario_empresa = models.ForeignKey(UsuarioEmpresa, on_delete=models.SET_NULL, null=True, blank=True)
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
