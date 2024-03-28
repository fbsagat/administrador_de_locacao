import string, secrets, os, uuid
from datetime import datetime, timedelta
from math import floor
from hashlib import sha256

from dateutil.relativedelta import relativedelta
from num2words import num2words

from Alugue_seu_imovel import settings
from django.core.validators import MinLengthValidator, MaxLengthValidator, RegexValidator, MinValueValidator, \
    MaxValueValidator, FileExtensionValidator
from django.db import models
from django.urls import reverse
from django.template.defaultfilters import date as data_ptbr
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.auth.models import AbstractUser
from django_resized import ResizedImageField
from core.funcoes_proprias import valor_format, tratar_imagem, cpf_format, cel_format, cep_format
from ckeditor.fields import RichTextField
from core.funcoes_proprias import modelo_variaveis, modelo_condicoes, tamanho_max_mb, gerar_uuid_6, gerar_uuid_8, \
    gerar_uuid_10, \
    gerar_uuid_20, _decrypt, _crypt

apenas_numeros = RegexValidator(regex=r'^[0-9]*$', message='Digite apenas números.')

estados_civis = (
    (0, 'Solteiro(a)'),
    (1, 'Casado(a)'),
    (2, 'Separado(a)'),
    (3, 'Divorciado(a)'),
    (4, 'Viuvo(a)'))


# Gerar o código para o contrato:
def gerar_codigo_contrato():
    codigos_existentes = list(Contrato.objects.all().values("codigo").values_list('codigo', flat=True))
    while True:
        con_codigo = ''.join(
            secrets.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(10))
        if con_codigo not in codigos_existentes:
            return f'{con_codigo[:5]}-{con_codigo[5:]}'


class Usuario(AbstractUser):
    # Informações de usuário
    RG = models.CharField(max_length=9, null=True, blank=True, help_text='Digite apenas números',
                          validators=[MinLengthValidator(7), MaxLengthValidator(9), apenas_numeros])
    cript_cpf = models.BinaryField(null=True, blank=True)
    telefone = models.CharField(max_length=11, null=False, blank=True, help_text='Celular/Digite apenas números',
                                validators=[MinLengthValidator(11), MaxLengthValidator(11), apenas_numeros])
    email = models.EmailField(unique=True)
    nacionalidade = models.CharField(null=True, blank=True, max_length=40, default='Brasileiro(a)')
    estadocivil = models.IntegerField(null=True, blank=True, verbose_name='Estado Civil', choices=estados_civis)
    ocupacao = models.CharField(null=True, blank=True, max_length=85, verbose_name='Ocupação')
    endereco_completo = models.CharField(null=True, blank=True, max_length=150, verbose_name='Endereço Completo')
    dados_pagamento1 = models.CharField(null=True, blank=True, max_length=90,
                                        verbose_name='Informações de pagamentos 1',
                                        help_text='Sua conta PIX ou dados bancários ou carteira crypto, etc...')
    dados_pagamento2 = models.CharField(null=True, blank=True, max_length=90,
                                        verbose_name='Informações de pagamentos 2')
    uuid = models.CharField(null=False, editable=False, max_length=10, unique=True, default=gerar_uuid_10)
    tickets = models.IntegerField(default=10)

    # Configurações de slots
    locat_slots = models.IntegerField(default=3)

    # Configurações da view Visão geral
    vis_ger_ultim_order_by = models.CharField(default='vencimento_atual', null=True, blank=True, max_length=60)

    # Configurações da view Eventos
    data_eventos_i = models.DateField(blank=True, null=True)
    itens_eventos = models.CharField(blank=True, null=True, max_length=31, default=['1', '2', '3', '4', '5', '6'])
    qtd_eventos = models.IntegerField(blank=True, null=True, default=10)
    ordem_eventos = models.IntegerField(default=1, blank=False)

    # Configurações da view Gerador de recibos PDF
    recibo_ultimo = models.ForeignKey('Contrato', null=True, blank=True, related_name='usuario_recibo_set',
                                      on_delete=models.SET_NULL)
    recibo_preenchimento = models.IntegerField(null=True, blank=True)

    # Configurações da view Gerador de Tabela PDF
    tabela_ultima_data_ger = models.IntegerField(null=True, blank=True)
    tabela_meses_qtd = models.IntegerField(null=True, blank=True)
    tabela_imov_qtd = models.IntegerField(null=True, blank=True)
    tabela_mostrar_ativos = models.BooleanField(null=True, blank=True)

    # Configurações da view Gerador de contratos PDF
    contrato_ultimo = models.ForeignKey('Contrato', null=True, blank=True, related_name='usuario_contrato_set',
                                        on_delete=models.SET_NULL)

    # Configurações da aplicação
    notif_qtd = models.IntegerField(default=20, blank=False)
    notif_qtd_hist = models.IntegerField(default=20, blank=False)
    itens_pag_visao_geral = models.IntegerField(default=27, blank=False)
    itens_pag_ativos = models.IntegerField(default=12, blank=False)
    itens_pag_pagamentos = models.IntegerField(default=56, blank=False)
    itens_pag_gastos = models.IntegerField(default=56, blank=False)
    itens_pag_imoveis = models.IntegerField(default=28, blank=False)
    itens_pag_locatarios = models.IntegerField(default=28, blank=False)
    itens_pag_contratos = models.IntegerField(default=28, blank=False)
    itens_pag_notas = models.IntegerField(default=28, blank=False)

    # Configurações de notificações
    notif_recibo = models.DateTimeField(default=datetime.now, null=True)
    notif_contrato_criado = models.DateTimeField(default=datetime.now, null=True)
    notif_contrato_venc_1 = models.DateTimeField(default=datetime.now, null=True)
    notif_contrato_venc_2 = models.DateTimeField(default=datetime.now, null=True)
    notif_parc_venc_1 = models.DateTimeField(default=datetime.now, null=True)
    notif_parc_venc_2 = models.DateTimeField(default=datetime.now, null=True)

    def locat_auto_registro_link(self):
        code = _crypt(self.uuid)
        return reverse('core:Locatario Auto-Registro', args=[str(code)[2:-1]])

    def recibos_code(self):
        site_code = os.environ.get('recibos')
        hash_uuid = sha256(str(f'{self.uuid}{site_code}').encode())
        code = hash_uuid.hexdigest()[:25]
        return code

    def contrato_code(self):
        site_code = os.environ.get('contrato')
        hash_uuid = sha256(str(f'{self.uuid}{site_code}').encode())
        code = hash_uuid.hexdigest()[:25]
        return code

    def contrato_modelo_code(self):
        site_code = os.environ.get('contrato-modelo')
        hash_uuid = sha256(str(f'{self.uuid}{site_code}').encode())
        code = hash_uuid.hexdigest()[:25]
        return code

    def nome_completo(self):
        if self.first_name and self.last_name:
            return f'{str(self.first_name)} {str(self.last_name)}'
        elif self.first_name:
            return str(self.first_name)
        else:
            return ''

    def primeiro_ultimo_nome(self):
        if self.nome_completo() != '':
            nome = self.nome_completo().split()
            return f'{nome[0]} {nome[len(nome) - 1]}'
        else:
            return ''

    def cpf(self):
        if self.cript_cpf:
            cpf = _decrypt(self.cript_cpf)
            return cpf

    def f_cpf(self):
        if self.cript_cpf:
            return cpf_format(self.cpf())

    def f_tel(self):
        if self.telefone:
            return cel_format(self.telefone)

    def arrecadacao_total(self):
        try:
            total = 0
            pagamentos = Pagamento.objects.filter(ao_locador=self).values_list('valor_pago')

            for pagamento in pagamentos:
                total += int(pagamento[0])

            return valor_format(str(total))
        except:
            return None

    def arrecadacao_mensal(self):
        try:
            contratos_user = Contrato.objects.ativos_hoje().filter(do_locador=self)
            arrecadacao_mensal = 0
            for contrato in contratos_user:
                arrecadacao_mensal += int(contrato.valor_mensal)
            return valor_format(str(arrecadacao_mensal))
        except:
            return None

    def valor_total_contratos_ativos(self):
        try:
            contratos_user = Contrato.objects.ativos_hoje().filter(do_locador=self)
            valor_total_contratos_ativos = 0
            for contrato in contratos_user:
                valor_total_contratos_ativos += int(contrato.valor_do_contrato())
            return valor_format(str(valor_total_contratos_ativos))
        except:
            return None

    def valor_total_contratos(self):
        try:
            contratos_user = Contrato.objects.filter(do_locador=self)
            valor_total_contratos = 0
            for contrato in contratos_user:
                valor_total_contratos += int(contrato.valor_do_contrato())
            return valor_format(str(valor_total_contratos))
        except:
            return None

    def tem_slot_disponivel(self):
        slots = Slot.objects.filter(do_usuario=self)
        for slot in slots:
            if slot.imovel() is None:
                return True
        return False


