import os, json, datetime
from dateutil.relativedelta import relativedelta

from Alugue_seu_imovel import settings

from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.db.models.signals import pre_delete, post_save, pre_save, post_delete
from django.db import transaction
from django.forms.models import model_to_dict
from django.dispatch import receiver

from core.models import Contrato, Locatario, Parcela, Pagamento, Usuario, Notificacao, Anotacoe, Sugestao, Slot, Imovei, \
    ContratoModelo, modelo_variaveis, modelo_condicoes, DevMensagen

from django.dispatch import receiver
from django.contrib.sites.shortcuts import get_current_site
from two_factor.signals import user_verified

from .tasks import gerar_contrato_pdf


# FUNÇÕES COMPARTILHADAS \/  ---------------------------------------

def verificar_aluguel_vencimento(do_usuario, contrato=None):
    """Esta função verifica quando o aluguel de alguém vence(e/ou faltando 5 dias).
    2. A função deve ser chamada ao fazer login e ao criar/editar um contrato.
    Se -Condição True e -Ainda não existe notificação(relacionada a esta parcela) e -Sua execução está
    autorizada em 'configurações de notificações':
    criar uma notificação para o usuário informando o fato."""
    if contrato:
        contrato_s = Contrato.objects.filter(do_locador=do_usuario, pk=contrato.pk)
    else:
        contrato_s = Contrato.objects.ativos_margem(dias_atras=15).filter(do_locador=do_usuario)
    parcelas = Parcela.objects.de_contratos_ativos().filter(do_usuario=do_usuario, apagada=False,
                                                            do_contrato__in=contrato_s)
    tipo_conteudo = ContentType.objects.get_for_model(Parcela)
    for parcela in parcelas:
        if parcela.esta_vencida():
            if not parcela.get_notific_esta_vencida():
                # Verificar se deve ou não criar notificação, neste caso, criar se user.notif_parc_venc_2 não está no
                # None e se a data de vencimento desta parcela é maior que a data em user.notif_parc_venc_2
                if do_usuario.notif_parc_venc_2 is not None:
                    if parcela.data_pagm_ref >= do_usuario.notif_parc_venc_2.date():
                        criar_uma_notificacao(do_usuario=do_usuario, autor_classe=tipo_conteudo, objeto_id=parcela.pk,
                                              assunto=2)

        if parcela.vence_em_ate_x_dias(5):
            if not parcela.get_notific_vence_em_ate_x_dias():
                # Verificar se deve ou não criar notificação, neste caso, criar se user.notif_parc_venc_1 não está no
                # None e se a data de vencimento desta parcela -5 dias é maior que a data em user.notif_parc_venc_2
                # ou menor que hoje
                if do_usuario.notif_parc_venc_1 is not None:
                    # Abaixo verificar se o usuario quer receber esta notificação, porém, deve-se notificar apenas
                    # as parcelas que vencerão depois do dia em que ele autorizou a notificação, as de antes não, ou
                    # seja, esta regra não retroage
                    vence_em = parcela.data_pagm_ref
                    data_autorizacao = do_usuario.notif_parc_venc_2.date()
                    if vence_em > data_autorizacao:
                        criar_uma_notificacao(do_usuario=do_usuario, autor_classe=tipo_conteudo, objeto_id=parcela.pk,
                                              assunto=3)


def verificar_contrato_vencimento(do_locador, contrato=None):
    """Esta função verifica quando o contrato de alguém vence(e/ou faltando 30 dias).
    2. A função deve ser chamada ao fazer login e ao criar/editar um contrato.
    Se: -Condição True e -Ainda não existe notificação(relacionada a esta parcela) e -Sua execução está
    autorizada em 'configurações de notificações':
    criar uma notificação para o usuário informando o fato."""
    if contrato:
        contrato_s = Contrato.objects.ativos_margem(dias_atras=15).filter(do_locador=do_locador, pk=contrato.pk)
    else:
        contrato_s = Contrato.objects.ativos_margem(dias_atras=15).filter(do_locador=do_locador)

    tipo_conteudo = ContentType.objects.get_for_model(Contrato)
    for contrato in contrato_s:
        if contrato.periodo_vencido():
            if not contrato.get_notific_periodo_vencido():
                # Verificar se deve ou não criar notificação, neste caso, criar se user.notif_contrato_venc_2 não está
                # no None e se a data de vencimento deste contrato é maior que a data em user.notif_parc_venc_2
                if do_locador.notif_contrato_venc_2 is not None:
                    if contrato.data_saida() >= do_locador.notif_contrato_venc_2.date():
                        lida = True if contrato.rescindido is False else False
                        criar_uma_notificacao(do_usuario=do_locador, autor_classe=tipo_conteudo, objeto_id=contrato.pk,
                                              assunto=3, lida=lida)
        dias = 31
        if contrato.vence_em_ate_x_dias(dias):
            if not contrato.get_notific_vence_em_ate_x_dias():
                # Verificar se deve ou não criar notificação, neste caso, criar se user.notif_contrato_venc_1 não está
                # no None e se a data de vencimento deste contrato -30 dias é maior que a data em user.notif_parc_venc_2
                # ou menor que hoje
                if do_locador.notif_contrato_venc_1 is not None:
                    vence_em = contrato.data_saida()
                    data_autorizacao = do_locador.notif_contrato_venc_1.date()
                    if vence_em > data_autorizacao:
                        criar_uma_notificacao(do_usuario=do_locador, autor_classe=tipo_conteudo, objeto_id=contrato.pk,
                                              assunto=2)


