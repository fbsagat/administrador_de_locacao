from math import ceil
from datetime import datetime, timedelta
import io, os, base64, json
from textwrap import wrap

from xhtml2pdf import pisa
from celery import shared_task
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.pagesizes import A4

from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from Alugue_seu_imovel import settings
from core.models import TempCodigo, TempLink, Usuario
from core.funcoes_proprias import cpf_format, modelo_variaveis, modelo_condicoes


# Gabarito e exemplo \/:
# bind: função pode receber o self, max_retry: número máximo de tentativas, default_retry_delay: tempo entre as
# tentativas, autoretry_for: tentar se houver erros contidos na tupla, retry_backoff: retentar progressivamente
# (ex: True: 1seg, 2seg, 4seg, 8seg..., ex2: 5: 5seg, 10seg, 20seg...)
#
# @shared_task(bind=True)
# def print_cavalo(self, arg1, arg2):
#     print('cavalo', 'arg: ', arg1, arg2)
#     return f'{self} / done'
#
#
# @shared_task(name='Função de Teste', bind=True, max_retry=5, default_retry_delay=20,
#              autoretry_for=(TypeError, Exception), )
# def test_func(self, tempo):
#     for i in range(tempo):
#         print('A', i)
#         time.sleep(1)
#     return f"{self} / done"
#
#
# @shared_task(name='Função de Teste 2', bind=True, max_retry=5, default_retry_delay=20,
#              autoretry_for=(TypeError, Exception), )
# def test_func2(self, tempo):
#     for i in range(tempo):
#         print('B', i)
#         time.sleep(1)
#     return f"{self} / done"


# -=-=-=-=-=-=-=-= GERADORES DE PDF -=-=-=-=-=-=-=-=