class TempLink(models.Model):
    do_usuario = models.ForeignKey('Usuario', null=False, on_delete=models.CASCADE)
    tempo_final = models.DateTimeField(null=False)
    link_uuid = models.CharField(null=False, editable=False, max_length=45, default=secrets.token_urlsafe)
    tipo = models.PositiveIntegerField(default=1)

    def get_link_completo(self):
        if self.tipo == 1:
            return reverse('core:Ativar Conta Url', args=[str(self.link_uuid)])
        elif self.tipo == 2:
            return reverse('core:Apagar Conta', args=[str(self.link_uuid)])


class TempCodigo(models.Model):
    do_usuario = models.ForeignKey('Usuario', null=False, on_delete=models.CASCADE)
    tempo_final = models.DateTimeField(null=False)
    codigo = models.CharField(null=False, editable=False, max_length=8, default=gerar_uuid_6)


class SlotsManager(models.Manager):
    def ativos(self):
        slots_qs = self.all()
        lista = []
        for slot in slots_qs:
            if slot.ativado() is True:
                lista.append(slot.pk)
        slots_ativos = Slot.objects.filter(pk__in=lista)
        return slots_ativos

    def inativos(self):
        slots_qs = self.all()
        lista = []
        for slot in slots_qs:
            if slot.ativado() is False:
                lista.append(slot.pk)
        slots_inativos = Slot.objects.filter(pk__in=lista)
        return slots_inativos

    def inativos_com_imovel(self):
        slots_qs = self.all()
        lista = []
        for slot in slots_qs:
            if slot.ativado() is False and slot.imovel() is not None:
                lista.append(slot.pk)
        slots_inativos = Slot.objects.filter(pk__in=lista)
        return slots_inativos


class Slot(models.Model):
    do_usuario = models.ForeignKey('Usuario', null=False, blank=False, on_delete=models.CASCADE)
    da_notificacao = models.OneToOneField('Notificacao', null=True, blank=True, on_delete=models.SET_NULL)

    gratuito = models.BooleanField(null=False, default=False)
    criado_em = models.DateTimeField(auto_now_add=True)
    tickets = models.PositiveIntegerField(default=0)
    objects = SlotsManager()

    class Meta:
        verbose_name_plural = 'Slots'
        ordering = ('pk',)

    def __str__(self):
        return (f'{self.pk}: {"Gratuito" if self.gratuito else "Pago"}/Criado: {self.criado_em}'
                f'/Tickets: {self.tickets}/{self.do_usuario}/{self.imovel()}')

    def posicao(self):
        slots = Slot.objects.filter(do_usuario=self.do_usuario).order_by('pk')
        return list(slots).index(self) + 1

    def imovel(self):
        try:
            slots = Slot.objects.filter(do_usuario=self.do_usuario).order_by('pk')
            imoveis = Imovei.objects.filter(do_locador=self.do_usuario).order_by('data_registro')
            return imoveis[list(slots).index(self)]
        except:
            return None

    def vencimento(self):
        # colocar para vencer um dia após, não zero(evitar reclamações dos usuários/não pode comer tempo deles)
        data = self.criado_em + relativedelta(days=int(self.tickets) * 30)
        return data.date()

    def dias_ativo(self):
        inicial = self.criado_em.date()
        final = self.vencimento()
        delta = final - inicial
        return int(delta.days)

    def dias_passados(self):
        inicial = self.criado_em.date()
        final = datetime.today().date()
        delta = final - inicial
        return int(delta.days)

    def dias_restando(self):
        dias_ativo = self.dias_ativo()
        dias_pasados = self.dias_passados()
        dias_restando = dias_ativo - dias_pasados
        return dias_restando if dias_restando >= 0 else 0

    def tickets_restando(self):
        """Aqui deve retornar os tickets(self.tickets) menos a quantia de tickets equivalentes aos dias que já passaram
        esde a criação do slot até hoje"""
        tickets_passados = floor(self.dias_passados() / 30)
        tickets_restando = self.tickets - tickets_passados
        return tickets_restando if tickets_restando >= 0 else 0

    def ativado(self):
        if self.gratuito:
            return True
        else:
            return False if datetime.today().date() >= self.vencimento() else True

    def borda(self):
        if self.gratuito:
            return 'border-success'
        else:
            return 'border-secondary' if self.ativado() else 'border-warning'


class LocatariosManager(models.Manager):
    def nao_temporarios(self):
        # Locatarios cadastrados pelos usuários, não que se cadastraram pelo link(Portanto seus cadastros
        # estão no modo temporário(para aprovação))
        return self.exclude(temporario=True)


class Locatario(models.Model):
    do_locador = models.ForeignKey('Usuario', null=True, blank=True, on_delete=models.CASCADE)
    da_notificacao = models.OneToOneField('Notificacao', null=True, blank=True, on_delete=models.SET_NULL)

    nome = models.CharField(max_length=120, blank=False, verbose_name='Nome Completo')
    docs = ResizedImageField(size=[1280, None], upload_to='locatarios_docs/%Y/%m/', null=True, blank=True,
                             verbose_name='Documentos', validators=[tratar_imagem, FileExtensionValidator])
    RG = models.CharField(max_length=9, null=False, blank=True, help_text='Digite apenas números',
                          validators=[MinLengthValidator(7), MaxLengthValidator(9), apenas_numeros])
    cript_cpf = models.BinaryField(null=True, blank=True)
    ocupacao = models.CharField(max_length=200, verbose_name='Ocupação')
    endereco_completo = models.CharField(null=True, blank=True, max_length=150, verbose_name='Endereço Completo')
    telefone1 = models.CharField(max_length=11, blank=False, verbose_name='Telefone 1',
                                 help_text='Celular/Digite apenas números',
                                 validators=[MinLengthValidator(11), MaxLengthValidator(11), apenas_numeros])
    telefone2 = models.CharField(max_length=11, null=True, blank=True, verbose_name='Telefone 2',
                                 help_text='Celular/Digite apenas números',
                                 validators=[MinLengthValidator(11), MaxLengthValidator(11), apenas_numeros])
    email = models.EmailField(max_length=65, null=True, blank=True)
    nacionalidade = models.CharField(max_length=40, blank=False, default='Brasileiro(a)')
    estadocivil = models.IntegerField(blank=False, verbose_name='Estado Civil', choices=estados_civis)
    data_registro = models.DateTimeField(auto_now_add=True)
    temporario = models.BooleanField(null=True)
    objects = LocatariosManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["cript_cpf", "do_locador"], name="cpf_locatario_por_usuario"),
        ]
        verbose_name_plural = 'Locatários'

    def __str__(self):
        return f'{self.nome}'

    def com_contratos(self):
        contratos = Contrato.objects.ativos_hoje().filter(do_locador=self.do_locador, do_locatario=self)
        return contratos or None

    def com_imoveis(self):
        contratos = self.com_contratos()
        contratos_ativos = []
        for contrato in contratos:
            contratos_ativos.append(contrato)
        if contratos_ativos:
            imoveis_pk = [contrato.do_imovel.pk for contrato in contratos_ativos]
            imoveis = Imovei.objects.filter(pk__in=imoveis_pk)
            return imoveis
        else:
            return None

    def primeiro_ultimo_nome(self):
        return f'{self.nome.split()[:1][0]} {self.nome.split()[len(self.nome.split()) - 1:][0]}'

    def imoveis_alugados(self):
        x = Imovei.objects.filter(com_locatario=self.pk)
        return x

    def cpf(self):
        if self.cript_cpf:
            cpf = _decrypt(self.cript_cpf)
            return cpf

    def f_cpf(self):
        if self.cript_cpf:
            return cpf_format(self.cpf())

    def f_tel1(self):
        if self.telefone1:
            return cel_format(self.telefone1)

    def f_tel2(self):
        if self.telefone2:
            return cel_format(self.telefone2)
        else:
            return None

    def contratos_qtd(self):
        return Contrato.objects.filter(do_locatario=self).count()