def gerenciar_parcelas(instance_contrato):
    # Criar as parcelas que não existem, definir apagadas as parcelas fora do range('data_pagm_ref')
    # e manter as que já existem e estão no range

    parcelas = Parcela.objects.filter(do_contrato=instance_contrato)
    parcelas_datas = parcelas.values_list('data_pagm_ref', flat=True)
    if parcelas:
        # Criar as novas parcelas dentro do range, manter as existentes(dentro tbm) e
        # 'definir apagadas' parcelas fora do range
        data_entrada = instance_contrato.data_entrada

        # Apagar parcelas fora do range:
        # Pegar datas atualizadas a partir da data de entrada e duração do contrato
        datas = []
        for x in range(0, instance_contrato.duracao):
            data = data_entrada.replace(day=instance_contrato.dia_vencimento) + relativedelta(months=x)
            datas.append(data)
        for parcela in parcelas:
            if parcela.data_pagm_ref not in datas:
                parcela.definir_apagada()
                if parcela.get_notific_pgm():
                    Notificacao.objects.filter(pk=parcela.get_notific_pgm().pk).update(apagada_oculta=True)
            else:
                parcela.restaurar()
                if parcela.get_notific_pgm():
                    Notificacao.objects.filter(pk=parcela.get_notific_pgm().pk).update(apagada_oculta=False)

        for data in datas:
            if data not in parcelas_datas:
                parcela = Parcela(do_usuario=instance_contrato.do_locador, do_contrato=instance_contrato,
                                  do_imovel=instance_contrato.do_imovel,
                                  do_locatario=instance_contrato.do_locatario,
                                  data_pagm_ref=data)
                parcela.save()
    else:
        # Criar parcelas zeradas
        for x in range(0, instance_contrato.duracao):
            data_entrada = instance_contrato.data_entrada
            data = data_entrada.replace(day=instance_contrato.dia_vencimento) + relativedelta(months=x)
            parcela = Parcela(do_usuario=instance_contrato.do_locador, do_contrato=instance_contrato,
                              do_imovel=instance_contrato.do_imovel,
                              do_locatario=instance_contrato.do_locatario,
                              data_pagm_ref=data)
            parcela.save()


def tratar_pagamentos(instance_contrato):
    # Pegar informações para tratamento
    contrato = Contrato.objects.get(pk=instance_contrato.pk)
    parcelas = Parcela.objects.filter(do_contrato=contrato.pk, apagada=False).order_by('data_pagm_ref')

    # Pega o total pago para este contrato e distribui para as parcelas do contrato
    pagamentos_tt = int(contrato.pagamento_total())
    valor_mensal = int(contrato.valor_mensal)
    for mes_n, parcela in enumerate(parcelas):
        if pagamentos_tt > valor_mensal:
            # print(f'Mês {mes_n}: Mensalidade({valor_mensal}), pois o pagamentos_total({pagamentos_tt}) é maior')
            parcela.tt_pago = valor_mensal
            pagamentos_tt -= valor_mensal
        elif 0 < pagamentos_tt <= valor_mensal:
            # print(f'Mês {mes_n}: pagamentos_tt({pagamentos_tt}), pois é menor que a mensalidade({valor_mensal})')
            parcela.tt_pago = pagamentos_tt
            pagamentos_tt -= valor_mensal
            # parcela.recibo_entregue = False
        else:
            # print(f'Mês {mes_n}: 0, pois o pagamento total está em {pagamentos_tt}')
            parcela.tt_pago = 0
        parcela.save(update_fields=['tt_pago'])


