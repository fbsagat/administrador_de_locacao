import os, sys, string, secrets
from cryptography.fernet import Fernet
from num2words import num2words
from django.core.exceptions import ValidationError
from Alugue_seu_imovel import settings


# 001: -----------------------------------------------


def valor_format(valor):
    """ O valor deve ser inteiro e vir em format string e será convertido para valor financeiro em Reais(R$) onde as
    duas últimas casas sempre representarão centavos Ex: de 134567899 para 1.345.678,99"""
    virgola = str(',') if int(valor) > 99 else str('0,')
    y = '' if int(valor) < 100 else f'{int(valor[:-2]):_.2f}'.replace('_', '.')
    z = f'{y[:-3]}{virgola}{str(valor)[-2:]}'
    return f'R${z}'


# 002: -----------------------------------------------


def cpf_format(cpf):
    if cpf is None:
        return None
    else:
        return f'{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:11]}'


# 003: -----------------------------------------------


def cel_format(cel):
    return f'({cel[:2]}) {cel[2:7]}-{cel[7:11]}'


# 004: -----------------------------------------------


def cep_format(cep):
    return f'{cep[:5]}-{cep[5:8]}'


# 005: -----------------------------------------------


def tratar_imagem(arquivo_obj):
    size = arquivo_obj.file.size
    limite_mb = settings.TAMANHO_DAS_IMAGENS_Mb
    if size > limite_mb * 1024 * 1024:
        raise ValidationError(f"O arquivo não deve ser maior que {str(limite_mb)}Mb")


# 006: -----------------------------------------------


def valor_por_extenso(valor):
    if type(valor) == str:
        reais = valor[:-2]
        centavos = valor[-2:]
        centavos_format = f' e {num2words(int(centavos), lang="pt_BR")} centavos'
        return f'{num2words(int(reais), lang="pt_BR").capitalize()} reais{centavos_format if int(centavos) > 1 else ""}'
    else:
        return None


# 007: -----------------------------------------------


def validar_cpf(cpf):
    if settings.DEBUG is False:
        # Remove todos os caracteres não numéricos
        cpf = ''.join(filter(str.isdigit, cpf))

        # Verifica se o CPF tem 11 dígitos
        if len(cpf) != 11:
            return False

        # Calcula o primeiro dígito verificador
        soma = 0
        for i in range(9):
            soma += int(cpf[i]) * (10 - i)
        resto = soma % 11
        if resto < 2:
            digito1 = 0
        else:
            digito1 = 11 - resto

        # Calcula o segundo dígito verificador
        soma = 0
        for i in range(10):
            soma += int(cpf[i]) * (11 - i)
        resto = soma % 11
        if resto < 2:
            digito2 = 0
        else:
            digito2 = 11 - resto

        # Verifica se os dígitos verificadores estão corretos
        if int(cpf[9]) == digito1 and int(cpf[10]) == digito2:
            return True
        else:
            return False
    else:
        return False


# 007: -----------------------------------------------


def tamanho_max_mb(value):
    size = sys.getsizeof(value)
    tama_max_mb = settings.TAMANHO_DO_MODELO_Mb * 1024 * 1024
    if size > tama_max_mb:
        raise ValidationError(f'O tamanho do arquivo está maior do que o permitido, o limite é de {tamanho_max_mb}Mb')


# 008: -----------------------------------------------


def gerar_uuid_8(caracteres=8, dividir=True):
    metade = int(caracteres / 2)
    if caracteres % 2 == 0:
        codigo_ = ''.join(
            secrets.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in
            range(caracteres))
        if dividir:
            return f'{codigo_[:metade]}-{codigo_[metade:]}'
        else:
            return codigo_
    else:
        raise Exception("A quantidade de caracteres deve ser par")


# 009: -----------------------------------------------


def gerar_uuid_10(caracteres=10, dividir=False):
    metade = int(caracteres / 2)
    if caracteres % 2 == 0:
        codigo_ = ''.join(
            secrets.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in
            range(caracteres))
        if dividir:
            return f'{codigo_[:metade]}-{codigo_[metade:]}'
        else:
            return codigo_
    else:
        raise Exception("A quantidade de caracteres deve ser par")


