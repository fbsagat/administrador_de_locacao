import json, os
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from Alugue_seu_imovel import settings

from faker import Faker
from random import randrange, choice

from core.models import ImovGrupo, Locatario, Imovei, Contrato, Usuario, estados

locales = 'pt_BR'
fake = Faker(locales)
nomes_populares = ['Silva', 'Rodrigues', 'Santos', 'Oliveira', 'Souza', 'Moraes', 'Carvalho', 'Dias']
nacionalidades = ['australiano', 'baremita', 'boliviano', 'americano', 'chinês', 'russo', 'argentino']


def porcentagem_de_chance(percentual):
    zero_a_cem = randrange(0, 100)
    return True if zero_a_cem <= percentual else False


def usuarios_ficticios():
    while True:
        username = fake.user_name()
        existentes = Usuario.objects.filter(username=username).values_list('username', flat=True)
        if username not in existentes:
            break
    password = 'Fb452651'
    first_name = fake.first_name()
    last_name = f'{fake.last_name()} {choice(nomes_populares)}'
    while True:
        email = f'{randrange(1, 999)}{fake.ascii_email()}'
        existentes = Usuario.objects.filter(email=email).values_list('email', flat=True)
        if email not in existentes:
            break
    telefone = fake.msisdn()[-11::]
    rg = randrange(1000000, 9999999)
    cpf = randrange(10000000000, 99999999999)
    nacionalidade = 'brasileiro' if porcentagem_de_chance(90) else choice(nacionalidades)
    estadocivil = randrange(0, 4)
    ocupacao = f'Frase sem nexo aleatória: {fake.catch_phrase()} kkkk q engraçado.'
    endereco_completo = fake.address()
    dados_pagamento1 = f'Pix, chave: {randrange(99999999, 999999999)} ({first_name} {last_name})'
    dados_pagamento2 = (f'Transferência: CC: {randrange(99999, 999999)} '
                        f'AG: ({randrange(999, 9999)}) ({first_name} {last_name})')

    return {'username': username, 'password': password, 'first_name': first_name, 'last_name': last_name,
            'email': email, 'telefone': telefone, 'RG': rg, 'CPF': cpf, 'nacionalidade': nacionalidade,
            'estadocivil': estadocivil, 'ocupacao': ocupacao, 'endereco_completo': endereco_completo,
            'dados_pagamento1': dados_pagamento1, 'dados_pagamento2': dados_pagamento2}


def locatarios_ficticios():
    nome = f'{fake.name()} {choice(nomes_populares)}'
    rg = randrange(1000000, 9999999)
    cpf = randrange(10000000000, 99999999999)
    ocupacao = f'Frase sem nexo aleatória: {fake.catch_phrase()} kkkk q engraçado.'
    endereco_completo = fake.address()
    telefone1 = f'{91}98{randrange(1000000, 9999999)}'
    telefone2 = fake.msisdn()[-11::]
    email = f'{randrange(1, 999)}{fake.email()}'
    nacionalidade = 'brasileiro' if porcentagem_de_chance(90) else choice(nacionalidades)
    estadocivil = randrange(0, 4)
    return {'nome': nome, 'RG': rg, 'CPF': cpf, 'ocupacao': ocupacao, 'telefone1': telefone1,
            'telefone2': telefone2, 'email': email, 'nacionalidade': nacionalidade, 'estadocivil': estadocivil,
            'endereco_completo': endereco_completo}


def imov_grupo_fict():
    lista = ['Res.', 'Edf.', 'Conj.', 'Rua', 'Avenida', 'Bairro']
    siglas = choice(lista)
    nome = f'{siglas} {fake.bairro()}'
    tipo = randrange(0, 6)
    return {'nome': nome, 'tipo': tipo}


def imoveis_ficticios(usuario):
    names = Imovei.objects.filter(do_locador=usuario).values_list('nome', flat=True)
    while True:
        nome = fake.neighborhood()
        if nome not in names:
            break
    cep = randrange(10000000, 99999999)
    endereco = fake.street_name()
    numero = fake.building_number()
    complemento = fake.neighborhood()
    bairro = fake.bairro()
    cidade = fake.city()
    estado = estados[randrange(0, 27)][0]
    uc_energia = randrange(100000000, 999999999)
    uc_agua = randrange(100000000, 999999999)
    grupos_disponiveis = ImovGrupo.objects.filter(do_usuario=usuario)
    if grupos_disponiveis:
        grupo = choice(grupos_disponiveis) if porcentagem_de_chance(80) else None
    else:
        grupo = None
    data_registro = fake.date_time_between_dates(datetime.now() + timedelta(days=-410),
                                                 datetime.now() + timedelta(days=-390))
    return {'nome': nome, 'cep': cep, 'numero': numero, 'complemento': complemento, 'bairro': bairro, 'cidade': cidade,
            'estado': estado, 'endereco': endereco, 'uc_energia': uc_energia, 'uc_agua': uc_agua, 'grupo': grupo,
            'data_registro': data_registro}


