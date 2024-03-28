from datetime import datetime, date
from dateutil.relativedelta import relativedelta

from core.funcoes_proprias import valor_format, validar_cpf

from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from crispy_forms.bootstrap import InlineCheckboxes
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout

from core.models import Usuario, DevMensagen, Pagamento, Gasto, Locatario, Contrato, Imovei, Anotacoe, ImovGrupo, \
    ContratoDocConfig, ContratoModelo, Sugestao


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

    def clean_telefone(self):
        telefone = self.cleaned_data['telefone']
        telefones_dos_user = Usuario.objects.all().values_list('telefone', flat=True)
        if telefone in telefones_dos_user and telefone != '':
            raise forms.ValidationError("Este telefone já está em uso.")
        else:
            return telefone


class FormToken(forms.Form):
    codigo_token = forms.CharField(max_length=6, min_length=6, widget=forms.TextInput(attrs={'class': 'form-control'}),
                                   help_text='Digite apenas números', label='Código')


class FormUsuario(UserChangeForm):
    cpf = forms.CharField(max_length=11, min_length=11, widget=forms.TextInput(attrs={'class': 'form-control'}),
                          help_text='Digite apenas números', label='CPF')

    class Meta:
        model = Usuario
        fields = ['username', 'password', 'first_name', 'last_name', 'email', 'telefone', 'RG', 'nacionalidade',
                  'estadocivil', 'ocupacao', 'endereco_completo', 'dados_pagamento1', 'dados_pagamento2']

    def __init__(self, *args, **kwargs):
        super(FormUsuario, self).__init__(*args, **kwargs)
        self.fields['dados_pagamento1'].widget.attrs['class'] = 'form-control-sm'
        self.fields['dados_pagamento2'].widget.attrs['class'] = 'form-control-sm'
        self.fields['cpf'].widget.attrs['class'] = 'mask-cpf'
        self.fields['cpf'].widget.attrs['id'] = 'id_CPF'

    def clean_cpf(self):
        cpf = self.cleaned_data['cpf']
        if validar_cpf(cpf):
            return cpf
        else:
            raise forms.ValidationError("Número de CPF inválido")


class FormConfigApp(forms.Form):
    notif_qtd = forms.IntegerField(max_value=40, min_value=10, step_size=10,
                                   widget=forms.NumberInput(attrs={'class': 'form-control-sm'}))
    notif_qtd_hist = forms.IntegerField(max_value=40, min_value=10, step_size=10,
                                        widget=forms.NumberInput(attrs={'class': 'form-control-sm'}))

    itens_pag_visao_geral = forms.IntegerField(max_value=54, min_value=27, step_size=1,
                                               widget=forms.NumberInput(attrs={'class': 'form-control-sm'}))

    itens_pag_ativos = forms.IntegerField(max_value=27, min_value=12, step_size=3,
                                          widget=forms.NumberInput(attrs={'class': 'form-control-sm'}))

    itens_pag_pagamentos = forms.IntegerField(max_value=108, min_value=28, step_size=4,
                                              widget=forms.NumberInput(attrs={'class': 'form-control-sm'}))
    itens_pag_gastos = forms.IntegerField(max_value=108, min_value=28, step_size=4,
                                          widget=forms.NumberInput(attrs={'class': 'form-control-sm'}))

    itens_pag_imoveis = forms.IntegerField(max_value=56, min_value=16, step_size=4,
                                           widget=forms.NumberInput(attrs={'class': 'form-control-sm'}))
    itens_pag_locatarios = forms.IntegerField(max_value=56, min_value=16, step_size=4,
                                              widget=forms.NumberInput(attrs={'class': 'form-control-sm'}))
    itens_pag_contratos = forms.IntegerField(max_value=56, min_value=16, step_size=4,
                                             widget=forms.NumberInput(attrs={'class': 'form-control-sm'}))
    itens_pag_notas = forms.IntegerField(max_value=56, min_value=16, step_size=4,
                                         widget=forms.NumberInput(attrs={'class': 'form-control-sm'}))

    def __init__(self, *args, **kwargs):
        super(FormConfigApp, self).__init__(*args, **kwargs)
        self.fields['notif_qtd'].label = 'Quantidade máxima de novas notificações a exibir na aba notificações'
        self.fields[
            'notif_qtd_hist'].label = 'Quantidade máxima de notificações a exibir na aba histórico de notificações'
        self.fields['itens_pag_visao_geral'].label = 'Quantidade máxima de itens por página em Visão Geral'
        self.fields['itens_pag_ativos'].label = 'Quantidade máxima de itens por página em Itens Ativos'
        self.fields['itens_pag_pagamentos'].label = 'Quantidade máxima de itens por página em Pagamentos'
        self.fields['itens_pag_gastos'].label = 'Quantidade máxima de itens por página em Gastos'
        self.fields['itens_pag_imoveis'].label = 'Quantidade máxima de itens por página em Imóveis'
        self.fields['itens_pag_locatarios'].label = 'Quantidade máxima de itens por página em Locatários'
        self.fields['itens_pag_contratos'].label = 'Quantidade máxima de itens por página em Contratos'
        self.fields['itens_pag_notas'].label = 'Quantidade máxima de itens por página em Anotações'