tipos_de_imovel = (
    (0, 'Casa'),
    (1, 'Apartamento'),
    (2, 'Kitnet'),
    (3, 'Box/Loja'),
    (4, 'Escritório'),
    (5, 'Depósito/Armazém'),
    (6, 'Galpão'))


class ImovGrupo(models.Model):
    do_usuario = models.ForeignKey('Usuario', null=True, blank=True, on_delete=models.CASCADE)
    nome = models.CharField(max_length=35, blank=False, verbose_name='Criar Grupo')
    tipo = models.IntegerField(null=True, blank=True, choices=tipos_de_imovel, verbose_name='Tipo de Imóvel')
    imoveis = models.ManyToManyField('Imovei', blank=True)

    class Meta:
        verbose_name_plural = 'Grupos de imóveis'
        ordering = ('nome',)

    def __str__(self):
        return self.nome

    def arrecadacao_total(self):
        try:
            total = 0
            imoveis = Imovei.objects.filter(grupo=self)
            for imovel in imoveis:
                total += imovel.receita_acumulada()
            return valor_format(str(total))
        except:
            return None

    def arrecadacao_mensal(self):
        try:
            imoveis = Imovei.objects.filter(grupo=self)
            contratos_user = Contrato.objects.ativos_hoje().filter(do_imovel__in=imoveis, do_locador=self.do_usuario)
            arrecadacao_mensal = 0
            for contrato in contratos_user:
                arrecadacao_mensal += int(contrato.valor_mensal)
            return valor_format(str(arrecadacao_mensal))
        except:
            return None

    def valor_total_contratos_ativos(self):
        try:
            imoveis = Imovei.objects.filter(grupo=self)
            contratos_user = Contrato.objects.ativos_hoje().filter(do_imovel__in=imoveis, do_locador=self.do_usuario)
            valor_total_contratos_ativos = 0
            for contrato in contratos_user:
                valor_total_contratos_ativos += int(contrato.valor_do_contrato())
            return valor_format(str(valor_total_contratos_ativos))
        except:
            return None

    def valor_total_contratos(self):
        try:
            imoveis = Imovei.objects.filter(grupo=self)
            contratos_user = Contrato.objects.filter(do_imovel__in=imoveis, do_locador=self.do_usuario)
            valor_total_contratos = 0
            for contrato in contratos_user:
                valor_total_contratos += int(contrato.valor_do_contrato())
            return valor_format(str(valor_total_contratos))
        except:
            return None


class ImoveiManager(models.Manager):
    def ativos(self):
        imoveis_qs = self
        lista = []
        for imovel in imoveis_qs:
            if imovel.esta_ocupado() is True:
                lista.append(imovel.pk)
        imoveis_ativos = Imovei.objects.filter(pk__in=lista)
        return imoveis_ativos


estados = (
    ('AC', 'Acre'), ('AL', 'Alagoas'), ('AP', 'Amapá'), ('AM', 'Amazonas'), ('BA', 'Bahia'), ('CE', 'Ceará'),
    ('DF', 'Distrito Federal'), ('ES', 'Espírito Santo'), ('GO', 'Goiás'), ('MA', 'Maranhão'), ('MT', 'Mato Grosso'),
    ('MS', 'Mato Grosso do Sul'), ('MG', 'Minas Gerais'), ('PA', 'Pará'), ('PB', 'Paraíba'), ('PR', 'Paraná'),
    ('PE', 'Pernambuco'), ('PI', 'Piauí'), ('RJ', 'Rio de Janeiro'), ('RN', 'Rio Grande do Norte'),
    ('RS', 'Rio Grande do Sul'), ('RO', 'Rondônia'), ('RR', 'Roraima'), ('SC', 'Santa Catarina'), ('SP', 'São Paulo'),
    ('SE', 'Sergipe'), ('TO', 'Tocantins')
)


class Imovei(models.Model):
    do_locador = models.ForeignKey('Usuario', blank=False, on_delete=models.CASCADE)
    grupo = models.ForeignKey('ImovGrupo', blank=True, null=True, on_delete=models.SET_NULL)

    nome = models.CharField(max_length=25, blank=False, verbose_name='Rótulo')
    cep = models.CharField(max_length=8, blank=False, verbose_name='CEP',
                           validators=[MinLengthValidator(8), MaxLengthValidator(8), apenas_numeros])
    endereco = models.CharField(max_length=180, blank=False, verbose_name='Endereço')
    numero = models.IntegerField(blank=False,
                                 validators=[MinValueValidator(1), MaxValueValidator(999999), apenas_numeros])
    complemento = models.CharField(max_length=80, null=True, blank=True)
    bairro = models.CharField(max_length=30, blank=False)
    cidade = models.CharField(max_length=30, blank=False)
    estado = models.CharField(max_length=2, blank=False, choices=estados)
    uc_energia = models.CharField(max_length=15, null=True, blank=True, verbose_name='Matrícula de Energia',
                                  validators=[MinLengthValidator(4), MaxLengthValidator(15)])
    uc_agua = models.CharField(max_length=15, null=True, blank=True, verbose_name='Matrícula de Saneamento',
                               validators=[MinLengthValidator(4), MaxLengthValidator(15)])
    data_registro = models.DateTimeField(default=datetime.now)
    objects = ImoveiManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["nome", "do_locador"], name="nome_imovel_por_usuario"),
        ]
        verbose_name_plural = 'Imóveis'
        ordering = ['-nome']

    def __str__(self):
        return f'{self.nome} ({self.grupo if self.grupo else "Sem grupo"})'

    def contrato_atual(self):
        contratos = Contrato.objects.ativos_hoje().filter(do_locador=self.do_locador, do_imovel=self)
        if contratos:
            return contratos[0]
        else:
            return None

    def contrato_todos(self):
        contratos = Contrato.objects.filter(do_locador=self.do_locador, do_imovel=self)
        if contratos:
            return contratos
        else:
            return None

    def com_locatario(self):
        if self.contrato_atual():
            return self.contrato_atual().do_locatario
        else:
            return None

    def nogrupo(self):
        return '' if self.grupo is None else self.grupo

    def esta_ocupado(self):
        return False if self.com_locatario is None else True

    def f_cep(self):
        return cep_format(self.cep)

    def endereco_base(self):
        complemento = f'({self.complemento})'
        return f'{self.endereco}, Nº{self.numero}{complemento if self.complemento else ""} - {self.bairro}'

    def endereco_completo(self):
        return f'{self.endereco_base()} - {self.cidade}/{self.estado}, {self.f_cep()}'

    def receita_acumulada(self):
        parcelas = Parcela.objects.filter(do_imovel=self, apagada=False)
        total = 0
        for parcela in parcelas:
            total += int(parcela.tt_pago)
        return total

    def receita_acumulada_format(self):
        return valor_format(str(self.receita_acumulada()))

    def em_slot(self):
        """ retorna true se estiver em slot e false se não """
        slots = Slot.objects.filter(do_usuario=self.do_locador)
        imoveis_em_slot = []
        for slot in slots:
            if slot.ativado():
                imoveis_em_slot.append(slot.imovel())
        return True if self in imoveis_em_slot else False


