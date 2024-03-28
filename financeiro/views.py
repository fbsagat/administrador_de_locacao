import stripe

from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib.messages.views import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import get_object_or_404
from Alugue_seu_imovel import settings
from financeiro.models import PacoteConfig, PagamentoInvoice
from django.shortcuts import redirect, reverse, render
from django.conf import settings
from django.http import HttpResponse


@login_required
def painel_loja(request):
    configs = PacoteConfig.objects.latest("data_registro")
    context = {'SITE_NAME': settings.SITE_NAME, 'loja_info': configs.loja_info()}
    return render(request, 'painel_loja.html', context)


# @login_required
# def pagamentos_enviar_webhook(request, pacote_index, forma):
#     print('aqui')
#     # Pegar a última configuração de pagamentos do site
#     configs = PacoteConfig.objects.latest("data_registro")
#     # Criar um objeto de invoice de pagamentos
#     invoice = PagamentoInvoice.objects.create(do_usuario=request.user, do_pacote=pacote_index)
#     # Receber o valor
#     valor = 0
#     if forma == 'brl':
#         valor = configs.loja_info()[int(pacote_index)]['valor_pct_brl']
#     elif forma == 'btc':
#         valor = configs.loja_info()[int(pacote_index)]['valor_pct_btc']
#
#     url = "https://webhook.site/01cb81d7-3d9b-4ec1-9249-826a7b74526d"
#
#     payload = {
#         "amount": valor,
#         "currency": "BRL",
#         "description": "Após a confirmação desta transação, seu pacote será automaticamente creditado em sua conta",
#         "customer_name": f"{invoice.do_usuario.username}",
#         "customer_email": f"{invoice.do_usuario.email}",
#         "order_id": f"{invoice.pk}",
#         "callback_url": "https://1417-177-86-30-4.ngrok.io/webhooks/",
#         "success_url": "http://127.0.0.1:8000/painel_loja/",
#         "auto_settle": False,
#         "split_to_btc_bps": 1,
#         "ttl": 20
#     }
#     headers = {
#         "accept": "application/json",
#         "Content-Type": "application/json",
#         "Authorization": "34c46f55-bbe5-484a-b6a8-b25e8a7834e4"
#     }
#
#     response = requests.post(url, json=payload, headers=headers)
#
#     if response.status_code == 200:
#         print("Webhook enviado com sucesso!")
#         print(response.text)
#
#     return redirect(reverse('core:Painel Loja'))
#
#
# @csrf_exempt
# @require_POST
# @non_atomic_requests
# def pagamentos_receber_webhook(request):
#     if request.method == 'POST':
#         print("Webhook chegou!")
#         print(request.POST)
#         return HttpResponse("Webhook chegou!")


@require_POST
@csrf_exempt
def create_checkout_session(request, pacote_index, forma):
    usuario = request.user
    configs = PacoteConfig.objects.latest("data_registro")
    if request.method == 'POST':
        if forma == 'brl':
            # Função para pagamentos em brl (stripe)
            stripe.api_key = settings.STRIPE_SECRET_KEY
            try:
                invoice = PagamentoInvoice.objects.create(do_usuario=usuario, do_pacote=pacote_index)
                success_url = request.build_absolute_uri(reverse('financeiro:Compra Sucesso', args=[invoice.pk]))
                cancel_url = request.build_absolute_uri(reverse('financeiro:Compra Cancelada'))
                checkout_session = stripe.checkout.Session.create(
                    line_items=[
                        {
                            'price': f'{configs.loja_info()[pacote_index]["pacote_stripe_preco"]}',
                            'quantity': 1,
                        },
                    ],
                    mode='payment',
                    success_url=success_url,
                    cancel_url=cancel_url,
                )
                checkout_id = checkout_session['id']
                invoice.checkout_id = checkout_id
                invoice.save(update_fields=['checkout_id', ])
            except Exception as e:
                return str(e)
            return redirect(checkout_session.url, code=303)

        elif forma == 'btc':
            # Função para pagamentos em btc (meu próprio node lightning + btcpay server? espero!)
            pass
    return redirect(reverse('core:Painel Loja'))


@csrf_exempt
def stripe_webhook(request):
    stripe.api_key = settings.STRIPE_SECRET_KEY
    endpoint_secret = settings.STRIPE_ENDPOINT_SECRET
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return HttpResponse(status=400)

        # Handle the checkout.session.completed event
    if event['type'] == 'checkout.session.completed':
        # Retrieve the session. If you require line items in the response, you may include them by expanding line_items.
        session = stripe.checkout.Session.retrieve(
            event['data']['object']['id'],
            expand=['line_items'],
        )
        try:
            invoice = PagamentoInvoice.objects.get(checkout_id=session['id'])
            if session.payment_status == 'paid':
                invoice.pago = True
                invoice.save(update_fields=['pago', ])
        except:
            return HttpResponse(status=400)
    # Passed signature verification
    return HttpResponse(status=200)


@login_required
def compra_sucesso(request, pk):
    invoice = get_object_or_404(PagamentoInvoice, pk=pk)
    if invoice.do_usuario == request.user and invoice.pago is True and invoice.verificar_se_e_recente(30):
        messages.success(request, f"Pagamento realizado com sucesso, seus tickets já foram creditados em sua conta")
    return redirect(reverse('core:Painel Loja'))


@login_required
def compra_cancelada(request):
    messages.error(request, f"Pagamento cancelado")
    return redirect(reverse('core:Painel Loja'))


def historico_de_compras(request):
    usuario = request.user
    invoices = PagamentoInvoice.objects.filter(do_usuario=usuario)

    parametro_page = request.GET.get('page', '1')
    parametro_limite = request.GET.get('limit', '25')
    contrato_pagination = Paginator(invoices, parametro_limite)

    try:
        page = contrato_pagination.page(parametro_page)
    except (EmptyPage, PageNotAnInteger):
        page = contrato_pagination.page(1)

    context = {'SITE_NAME': settings.SITE_NAME, 'page_obj': page}
    return render(request, 'painel_historico_compras.html', context)