def criar_uma_notificacao(do_usuario, autor_classe, objeto_id, lida=False, assunto=int()):
    notific = Notificacao()
    notific.do_usuario = do_usuario
    notific.autor_classe = autor_classe
    notific.objeto_id = objeto_id
    if lida is True:
        notific.lida = lida
        notific.data_registro = datetime.datetime.now()
    if assunto:
        notific.assunto = assunto
    notific.save()
    return notific


# Gerenciadores de pre_save \/  ---------------------------------------
@receiver(pre_save, sender=Parcela)
def parcela_pre_save(sender, instance, **kwargs):
    if instance.pk is None:  # if criado
        pass
    else:
        # Parcela quitada? então criar uma notificação de pagamento para este objeto e marcar avisos(de 5 dias para
        # vencimento e/ou vencida) como lidos
        tipo_conteudo = ContentType.objects.get_for_model(Parcela)
        objeto_id = instance.pk
        if instance.esta_pago():
            usuario = instance.do_contrato.do_locador
            if instance.get_notific_pgm() is None:
                if instance.do_usuario.notif_recibo is not None:
                    criar_uma_notificacao(do_usuario=usuario, autor_classe=tipo_conteudo, objeto_id=objeto_id,
                                          assunto=1)

            vencera = Notificacao.objects.filter(do_usuario=usuario, autor_classe=tipo_conteudo,
                                                 objeto_id=objeto_id, assunto=3).first()
            if vencera:
                vencera.definir_lida()
            venceu = Notificacao.objects.filter(do_usuario=usuario, autor_classe=tipo_conteudo, objeto_id=objeto_id,
                                                assunto=2).first()
            if venceu:
                venceu.definir_lida()
        else:
            # Se não quitada definir apagada (caso haja).
            notific = Notificacao.objects.filter(autor_classe=tipo_conteudo, objeto_id=objeto_id, assunto=1)
            if notific.first():
                notific.first().definir_apagada()


@receiver(pre_save, sender=Usuario)
def usuario_pre_save(sender, instance, **kwargs):
    if instance.pk is None:  # if criado
        pass
    else:
        # Apaga todos os recibos em pdf do usuário(para que novos possam ser criados) quando se modifica informações
        # desta model contidas neles (RG, CPF, First Name, Last Name)
        # Também apaga quando o usuário troca o preenchimento do campo data
        ante = Usuario.objects.get(pk=instance.pk)

        try:
            if ante.RG != instance.RG or ante.cpf() != instance.cpf() or ante.first_name != instance.first_name \
                    or ante.last_name != instance.last_name \
                    or ante.recibo_preenchimento != int(instance.recibo_preenchimento):
                contratos = Contrato.objects.filter(do_locador=instance)
                for contrato in contratos:
                    contrato.recibos_pdf.delete()
        except:
            pass


@receiver(pre_save, sender=Locatario)
def locatario_pre_save(sender, instance, **kwargs):
    if instance.pk is None or kwargs['raw']:  # Se criado ou vem de fixture
        pass
    else:
        # Apaga todos os recibos em pdf do locatário(para que novos possam ser criados) quando se modifica
        # informações desta model contidas neles
        ante = Locatario.objects.get(pk=instance.pk)
        if ante.RG != instance.RG or ante.cpf() != instance.cpf() or ante.nome != instance.nome:
            contratos = Contrato.objects.filter(do_locatario=instance)
            for contrato in contratos:
                contrato.recibos_pdf.delete()
            pass


@receiver(pre_save, sender=Contrato)
def contrato_pre_save(sender, instance, **kwargs):
    if instance.pk is None or kwargs['raw']:  # Se criado ou vem de fixture
        pass
    else:
        # Após modificar/editar um contrato(parameters: duracao e data_entrada):
        # Editar as parcelas (função gerenciar_parcelas)
        # E com a função: tratar_pagamentos \/
        #   1. Recalcular as parcelas (model Parcela) pagas a partir do total de pagamentos armazenados
        #   no seu respectivo contrato.
        #   2. Enviar as notificações relacionadas.

        ante = Contrato.objects.get(pk=instance.pk)
        if ante.duracao != instance.duracao or ante.data_entrada != instance.data_entrada:
            gerenciar_parcelas(instance_contrato=instance)
            tratar_pagamentos(instance_contrato=instance)

        if instance.em_posse is True:
            # Ao editar um contrato, se em_posse is true, marcar a sua notificação como lida.
            try:
                notificacao = Notificacao.objects.filter(pk=instance.get_notific_criado().pk)
                notificacao.definir_lida()
            except:
                pass