class ContratoManager(models.Manager):
    def ativos_hoje(self):
        hoje = datetime.today().date()
        contratos_qs = self.filter(em_posse=True, rescindido=False, data_entrada__lte=hoje)
        lista = []
        for contrato in contratos_qs:
            if contrato.periodo_ativo_hoje():
                lista.append(contrato.pk)
        contratos_ativos = Contrato.objects.filter(pk__in=lista)
        return contratos_ativos

    def ativos_hoje_e_antes_de(self, data):
        contratos_qs = self.filter(em_posse=True, rescindido=False, data_entrada__lte=data)
        lista = []
        for contrato in contratos_qs:
            if contrato.periodo_ativo_hoje() or contrato.periodo_ativo_antes_de(data):
                lista.append(contrato.pk)
        contratos_ativos = Contrato.objects.filter(pk__in=lista)
        return contratos_ativos

    def ativos_margem(self, dias_atras=45):
        hoje = datetime.today().date()
        contratos_qs = self.filter(rescindido=False, em_posse=True)
        lista = []
        for contrato in contratos_qs:
            if contrato.periodo_ativo_hoje() or contrato.periodo_ativo_futuramente() or \
                    contrato.periodo_ativo_xx_dias_atras(dias_atras):
                lista.append(contrato.pk)
        contratos_ativos = Contrato.objects.filter(pk__in=lista)
        return contratos_ativos

    def inativos(self):
        pass

    def ativos_e_no_slot(self):
        hoje = datetime.today().date()
        contratos_qs = self.filter(em_posse=True, rescindido=False, data_entrada__lte=hoje)
        lista = []
        for contrato in contratos_qs:
            if contrato.periodo_ativo_hoje() is True and contrato.do_imovel.em_slot() is True:
                lista.append(contrato.pk)
        contratos_ativos_slot = Contrato.objects.filter(pk__in=lista)
        return contratos_ativos_slot

    def ativos_e_sem_slot(self):
        hoje = datetime.today().date()
        contratos_qs = self.filter(em_posse=True, rescindido=False, data_entrada__lte=hoje)
        lista = []
        for contrato in contratos_qs:
            if contrato.periodo_ativo_hoje() is True and contrato.do_imovel.em_slot() is False:
                lista.append(contrato.pk)
        contratos_ativos_sem_slot = Contrato.objects.filter(pk__in=lista)
        return contratos_ativos_sem_slot


class Contrato(models.Model):
    do_locador = models.ForeignKey('Usuario', null=True, blank=True, on_delete=models.CASCADE)
    do_locatario = models.ForeignKey('Locatario', on_delete=models.CASCADE,
                                     verbose_name='Locatário')
    do_imovel = models.ForeignKey('Imovei', on_delete=models.CASCADE, verbose_name='No imóvel')

    data_entrada = models.DateField(blank=False, verbose_name='Data de Entrada')
    duracao = models.IntegerField(null=False, blank=False, verbose_name='Duração do contrato(Meses)',
                                  validators=[MaxValueValidator(18), MinValueValidator(1)])
    valor_mensal = models.CharField(max_length=9, verbose_name='Valor Mensal (R$) ', blank=False,
                                    help_text='Digite apenas números',
                                    validators=[apenas_numeros, MinLengthValidator(3)])
    dia_vencimento = models.IntegerField(blank=False, validators=[MaxValueValidator(28), MinValueValidator(1)],
                                         verbose_name='Dia do vencimento', help_text='(1-28)')
    em_posse = models.BooleanField(default=False, null=False,
                                   help_text='Marque quando receber a sua via assinada e registrada em cartório')
    rescindido = models.BooleanField(default=False, null=False, help_text='Marque caso haja rescisão do contrato')
    codigo = models.CharField(null=False, editable=False, max_length=11, default=gerar_codigo_contrato)
    data_de_rescisao = models.DateField(blank=True, verbose_name='Data da rescisão', null=True)
    recibos_pdf = models.FileField(upload_to='recibos_docs/%Y/%m/', blank=True, verbose_name='Recibos')
    data_registro = models.DateTimeField(auto_now_add=True)
    objects = ContratoManager()

    class Meta:
        ordering = ['-data_entrada']

    def __str__(self):
        """'O objeto count' diz em que posição este contrato fica na lista de contratos feitos com este locador neste
         imóvel"""
        contratos = Contrato.objects.filter(do_locador=self.do_locador, do_locatario=self.do_locatario,
                                            do_imovel=self.do_imovel).order_by('pk')
        count = (f'{list(contratos).index(self) + 1}' if len(contratos) > 1 else '1')
        return (f'({count}º - {self.do_locatario.primeiro_ultimo_nome()} - '
                f'{self.do_imovel.nome} - '
                f'{self.data_entrada.strftime("%m/%Y")})')

    def nome_completo(self):
        return f'{self.do_locatario.nome} - {self.do_imovel} - {self.data_entrada.strftime("%d/%m/%Y")} - ' \
               f'({self.codigo})'

    def valor_format(self):
        return valor_format(self.valor_mensal)

    def valor_por_extenso(self):
        reais = self.valor_mensal[:-2]
        centavos = self.valor_mensal[-2:]
        centavos_format = f' e {num2words(int(centavos), lang="pt_BR")} centavos'
        return f'{num2words(int(reais), lang="pt_BR").capitalize()} reais{centavos_format if int(centavos) > 1 else ""}'

    def valor_do_contrato(self):
        return str(int(self.valor_mensal) * int(self.duracao))

    def valor_do_contrato_format(self):
        return valor_format(self.valor_do_contrato())

    def valor_do_contrato_por_extenso(self):
        valor = str(int(self.valor_mensal) * int(self.duracao))
        reais = valor[:-2]
        centavos = valor[-2:]
        centavos_format = f' e {num2words(int(centavos), lang="pt_BR")} centavos'
        return f'{num2words(int(reais), lang="pt_BR").capitalize()} reais{centavos_format if int(centavos) > 1 else ""}'

    def total_quitado(self):
        valores = Pagamento.objects.filter(ao_contrato=self).values_list('valor_pago')
        valor_tt = 0
        for valor in valores:
            valor_tt += int(valor[0])
        return valor_tt

    def total_pg_format(self):
        if self.total_quitado() is None:
            return 'R$0,00'
        else:
            return valor_format(str(self.total_quitado()))

    def falta_pg(self):
        if self.total_quitado() is None:
            return self.valor_do_contrato()
        else:
            return str((int(self.valor_mensal) * int(self.duracao)) - self.total_quitado())

    def falta_pg_format(self):
        return valor_format(self.falta_pg())

    def em_maos(self):
        return 'Sim' if self.em_posse else 'Não'

    def data_saida(self):
        data = self.data_entrada + relativedelta(months=self.duracao)
        return data

    def periodo_vencido(self):
        return True if self.data_saida() < datetime.today().date() else False

    def vence_em_ate_x_dias(self, dias=int()):
        # Retorna True se este contrato vence na quantidade definida em 'dias'
        data_saida = self.data_saida()
        x_dias = datetime.today().date() + timedelta(days=dias)
        delta = data_saida - x_dias
        return True if delta.days <= 0 else False

    def periodo_ativo_hoje(self):
        hoje = datetime.today().date()
        return True if self.data_entrada <= hoje <= self.data_saida() else False

    def periodo_ativo_antes_de(self, data):
        return True if self.data_entrada <= data <= self.data_saida() else False

    def periodo_ativo_futuramente(self):
        return True if self.data_entrada > datetime.today().date() else False

    def periodo_ativo_xx_dias_atras(self, dias=45):
        return True if self.data_saida() >= datetime.today().date() + timedelta(days=-dias) else False

    def pagamento_total(self):
        pagamentos = Pagamento.objects.filter(ao_contrato=self.pk).values('valor_pago')
        valor_tt = 0
        for valor in pagamentos:
            valor_tt += int(valor['valor_pago'])
        return valor_tt

    def duracao_dias(self):
        delta = self.data_saida() - self.data_entrada
        return delta.days

    def transcorrido_dias(self):
        delta = datetime.today().date() - self.data_entrada
        return delta.days

    def faltando_dias(self):
        return self.duracao_dias() - self.transcorrido_dias()

    def passou_do_limite(self):
        return True if int(self.faltando_dias()) <= 30 else False

    def recibos_entregues_qtd(self):
        x = Parcela.objects.filter(do_contrato=self, recibo_entregue=True).count()
        return x

    def parcelas_pagas_qtd(self):
        numero = self.pagamento_total() / int(self.valor_mensal)
        return int(floor(numero))

    def quitado(self):
        return True if self.total_quitado() == int(self.valor_do_contrato()) else False

    def title_pagou_parcelas(self):
        if self.parcelas_pagas_qtd() > 0:
            plural = 's' if self.parcelas_pagas_qtd() > 1 else ''
            return f'Quitou: {self.parcelas_pagas_qtd()} de {self.duracao} parcela{plural}'
        else:
            return 'Nenhuma parcela quitada ainda'

    def faltando_recibos_qtd(self):
        try:
            return self.parcelas_pagas_qtd() - self.recibos_entregues_qtd()
        except:
            return None

    def duracao_meses_por_extenso(self):
        return num2words(self.duracao, lang='pt_BR')

    def dia_vencimento_por_extenso(self):
        return num2words(self.dia_vencimento, lang='pt_BR')

    def vencimento_atual(self):
        parcela_n_kit = Parcela.objects.filter(do_contrato=self, apagada=False).order_by('data_pagm_ref')
        parcelas = []
        for parcela in parcela_n_kit:
            if int(parcela.tt_pago) < int(self.valor_mensal) or int(parcela.tt_pago) == 0:
                parcelas.append(parcela)
        return parcelas[0].data_pagm_ref if parcelas else None

    def vencimento_atual_textual(self):
        txt = '📃✔️'
        title = 'O contrato está quitado'
        if self.vencimento_atual() is not None:
            hoje = datetime.today().date()
            vencim_atual = self.vencimento_atual()
            delta = hoje - vencim_atual
            delta2 = vencim_atual - hoje
            if vencim_atual == hoje + relativedelta(days=-1):
                txt = f'⭕ Venceu ontem ({vencim_atual.strftime("%d/%m/%Y")})'
                title = ''
            elif vencim_atual < hoje + relativedelta(days=-1):
                txt = f'⭕ Venceu em {vencim_atual.strftime("%d/%m/%Y")} ({delta.days} dias atrás)'
                title = ''
            elif vencim_atual == hoje:
                txt = f'🟡 Vence hoje ({vencim_atual.strftime("%d/%m/%Y")})'
                title = ''
            elif vencim_atual == hoje + relativedelta(days=+1):
                txt = f'🟡 Vencerá amanhã ({vencim_atual.strftime("%d/%m/%Y")})'
                title = ''
            elif vencim_atual > hoje + relativedelta(days=+1):
                if delta2.days <= 5:
                    txt = f'🟡 Vencerá em {vencim_atual.strftime("%d/%m/%Y")} (em {delta2.days} dias)'
                else:
                    txt = f'Vencerá em {vencim_atual.strftime("%d/%m/%Y")} (em {delta2.days} dias)'
                title = ''
        return txt, title

    def divida_atual_meses(self):
        parcelas = Parcela.objects.filter(do_contrato=self, apagada=False,
                                          data_pagm_ref__lte=datetime.today().date() - timedelta(days=1))
        parcelas_vencidas_n_quitadas = 0
        for parcela in parcelas:
            if int(parcela.tt_pago) < int(self.valor_mensal):
                parcelas_vencidas_n_quitadas += 1
        return parcelas_vencidas_n_quitadas

    def divida_atual_valor(self):
        parcelas = Parcela.objects.filter(do_contrato=self, apagada=False,
                                          data_pagm_ref__lte=datetime.today().date() - timedelta(days=1))
        parcelas_vencidas_n_quitadas = []
        for parcela in parcelas:
            if int(parcela.tt_pago) < int(self.valor_mensal) and parcela.apagada is False:
                parcelas_vencidas_n_quitadas.append(int(parcela.tt_pago))
        soma_tt_pg = sum([i for i in parcelas_vencidas_n_quitadas])
        valor = (len(parcelas_vencidas_n_quitadas) * int(self.valor_mensal)) - (int(soma_tt_pg) if soma_tt_pg else 0)
        return valor, valor_format(str(valor))

    def get_notific_all(self):
        # Retorna todas as notificações desda parcela
        tipo_conteudo = ContentType.objects.get_for_model(Contrato)
        notificacoes = Notificacao.objects.filter(do_usuario=self.do_locador, objeto_id=self.pk,
                                                  autor_classe=tipo_conteudo)
        if notificacoes:
            return notificacoes

    def get_notific_criado(self):
        # Retorna a notificação de aviso que o contrato foi criado
        tipo_conteudo = ContentType.objects.get_for_model(Contrato)
        notificacao = Notificacao.objects.filter(do_usuario=self.do_locador, objeto_id=self.pk,
                                                 autor_classe=tipo_conteudo, assunto=1)
        if notificacao:
            return notificacao.first()

    def get_notific_vence_em_ate_x_dias(self):
        # Retorna a notificação de aviso: 'faltam 30 dias para vencer'
        tipo_conteudo = ContentType.objects.get_for_model(Contrato)
        notificacao = Notificacao.objects.filter(do_usuario=self.do_locador, objeto_id=self.pk,
                                                 autor_classe=tipo_conteudo, assunto=2)
        if notificacao:
            return notificacao.first()

    def get_notific_periodo_vencido(self):
        # Retorna a notificação de aviso: 'contrato venceu'
        tipo_conteudo = ContentType.objects.get_for_model(Contrato)
        notificacao = Notificacao.objects.filter(do_usuario=self.do_locador, objeto_id=self.pk,
                                                 autor_classe=tipo_conteudo, assunto=3)
        if notificacao:
            return notificacao.first()


