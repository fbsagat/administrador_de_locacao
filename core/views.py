import io, os, json, base64
from datetime import datetime, timedelta
from os import path
from math import floor
from random import randrange
from dateutil.relativedelta import relativedelta

from Alugue_seu_imovel import settings
from num2words import num2words
import xlsxwriter
from django.views.decorators.cache import never_cache
from django.db import transaction
from django.forms.models import model_to_dict
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.files import File
from django.core.files.storage import default_storage
from django.http import FileResponse, HttpResponse
from django.views.generic import CreateView, DeleteView, FormView, UpdateView, ListView
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import redirect, render, reverse, get_object_or_404, Http404, HttpResponseRedirect
from django.utils import timezone, dateformat
from django.urls import reverse_lazy
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import messages
from django.db.models.aggregates import Count, Sum
from django.contrib.postgres.aggregates import ArrayAgg
from django.template.defaultfilters import date as data_ptbr
from core.fakes_test import porcentagem_de_chance
from .tasks import enviar_email_conf_de_email, enviar_email_exclusao_de_conta, gerar_recibos_pdf, gerar_tabela_pdf, \
    gerar_contrato_pdf

from core.funcoes_proprias import valor_format, valor_por_extenso, _crypt, _decrypt, cpf_format, gerar_uuid_20, \
    modelo_variaveis, modelo_condicoes, gerar_uuid_64
from core.fakes_test import locatarios_ficticios, imoveis_ficticios, imov_grupo_fict, contratos_ficticios, \
    pagamentos_ficticios, gastos_ficticios, anotacoes_ficticias, usuarios_ficticios, sugestoes_ficticias, \
    modelos_contratos_ficticios
from core.forms import FormCriarConta, FormEmail, FormMensagem, FormEventos, FormAdmin, FormPagamento, FormGasto, \
    FormLocatario, FormImovel, FormAnotacoes, FormContrato, FormimovelGrupo, FormRecibos, FormTabela, \
    FormContratoDoc, FormContratoDocConfig, FormContratoModelo, FormUsuario, FormSugestao, FormTickets, FormSlots, \
    FormConfigNotific, FormConfigApp, FormToken

from core.models import Locatario, Contrato, Pagamento, Gasto, Anotacoe, ImovGrupo, Usuario, Imovei, Parcela, \
    Notificacao, ContratoDocConfig, ContratoModelo, Sugestao, DevMensagen, Slot, UsuarioContratoModelo, TempLink, \
    TempCodigo


# -=-=-=-=-=-=-=-= BOTÃO VISÃO GERAL -=-=-=-=-=-=-=-=


@login_required
def visao_geral(request):
    context = {}
    data = datetime.now().date() + timedelta(days=15)
    contratos = Contrato.objects.ativos_hoje_e_antes_de(data=data).filter(do_locador=request.user)
    usuario = Usuario.objects.get(pk=request.user.pk)

    # Sistema de ordenação inicio \/
    order_by = 'nome_do_locatario'
    if usuario.vis_ger_ultim_order_by:
        order_by = usuario.vis_ger_ultim_order_by
    if request.GET.get('order_by'):
        order_by = request.GET.get('order_by')

    context['reverter'] = ''
    if '-' not in order_by:
        context['reverter'] = '-'

    if 'nome_do_locatario' in order_by:
        contratos = contratos.order_by(f'{"-" if "-" in order_by else ""}do_locatario__nome')
    elif 'nome_do_imovel' in order_by:
        contratos = contratos.order_by(f'{"-" if "-" in order_by else ""}do_imovel__nome')
    elif 'valor_mensal' in order_by:
        contratos = sorted(contratos,
                           key=lambda a: int(a.valor_mensal) or datetime.now().date() + relativedelta(years=+ 100),
                           reverse=True if '-' in order_by else False)
    elif 'vencimento_atual' in order_by:
        contratos = sorted(contratos,
                           key=lambda a: a.vencimento_atual() or datetime.now().date() + relativedelta(years=+ 100),
                           reverse=True if '-' in order_by else False)
    elif 'divida_atual_valor' in order_by:
        contratos = sorted(contratos, key=lambda a: a.divida_atual_valor()[0],
                           reverse=True if '-' in order_by else False)
    elif 'recibos_entregues' in order_by:
        contratos0 = sorted(contratos, key=lambda a: a.recibos_entregues_qtd(),
                            reverse=True if '-' in order_by else False)
        contratos = sorted(contratos0,
                           key=lambda a: a.faltando_recibos_qtd(), reverse=True if '-' in order_by else False)
    elif 'total_quitado' in order_by:
        contratos = sorted(contratos,
                           key=lambda a: a.total_quitado(), reverse=True if '-' in order_by else False)
    elif 'dias_transcorridos' in order_by:
        contratos = sorted(contratos,
                           key=lambda a: a.transcorrido_dias(), reverse=True if '-' in order_by else False)

    usuario.vis_ger_ultim_order_by = order_by
    usuario.save(update_fields=['vis_ger_ultim_order_by', ])
    # Sistema de ordenação fim /\

    parametro_page = request.GET.get('page', '1')
    parametro_limite = request.GET.get('limit', request.user.itens_pag_visao_geral)
    contrato_pagination = Paginator(contratos, parametro_limite)

    try:
        page = contrato_pagination.page(parametro_page)
    except (EmptyPage, PageNotAnInteger):
        page = contrato_pagination.page(1)

    grupos = ImovGrupo.objects.filter(do_usuario=request.user)

    context['grupos'] = {}
    for grupo in grupos:
        arrecadacao_total = grupo.arrecadacao_total()
        arrecadacao_mensal = grupo.arrecadacao_mensal()
        valor_total_contratos_ativos = grupo.valor_total_contratos_ativos()
        valor_total_contratos = grupo.valor_total_contratos()
        context['grupos'][f'{grupo.nome}'] = [arrecadacao_total, arrecadacao_mensal, valor_total_contratos_ativos,
                                              valor_total_contratos]

    context['arrecadacao_total'] = usuario.arrecadacao_total()
    context['arrecadacao_mensal'] = usuario.arrecadacao_mensal()
    context['valor_total_contratos_ativos'] = usuario.valor_total_contratos_ativos()
    context['valor_total_contratos'] = usuario.valor_total_contratos()
    context['page_obj'] = page

    return render(request, 'exibir_visao_geral.html', context)


# -=-=-=-=-=-=-=-= BOTÃO EVENTOS -=-=-=-=-=-=-=-=


@login_required
def eventos(request):
    user = Usuario.objects.get(pk=request.user.pk)
    form = FormEventos()
    pagamentos = gastos = locatarios = contratos = imoveis = anotacoes = pg_tt = gasto_tt = contr_tt = pag_m_gast = ''
    agreg_1 = agreg_2 = int()
    pesquisa_req = True if user.data_eventos_i and user.itens_eventos and user.qtd_eventos and user.ordem_eventos else \
        False

    data_eventos_i = user.data_eventos_i
    data_eventos_f = datetime.now()
    itens_eventos = user.itens_eventos
    qtd_eventos = user.qtd_eventos
    ordem_eventos = int(user.ordem_eventos)
    if ordem_eventos == 2:
        ordem = ''
    elif ordem_eventos == 1:
        ordem = '-'

    if pesquisa_req:
        form = FormEventos(initial={'qtd': user.qtd_eventos, 'data_eventos_i': user.data_eventos_i.strftime('%Y-%m-%d'),
                                    'itens_eventos': list(user.itens_eventos), 'ordem_eventos': user.ordem_eventos})
    if request.method == 'POST':
        form = FormEventos(request.POST)
        if form.is_valid():
            pesquisa_req = True
            user.data_eventos_i = form.cleaned_data['data_eventos_i']
            user.itens_eventos = form.cleaned_data['itens_eventos']
            user.qtd_eventos = form.cleaned_data['qtd']
            user.ordem_eventos = form.cleaned_data['ordem_eventos']
            user.save(update_fields=["data_eventos_i", "itens_eventos", "qtd_eventos", "ordem_eventos"])

            data_eventos_i = form.cleaned_data['data_eventos_i']
            data_eventos_f = datetime.combine(form.cleaned_data['data_eventos_f'], datetime.now().time())
            itens_eventos = form.cleaned_data['itens_eventos']
            qtd_eventos = form.cleaned_data['qtd']
            ordem_eventos = int(form.cleaned_data['ordem_eventos'])
            if ordem_eventos == 2:
                ordem = ''
            elif ordem_eventos == 1:
                ordem = '-'

    if '1' in itens_eventos and pesquisa_req:
        pagamentos = Pagamento.objects.filter(ao_locador=request.user,
                                              data_pagamento__range=[data_eventos_i, data_eventos_f]).order_by(
            f'{ordem}data_pagamento')[:qtd_eventos]

        if settings.USAR_DB == 1:
            # SQlite3 agregation
            agreg_1 = pagamentos.aggregate(total=Sum("valor_pago"))
            if agreg_1["total"]:
                pg_tt = f'{valor_format(str(agreg_1["total"]))}'
        elif settings.USAR_DB == 2 or settings.USAR_DB == 3:
            # PostGreSQL agregation
            array = pagamentos.aggregate(arr=ArrayAgg('valor_pago'))
            t = 0
            for _ in array['arr']:
                t += int(_)
            agreg_1 = {'total': t}
            if agreg_1["total"]:
                pg_tt = f'{valor_format(str(agreg_1["total"]))}'

    if '2' in itens_eventos and pesquisa_req:
        gastos = Gasto.objects.filter(do_locador=request.user, data__range=[data_eventos_i, data_eventos_f]).order_by(
            f'{ordem}data')[:qtd_eventos]

        if settings.USAR_DB == 1:
            # SQlite3 agregation
            agreg_2 = gastos.aggregate(total=Sum("valor"))
            if agreg_2["total"]:
                gasto_tt = f'{valor_format(str(agreg_2["total"]))}'
        elif settings.USAR_DB == 2 or settings.USAR_DB == 3:
            # PostGreSQL agregation
            array = gastos.aggregate(total=ArrayAgg('valor'))
            t = 0
            for _ in array['total']:
                t += int(_)
            agreg_2 = {'total': t}
            if agreg_2["total"]:
                gasto_tt = f'{valor_format(str(agreg_2["total"]))}'

    if '1' and '2' in itens_eventos and pesquisa_req and agreg_1["total"] and agreg_2["total"]:
        pag_m_gast = valor_format(str(agreg_1["total"] - agreg_2["total"]))
    if '3' in itens_eventos and pesquisa_req:
        locatarios = Locatario.objects.nao_temporarios().filter(do_locador=request.user,
                                                                data_registro__range=[data_eventos_i,
                                                                                      data_eventos_f]).order_by(
            f'{ordem}data_registro')[:qtd_eventos]
    if '4' in itens_eventos and pesquisa_req:
        contratos = Contrato.objects.filter(do_locador=request.user,
                                            data_registro__range=[data_eventos_i, data_eventos_f]).order_by(
            f'{ordem}data_registro')[:qtd_eventos]

        if settings.USAR_DB == 1:
            # SQlite3 agregation
            contratotal = contratos.aggregate(total=Sum("valor_mensal"))["total"]
            if contratotal:
                contr_tt = f'{valor_format(str(contratotal))}'
        elif settings.USAR_DB == 2 or settings.USAR_DB == 3:
            # PostGreSQL agregation
            array = contratos.aggregate(total=ArrayAgg("valor_mensal"))
            t = 0
            for _ in array['total']:
                t += int(_)
            contratotal = {'total': t}
            if contratotal:
                contr_tt = f'{valor_format(str(contratotal["total"]))}'

    if '5' in itens_eventos and pesquisa_req:
        imoveis = Imovei.objects.filter(do_locador=request.user,
                                        data_registro__range=[data_eventos_i, data_eventos_f]).order_by(
            f'{ordem}data_registro')[:qtd_eventos]
    if '6' in itens_eventos and pesquisa_req:
        anotacoes = Anotacoe.objects.filter(do_usuario=request.user,
                                            data_registro__range=[data_eventos_i, data_eventos_f]).order_by(
            f'{ordem}data_registro')[:qtd_eventos]

    retornou_algo = True if locatarios or imoveis or pagamentos or gastos or contratos or anotacoes else False
    context = {'form': form, 'pagamentos': pagamentos, 'gastos': gastos, 'locatarios': locatarios,
               'contratos': contratos, 'imoveis': imoveis, 'anotacoes': anotacoes, 'pg_tt': pg_tt,
               'gasto_tt': gasto_tt, 'contr_tt': contr_tt, 'pag_m_gast': pag_m_gast,
               'retornou_algo': retornou_algo}
    return render(request, 'exibir_eventos.html', context)


# -=-=-=-=-=-=-=-= BOTÃO ATIVOS -=-=-=-=-=-=-=-=
class ImoveisAtivos(LoginRequiredMixin, ListView):
    template_name = 'exibir_ativos.html'
    model = Imovei
    context_object_name = 'imoveis'
    paginate_by = 12

    def get_paginate_by(self, queryset):
        self.paginate_by = self.request.user.itens_pag_ativos
        return self.paginate_by

    def get_queryset(self):
        self.object_list = Contrato.objects.ativos_hoje().filter(do_locador=self.request.user).order_by('-data_entrada')
        ativo_tempo = []
        for obj in self.object_list:
            ativo_tempo.append(obj.do_imovel)
        return ativo_tempo

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(ImoveisAtivos, self).get_context_data(**kwargs)
        context['imoveis_qtd'] = len(self.object_list)
        return context


class LocatariosAtivos(LoginRequiredMixin, ListView):
    template_name = 'exibir_ativos.html'
    model = Locatario
    context_object_name = 'locatarios'
    paginate_by = 12

    def get_paginate_by(self, queryset):
        self.paginate_by = self.request.user.itens_pag_ativos
        return self.paginate_by

    def get_queryset(self):
        self.object_list = Contrato.objects.ativos_hoje().filter(do_locador=self.request.user).order_by('-data_entrada')
        ativo = []
        for obj in self.object_list:
            if obj.do_locatario not in ativo:
                ativo.append(obj.do_locatario)
        return ativo

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(LocatariosAtivos, self).get_context_data(**kwargs)
        context['locatario_qtd'] = len(self.object_list)
        return context


class ContratosAtivos(LoginRequiredMixin, ListView):
    template_name = 'exibir_ativos.html'
    model = Contrato
    context_object_name = 'contratos'
    paginate_by = 12

    def get_paginate_by(self, queryset):
        self.paginate_by = self.request.user.itens_pag_ativos
        return self.paginate_by

    def get_queryset(self):
        self.object_list = Contrato.objects.ativos_hoje().filter(do_locador=self.request.user).order_by('-data_entrada')
        return self.object_list

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(ContratosAtivos, self).get_context_data(**kwargs)
        context['contrato_qtd'] = len(self.object_list)
        return context


# -=-=-=-=-=-=-=-= BOTÃO REGISTRAR -=-=-=-=-=-=-=-=

# PAGAMENTO ---------------------------------------
@login_required
def registrar_pagamento(request):
    form = FormPagamento(request.user, request.POST)
    if form.is_valid():
        contrato_pk = request.POST.get('ao_contrato')

        # se o imóvel do contrato está em slot \/
        contrato = Contrato.objects.get(pk=contrato_pk)
        if contrato.do_imovel.em_slot():
            pagamento = form.save(commit=False)
            pagamento.ao_locador = request.user
            locatario = contrato.do_locatario
            pagamento.do_locatario = locatario
            pagamento.save()
            messages.success(request, f"Pagamento registrado com sucesso!")
        else:
            messages.error(request,
                           f"O pagamento não foi registrado. Imóvel desabilitado. por favor, "
                           f"habilite-o no painel.")
        if 'form1' in request.session:
            del request.session['form1']

    else:
        request.session['form1'] = [request.POST, str(datetime.now().time().strftime('%H:%M:%S'))]
        messages.error(request, f"Formulário inválido.")
    return redirect(request.META['HTTP_REFERER'])