@shared_task
def gerar_recibos_pdf(dados1):
    def gerar_um_recibo(pdf, pag_lar, pag_centro, recibo_n, pos_y, dados, parcelas):
        """ Ex:
            infos = {'cod_recibo': ['465736', '463416', '125736', '465676', '465756', '465346', '474936'],
                 'cod_contrato': '4536-3382', 'nome_locador': 'FÁBIO AUGUSTO MACEDO DOS SANTOS', 'rg_locd': '5667789',
                 'cpf_locd': '005.234.342-10', 'nome_locatario': 'SANDRA DINORIA CRAVO COUTINHO', 'rg_loct': '8798122',
                 'cpf_loct': '235.632.142-04', 'valor_e_extenso': 'R$800,00 (OITOCENTOS REAIS)',
                 'mes_e_ano': ['NOVEMBRO', '2022', 'DEZEMBRO', '2022', 'JANEIRO', '2023', 'FEVEREIRO', '2023', 'MARÇO', '2023',
                               'ABRIL', '2023', 'MAIO', '2023'],
                 'endereco': "Passagem Péricles Guedes, 391, Apto 102 Castanheira Belém/PA 66645_290", 'cidade': 'Belém',
                 'data': '________________, ____ de _________ de ________'}
        """

        rect_lar = pag_lar - (pag_lar * 10 / 100)
        rect_alt = pag_lar / 2.5

        rect_pos_x = pag_centro[0] - (rect_lar / 2)
        rect_pos_y = pos_y - (rect_alt / 2)

        pdf.rect(rect_pos_x, rect_pos_y, rect_lar, rect_alt)

        pdf.setFont('Helvetica-Bold', 12)
        pdf.drawString(rect_pos_x + 5, rect_pos_y + rect_alt - 15, 'RECIBO DE PAGAMENTO DE ALUGUEL')

        pdf.setFont('Helvetica-Bold', 8)
        pdf.drawString(rect_pos_x + rect_lar - 213, rect_pos_y + rect_alt - 10,
                       f'Cód. recibo: {dados["cod_recibo"][recibo_n - 1]} / Cód. contrato: {dados["cod_contrato"]}')

        pdf.drawString(rect_pos_x + 12, rect_pos_y + 3,
                       f'Cód. recibo: {dados["cod_recibo"][recibo_n - 1]} / Cód. contrato: '
                       f'{dados["cod_contrato"]}')

        pdf.setFont('Helvetica-Bold', 10)

        texto_estilo = ParagraphStyle('My Para style', fontName='Times-Roman', fontSize=12, borderPadding=(20, 20, 20),
                                      leading=14, alignment=1)

        texto = Paragraph(
            f'Eu, <b>{dados["nome_locador"]}</b>, inscrito(a) no {dados["rg_locd"]} CPF sob o nº '
            f'{cpf_format(dados["cpf_locd"])}, recebi de <b>{dados["nome_locatario"]}</b>,'
            f' inscrito(a) no {dados["rg_loct"]} CPF sob o n° {cpf_format(dados["cpf_loct"])},'
            f' a importância de <b>{dados["valor_e_extenso"]}</b>, referente ao pagamento do aluguel'
            f' do mês de <b>{dados["mes_e_ano"][2 * (recibo_n - 1)]} DE '
            f'{dados["mes_e_ano"][(2 * (recibo_n - 1)) + 1]}</b> (Parcela {recibo_n} de um total '
            f'de {parcelas}), de um imóvel localizado no endereço: {dados["endereco"]}, declarando '
            f'portanto, plena, total e irrevogável quitação do mês referido a partir de então.'
            f' <BR/><BR/><i> Para maior clareza firmo o presente em:'
            f'<BR/>{dados["data_preenchimento"][recibo_n - 1]}</i><BR/><BR/><BR/>'
            f'___________________________________________________________________________________'
            f'<BR/>{dados["nome_locador"]}',
            texto_estilo)
        texto.wrapOn(pdf, 525, 110)
        texto.drawOn(pdf, rect_pos_x + 5, rect_pos_y + 15)

    def gerar_uma_pagina_recibo(pdf, parcelas, pag_centro, pag_alt, pag_lar, pag_n, dados):
        recibos_qtd = pag_n * 3
        if recibos_qtd < parcelas + 1:
            gerar_um_recibo(pdf=pdf, pag_centro=pag_centro, pag_lar=pag_lar, recibo_n=recibos_qtd,
                            pos_y=pag_centro[1] - pag_alt * 33 / 100, dados=dados, parcelas=parcelas)
        if recibos_qtd < parcelas + 2:
            gerar_um_recibo(pdf=pdf, pag_centro=pag_centro, pag_lar=pag_lar, recibo_n=recibos_qtd - 1,
                            pos_y=pag_centro[1],
                            dados=dados, parcelas=parcelas)
        if recibos_qtd < parcelas + 3:
            gerar_um_recibo(pdf=pdf, pag_centro=pag_centro, pag_lar=pag_lar, recibo_n=recibos_qtd - 2,
                            pos_y=pag_centro[1] + pag_alt * 33 / 100, dados=dados, parcelas=parcelas)

    def gerar_recibos_pdf_inicial(dados):
        buffer = io.BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=A4)
        pdf.setAuthor(f'{dados["nome_locador"]}')
        pdf.setTitle(f'Recibos do contrato {dados["cod_contrato"]}')
        pdf.setCreator(settings.SITE_URL)
        pdf.setSubject(f'Locatário: {dados["nome_locatario"]}')

        pag_lar = A4[0]
        pag_alt = A4[1]
        pag_centro = (pag_lar / 2, pag_alt / 2)

        parcelas = int(len(dados['mes_e_ano']) / 2)
        paginas = int((len(dados['mes_e_ano']) / 2) / 3) if (len(dados['mes_e_ano']) / 2) / 3 % 2 == 1 else ceil(
            (len(dados['mes_e_ano']) / 2) / 3)

        # Tratando itens opcionais \/
        dados['rg_locd'] = '' if dados['rg_locd'] == 'None' else f' RG sob o nº {dados["rg_locd"]} e '
        dados['rg_loct'] = f' RG sob o nº {dados["rg_loct"]} e ' if dados['rg_loct'] != '' else ''
        if dados['data_preenchimento']:
            pass
        else:
            for x in range(0, (len(dados['mes_e_ano']))):
                dados['data_preenchimento'].append(f"{dados['cidade']} ,____________, ____ de ____________ de ________")

        for pagina in range(paginas):
            page_num = pdf.getPageNumber()
            gerar_uma_pagina_recibo(pag_n=page_num, pag_alt=pag_alt, pag_centro=pag_centro, pag_lar=pag_lar,
                                    parcelas=parcelas, dados=dados, pdf=pdf)
            pdf.showPage()

        pdf.save()
        buffer.seek(0)
        pdf_bytes = buffer.read()
        base64_encoded_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
        pdf_data = {
            'file_name': 'recibos_pdf.pdf',
            'file_content': base64_encoded_pdf
        }
        json_data = json.dumps(pdf_data)
        return json_data

    return gerar_recibos_pdf_inicial(dados=dados1)