class ContratoModelo(models.Model):
    titulo = models.CharField(blank=False, max_length=120, verbose_name='Titulo', help_text='Titulo')
    autor = models.ForeignKey('Usuario', blank=False, null=True, related_name='contratomod_autor_set',
                              on_delete=models.SET_NULL)
    usuarios = models.ManyToManyField('Usuario', related_name='contratos_modelos', blank=True,
                                      through='UsuarioContratoModelo')
    excluidos = models.ManyToManyField('Usuario', related_name='contratos_modelos_excluidos', blank=True)

    descricao = models.CharField(blank=True, max_length=480, verbose_name='', help_text='Descrição')
    corpo = RichTextField(null=True, blank=True, verbose_name='', validators=[tamanho_max_mb])
    data_criacao = models.DateTimeField(auto_now_add=True)
    variaveis = models.JSONField(null=True, blank=True)
    condicoes = models.JSONField(null=True, blank=True)
    comunidade = models.BooleanField(default=False, verbose_name='Comunidade')
    visualizar = models.FileField(null=True, blank=True)

    class Meta:
        verbose_name_plural = 'Modelos de contratos'

    def __str__(self):
        return f'{self.titulo}'

    def display_variaveis(self):
        variaveis = []
        for variavel in list(self.variaveis):
            if variavel in modelo_variaveis:
                variaveis.append([modelo_variaveis[variavel][0], modelo_variaveis[variavel][1]])
        return variaveis if len(variaveis) > 0 else False

    def display_condicoes(self):
        condicoes = []
        for condicao in list(self.condicoes):
            if condicao in modelo_condicoes:
                condicoes.append([modelo_condicoes[condicao][0], modelo_condicoes[condicao][1]])
        return condicoes if len(condicoes) > 0 else False

    def verificar_utilizacao_config(self):
        """Este método visa verificar se existe algum 'ContratoDocConfig' utilizando esta instancia de modelo"""
        configs_do_user = ContratoDocConfig.objects.filter(do_modelo=self).count()
        return True if configs_do_user > 0 else False

    def verificar_utilizacao_usuarios(self):
        """Este método visa verificar se existe algum 'usuário' além do usuário verificador com uma cópia desta
        instancia de modelo"""
        outros_usuarios = self.usuarios.all().count()
        return True if outros_usuarios > 1 else False

    def delete(self, *args, **kwargs):
        """Apagar o contrato apenas se não houver nenhum ContratoDocConfig ou outro usuário utilizando-o, caso contrário
        # apagar o contrato apenas para o usuário, retirar da comunidade caso ele seja o autor."""
        try:
            user = Usuario.objects.get(pk=kwargs['kwargs'].get('user_pk'))
            um = self.verificar_utilizacao_config()
            dois = self.verificar_utilizacao_usuarios()

            # Se alguém estiver usando \/
            if um or dois:
                self.usuarios.remove(user)
                if self.autor == user:
                    self.comunidade = False
                    self.excluidos.add(user)
                    self.save(update_fields=['comunidade', ])
                if um and not dois:
                    self.titulo = f'config/{gerar_uuid_20(caracteres=20)}'
                    self.comunidade = False

                    # remover o arquivo visualizar e o campo visualizar da model
                    diretorio = fr'{settings.MEDIA_ROOT}/{self.visualizar}'
                    se_existe = os.path.isfile(diretorio)
                    if se_existe:
                        os.remove(diretorio)
                    self.visualizar = None
                    self.variaveis = None
                    self.condicoes = None
                    self.save(update_fields=['titulo', 'comunidade', 'visualizar', 'variaveis', 'condicoes', ])
            else:
                super(ContratoModelo, self).delete()
        except:
            super(ContratoModelo, self).delete()


