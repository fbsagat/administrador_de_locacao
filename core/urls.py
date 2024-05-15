from django.urls import path
from django.urls import reverse_lazy
from django.contrib.auth import views as auth_view

from core.views import visao_geral, Locatarios, Imoveis, Contratos, registrar_pagamento, registrar_imovel, \
    registrar_anotacao, registrar_contrato, registrar_locat, EditarLocat, ExcluirLocat, registrar_gasto, Pagamentos, \
    Gastos, Notas, EditarGrup, ExcluirGrupo, EditarImov, ExcluirImov, criar_grupo, rescindir_contrat, recebido_contrat, \
    ExcluirPagm, EditarContrato, ExcluirContrato, EditarGasto, ExcluirGasto, EditarAnotacao, ExcluirAnotacao, recibos, \
    ApagarConta, Homepage, CriarConta, EditarPerfil, mensagem_desenvolvedor, gerador_de_ficticios, ImoveisAtivos, \
    LocatariosAtivos, ContratosAtivos, eventos, tabela, recibo_entregue, afazer_concluida, gerar_contrato, criar_modelo, \
    editar_modelo, ExcluirModelo, MeusModelos, forum_sugestoes, like_de_sugestoes, apagar_sugestao, \
    implementar_sugestao, aprovar_sugestao, arquivos_sugestoes_docs, arquivos_locatarios_docs, \
    arquivos_mensagens_ao_dev, arquivos_recibos_docs, arquivos_tabela_docs, arquivos_contrato_docs, \
    arquivos_gastos_docs, locat_auto_registro, RevisarLocat, painel_slots, add_slot, apagar_slot, \
    adicionar_ticket, adicionar_ticket_todos, painel_configs, ModelosComunidade, confirmar_email, \
    arquivos_contratos_modelos, visualizar_modelo, copiar_modelo, notificacao_lida, conversa_com_o_dev, \
    configurar_notificacoes, configurar_app, baixar_planilha, botao_teste, activate_account_link, \
    exclusao_de_conta, trocar_link_auto_registro

from financeiro.views import painel_loja
from Alugue_seu_imovel import settings

app_name = 'core'