@shared_task
def gerar_tabela_pdf(dados1):
    def criar_uma_pagina_tabela(fazer, pag_n, a4h, dados, pdf, celula_altura):
        # Atributos da página
        pag_lar = a4h[0]
        pag_alt = a4h[1]
        pag_centro_h = pag_lar / 2
        pag_centro_v = pag_alt / 2

        # Customize a tabela
        celula_quantidade_h = len(dados['datas']) + 1
        celula_quantidade_v = fazer
        margem_vertical = 40
        margem_horizontal = 0
        celula_altura_max = 92

        if pag_n == 1:
            tam_calc = round((pag_alt / celula_quantidade_v) - (margem_vertical / celula_quantidade_v)) - 1
            celula_altura = tam_calc if tam_calc <= celula_altura_max else celula_altura_max
        celula_largura = round(pag_lar / celula_quantidade_h) - 1
        media_alt_larg = round(((celula_altura + celula_largura) / 2))

        # print('celula_altura: ', celula_altura, 'celula_largura: ', celula_largura, 'media: ', media_alt_larg)

        # Encaixe de texto
        text_wrap_imo = espacamento_h = espac_h_sinal = espacamento_v = text_tam_imo = text_wrap_parc = text_tam_parc = \
            leading = char_space = 0

        # Verticalmente (leading)
        max_linhas = int(0)
        if celula_altura <= 61:  # Célula pequena
            leading = 9
            espacamento_v = 12
            max_linhas = 4
        elif celula_altura <= 76:  # Célula média
            leading = 8.5
            espacamento_v = 12
            max_linhas = 5
        elif celula_altura <= 92:  # Célula grande
            leading = 12
            espacamento_v = 13
            max_linhas = 6

        # Horizontalmente  (wrap)
        if celula_largura <= 104:  # Célula pequena
            text_wrap_imo = 18
            text_wrap_parc = 30
            espacamento_h = 2
            espac_h_sinal = 9
            char_space = 0
        elif celula_largura <= 135:  # Célula média
            text_wrap_imo = 19
            text_wrap_parc = 32
            espacamento_h = 2
            espac_h_sinal = 9
            char_space = 0.1
        elif celula_largura <= 167:  # Célula grande
            text_wrap_imo = 19
            text_wrap_parc = 33
            espacamento_h = 3
            espac_h_sinal = 12
            char_space = 0.2

        # media (tam)
        if media_alt_larg <= 82:  # Célula pequena
            text_tam_imo = 11
            text_tam_parc = 8
        elif media_alt_larg <= 106:  # Célula média
            text_tam_imo = 11
            text_tam_parc = 8
        elif media_alt_larg <= 130:  # Célula grande
            text_tam_imo = 12
            text_tam_parc = 11

        # Calculos para organização
        tam_tt_h = celula_largura * celula_quantidade_h
        tam_tt_v = celula_altura * celula_quantidade_v
        centro_h = tam_tt_h / 2
        centro_v = tam_tt_v / 2
        inicia_em_h = (tam_tt_h / pag_lar) + (pag_centro_h - centro_h) - 1
        # \/ Para centralizar verticalmente: (tam_tt_v / pag_alt) + (pag_centro_v - centro_v)
        inicia_em_v = margem_vertical

        # Cria na horizontal
        for horizontal, y in enumerate(range(0, tam_tt_h, celula_largura)):
            # Cria na vertical
            for vertical, x in enumerate(range(0, tam_tt_v, celula_altura)):
                if vertical % 2 == 0:
                    pdf.setFillColorRGB(0, 0, 0, 0.05)
                else:
                    pdf.setFillColorRGB(0, 0, 0, 0)

                # Criar tabela
                pdf.rect(inicia_em_h + y, pag_alt - inicia_em_v - celula_altura - x, celula_largura, celula_altura,
                         fill=1)
                pdf.rect(inicia_em_h + y, pag_alt - inicia_em_v - celula_altura - x, celula_largura, celula_altura,
                         fill=1)
                pdf.setFillColorRGB(0, 0, 0, 1)

                # Criar textos
                if vertical == 0 and horizontal == 0:
                    pdf.saveState()
                    pdf.setLineWidth(0.01)
                    pdf.setStrokeColor(colors.gray)
                    pdf.rect(inicia_em_h + y, pag_alt - inicia_em_v - celula_altura - x + celula_altura + 20,
                             tam_tt_h, 15, stroke=1)
                    pdf.restoreState()

                    textobject = pdf.beginText(inicia_em_h + y + 2,
                                               pag_alt - inicia_em_v - celula_altura - x + celula_altura + 24)
                    textobject.setFillColor(colors.dimgray)
                    textobject.setFont('Helvetica-Bold', 11)
                    textobject.textLine(
                        f'Tabela de agenda dos imóveis de '
                        f'{dados["usuario_username"]} (De {dados["datas"][0]} Até {dados["datas"][-1]})')
                    pdf.drawText(textobject)

                    textobject = pdf.beginText(inicia_em_h + y,
                                               pag_alt - inicia_em_v - celula_altura - x + celula_altura + 2)
                    textobject.setFillColor(colors.black)
                    textobject.setFont('Times-Roman', 14)
                    textobject.textLine('Imóveis Ativos')
                    pdf.drawText(textobject)

                if vertical == 0 and horizontal > 0:
                    textobject = pdf.beginText(inicia_em_h + y,
                                               pag_alt - inicia_em_v - celula_altura - x + celula_altura + 2)
                    textobject.setFillColor(colors.black)
                    textobject.setFont('Times-Roman', 14)
                    textobject.textLine(f'{dados["datas"][horizontal - 1]}')
                    pdf.drawText(textobject)

                if vertical >= 0 and horizontal == 0:
                    mytext = f'{dados["imoveis"]["nomes"][((pag_n - 1) * dados["imov_qtd"]) + vertical]}'
                    wraped_text = "\n".join(wrap(mytext, text_wrap_imo))
                    textobject = pdf.beginText(inicia_em_h + y + espacamento_h,
                                               pag_alt - inicia_em_v - x - espacamento_v)
                    textobject.setFillColor(colors.black)
                    textobject.setFont('Times-Roman', text_tam_imo)
                    for n, line in enumerate(wraped_text.splitlines(False)):
                        if n < max_linhas:
                            textobject.textLine(line.rstrip())
                    pdf.drawText(textobject)

                if vertical >= 0 and horizontal > 0:
                    parc = str(
                        dados['imoveis']['parcelas'][((pag_n - 1) * dados["imov_qtd"]) + vertical][horizontal - 1])
                    wraped_text = "\n".join(wrap(parc, text_wrap_parc))
                    textobject = pdf.beginText(inicia_em_h + y + espacamento_h,
                                               pag_alt - inicia_em_v - x - (espacamento_v - 3))

                    se_ativo = dados['imoveis']['parcelas_ativas'][((pag_n - 1) * dados["imov_qtd"]) + vertical][
                        horizontal - 1]
                    if se_ativo is True:
                        textobject.setFillColor(colors.black)
                    else:
                        textobject.setFillColor(colors.gray)

                    textobject.setFont('Times-Roman', text_tam_parc)
                    textobject.setCharSpace(char_space)
                    textobject.setLeading(leading)
                    for line in wraped_text.splitlines(False):
                        textobject.textLine(line.rstrip())
                    pdf.drawText(textobject)

                    sinal = str(
                        dados['imoveis']['sinais'][((pag_n - 1) * dados["imov_qtd"]) + vertical][horizontal - 1])
                    textobject = pdf.beginText(inicia_em_h + y + celula_largura - espacamento_h - espac_h_sinal,
                                               pag_alt - inicia_em_v - x - text_tam_parc)
                    textobject.setFillColor(colors.blue)

                    if sinal == 'Ok':
                        # Ok
                        textobject.setFillColor(HexColor(0x354c70))
                    elif sinal == 'Re':
                        # Falta recibo
                        textobject.setFillColor(HexColor(0xCEAD4D))
                    elif sinal == 'Ve':
                        # Venceu
                        textobject.setFillColor(HexColor(0x8D0000))

                    textobject.setFont('Times-Roman', text_tam_parc)
                    textobject.setCharSpace(char_space)
                    textobject.setLeading(leading)
                    textobject.textLine(sinal.rstrip())
                    pdf.drawText(textobject)

        return {'celula_altura': celula_altura}

    def gerar_tabela_pdf_inicial(dados):
        # Preparando o PDF:
        buffer = io.BytesIO()
        a4h = (297 * mm, 210 * mm)
        pdf = canvas.Canvas(buffer, pagesize=a4h)

        paginas = int((len(dados['imoveis']['nomes'])) / dados['imov_qtd']) if (len(dados['imoveis']['nomes'])) / dados[
            'imov_qtd'] % 2 == 1 else ceil((len(dados['imoveis']['nomes'])) / dados['imov_qtd'])
        ultima = len(dados['imoveis']['nomes']) - ((paginas - 1) * dados['imov_qtd'])
        fazer = dados['imov_qtd']

        infos = {'celula_altura': 100}
        for pagina in range(0, paginas):
            if pagina == paginas - 1:
                fazer = ultima
            pag_n = pdf.getPageNumber()
            infos = criar_uma_pagina_tabela(fazer=fazer, pag_n=pag_n, a4h=a4h, dados=dados, pdf=pdf,
                                            celula_altura=infos['celula_altura'])
            pdf.showPage()

        pdf.setCreator(settings.SITE_URL)
        pdf.setAuthor(f'{dados["usuario_nome_compl"]}')
        pdf.setTitle(f'Tabela de agenda dos imóveis de {dados["usuario_username"]}')
        pdf.setSubject(f'Tabela completa com a agenda dos imóveis ativos.')

        pdf.save()
        buffer.seek(0)
        pdf_bytes = buffer.read()
        base64_encoded_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
        pdf_data = {
            'file_name': 'tabela_pdf.pdf',
            'file_content': base64_encoded_pdf
        }
        json_data = json.dumps(pdf_data)
        return json_data

    return gerar_tabela_pdf_inicial(dados=dados1)