class ExcluirPagm(LoginRequiredMixin, DeleteView):
    model = Pagamento
    template_name = 'excluir_item.html'

    def get_success_url(self):
        return reverse_lazy('core:Pagamentos')

    def get_object(self, queryset=None):
        self.object = get_object_or_404(Pagamento, pk=self.kwargs['pk'], ao_locador=self.request.user)
        return self.object

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(ExcluirPagm, self).get_context_data(**kwargs)
        return context


# GASTO ---------------------------------------
@login_required
def registrar_gasto(request):
    form = FormGasto(request.POST, request.FILES)

    if form.is_valid():
        gasto = form.save(commit=False)
        gasto.do_locador = request.user
        gasto.save()
        messages.success(request, "Gasto registrado com sucesso!")
        if 'form3' in request.session:
            del request.session['form3']
        return redirect(request.META['HTTP_REFERER'])
    else:
        request.session['form3'] = [request.POST, str(datetime.now().time().strftime('%H:%M:%S'))]
        messages.error(request, "Formulário inválido.")
        return redirect(request.META['HTTP_REFERER'])


class EditarGasto(LoginRequiredMixin, UpdateView):
    model = Gasto
    template_name = 'editar_gasto.html'
    form_class = FormGasto

    def get_initial(self):
        return {'data': self.object.data.strftime('%Y-%m-%d')}

    def get_success_url(self):
        return reverse_lazy('core:Gastos')

    def get_object(self, queryset=None):
        self.object = get_object_or_404(Gasto, pk=self.kwargs['pk'], do_locador=self.request.user)
        return self.object


class ExcluirGasto(LoginRequiredMixin, DeleteView):
    model = Gasto
    template_name = 'excluir_item.html'

    def get_success_url(self):
        return reverse_lazy('core:Gastos')

    def get_object(self, queryset=None):
        self.object = get_object_or_404(Gasto, pk=self.kwargs['pk'], do_locador=self.request.user)
        return self.object

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(ExcluirGasto, self).get_context_data(**kwargs)
        return context


# LOCATARIO ---------------------------------------
@login_required
def registrar_locat(request):
    form = FormLocatario(request.POST, request.FILES, usuario=request.user.pk)
    if form.is_valid():
        locatario = form.save(commit=False)
        locatario.do_locador = request.user
        cpf = _crypt(message=form.cleaned_data['cpf'])
        locatario.cript_cpf = cpf
        locatario.save()
        messages.success(request, "Locatário registrado com sucesso!")
        if 'form4' in request.session:
            del request.session['form4']
        return redirect(request.META['HTTP_REFERER'])
    else:
        request.session['form4'] = [request.POST, str(datetime.now().time().strftime('%H:%M:%S'))]
        messages.error(request, f"Formulário inválido.")
        return redirect(request.META['HTTP_REFERER'])


def locat_auto_registro(request, code):
    user = get_object_or_404(Usuario, locat_auto_registro_url=code)
    context = {}
    if request.method == 'POST':
        form = FormLocatario(request.POST, request.FILES, usuario=request.user.pk)

        if form.is_valid():
            locatario = form.save(commit=False)
            locatario.do_locador = user
            locatario.temporario = True
            cpf = _crypt(message=form.cleaned_data['cpf'])
            locatario.cript_cpf = cpf
            locatario.save()
            messages.success(request, "Dados enviados com sucesso! Aguarde o contato do locador.")
            return redirect(reverse('core:Locatario Auto-Registro', args=[code]))
        else:
            messages.error(request, f"Formulário inválido.")
            context['form'] = form
            return render(request, 'locatario_auto_registro.html', context)
    else:
        form = FormLocatario(usuario=request.user.pk)

    context['form'] = form
    return render(request, 'locatario_auto_registro.html', context)


def trocar_link_auto_registro(request):
    if request.user.is_anonymous is False:
        user = request.user
        user.locat_auto_registro_url = gerar_uuid_64()
        user.save(update_fields=['locat_auto_registro_url', ])
    return redirect(request.META['HTTP_REFERER'])


class RevisarLocat(LoginRequiredMixin, UpdateView):
    model = Locatario
    template_name = 'revisar_locatario.html'
    form_class = FormLocatario

    def get_success_url(self):
        return reverse_lazy('core:Locatários')

    def get_object(self, queryset=None):
        notific = get_object_or_404(Notificacao, pk=self.kwargs.get('pk'), do_usuario=self.request.user)
        self.object = get_object_or_404(Locatario, pk=notific.content_object.pk, do_locador=self.request.user,
                                        temporario=True)
        return self.object

    def get_form(self, form_class=None):
        if form_class is None:
            form_class = self.get_form_class()
        return form_class(**self.get_form_kwargs(), usuario=self.request.user)

    def form_valid(self, form):
        self.object = form.save()
        self.object.temporario = None
        notific = get_object_or_404(Notificacao, pk=self.kwargs.get('pk'), do_usuario=self.request.user)
        notific.definir_lida()
        return super().form_valid(form)

    def get_initial(self):
        return {'nome': self.object.nome, 'RG': self.object.RG, 'cpf': self.object.cpf(),
                'ocupacao': self.object.ocupacao,
                'endereco_completo': self.object.endereco_completo,
                'telefone1': self.object.telefone1, 'telefone2': self.object.telefone2,
                'estadocivil': self.object.estadocivil,
                'nacionalidade': self.object.nacionalidade, 'email': self.object.email}

    def get_context_data(self, *, object_list=True, **kwargs):
        context = super(RevisarLocat, self).get_context_data(**kwargs)
        context['form'] = self.get_form()
        return context


# CONTRATO ---------------------------------------
@login_required
def registrar_contrato(request):
    form = FormContrato(request.user, request.POST)
    if form.is_valid():
        imovel_pk = request.POST.get('do_imovel')
        imovel = get_object_or_404(Imovei, pk=imovel_pk, do_locador=request.user)
        if imovel.em_slot():
            contrato = form.save(commit=False)
            contrato.do_locador = request.user
            contrato.save()
            messages.success(request, "Contrato registrado com sucesso!")
            if 'form5' in request.session:
                del request.session['form5']
        else:
            messages.error(request,
                           f"O contrato não foi registrado. Imóvel desabilitado. por favor, "
                           f"habilite-o no painel.")
    else:
        request.session['form5'] = [request.POST, str(datetime.now().time().strftime('%H:%M:%S'))]
        messages.error(request, "Formulário inválido.")

    return redirect(request.META['HTTP_REFERER'])


def validar_contrato_no_imovel_na_data(contrato, entrada, saida):
    """Esta função verifica se tem outro contrato ativo neste imóvel neste período.
    # Se existir algum contrato com datas de entrada e saida entre o período registrado no contrato de
    entrada, esta entrada é bloqueada pela função, retorna False, caso contrário retorna True.
    # Obs: Existe uma cópia deste validador em forms. """

    contratos_deste_imovel = Contrato.objects.filter(do_imovel=contrato.do_imovel, rescindido=False).exclude(
        pk=contrato.pk)
    entrada_novo = entrada
    saida_novo = saida
    permitido = True
    for n, contrato in enumerate(contratos_deste_imovel):
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
        return True if permitido else False


@login_required
def rescindir_contrat(request, pk):
    contrato = get_object_or_404(Contrato, pk=pk, do_locador=request.user)
    if contrato.do_locador == request.user:
        if contrato.rescindido is True:
            entrada = contrato.data_entrada
            saida = contrato.data_saida()
            if validar_contrato_no_imovel_na_data(contrato, entrada, saida) is False:
                messages.warning(request, f"Já existe um contrato registrado para este imóvel neste período.")
            else:
                contrato.data_de_rescisao = datetime.now()
                data = dateformat.format(datetime.now(), 'd-m-Y')
                contrato.rescindido = False
                contrato.save(update_fields=['rescindido', 'data_de_rescisao'])
                messages.success(request, f"Contrato ativado com sucesso! Registro criado em {data}.")
                return redirect(request.META['HTTP_REFERER'])
        else:
            contrato.data_de_rescisao = datetime.now()
            data = dateformat.format(datetime.now(), 'd-m-Y')
            contrato.rescindido = True
            contrato.save(update_fields=['rescindido', 'data_de_rescisao'])
            messages.warning(request, f"Contrato rescindido com sucesso! Registro criado em {data}.")
        return redirect(request.META['HTTP_REFERER'])
    else:
        raise Http404


@login_required
def recebido_contrat(request, pk, tipo):
    if tipo == 'n':
        notific = get_object_or_404(Notificacao, do_usuario=request.user, pk=pk)
        contrato = notific.content_object
    elif tipo == 'c':
        contrato = get_object_or_404(Contrato, do_locador=request.user, pk=pk)
        notific = contrato.get_notific_criado()

    if contrato.do_locador == request.user:
        if contrato.em_posse is True:
            contrato.em_posse = False
        else:
            contrato.em_posse = True
            if notific:
                notific.definir_lida()
            messages.success(request, f"Cópia do contrato do locador em mãos!")
        contrato.save(update_fields=['em_posse', ])
        return redirect(request.META['HTTP_REFERER'])
    else:
        raise Http404


# IMOVEL ---------------------------------------
@login_required
def registrar_imovel(request):
    if request.method == 'POST':
        form = FormImovel(request.user, request.POST)
        if form.is_valid():
            if request.user.tem_slot_disponivel():
                imovel = form.save(commit=False)
                imovel.do_locador = request.user
                imovel.save()
                messages.success(request, "Imóvel registrado com sucesso!")
            else:
                messages.success(request,
                                 "Usuário não possui slot disponível para registrar um imóvel, por favor, "
                                 "acesse o painel para habilitar.")
            if 'form6' in request.session:
                del request.session['form6']
            return redirect(request.META['HTTP_REFERER'])
        else:
            request.session['form6'] = [request.POST, str(datetime.now().time().strftime('%H:%M:%S'))]
            messages.error(request, "Formulário inválido.")
            return redirect(request.META['HTTP_REFERER'])


# ANOTAÇÃO ---------------------------------------
@login_required
def registrar_anotacao(request):
    form = FormAnotacoes(request.POST)
    if form.is_valid():
        nota = form.save(commit=False)
        nota.do_usuario = request.user
        nota.save()

        if form.cleaned_data['tarefa']:
            messages.success(request, "Tarefa registrada com sucesso!")
        else:
            messages.success(request, "Anotação registrada com sucesso!")
        if 'form7' in request.session:
            del request.session['form7']
        return redirect(request.META['HTTP_REFERER'])
    else:
        request.session['form7'] = [request.POST, str(datetime.now().time().strftime('%H:%M:%S'))]
        messages.error(request, "Formulário inválido.")
        return redirect(request.META['HTTP_REFERER'])


# -=-=-=-=-=-=-=-= BOTÃO GERAR -=-=-=-=-=-=-=-=
@login_required
def recibos(request):
    contratos_ativos = Contrato.objects.ativos_margem().filter(do_locador=request.user).order_by('-data_entrada')

    form = FormRecibos()
    form.fields['contrato'].queryset = contratos_ativos
    context = {}

    # Indica se o usuario tem contrato para o template e ja pega o primeiro para carregar\/
    usuario = Usuario.objects.get(pk=request.user.pk)
    tem_contratos = contratos_ativos.first()

    if tem_contratos:
        contrato = tem_contratos

        # Indíca para o template se o usuário preencheu os dados necessários para gerar os recibos\/
        pede_dados = False
        if usuario.first_name == '' or usuario.last_name == '' or usuario.cpf() == '':
            pede_dados = True
        else:
            if request.user.recibo_ultimo:
                contrato = Contrato.objects.get(pk=request.user.recibo_ultimo.pk)

            # Carrega do model do usuario o ultimo recibo salvo no form, se existe\/
            if usuario.recibo_ultimo and usuario.recibo_preenchimento:
                form = FormRecibos(
                    initial={'contrato': usuario.recibo_ultimo, 'data_preenchimento': usuario.recibo_preenchimento})
                form.fields['contrato'].queryset = contratos_ativos

            # Se for um post, salvar o novo contrato no campo 'ultimo recibo salvo' do usuario e etc...\/
            if request.method == 'POST':
                form = FormRecibos(request.POST)
                form.fields['contrato'].queryset = contratos_ativos
                if form.is_valid():
                    contrato = get_object_or_404(Contrato, pk=form.cleaned_data['contrato'].pk, do_locador=request.user)
                    usuario.recibo_preenchimento = form.cleaned_data['data_preenchimento']
                    usuario.recibo_ultimo = contrato
                    usuario.save(update_fields=['recibo_ultimo', 'recibo_preenchimento'])

            # Criar o arquivo se não existe ou carregar se existe:
            if contrato.recibos_pdf and path.isfile(f'{settings.MEDIA_ROOT}/{contrato.recibos_pdf}'):
                pass
            else:
                locatario = contrato.do_locatario
                imovel = contrato.do_imovel

                # Tratamentos
                reais = int(contrato.valor_mensal[:-2])
                centavos = int(contrato.valor_mensal[-2:])
                num_ptbr_reais = num2words(reais, lang='pt_BR')
                completo = ''
                if centavos > 0:
                    num_ptbr_centavos = num2words(centavos, lang='pt_BR')
                    completo = f' E {num_ptbr_centavos} centavos'
                codigos = list(
                    Parcela.objects.filter(do_contrato=contrato.pk, apagada=False).order_by('data_pagm_ref').values(
                        "codigo").values_list('codigo', flat=True))
                datas = list(
                    Parcela.objects.filter(do_contrato=contrato.pk, apagada=False).order_by('data_pagm_ref').values(
                        "data_pagm_ref").values_list('data_pagm_ref', flat=True))
                datas_tratadas = list()
                data_preenchimento = list()
                for data in datas:
                    month = data_ptbr(data, "F")
                    year = data.strftime('%Y')
                    datas_tratadas.append(f'{month.upper()}')
                    datas_tratadas.append(f'{year}')

                if usuario.recibo_preenchimento == '2':
                    for x in range(0, contrato.duracao):
                        data = contrato.data_entrada + relativedelta(months=x)
                        data_preenchimento.append(
                            f'{contrato.do_imovel.cidade}, '
                            f'____________ ,____ de {data_ptbr(data.replace(day=contrato.dia_vencimento), "F")} de '
                            f'{data_ptbr(data.replace(day=contrato.dia_vencimento), "Y")}')
                elif usuario.recibo_preenchimento == '3':
                    dia_venc = contrato.dia_vencimento
                    for x in range(0, contrato.duracao):
                        data = contrato.data_entrada + relativedelta(months=x)
                        data_preenchimento.append(
                            f'{contrato.do_imovel.cidade}, '
                            f'{data_ptbr(data.replace(day=dia_venc), "l, d")} de '
                            f'{data_ptbr(data.replace(day=dia_venc), "F")} de '
                            f'{data_ptbr(data.replace(day=dia_venc), "Y")}')

                # Preparar dados para envio
                dados = {'cod_contrato': f'{contrato.codigo}',
                         'nome_locador': f'{usuario.first_name.upper()} {usuario.last_name.upper()}',
                         'rg_locd': f'{usuario.RG}',
                         'cpf_locd': f'{usuario.cpf()}',
                         'nome_locatario': f'{locatario.nome.upper()}',
                         'rg_loct': f'{locatario.RG}',
                         'cpf_loct': f'{locatario.cpf()}',
                         'valor_e_extenso': f'{contrato.valor_format()} ({num_ptbr_reais.upper()} REAIS{completo.upper()})',
                         'endereco': f"{imovel.endereco_completo()}",
                         'cidade': f'{imovel.cidade}',
                         'data_preenchimento': data_preenchimento,
                         'cod_recibo': codigos,
                         'mes_e_ano': datas_tratadas,
                         }

                local_temp = gerar_recibos_pdf.delay(dados)
                pdf_data = json.loads(local_temp.get())
                base64_encoded_pdf = pdf_data['file_content']
                pdf_bytes = base64.b64decode(base64_encoded_pdf)
                pdf_bytesio = io.BytesIO(pdf_bytes)

                contrato.recibos_pdf = File(pdf_bytesio,
                                            name=f'recibos_de_{usuario.recibos_code()}_{dados["cod_contrato"]}.pdf')
                contrato.save()

        context = {'form': form, 'contrato': contrato, 'tem_contratos': tem_contratos, 'pede_dados': pede_dados}
        return render(request, 'gerar_recibos.html', context)
    else:
        context = {'tem_contratos': tem_contratos}
        return render(request, 'gerar_recibos.html', context)