@receiver(pre_save, sender=Anotacoe)
def anotacao_pre_save(sender, instance, **kwargs):
    # Criar e apagar notificação referente a anotações
    if instance.pk is None or kwargs['raw']:  # Se criado ou vem de fixture
        pass
    else:
        # If editado
        ante = Anotacoe.objects.get(pk=instance.pk)
        if instance.tarefa is False and ante.tarefa != instance.tarefa:
            # Defini apagada a notificação referente à anotação se o usuário ao editar a anotação.
            notific = Notificacao.objects.filter(autor_classe=ContentType.objects.get_for_model(Anotacoe),
                                                 objeto_id=instance.pk).first()
            if notific:
                notific.definir_apagada()

        elif instance.tarefa is True and ante.tarefa != instance.tarefa:
            # Criar a notificação referente à anotação se o usuário ao editar a anotação, marcar o botão tarefa.
            usuario = ante.do_usuario
            tipo_conteudo = ContentType.objects.get_for_model(Anotacoe)
            objeto_id = instance.pk
            criar_uma_notificacao(do_usuario=usuario, autor_classe=tipo_conteudo, objeto_id=objeto_id)
        if instance.feito:
            try:
                Notificacao.objects.filter(pk=instance.da_notificacao.pk).update(data_lida=datetime.datetime.now())
            except:
                pass


@receiver(pre_save, sender=Sugestao)
def sugestao_pre_save(sender, instance, **kwargs):
    if instance.pk is None:  # if criado
        pass
    else:
        if instance.aprovada is True:
            usuario = instance.do_usuario
            tipo_conteudo = ContentType.objects.get_for_model(Sugestao)
            objeto_id = instance.pk
            notific = criar_uma_notificacao(do_usuario=usuario, autor_classe=tipo_conteudo, objeto_id=objeto_id)
            Sugestao.objects.filter(pk=instance.pk).update(da_notificacao=notific)
        else:
            if instance.da_notificacao:
                instance.da_notificacao.definir_apagada()


@receiver(post_save, sender=ContratoModelo)
def contrato_modelo_post_save(sender, instance, created, **kwargs):
    # Tem outro gerar_contrato_pdf em visualizar_modelo em views (backup deste)
    if instance.verificar_utilizacao_config() and not instance.verificar_utilizacao_usuarios():
        pass
    else:
        fields = ['id', 'corpo', ]
        dados = {'modelo_pk': instance.pk, 'modelo': model_to_dict(instance, fields=fields),
                 'usuario_username': str(instance.autor.username),
                 'contrato_modelo_code': instance.autor.contrato_modelo_code()}
        local = f'contratos_modelos/{dados["contrato_modelo_code"]}{dados["modelo_pk"]}.pdf'
        gerar_contrato_pdf.delay(dados=dados, local=local, visualizar=True)
        variaveis = []
        for i, j in modelo_variaveis.items():
            if j[0] in instance.corpo:
                variaveis.append(i)
        variaveis = list(dict.fromkeys(variaveis))
        condicoes = []
        for i, j in modelo_condicoes.items():
            if j[0] in instance.corpo:
                condicoes.append(i)
        condicoes = list(dict.fromkeys(condicoes))
        ContratoModelo.objects.filter(pk=instance.pk).update(variaveis=variaveis, condicoes=condicoes,
                                                             visualizar=local)


@receiver(post_save, sender=Usuario)
def usuario_post_save(sender, instance, created, **kwargs):
    if created:
        for _ in range(0, instance.locat_slots):
            Slot.objects.create(do_usuario=instance, gratuito=True)


@receiver(post_save, sender=Anotacoe)
def anotacao_post_save(sender, instance, **kwargs):
    # Criar e apagar notificação referente a anotações
    if instance.tarefa:
        usuario = instance.do_usuario
        tipo_conteudo = ContentType.objects.get_for_model(Anotacoe)
        objeto_id = instance.pk
        notific = criar_uma_notificacao(do_usuario=usuario, autor_classe=tipo_conteudo, objeto_id=objeto_id,
                                        lida=True if instance.feito else False)
        Anotacoe.objects.filter(pk=instance.pk).update(da_notificacao=notific)