tipos_de_locacao = (
    (None, '-----------'),
    (1, 'residencial'),
    (2, 'não residencial'))


class UsuarioContratoModelo(models.Model):
    usuario = models.ForeignKey('Usuario', on_delete=models.CASCADE, related_name='usuario_contrato_modelo')
    contrato_modelo = models.ForeignKey('ContratoModelo', on_delete=models.CASCADE,
                                        related_name='usuario_contrato_modelo')
    data_criacao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.contrato_modelo} - {self.usuario} - {self.data_criacao}'

    class Meta:
        verbose_name_plural = 'Modelos de contratos-Usuários'


class ContratoDocConfig(models.Model):
    do_contrato = models.ForeignKey('Contrato', null=True, blank=False, on_delete=models.CASCADE)
    do_modelo = models.ForeignKey('ContratoModelo', null=True, blank=False, on_delete=models.SET_NULL,
                                  verbose_name='Modelo de contrato')

    tipo_de_locacao = models.IntegerField(null=True, blank=True, choices=tipos_de_locacao,
                                          verbose_name='Tipo de Locação')
    caucao = models.IntegerField(null=True, blank=True,
                                 validators=[MinValueValidator(0), MaxValueValidator(3), apenas_numeros])

    fiador_nome = models.CharField(max_length=100, null=True, blank=True, verbose_name='Nome Completo')
    fiador_RG = models.CharField(max_length=9, null=True, blank=True, help_text='Digite apenas números',
                                 validators=[MinLengthValidator(7), MaxLengthValidator(9), apenas_numeros],
                                 verbose_name='RG')
    fiador_cript_cpf = models.BinaryField(null=True, blank=True)
    fiador_ocupacao = models.CharField(max_length=85, null=True, blank=True, verbose_name='Ocupação')
    fiador_endereco_completo = models.CharField(null=True, blank=True, max_length=150, verbose_name='Endereço Completo')
    fiador_nacionalidade = models.CharField(max_length=40, null=True, blank=True, verbose_name='Nacionalidade')
    fiador_estadocivil = models.IntegerField(null=True, blank=True, verbose_name='Estado Civil', choices=estados_civis)

    class Meta:
        verbose_name_plural = 'Configs de contratos'

    def __str__(self):
        return f'{self.do_contrato} ({self.do_modelo})'

    def fiador_cpf(self):
        if self.fiador_cript_cpf:
            cpf = _decrypt(self.fiador_cript_cpf)
            return cpf

    def f_cpf(self):
        if self.fiador_cript_cpf:
            return cpf_format(self.fiador_cpf())


class ParcelaManager(models.Manager):
    def de_contratos_ativos(self):
        parcela_qs = self.all()
        lista = []
        for parcela in parcela_qs:
            if parcela.contrato_em_posse() is True and parcela.contrato_rescindido() is False:
                lista.append(parcela.pk)
        resultado = Parcela.objects.filter(pk__in=lista)
        return resultado


class Parcela(models.Model):
    do_usuario = models.ForeignKey('Usuario', blank=False, on_delete=models.CASCADE)
    do_contrato = models.ForeignKey('Contrato', null=False, blank=False, on_delete=models.CASCADE)
    do_imovel = models.ForeignKey('Imovei', null=False, blank=False, on_delete=models.CASCADE)
    do_locatario = models.ForeignKey('Locatario', null=False, blank=False, on_delete=models.CASCADE)
    codigo = models.CharField(blank=False, null=False, editable=False, max_length=7, unique_for_month=True,
                              default=gerar_uuid_8)
    data_pagm_ref = models.DateField(null=False, blank=False,
                                     help_text='Data referente ao vencimento do pagamento desta parcela')
    tt_pago = models.CharField(max_length=9, blank=False, default=0)
    recibo_entregue = models.BooleanField(default=False)
    apagada = models.BooleanField(default=False)
    objects = ParcelaManager()

    def __str__(self):
        return (f'Parcela do contr.: {str(self.do_contrato.codigo)}/{self.do_locatario.primeiro_ultimo_nome()}/'
                f'{self.do_imovel}({self.data_pagm_ref.strftime("%B/%Y")})')

    def tt_pago_format(self):
        return valor_format(self.tt_pago)

    def contrato_em_posse(self):
        return self.do_contrato.em_posse

    def contrato_rescindido(self):
        return self.do_contrato.rescindido

    def falta_pagar_format(self):
        contrato = Contrato.objects.get(pk=self.do_contrato.pk)
        return valor_format(str(int(contrato.valor_mensal) - int(self.tt_pago)))

    def esta_pago(self):
        contrato = self.do_contrato
        return True if int(self.tt_pago) == int(contrato.valor_mensal) else False

    def esta_vencida(self):
        passou_data_pagm = True if datetime.today().date() > self.data_pagm_ref else False
        return True if self.esta_pago() is False and passou_data_pagm else False

    def vence_em_ate_x_dias(self, dias=int()):
        # Retorna True se esta parcela vence na quantidade definida em 'dias' ou menos disso
        # a partir do momento da execução da função
        vencimento = self.data_pagm_ref
        hoje = datetime.today().date()
        x_dias = datetime.today().date() + timedelta(days=dias)
        return True if x_dias > vencimento > hoje and not self.esta_vencida() else False

    def posicao(self):
        try:
            parcelas = list(
                Parcela.objects.filter(do_contrato=self.do_contrato, apagada=False).values_list('pk', flat=True))
            parcela = self.pk
            return parcelas.index(parcela) + 1
        except:
            return None

    def definir_apagada(self):
        self.apagada = True
        self.save(update_fields=['apagada'])

    def restaurar(self):
        self.apagada = False
        self.save(update_fields=['apagada'])

    def de_contrato_ativo(self):
        if (self.do_contrato.periodo_ativo_hoje() and self.do_contrato.em_posse is True and self.do_contrato.rescindido
                is False):
            return True
        else:
            return False

    def get_notific_all(self):
        # Retorna todas as notificações desda parcela
        tipo_conteudo = ContentType.objects.get_for_model(Parcela)
        notificacoes = Notificacao.objects.filter(do_usuario=self.do_usuario, objeto_id=self.pk,
                                                  autor_classe=tipo_conteudo)
        if notificacoes:
            return notificacoes

    def get_notific_pgm(self):
        # Retorna a notificação de pagamento detectado
        tipo_conteudo = ContentType.objects.get_for_model(Parcela)
        notificacao = Notificacao.objects.filter(do_usuario=self.do_usuario, objeto_id=self.pk,
                                                 autor_classe=tipo_conteudo, assunto=1)
        if notificacao:
            if notificacao.first().pk == 51:
                print('get_notific_pgm')
            return notificacao.first()

    def get_notific_esta_vencida(self):
        # Retorna a notificação de aviso: 'aluguel venceu'
        tipo_conteudo = ContentType.objects.get_for_model(Parcela)
        notificacao = Notificacao.objects.filter(do_usuario=self.do_usuario, objeto_id=self.pk,
                                                 autor_classe=tipo_conteudo, assunto=2)
        if notificacao:
            return notificacao.first()

    def get_notific_vence_em_ate_x_dias(self):
        # Retorna a notificação de aviso: 'faltam 5 dias para vencer'
        tipo_conteudo = ContentType.objects.get_for_model(Parcela)
        notificacao = Notificacao.objects.filter(do_usuario=self.do_usuario, objeto_id=self.pk,
                                                 autor_classe=tipo_conteudo, assunto=3)
        if notificacao:
            return notificacao.first()

    def lancar_entre(self):
        """Aqui temos as regras para o lançamento da notificação desta instância"""