@login_required
def tabela(request):
    # Criar a pasta tabela_docs se não existe
    pasta = rf'{settings.MEDIA_ROOT}/tabela_docs/'
    se_existe = os.path.exists(pasta)
    if not se_existe:
        os.makedirs(pasta)

    # Cria o objeto usuario
    usuario = Usuario.objects.get(pk=request.user.pk)

    # Cria os meses a partir da mes atual do usuario para escolher no form
    meses = []
    mes_inicial = datetime.now().replace(day=1) - relativedelta(months=4)

    for mes in range(9):
        meses.append(
            (mes, str(data_ptbr(mes_inicial + relativedelta(months=mes), "F/Y"))))

    # Carregar os dados de mes para o form e tabela a partir da informação salva no perfil
    # ou timezone.now quando não há info salva
    if (usuario.tabela_ultima_data_ger is not None and usuario.tabela_meses_qtd is not None
            and usuario.tabela_imov_qtd is not None and usuario.tabela_mostrar_ativos is not None
            and request.method == 'GET'):

        form = FormTabela(initial={'mes': usuario.tabela_ultima_data_ger, 'mostrar_qtd': usuario.tabela_meses_qtd,
                                   'itens_qtd': usuario.tabela_imov_qtd,
                                   'mostrar_ativos': usuario.tabela_mostrar_ativos})
        a_partir_de = datetime.now().replace(day=1) - relativedelta(months=4 - usuario.tabela_ultima_data_ger)
        mostrar_somente_ativos = usuario.tabela_mostrar_ativos
        meses_qtd = usuario.tabela_meses_qtd
        imov_qtd = usuario.tabela_imov_qtd
    else:
        form = FormTabela(initial={'mes': 4})
        a_partir_de = datetime.now().replace(day=1)
        mostrar_somente_ativos = False
        meses_qtd = 7
        imov_qtd = 10

    # Salva o último post do 'form' no perfil do usuario, se 'form' valido
    if request.method == 'POST':
        form = FormTabela(request.POST)
        if form.is_valid():
            usuario.tabela_ultima_data_ger = int(form.cleaned_data['mes'])
            usuario.tabela_mostrar_ativos = int(form.cleaned_data['mostrar_ativos'])
            usuario.tabela_meses_qtd = int(form.cleaned_data['mostrar_qtd'])
            usuario.tabela_imov_qtd = int(form.cleaned_data['itens_qtd'])
            usuario.save(update_fields=["tabela_ultima_data_ger", 'tabela_meses_qtd', 'tabela_imov_qtd',
                                        'tabela_mostrar_ativos'])
            a_partir_de = datetime.now().replace(day=1) - relativedelta(months=4 - int(form.cleaned_data['mes']))
            mostrar_somente_ativos = form.cleaned_data['mostrar_ativos']
            meses_qtd = int(form.cleaned_data['mostrar_qtd'])
            imov_qtd = int(form.cleaned_data['itens_qtd'])

    # coloca as choices no form.(todos acima)
    form.fields['mes'].choices = meses

    # Tratamento de dados para a tabela \/
    # Definir o último dia do último mês
    ate = (a_partir_de + relativedelta(months=meses_qtd)) + timedelta(days=-1)

    # Cria a lista de mes/ano para a tabela a partir da mes definida pelo usuario na variavel ('a_partir_de')
    datas = []
    for data in range(0, meses_qtd):
        datas.append(str(data_ptbr(a_partir_de + relativedelta(months=data), "F/Y")).title())

    def gerar_dados_de_imoveis_para_tabela_pdf(def_contratos_ativos):
        """
        Objetivo geral: Fazer um dicionário dos imoveis ativos contendo estas informações:
        1. Nomes dos imoveis.
        2. Lista com as parcelas dos imoveis entre as datas a_partir_de e até (inclusive as parcelas de outros
                contratos inativos deste imóvel, que estejas entre as datas citadas) ou 'Sem contrato' caso não haja
                 contrato nesta data.
        3. Lista boolean indicando as parcelas que estão ativas(com True) dentre todas as listadas em 'parcelas'.
        4. Lista com os sinais(texto auxiliar) para cada parcela de cada imovel. """

        def_imoveis = {'nomes': [], 'parcelas': [], 'parcelas_ativas': [], 'sinais:': []}

        def imovel_parcelas(contrato, datas):
            """
            Essa função deve retornar as parcelas de um imóvel a partir do parâmetro/objeto contrato, organizadas em
             uma lista do tamanho da quantidade de meses no parâmetro datas (len(datas)). Caso haja conflito, ou seja,
             duas parcelas referentes ao mesmo período, a do contrato ativo é priorizada, ficando assim apenas uma parcela
              no slot. """
            todas_parcelas = Parcela.objects.filter(do_imovel=contrato.do_imovel, apagada=False,
                                                    data_pagm_ref__range=[a_partir_de, ate]).order_by(
                '-do_contrato__data_entrada')
            imovel_meses = {}
            parcelas_ativas = []
            for num, mes in enumerate(datas):
                # 'colocar aqui a parcela do contrato ativo(na data respectiva/parametro mes do for), ou a parcela do
                # contrato inativo (na data respectiva/parametro mes do for), ou none'.
                imovel_mes = []
                for parcela in todas_parcelas:
                    if str(data_ptbr(parcela.data_pagm_ref, "F/Y").title()) == str(datas[num]):
                        imovel_mes.append(parcela)
                imovel_meses[datas[num]] = imovel_mes or None

            for key, values in imovel_meses.items():
                if values is not None:
                    if len(values) > 1:
                        count = 0
                        while len(values) > 1:
                            values.pop()
                            count += 1
                        if values[0].de_contrato_ativo():
                            parcelas_ativas.append(True)
                        else:
                            parcelas_ativas.append(False)
                    else:
                        if values[0].de_contrato_ativo():
                            parcelas_ativas.append(True)
                        else:
                            parcelas_ativas.append(False)
                else:
                    parcelas_ativas.append(False)
            return imovel_meses, parcelas_ativas

        def parcelas_formatadas(def_lista_parcelas):
            """ Esta função tem por objetivo formatar os parcelas, de objeto, para texto, texto este que preencherá
            os campos no arquivo PDF com dados de cada imóvel em cada mês, como em uma agenda. """
            lista_parcelas_compl = []
            lista_parcsinais_compl = []
            for parcela in def_lista_parcelas:
                parcelas = []
                sinais = []
                lista_parcelas_compl.append(parcelas)
                lista_parcsinais_compl.append(sinais)
                for mes in range(0, meses_qtd):
                    for parc in parcela:
                        if parc is not None:
                            pago = parc.esta_pago()
                            recibo = parc.recibo_entregue
                            vencido = parc.esta_vencida()
                            sinal = ''
                            if pago and recibo:
                                enviar = 'Pago! Recibo entregue'
                                sinal += str('Ok')
                            else:
                                if pago:
                                    enviar = 'Pago! Recibo não entregue'
                                    sinal += 'Re'
                                else:
                                    if vencido:
                                        enviar = f"""O Pagam. VENCEU dia {parc.do_contrato.dia_vencimento}
                                            Pg: {parc.tt_pago_format()} F: {parc.falta_pagar_format()}
                                            """
                                        sinal += 'Ve'
                                    else:
                                        enviar = f"""O Pagam. Vencerá dia {parc.do_contrato.dia_vencimento}
                                            P:{parc.tt_pago_format()} F:{parc.falta_pagar_format()}
                                            """
                            parcelas.append(f"""Com: {parc.do_locatario.primeiro_ultimo_nome()}
                                Contr. cód.: {parc.do_contrato.codigo}
                                Valor: {parc.do_contrato.valor_format()}
                                {enviar}""")
                            sinais.append(sinal)
                        else:
                            parcelas.append('Sem contrato')
                            sinais.append('')

                if len(parcelas) - meses_qtd != 0:
                    del parcelas[-(len(parcelas) - meses_qtd):]
                if len(sinais) - meses_qtd != 0:
                    del sinais[-(len(sinais) - meses_qtd):]

            return lista_parcelas_compl, lista_parcsinais_compl

        imoveis_nomes = []
        parcelas_ativas = []
        lista_parcelas = []

        for contrato in def_contratos_ativos:
            imoveis_nomes.append(contrato.do_imovel.__str__())
            imovel_parcelas_final = imovel_parcelas(contrato, datas)
            lista_parcelas.append(imovel_parcelas_final[0])
            parcelas_ativas.append(imovel_parcelas_final[1])

        lista_parcelas_format = []
        for i in lista_parcelas:
            items = []
            for key, value in i.items():
                if value is not None:
                    items.append(value[0])
                else:
                    items.append(None)
            lista_parcelas_format.append(items)

        parcelas_e_sinais = parcelas_formatadas(lista_parcelas_format)

        def_imoveis['nomes'] = imoveis_nomes
        def_imoveis['parcelas'] = parcelas_e_sinais[0]
        def_imoveis['parcelas_ativas'] = parcelas_ativas
        def_imoveis['sinais'] = parcelas_e_sinais[1]
        return def_imoveis

    # Pegando informações dos imoveis que possuem contrato no período selecionado para preenchimento da tabela
    if mostrar_somente_ativos:
        contratos = Contrato.objects.ativos_hoje().filter(do_locador=request.user).order_by('-data_entrada')
    else:
        contratos = Contrato.objects.ativos_hoje_e_antes_de(data=ate.date()).filter(do_locador=request.user).order_by(
            '-data_entrada')
    imoveis = gerar_dados_de_imoveis_para_tabela_pdf(contratos)

    dados = {"usuario_uuid": usuario.uuid,
             "usuario_username": usuario.username,
             "usuario_nome_compl": usuario.nome_completo().upper(),
             'imov_qtd': imov_qtd,
             'datas': datas,
             'imoveis': imoveis}

    # Finalizando para envio ao template -==-==-==-==-==-

    # Cria o context e já adiciona o campo SITE_NAME
    context = {}

    # verifica se o usuario tem contrato para o template assumir outro comportamento
    tem_contratos = True if Contrato.objects.filter(do_locador=request.user.pk).first() else False
    context['tem_contratos'] = tem_contratos

    tem_imoveis = True if len(imoveis['nomes']) > 0 else False
    context['tem_imoveis'] = tem_imoveis

    if tem_contratos:
        # Gerar a tabela com os dados
        local_temp = gerar_tabela_pdf.delay(dados)

        # Link da tabela
        link = '/tabela_docs/'
        nome = f'tabela_{request.session.session_key}_{usuario}.pdf'

        pdf_data = json.loads(local_temp.get())
        base64_encoded_pdf = pdf_data['file_content']
        pdf_bytes = base64.b64decode(base64_encoded_pdf)
        pdf_bytesio = io.BytesIO(pdf_bytes)
        file_path = f'{settings.MEDIA_ROOT}{link}{nome}'

        with default_storage.open(file_path, 'wb') as destination:
            pdf_bytesio.seek(0)
            destination.write(pdf_bytesio.read())

    file_path_django = rf'/media/tabela_docs/tabela_{request.session.session_key}_{usuario}.pdf'
    # Preparar o context
    context['tabela'] = file_path_django
    context['form'] = form

    return render(request, 'gerar_tabela.html', context)