@shared_task
def gerar_contrato_pdf(dados, local, visualizar=False):
    # Gerar modelo em pdf e salvar em media/contrato_docs para ser carregado pela view'
    # Criar a pasta contrato_docs se não existe
    modelo_corpo = dados['modelo']['corpo']

    if visualizar:
        pasta = rf'{settings.MEDIA_ROOT}/contratos_modelos/'
        se_existe = os.path.exists(pasta)
        if not se_existe:
            os.makedirs(pasta)
    else:
        pasta = rf'{settings.MEDIA_ROOT}/contrato_docs/'
        se_existe = os.path.exists(pasta)
        if not se_existe:
            os.makedirs(pasta)

    if visualizar is False:
        # Capturar trechos de cada condição registrada em modelo_condicoes
        for i, j in modelo_condicoes.items():
            # Aqui colocaremos no objeto posições cada trecho do item atual de modelo_condicoes(caso haja, senão aviso)
            comando_inicio = j[0]
            comando_fim = f'{comando_inicio[:comando_inicio.find("]")]}_fim{comando_inicio[comando_inicio.find("]"):]}'
            indice = 0

            while indice < len(modelo_corpo):
                indice = modelo_corpo.find(j[0], indice)
                if indice == -1:
                    break
                pos_fim = modelo_corpo[indice:].find(comando_fim)
                trecho = modelo_corpo[indice:indice + pos_fim + len(comando_fim)]
                tem_comando_fim = True if comando_fim in trecho else False
                trecho_final = trecho[len(comando_inicio):-len(comando_fim)]

                # Funções das condições:
                # Economizar processamento, se necessário: Evitar essa busca de texto, e sim, enviar um parâmetro \/
                if comando_inicio == '[!condicao: fiador_existe]' and tem_comando_fim:
                    if '[ESTE DADO DO FIADOR NÃO FOI PREENCHIDO]' in dados['fiador_nome_completo']:
                        modelo_corpo = modelo_corpo.replace(trecho, '')
                    else:
                        modelo_corpo = modelo_corpo.replace(trecho, trecho_final)

                if comando_inicio == '[!condicao: fiador_nao_existe]' and tem_comando_fim:
                    if '[ESTE DADO DO FIADOR NÃO FOI PREENCHIDO]' in dados['fiador_nome_completo']:
                        modelo_corpo = modelo_corpo.replace(trecho, trecho_final)
                    else:
                        modelo_corpo = modelo_corpo.replace(trecho, '')

                if comando_inicio == '[!condicao: tipo_residencial]' and tem_comando_fim:
                    if dados['tipo_de_locacao'] == 'residencial':
                        modelo_corpo = modelo_corpo.replace(trecho, trecho_final)
                    else:
                        modelo_corpo = modelo_corpo.replace(trecho, '')

                if comando_inicio == '[!condicao: tipo_nao_residencial]' and tem_comando_fim:
                    if dados['tipo_de_locacao'] == 'não residencial':
                        modelo_corpo = modelo_corpo.replace(trecho, trecho_final)
                    else:
                        modelo_corpo = modelo_corpo.replace(trecho, '')

                if comando_inicio == '[!condicao: imovel_grupo_Casa]' and tem_comando_fim:
                    if dados['imovel_grupo_tipo'] == 'Casa':
                        modelo_corpo = modelo_corpo.replace(trecho, trecho_final)
                    else:
                        modelo_corpo = modelo_corpo.replace(trecho, '')

                if comando_inicio == '[!condicao: imovel_grupo_Apartamento]' and tem_comando_fim:
                    if dados['imovel_grupo_tipo'] == 'Apartamento':
                        modelo_corpo = modelo_corpo.replace(trecho, trecho_final)
                    else:
                        modelo_corpo = modelo_corpo.replace(trecho, '')

                if comando_inicio == '[!condicao: imovel_grupo_Kitnet]' and tem_comando_fim:
                    if dados['imovel_grupo_tipo'] == 'Kitnet':
                        modelo_corpo = modelo_corpo.replace(trecho, trecho_final)
                    else:
                        modelo_corpo = modelo_corpo.replace(trecho, '')

                if comando_inicio == '[!condicao: imovel_grupo_Box/Loja]' and tem_comando_fim:
                    if dados['imovel_grupo_tipo'] == 'Box/Loja':
                        modelo_corpo = modelo_corpo.replace(trecho, trecho_final)
                    else:
                        modelo_corpo = modelo_corpo.replace(trecho, '')

                if comando_inicio == '[!condicao: imovel_grupo_Escritório]' and tem_comando_fim:
                    if dados['imovel_grupo_tipo'] == 'Escritório':
                        modelo_corpo = modelo_corpo.replace(trecho, trecho_final)
                    else:
                        modelo_corpo = modelo_corpo.replace(trecho, '')

                if comando_inicio == '[!condicao: imovel_grupo_Depósito/Armazém]' and tem_comando_fim:
                    if dados['imovel_grupo_tipo'] == 'Depósito/Armazém':
                        modelo_corpo = modelo_corpo.replace(trecho, trecho_final)
                    else:
                        modelo_corpo = modelo_corpo.replace(trecho, '')

                if comando_inicio == '[!condicao: imovel_grupo_Galpão]' and tem_comando_fim:
                    if dados['imovel_grupo_tipo'] == 'Galpão':
                        modelo_corpo = modelo_corpo.replace(trecho, trecho_final)
                    else:
                        modelo_corpo = modelo_corpo.replace(trecho, '')

                if comando_inicio == '[!condicao: imovel_uc_sanemameto_existe]' and tem_comando_fim:
                    if '[ESTE DADO DO IMÓVEL NÃO FOI PREENCHIDO]' not in dados['imovel_uc_sanemameto']:
                        modelo_corpo = modelo_corpo.replace(trecho, trecho_final)
                    else:
                        modelo_corpo = modelo_corpo.replace(trecho, '')

                if comando_inicio == '[!condicao: imovel_uc_energia_existe]' and tem_comando_fim:
                    if '[ESTE DADO DO IMÓVEL NÃO FOI PREENCHIDO]' not in dados['imovel_uc_energia']:
                        modelo_corpo = modelo_corpo.replace(trecho, trecho_final)
                    else:
                        modelo_corpo = modelo_corpo.replace(trecho, '')

                if comando_inicio == '[!condicao: contrato_anterior_existe]' and tem_comando_fim:
                    if '[NÃO EXISTE CONTRATO ANTERIOR A ESTE]' in dados['contrato_anterior-codigo']:
                        modelo_corpo = modelo_corpo.replace(trecho, '')
                    else:
                        modelo_corpo = modelo_corpo.replace(trecho, trecho_final)

                if comando_inicio == '[!condicao: contrato_anterior_nao_existe]' and tem_comando_fim:
                    if '[NÃO EXISTE CONTRATO ANTERIOR A ESTE]' in dados['contrato_anterior-codigo']:
                        modelo_corpo = modelo_corpo.replace(trecho, trecho_final)
                    else:
                        modelo_corpo = modelo_corpo.replace(trecho, '')

                # Fim das funções das condições
                indice += 1

        # Aplicar Variaveis \/
        for i, j in modelo_variaveis.items():
            modelo_corpo = modelo_corpo.replace(j[0], dados[f"{j[0][j[0].find(': ') + 2:-1]}"])

    with open(fr"{settings.MEDIA_ROOT}/{local}", "wb") as f:
        pisa.CreatePDF(modelo_corpo, dest=f, )
    f.close()