lista_pagamentos = (
    (0, 'PIX'),
    (1, 'Din. Espécie'),
    (2, 'Boleto Banc.'),
    (3, 'Tranfer. Banc.'))


class Pagamento(models.Model):
    ao_locador = models.ForeignKey('Usuario', on_delete=models.CASCADE)
    ao_contrato = models.ForeignKey('Contrato', on_delete=models.CASCADE,
                                    verbose_name='Do Contrato')
    do_locatario = models.ForeignKey('Locatario', on_delete=models.CASCADE)

    valor_pago = models.CharField(max_length=9, verbose_name='Valor Pago (R$) ', blank=False,
                                  validators=[apenas_numeros])
    data_pagamento = models.DateTimeField(blank=False, verbose_name='Data do Pagamento')
    data_de_recibo = models.DateTimeField(blank=True, verbose_name='Data em que foi marcado recibo entregue', null=True)
    forma = models.IntegerField(blank=False, choices=lista_pagamentos, verbose_name='Forma de Pagamento')
    data_criacao = models.DateTimeField(auto_now_add=True)

    def valor_format(self):
        return valor_format(self.valor_pago)

    def __str__(self):
        return f'{self.do_locatario} - R${self.valor_format()} - {self.data_pagamento.strftime("%D")}'


class Gasto(models.Model):
    do_locador = models.ForeignKey('Usuario', null=False, on_delete=models.CASCADE)
    do_imovel = models.ForeignKey('Imovei', blank=True, null=True, on_delete=models.CASCADE,
                                  help_text='Deixe em branco para registrar um gasto avulso')

    valor = models.CharField(max_length=9, verbose_name='Valor Gasto (R$) ', blank=False, validators=[apenas_numeros])
    data = models.DateTimeField(blank=False)
    observacoes = models.TextField(max_length=500, blank=True, verbose_name='Observações')
    comprovante = ResizedImageField(size=[1280, None], upload_to='gastos_comprovantes/%Y/%m/', blank=True,
                                    verbose_name='Comporvante', validators=[tratar_imagem, FileExtensionValidator])
    data_criacao = models.DateTimeField(auto_now_add=True)

    def get_alsolute_url(self):
        return reverse('core:Gastos', args=[(str(self.pk)), ])

    def valor_format(self):
        return valor_format(self.valor)

    def __str__(self):
        return f'{self.observacoes[:20]} - {self.valor_format()} - {self.data.strftime("%D")}'


class Anotacoe(models.Model):
    do_usuario = models.ForeignKey('Usuario', null=False, on_delete=models.CASCADE)
    da_notificacao = models.OneToOneField('Notificacao', null=True, blank=True, on_delete=models.SET_NULL)

    titulo = models.CharField(blank=False, max_length=100, verbose_name='Título')
    data_registro = models.DateTimeField(blank=True)
    texto = models.TextField(blank=True, null=True)
    tarefa = models.BooleanField(default=False,
                                 help_text='Marque para adicionar este registro na sua lista de tarefas.')
    feito = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = 'Anotações'

    def tipo(self):
        if self.tarefa:
            if self.feito:
                return 'Tarefa concluída'
            else:
                return 'Tarefa pendente'
        else:
            return 'Anotação'

    def __str__(self):
        return f'{self.titulo} - {self.data_registro.strftime("%d/%m/%Y")}'

    def texto_pequeno(self):
        tamanho = 50
        if len(self.texto) == 0:
            return [0, '---']
        elif len(self.texto) < tamanho:
            return [1, self.texto]
        else:
            return [2, f'{self.texto[:tamanho]}...']