@login_required
def gerar_contrato(request):
    context = {}
    # Criando objetos para tratamentos
    usuario = Usuario.objects.get(pk=request.user.pk)
    contrato_ultimo = usuario.contrato_ultimo
    contr_doc_configs = ContratoDocConfig.objects.filter(do_contrato=contrato_ultimo).first()
    form = FormContratoDoc(initial={'contrato': contrato_ultimo})
    form2 = FormContratoDocConfig()  # ver se ainda é util: initial={'do_modelo': contr_doc_configs.do_modelo}
    qs1 = ContratoModelo.objects.filter(usuarios=request.user).order_by('-data_criacao')
    form2.fields['do_modelo'].queryset = qs1
    contratos_ativos = Contrato.objects.ativos_margem().filter(do_locador=request.user).order_by('-data_entrada')

    # Se for POST
    if request.method == 'POST':
        # Se for um POST do primeiro form
        if 'contrato' in request.POST:
            form = FormContratoDoc(request.POST)
            form.fields['contrato'].queryset = contratos_ativos
            if form.is_valid():
                # Se o form for valido atualiza o campo contrato_ultimo do usuario
                usuario.contrato_ultimo = form.cleaned_data['contrato']
                usuario.save(update_fields=['contrato_ultimo', ])
                # O contrato carregado inicialmente pelo campo do usuario(contrato_ultimo) é atualizado para o
                # do form(mais atual)
                contrato_ultimo = form.cleaned_data['contrato']
                contr_doc_configs = ContratoDocConfig.objects.filter(do_contrato=contrato_ultimo).first()

        # Se for um POST do segundo form
        elif 'do_modelo' in request.POST:
            form2 = FormContratoDocConfig(request.POST)
            if form2.is_valid():
                configs = form2.save(commit=False)
                configs.do_contrato = contrato_ultimo
                if form2.cleaned_data['fiador_nome'] and form2.cleaned_data['fiador_cript_cpf']:
                    pass
                else:
                    configs.fiador_RG = None
                    configs.fiador_cript_cpf = None
                    configs.fiador_ocupacao = None
                    configs.fiador_nacionalidade = None
                    configs.fiador_estadocivil = None
                    configs.fiador_endereco_completo = None

                if contr_doc_configs:
                    # Se o form for válido e houver configs para o contrato selecionado, atualiza a instância do
                    # ContratoDocConfig deste contrato.
                    configs.pk = contr_doc_configs.pk
                    cpf = form2.cleaned_data['fiador_cript_cpf']
                    configs.fiador_cript_cpf = _crypt(cpf)
                    configs.save()
                else:
                    # Se o form for válido e não houver configs para o contrato selecionado, cria uma instância do
                    # ContratoDocConfig para o contrato selecionado.
                    cpf = form2.cleaned_data['fiador_cript_cpf']
                    configs.fiador_cript_cpf = _crypt(cpf)
                    configs.save()
                return redirect(reverse('core:Contrato PDF'))
            else:
                context['form2'] = form2
                context['contrato_ultimo_nome'] = contrato_ultimo

        elif request.POST.get("mod", ""):
            form2 = FormContratoDocConfig(
                initial={'do_modelo': contr_doc_configs.do_modelo,
                         'tipo_de_locacao': contr_doc_configs.tipo_de_locacao,
                         'caucao': contr_doc_configs.caucao,
                         'fiador_nome': contr_doc_configs.fiador_nome,
                         'fiador_RG': contr_doc_configs.fiador_RG,
                         'fiador_cript_cpf': contr_doc_configs.f_cpf(),
                         'fiador_ocupacao': contr_doc_configs.fiador_ocupacao,
                         'fiador_endereco_completo': contr_doc_configs.fiador_endereco_completo,
                         'fiador_nacionalidade': contr_doc_configs.fiador_nacionalidade,
                         'fiador_estadocivil': contr_doc_configs.fiador_estadocivil})
            form2.fields['do_modelo'].queryset = qs1
            contr_doc_configs = None

    form.fields['contrato'].queryset = contratos_ativos
    context['form'] = form

    if contr_doc_configs and contr_doc_configs.do_modelo:
        imovel = contrato_ultimo.do_imovel
        imov_grupo = contrato_ultimo.do_imovel.grupo
        contrato = contrato_ultimo
        locatario = contrato_ultimo.do_locatario
        try:
            contrato_anterior = Contrato.objects.filter(do_locatario=locatario, do_imovel=imovel).order_by('-pk')[1]
        except:
            contrato_anterior = None
        data = datetime.today()
        # Se o contrato tem configurações para o documento e todas estão presentes(principalmente o modelo)
        # Verificar se os campos obrigatório estão validos(para não ocorrer erros)
        # Carregar o contrato e liberar o botão para modificar configurações
        erro1 = '<span style="color:#ffffff"><strong><span style="background-color:#ff0000">' \
                '[ESTE DADO DO LOCADOR NÃO FOI PREENCHIDO]</span></strong></span>'
        erro2 = '<span style="color:#ffffff"><strong><span style="background-color:#ff0000">' \
                '[ESTE DADO DO CONTRATO NÃO FOI PREENCHIDO]</span></strong></span>'
        erro3 = '<span style="color:#ffffff"><strong><span style="background-color:#ff0000">' \
                '[NÃO EXISTE CONTRATO ANTERIOR A ESTE]</span></strong></span>'
        erro4 = '<span style="color:#ffffff"><strong><span style="background-color:#ff0000">' \
                '[ESTE DADO DO IMÓVEL NÃO FOI PREENCHIDO]</span></strong></span>'
        erro5 = '<span style="color:#ffffff"><strong><span style="background-color:#ff0000">' \
                '[ESTE DADO DO FIADOR NÃO FOI PREENCHIDO]</span></strong></span>'
        erro6 = '<span style="color:#ffffff"><strong><span style="background-color:#ff0000">' \
                '[ESTE DADO DO LOCATÁRIO NÃO FOI PREENCHIDO]</span></strong></span>'
        erro7 = '<span style="color:#ffffff"><strong><span style="background-color:#ff0000">' \
                '[ESTE DADO NÃO FOI PREENCHIDO]</span></strong></span>'

        caucao = None
        caucao_por_extenso = None
        if contr_doc_configs.caucao and contrato.valor_mensal:
            caucao = valor_format(str(contr_doc_configs.caucao * int(contrato.valor_mensal)))
            caucao_por_extenso = valor_por_extenso(str(contr_doc_configs.caucao * int(contrato.valor_mensal)))

        fields = ['id', 'corpo', ]
        dados = {'modelo': model_to_dict(contr_doc_configs.do_modelo, fields=fields),
                 'contrato_pk': contrato.pk,
                 'contrato_code': usuario.contrato_code(),

                 # A partir deste ponto, variaveis do contrato \/
                 # Regra:
                 # A variavel no documento: [!variavel: locador_pagamento_2]
                 # logo o nome deve ser: locador_pagamento_2

                 'semana_extenso_hoje': f'{data_ptbr(data, "l")}',
                 'data_extenso_hoje': f'{data_ptbr(data, "d")} de {data_ptbr(data, "F")}  de {data_ptbr(data, "Y")}',
                 'data_hoje': str(data.strftime('%d/%m/%Y')),
                 'tipo_de_locacao': erro7 if contr_doc_configs.tipo_de_locacao is None else \
                     contr_doc_configs.get_tipo_de_locacao_display(),
                 'caucao': caucao or erro7,
                 'caucao_por_extenso': caucao_por_extenso or erro7,

                 'locador_nome_completo': usuario.nome_completo() or erro1,
                 'locador_nacionalidade': getattr(usuario, 'nacionalidade') or erro1,
                 'locador_estado_civil': str(usuario.get_estadocivil_display() or erro1),
                 'locador_ocupacao': getattr(usuario, 'ocupacao') or erro1,
                 'locador_rg': str(getattr(usuario, 'RG') or erro1),
                 'locador_cpf': usuario.f_cpf() or erro1,
                 'locador_telefone': usuario.f_tel() or erro1,
                 'locador_endereco_completo': getattr(usuario, 'endereco_completo') or erro1,
                 'locador_email': getattr(usuario, 'email') or erro1,
                 'locador_pagamento_1': getattr(usuario, 'dados_pagamento1') or erro1,
                 'locador_pagamento_2': getattr(usuario, 'dados_pagamento2') or erro1,

                 'contrato_data_entrada': str(contrato.data_entrada.strftime('%d/%m/%Y') or erro2),
                 'contrato_data_saida': str(contrato.data_saida().strftime('%d/%m/%Y') or erro2),
                 'contrato_codigo': getattr(contrato, 'codigo') or erro2,
                 'contrato_periodo': str(getattr(contrato, 'duracao') or erro2),
                 'contrato_periodo_por_extenso': contrato.duracao_meses_por_extenso() or erro2,
                 'contrato_parcela_valor': contrato.valor_format() or erro2,
                 'contrato_parcela_valor_por_extenso': contrato.valor_por_extenso() or erro2,
                 'contrato_valor_total': contrato.valor_do_contrato_format() or erro2,
                 'contrato_valor_total_por_extenso': str(contrato.valor_do_contrato_por_extenso() or erro2),
                 'contrato_vencimento': str(getattr(contrato, 'dia_vencimento') or erro2),
                 'contrato_vencimento_por_extenso': contrato.dia_vencimento_por_extenso() or erro2,

                 'contrato_anterior-codigo':
                     getattr(contrato_anterior, 'codigo') or erro2 if contrato_anterior else erro3,
                 'contrato_anterior-parcela_valor':
                     contrato_anterior.valor_format() or erro2 if contrato_anterior else erro3,
                 'contrato_anterior-parcela_valor_por_extenso':
                     contrato_anterior.valor_por_extenso() or erro2 if contrato_anterior else erro3,
                 'contrato_anterior_valor_total':
                     contrato_anterior.valor_do_contrato_format() or erro2 if contrato_anterior else erro3,
                 'contrato_anterior_valor_total_por_extenso':
                     str(contrato_anterior.valor_do_contrato_por_extenso() or erro2) if contrato_anterior else erro3,
                 'contrato_anterior_vencimento':
                     str(getattr(contrato_anterior, 'dia_vencimento') or erro2) if contrato_anterior else erro3,
                 'contrato_anterior_vencimento_por_extenso':
                     contrato_anterior.dia_vencimento_por_extenso() or erro2 if contrato_anterior else erro3,
                 'contrato_anterior-data_entrada':
                     str(contrato_anterior.data_entrada.strftime('%d/%m/%Y') or erro2) if contrato_anterior else erro3,
                 'contrato_anterior-data_saida':
                     str(contrato_anterior.data_saida().strftime('%d/%m/%Y') or erro2) if contrato_anterior else erro3,
                 'contrato_anterior-periodo':
                     str(getattr(contrato_anterior, 'duracao') or erro2) if contrato_anterior else erro3,
                 'contrato_anterior-periodo_por_extenso':
                     str(contrato_anterior.duracao_meses_por_extenso() or erro2) if contrato_anterior else erro3,

                 'imovel_rotulo': getattr(imovel, 'nome') or erro4,
                 'imovel_uc_energia': getattr(imovel, 'uc_energia') or erro4,
                 'imovel_uc_sanemameto': getattr(imovel, 'uc_agua') or erro4,
                 'imovel_endereco_completo': imovel.endereco_completo() or erro4,
                 'imovel_cidade': getattr(imovel, 'cidade') or erro4,
                 'imovel_estado': imovel.get_estado_display() or erro4,
                 'imovel_bairro': imovel.bairro or erro4,
                 'imovel_grupo': str(getattr(imovel, 'grupo') or erro4),
                 'imovel_grupo_tipo': imov_grupo.get_tipo_display() or erro4 if imov_grupo else erro4,

                 'fiador_nome_completo': getattr(contr_doc_configs, 'fiador_nome') or erro5,
                 'fiador_cpf': contr_doc_configs.f_cpf() or erro5,
                 'fiador_rg': getattr(contr_doc_configs, 'fiador_RG') or erro5,
                 'fiador_nacionalidade': getattr(contr_doc_configs, 'fiador_nacionalidade') or erro5,
                 'fiador_estado_civil': contr_doc_configs.get_fiador_estadocivil_display() or erro5,
                 'fiador_ocupacao': getattr(contr_doc_configs, 'fiador_ocupacao') or erro5,
                 'fiador_endereco_completo': getattr(contr_doc_configs, 'fiador_endereco_completo') or erro5,

                 'locatario_nome_completo': getattr(locatario, 'nome') or erro6,
                 'locatario_cpf': locatario.f_cpf() or erro6,
                 'locatario_rg': getattr(locatario, 'RG') or erro6,
                 'locatario_nacionalidade': getattr(locatario, 'nacionalidade') or erro6,
                 'locatario_estado_civil': locatario.get_estadocivil_display() or erro6,
                 'locatario_ocupacao': getattr(locatario, 'ocupacao') or erro6,
                 'locatario_endereco_completo': getattr(locatario, 'endereco_completo') or erro6,
                 'locatario_celular_1': locatario.f_tel1() or erro6,
                 'locatario_celular_2': locatario.f_tel2() or erro6,
                 'locatario_email': getattr(locatario, 'email') or erro6,
                 }
        local = f'contrato_docs/{dados["contrato_code"]}{dados['modelo']['id']}-contrato_{dados["contrato_pk"]}.pdf'
        gerar_contrato_pdf.delay(dados=dados, local=local)

        # Preparar o context
        context['contrato_doc'] = fr'/media/{local}'
    else:
        if contrato_ultimo:
            # Se o contrato não tem configurações, carrega o formulário de configuração para criar uma instância
            # de configurações para este contrato
            context['form2'] = form2
            context['contrato_ultimo_nome'] = contrato_ultimo

    context['tem_contratos'] = True if contratos_ativos else False
    context['contrato_ultimo'] = True if contrato_ultimo is not None else False
    return render(request, 'gerar_contrato.html', context)

@login_required
@never_cache
def criar_modelo(request):
    context = {}
    form = FormContratoModelo(request=request)

    if request.method == 'POST':
        form = FormContratoModelo(request.POST)
        if form.is_valid():
            modelo = form.save(commit=False)
            modelo.autor = request.user
            modelo.save()
            modelo.usuarios.add(request.user)
            return redirect(reverse('core:Modelos'))
        else:
            if 'já existe' in str(form.errors):
                messages.error(request, f'Por favor, escolha outro nome para este modelo de contrato')
            else:
                messages.error(request, f'O tamanho do arquivo está maior do que o permitido, o limite é de'
                                        f' {settings.TAMANHO_DO_MODELO_Mb}Mb')
            messages.error(request, f'O tamanho do arquivo está maior do que o permitido, o limite é de'
                                    f' {settings.TAMANHO_DO_MODELO_Mb}Mb')

    context['form'] = form
    context['variaveis'] = modelo_variaveis
    context['condicoes'] = modelo_condicoes
    return render(request, 'criar_modelo.html', context)


@login_required
def copiar_modelo(request, pk):
    modelo = get_object_or_404(ContratoModelo, pk=pk)
    if (modelo.comunidade is True and request.user not in modelo.usuarios.all()
            and request.user not in modelo.excluidos.all()):
        modelo.usuarios.add(request.user.pk)
    return redirect(reverse('core:Modelos'))


@login_required
def visualizar_modelo(request, pk):
    context = {}
    modelo = get_object_or_404(ContratoModelo, pk=pk)
    if request.user in modelo.excluidos.all():
        raise Http404
    else:
        # Cria o modelo caso não tenha sido criado, por algum erro, pelo signals ou tenha sido apagado do armazenamento.
        path_completo = fr'{settings.MEDIA_ROOT}/{modelo.visualizar}'
        if not os.path.isfile(path_completo):
            fields = ['id', 'corpo', ]
            dados = {'modelo_pk': modelo.pk, 'modelo': model_to_dict(modelo, fields=fields),
                     'usuario_username': str(modelo.autor.username),
                     'contrato_modelo_code': modelo.autor.contrato_modelo_code()}
            local = f'contratos_modelos/{dados["contrato_modelo_code"]}{dados["modelo_pk"]}.pdf'
            gerar_contrato_pdf.delay(dados=dados, local=local, visualizar=True)
            ContratoModelo.objects.filter(pk=modelo.pk).update(visualizar=local)

        if modelo.autor == request.user or modelo.comunidade or request.user in modelo.usuarios.all():
            context['modelo'] = modelo
            return render(request, 'visualizar_contratos_modelos.html', context)
        else:
            raise Http404


class MeusModelos(LoginRequiredMixin, ListView):
    template_name = 'exibir_modelos.html'
    model = ContratoModelo
    context_object_name = 'modelos'
    paginate_by = 9

    def get_queryset(self):
        user = self.request.user
        qs1 = UsuarioContratoModelo.objects.filter(usuario__in=[user, ]).exclude(
            contrato_modelo__excluidos__in=[user, ])
        return qs1.order_by('-data_criacao')


class ModelosComunidade(LoginRequiredMixin, ListView):
    template_name = 'modelos_da_comunidade.html'
    model = ContratoModelo
    context_object_name = 'modelos'
    paginate_by = 9

    def get_queryset(self):
        # Aqui mostrar todos os modelos de contratos com comunidade True, retirar os que o usuário está em excluídos,
        # retirar os que o usuário está em usuários
        user = self.request.user
        qs1 = ContratoModelo.objects.filter(comunidade=True, autor=user).exclude(excluidos__in=[user, ])
        qs2 = ContratoModelo.objects.filter(comunidade=True).exclude(excluidos__in=[user, ])
        return qs1.union(qs2).order_by('-data_criacao')


@transaction.atomic
@login_required
def editar_modelo(request, pk):
    local_debug = False
    context = {}
    modelo__ = get_object_or_404(ContratoModelo, pk=pk)
    form = FormContratoModelo(request=request, instance=modelo__)
    context['form'] = form
    context['object'] = modelo__
    context['variaveis'] = modelo_variaveis
    context['condicoes'] = modelo_condicoes

    def criar_um_modelo(modelo, _um, _dois):
        if local_debug:
            print('bora criar_um_modelo')
        novo_modelo = ContratoModelo.objects.create(autor=request.user, titulo=form_titulo,
                                                    corpo=form_corpo, descricao=form_descr,
                                                    comunidade=form_comun)
        novo_modelo.usuarios.add(request.user)
        modelo.usuarios.remove(request.user)
        if modelo.autor == request.user:
            modelo.comunidade = False
            modelo.excluidos.add(request.user)
        if _um and not _dois:
            if local_debug:
                print('só config usa este modelo')
            modelo.titulo = f'config/{gerar_uuid_20()}'
            modelo.comunidade = False

            # remover o arquivo visualizar e o campo visualizar da model
            diretorio = fr'{settings.MEDIA_ROOT}/{modelo.visualizar}'
            se_existe = os.path.isfile(diretorio)
            if se_existe:
                os.remove(diretorio)
            modelo.visualizar = None
            modelo.variaveis = None
            modelo.condicoes = None
            modelo.save(update_fields=['titulo', 'comunidade', 'visualizar', 'variaveis', 'condicoes', ])

        if local_debug:
            print('criei um novo modelo')

    def atualizar_o_modelo(modelo, _um, _dois):
        if local_debug:
            print('bora atualizar_o_modelo')
        modelo.autor = request.user
        modelo.titulo = form_titulo
        if modelo.corpo != form_corpo:
            modelo.corpo = form_corpo
            if local_debug:
                print('atualizou corpo no banco')
        else:
            if local_debug:
                print('não precisou atualizar corpo no banco')
        if modelo.descricao != form_descr:
            modelo.descricao = form_descr
            if local_debug:
                print('atualizou descrição no banco')
        else:
            if local_debug:
                print('não precisou atualizar descrição no banco')
        modelo.comunidade = form_comun
        modelo.data_criacao = datetime.now()
        modelo.usuarios.remove(request.user)
        modelo.usuarios.add(request.user)
        modelo.save()
        if local_debug:
            print('atualizei esse modelo')

    if request.method == "POST":
        form = FormContratoModelo(request=request, data=request.POST, instance=modelo__)
        if form.is_valid():
            modelo_ = get_object_or_404(ContratoModelo, pk=pk)
            form_titulo = form.cleaned_data['titulo']
            form_descr = form.cleaned_data['descricao']
            form_corpo = form.cleaned_data['corpo']
            form_comun = form.cleaned_data['comunidade']

            config_usa = modelo_.verificar_utilizacao_config()
            usuario_usa = modelo_.verificar_utilizacao_usuarios()

            # NO ATO DE O USUÁRIO EDITAR UM MODELO:
            # QUANDO EU DEVO CRIAR UM MODELO NOVO?
            # Quando o corpo, compartilhar, título ou descrição do modelo for diferente e ele não for o único usuário

            # QUANDO EU DEVO MODIFICAR O MODELO EXISTENTE?
            # Quando o corpo, compartilhar, título ou descrição do modelo for diferente e ele for o único usuário

            # QUANDO EU NÃO DEVO FAZER NADA?
            # Quando o corpo, compartilhar, título ou descrição do modelo forem idênticos ao inicial

            if local_debug:
                print('O q fazer?')
            if (form_titulo != modelo_.titulo or form_comun != modelo_.comunidade or form_descr != modelo_.descricao or
                    form_corpo != modelo_.corpo):
                if local_debug:
                    print('titulo ou descrição ou corpo ou comunidade diferentes')
                if usuario_usa:
                    if local_debug:
                        print('Tem outros usuários usando o modelo')
                    criar_um_modelo(modelo=modelo_, _um=config_usa, _dois=usuario_usa)
                else:
                    if local_debug:
                        print('Não tem outros usuários usando o modelo')
                    if config_usa:
                        if local_debug:
                            print('Tem configurações usando este modelo')
                        if form_corpo != modelo_.corpo:
                            if local_debug:
                                print('O corpo do modelo está diferente')
                            criar_um_modelo(modelo=modelo_, _um=config_usa, _dois=usuario_usa)
                    else:
                        atualizar_o_modelo(modelo=modelo_, _um=config_usa, _dois=usuario_usa)
            else:
                if local_debug:
                    print('Não fiz nada')

            return redirect(reverse_lazy('core:Modelos'))

        else:
            if 'O tamanho do arquivo está maior do que o permitido' in str(form.errors):
                messages.error(request, f'O tamanho do arquivo está maior do que o permitido, o limite é de'
                                        f' {settings.TAMANHO_DO_MODELO_Mb}Mb')
            form = FormContratoModelo(request=request, data=request.POST, instance=modelo__)
            context['form'] = form

    return render(request, 'editar_modelo.html', context)


