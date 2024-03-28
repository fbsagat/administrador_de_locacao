import datetime
from datetime import timedelta

from Alugue_seu_imovel import settings

from django.urls import resolve

from core.models import Notificacao
from core.forms import FormMensagem, FormAdmin
from core.forms import FormPagamento, FormGasto, FormLocatario, FormContrato, FormImovel, FormAnotacoes
from core.models import Contrato, Imovei


def titulo_pagina(request):
    titulo = resolve(request.path_info).url_name
    ano_atual = datetime.date.today().year
    return {'block_titulo': titulo, 'ano_atual': ano_atual, 'debug_true': True if settings.DEBUG else False,
            'SITE_NAME': settings.SITE_NAME}


def navbar_forms(request):
    if request.user.is_authenticated:

        # Apenas contratos ativos hoje ou futuramente e não quitados para os forms
        contratos_exibir = Contrato.objects.ativos_margem().filter(do_locador=request.user).order_by('-data_entrada')
        for contrato in contratos_exibir:
            if contrato.quitado():
                contratos_exibir = contratos_exibir.exclude(pk=contrato.pk)

        # Apenas os imóveis do locador
        imovies_locador = Imovei.objects.filter(do_locador=request.user).order_by('-data_registro')

        if request.session.get('form1'):
            tempo_form = datetime.datetime.strptime(request.session.get('form1')[1], '%H:%M:%S')
            tempo_agora = datetime.datetime.strptime(datetime.datetime.now().time().strftime('%H:%M:%S'), '%H:%M:%S')

            if tempo_form + timedelta(seconds=settings.TEMPO_SESSION_FORM) > tempo_agora:
                form1 = FormPagamento(request.user, request.session.get('form1')[0])
                form1.fields['ao_contrato'].queryset = contratos_exibir
            else:
                form1 = FormPagamento(request.user,
                                      initial={'data_pagamento': datetime.date.today().strftime('%Y-%m-%d')})
                form1.fields['ao_contrato'].queryset = contratos_exibir
                request.session.pop('form1')
        else:
            form1 = FormPagamento(request.user, initial={'data_pagamento': datetime.date.today().strftime('%Y-%m-%d')})
            form1.fields['ao_contrato'].queryset = contratos_exibir

        if request.session.get('form2'):
            tempo_form = datetime.datetime.strptime(request.session.get('form2')[1], '%H:%M:%S')
            tempo_agora = datetime.datetime.strptime(datetime.datetime.now().time().strftime('%H:%M:%S'), '%H:%M:%S')

            if tempo_form + timedelta(seconds=settings.TEMPO_SESSION_FORM) > tempo_agora:
                form2 = FormMensagem(request.session.get('form2')[0])
            else:
                form2 = FormMensagem()
                request.session.pop('form2')
        else:
            form2 = FormMensagem()

        if request.session.get('form3'):
            tempo_form = datetime.datetime.strptime(request.session.get('form3')[1], '%H:%M:%S')
            tempo_agora = datetime.datetime.strptime(datetime.datetime.now().time().strftime('%H:%M:%S'), '%H:%M:%S')

            if tempo_form + timedelta(seconds=settings.TEMPO_SESSION_FORM) > tempo_agora:
                form3 = FormGasto(request.session.get('form3')[0])
                form3.fields['do_imovel'].queryset = imovies_locador
            else:
                form3 = FormGasto(initial={'data': datetime.date.today().strftime('%Y-%m-%d')})
                form3.fields['do_imovel'].queryset = imovies_locador
                request.session.pop('form3')
        else:
            form3 = FormGasto(initial={'data': datetime.date.today().strftime('%Y-%m-%d')})
            form3.fields['do_imovel'].queryset = imovies_locador

        if request.session.get('form4'):
            tempo_form = datetime.datetime.strptime(request.session.get('form4')[1], '%H:%M:%S')
            tempo_agora = datetime.datetime.strptime(datetime.datetime.now().time().strftime('%H:%M:%S'), '%H:%M:%S')

            if tempo_form + timedelta(seconds=settings.TEMPO_SESSION_FORM) > tempo_agora:
                form4 = FormLocatario(request.session.get('form4')[0], usuario=request.user.pk)
            else:
                form4 = FormLocatario(usuario=request.user.pk)
                request.session.pop('form4')
        else:
            form4 = FormLocatario(usuario=request.user.pk)

        if request.session.get('form5'):
            tempo_form = datetime.datetime.strptime(request.session.get('form5')[1], '%H:%M:%S')
            tempo_agora = datetime.datetime.strptime(datetime.datetime.now().time().strftime('%H:%M:%S'), '%H:%M:%S')

            if tempo_form + timedelta(seconds=settings.TEMPO_SESSION_FORM) > tempo_agora:
                form5 = FormContrato(request.user, request.session.get('form5')[0])
            else:
                form5 = FormContrato(request.user, initial={'data_entrada': datetime.date.today().strftime('%Y-%m-%d')})
                request.session.pop('form5')
        else:
            form5 = FormContrato(request.user, initial={'data_entrada': datetime.date.today().strftime('%Y-%m-%d')})

        if request.session.get('form6'):
            tempo_form = datetime.datetime.strptime(request.session.get('form6')[1], '%H:%M:%S')
            tempo_agora = datetime.datetime.strptime(datetime.datetime.now().time().strftime('%H:%M:%S'), '%H:%M:%S')

            if tempo_form + timedelta(seconds=settings.TEMPO_SESSION_FORM) > tempo_agora:
                form6 = FormImovel(request.user, request.session.get('form6')[0])
            else:
                form6 = FormImovel(request.user)
                request.session.pop('form6')
        else:
            form6 = FormImovel(request.user)

        if request.session.get('form7'):
            tempo_form = datetime.datetime.strptime(request.session.get('form7')[1], '%H:%M:%S')
            tempo_agora = datetime.datetime.strptime(datetime.datetime.now().time().strftime('%H:%M:%S'), '%H:%M:%S')

            if tempo_form + timedelta(seconds=settings.TEMPO_SESSION_FORM) > tempo_agora:
                form7 = FormAnotacoes(request.user, request.session.get('form7')[0])
            else:
                form7 = FormAnotacoes(initial={'data_registro': datetime.date.today().strftime('%Y-%m-%d')})
                request.session.pop('form7')
        else:
            form7 = FormAnotacoes(initial={'data_registro': datetime.date.today().strftime('%Y-%m-%d')})

        if request.user.is_superuser or settings.DEBUG:
            form8 = FormAdmin(
                initial={'qtd_usuario': settings.FICT_QTD['qtd_usuario'],
                         'qtd_locatario': settings.FICT_QTD['qtd_locatario'],
                         'qtd_imovel_g': settings.FICT_QTD['qtd_imovel_g'],
                         'qtd_imovel': settings.FICT_QTD['qtd_imovel'],
                         'qtd_contrato': settings.FICT_QTD['qtd_contrato'],
                         'qtd_pagamento': settings.FICT_QTD['qtd_pagamento'],
                         'qtd_gasto': settings.FICT_QTD['qtd_gasto'],
                         'qtd_nota': settings.FICT_QTD['qtd_nota'],
                         'qtd_sugestao': settings.FICT_QTD['qtd_sugestao'],
                         'qtd_contr_modelo': settings.FICT_QTD['qtd_contr_modelo'],
                         'para_o_usuario': request.user})
        else:
            form8 = ''

        context = {'form_pagamento': form1, 'form_mensagem': form2, 'form_gasto': form3, 'form_locatario': form4,
                   'form_contrato': form5, 'form_imovel': form6, 'form_notas': form7, 'botao_admin': form8}
        return context
    else:
        context = {}
        return context


def navbar_notificacoes(request):
    if request.user.is_authenticated:
        notific = Notificacao.objects.filter(do_usuario=request.user, lida=False, apagada_oculta=False).order_by(
            '-data_registro')
        notific_hist = Notificacao.objects.filter(do_usuario=request.user, lida=True, apagada_oculta=False).order_by(
            '-data_lida')
        context = {'notificacoes': notific[:request.user.notif_qtd],
                   'notificacoes_hist': notific_hist[:request.user.notif_qtd_hist]}
        return context
    else:
        context = {}
        return context


def ultima_pagina_valida(request):
    """Esta função registra na sessão do usuário, para qualquer tipo de uso pelo programa, o reverse da última página
     visitada pelo usuário, desde que esta página não seja a de exclusão de algum objeto. Criada para resolver um
      problema em que após excluir um item, o site não conseguia redirecionar para a última página anterior a de
      exclusão"""
    from django.urls import resolve
    current_reverse = f"{resolve(request.path_info).namespace}:{resolve(request.path_info).url_name}"
    context = {}
    if 'Excluir' not in current_reverse:
        request.session['ult_pag_valida_reverse'] = current_reverse
    return context
