import datetime
from datetime import timedelta
from dateutil.relativedelta import relativedelta

import requests
from Alugue_seu_imovel import settings
from django.db import models
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from hashlib import sha256

pacotes_nomes = ['Pacote Pequeno', 'Pacote Médio', 'Pacote Grande', 'Pacote Gigante']


class PacoteConfig(models.Model):
    ticket_valor_base_brl = models.FloatField(null=False, help_text='Apenas números pares')
    pacote_qtd_inicial = models.IntegerField(null=False, help_text='Primeiro pacote inicia com quantos tickets?')
    pacote_qtd_multiplicador = models.IntegerField(null=False, help_text='Multiplicador de tickets por pacote')
    desconto_pacote_multiplicador = models.IntegerField(null=False,
                                                        help_text='Percentual / fator multiplicador de desconto por '
                                                                  'pacote')
    desconto_add_bitcoin = models.IntegerField(null=False,
                                               help_text='Percentual / fator multiplicador de desconto por pacote com'
                                                         ' pg em btc')
    data_registro = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Pacotes configs'

    def __str__(self):
        return f'Configs de: {self.data_registro} / Valor base: R${self.ticket_valor_base_brl}'

    def loja_info(self):
        """ Esta função deve retornar um dicionário com os cards da loja
        Cada item deve conter uma lista com as seguintes informações e na mesma ordem:
        Nome do card(nome), percentual de desconto para o card(desconto_porcent), quantidade de tickets(ticket_qtd),
         valor do pacote(btc e brl)(valor_pct_brl, valor_pct_btc), valor por ticket no pacote(btc e brl)
         (valor_por_ticket_brl, valor_por_ticket_btc) e desconto percentual por unidade(btc e brl)(desconto_p_un_brl,
         desconto_p_un_btc).
        """

        valor_ticket = self.ticket_valor_base_brl
        pacote_qtd_inicial = self.pacote_qtd_inicial
        pacote_qtd_mult = self.pacote_qtd_multiplicador
        desconto_multiplicador = self.desconto_pacote_multiplicador
        desconto_add_cripto = self.desconto_add_bitcoin

        # Pegar valor em satoshis
        url = 'https://api.bitpreco.com/btc-brl/ticker'
        request = requests.get(url)
        j_son = request.json()
        btc_brl = j_son['last']

        cards = []
        for n, pacote in enumerate(pacotes_nomes):
            ticket_qtd = pacote_qtd_inicial + (n * pacote_qtd_mult)
            desconto_porcent = desconto_multiplicador * n
            valor_por_ticket_brl = round(valor_ticket - (valor_ticket * desconto_porcent / 100), ndigits=2)
            valor_pacote_brl = valor_por_ticket_brl * ticket_qtd
            valor_por_ticket_btc = round(valor_ticket - (valor_ticket * (desconto_porcent + desconto_add_cripto) / 100),
                                         ndigits=2)
            valor_pacote_btc = valor_por_ticket_btc * ticket_qtd
            valor_pacote_em_satoshis = round(valor_pacote_btc / (btc_brl / 100000000))
            desconto_p_un_btc = desconto_porcent + desconto_add_cripto

            pacote = {
                'nome': pacote,
                'ticket_qtd': ticket_qtd,
                'desconto_porcent': desconto_porcent,
                'valor_pct_brl': f'{valor_pacote_brl:.2f}',
                'valor_pct_btc': f'{round(valor_pacote_btc, 2):.2f}',
                'valor_por_ticket_brl': f'{round(valor_por_ticket_brl, 2):.2f}',
                'valor_por_ticket_btc': f'{round(valor_por_ticket_btc, 2):.2f}',
                'desconto_p_un_brl': desconto_porcent,
                'desconto_p_un_btc': desconto_p_un_btc,
                'valor_pacote_em_satoshis': valor_pacote_em_satoshis,
                'pacote_stripe_preco': settings.pacotes_stripe_precos[n],
            }
            cards.append(pacote)
        return cards


class PagamentoInvoice(models.Model):
    do_usuario = models.ForeignKey('core.Usuario', null=False, blank=False, on_delete=models.DO_NOTHING)
    do_config = models.ForeignKey('PacoteConfig', null=True, on_delete=models.DO_NOTHING)
    do_pacote = models.IntegerField(null=True, blank=True)
    btc = models.BooleanField(default=False, help_text='Marque se o pagamento foi em bitcoin')
    pago = models.BooleanField(default=False)
    checkout_id = models.CharField(max_length=100, null=True)
    data_registro = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Invoices'
        ordering = ['-data_registro']

    def __str__(self):
        return f'{self.do_usuario}/Pacote:{self.do_pacote}/{self.data_registro}{" - PG" if self.pago else " - Ñ PG"}'

    def verificar_se_e_recente(self, minutos):
        if self.data_registro <= datetime.datetime.now() + relativedelta(minutes=minutos):
            return True

    def pacote(self):
        return self.do_config.loja_info()[self.do_pacote]


@receiver(pre_save, sender=PagamentoInvoice)
def pagamento_invoice_pre_save(sender, instance, **kwargs):
    if instance.pk is None:  # if criado
        instance.do_config = PacoteConfig.objects.latest("data_registro")


@receiver(post_save, sender=PagamentoInvoice)
def pagamento_invoice_post_save(sender, instance, created, **kwargs):
    if not created and instance.pago:
        tickets_quantidade = instance.do_config.loja_info()[instance.do_pacote]["ticket_qtd"]
        instance.do_usuario.tickets += tickets_quantidade
        instance.do_usuario.save(update_fields=['tickets', ])
