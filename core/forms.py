from django import forms

from core.models import (
    CategoriaFinanceira,
    ContaFinanceira,
    ContaPagar,
    Empresa,
    Fornecedor,
    Plano,
    Produto,
    Profissional,
    Receita,
    Servico,
    SubcategoriaFinanceira,
    UsuarioAdmin,
    VendaCentral,
)


class FormularioBase(forms.ModelForm):
    class Meta:
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for nome, campo in self.fields.items():
            if isinstance(campo.widget, forms.CheckboxInput):
                campo.widget.attrs["class"] = "h-4 w-4 rounded border-slate-300 text-blue-600"
            else:
                campo.widget.attrs["class"] = "w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 outline-none focus:border-blue-400"
            if isinstance(campo.widget, forms.PasswordInput):
                campo.widget.attrs["autocomplete"] = "new-password"


class LoginAdminFormulario(forms.Form):
    email = forms.EmailField(label="E-mail")
    senha = forms.CharField(label="Senha", widget=forms.PasswordInput)
    lembrar_me = forms.BooleanField(label="Lembrar-me", required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for nome, campo in self.fields.items():
            campo.widget.attrs["class"] = (
                "h-4 w-4 rounded border-slate-300 text-blue-600"
                if nome == "lembrar_me"
                else "w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 outline-none focus:border-blue-400"
            )


class UsuarioAdminFormulario(forms.ModelForm):
    senha = forms.CharField(label="Senha", widget=forms.PasswordInput, required=False)

    class Meta:
        model = UsuarioAdmin
        fields = ["nome", "email", "senha", "perfil", "ativo"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for nome, campo in self.fields.items():
            campo.widget.attrs["class"] = (
                "h-4 w-4 rounded border-slate-300 text-blue-600"
                if nome == "ativo"
                else "w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 outline-none focus:border-blue-400"
            )

    def save(self, commit=True):
        instancia = super().save(commit=False)
        senha = self.cleaned_data.get("senha")
        if senha:
            instancia.definir_senha(senha)
        if commit:
            instancia.save()
        return instancia


class ProfissionalFormulario(FormularioBase):
    class Meta(FormularioBase.Meta):
        model = Profissional
        fields = ["nome_completo", "email", "telefone", "cargo", "ativo", "observacoes"]


class PlanoFormulario(FormularioBase):
    recursos_json = forms.JSONField(required=False)

    class Meta(FormularioBase.Meta):
        model = Plano
        fields = [
            "nome",
            "descricao",
            "preco",
            "ciclo_cobranca",
            "ativo",
            "limite_usuarios",
            "limite_registros",
            "recursos_json",
        ]


class EmpresaFormulario(FormularioBase):
    class Meta(FormularioBase.Meta):
        model = Empresa
        fields = [
            "nome",
            "slug",
            "documento",
            "email",
            "telefone",
            "ativo",
            "plano",
            "status_assinatura",
            "inicio_assinatura",
            "fim_teste",
            "motor_banco",
            "nome_banco",
            "usuario_banco",
            "senha_banco",
            "host_banco",
            "porta_banco",
        ]


class FornecedorFormulario(FormularioBase):
    class Meta(FormularioBase.Meta):
        model = Fornecedor
        fields = ["nome", "documento", "email", "telefone", "contato_principal", "ativo", "observacoes"]


class ProdutoFormulario(FormularioBase):
    class Meta(FormularioBase.Meta):
        model = Produto
        fields = ["nome", "sku", "fornecedor", "valor_custo", "valor_venda", "ativo", "observacoes"]


class ServicoFormulario(FormularioBase):
    class Meta(FormularioBase.Meta):
        model = Servico
        fields = ["nome", "descricao", "valor_custo", "valor_venda", "ativo"]


class ContaFinanceiraFormulario(FormularioBase):
    class Meta(FormularioBase.Meta):
        model = ContaFinanceira
        fields = ["nome", "instituicao", "saldo_inicial", "ativo", "observacoes"]


class CategoriaFinanceiraFormulario(FormularioBase):
    class Meta(FormularioBase.Meta):
        model = CategoriaFinanceira
        fields = ["nome", "ativo", "observacoes"]


class SubcategoriaFinanceiraFormulario(FormularioBase):
    class Meta(FormularioBase.Meta):
        model = SubcategoriaFinanceira
        fields = ["categoria", "nome", "ativo", "observacoes"]


class VendaCentralFormulario(FormularioBase):
    class Meta(FormularioBase.Meta):
        model = VendaCentral
        fields = ["titulo", "cliente", "data_venda", "status", "valor_bruto", "desconto", "ativo", "observacoes"]


class ReceitaFormulario(FormularioBase):
    class Meta(FormularioBase.Meta):
        model = Receita
        fields = [
            "descricao",
            "venda",
            "conta_financeira",
            "categoria",
            "subcategoria",
            "data_recebimento",
            "valor",
            "status",
            "ativo",
            "observacoes",
        ]


class ContaPagarFormulario(FormularioBase):
    class Meta(FormularioBase.Meta):
        model = ContaPagar
        fields = [
            "descricao",
            "fornecedor",
            "conta_financeira",
            "categoria",
            "subcategoria",
            "data_vencimento",
            "valor",
            "status",
            "ativo",
            "observacoes",
        ]
