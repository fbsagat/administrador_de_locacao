from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    """
    Create a superuser if none exist
    Example:
        manage.py createsuperuser_if_none_exists --user=admin --password=changeme
    """

    def add_arguments(self, parser):
        parser.add_argument("--user", required=True)
        parser.add_argument("--password", required=True)
        parser.add_argument("--email", default="www.fabioaugusto@hotmail.com")

    def handle(self, *args, **options):
        User = get_user_model()
        if User.objects.exists():
            return

        username = options["user"]
        password = options["password"]
        email = options["email"]

        first = 'Fábio'
        last = 'Augusto Macedo dos Santos'
        RG = '4853497'
        cript_cpf = b'gAAAAABlW2OE6p5S8j_Xoe7IiEWpSOGzWQr6SA2LRpSo4QDKku_DqOO3JDSm3mkK18FJWdW6Qlgv_eYWoyVdtiT_bZHOLRHf_A=='
        telefone = '91985707819'
        tickets = 100
        estadocivil = 0
        ocupacao = 'Programador - Hashtag Treinamentos'
        endereco_completo = 'Rodovia Augusto Montenegro, 6955'
        dados_pagamento1 = 'Pix, chave: 91985707819 (Fábio A M Santos)'

        User.objects.create_superuser(username=username, password=password, email=email, first_name=first,
                                      last_name=last, RG=RG, cript_cpf=cript_cpf, telefone=telefone, tickets=tickets,
                                      estadocivil=estadocivil, ocupacao=ocupacao, endereco_completo=endereco_completo,
                                      dados_pagamento1=dados_pagamento1)

        self.stdout.write(f'Local user "{username}" was created')
