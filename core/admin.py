from django.contrib import admin
from .models import Usuario, Locatario, Imovei, Contrato, Pagamento, Gasto, Anotacoe, DevMensagen, ImovGrupo, Parcela, \
    Notificacao, ContratoDocConfig, ContratoModelo, Sugestao, UsuarioContratoModelo


@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    model = Usuario
    list_display = ('username', 'first_name', 'last_name', 'email', 'is_staff', 'is_active')
    list_filter = ("is_staff", "is_active", 'is_superuser',)
    search_fields = ('first_name', 'email',)
    fieldsets = (
        ('Informações', {"fields": (
            'username', 'first_name', 'last_name', 'telefone', 'RG', 'cript_cpf', 'locat_slots', 'email',
            'nacionalidade', 'estadocivil', 'ocupacao', 'endereco_completo', 'password')}),

        ("Configurações", {'fields': ('data_eventos_i', 'itens_eventos', 'qtd_eventos',
                                      'ordem_eventos', 'recibo_ultimo', 'recibo_preenchimento',
                                      'tabela_ultima_data_ger', 'tabela_meses_qtd', 'tabela_imov_qtd')}),

        ("Permissões", {"fields": ("is_staff", "is_active", "groups", "user_permissions")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "email", "password1", "password2", "is_staff",
                "is_active", "groups", "user_permissions"
            )}
         ),
    )
    ordering = ("first_name",)
    readonly_fields = ['cript_cpf']


@admin.register(Locatario)
class LocatarioAdmin(admin.ModelAdmin):
    list_display = (
        'nome', 'do_locador', 'RG', 'cript_cpf', 'ocupacao', 'endereco_completo', 'telefone1', 'telefone2', 'email',
        'docs',
        'nacionalidade', 'estadocivil', 'temporario', 'data_registro')
    search_fields = ('nome', 'temporario')
    readonly_fields = ['cript_cpf']


@admin.register(ImovGrupo)
class ImovGrupoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'do_usuario')
    search_fields = ('nome',)


@admin.register(Imovei)
class ImoveisAdmin(admin.ModelAdmin):
    list_display = ('nome', 'do_locador', 'grupo', 'contrato_atual', 'com_locatario', 'data_registro')
    search_fields = ('nome', 'grupo')


@admin.register(Contrato)
class ContratosAdmin(admin.ModelAdmin):
    list_display = ('do_locador', 'do_locatario', 'do_imovel', 'data_entrada', 'duracao', 'valor_mensal',
                    'data_registro')
    list_filter = ('em_posse', 'rescindido',)


@admin.register(ContratoDocConfig)
class ContratoDocConfigsAdmin(admin.ModelAdmin):
    list_display = ('do_contrato', 'do_modelo',)


@admin.register(ContratoModelo)
class ContratoModeloAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'autor', 'data_criacao',)


@admin.register(UsuarioContratoModelo)
class UsuarioContratoModeloAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'contrato_modelo', 'data_criacao',)
    readonly_fields = ['data_criacao']


@admin.register(Pagamento)
class PagamentosAdmin(admin.ModelAdmin):
    list_display = ('ao_locador', 'ao_contrato', 'do_locatario', 'valor_pago', 'data_pagamento',
                    'data_de_recibo', 'data_criacao')
    list_filter = ('forma',)


@admin.register(Parcela)
class ParcelasAdmin(admin.ModelAdmin):
    list_display = ('do_contrato', 'codigo', 'data_pagm_ref')


@admin.register(Gasto)
class GastoAdmin(admin.ModelAdmin):
    list_display = ('do_locador', 'do_imovel', 'valor', 'data', 'comprovante', 'data_criacao')


@admin.register(Anotacoe)
class AnotacoeAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'do_usuario', 'data_registro', 'tarefa', 'da_notificacao')
    search_fields = ('titulo',)


@admin.register(DevMensagen)
class MensagemDevAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'do_usuario', 'data_registro', 'imagem')
    list_filter = ('tipo_msg',)
    search_fields = ('titulo',)


@admin.register(Sugestao)
class MensagemDevAdmin(admin.ModelAdmin):
    list_display = ('do_usuario', 'data_registro', 'imagem', 'implementada', 'aprovada')
    list_filter = ('implementada', 'aprovada')
    search_fields = ('corpo',)


@admin.register(Notificacao)
class NotificacoesAdmin(admin.ModelAdmin):
    list_display = (
        'texto', 'content_object', 'do_usuario', 'autor_classe', 'objeto_id', 'assunto', 'data_registro', 'lida',
        'data_lida')
    readonly_fields = ['content_object', 'texto']
    list_filter = ('autor_classe', 'apagada_oculta')