# 010: -----------------------------------------------


def gerar_uuid_20(caracteres=20, dividir=False):
    metade = int(caracteres / 2)
    if caracteres % 2 == 0:
        codigo_ = ''.join(
            secrets.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in
            range(caracteres))
        if dividir:
            return f'{codigo_[:metade]}-{codigo_[metade:]}'
        else:
            return codigo_
    else:
        raise Exception("A quantidade de caracteres deve ser par")


# 011: -----------------------------------------------


def _crypt(message):
    site_code = str(settings.IMPORT_UM).encode()
    fernet = Fernet(site_code)
    enc_message = fernet.encrypt(message.encode())
    return enc_message


# 012: -----------------------------------------------


def _decrypt(enc_message):
    site_code = str(settings.IMPORT_UM).encode()
    fernet = Fernet(site_code)
    dec_message = fernet.decrypt(enc_message).decode()
    return dec_message


# 012: -----------------------------------------------


def gerar_uuid_6(caracteres=6, dividir=False):
    metade = int(caracteres / 2)
    if caracteres % 2 == 0:
        codigo_ = ''.join(
            secrets.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in
            range(caracteres))
        if dividir:
            return f'{codigo_[:metade]}-{codigo_[metade:]}'
        else:
            return codigo_
    else:
        raise Exception("A quantidade de caracteres deve ser par")


# 013: -----------------------------------------------


def gerar_uuid_64(caracteres=64, dividir=False):
    metade = int(caracteres / 2)
    if caracteres % 2 == 0:
        codigo_ = ''.join(
            secrets.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in
            range(caracteres))
        if dividir:
            return f'{codigo_[:metade]}-{codigo_[metade:]}'
        else:
            return codigo_
    else:
        raise Exception("A quantidade de caracteres deve ser par")


# 014: -----------------------------------------------