def contratos_ficticios(request, locador):
    """Prioriza os imoveis_disponiveis_do_usuario, caso não haja algum, pega todos_imoveis e tenta criar um contrato
     em um período disponível para o mesmo"""
    todos_locatarios = Locatario.objects.filter(do_locador=locador)
    do_locatario = choice(todos_locatarios)
    contratos_ativos = Contrato.objects.ativos_hoje().filter(do_locador=locador)
    imoveis_ativos = []
    for contrato in contratos_ativos:
        imoveis_ativos.append(contrato.do_imovel.pk)

    imoveis_disponiveis_do_usuario = Imovei.objects.filter(do_locador=locador).exclude(pk__in=imoveis_ativos)
    imoveis_ocupados_do_usuario = (
        Imovei.objects.filter(do_locador=locador).exclude(pk__in=imoveis_disponiveis_do_usuario.values_list('pk')))

    # 80% de chance de pegar um imóvel disponível(sem contrato ativo), 20% de um ocupado(com contrato ativo), caso não
    # haja ocupado, pegar aleatoriamente de todos mesmo (que são os da lista de disponíveis).
    # O gerador vai tratar de colocar o contrato em um período disponível para o imóvel(código validador mais abaixo).
    do_imovel = choice(imoveis_disponiveis_do_usuario) if porcentagem_de_chance(90) else choice(
        imoveis_ocupados_do_usuario) if imoveis_ocupados_do_usuario else choice(imoveis_disponiveis_do_usuario)

    count = 0
    while True:
        dias = count + randrange(90, 365 + (count * 2))
        passado = fake.date_between(datetime.now().date() - timedelta(days=dias * randrange(2, 5)),
                                    datetime.now().date() - timedelta(days=dias))

        dias = count + randrange(10, 30 + (count * 2))
        presente = fake.date_between(datetime.now().date() - timedelta(days=dias * 2),
                                     datetime.now().date() - timedelta(days=dias))

        dias = count + randrange(30, 90 + (count * 2))
        futuro = fake.date_between(datetime.now().date() + timedelta(days=dias),
                                   datetime.now().date() + timedelta(days=dias * 2))

        entrada_novo = presente if porcentagem_de_chance(75) else choice([passado, futuro])
        # print(passado.strftime("%d/%m/%Y"), presente.strftime("%d/%m/%Y"), futuro.strftime("%d/%m/%Y"))
        # print('escolhido:', entrada_novo.strftime("%d/%m/%Y"))
        # print('')

        duracao = randrange(3, 18) - count
        if duracao <= 0:
            duracao = 1
        saida_novo = entrada_novo + relativedelta(months=duracao)
        contratos_deste_imovel = Contrato.objects.filter(do_imovel=do_imovel.pk)
        permitido = True
        for contrato in contratos_deste_imovel:
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
        if permitido is True:
            data_entrada = entrada_novo
            break
        else:
            count += 1
    centavos = '00' if porcentagem_de_chance(70) else randrange(10, 95, step=5)
    reais = [randrange(500, 1200, step=150), randrange(700, 3400, step=180), randrange(750, 3450, step=130),
             randrange(3400, 12000, step=1500), randrange(520, 32460, step=100)]
    valor_mensal = f'{choice(reais)}{centavos}'
    dia_vencimento = randrange(1, 28)
    em_posse = True if porcentagem_de_chance(85) else False

    return {'do_locatario': do_locatario, 'do_imovel': do_imovel, 'data_entrada': data_entrada,
            'duracao': duracao, 'valor_mensal': valor_mensal, 'dia_vencimento': dia_vencimento, 'em_posse': em_posse}


