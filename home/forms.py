from datetime import datetime, date

from Alugue_seu_imovel import settings

from django import forms

from django.contrib.auth.forms import UserCreationForm
from crispy_forms.bootstrap import InlineCheckboxes
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout

from home.models import Usuario, MensagemDev
from home.models import Pagamento, Gasto, Locatario, Contrato, Imovei, Anotacoe, ImovGrupo


class Textarea(forms.Textarea):
    input_type = 'text'


class DateInput(forms.DateInput):
    input_type = 'date'


class Numeros(forms.NumberInput):
    input_type = 'numbers'


class FormCriarConta(UserCreationForm):
    class Meta:
        model = Usuario
        fields = ['username', 'email', 'telefone', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super(FormCriarConta, self).__init__(*args, **kwargs)
        self.fields['telefone'].widget.attrs['class'] = 'mask-telefone1'


class FormUsuario(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ['username', 'password', 'first_name', 'last_name', 'email', 'telefone', 'RG', 'CPF']


class FormEventos(forms.Form):
    mostrar_em_eventos = [
        (1, 'Pagamentos'),
        (2, 'Gastos'),
        (3, 'Locatarios'),
        (4, 'Contratos'),
        (5, 'Imóveis'),
        (6, 'Anotações'),
    ]

    ordem_em_eventos = [
        (1, 'Recentes primeiro'),
        (2, 'Antigos primeiro'),
    ]

    data_eventos_i = forms.DateField(label='A partir de',
                                     widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control-sm'}))

    data_eventos_f = forms.DateField(label='Até', initial=date.today().strftime('%Y-%m-%d'), widget=forms.DateInput(
        attrs={'type': 'date', 'class': 'form-control-sm', 'max': datetime.now().date()}))

    qtd = forms.IntegerField(label='Qtd', max_value=50, min_value=5, step_size=5, initial=10,
                             widget=forms.NumberInput(attrs={'class': 'form-control-sm'}))

    ordem_eventos = forms.ChoiceField(label='Ordem', initial=1, choices=ordem_em_eventos,
                                      widget=forms.RadioSelect())

    itens_eventos = forms.MultipleChoiceField(label='Selecione os itens', choices=mostrar_em_eventos,
                                              initial=[1, 2, 3, 4, 5, 6],
                                              widget=forms.CheckboxSelectMultiple(
                                                  attrs={'choices': mostrar_em_eventos}))

    def __init__(self, *args, **kwargs):
        super(FormEventos, self).__init__(*args, **kwargs)
        self.fields['qtd'].widget.attrs.update(style="width: 65px;")
        self.helper = FormHelper()
        self.helper.layout = Layout(
            InlineCheckboxes('itens_eventos'),
        )


class FormHomePage(forms.Form):
    email = forms.EmailField(label=False)


class FormMensagem(forms.ModelForm):
    class Meta:
        model = MensagemDev
        fields = '__all__'
        exclude = ['do_usuario', 'data_criacao']
        widgets = {
            'mensagem': Textarea(),
        }


class Mascara(forms.ModelForm):
    class Media:
        js = ('js/jquery.mask.min.js', 'js/custom.js')

    def __init__(self, *args, **kwargs):
        super(Mascara, self).__init__(*args, **kwargs)
        self.fields['telefone1'].widget.attrs['class'] = 'mask-telefone1'
        self.fields['telefone2'].widget.attrs['class'] = 'mask-telefone2'
        self.fields['CPF'].widget.attrs['class'] = 'mask-cpf'


class FormPagamento(forms.ModelForm):
    class Meta:
        model = Pagamento
        fields = '__all__'
        exclude = ['ao_locador', 'do_locatario', 'data_de_recibo', 'data_criacao']
        widgets = {
            'data_pagamento': DateInput(),
            'valor_pago': Numeros(),
        }

    def __init__(self, user, *args, **kwargs):
        super(FormPagamento, self).__init__(*args, **kwargs)
        self.fields['ao_contrato'].queryset = Contrato.objects.filter(do_locador=user)
        self.fields['valor_pago'].widget.attrs.update({'class': 'mask-valor'})


class FormGasto(forms.ModelForm):
    class Meta:
        model = Gasto
        fields = '__all__'
        exclude = ['do_locador', 'data_criacao']
        widgets = {
            'observacoes': Textarea(attrs={'cols': 100, 'rows': 12}),
            'data': DateInput(),
            'valor': Numeros(),
        }

    def __init__(self, *args, **kwargs):
        super(FormGasto, self).__init__(*args, **kwargs)
        self.fields['valor'].widget.attrs['class'] = 'mask-valor'


class FormLocatario(forms.ModelForm):
    class Meta:
        model = Locatario
        fields = '__all__'
        exclude = ['do_locador', 'dataentrada', 'com_imoveis', 'com_contratos', 'data_registro']

    def __init__(self, *args, **kwargs):
        super(FormLocatario, self).__init__(*args, **kwargs)
        self.fields['CPF'].widget.attrs.update({'class': 'mask-cpf'})
        self.fields['telefone1'].widget.attrs.update({'class': 'mask-telefone1'})
        self.fields['telefone2'].widget.attrs.update({'class': 'mask-telefone2'})


class FormContrato(forms.ModelForm):
    class Meta:
        model = Contrato
        fields = '__all__'
        exclude = ['do_locador', 'em_posse', 'rescindido', 'vencido', 'codigo', 'data_de_rescisao', 'recibos_pdf',
                   'data_registro']
        widgets = {
            'data_entrada': DateInput(),
            'duracao': Numeros(),
            'valor_mensal': Numeros(),
            'dia_vencimento': Numeros(),
        }

    def __init__(self, user, *args, **kwargs):
        super(FormContrato, self).__init__(*args, **kwargs)
        self.fields['do_locatario'].queryset = Locatario.objects.filter(do_locador=user)
        self.fields['do_imovel'].queryset = Imovei.objects.disponiveis().filter(do_locador=user)
        self.fields['valor_mensal'].widget.attrs.update({'class': 'mask-valor'})


class FormimovelGrupo(forms.ModelForm):
    class Meta:
        model = ImovGrupo
        fields = '__all__'
        exclude = ['imoveis', 'do_usuario']
        labels = {
            "nome": ""}


class FormImovel(forms.ModelForm):
    class Meta:
        model = Imovei
        fileds = '__all__'
        exclude = ['do_locador', 'com_locatario', 'contrato_atual', 'data_registro']

    def __init__(self, user, *args, **kwargs):
        super(FormImovel, self).__init__(*args, **kwargs)
        self.fields['grupo'].queryset = ImovGrupo.objects.filter(do_usuario=user)
        self.fields['cep'].widget.attrs.update({'class': 'mask-cep'})
        self.fields['cep'].widget.attrs.update({'id': 'id_CEP'})


class FormAnotacoes(forms.ModelForm):

    class Meta:
        model = Anotacoe
        fields = '__all__'
        exclude = ['do_usuario']
        widgets = {
            'data_registro': DateInput(),
            'texto': Textarea(attrs={'cols': 120, 'rows': 15}),
        }


class FormRecibos(forms.Form):
    contrato = forms.ModelChoiceField(label='', queryset=Contrato.objects.all().order_by('-data_registro'), initial='')

    def __init__(self, *args, **kwargs):
        super(FormRecibos, self).__init__(*args, **kwargs)
        self.fields['contrato'].widget.attrs['class'] = 'form-select form-select-sm'


meses = [(0, '...'), (1, '...'), (2, '...'), (3, '...'), (4, '...'), (5, '...'), (6, '...')]


class FormTabela(forms.Form):
    mes = forms.ChoiceField(label='', initial='', choices=meses)


class FormAdmin(forms.Form):
    escolhas = (
        ('1', f'Criar {settings.FICT_QTD["locatario"]} Locatários'),
        ('2', f'Criar {settings.FICT_QTD["imovel"]} Imoveis'),
        ('3', f'Criar {settings.FICT_QTD["contrato"]} Contratos'),
        ('4', f'Criar {settings.FICT_QTD["pagamento"]} Pagamentos'),
        ('5', f'Criar {settings.FICT_QTD["gasto"]} Gastos'),
        ('6', f'Criar {settings.FICT_QTD["nota"]} Anotações'),
        ('1000', '-------------'),
        ('100', f'Criar todos acima'),
        ('1000', '-------------'),
        ('150', f'Criar {settings.FICT_QTD["user"]} Usuários'),
        ('160', f'Criar {settings.FICT_QTD["imovel_g"]} Imov_Grupos'),
        ('170', 'Teste Mensagem'),
    )

    executar = forms.ChoiceField(choices=escolhas, initial='100')
    p_usuario = forms.ModelChoiceField(label='', queryset=Usuario.objects.all(),
                                       initial='')
    multiplicar_por = forms.IntegerField(max_value=10, min_value=0, initial=1)

    def __init__(self, *args, **kwargs):
        super(FormAdmin, self).__init__(*args, **kwargs)
        self.fields['multiplicar_por'].widget.attrs.update(style="width: 60px;")
        self.fields['executar'].widget.attrs['class'] = 'mt-1 form-control form-control-sm'
        self.fields['p_usuario'].widget.attrs['class'] = 'mt-1 form-control form-control-sm'
        self.fields['multiplicar_por'].widget.attrs['class'] = 'mt-1 form-control form-control-sm'