modelo_variaveis = {
        0: ['[!variavel: semana_extenso_hoje]', 'Dia da semana hoje escrito por extenso'],
        64: ['[!variavel: data_extenso_hoje]', 'Dia, mês e ano de hoje escritos por extenso'],
        1: ['[!variavel: data_hoje]', 'Data abreviada de hoje'],
        43: ['[!variavel: tipo_de_locacao]', 'Locação residencial ou locação comercial/industrial'],
        49: ['[!variavel: caucao]', 'Valor da caução/depósito a ser pago'],
        50: ['[!variavel: caucao_por_extenso]', 'Valor da caução/depósito a ser pago por extenso'],

        2: ['[!variavel: locador_nome_completo]', 'Nome completo do locador do imóvel deste contrato'],
        3: ['[!variavel: locador_nacionalidade]', 'Nacionalidade do locador do imóvel deste contrato'],
        4: ['[!variavel: locador_estado_civil]', 'Estado civil do locador do imóvel deste contrato'],
        5: ['[!variavel: locador_ocupacao]', 'Ocupação trabalhista do locador do imóvel deste contrato'],
        6: ['[!variavel: locador_rg]', 'Documento número de RG do locador do imóvel deste contrato'],
        7: ['[!variavel: locador_cpf]', 'Documento número de CPF do locador do imóvel deste contrato'],
        63: ['[!variavel: locador_telefone]', 'Número do telefone celular do locador do imóvel deste contrato'],
        8: ['[!variavel: locador_endereco_completo]', 'Endereço completo do locador do imóvel deste contrato'],
        47: ['[!variavel: locador_email]', 'Endereço de e-mail do locador do imóvel deste contrato'],
        32: ['[!variavel: locador_pagamento_1]', 'Informações de pagamento 1 do locador do imóvel deste contrato'],
        33: ['[!variavel: locador_pagamento_2]', 'Informações de pagamento 2 do locador do imóvel deste contrato'],

        9: ['[!variavel: imovel_rotulo]', 'Rótulo do imóvel deste contrato'],
        44: ['[!variavel: imovel_grupo]', 'Grupo no qual o imóvel deste contrato está inserido'],
        10: ['[!variavel: imovel_uc_energia]', 'Unidade consumidora de energia do imóvel deste contrato'],
        11: ['[!variavel: imovel_uc_sanemameto]', 'Unidade consumidora de saneamento do imóvel deste contrato'],
        12: ['[!variavel: imovel_cidade]', 'Cidade onde se localiza o imóvel deste contrato'],
        48: ['[!variavel: imovel_estado]', 'Estado onde se localiza o imóvel deste contrato'],
        62: ['[!variavel: imovel_bairro]', 'Bairro onde se localiza o imóvel deste contrato'],
        13: ['[!variavel: imovel_endereco_completo]', 'Endereço completo do imóvel deste contrato'],
        61: ['[!variavel: imovel_grupo_tipo]', 'Tipo de grupo no qual o imóvel deste contrato está inserido'],

        14: ['[!variavel: locatario_nome_completo]', 'Nome completo do locatário do imóvel deste contrato'],
        15: ['[!variavel: locatario_cpf]', 'Documento número de CPF do locatário do imóvel deste contrato'],
        16: ['[!variavel: locatario_rg]', 'Documento número de RG do locatário do imóvel deste contrato'],
        17: ['[!variavel: locatario_nacionalidade]', 'Nacionalidade do locatário do imóvel deste contrato'],
        18: ['[!variavel: locatario_estado_civil]', 'Estado civil do locatário do imóvel deste contrato'],
        19: ['[!variavel: locatario_ocupacao]', 'Ocupação trabalhista do locatário do imóvel deste contrato'],
        52: ['[!variavel: locatario_endereco_completo]', 'Endereço completo do locatário do imóvel deste contrato'],
        20: ['[!variavel: locatario_celular_1]', 'Número de celular 1 do locatário do imóvel deste contrato'],
        21: ['[!variavel: locatario_celular_2]', 'Número de celular 2 do locatário do imóvel deste contrato'],
        42: ['[!variavel: locatario_email]', 'Endereço de e-mail do locatário do imóvel deste contrato'],

        36: ['[!variavel: fiador_nome_completo]', 'Nome completo do fiador do imóvel deste contrato'],
        37: ['[!variavel: fiador_rg]', 'Documento número de RG do fiador do imóvel deste contrato'],
        38: ['[!variavel: fiador_cpf]', 'Documento número de CPF do fiador do imóvel deste contrato'],
        51: ['[!variavel: fiador_endereco_completo]', 'Endereço completo do fiador do imóvel deste contrato'],
        39: ['[!variavel: fiador_ocupacao]', 'Ocupação trabalhista do fiador do imóvel deste contrato'],
        40: ['[!variavel: fiador_nacionalidade]', 'Nacionalidade do fiador do imóvel deste contrato'],
        41: ['[!variavel: fiador_estado_civil]', 'Estado civil do fiador do imóvel deste contrato'],

        22: ['[!variavel: contrato_data_entrada]', 'Data de entrada do locatário no imóvel'],
        23: ['[!variavel: contrato_data_saida]', 'Data de saída do locatário no imóvel'],
        24: ['[!variavel: contrato_codigo]', 'Código do contrato'],
        25: ['[!variavel: contrato_periodo]', 'Período de validade, em meses, de validade do contrato'],
        26: ['[!variavel: contrato_periodo_por_extenso]',
             'Período de validade, em meses, de validade do contrato, por extenso'],
        27: ['[!variavel: contrato_parcela_valor]', 'Valor da mensalidade do aluguel'],
        28: ['[!variavel: contrato_parcela_valor_por_extenso]', 'Valor da mensalidade do aluguel, por extenso'],
        45: ['[!variavel: contrato_valor_total]', 'Valor total do contrato, todas as parcelas juntas'],
        46: ['[!variavel: contrato_valor_total_por_extenso]', 'Valor total do contrato, por extenso'],
        34: ['[!variavel: contrato_vencimento]', 'Dia de vencimento do pagamento da mensalidade do aluguel'],
        35: ['[!variavel: contrato_vencimento_por_extenso]',
             'Dia de vencimento do pagamento da mensalidade do aluguel, por extenso'],

        29: ['[!variavel: contrato_anterior-codigo]',
             'Código do contrato anterior deste locatário, neste imóvel'],
        30: ['[!variavel: contrato_anterior-data_entrada]',
             'Data de entrada do locatário do imóvel do contrato anterior'],
        31: ['[!variavel: contrato_anterior-data_saida]',
             'Data de saída do locatário do imóvel do contrato anterior'],
        53: ['[!variavel: contrato_anterior-parcela_valor]',
             'Valor da mensalidade do aluguel do contrato anterior'],
        54: ['[!variavel: contrato_anterior-parcela_valor_por_extenso]',
             'Valor da mensalidade do aluguel do contrato anterior, por extenso'],
        55: ['[!variavel: contrato_anterior_valor_total]',
             'Valor total do contrato anterior, todas as parcelas juntas'],
        56: ['[!variavel: contrato_anterior_valor_total_por_extenso]',
             'Valor total do contrato anterior, por extenso'],
        57: ['[!variavel: contrato_anterior_vencimento]',
             'Dia de vencimento do pagamento da mensalidade do aluguel do contrato anterior'],
        58: ['[!variavel: contrato_anterior_vencimento_por_extenso]',
             'Dia de vencimento do pagamento da mensalidade do aluguel do contrato anterior, por extenso'],
        59: ['[!variavel: contrato_anterior-periodo]',
             'Período de validade, em meses, de validade do contrato anterior'],
        60: ['[!variavel: contrato_anterior-periodo_por_extenso]',
             'Período de validade, em meses, de validade do contrato anterior, por extenso'],
    }

