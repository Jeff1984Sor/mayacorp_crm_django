from django import forms
from django.core.exceptions import ValidationError

from crm.models import Cliente, ItemVenda, Produto, ProfissionalEmpresa, Servico, UsuarioEmpresa, Venda


class LoginEmpresaFormulario(forms.Form):
    email = forms.EmailField(label="E-mail")
    senha = forms.CharField(label="Senha", widget=forms.PasswordInput)
    lembrar_me = forms.BooleanField(label="Lembrar-me", required=False)


class UsuarioEmpresaFormulario(forms.ModelForm):
    senha = forms.CharField(label="Senha", widget=forms.PasswordInput, required=False)

    class Meta:
        model = UsuarioEmpresa
        fields = ["nome", "email", "senha", "perfil", "ativo"]

    def save(self, commit=True):
        instancia = super().save(commit=False)
        senha = self.cleaned_data.get("senha")
        if senha:
            instancia.definir_senha(senha)
        if commit:
            instancia.save()
        return instancia


class ProfissionalEmpresaFormulario(forms.ModelForm):
    class Meta:
        model = ProfissionalEmpresa
        fields = ["nome_completo", "email", "telefone", "funcao", "ativo", "observacoes"]


class ClienteFormulario(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = [
            "nome",
            "documento",
            "email",
            "telefone",
            "status",
            "responsavel_usuario",
            "responsavel_profissional",
            "ativo",
        ]


class ProdutoFormulario(forms.ModelForm):
    class Meta:
        model = Produto
        fields = ["nome", "sku", "preco", "ativo"]


class ServicoFormulario(forms.ModelForm):
    class Meta:
        model = Servico
        fields = ["nome", "preco", "ativo"]


class VendaFormulario(forms.ModelForm):
    class Meta:
        model = Venda
        fields = [
            "cliente",
            "vendedor_usuario",
            "vendedor_profissional",
            "data",
            "status",
            "desconto",
            "observacoes",
        ]

    def clean(self):
        dados = super().clean()
        if self.instance.pk and not self.instance.pode_editar() and dados.get("status") != Venda.Status.CANCELADA:
            raise ValidationError("Venda fechada não pode ser editada.")
        return dados


class ItemVendaFormulario(forms.ModelForm):
    class Meta:
        model = ItemVenda
        fields = ["tipo_item", "produto", "servico", "quantidade", "valor_unitario"]