def pagamentos_ficticios(usuario):
    x = Contrato.objects.filter(do_locador=usuario)
    contratos = []
    for contrato in x:
        if contrato.quitado() is False:
            contratos.append(contrato)
    if len(contratos) > 0:
        contrato_escolhido = choice(contratos)
        ao_contrato = contrato_escolhido
        valor_mensal = int(contrato_escolhido.valor_mensal)
        chance_aleatoria = randrange(valor_mensal // 3, valor_mensal)
        valor_sorteado = valor_mensal if porcentagem_de_chance(75) else chance_aleatoria
        valor_pago = str(valor_sorteado if valor_sorteado < int(contrato_escolhido.falta_pg()) else int(
            contrato_escolhido.falta_pg()))
        data_pagamento = fake.date_between(contrato_escolhido.data_entrada, contrato_escolhido.data_saida())
        pix_vista = randrange(0, 1)
        todas = randrange(0, 4)
        forma = pix_vista if porcentagem_de_chance(65) else todas
    else:
        return None
    return {'ao_contrato': ao_contrato, 'valor_pago': valor_pago, 'data_pagamento': data_pagamento, 'forma': forma}


def gastos_ficticios():
    imoveis = Imovei.objects.all()
    do_imovel = choice(imoveis)
    valor = randrange(5000, 28000)
    data = fake.date_between(do_imovel.data_registro.date(), datetime.today())
    observacoes = f'Frase sem nexo aleatória: {fake.paragraph(nb_sentences=randrange(1, 5))} kkkk q engraçado.'
    return {'do_imovel': do_imovel, 'valor': valor, 'data': data, 'observacoes': observacoes}


def anotacoes_ficticias():
    titulo = f'Titulo fictício sem nexo total: {fake.paragraph(nb_sentences=1)}'
    data_registro = fake.date_between(datetime.today() + timedelta(days=-80), datetime.today())
    texto = f'Frase sem nexo aleatória: {fake.paragraph(nb_sentences=randrange(6, 7))} kkkk q engraçado.'
    tarefa = True if porcentagem_de_chance(70) else False
    feito = False
    if tarefa:
        feito = True if porcentagem_de_chance(60) else False
    return {'titulo': titulo, 'data_registro': data_registro, 'texto': texto, 'tarefa': tarefa, 'feito': feito}


def sugestoes_ficticias():
    usuarios = Usuario.objects.all()
    corpo = f'Frase sem nexo aleatória: {fake.paragraph(nb_sentences=randrange(6, 7))} kkkk q engraçado.'
    alguns_usuarios = []
    count = 0
    valor = randrange(0, len(usuarios))
    while True:
        alguns_usuarios.append(choice(usuarios)) if porcentagem_de_chance(75) else None
        if count == valor:
            break
        count += 1
    likes = alguns_usuarios
    aprovada = True if porcentagem_de_chance(75) else False
    implementada = False
    if aprovada:
        implementada = True if porcentagem_de_chance(45) else False
    dias = randrange(1, 100)
    data_implementada = fake.date_between(datetime.now().date() + timedelta(days=-dias * 2),
                                          datetime.now().date() + timedelta(days=-dias))
    return {'corpo': corpo, 'likes': likes, 'aprovada': aprovada, 'implementada': implementada,
            'data_implementada': data_implementada}


def modelos_contratos_ficticios(usuario):
    titulo = fake.paragraph(nb_sentences=1)
    # PS: \/ o aplicativo ckeditor costuma modificar este campo, mesmo que o usuário, no site, não modifique nada na
    # edição. (causa um fork no modelo, porém isto só acontece com os fictícios)
    try:
        home = os.path.join(settings.BASE_DIR, 'core').replace('\\', '/')
        with open(fr"{home}/fixtures/dados_iniciais.json", 'r') as dados:
            arquivo = json.load(dados)
            corpo = arquivo[0 if porcentagem_de_chance(50) else 1]['fields']['corpo']
        dados.close()
    except:
        corpo = str(f'<p>{fake.paragraph(nb_sentences=randrange(10, 15))}<p>')

    todos_usuarios = Usuario.objects.all()
    alguns_usuarios = []
    comunidade = porcentagem_de_chance(75)
    count = 0
    valor = randrange(0, len(todos_usuarios))
    alguns_usuarios.append(usuario)
    if comunidade:
        if porcentagem_de_chance(50):
            while True:
                alguns_usuarios.append(choice(todos_usuarios)) if porcentagem_de_chance(50) else None
                if count == valor:
                    break
                count += 1
    usuarios = alguns_usuarios
    descricao = fake.paragraph(nb_sentences=randrange(2, 3))

    return {'titulo': titulo, 'corpo': corpo, 'usuarios': usuarios, 'descricao': descricao,
            'comunidade': comunidade}