# -=-=-=-=-=-=-=-= TEMP DELETIONS -=-=-=-=-=-=-=-=


@shared_task(bind=True)
def temp_activations_tokens_deletions(self):
    """Esta função tem por objetivo apagar todas as instâncias inválidas, ou seja, as que estão fora de validade,
    dos models de criação de links e códigos de validação. Esta função deverá ser executada periodicamente através do
    celery beat"""
    templink = TempLink.objects.filter(tempo_final__lte=datetime.now())
    tempcodigo = TempCodigo.objects.filter(tempo_final__lte=datetime.now())
    if templink:
        templink.delete()
    if tempcodigo:
        tempcodigo.delete()


@shared_task(bind=True)
def temp_inative_users_deletions(self):
    """Esta função tem por objetivo apagar todos os usuários inativos, ou seja, que não concluíram o cadastro e que
    iniciaram o cadastro a mais de seis horas a partir do momento em que esta função for executada. Esta função deverá
    ser executada periodicamente através do celery beat"""
    agora_menos_tempo = datetime.now() - timedelta(hours=6)
    usuarios_inativos = Usuario.objects.filter(is_active=False, date_joined__lte=agora_menos_tempo)
    if usuarios_inativos:
        usuarios_inativos.delete()


# -=-=-=-=-=-=-=-= EMAIL -=-=-=-=-=-=-=-=