class FormConfigNotific(forms.Form):
    notif_recibo = forms.BooleanField(initial=True, required=False)
    notif_contrato_criado = forms.BooleanField(initial=True, required=False)
    notif_contrato_venc_1 = forms.BooleanField(initial=True, required=False)
    notif_contrato_venc_2 = forms.BooleanField(initial=True, required=False)
    notif_parc_venc_1 = forms.BooleanField(initial=True, required=False)
    notif_parc_venc_2 = forms.BooleanField(initial=True, required=False)

    def __init__(self, *args, **kwargs):
        super(FormConfigNotific, self).__init__(*args, **kwargs)
        self.fields['notif_recibo'].label = 'Notificar quando um pagamento de aluguel for detectado'
        self.fields['notif_contrato_criado'].label = 'Notificar quando um contrato for criado'
        self.fields[
            'notif_contrato_venc_1'].label = 'Notificar quando faltar menos de 30 dias para o vencimento de um contrato'
        self.fields['notif_contrato_venc_2'].label = 'Notificar quando um contrato vencer'
        self.fields[
            'notif_parc_venc_1'].label = 'Notificar quando faltar menos de 5 dias para o vencimento de um aluguel'
        self.fields['notif_parc_venc_2'].label = 'Notificar quando um aluguel vencer'


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
        (1, 'Recentes'),
        (2, 'Antigos'),
    ]

    data_eventos_i = forms.DateField(label='A partir de',
                                     widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control-sm'}))

    data_eventos_f = forms.DateField(label='Até', initial=date.today().strftime('%Y-%m-%d'), widget=forms.DateInput(
        attrs={'type': 'date', 'class': 'form-control-sm', 'max': datetime.now().date()}))

    qtd = forms.IntegerField(label='Qtd', max_value=50, min_value=5, step_size=5, initial=10,
                             widget=forms.NumberInput(attrs={'class': 'form-control-sm'}))

    ordem_eventos = forms.ChoiceField(label='Ordem', initial=1, choices=ordem_em_eventos,
                                      widget=forms.RadioSelect())

    itens_eventos = forms.MultipleChoiceField(label='Mostrar os itens selecionados', choices=mostrar_em_eventos,
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


class FormEmail(forms.Form):
    email = forms.EmailField(label=False)


class FormMensagem(forms.ModelForm):
    class Meta:
        model = DevMensagen
        fields = '__all__'
        exclude = ['do_usuario', 'data_criacao', 'resposta', 'da_notificacao']
        widgets = {
            'mensagem': Textarea(),
        }


class FormSugestao(forms.ModelForm):
    class Meta:
        model = Sugestao
        fields = '__all__'
        exclude = ['do_usuario', 'data_registro', 'implementada', 'likes']

        widgets = {
            'corpo': Textarea(attrs={'cols': 500, 'rows': 22}),

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

    def clean_valor_pago(self):
        valor_pago = self.cleaned_data['valor_pago']
        ao_contrato = self.cleaned_data['ao_contrato']
        contrato = Contrato.objects.get(pk=ao_contrato.pk)
        pagamento_tt = contrato.pagamento_total()
        total = int(contrato.valor_mensal) * int(contrato.duracao)
        total_futuro = pagamento_tt + int(valor_pago)
        valor_maximo = total - pagamento_tt
        if total_futuro > total:
            raise forms.ValidationError(
                f"Com este valor o limite total do contrato será ultrapassado. Valor máximo: "
                f"{valor_format(str(total - pagamento_tt))}" if valor_maximo > 0 else
                f'Impossível adicionar mais pagamentos, o contrato está quitado.'
                f' Valor do contrato: {valor_format(str(total))}.')
        else:
            return valor_pago

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
    cpf = forms.CharField(max_length=11, min_length=11, widget=forms.TextInput(attrs={'class': 'form-control'}),
                          help_text='Digite apenas números', label='CPF')

    class Meta:
        model = Locatario
        fields = '__all__'
        exclude = ['do_locador', 'data_registro', 'temporario']

    def __init__(self, *args, usuario, **kwargs):
        super(FormLocatario, self).__init__(*args, **kwargs)
        self.fields['cpf'].widget.attrs.update({'class': 'mask-cpf'})
        self.fields['cpf'].widget.attrs['id'] = 'id_CPF'
        self.fields['telefone1'].widget.attrs.update({'class': 'mask-telefone1'})
        self.fields['telefone2'].widget.attrs.update({'class': 'mask-telefone2'})
        self.locador_pk = usuario

    def clean_cpf(self):
        cpf = self.cleaned_data['cpf']
        cpfs_dos_locat_deste_user = Locatario.objects.filter(do_locador=self.locador_pk).exclude(
            pk=self.instance.pk).values_list('cript_cpf', flat=True)
        if cpf in cpfs_dos_locat_deste_user:
            raise forms.ValidationError("Já existe um locatário registrado com este CPF.")
        elif validar_cpf(cpf) is False:
            raise forms.ValidationError("Número de CPF inválido")
        else:
            return cpf

    def clean_nome(self):
        nome = self.cleaned_data['nome']
        if " " not in nome:
            raise forms.ValidationError("Digite o nome completo do locatário")
        else:
            return nome


class FormContrato(forms.ModelForm):
    class Meta:
        model = Contrato
        fields = '__all__'
        exclude = ['do_locador', 'em_posse', 'rescindido', 'vencido', 'codigo', 'data_de_rescisao', 'recibos_pdf',
                   'data_registro', 'da_notificacao']
        widgets = {
            'data_entrada': DateInput(),
            'duracao': Numeros(),
            'valor_mensal': Numeros(),
            'dia_vencimento': Numeros(),
        }

    def clean_data_entrada(self):
        entrada_novo = self.cleaned_data['data_entrada']
        duracao = int(self.data['duracao'])
        saida_novo = entrada_novo + relativedelta(months=duracao)
        imovel = self.cleaned_data['do_imovel']

        # Se existir algum contrato com datas de entrada e saida entre o período registrado no novo contrato, esta
        # entrada não pode ser permitida \/
        # Obs: Existe uma cópia deste validador em views
        contratos_deste_imovel = Contrato.objects.filter(do_imovel=imovel.pk, rescindido=False).exclude(
            pk=self.instance.pk)
        permitido = True
        # print('Contrato novo entra nesta data', entrada_novo.strftime("%d/%m/%Y"))
        # print('Contrato nov sai nesta data', saida_novo.strftime("%d/%m/%Y"))
        # print('-=-=-=-=-')
        for n, contrato in enumerate(contratos_deste_imovel):
            # print(f'Contrato {n}: entra nesta data', contrato.data_entrada.strftime("%d/%m/%Y"))
            # print(f'Contrato {n}: sai nesta data',
            #       (contrato.data_entrada + relativedelta(months=contrato.duracao)).strftime("%d/%m/%Y"))
            # print('')
            entrada_antigo = contrato.data_entrada
            saida_antigo = contrato.data_entrada + relativedelta(months=contrato.duracao)

            if entrada_antigo <= entrada_novo <= saida_antigo:
                permitido = False
            if entrada_antigo <= saida_novo <= saida_antigo:
                permitido = False

            if entrada_antigo >= entrada_novo >= saida_antigo:
                permitido = False
            if entrada_antigo >= saida_novo >= saida_antigo:
                permitido = False

            if entrada_antigo >= entrada_novo and saida_antigo <= saida_novo:
                permitido = False
        if permitido is False:
            raise forms.ValidationError("Já existe um contrato registrado para este imóvel neste período.")
        else:
            return entrada_novo

    def __init__(self, user, *args, **kwargs):
        super(FormContrato, self).__init__(*args, **kwargs)
        self.fields['do_locatario'].queryset = Locatario.objects.filter(do_locador=user)
        self.fields['do_imovel'].queryset = Imovei.objects.filter(do_locador=user)
        self.fields['valor_mensal'].widget.attrs.update({'class': 'mask-valor'})


class FormContratoDoc(forms.Form):
    contrato = forms.ModelChoiceField(label='', queryset=Contrato.objects.none(), initial='')

    def __init__(self, *args, **kwargs):
        super(FormContratoDoc, self).__init__(*args, **kwargs)
        self.fields['contrato'].widget.attrs.update({'class': 'mt-3'})


class FormContratoDocConfig(forms.ModelForm):
    caucao = forms.IntegerField(help_text='Multiplicado pelo valor de uma parcela', label='Caução (parcela multipl.)',
                                max_value=3, min_value=0, initial=1, required=False)
    fiador_cript_cpf = forms.CharField(max_length=11, min_length=11, required=False,
                                       widget=forms.TextInput(attrs={'class': 'form-control'}),
                                       help_text='Digite apenas números', label='CPF')

    class Meta:
        model = ContratoDocConfig
        fields = '__all__'
        exclude = ['do_contrato']

    def __init__(self, *args, **kwargs):
        super(FormContratoDocConfig, self).__init__(*args, **kwargs)
        self.fields['fiador_cript_cpf'].widget.attrs['id'] = 'id_CPF'
        self.fields['tipo_de_locacao'].choices = ((None, '-----------'), (1, 'Residencial'), (2, 'Não residencial'))

    def clean(self):
        msg = 'Para fiador este campo deve ser preenchido'
        msg2 = 'Este número náo é um CPF válido'
        cleaned_data = super(FormContratoDocConfig, self).clean()
        fiador_nome = cleaned_data.get("fiador_nome")
        fiador_cpf = cleaned_data.get("fiador_cript_cpf")

        if fiador_nome is not None and fiador_cpf == '':
            self.add_error('fiador_cript_cpf', msg)
        if len(fiador_cpf) > 0 and fiador_nome is None:
            self.add_error('fiador_nome', msg)
        if fiador_cpf != '' and validar_cpf(fiador_cpf) is False:
            self.add_error('fiador_cript_cpf', msg2)
        return cleaned_data


class FormContratoModelo(forms.ModelForm):
    class Meta:
        model = ContratoModelo
        fields = '__all__'
        exclude = ['autor', 'data_criacao', 'variaveis', 'condicoes', 'visualizar', 'usuarios', 'excluidos']

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request") if 'request' in kwargs else None
        super(FormContratoModelo, self).__init__(*args, **kwargs)
        self.fields['titulo'].widget.attrs.update({'class': 'text-center'})
        self.fields['descricao'].widget.attrs.update({'class': 'text-center'})
        self.fields['comunidade'].label = 'Compartilhar'
        self.fields['titulo'].label = ''

    def clean_titulo(self):
        titulo = self.cleaned_data['titulo']
        user = self.request.user if self.request else None
        if user == self.instance.autor or self.instance.verificar_utilizacao_usuarios() is False:
            titulos_de_modelos = ContratoModelo.objects.all().exclude(pk=self.instance.pk).values_list('titulo',
                                                                                                       flat=True)
        else:
            titulos_de_modelos = ContratoModelo.objects.all().values_list('titulo', flat=True)
        if titulo in titulos_de_modelos:
            raise forms.ValidationError("Por favor, escolha outro título para este modelo.")
        else:
            return titulo


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
        exclude = ['do_locador', 'com_locatario', 'data_registro']

    def __init__(self, user, *args, **kwargs):
        super(FormImovel, self).__init__(*args, **kwargs)
        self.fields['grupo'].queryset = ImovGrupo.objects.filter(do_usuario=user)
        self.fields['cep'].widget.attrs.update({'class': 'mask-cep'})
        self.fields['cep'].widget.attrs.update({'id': 'id_CEP'})
        self.user = user

    def clean_nome(self):
        nome = self.cleaned_data['nome']
        nomes_dos_imoveis_deste_user = Imovei.objects.filter(do_locador=self.user).exclude(
            pk=self.instance.pk).values_list('nome', flat=True)
        if nome in nomes_dos_imoveis_deste_user:
            raise forms.ValidationError("Já existe um Imóvel registrado com este rótulo.")
        else:
            return nome

    # Forma clean do campo unico
    def clean_uc_energia(self):
        uc_energia = self.cleaned_data['uc_energia']
        uc_energia_dos_imoveis_deste_user = Imovei.objects.filter(do_locador=self.user).exclude(
            pk=self.instance.pk).values_list('uc_energia', flat=True)
        if uc_energia is None:
            return uc_energia
        elif uc_energia in uc_energia_dos_imoveis_deste_user:
            raise forms.ValidationError("Já existe um Imóvel registrado com esta matrícula de Energia.")
        else:
            return uc_energia

    def clean_uc_agua(self):
        uc_agua = self.cleaned_data['uc_agua']
        uc_agua_dos_imoveis_deste_user = Imovei.objects.filter(do_locador=self.user).exclude(
            pk=self.instance.pk).values_list('uc_agua', flat=True)
        if uc_agua is None:
            return uc_agua
        elif uc_agua in uc_agua_dos_imoveis_deste_user:
            raise forms.ValidationError("Já existe um Imóvel registrado com esta matrícula de Saneamento.")
        else:
            return uc_agua


class FormAnotacoes(forms.ModelForm):
    class Meta:
        model = Anotacoe
        fields = '__all__'
        exclude = ['do_usuario', 'feito', 'da_notificacao']
        widgets = {
            'data_registro': DateInput(attrs={'style': 'width: 140px;'}),
            'texto': Textarea(attrs={'cols': 10, 'rows': 15}),
        }


class FormRecibos(forms.Form):
    data_pre = [(1, '___/___/___'), (2, '___/mês/ano'), (3, 'dia/mês/ano')]
    contrato = forms.ModelChoiceField(label='', queryset=Contrato.objects.none(), initial='')
    data_preenchimento = forms.ChoiceField(label='', choices=data_pre, required=True)

    def __init__(self, *args, **kwargs):
        # user = kwargs.pop('user', None) # Acho q não é util
        super(FormRecibos, self).__init__(*args, **kwargs)
        self.fields['contrato'].widget.attrs['class'] = 'form-select form-select-sm'
        self.fields['data_preenchimento'].widget.attrs['class'] = 'form-select form-select-sm'


class FormTabela(forms.Form):
    meses = [(0, '...'), (1, '...'), (2, '...'), (3, '...'), (4, '...'), (5, '...'), (6, '...'), (7, '...'), (8, '...')]
    mostrar = [(4, '4'), (5, '5'), (6, '6'), (7, '7')]
    itens = [(6, '6'), (7, '7'), (8, '8'), (9, '9'), (10, '10')]

    mes = forms.ChoiceField(label='', initial='', choices=meses, required=True)
    mostrar_ativos = forms.BooleanField(label='', initial='', required=False)
    itens_qtd = forms.ChoiceField(label='', initial=10, choices=itens, required=True)
    mostrar_qtd = forms.ChoiceField(label='', initial=7, choices=mostrar, required=True)


class FormTickets(forms.Form):
    tickets_qtd = forms.IntegerField(label='', initial=1, min_value=1, max_value=25, required=True,
                                     widget=forms.NumberInput())


class FormSlots(forms.Form):
    slots_qtd = forms.IntegerField(label='', initial=1, min_value=1, max_value=25, required=True,
                                   widget=forms.NumberInput())


class FormAdmin(forms.Form):
    todos_ou_cada_opt = [(0, 'Quantia para cada usuário (inclusive adm)'),
                         (1, 'Quantia para cada usuário (exceto adm)'),
                         (2, 'Distribuir quantia entre todos (inclusive adm)'),
                         (3, 'Distribuir quantia entre todos (exceto adm)'),
                         (4, 'Para o usuário específico ------------>> ')]

    criar_usuarios = forms.BooleanField(label='Criar usuários: ', required=False)
    qtd_usuario = forms.IntegerField(label='Quantidade', widget=forms.NumberInput(attrs={'class': 'form-control'}),
                                     required=True, min_value=0, max_value=100)
    multiplicar_user_por = forms.IntegerField(label='Multipl. por',
                                              widget=forms.NumberInput(attrs={'class': 'form-control'}), max_value=100,
                                              min_value=1, initial=1, required=True)
    criar_itens = forms.BooleanField(label='Criar itens para os usuários: ', required=False)
    qtd_locatario = forms.IntegerField(label='Locatário(s)',
                                       widget=forms.NumberInput(attrs={'class': 'form-control-sm'}), required=True,
                                       min_value=0, max_value=100)
    qtd_imovel_g = forms.IntegerField(label='Imóv. Grupo(s)',
                                      widget=forms.NumberInput(attrs={'class': 'form-control-sm'}), required=True,
                                      min_value=0, max_value=100)
    qtd_imovel = forms.IntegerField(label='Imóvel(s)', widget=forms.NumberInput(attrs={'class': 'form-control-sm'}),
                                    required=True, min_value=0, max_value=100)
    qtd_contrato = forms.IntegerField(label='Contrato(s)', widget=forms.NumberInput(attrs={'class': 'form-control-sm'}),
                                      required=True, min_value=0, max_value=100)
    qtd_pagamento = forms.IntegerField(label='Pagamento(s)',
                                       widget=forms.NumberInput(attrs={'class': 'form-control-sm'}), required=True,
                                       min_value=0, max_value=100)
    qtd_gasto = forms.IntegerField(label='Gasto(s)', widget=forms.NumberInput(attrs={'class': 'form-control-sm'}),
                                   required=True, min_value=0, max_value=100)
    qtd_nota = forms.IntegerField(label='Nota(s)', widget=forms.NumberInput(attrs={'class': 'form-control-sm'}),
                                  required=True, min_value=0, max_value=100)
    qtd_sugestao = forms.IntegerField(label='Sugestão(ões)',
                                      widget=forms.NumberInput(attrs={'class': 'form-control-sm'}),
                                      required=True, min_value=0, max_value=100)
    qtd_contr_modelo = forms.IntegerField(label='Contr. Modelo(s)',
                                          widget=forms.NumberInput(attrs={'class': 'form-control-sm'}),
                                          required=True, min_value=0, max_value=100)
    para_o_usuario = forms.ModelChoiceField(label='Para o usuário', queryset=Usuario.objects.all(), required=True)
    multiplicar_por = forms.IntegerField(label='Multiplicar cada item por',
                                         widget=forms.NumberInput(attrs={'class': 'form-control'}), max_value=100,
                                         min_value=1, initial=1, required=True)
    todos_ou_cada = forms.ChoiceField(label='', choices=todos_ou_cada_opt, initial=4, required=True)

    def __init__(self, *args, **kwargs):
        super(FormAdmin, self).__init__(*args, **kwargs)
        self.fields['qtd_usuario'].widget.attrs.update(id="zero_fill1")
        self.fields['qtd_locatario'].widget.attrs.update(id="zero_fill2")
        self.fields['qtd_imovel_g'].widget.attrs.update(id="zero_fill3")
        self.fields['qtd_imovel'].widget.attrs.update(id="zero_fill4")
        self.fields['qtd_contrato'].widget.attrs.update(id="zero_fill5")
        self.fields['qtd_pagamento'].widget.attrs.update(id="zero_fill6")
        self.fields['qtd_gasto'].widget.attrs.update(id="zero_fill7")
        self.fields['qtd_nota'].widget.attrs.update(id="zero_fill8")
        self.fields['qtd_sugestao'].widget.attrs.update(id="zero_fill9")
        self.fields['qtd_contr_modelo'].widget.attrs.update(id="zero_fill10")