modelo_condicoes = {
        0: ['[!condicao: fiador_existe]', 'Mostrar trecho caso exista dados do fiador'],
        1: ['[!condicao: fiador_nao_existe]', 'Mostrar trecho caso não exista dados do fiador'],
        2: ['[!condicao: tipo_residencial]', 'Mostrar trecho caso o tipo de contrato é residencial'],
        3: ['[!condicao: tipo_nao_residencial]', 'Mostrar trecho caso o tipo de contrato é comercial/industrial'],
        4: ['[!condicao: imovel_grupo_Casa]', 'Mostrar trecho caso o imóvel pertença à um grupo do tipo Casa'],
        5: ['[!condicao: imovel_grupo_Apartamento]',
            'Mostrar trecho caso o imóvel pertença à um grupo do tipo Apartamento'],
        6: ['[!condicao: imovel_grupo_Kitnet]', 'Mostrar trecho caso o imóvel pertença à um grupo do tipo Kitnet'],
        7: ['[!condicao: imovel_grupo_Box/Loja]', 'Mostrar trecho caso o imóvel pertença à um grupo do tipo Box/Loja'],
        8: ['[!condicao: imovel_grupo_Escritório]',
            'Mostrar trecho caso o imóvel pertença à um grupo do tipo Escritório'],
        9: ['[!condicao: imovel_grupo_Depósito/Armazém]',
            'Mostrar trecho caso o imóvel pertença à um grupo do tipo Depósito/Armazém'],
        10: ['[!condicao: imovel_grupo_Galpão]', 'Mostrar trecho caso o imóvel pertença à um grupo do tipo Galpão'],
        11: ['[!condicao: contrato_anterior_existe]',
             'Mostrar trecho caso exista um contrato anterior à este com este locador neste imóvel'],
        12: ['[!condicao: contrato_anterior_nao_existe]',
             'Mostrar trecho caso não exista um contrato anterior à este com este locador neste imóvel'],
        13: ['[!condicao: imovel_uc_sanemameto_existe]',
             'Mostrar trecho caso exista uma Unidade Consumidora de saneamento registrada neste imóvel'],
        14: ['[!condicao: imovel_uc_energia_existe]',
             'Mostrar trecho caso exista uma Unidade Consumidora de energia elétrica registrada neste imóvel'],
    }