@shared_task
def enviar_email_conf_de_email(absolute_uri, tempo_h, codigo, username, email):
    remetente = settings.EMAIL_HOST_USER
    destinatario = [email, ]
    context = {'username': username, 'codigo': codigo, 'link': absolute_uri,
               'site': settings.SITE_URL, 'tempo': tempo_h}
    html_content = render_to_string('registration/confirmacao_email_email.html', context=context)
    text_content = strip_tags(html_content)
    email_ = EmailMultiAlternatives('Confirmação de Email', text_content, remetente, destinatario)
    email_.attach_alternative(html_content, 'text/html')
    email_.send()
    # send_mail('Assunto', 'Esse é o email de teste!', remetente, destinatarios)


@shared_task
def enviar_email_exclusao_de_conta(absolute_uri, tempo_m, username, email):
    remetente = settings.EMAIL_HOST_USER
    destinatario = [email, ]
    context = {'username': username, 'link': absolute_uri,
               'site': settings.SITE_URL, 'tempo': tempo_m, 'site_name': settings.SITE_NAME}
    html_content = render_to_string('registration/exclusao_email.html', context=context)
    text_content = strip_tags(html_content)
    email_ = EmailMultiAlternatives('Exclusão de conta', text_content, remetente, destinatario)
    email_.attach_alternative(html_content, 'text/html')
    email_.send()