class ExcluirModelo(LoginRequiredMixin, DeleteView):
    model = ContratoModelo
    template_name = 'excluir_item.html'

    def form_valid(self, form):
        success_url = self.get_success_url()
        self.object.delete(kwargs=dict(user_pk=self.request.user.pk))
        return HttpResponseRedirect(success_url)

    def get_success_url(self):
        if self.kwargs['pag_orig'] == 1:
            return reverse_lazy('core:Modelos Comunidade')
        else:
            return reverse_lazy('core:Modelos')

    def get_object(self, queryset=None):
        self.object = get_object_or_404(ContratoModelo, pk=self.kwargs['pk'])
        return self.object

    def get_context_data(self, *, object_list=True, **kwargs):
        context = super(ExcluirModelo, self).get_context_data(**kwargs)
        contratos_config = ContratoDocConfig.objects.filter(do_modelo=self.object,
                                                            do_contrato__do_locador=self.request.user).values_list(
            'do_contrato')
        contratos = Contrato.objects.filter(pk__in=contratos_config)
        context['contratos_modelo'] = contratos
        return context


# -=-=-=-=-=-=-=-= BOTÃO HISTÓRICO -=-=-=-=-=-=-=-=

# PAGAMENTOS ---------------------------------------
class Pagamentos(LoginRequiredMixin, ListView):
    template_name = 'exibir_pagamentos.html'
    model = Pagamento
    context_object_name = 'pagamentos'
    paginate_by = 54

    def get_paginate_by(self, queryset):
        self.paginate_by = self.request.user.itens_pag_pagamentos
        return self.paginate_by

    def get_queryset(self):
        self.object_list = Pagamento.objects.filter(ao_locador=self.request.user).order_by('-data_criacao')
        return self.object_list


# GASTOS ---------------------------------------
class Gastos(LoginRequiredMixin, ListView):
    template_name = 'exibir_gastos.html'
    model = Gasto
    context_object_name = 'gastos'
    paginate_by = 54

    def get_paginate_by(self, queryset):
        self.paginate_by = self.request.user.itens_pag_gastos
        return self.paginate_by

    def get_queryset(self):
        self.object_list = Gasto.objects.filter(do_locador=self.request.user).order_by('-data_criacao')
        return self.object_list


# GRUPO ---------------------------------------
@login_required
def criar_grupo(request):
    if request.method == "GET":
        grupos = ImovGrupo.objects.filter(do_usuario=request.user)
        form = FormimovelGrupo()
        context = {'form': form if ImovGrupo.objects.filter(do_usuario=request.user).count() <= 17 else '',
                   'grupos': grupos}
        return render(request, 'criar_grupos.html', context)
    elif request.method == 'POST':
        nome = request.POST.get('nome')
        tipo = request.POST.get('tipo')
        do_usuario = request.user
        grupo = ImovGrupo(nome=nome, do_usuario=do_usuario, tipo=tipo)
        grupo.save()
        return redirect(request.META['HTTP_REFERER'])


class EditarGrup(LoginRequiredMixin, UpdateView):
    model = ImovGrupo
    template_name = 'editar_grupo.html'
    form_class = FormimovelGrupo

    def get_success_url(self):
        return reverse_lazy('core:Criar Grupo Imóveis')

    def get_object(self, queryset=None):
        self.object = get_object_or_404(ImovGrupo, pk=self.kwargs['pk'], do_usuario=self.request.user)
        return self.object


class ExcluirGrupo(LoginRequiredMixin, DeleteView):
    model = ImovGrupo
    template_name = 'excluir_item.html'

    def get_success_url(self):
        return reverse_lazy('core:Criar Grupo Imóveis')

    def get_object(self, queryset=None):
        self.object = get_object_or_404(ImovGrupo, pk=self.kwargs['pk'], do_usuario=self.request.user)
        return self.object


# IMOVEIS ---------------------------------------
class Imoveis(LoginRequiredMixin, ListView):
    template_name = 'exibir_imoveis.html'
    model = Imovei
    context_object_name = 'imoveis'
    paginate_by = 27

    def get_paginate_by(self, queryset):
        self.paginate_by = self.request.user.itens_pag_imoveis
        return self.paginate_by

    def get_queryset(self):
        self.object_list = Imovei.objects.filter(do_locador=self.request.user).order_by('-data_registro')
        return self.object_list


class EditarImov(LoginRequiredMixin, UpdateView):
    model = Imovei
    template_name = 'editar_imovel.html'
    form_class = FormImovel

    def get_form_kwargs(self, **kwargs):
        form_kwargs = super(EditarImov, self).get_form_kwargs(**kwargs)
        form_kwargs["user"] = self.request.user
        return form_kwargs

    def get_success_url(self):
        return reverse_lazy('core:Imóveis')

    def get_object(self, queryset=None):
        self.object = get_object_or_404(Imovei, pk=self.kwargs['pk'], do_locador=self.request.user)
        return self.object


class ExcluirImov(LoginRequiredMixin, DeleteView):
    model = Imovei
    template_name = 'excluir_item.html'

    def get_success_url(self):
        return reverse_lazy('core:Imóveis')

    def get_object(self, queryset=None):
        self.object = get_object_or_404(Imovei, pk=self.kwargs['pk'], do_locador=self.request.user)
        return self.object

    def get_context_data(self, *, object_list=True, **kwargs):
        context = super(ExcluirImov, self).get_context_data(**kwargs)
        context['aviso'] = ('Tem certeza de que deseja apagar o imóvel selecionado? Todos os contratos e seus'
                            ' respectivos registros de pagamentos também serão removidos.')
        return context


# LOCATARIOS ---------------------------------------
class Locatarios(LoginRequiredMixin, ListView):
    template_name = 'exibir_locatarios.html'
    model = Locatario
    context_object_name = 'locatarios'
    paginate_by = 27

    def get_paginate_by(self, queryset):
        self.paginate_by = self.request.user.itens_pag_locatarios
        return self.paginate_by

    def get_queryset(self):
        self.object_list = Locatario.objects.nao_temporarios().filter(do_locador=self.request.user).order_by(
            '-data_registro').annotate(
            Count('do_locador'))
        return self.object_list


class EditarLocat(LoginRequiredMixin, UpdateView):
    model = Locatario
    template_name = 'editar_locatario.html'
    form_class = FormLocatario

    def get_success_url(self):
        return reverse_lazy('core:Locatários')

    def get_object(self, queryset=None):
        self.object = get_object_or_404(Locatario, pk=self.kwargs['pk'], do_locador=self.request.user)
        return self.object

    def get_form(self, form_class=None):
        if form_class is None:
            form_class = self.get_form_class()
        return form_class(**self.get_form_kwargs(), usuario=self.request.user)

    def form_valid(self, form):
        self.object = form.save()
        cpf = _crypt(message=form.cleaned_data['cpf'])
        self.object.cript_cpf = cpf
        return super().form_valid(form)

    def get_initial(self):
        return {'nome': self.object.nome, 'RG': self.object.RG, 'cpf': self.object.cpf(),
                'ocupacao': self.object.ocupacao,
                'endereco_completo': self.object.endereco_completo,
                'telefone1': self.object.telefone1, 'telefone2': self.object.telefone2,
                'estadocivil': self.object.estadocivil,
                'nacionalidade': self.object.nacionalidade, 'email': self.object.email}

    def get_context_data(self, *, object_list=True, **kwargs):
        context = super(EditarLocat, self).get_context_data(**kwargs)
        context['form'] = self.get_form()
        return context


class ExcluirLocat(LoginRequiredMixin, DeleteView):
    model = Locatario
    template_name = 'excluir_item.html'

    def get_success_url(self):
        if self.request.session.get('ult_pag_valida_reverse', None):
            return reverse(self.request.session.get('ult_pag_valida_reverse'))
        else:
            return reverse('core:Locatários')

    def get_object(self, queryset=None):
        self.object = get_object_or_404(Locatario, pk=self.kwargs['pk'], do_locador=self.request.user)
        return self.object

    def get_context_data(self, *, object_list=True, **kwargs):
        context = super(ExcluirLocat, self).get_context_data(**kwargs)
        if self.get_object().temporario is True:
            pass
        else:
            context['aviso'] = (''
                                'Tem certeza de que deseja apagar o locatário selecionado? Todos os seus contratos e'
                                ' respectivos registros de pagamentos também serão removidos.')
        return context


# CONTRATOS ---------------------------------------
class Contratos(LoginRequiredMixin, ListView):
    template_name = 'exibir_contratos.html'
    model = Contrato
    context_object_name = 'contratos'
    paginate_by = 27

    def get_paginate_by(self, queryset):
        self.paginate_by = self.request.user.itens_pag_contratos
        return self.paginate_by

    def get_queryset(self):
        self.object_list = Contrato.objects.filter(do_locador=self.request.user).order_by('-data_registro')
        return self.object_list


class EditarContrato(LoginRequiredMixin, UpdateView):
    model = Contrato
    template_name = 'editar_contrato.html'
    form_class = FormContrato
    success_url = reverse_lazy('/')

    def get_initial(self):
        return {'data_entrada': self.object.data_entrada.strftime('%Y-%m-%d')}

    def get_form_kwargs(self, **kwargs):
        form_kwargs = super(EditarContrato, self).get_form_kwargs(**kwargs)
        form_kwargs["user"] = self.request.user
        return form_kwargs

    def get_success_url(self):
        contrato = Contrato.objects.get(pk=self.object.pk)
        contrato.recibos_pdf.delete()
        contrato.save()
        return reverse_lazy('core:Contratos')

    def get_object(self, queryset=None):
        self.object = get_object_or_404(Contrato, pk=self.kwargs['pk'], do_locador=self.request.user)
        return self.object


class ExcluirContrato(LoginRequiredMixin, DeleteView):
    model = Contrato
    template_name = 'excluir_item.html'

    def get_success_url(self):
        if self.request.session.get('ult_pag_valida_reverse', None):
            return reverse(self.request.session.get('ult_pag_valida_reverse'))
        else:
            return reverse('core:Contratos')

    def get_object(self, queryset=None):
        self.object = get_object_or_404(Contrato, pk=self.kwargs['pk'], do_locador=self.request.user)
        return self.object

    def get_context_data(self, *, object_list=True, **kwargs):
        context = super(ExcluirContrato, self).get_context_data(**kwargs)
        context['aviso'] = ('Tem certeza de que deseja apagar o contrato selecionado? Todos os pagamentos referentes a'
                            ' ele também serão removidos.')
        return context


# ANOTAÇÕES ---------------------------------------
class Notas(LoginRequiredMixin, ListView):
    template_name = 'exibir_anotacao.html'
    model = Anotacoe
    context_object_name = 'anotacoes'
    paginate_by = 27
    form_class = FormAnotacoes

    def get_paginate_by(self, queryset):
        self.paginate_by = self.request.user.itens_pag_notas
        return self.paginate_by

    def get_queryset(self):
        self.object_list = Anotacoe.objects.filter(do_usuario=self.request.user).order_by('-data_registro')
        return self.object_list

    def get_context_data(self, *, object_list=True, **kwargs):
        context = super(Notas, self).get_context_data(**kwargs)
        return context


class EditarAnotacao(LoginRequiredMixin, UpdateView):
    model = Anotacoe
    template_name = 'editar_anotacao.html'
    form_class = FormAnotacoes
    success_url = reverse_lazy('/')

    def get_initial(self):
        return {'data_registro': self.object.data_registro.strftime('%Y-%m-%d')}

    def get_success_url(self):
        return reverse_lazy('core:Anotações')

    def get_object(self, queryset=None):
        self.object = get_object_or_404(Anotacoe, pk=self.kwargs['pk'], do_usuario=self.request.user)
        return self.object


class ExcluirAnotacao(LoginRequiredMixin, DeleteView):
    model = Anotacoe
    template_name = 'excluir_item.html'

    def get_success_url(self):
        return reverse_lazy('core:Anotações')

    def get_object(self, queryset=None):
        self.object = get_object_or_404(Anotacoe, pk=self.kwargs['pk'], do_usuario=self.request.user)
        return self.object


# -=-=-=-=-=-=-=-= TAREFAS -=-=-=-=-=-=-=-=
@login_required
def recibo_entregue(request, pk):
    notific = get_object_or_404(Notificacao, pk=pk, do_usuario=request.user)
    parcela = Parcela.objects.get(pk=notific.objeto_id)
    if parcela.recibo_entregue is True:
        parcela.recibo_entregue = False
    else:
        parcela.recibo_entregue = True
        notific.definir_lida()
    parcela.save(update_fields=['recibo_entregue', ])
    return redirect(request.META['HTTP_REFERER'])


@login_required
def afazer_concluida(request, pk):
    notific = get_object_or_404(Notificacao, pk=pk, do_usuario=request.user)
    nota = Anotacoe.objects.get(pk=notific.objeto_id)
    if nota.feito is True:
        nota.feito = False
    else:
        nota.feito = True
        notific.definir_lida()
    nota.save(update_fields=['feito', ])
    return redirect(request.META['HTTP_REFERER'])


@login_required
def aviso_lido(request, pk):
    notific = get_object_or_404(Notificacao, pk=pk, do_usuario=request.user)
    if notific.lida is False or notific.lida is None:
        notific.definir_lida()
    else:
        notific.lida = False
        notific.save(update_fields=['lida', ])
    return redirect(request.META['HTTP_REFERER'])


@login_required
def notificacao_lida(request, pk):
    notific = get_object_or_404(Notificacao, pk=pk, do_usuario=request.user)
    if notific.lida is False or notific.lida is None:
        notific.definir_lida()
    else:
        notific.definir_nao_lida()
    return redirect(request.META['HTTP_REFERER'])


# -=-=-=-=-=-=-=-= USUARIO -=-=-=-=-=-=-=-=

class Homepage(FormView):
    template_name = 'home.html'
    form_class = FormEmail

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(reverse('core:Visão Geral'))
        else:
            return super().get(request, *args, **kwargs)

    def get_success_url(self):
        email = self.request.POST.get('email')
        self.request.session['email_inicio'] = email
        usuarios = Usuario.objects.filter(email=email)
        if usuarios:
            return reverse(settings.LOGIN_URL)
        else:
            return reverse('core:Criar Conta')