class Notificacao(models.Model):
    do_usuario = models.ForeignKey('Usuario', null=False, on_delete=models.CASCADE)
    autor_classe = models.ForeignKey(ContentType, null=False, on_delete=models.CASCADE)
    objeto_id = models.PositiveIntegerField(null=False)
    content_object = GenericForeignKey('autor_classe', 'objeto_id')
    assunto = models.PositiveIntegerField(null=True)

    data_registro = models.DateTimeField(auto_now_add=True)
    lida = models.BooleanField(default=False)
    apagada_oculta = models.BooleanField(default=False)
    data_lida = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-data_registro']
        verbose_name_plural = 'Notificações'

    def __str__(self):
        return f'Notificação: classe:{self.autor_classe} / objeto_id:{self.objeto_id}'

    def autor_tipo(self):
        if self.autor_classe == ContentType.objects.get_for_model(Parcela):
            if self.assunto == 1 or self.assunto is None:
                return 1
            elif self.assunto == 2:
                return 4
            elif self.assunto == 3:
                return 4
        elif self.autor_classe == ContentType.objects.get_for_model(Anotacoe):
            return 2
        elif self.autor_classe == ContentType.objects.get_for_model(Contrato):
            if self.assunto == 1 or self.assunto is None:
                return 3
            elif self.assunto == 2:
                return 4
            elif self.assunto == 3:
                return 4
        elif self.autor_classe == ContentType.objects.get_for_model(Sugestao):
            return 4
        elif self.autor_classe == ContentType.objects.get_for_model(Locatario):
            return 5
        elif self.autor_classe == ContentType.objects.get_for_model(Slot):
            return 6
        elif self.autor_classe == ContentType.objects.get_for_model(DevMensagen):
            return 7

    def autor_tipo_display(self):
        if self.autor_classe == ContentType.objects.get_for_model(Parcela):
            if self.assunto == 1 or self.assunto is None:
                return '🧾 Recibo'
            elif self.assunto == 2:
                return '⚠️ Aviso'
            elif self.assunto == 3:
                return '⚠️ Aviso'
        elif self.autor_classe == ContentType.objects.get_for_model(Anotacoe):
            return '🗒️ Tarefa'
        elif self.autor_classe == ContentType.objects.get_for_model(Contrato):
            if self.assunto == 1 or self.assunto is None:
                return '📃 Contrato'
            elif self.assunto == 2:
                return '⚠️ Aviso'
            elif self.assunto == 3:
                return '⚠️ Aviso'
        elif self.autor_classe == ContentType.objects.get_for_model(Sugestao):
            return '⚠️ Aviso'
        elif self.autor_classe == ContentType.objects.get_for_model(Locatario):
            return '👨‍💼 Locatário'
        elif self.autor_classe == ContentType.objects.get_for_model(Slot):
            return '⚠️ Aviso'
        elif self.autor_classe == ContentType.objects.get_for_model(DevMensagen):
            return '⚠️ Aviso'

    def borda(self):
        if self.autor_classe == ContentType.objects.get_for_model(Parcela):
            if self.assunto == 1 or self.assunto is None:
                return 'border-white'
            elif self.assunto == 2:
                return 'border-success'
            elif self.assunto == 3:
                return 'border-success'
        elif self.autor_classe == ContentType.objects.get_for_model(Anotacoe):
            return 'border-warning'
        elif self.autor_classe == ContentType.objects.get_for_model(Contrato):
            if self.assunto == 1 or self.assunto is None:
                return 'border-primary'
            elif self.assunto == 2:
                return 'border-success'
            elif self.assunto == 3:
                return 'border-success'
        elif self.autor_classe == ContentType.objects.get_for_model(Sugestao):
            return 'border-success'
        elif self.autor_classe == ContentType.objects.get_for_model(Locatario):
            return 'border-secondary'
        elif self.autor_classe == ContentType.objects.get_for_model(Slot):
            return 'border-success'
        elif self.autor_classe == ContentType.objects.get_for_model(DevMensagen):
            return 'border-success'

    def texto(self):
        mensagem = ''
        if self.autor_classe == ContentType.objects.get_for_model(Parcela):
            try:
                if self.assunto == 1 or self.assunto is None:
                    parcela = self.content_object
                    mensagem = f'O Pagamento de {parcela.do_contrato.do_locatario.primeiro_ultimo_nome().upper()}' \
                               f' referente à parcela de {data_ptbr(parcela.data_pagm_ref, "F/Y").upper()}' \
                               f'(Parcela {parcela.posicao()} de {parcela.do_contrato.duracao}) do contrato ' \
                               f'{parcela.do_contrato.codigo} em {parcela.do_contrato.do_imovel} foi detectado. ' \
                               f'Confirme a entrega do recibo.'
                if self.assunto == 2:
                    parcela = self.content_object
                    mensagem = f'O Pagamento de {parcela.do_contrato.do_locatario.primeiro_ultimo_nome().upper()}' \
                               f' referente à parcela de {data_ptbr(parcela.data_pagm_ref, "F/Y").upper()}' \
                               f'(Parcela {parcela.posicao()} de {parcela.do_contrato.duracao}) do contrato ' \
                               f'{parcela.do_contrato.codigo} em {parcela.do_contrato.do_imovel} está ' \
                               f'<span style="color:red">atrasado</span> desde ' \
                               f'{parcela.data_pagm_ref.strftime("%d/%m/%Y")}.'
                if self.assunto == 3:
                    parcela = self.content_object
                    mensagem = f'O Pagamento de {parcela.do_contrato.do_locatario.primeiro_ultimo_nome().upper()}' \
                               f' referente à parcela de {data_ptbr(parcela.data_pagm_ref, "F/Y").upper()}' \
                               f'(Parcela {parcela.posicao()} de {parcela.do_contrato.duracao}) do contrato ' \
                               f'{parcela.do_contrato.codigo} em {parcela.do_contrato.do_imovel} ' \
                               f'<span style="color:yellow">vencerá</span> em ' \
                               f'{parcela.data_pagm_ref.strftime("%d/%m/%Y")}. '
            except:
                pass
        elif self.autor_classe == ContentType.objects.get_for_model(Anotacoe):
            try:
                tamanho_max_txt = 200
                nota = self.content_object
                cortado = f'{nota.texto[:tamanho_max_txt]}...'
                mensagem = f'''{nota.titulo}<br>{nota.texto if len(nota.texto) <= tamanho_max_txt else cortado}'''
            except:
                pass
        elif self.autor_classe == ContentType.objects.get_for_model(Contrato):

            try:
                if self.assunto == 1 or self.assunto is None:
                    contrato = self.content_object
                    mensagem = f'O contrato {contrato} foi criado com sucesso!<br><br>' \
                               f'Depois de:<br>' \
                               f'1. Gerar e imprimir o documento referente(Gerar PDF de Contrato), <br>' \
                               f'2. Entregar ao locatário para reconhecimento em cartório, e <br>' \
                               f'3. Recebê-lo novamente com a firma reconhecida. <br>' \
                               f'Confirme a posse de sua via no botão abaixo para ativá-lo no sistema.'
                if self.assunto == 2:
                    contrato = self.content_object
                    mensagem = f'O contrato {contrato} <span style="color:yellow">está perto de seu vencimento</span>!' \
                               f'<br><br>' \
                               f'Data do vencimento: {contrato.data_saida().strftime("%d/%m/%Y")}<br><br>' \
                               f'Você pode providenciar um termo de renovação contratual ou pedir a entrega do ' \
                               f'imóvel ao locatário atual.'
                if self.assunto == 3:
                    contrato = self.content_object
                    mensagem = f'O contrato {contrato} <span style="color:red">venceu</span>!<br><br>' \
                               f'Data do vencimento: {contrato.data_saida()}<br><br>'
            except:
                pass

        elif self.autor_classe == ContentType.objects.get_for_model(Sugestao):
            try:
                tamanho_max_txt = 200
                sugestao = self.content_object
                cortado = f'{sugestao.corpo[:tamanho_max_txt]}...'
                mensagem = f'''Sua sugestão foi aprovada e está disponível para votação:<br>
                "{sugestao.corpo if len(sugestao.corpo) <= tamanho_max_txt else cortado}"'''
            except:
                pass
        elif self.autor_classe == ContentType.objects.get_for_model(Locatario):
            try:
                locatario = self.content_object
                mensagem = f'''Um novo locatário se registrou:<br>
                            Nome: {locatario.nome}<br>
                            Telefone: {cel_format(locatario.telefone1)}<br>
                            Email: {locatario.email}'''
            except:
                pass
        elif self.autor_classe == ContentType.objects.get_for_model(Slot):
            try:
                slot = self.content_object
                mensagem = f'''O imóvel {slot.imovel()} está desabilitado, por favor, acesse o painel para 
                habilitá-lo.'''
            except:
                pass
        elif self.autor_classe == ContentType.objects.get_for_model(DevMensagen):
            try:
                dev_msg = self.content_object
                mensagem = f'''O desenvolvedor respondeu a sua mensagem:<br> 
                "{dev_msg.titulo}"'''
            except:
                pass
        return mensagem

    def definir_apagada(self):
        self.apagada_oculta = True
        self.save(update_fields=['apagada_oculta'])

    def restaurar(self):
        self.apagada_oculta = False
        self.save(update_fields=['apagada_oculta'])

    def definir_nao_lida(self):
        self.lida = False
        self.data_lida = None
        self.data_registro = datetime.now()
        self.save(update_fields=['lida', 'data_registro'])

    def definir_lida(self):
        self.lida = True
        self.data_lida = datetime.now()
        self.save(update_fields=['lida', 'data_lida'])


lista_mensagem = (
    (1, 'Elogio'),
    (2, 'Reclamação'),
    (3, 'Dúvida'),
    (4, 'Report de bug'))


class DevMensagen(models.Model):
    do_usuario = models.ForeignKey('Usuario', null=True, blank=True, on_delete=models.CASCADE)
    da_notificacao = models.OneToOneField('Notificacao', null=True, blank=True, on_delete=models.SET_NULL)

    data_registro = models.DateTimeField(auto_now=True)
    titulo = models.CharField(blank=False, max_length=100)
    mensagem = models.TextField(blank=False)
    resposta = models.TextField(blank=True)
    tipo_msg = models.IntegerField(blank=False, choices=lista_mensagem)
    imagem = ResizedImageField(size=[1280, None], upload_to='mensagens_ao_dev/%Y/%m/', blank=True,
                               validators=[tratar_imagem, FileExtensionValidator])

    class Meta:
        verbose_name_plural = 'Mensagens ao Dev'

    def __str__(self):
        return f'{self.do_usuario} - {self.titulo} - {self.data_registro}'


class Sugestao(models.Model):
    do_usuario = models.ForeignKey('Usuario', null=True, blank=True, on_delete=models.CASCADE)
    da_notificacao = models.OneToOneField('Notificacao', null=True, blank=True, on_delete=models.SET_NULL)

    data_registro = models.DateTimeField(auto_now=True)
    corpo = models.TextField(max_length=1500, blank=False, null=False, verbose_name='')
    imagem = ResizedImageField(size=[1280, None], upload_to='sugestoes_docs/%Y/%m/', blank=True,
                               validators=[tratar_imagem, FileExtensionValidator], verbose_name='Imagem(opcional)')
    likes = models.ManyToManyField('Usuario', related_name='Likes', blank=True)
    implementada = models.BooleanField(default=False)
    aprovada = models.BooleanField(default=False)
    data_implementada = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name_plural = 'Sugestões'

    def __str__(self):
        return f'{self.do_usuario} - {self.corpo[:30]} - {self.data_registro}'

    def numero_de_likes(self):
        return self.likes.count()