urlpatterns = [
    # BOTÕES PRINCIPAIS -------------------
    path('visao_geral/', visao_geral, name='Visão Geral'),
    path('eventos/', eventos, name='Eventos'),
    path('imoveis_ativos/', ImoveisAtivos.as_view(), name='Imóveis Ativos'),
    path('locatarios_ativos/', LocatariosAtivos.as_view(), name='Locatários Ativos'),
    path('contratos_ativos/', ContratosAtivos.as_view(), name='Contratos Ativos'),

    # ABA REGISTRAR -------------------

    # PAGAMENTO -------------------
    path('registrar_pagamento/', registrar_pagamento, name='Registrar Pagamento'),
    path('excluir_pagamento/<int:pk>/', ExcluirPagm.as_view(), name='Excluir Pagamento'),

    # GASTO -------------------
    path('registrar_gasto/', registrar_gasto, name='Registrar Gasto'),
    path('editar_registro_de_gasto/<int:pk>/', EditarGasto.as_view(), name='Editar Gasto'),
    path('excluir_registro_de_gasto/<int:pk>/', ExcluirGasto.as_view(), name='Excluir Gasto'),

    # LOCATÁRIO -------------------
    path('registro_de_locatario/', registrar_locat, name='Registrar Locatario'),
    path('editar_registro_de_locatario/<int:pk>/', EditarLocat.as_view(), name='Editar Locatario'),
    path('excluir_registro_de_locatario/<int:pk>/', ExcluirLocat.as_view(), name='Excluir Locatario'),

    # LOCATÁRIO AUTO-REGISTRO -------------------
    path('locatario_auto_registro/<str:code>/', locat_auto_registro, name='Locatario Auto-Registro'),
    path('trocar_link_auto_registro', trocar_link_auto_registro, name='Auto-Registro Trocar Link'),
    path('revisar_registro_de_locatario/<int:pk>/', RevisarLocat.as_view(), name='Revisar Locatário'),

    # CONTRATO -------------------
    path('registrar_contrato/', registrar_contrato, name='Registrar Contrato'),
    path('contrato_rescindido/<int:pk>/', rescindir_contrat, name='Rescindir Contrato'),
    path('receber_contrato/<int:pk>/<str:tipo>/', recebido_contrat, name='Contrato Recebido'),
    path('editar_contrato/<int:pk>/', EditarContrato.as_view(), name='Editar Contrato'),
    path('excluir_contrato/<int:pk>/', ExcluirContrato.as_view(), name='Excluir Contrato'),

    # GRUPO -------------------
    path('criar_grupo/', criar_grupo, name='Criar Grupo Imóveis'),
    path('editar_grupo/<int:pk>/', EditarGrup.as_view(), name='Editar Grupo Imóveis'),
    path('excluir_grupo/<int:pk>/', ExcluirGrupo.as_view(), name='Excluir Grupo Imóveis'),

    # IMÓVEL -------------------
    path('registrar_imovel/', registrar_imovel, name='Registrar Imóvel'),
    path('editar_regimov/<int:pk>/', EditarImov.as_view(), name='Editar Imóvel'),
    path('excluir_regimov/<int:pk>/', ExcluirImov.as_view(), name='Excluir Imóvel'),

    # ANOTAÇÕES -------------------
    path('registrar_anotacoes/', registrar_anotacao, name='Registrar Anotação'),
    path('editar_anotacao/<int:pk>/', EditarAnotacao.as_view(), name='Editar Anotação'),
    path('excluir_anotacao/<int:pk>/', ExcluirAnotacao.as_view(), name='Excluir Anotação'),

    # ABA GERAR -------------------
    path('recibos_PDF/', recibos, name='Recibos PDF'),
    path('tabela_PDF/', tabela, name='Tabela PDF'),
    path('contrato_PDF/', gerar_contrato, name='Contrato PDF'),

    # MODELO DE CONTRATO -------------------
    path('modelos/', MeusModelos.as_view(), name='Modelos'),
    path('criar_modelo/', criar_modelo, name='Criar Modelo'),
    path('editar_modelo/<int:pk>/', editar_modelo, name='Editar Modelo'),
    path('copiar_modelo/<int:pk>/', copiar_modelo, name='Copiar Modelo'),
    path('visualizar_modelo/<int:pk>/', visualizar_modelo, name='Visualizar Modelo'),
    path('excluir_modelo/<int:pk>/<int:pag_orig>/', ExcluirModelo.as_view(), name='Excluir Modelo'),
    path('contrato_modelos_comunidade/', ModelosComunidade.as_view(), name='Modelos Comunidade'),

    # ABA HISTÓRICO -------------------
    path('pagamentos/', Pagamentos.as_view(), name='Pagamentos'),
    path('gastos/', Gastos.as_view(), name='Gastos'),
    path('locatarios/', Locatarios.as_view(), name='Locatários'),
    path('imoveis/', Imoveis.as_view(), name='Imóveis'),
    path('anotacoes/', Notas.as_view(), name='Anotações'),
    path('contratos/', Contratos.as_view(), name='Contratos'),

    # NOTIFICAÇÕES -------------------
    path('recibo_entregue/<int:pk>/', recibo_entregue, name='Recibo Entregue'),
    path('afazer_concluida/<int:pk>/', afazer_concluida, name='Afazer Concluida'),
    path('notificacao_lida/<int:pk>/', notificacao_lida, name='Notificação Lida'),

    # DESENVOLVIMENTO -------------------
    path('mensagem_para_o_dev/', mensagem_desenvolvedor, name='Mensagem pro Desenvolvedor'),
    path('mensagem_para_o_dev_resposta/<int:pk>/', conversa_com_o_dev, name='Conversa Dev'),
    path('sugestoes_docs/', forum_sugestoes, name='Sugestões'),
    path('sugestao_like/<int:pk>/', like_de_sugestoes, name='like de Sugestão'),
    path('sugestao_apagar/<int:pk>/', apagar_sugestao, name='Apagar Sugestão'),
    path('sugestao_implementar/<int:pk>/', implementar_sugestao, name='Implementar Sugestão'),
    path('sugestao_aprovar/<int:pk>/', aprovar_sugestao, name='Aprovar Sugestão'),

    # PAINEL -------------------
    path('painel_slots/', painel_slots, name='Painel Slots'),
    path('painel_configuracoes/', painel_configs, name='Painel Configs'),
    path('configurar_notificacoes/', configurar_notificacoes, name='Configurar Notificações'),
    path('configurar_app/', configurar_app, name='Configurar App'),
    path('baixar_planilha/', baixar_planilha, name='Baixar Planilha'),
    path('painel_loja/', painel_loja, name='Painel Loja'),
    path('adicionar_slot/', add_slot, name='Add Slot'),
    path('apagar_slot/<int:pk>/', apagar_slot, name='Apagar Slot'),
    path('adicionar_ticket/<int:pk>/', adicionar_ticket, name='Adicionar Ticket'),
    path('adicionar_ticket_todos/', adicionar_ticket_todos, name='Adicionar Ticket Todos'),

    # GERAL -------------------
    path('', Homepage.as_view(), name='Home'),
    path('criar_conta/', CriarConta.as_view(), name='Criar Conta'),
    path('confirmar_email/<str:user_pk>/', confirmar_email, name='Confirmar Email'),
    path('ativar_conta_url/<str:link>/', activate_account_link, name='Ativar Conta Url'),
    path('apagar_conta_enviar_email/', exclusao_de_conta, name='Apagar Conta Email'),
    path('apagar_conta/<str:link>/', ApagarConta.as_view(), name='Apagar Conta'),
    path('mudar_senha/', auth_view.PasswordChangeView.as_view(
        template_name='editar_perfil.html/', success_url=reverse_lazy('core:Home'),
        extra_context={'SITE_NAME': settings.SITE_NAME}), name='Mudar Senha'),
    path('editar_perfil/', EditarPerfil.as_view(), name='Editar Perfil'),
    path('logout/', auth_view.LogoutView.as_view(), name='Logout'),
    path('gerador_de_ficticios/', gerador_de_ficticios, name='Gerador de Fictícios'),
    path('botao_teste/', botao_teste, name='Botão Teste'),

    # SERVIDORES DE ARQUIVOS -------------------
    path('media/contratos_modelos/<str:file>/', arquivos_contratos_modelos),
    path('media/sugestoes_docs/<str:year>/<str:month>/<str:file>/', arquivos_sugestoes_docs),
    path('media/locatarios_docs/<str:year>/<str:month>/<str:file>/', arquivos_locatarios_docs),
    path('media/gastos_comprovantes/<str:year>/<str:month>/<str:file>/', arquivos_gastos_docs),
    path('media/mensagens_ao_dev/<str:year>/<str:month>/<str:file>/', arquivos_mensagens_ao_dev),
    path('media/recibos_docs/<str:year>/<str:month>/<str:file>/', arquivos_recibos_docs),
    path('media/tabela_docs/<str:file>/', arquivos_tabela_docs),
    path('media/contrato_docs/<str:file>/', arquivos_contrato_docs),
]