def exclusao_de_conta(request):
    temp_link = TempLink.objects.filter(tipo=2, tempo_final__gte=datetime.now()).first()
    if temp_link:
        messages.warning(request,
                         'Um e-mail com instruções já foi enviado para o endereço associado à sua conta. '
                         'Por favor, verifique sua caixa de entrada e siga as orientações para concluir, verifique'
                         ' também a pasta de spam.')
    else:
        TempLink.objects.filter(tipo=2).delete()
        user = request.user
        tempo_m = 30
        tempo_final = datetime.now() + timedelta(minutes=tempo_m)
        link = TempLink.objects.create(do_usuario=user, tempo_final=tempo_final, tipo=2)
        absolute_uri = request.build_absolute_uri(link.get_link_completo())
        enviar_email_exclusao_de_conta.delay(absolute_uri=absolute_uri, tempo_m=tempo_m, username=user.username,
                                             email=user.email)
        messages.success(request,
                         'Um e-mail com instruções foi enviado para o endereço associado à sua conta. '
                         'Por favor, verifique sua caixa de entrada e siga as orientações para concluir, verifique'
                         ' também a pasta de spam.')
    return redirect(request.META['HTTP_REFERER'])


class CriarConta(CreateView):
    template_name = 'criar_conta.html'
    form_class = FormCriarConta
    success_url = reverse_lazy(settings.LOGIN_URL)

    def get_form(self, form_class=None):
        form = super(CriarConta, self).get_form(form_class)
        form.fields['email'].required = True
        if self.request.session.get('email_inicio', None):
            form.initial = {'email': self.request.session.get('email_inicio')}
        return form

    def form_valid(self, form):
        self.object = form.save()
        self.object.is_active = False
        self.object.save(update_fields=['is_active', ])
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("core:Confirmar Email", kwargs={'user_pk': self.object.pk})


def confirmar_email(request, user_pk):
    if request.method == 'GET':
        form = FormToken()
        context = {'form': form, 'user_pk': user_pk}
        if user_pk is not None:
            user = Usuario.objects.filter(pk=user_pk).first()
            if user:
                link = TempLink.objects.filter(do_usuario=user, tempo_final__gte=datetime.now(), tipo=1)
                if not link and user.is_active is False:
                    tempo_h = 6
                    tempo_final = datetime.now() + timedelta(hours=tempo_h)
                    link_ = TempLink.objects.create(do_usuario=user, tempo_final=tempo_final, tipo=1)
                    codigo = TempCodigo.objects.create(do_usuario=user, tempo_final=tempo_final)
                    absolute_uri = request.build_absolute_uri(link_.get_link_completo())

                    enviar_email_conf_de_email.delay(absolute_uri=absolute_uri, tempo_h=tempo_h, codigo=codigo.codigo,
                                                     username=user.username, email=user.email)

                    return render(request, 'confirmacao_email.html', context)
                elif user.is_active is False:
                    return render(request, 'confirmacao_email.html', context)

    elif request.method == 'POST':
        form = FormToken(request.POST)
        if form.is_valid():
            token_code = form.cleaned_data['codigo_token']
            token = TempCodigo.objects.filter(codigo=token_code).first()
            if token:
                if token.tempo_final > datetime.now():
                    user = token.do_usuario
                    user.is_active = True
                    user.save(update_fields=['is_active', ])
                    messages.success(request, f"Email confirmado com sucesso!")
                    token.delete()
                    TempLink.objects.filter(do_usuario=user, tipo=1).delete()
                    TempCodigo.objects.filter(do_usuario=user).delete()
                    return redirect(reverse(settings.LOGIN_URL))
                else:
                    token.delete()
            messages.error(request, f"Token inexistente")
            return redirect(reverse('core:Confirmar Email', args=[user_pk]))
    return redirect(reverse('core:Home'))


def activate_account_link(request, link):
    link = TempLink.objects.filter(link_uuid=link, tempo_final__gte=datetime.now(), tipo=1).first()
    if link:
        user = link.do_usuario
        user.is_active = True
        user.save(update_fields=['is_active', ])
        messages.success(request, f"Email confirmado com sucesso!")
        link.delete()
        TempCodigo.objects.filter(do_usuario=user).delete()
        return redirect(reverse(settings.LOGIN_URL))
    else:
        messages.error(request, f"Link inexistente")
    return redirect(reverse('core:Home'))


class EditarPerfil(SuccessMessageMixin, LoginRequiredMixin, UpdateView):
    template_name = 'editar_perfil.html'
    model = Usuario
    form_class = FormUsuario

    def get_form(self, form_class=None):
        form = super(EditarPerfil, self).get_form(form_class)
        form.fields['first_name'].required = True
        form.fields['last_name'].required = True
        form.fields['cpf'].required = True
        if self.object.cript_cpf:
            cpf = cpf_format(_decrypt(self.object.cript_cpf))
            form.fields['cpf'].initial = cpf
        return form

    def form_valid(self, form):
        self.object = form.save()
        cpf = _crypt(message=form.cleaned_data['cpf'])
        self.object.cript_cpf = cpf
        return super().form_valid(form)

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_message(self, cleaned_data):
        success_message = 'Perfil editado com sucesso!'
        return success_message

    def get_success_url(self):
        return reverse("core:Visão Geral")


class ApagarConta(SuccessMessageMixin, LoginRequiredMixin, DeleteView):
    template_name = 'excluir_conta.html'
    model = Usuario
    success_message = 'Conta apagada'
    success_url = reverse_lazy('core:Home')

    def get_object(self, queryset=None):
        return self.request.user

    def render_to_response(self, context, **response_kwargs):
        link_uuid = self.kwargs['link']
        temp_link = get_object_or_404(TempLink, link_uuid=link_uuid, tempo_final__gte=datetime.now(), tipo=2)
        if self.request.user == temp_link.do_usuario:
            if temp_link.tempo_final > datetime.now():
                response_kwargs.setdefault("content_type", self.content_type)
                return self.response_class(
                    request=self.request,
                    template=self.get_template_names(),
                    context=context,
                    using=self.template_engine,
                    **response_kwargs,
                )
            else:
                raise Http404


@login_required
def painel_slots(request):
    context = {}
    if request.method == 'GET':
        context['form'] = FormTickets()
        context['form_slots'] = FormSlots()

    slots = Slot.objects.filter(do_usuario=request.user).order_by('pk')

    context['slots'] = slots
    context['tickets'] = request.user.tickets
    return render(request, 'painel_slots.html', context)


@login_required
def painel_configs(request):
    user = request.user
    tfa_verif = request.user.is_verified()
    context = {}

    device = request.user.staticdevice_set.get_or_create(name='backup')[0]
    tokens_qtd = len(device.token_set.all())
    context['tokens_qtd'] = tokens_qtd

    form_config = FormConfigNotific(initial={
        'notif_recibo': True if user.notif_recibo else False,
        'notif_contrato_criado': True if user.notif_contrato_criado else False,
        'notif_contrato_venc_1': True if user.notif_contrato_venc_1 else False,
        'notif_contrato_venc_2': True if user.notif_contrato_venc_2 else False,
        'notif_parc_venc_1': True if user.notif_parc_venc_1 else False,
        'notif_parc_venc_2': True if user.notif_parc_venc_2 else False})

    form_config_app = FormConfigApp(initial={
        'notif_qtd': user.notif_qtd,
        'notif_qtd_hist': user.notif_qtd_hist,
        'itens_pag_visao_geral': user.itens_pag_visao_geral,
        'itens_pag_ativos': user.itens_pag_ativos,
        'itens_pag_pagamentos': user.itens_pag_pagamentos,
        'itens_pag_gastos': user.itens_pag_gastos,
        'itens_pag_imoveis': user.itens_pag_imoveis,
        'itens_pag_locatarios': user.itens_pag_locatarios,
        'itens_pag_contratos': user.itens_pag_contratos,
        'itens_pag_notas': user.itens_pag_notas})

    context['form_config'] = form_config
    context['form_config_app'] = form_config_app
    context['tfa'] = tfa_verif

    return render(request, 'painel_configs.html', context)


@login_required
def configurar_notificacoes(request):
    if request.method == 'POST':
        form = FormConfigNotific(request.POST)
        if form.is_valid():
            user = request.user
            notif_recibo = form.cleaned_data['notif_recibo']
            notif_contrato_criado = form.cleaned_data['notif_contrato_criado']
            notif_contrato_venc_1 = form.cleaned_data['notif_contrato_venc_1']
            notif_contrato_venc_2 = form.cleaned_data['notif_contrato_venc_2']
            notif_parc_venc_1 = form.cleaned_data['notif_parc_venc_1']
            notif_parc_venc_2 = form.cleaned_data['notif_parc_venc_2']

            user.notif_recibo = datetime.now() if notif_recibo else None
            user.notif_contrato_criado = datetime.now() if notif_contrato_criado else None
            user.notif_contrato_venc_1 = datetime.now() if notif_contrato_venc_1 else None
            user.notif_contrato_venc_2 = datetime.now() if notif_contrato_venc_2 else None
            user.notif_parc_venc_1 = datetime.now() if notif_parc_venc_1 else None
            user.notif_parc_venc_2 = datetime.now() if notif_parc_venc_2 else None
            user.save(update_fields=['notif_recibo', 'notif_contrato_criado', 'notif_contrato_venc_1',
                                     'notif_contrato_venc_2', 'notif_parc_venc_1', 'notif_parc_venc_2', ])
            messages.success(request, f"As novas configurações foram salvas")
    return redirect(request.META['HTTP_REFERER'])


@login_required
def configurar_app(request):
    if request.method == 'POST':
        form = FormConfigApp(request.POST)
        if form.is_valid():
            user = request.user
            user.notif_qtd = form.cleaned_data['notif_qtd']
            user.notif_qtd_hist = form.cleaned_data['notif_qtd_hist']
            user.itens_pag_visao_geral = form.cleaned_data['itens_pag_visao_geral']
            user.itens_pag_ativos = form.cleaned_data['itens_pag_ativos']
            user.itens_pag_pagamentos = form.cleaned_data['itens_pag_pagamentos']
            user.itens_pag_gastos = form.cleaned_data['itens_pag_gastos']
            user.itens_pag_imoveis = form.cleaned_data['itens_pag_imoveis']
            user.itens_pag_locatarios = form.cleaned_data['itens_pag_locatarios']
            user.itens_pag_contratos = form.cleaned_data['itens_pag_contratos']
            user.itens_pag_notas = form.cleaned_data['itens_pag_notas']
            user.save(update_fields=['notif_qtd', 'notif_qtd_hist', 'itens_pag_visao_geral', 'itens_pag_ativos',
                                     'itens_pag_pagamentos', 'itens_pag_gastos', 'itens_pag_imoveis',
                                     'itens_pag_locatarios', 'itens_pag_contratos', 'itens_pag_notas', ])
            messages.success(request, f"As novas configurações foram salvas")
    return redirect(request.META['HTTP_REFERER'])