@transaction.atomic
@receiver(post_save, sender=Locatario)
def locatario_post_save(sender, instance, **kwargs):
    if instance.temporario is True:
        tipo_conteudo = ContentType.objects.get_for_model(Locatario)
        notific = criar_uma_notificacao(do_usuario=instance.do_locador, autor_classe=tipo_conteudo,
                                        objeto_id=instance.pk)
        instance.da_notificacao = notific
        Locatario.objects.filter(pk=instance.pk).update(da_notificacao=notific)


@transaction.atomic
@receiver(post_save, sender=Contrato)
def contrato_post_save(sender, instance, created, **kwargs):
    # Pega os dados para tratamento:
    if created:
        # Gera as parcelas quando o contrato é criado:
        gerenciar_parcelas(instance)
        # Criar notificação 'contrato criado' com o botão 'receber contrato'
        tipo_conteudo = ContentType.objects.get_for_model(Contrato)
        if instance.do_locador.notif_contrato_criado is not None:
            lida = True if instance.em_posse is True else False
            criar_uma_notificacao(do_usuario=instance.do_locador, autor_classe=tipo_conteudo,
                                  objeto_id=instance.pk, lida=lida, assunto=1)
    else:
        verificar_aluguel_vencimento(do_usuario=instance.do_locador, contrato=instance)
        verificar_contrato_vencimento(do_locador=instance.do_locador, contrato=instance)


@receiver(post_save, sender=Pagamento)
def pagamento_post_save(sender, instance, created, **kwargs):
    # Após criar um pagamento:
    # Com a função: tratar_pagamentos \/
    # 1. Recalcular as parcelas (model Parcela) pagas a partir do total de pagamentos armazenados
    # no seu respectivo contrato
    # 2. Enviar as notificações relacionadas
    tratar_pagamentos(instance_contrato=instance.ao_contrato)


@receiver(pre_save, sender=DevMensagen)
def dev_mensagem_pre_save(sender, instance, **kwargs):
    if instance.pk is None:  # if criado
        pass
    else:
        ante = DevMensagen.objects.get(pk=instance.pk)
        if instance.resposta != '' and ante.resposta != instance.resposta:
            usuario = instance.do_usuario
            objeto_id = instance.pk
            tipo_conteudo = ContentType.objects.get_for_model(DevMensagen)
            notific = criar_uma_notificacao(do_usuario=usuario, autor_classe=tipo_conteudo, objeto_id=objeto_id)
            instance.da_notificacao = notific
        elif instance.resposta == '':
            instance.da_notificacao.definir_apagada()


# Gerenciadores de pre_delete \/  ---------------------------------------
@transaction.atomic
@receiver(pre_delete, sender=Contrato)
def contrato_pre_delete(sender, instance, **kwards):
    # Apagar as notificações deste contrato
    notificacoes = instance.get_notific_all()
    if notificacoes:
        for notificacao in notificacoes:
            notificacao.delete()


# Apaga as notificações dos objetos quando eles forem apagados \/
@receiver(pre_delete, sender=Anotacoe)
def anotacao_pre_delete(sender, instance, **kwargs):
    # Apagar a notificação desta anotação
    if instance.da_notificacao:
        Notificacao.objects.filter(pk=instance.da_notificacao.pk).delete()


@receiver(pre_delete, sender=Sugestao)
def sugestao_pre_delete(sender, instance, **kwargs):
    # Apagar a notificação desta sugestão
    if instance.da_notificacao:
        Notificacao.objects.filter(pk=instance.da_notificacao.pk).delete()


@receiver(pre_delete, sender=Locatario)
def locatario_pre_delete(sender, instance, **kwargs):
    # Apagar a notificação deste locatário
    if instance.da_notificacao:
        Notificacao.objects.filter(pk=instance.da_notificacao.pk).delete()


@receiver(pre_delete, sender=Parcela)
def parcela_pre_delete(sender, instance, **kwargs):
    # Apagar as notificações desta parcela
    notificacoes = instance.get_notific_all()
    if notificacoes:
        for parcela in notificacoes:
            parcela.delete()


@receiver(pre_delete, sender=Slot)
def slot_pre_delete(sender, instance, **kwargs):
    # Apagar as notificações deste slot
    if instance.da_notificacao:
        Notificacao.objects.filter(pk=instance.da_notificacao.pk).delete()