def baixar_planilha(request):
    # Criar o arquivo de planilha contendo todas as informações que o usuário colocou no site: Registros de Imóveis,
    # locatários, contratos, pagamentos, gastos e anotações e enviar para download.
    user = request.user
    imoveis_user = Imovei.objects.filter(do_locador=user).order_by('data_registro').values()
    locatarios_user = Locatario.objects.filter(do_locador=user).order_by('data_registro').values()
    contratos_user = Contrato.objects.filter(do_locador=user).order_by('data_registro').values()
    pagamentos_user = Pagamento.objects.filter(ao_locador=user).order_by('data_criacao').values()
    gastos_user = Gasto.objects.filter(do_locador=user).order_by('data_criacao').values()
    notas_user = Anotacoe.objects.filter(do_usuario=user).order_by('data_registro').values()

    def planilha_response():
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        date_format = workbook.add_format({'num_format': 'dd/mm/yyyy'})

        imoveis = workbook.add_worksheet()
        imoveis.name = 'imoveis'
        excluidos = ['do_locador_id', ]
        renomear = {'grupo_id': 'grupo'}
        for col, imovel in enumerate(imoveis_user):
            row = 0
            for titulo, item in imovel.items():
                if titulo not in excluidos:
                    if isinstance(item, datetime):
                        imoveis.write_datetime(col + 1, row, item, date_format)
                    else:
                        if titulo == 'grupo_id':
                            imovel_id = imovel['id']
                            imovel = Imovei.objects.get(pk=imovel_id)
                            imoveis.write(col + 1, row, str(imovel.grupo))
                        else:
                            imoveis.write(col + 1, row, item)
                    if col == 0:
                        if titulo in renomear.keys():
                            titulo = renomear[f'{titulo}']
                        imoveis.write(col, row, titulo)
                    row += 1

        locatarios = workbook.add_worksheet()
        locatarios.name = 'locatarios'
        excluidos = ['do_locador_id', 'da_notificacao_id', 'docs', 'temporario']
        renomear = {'RG': 'rg', 'cript_cpf': 'cpf'}
        for col, locatario in enumerate(locatarios_user):
            row = 0
            for titulo, item in locatario.items():
                if titulo not in excluidos:
                    if isinstance(item, datetime):
                        locatarios.write_datetime(col + 1, row, item, date_format)
                    else:
                        if titulo == 'cript_cpf':
                            locatario_id = locatario['id']
                            locat = Locatario.objects.get(pk=locatario_id)
                            locatarios.write(col + 1, row, locat.cpf())
                        elif titulo == 'estadocivil':
                            locatario_id = locatario['id']
                            locat = Locatario.objects.get(pk=locatario_id)
                            locatarios.write(col + 1, row, locat.get_estadocivil_display())
                        else:
                            locatarios.write(col + 1, row, item)
                    if col == 0:
                        if titulo in renomear.keys():
                            titulo = renomear[f'{titulo}']
                        locatarios.write(col, row, titulo)
                    row += 1

        contratos = workbook.add_worksheet()
        contratos.name = 'contratos'
        excluidos = ['do_locador_id', 'codigo', 'recibos_pdf', 'objects']
        renomear = {'duracao': 'duração', 'do_locatario_id': 'locatario_id', 'do_imovel_id': 'imovel_id'}
        for col, contrato in enumerate(contratos_user):
            row = 0
            for titulo, item in contrato.items():
                if titulo not in excluidos:
                    if isinstance(item, datetime):
                        contratos.write_datetime(col + 1, row, item, date_format)
                    else:
                        if titulo == 'valor_mensal':
                            contrato_id = contrato['id']
                            contr = Contrato.objects.get(pk=contrato_id)
                            contratos.write(col + 1, row, contr.valor_format())
                        else:
                            contratos.write(col + 1, row, item)
                    if col == 0:
                        if titulo in renomear.keys():
                            titulo = renomear[f'{titulo}']
                        contratos.write(col, row, titulo)
                    row += 1

        pagamentos = workbook.add_worksheet()
        pagamentos.name = 'pagamentos'
        excluidos = ['ao_locador_id', 'codigo', 'recibos_pdf']
        renomear = {'ao_contrato_id': 'contrato_id', 'do_locatario_id': 'locatario_id', 'data_criacao': 'data_registro'}
        for col, pagamento in enumerate(pagamentos_user):
            row = 0
            for titulo, item in pagamento.items():
                if titulo not in excluidos:
                    if isinstance(item, datetime):
                        pagamentos.write_datetime(col + 1, row, item, date_format)
                    else:
                        if titulo == 'valor_pago':
                            pagamento_id = pagamento['id']
                            pagam = Pagamento.objects.get(pk=pagamento_id)
                            pagamentos.write(col + 1, row, pagam.valor_format())
                        elif titulo == 'forma':
                            pagamento_id = pagamento['id']
                            pagam = Pagamento.objects.get(pk=pagamento_id)
                            pagamentos.write(col + 1, row, pagam.get_forma_display())
                        else:
                            pagamentos.write(col + 1, row, item)
                    if col == 0:
                        if titulo in renomear.keys():
                            titulo = renomear[f'{titulo}']
                        pagamentos.write(col, row, titulo)
                    row += 1

        gastos = workbook.add_worksheet()
        gastos.name = 'gastos'
        excluidos = ['do_locador_id', 'comprovante']
        renomear = {'observacoes': 'observações', 'do_imovel_id': 'imovel_id', 'data_criacao': 'data_registro'}
        for col, gasto in enumerate(gastos_user):
            row = 0
            for titulo, item in gasto.items():
                if titulo not in excluidos:
                    if isinstance(item, datetime):
                        gastos.write_datetime(col + 1, row, item, date_format)
                    else:
                        if titulo == 'valor':
                            gasto_id = gasto['id']
                            gasto = Gasto.objects.get(pk=gasto_id)
                            gastos.write(col + 1, row, gasto.valor_format())
                        else:
                            gastos.write(col + 1, row, item)
                    if col == 0:
                        if titulo in renomear.keys():
                            titulo = renomear[f'{titulo}']
                        gastos.write(col, row, titulo)
                    row += 1

        notas = workbook.add_worksheet()
        notas.name = 'notas'
        excluidos = ['do_usuario_id', 'da_notificacao_id', 'tarefa']
        renomear = {}
        for col, nota in enumerate(notas_user):
            row = 0
            for titulo, item in nota.items():
                if titulo not in excluidos:
                    if isinstance(item, datetime):
                        notas.write_datetime(col + 1, row, item, date_format)
                    else:
                        notas.write(col + 1, row, item)
                    if col == 0:
                        if titulo in renomear.keys():
                            titulo = renomear[f'{titulo}']
                        notas.write(col, row, titulo)
                    row += 1
        workbook.close()

        output.seek(0)
        filename = f"{user.username}_planilha.xlsx"
        response = HttpResponse(output,
                                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", )
        response["Content-Disposition"] = "attachment; filename=%s" % filename
        return response

    return planilha_response()


# 1. Primeiro criar a funcao restaurar, tentar restaurar como uma fixture, esta funcao deve restaurar o arquivo de
# fixture gerado pelo aplicativo 'planilha_to_json' do prédio, perfeitamente e através da view; depois eu aplico a
# criptografia. (vou precisar juntar os três arquivos em um zip)
# 2. Depois que a funcao acima estiver apta, criar a funcao backup, criando os arquivos json como se cria em
# 'planilha_to_json'. (vou precisar juntar os três arquivos em um zip)
# Por último criar o sistema de criptografia/descriptografia e verificador de usuário.


@login_required
@transaction.atomic
def add_slot(request):
    usuario = request.user
    if usuario.tickets <= 0:
        messages.error(request, "Tickets insuficientes para esta operação")
    else:
        if request.method == 'POST':
            form = FormSlots(request.POST)
            if form.is_valid():
                quantidade = int(form.cleaned_data['slots_qtd'])
                if usuario.tickets >= quantidade:
                    for x in range(0, quantidade):
                        Slot.objects.create(do_usuario=request.user, gratuito=False, tickets=1)
                        usuario.tickets -= 1
                    usuario.save(update_fields=['tickets'])
                    messages.success(request, f"Slot adicionado com sucesso")
                else:
                    messages.error(request, "Tickets insuficientes para esta operação")
    return redirect(request.META['HTTP_REFERER'])


@login_required
@transaction.atomic
def adicionar_ticket(request, pk):
    slot = get_object_or_404(Slot, pk=pk, do_usuario=request.user)
    quantidade = 1
    if request.method == 'POST':
        form = FormTickets(request.POST)
        if form.is_valid():
            quantidade = form.cleaned_data['tickets_qtd']
    if slot.do_usuario == request.user and slot.gratuito is False:
        if quantidade <= request.user.tickets:
            usuario = request.user
            usuario.tickets -= quantidade
            if slot.tickets_restando() == 0:
                slot.criado_em = datetime.now()
                slot.tickets = quantidade
            else:
                slot.tickets += quantidade
            usuario.save(update_fields=['tickets'])
            slot.save(update_fields=['tickets', 'criado_em'])
            messages.success(request, f"Ticket adicionado com sucesso no slot {slot.posicao()}")
        else:
            messages.error(request, "Tickets insuficientes para esta operação")
    else:
        messages.error(request, "Ticket não foi adicionado!")
    return redirect(request.META['HTTP_REFERER'])


@login_required
@transaction.atomic
def adicionar_ticket_todos(request):
    slots = Slot.objects.filter(do_usuario=request.user, gratuito=False)
    quantidade = 1
    if request.method == 'POST':
        form = FormTickets(request.POST)
        if form.is_valid():
            quantidade = form.cleaned_data['tickets_qtd']

    if len(slots) * quantidade <= request.user.tickets:
        for slot in slots:
            slot.tickets += quantidade
            usuario = request.user
            usuario.tickets -= quantidade
            usuario.save(update_fields=['tickets'])
            slot.save(update_fields=['tickets'])
        messages.success(request, f"Tickets adicionados com sucesso,"
                                  f" {len(slots) * quantidade} tickets para {len(slots)} slots")
    else:
        messages.error(request, "Tickets insuficientes para esta operação")
    return redirect(request.META['HTTP_REFERER'])


@login_required
def apagar_slot(request, pk):
    slot = get_object_or_404(Slot, pk=pk, do_usuario=request.user)
    if slot.do_usuario == request.user and slot.imovel() is None and slot.gratuito is False:
        slot.delete()
        messages.success(request, f"Slot apagado com sucesso")
    else:
        messages.error(request, "Slot não foi apagado!")
    return redirect(request.META['HTTP_REFERER'])


# -=-=-=-=-=-=-=-= SERVIDORES DE ARQUIVOS -=-=-=-=-=-=-=-=


@login_required
def arquivos_contratos_modelos(request, file):
    link = str(f'contratos_modelos/{file}')
    modelo = get_object_or_404(ContratoModelo, visualizar=link)
    if modelo.autor == request.user or modelo.comunidade or request.user.is_superuser:
        local = fr'{settings.MEDIA_ROOT}/{modelo.visualizar}'
        if os.path.isfile(local):
            return FileResponse(modelo.visualizar)
        else:
            raise Http404
    else:
        raise Http404


@login_required
def arquivos_sugestoes_docs(request, year, month, file):
    link = str(f'sugestoes_docs/{year}/{month}/{file}')
    sugestao = get_object_or_404(Sugestao, imagem=link)
    if sugestao.aprovada or request.user.is_superuser:
        local = fr'{settings.MEDIA_ROOT}/{sugestao.imagem}'
        if os.path.exists(local):
            return FileResponse(sugestao.imagem)
        else:
            raise Http404
    else:
        raise Http404


@login_required
def arquivos_locatarios_docs(request, year, month, file):
    link = str(f'locatarios_docs/{year}/{month}/{file}')
    locatario = get_object_or_404(Locatario, docs=link)
    if locatario.do_locador == request.user or request.user.is_superuser:
        local = fr'{settings.MEDIA_ROOT}/{locatario.docs}'
        if os.path.exists(local):
            return FileResponse(locatario.docs)
        else:
            raise Http404
    else:
        raise Http404


@login_required
def arquivos_recibos_docs(request, year, month, file):
    link = str(f'recibos_docs/{year}/{month}/{file}')
    contrato = get_object_or_404(Contrato, recibos_pdf=link)
    if contrato.do_locador == request.user or request.user.is_superuser:
        local = fr'{settings.MEDIA_ROOT}/{contrato.recibos_pdf}'
        if os.path.exists(local):
            return FileResponse(contrato.recibos_pdf)
        else:
            raise Http404
    else:
        raise Http404


@login_required
def arquivos_tabela_docs(request, file):
    link = str(f'/tabela_docs/{file}')
    if request.session.session_key in file:
        local = fr'{settings.MEDIA_ROOT}/{link}'
        if os.path.exists(local):
            return FileResponse(open(f'{settings.MEDIA_ROOT + link}', 'rb'), content_type='application/pdf')
        else:
            raise Http404
    else:
        raise Http404


@login_required
def arquivos_contrato_docs(request, file):
    link = str(f'/contrato_docs/{file}')
    if request.user.contrato_code() in file:
        local = fr'{settings.MEDIA_ROOT}/{link}'
        if os.path.exists(local):
            return FileResponse(open(f'{settings.MEDIA_ROOT + link}', 'rb'), content_type='application/pdf')
        else:
            raise Http404
    else:
        raise Http404


@login_required
def arquivos_gastos_docs(request, year, month, file):
    link = str(f'gastos_comprovantes/{year}/{month}/{file}')
    gasto = get_object_or_404(Gasto, comprovante=link)
    if gasto.do_locador == request.user or request.user.is_superuser:
        local = fr'{settings.MEDIA_ROOT}/{gasto.comprovante}'
        if os.path.exists(local):
            return FileResponse(gasto.comprovante)
        else:
            raise Http404
    else:
        raise Http404


@login_required
@user_passes_test(lambda u: u.is_superuser)
def arquivos_mensagens_ao_dev(request, year, month, file):
    link = str(f'mensagens_ao_dev/{year}/{month}/{file}')
    dev_mensagem = get_object_or_404(DevMensagen, imagem=link)
    if dev_mensagem.do_usuario == request.user:
        local = fr'{settings.MEDIA_ROOT}/{dev_mensagem.imagem}'
        if os.path.exists(local):
            return FileResponse(dev_mensagem.imagem)
        else:
            raise Http404
    else:
        raise Http404


# -=-=-=-=-=-=-=-= OUTROS -=-=-=-=-=-=-=-=

@login_required
def mensagem_desenvolvedor(request):
    form = FormMensagem(request.POST, request.FILES)
    if form.is_valid():
        mensagem = form.save(commit=False)
        mensagem.do_usuario = request.user
        mensagem.save()
        messages.success(request, "Mensagem enviada com sucesso!")
        return redirect(request.META['HTTP_REFERER'])
    else:
        request.session['form2'] = request.POST
        messages.error(request, "Formulário inválido.")
        return redirect(request.META['HTTP_REFERER'])


@login_required
def conversa_com_o_dev(request, pk):
    mensagem = get_object_or_404(DevMensagen, do_usuario=request.user, pk=pk)
    if mensagem.resposta == '':
        raise Http404
    notific = get_object_or_404(Notificacao, pk=mensagem.da_notificacao.pk, do_usuario=request.user)
    notific.definir_lida()
    context = {'mensagem': mensagem}
    return render(request, 'dev_chat.html', context)


@login_required
def forum_sugestoes(request):
    if request.user.is_superuser:
        sugestoes = Sugestao.objects.filter(implementada=False).order_by('-data_registro')
        sugestoes_implementadas = Sugestao.objects.filter(implementada=True).order_by('-data_implementada')
    else:
        sugestoes_geral = Sugestao.objects.filter(implementada=False, aprovada=True)
        sugestoes_implementadas_geral = Sugestao.objects.filter(implementada=True, aprovada=True)

        sugestoes_usuario = Sugestao.objects.filter(implementada=False, aprovada=False, do_usuario=request.user.pk)
        sugestoes_implementadas_usuario = Sugestao.objects.filter(implementada=True, aprovada=False,
                                                                  do_usuario=request.user.pk)

        sugestoes = sugestoes_geral.union(sugestoes_usuario).order_by('-data_registro')[:20]
        sugestoes_implementadas = sugestoes_implementadas_geral.union(sugestoes_implementadas_usuario).order_by(
            '-data_implementada')[:40]

    usuario = request.user
    sugestoes_curtidas = Sugestao.objects.filter(likes=usuario)
    form = FormSugestao()
    context = {}
    if request.method == 'POST':
        form = FormSugestao(request.POST, request.FILES)
        if form.is_valid():
            sugestao = form.save(commit=False)
            sugestao.do_usuario = usuario
            sugestao.save()
            messages.success(request, f"Sugestão criada com sucesso!")
            return redirect(reverse('core:Sugestões'))

    context['sugestoes'] = sugestoes
    context['sugestoes_curtidas'] = sugestoes_curtidas
    context['sugestoes_implementadas'] = sugestoes_implementadas
    context['usuario'] = usuario
    context['form'] = form
    return render(request, 'forum_sugestoes.html', context)


@login_required
def like_de_sugestoes(request, pk):
    sugestao = get_object_or_404(Sugestao, pk=pk)
    if sugestao.implementada is False and sugestao.aprovada is True:
        if sugestao.likes.filter(id=request.user.pk).exists():
            sugestao.likes.remove(request.user)
        else:
            sugestao.likes.add(request.user)
    return HttpResponseRedirect(reverse('core:Sugestões'))


@login_required
def apagar_sugestao(request, pk):
    sugestao = get_object_or_404(Sugestao, pk=pk)
    if request.user.is_superuser or request.user == sugestao.do_usuario:
        sugestao.delete()
    return HttpResponseRedirect(reverse('core:Sugestões'))


@login_required
@user_passes_test(lambda u: u.is_superuser)
def implementar_sugestao(request, pk):
    sugestao = get_object_or_404(Sugestao, pk=pk)
    if sugestao.implementada is False:
        sugestao.implementada = True
        sugestao.data_implementada = datetime.now()
    else:
        sugestao.implementada = False
        sugestao.data_implementada = None
    sugestao.save(update_fields=['implementada', 'data_implementada'])
    return HttpResponseRedirect(reverse('core:Sugestões'))


@login_required
@user_passes_test(lambda u: u.is_superuser)
def aprovar_sugestao(request, pk):
    sugestao = get_object_or_404(Sugestao, pk=pk)
    if sugestao.aprovada is False:
        sugestao.aprovada = True
    else:
        sugestao.aprovada = False
    sugestao.save(update_fields=['aprovada'])
    return HttpResponseRedirect(reverse('core:Sugestões'))


def criar_locatarios_ficticios(request, quantidade, multiplicador, usuario_s, distribuir):
    if distribuir:
        range_ = floor((multiplicador * quantidade) / len(usuario_s))
    else:
        range_ = multiplicador * quantidade
    if range_ < 1 and distribuir:
        messages.error(request, f"Quantia insuficiente para distribuir 'locatários' entre todos os usuários")
    else:
        for usuario in usuario_s:
            count = 0
            for x in range(range_):
                count += 1
                aleatorio = locatarios_ficticios()
                form = FormLocatario(usuario=request.user.pk)
                locatario = form.save(commit=False)
                locatario.do_locador = usuario
                locatario.nome = aleatorio.get('nome')
                locatario.RG = aleatorio.get('RG')
                cpf = _crypt(str(aleatorio.get('CPF')))
                locatario.cript_cpf = cpf
                locatario.ocupacao = aleatorio.get('ocupacao')
                locatario.endereco_completo = aleatorio.get('endereco_completo')
                locatario.telefone1 = aleatorio.get('telefone1')
                locatario.telefone2 = aleatorio.get('telefone2')
                locatario.email = aleatorio.get('email')
                locatario.nacionalidade = aleatorio.get('nacionalidade')
                locatario.estadocivil = aleatorio.get('estadocivil')
                locatario.save()
            messages.success(request, f"Criado(s) {count} locatário(s) para {usuario}")


def criar_imov_grupo_fict(request, quantidade, multiplicador, usuario_s, distribuir):
    if distribuir:
        range_ = floor((multiplicador * quantidade) / len(usuario_s))
    else:
        range_ = multiplicador * quantidade
    if range_ < 1 and distribuir:
        messages.error(request,
                       f"Quantia insuficiente para distribuir 'grupos de imóveis' entre todos os usuários")
    else:
        for usuario in usuario_s:
            count = 0
            for x in range(range_):
                count += 1
                aleatorio = imov_grupo_fict()
                form = FormimovelGrupo()
                imovel_g = form.save(commit=False)
                imovel_g.do_usuario = usuario
                imovel_g.nome = aleatorio.get('nome')
                imovel_g.tipo = aleatorio.get('tipo')
                imovel_g.save()
            messages.success(request, f"Criado(s) {count} grupo(s) para {usuario}")


def criar_imoveis_ficticios(request, quantidade, multiplicador, usuario_s, distribuir):
    if distribuir:
        range_ = floor((multiplicador * quantidade) / len(usuario_s))
    else:
        range_ = multiplicador * quantidade
    if range_ < 1 and distribuir:
        messages.error(request, f"Quantia insuficiente para distribuir 'imóveis' entre todos os usuários")
    else:
        for usuario in usuario_s:
            count = 0
            for x in range(range_):
                count += 1
                aleatorio = imoveis_ficticios(usuario)
                form = FormImovel(usuario)
                imovel = form.save(commit=False)
                imovel.do_locador = usuario
                imovel.nome = aleatorio.get('nome')
                imovel.grupo = aleatorio.get('grupo')
                imovel.cep = aleatorio.get('cep')
                imovel.endereco = aleatorio.get('endereco')
                imovel.numero = aleatorio.get('numero')
                imovel.complemento = aleatorio.get('complemento')
                imovel.bairro = aleatorio.get('bairro')
                imovel.cidade = aleatorio.get('cidade')
                imovel.estado = aleatorio.get('estado')
                imovel.uc_energia = aleatorio.get('uc_energia')
                imovel.uc_agua = aleatorio.get('uc_agua')
                imovel.data_registro = aleatorio.get('data_registro')
                imovel.save()
                if Imovei.objects.filter(do_locador=usuario).count() > 3:
                    Slot.objects.create(do_usuario=usuario, gratuito=False, tickets=1)
            messages.success(request, f"Criado(s) {count} imovei(s) para {usuario}")


def criar_contratos_ficticios(request, quantidade, multiplicador, usuario_s, distribuir):
    if distribuir:
        range_ = floor((multiplicador * quantidade) / len(usuario_s))
    else:
        range_ = multiplicador * quantidade
    if range_ < 1 and distribuir:
        messages.error(request, f"Quantia insuficiente para distribuir 'contratos' entre todos os usuários")
    else:
        for usuario in usuario_s:
            locatarios = Locatario.objects.filter(do_locador=usuario).count()
            imoveis = Imovei.objects.filter(do_locador=usuario).count()

            if imoveis == 0:
                messages.error(request,
                               f"Nenhum Imóvel disponível para criar contrato(s) para o usuário: {usuario}")
            elif locatarios == 0:
                messages.error(request,
                               f"Nenhum Locatário disponível para criar contratos para o usuário: {usuario}")
            else:
                count = 0
                for x in range(range_):
                    count += 1
                    aleatorio = contratos_ficticios(request, usuario)
                    form = FormContrato(usuario)
                    contrato = form.save(commit=False)
                    contrato.do_locador = usuario
                    contrato.em_posse = aleatorio.get('em_posse')
                    contrato.do_locatario = aleatorio.get('do_locatario')
                    contrato.do_imovel = aleatorio.get('do_imovel')
                    contrato.data_entrada = aleatorio.get('data_entrada')
                    contrato.duracao = aleatorio.get('duracao')
                    contrato.valor_mensal = aleatorio.get('valor_mensal')
                    contrato.dia_vencimento = aleatorio.get('dia_vencimento')
                    contrato.save()
                messages.success(request, f"Criado(s) {count} contrato(s) para {usuario}")


def criar_pagamentos_ficticios(request, quantidade, multiplicador, usuario_s, distribuir):
    if distribuir:
        range_ = floor((multiplicador * quantidade) / len(usuario_s))
    else:
        range_ = multiplicador * quantidade
    if range_ < 1 and distribuir:
        messages.error(request, f"Quantia insuficiente para distribuir 'pagamentos' entre todos os usuários")
    else:
        for usuario in usuario_s:
            contratos = Contrato.objects.filter(do_locador=usuario)
            tem_contrato_nao_quitado = False
            for contrato in contratos:
                if contrato.quitado() is False:
                    tem_contrato_nao_quitado = True
                    break

            if contratos.count() == 0:
                messages.error(request,
                               f"Nenhum contrato disponível para criar pagamentos(s) para o usuário: {usuario}")
            elif tem_contrato_nao_quitado is False:
                messages.error(request,
                               f"Nenhum contrato disponível para criar pagamentos(s) para o usuário: {usuario},"
                               f" todos estão quitados")
            else:
                count = 0
                for x in range(range_):
                    count += 1
                    aleatorio = pagamentos_ficticios(usuario=usuario)
                    form = FormPagamento(usuario)
                    pagamento = form.save(commit=False)
                    locatario = Contrato.objects.get(pk=aleatorio.get('ao_contrato').pk).do_locatario
                    pagamento.ao_locador = usuario
                    pagamento.do_locatario = locatario
                    pagamento.ao_contrato = aleatorio.get('ao_contrato')
                    pagamento.valor_pago = aleatorio.get('valor_pago')
                    pagamento.data_pagamento = aleatorio.get('data_pagamento')
                    pagamento.forma = aleatorio.get('forma')
                    pagamento.save()

                # Marcar recibo_entregue de algumas parcelas, porém em ordem sequencial desde o primeiro. Marcar todos
                # como entregues ou deixar alguns.
                contratos_user = Contrato.objects.filter(do_locador=usuario)
                for contrato in contratos_user:
                    parcelas = Parcela.objects.filter(do_contrato=contrato).order_by('pk')
                    # for para saber a quantidade de parcelas deste contrato que estão pagas
                    parc_pagas_qtd = 0
                    for parcela in parcelas:
                        if parcela.esta_pago():
                            parc_pagas_qtd += 1
                    # Decidir a quantidade de recibos a distribuir para a lista de parcelas do contrato
                    # chance para decidir 'recibar' tudo, ou um certo range \/
                    if parc_pagas_qtd > 0:
                        chance = 70
                        recibos_qtd = parc_pagas_qtd if porcentagem_de_chance(chance) else randrange(0, parc_pagas_qtd)
                        # For para alterar as parcelas com recibo entregue
                        for n, parcela in enumerate(parcelas):
                            if parcela.recibo_entregue is False and n < recibos_qtd:
                                parcela.recibo_entregue = True
                                if parcela.get_notific_pgm():
                                    parcela.get_notific_pgm().definir_lida()
                                parcela.save(update_fields=['recibo_entregue', ])
                            else:
                                break
                messages.success(request, f"Criado(s) {count} pagamento(s) para {usuario}")


def criar_gastos_ficticios(request, quantidade, multiplicador, usuario_s, distribuir):
    if distribuir:
        range_ = floor((multiplicador * quantidade) / len(usuario_s))
    else:
        range_ = multiplicador * quantidade
    if range_ < 1 and distribuir:
        messages.error(request, f"Quantia insuficiente para distribuir 'gastos' entre todos os usuários")
    else:
        for usuario in usuario_s:
            count = 0
            for x in range(range_):
                count += 1
                aleatorio = gastos_ficticios()
                form = FormGasto()
                gasto = form.save(commit=False)
                gasto.do_locador = usuario
                gasto.do_imovel = aleatorio.get('do_imovel')
                gasto.valor = aleatorio.get('valor')
                gasto.data = aleatorio.get('data')
                gasto.observacoes = aleatorio.get('observacoes')
                gasto.save()
            messages.success(request, f"Criado(s) {count} gasto(s) para {usuario}")


def criar_anotacoes_ficticias(request, quantidade, multiplicador, usuario_s, distribuir):
    if distribuir:
        range_ = floor((multiplicador * quantidade) / len(usuario_s))
    else:
        range_ = multiplicador * quantidade
    if range_ < 1 and distribuir:
        messages.error(request, f"Quantia insuficiente para distribuir 'anotações' entre todos os usuários")
    else:
        for usuario in usuario_s:
            count = 0
            for x in range(range_):
                count += 1
                aleatorio = anotacoes_ficticias()
                form = FormAnotacoes()
                nota = form.save(commit=False)
                nota.do_usuario = usuario
                nota.titulo = aleatorio.get('titulo')
                nota.data_registro = aleatorio.get('data_registro')
                nota.texto = aleatorio.get('texto')
                nota.tarefa = aleatorio.get('tarefa')
                nota.feito = aleatorio.get('feito')
                nota.save()
            messages.success(request, f"Criada(s) {count} anotação(ões) para {usuario}")


def criar_sugestoes_ficticias(request, quantidade, multiplicador, usuario_s, distribuir):
    if distribuir:
        range_ = floor((multiplicador * quantidade) / len(usuario_s))
    else:
        range_ = multiplicador * quantidade
    if range_ < 1 and distribuir:
        messages.error(request, f"Quantia insuficiente para distribuir 'sugestões' entre todos os usuários")
    else:
        for usuario in usuario_s:
            count = 0
            for x in range(range_):
                count += 1
                aleatorio = sugestoes_ficticias()
                form = FormSugestao()
                sugestao = form.save(commit=False)
                sugestao.do_usuario = usuario
                sugestao.corpo = aleatorio.get('corpo')
                sugestao.aprovada = aleatorio.get('aprovada')
                sugestao.implementada = aleatorio.get('implementada')
                sugestao.data_implementada = aleatorio.get('data_implementada')
                sugestao.save()
                for usuario_ in aleatorio.get('likes'):
                    sugestao.likes.add(usuario_)
            messages.success(request, f"Criada(s) {count} sugestão(ões) para {usuario}")


def criar_modelos_contratos_ficticios(request, quantidade, multiplicador, usuario_s, distribuir):
    if distribuir:
        range_ = floor((multiplicador * quantidade) / len(usuario_s))
    else:
        range_ = multiplicador * quantidade
    if range_ < 1 and distribuir:
        messages.error(request, f"Quantia insuficiente para distribuir 'Modelos de Contratos' entre todos os usuários")
    else:
        for usuario in usuario_s:
            count = 0
            for x in range(range_):
                count += 1
                aleatorio = modelos_contratos_ficticios(usuario)
                form = FormContratoModelo(request=request)
                c_model = form.save(commit=False)
                c_model.autor = usuario
                c_model.titulo = aleatorio.get('titulo')
                c_model.corpo = aleatorio.get('corpo')
                c_model.descricao = aleatorio.get('descricao')
                c_model.comunidade = aleatorio.get('comunidade')
                c_model.save()

                if aleatorio.get('usuarios'):
                    for usuario_ in aleatorio.get('usuarios'):
                        c_model.usuarios.add(usuario_)
            messages.success(request, f"Criado(s) {count} modelo(s) de contrato(s) para {usuario}")


def criar_usuarios_ficticios(request, quantidade, multiplicador):
    count = 0
    for x in range(multiplicador * quantidade):
        UserModel = get_user_model()
        while True:
            aleatorio = usuarios_ficticios()
            if not UserModel.objects.filter(username=aleatorio.get('username')).exists():
                count += 1
                user = UserModel.objects.create_user(aleatorio.get('username'), password=aleatorio.get('password'))
                user.is_superuser = False
                user.is_staff = False
                user.first_name = aleatorio.get('first_name')
                user.last_name = aleatorio.get('last_name')
                user.email = aleatorio.get('email')
                user.telefone = aleatorio.get('telefone')
                user.nacionalidade = aleatorio.get('nacionalidade')
                user.estadocivil = aleatorio.get('estadocivil')
                user.ocupacao = aleatorio.get('ocupacao')
                user.endereco_completo = aleatorio.get('endereco_completo')
                user.dados_pagamento1 = aleatorio.get('dados_pagamento1')
                user.dados_pagamento2 = aleatorio.get('dados_pagamento2')
                user.RG = aleatorio.get('RG')
                cpf = _crypt(str(aleatorio.get('CPF')))
                user.cript_cpf = cpf
                user.save()
                break
    messages.success(request, f"Criado(s) {count} usuário(s)")


@login_required
def gerador_de_ficticios(request):
    if request.user.is_superuser or settings.DEBUG:
        form_adm = FormAdmin(request.POST)

        if form_adm.is_valid():
            qtd_usuario = form_adm.cleaned_data['qtd_usuario']
            qtd_locatario = form_adm.cleaned_data['qtd_locatario']
            qtd_imovel_g = form_adm.cleaned_data['qtd_imovel_g']
            qtd_imovel = form_adm.cleaned_data['qtd_imovel']
            qtd_contrato = form_adm.cleaned_data['qtd_contrato']
            qtd_pagamento = form_adm.cleaned_data['qtd_pagamento']
            qtd_gasto = form_adm.cleaned_data['qtd_gasto']
            qtd_nota = form_adm.cleaned_data['qtd_nota']
            qtd_sugestao = form_adm.cleaned_data['qtd_sugestao']
            qtd_contr_modelo = form_adm.cleaned_data['qtd_contr_modelo']

            fict_multi = int(form_adm.data['multiplicar_por'])
            fict_user_multi = int(form_adm.data['multiplicar_user_por'])

            if qtd_usuario > 0 and form_adm.cleaned_data['criar_usuarios']:
                criar_usuarios_ficticios(request, quantidade=qtd_usuario, multiplicador=fict_user_multi)

            distribuir = False
            usuario_s = Usuario.objects.none()
            if form_adm.cleaned_data['criar_itens']:
                todos_ou_cada = int(form_adm.data['todos_ou_cada'])
                if todos_ou_cada == 0:
                    usuario_s = Usuario.objects.all()
                elif todos_ou_cada == 1:
                    usuario_s = Usuario.objects.all().exclude(is_superuser=True)
                elif todos_ou_cada == 2:
                    usuario_s = Usuario.objects.all()
                    distribuir = True
                elif todos_ou_cada == 3:
                    usuario_s = Usuario.objects.all().exclude(is_superuser=True)
                    distribuir = True
                elif todos_ou_cada == 4:
                    usuario = form_adm.cleaned_data['para_o_usuario']
                    usuario_s = Usuario.objects.filter(pk=usuario.pk)

                if qtd_locatario * fict_multi > 0 and len(usuario_s) > 0:
                    criar_locatarios_ficticios(request, quantidade=qtd_locatario, multiplicador=fict_multi,
                                               usuario_s=usuario_s, distribuir=distribuir)
                if qtd_imovel_g * fict_multi > 0 and len(usuario_s) > 0:
                    criar_imov_grupo_fict(request, quantidade=qtd_imovel_g, multiplicador=fict_multi,
                                          usuario_s=usuario_s, distribuir=distribuir)
                if qtd_imovel * fict_multi > 0 and len(usuario_s) > 0:
                    criar_imoveis_ficticios(request, quantidade=qtd_imovel, multiplicador=fict_multi,
                                            usuario_s=usuario_s, distribuir=distribuir)
                if qtd_contrato * fict_multi > 0 and len(usuario_s) > 0:
                    criar_contratos_ficticios(request, quantidade=qtd_contrato, multiplicador=fict_multi,
                                              usuario_s=usuario_s, distribuir=distribuir)
                if qtd_pagamento * fict_multi > 0 and len(usuario_s) > 0:
                    criar_pagamentos_ficticios(request, quantidade=qtd_pagamento, multiplicador=fict_multi,
                                               usuario_s=usuario_s, distribuir=distribuir)
                if qtd_gasto * fict_multi > 0 and len(usuario_s) > 0:
                    criar_gastos_ficticios(request, quantidade=qtd_gasto, multiplicador=fict_multi,
                                           usuario_s=usuario_s, distribuir=distribuir)
                if qtd_nota * fict_multi > 0 and len(usuario_s) > 0:
                    criar_anotacoes_ficticias(request, quantidade=qtd_nota, multiplicador=fict_multi,
                                              usuario_s=usuario_s, distribuir=distribuir)
                if qtd_sugestao * fict_multi > 0 and len(usuario_s) > 0:
                    criar_sugestoes_ficticias(request, quantidade=qtd_sugestao, multiplicador=fict_multi,
                                              usuario_s=usuario_s, distribuir=distribuir)
                if qtd_contr_modelo * fict_multi > 0 and len(usuario_s) > 0:
                    criar_modelos_contratos_ficticios(request, quantidade=qtd_contr_modelo, multiplicador=fict_multi,
                                                      usuario_s=usuario_s, distribuir=distribuir)

        return redirect(request.META['HTTP_REFERER'])


def botao_teste(request):
    # test_func.delay(5)
    # test_func2.delay(10)
    messages.success(request, 'Fim!')
    return HttpResponse('Done')