# Gerenciadores de post_delete \/  ---------------------------------------
@receiver(post_delete, sender=Pagamento)
def pagamento_post_delete(sender, instance, **kwards):
    # Após apagar um pagamento:
    # Com a função: tratar_pagamentos \/
    # 1. Recalcular as parcelas (model Parcela) pagas a partir do total de pagamentos armazenados
    # no seu respectivo contrato
    # 2. Enviar as notificações relacionadas
    tratar_pagamentos(instance_contrato=instance.ao_contrato)


# Gerenciadores de login e logout \/  ---------------------------------------
@receiver(user_logged_in)
def usuario_fez_login(sender, user, **kwargs):
    if user.is_superuser and user.username == 'fbaugusto':
        caminho = fr"C:\Users\Fabio\PycharmProjects\alugueseuimovel2024\home\fixtures\recibos_entregues.json"
        caminho_2 = fr"C:\Users\Fabio\PycharmProjects\alugueseuimovel2024\home\fixtures\dados_do_predio.json"
        caminho_3 = fr"C:\Users\Fabio\PycharmProjects\alugueseuimovel2024\home\fixtures\locatarios_cpfs.json"

        # Marcar os recibos entregues
        if os.path.isfile(caminho):
            arquivo = open(caminho)
            dados = json.load(arquivo)
            for key, value in dados['dados'].items():
                parcelas = Parcela.objects.filter(do_contrato=key).order_by('data_pagm_ref')
                for index, parcela in enumerate(parcelas):
                    parcela.recibo_entregue = 1 if index < value else 0
                    parcela.save(update_fields=['recibo_entregue', ])
                    if parcela.get_notific_pgm() and index < value:
                        # \/ Aqui as parcelas pagas e recibo entregue
                        parcela.get_notific_pgm().definir_lida()
                    elif parcela.get_notific_pgm() and index >= value:
                        # \/ Aqui as parcelas pagas, mas recibo não entregue
                        parcela.get_notific_pgm().definir_nao_lida()
            arquivo.close()
            os.remove(caminho)
        if os.path.isfile(caminho_2):
            os.remove(caminho_2)

        # Preencher os CPFs criptografados dos locatários
        if os.path.isfile(caminho_3):
            arquivo = open(caminho_3)
            dados = json.load(arquivo)
            for n, cpf in enumerate(dados):
                locatario = Locatario.objects.get(pk=n + 1)
                cpf_enc = bytes(cpf, 'UTF-8')
                locatario.cript_cpf = cpf_enc
                locatario.save(update_fields=['cript_cpf', ])
                arquivo.close()
            os.remove(caminho_3)

            # Criar slots restantes
            imoveis_qtd = Imovei.objects.filter(do_locador=user).count()
            if imoveis_qtd > 3:
                for n in range(3, imoveis_qtd):
                    Slot.objects.create(do_usuario=user, gratuito=False, tickets=1)
    # Verificar se tem algum slot vencido e enviar uma notificação avisando o usuário, caso a notificação já exista,
    # não enviar nada.
    inativos_com_imovel = Slot.objects.inativos_com_imovel().filter(do_usuario=user)
    for slot in inativos_com_imovel:
        tipo_conteudo = ContentType.objects.get_for_model(Slot)
        notific = criar_uma_notificacao(do_usuario=user, autor_classe=tipo_conteudo, objeto_id=slot.pk)
        Slot.objects.filter(pk=slot.pk).update(da_notificacao=notific)

    verificar_aluguel_vencimento(do_usuario=user, contrato=None)
    verificar_contrato_vencimento(do_locador=user, contrato=None)


@receiver(user_logged_out)
def usuario_fez_logout(sender, user, **kwargs):
    if user:
        # Apagar arquivos temporários da sessão do usuário
        # 1. Tabela_docs
        diretorio = rf'{settings.MEDIA_ROOT}/tabela_docs'
        se_existe = os.path.exists(diretorio)
        if not se_existe:
            os.makedirs(diretorio)
        for file in os.listdir(diretorio):
            if file.endswith(f"{user}.pdf"):
                os.remove(os.path.join(diretorio, file))

        # 2. Contrato_docs
        diretorio = f'{settings.MEDIA_ROOT}/contrato_docs'
        se_existe = os.path.exists(diretorio)
        if not se_existe:
            os.makedirs(diretorio)
        code = user.contrato_code()
        for file in os.listdir(diretorio):
            if file.startswith(code):
                os.remove(os.path.join(diretorio, file))
