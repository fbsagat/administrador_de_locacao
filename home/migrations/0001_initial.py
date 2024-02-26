# Generated by Django 4.2.9 on 2024-02-25 05:05

import ckeditor.fields
import datetime
from django.conf import settings
import django.contrib.auth.models
import django.contrib.auth.validators
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import django_resized.forms
import home.funcoes_proprias
import home.models
import secrets


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='Usuario',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('RG', models.CharField(blank=True, help_text='Digite apenas números', max_length=9, null=True, validators=[django.core.validators.MinLengthValidator(7), django.core.validators.MaxLengthValidator(9), django.core.validators.RegexValidator(message='Digite apenas números.', regex='^[0-9]*$')])),
                ('cript_cpf', models.BinaryField(blank=True, null=True)),
                ('telefone', models.CharField(blank=True, help_text='Celular/Digite apenas números', max_length=11, validators=[django.core.validators.MinLengthValidator(11), django.core.validators.MaxLengthValidator(11), django.core.validators.RegexValidator(message='Digite apenas números.', regex='^[0-9]*$')])),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('nacionalidade', models.CharField(blank=True, default='Brasileiro(a)', max_length=40, null=True)),
                ('estadocivil', models.IntegerField(blank=True, choices=[(0, 'Solteiro(a)'), (1, 'Casado(a)'), (2, 'Separado(a)'), (3, 'Divorciado(a)'), (4, 'Viuvo(a)')], null=True, verbose_name='Estado Civil')),
                ('ocupacao', models.CharField(blank=True, max_length=85, null=True, verbose_name='Ocupação')),
                ('endereco_completo', models.CharField(blank=True, max_length=150, null=True, verbose_name='Endereço Completo')),
                ('dados_pagamento1', models.CharField(blank=True, help_text='Sua conta PIX ou dados bancários ou carteira crypto, etc...', max_length=90, null=True, verbose_name='Informações de pagamentos 1')),
                ('dados_pagamento2', models.CharField(blank=True, max_length=90, null=True, verbose_name='Informações de pagamentos 2')),
                ('uuid', models.CharField(default=home.funcoes_proprias.gerar_uuid_10, editable=False, max_length=10, unique=True)),
                ('tickets', models.IntegerField(default=10)),
                ('locat_slots', models.IntegerField(default=3)),
                ('vis_ger_ultim_order_by', models.CharField(blank=True, default='vencimento_atual', max_length=60, null=True)),
                ('data_eventos_i', models.DateField(blank=True, null=True)),
                ('itens_eventos', models.CharField(blank=True, default=['1', '2', '3', '4', '5', '6'], max_length=31, null=True)),
                ('qtd_eventos', models.IntegerField(blank=True, default=10, null=True)),
                ('ordem_eventos', models.IntegerField(default=1)),
                ('recibo_preenchimento', models.IntegerField(blank=True, null=True)),
                ('tabela_ultima_data_ger', models.IntegerField(blank=True, null=True)),
                ('tabela_meses_qtd', models.IntegerField(blank=True, null=True)),
                ('tabela_imov_qtd', models.IntegerField(blank=True, null=True)),
                ('tabela_mostrar_ativos', models.BooleanField(blank=True, null=True)),
                ('notif_qtd', models.IntegerField(default=20)),
                ('notif_qtd_hist', models.IntegerField(default=20)),
                ('itens_pag_visao_geral', models.IntegerField(default=27)),
                ('itens_pag_ativos', models.IntegerField(default=12)),
                ('itens_pag_pagamentos', models.IntegerField(default=56)),
                ('itens_pag_gastos', models.IntegerField(default=56)),
                ('itens_pag_imoveis', models.IntegerField(default=28)),
                ('itens_pag_locatarios', models.IntegerField(default=28)),
                ('itens_pag_contratos', models.IntegerField(default=28)),
                ('itens_pag_notas', models.IntegerField(default=28)),
                ('notif_recibo', models.DateTimeField(default=datetime.datetime.now, null=True)),
                ('notif_contrato_criado', models.DateTimeField(default=datetime.datetime.now, null=True)),
                ('notif_contrato_venc_1', models.DateTimeField(default=datetime.datetime.now, null=True)),
                ('notif_contrato_venc_2', models.DateTimeField(default=datetime.datetime.now, null=True)),
                ('notif_parc_venc_1', models.DateTimeField(default=datetime.datetime.now, null=True)),
                ('notif_parc_venc_2', models.DateTimeField(default=datetime.datetime.now, null=True)),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
                'abstract': False,
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Contrato',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data_entrada', models.DateField(verbose_name='Data de Entrada')),
                ('duracao', models.IntegerField(validators=[django.core.validators.MaxValueValidator(18), django.core.validators.MinValueValidator(1)], verbose_name='Duração do contrato(Meses)')),
                ('valor_mensal', models.CharField(help_text='Digite apenas números', max_length=9, validators=[django.core.validators.RegexValidator(message='Digite apenas números.', regex='^[0-9]*$'), django.core.validators.MinLengthValidator(3)], verbose_name='Valor Mensal (R$) ')),
                ('dia_vencimento', models.IntegerField(help_text='(1-28)', validators=[django.core.validators.MaxValueValidator(28), django.core.validators.MinValueValidator(1)], verbose_name='Dia do vencimento')),
                ('em_posse', models.BooleanField(default=False, help_text='Marque quando receber a sua via assinada e registrada em cartório')),
                ('rescindido', models.BooleanField(default=False, help_text='Marque caso haja rescisão do contrato')),
                ('codigo', models.CharField(default=home.models.gerar_codigo_contrato, editable=False, max_length=11)),
                ('data_de_rescisao', models.DateField(blank=True, null=True, verbose_name='Data da rescisão')),
                ('recibos_pdf', models.FileField(blank=True, upload_to='recibos_docs/%Y/%m/', verbose_name='Recibos')),
                ('data_registro', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['-data_entrada'],
            },
        ),
        migrations.CreateModel(
            name='ContratoModelo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titulo', models.CharField(help_text='Titulo', max_length=120, verbose_name='Titulo')),
                ('descricao', models.CharField(blank=True, help_text='Descrição', max_length=480, verbose_name='')),
                ('corpo', ckeditor.fields.RichTextField(blank=True, null=True, validators=[home.funcoes_proprias.tamanho_max_mb], verbose_name='')),
                ('data_criacao', models.DateTimeField(auto_now_add=True)),
                ('variaveis', models.JSONField(blank=True, null=True)),
                ('condicoes', models.JSONField(blank=True, null=True)),
                ('comunidade', models.BooleanField(default=False, verbose_name='Comunidade')),
                ('visualizar', models.FileField(blank=True, null=True, upload_to='')),
                ('autor', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='contratomod_autor_set', to=settings.AUTH_USER_MODEL)),
                ('excluidos', models.ManyToManyField(blank=True, related_name='contratos_modelos_excluidos', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'Modelos de contratos',
            },
        ),
        migrations.CreateModel(
            name='Imovei',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=25, verbose_name='Rótulo')),
                ('cep', models.CharField(max_length=8, validators=[django.core.validators.MinLengthValidator(8), django.core.validators.MaxLengthValidator(8), django.core.validators.RegexValidator(message='Digite apenas números.', regex='^[0-9]*$')], verbose_name='CEP')),
                ('endereco', models.CharField(max_length=150, verbose_name='Endereço')),
                ('numero', models.IntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(999999), django.core.validators.RegexValidator(message='Digite apenas números.', regex='^[0-9]*$')])),
                ('complemento', models.CharField(blank=True, max_length=80, null=True)),
                ('bairro', models.CharField(max_length=30)),
                ('cidade', models.CharField(max_length=30)),
                ('estado', models.CharField(choices=[('AC', 'Acre'), ('AL', 'Alagoas'), ('AP', 'Amapá'), ('AM', 'Amazonas'), ('BA', 'Bahia'), ('CE', 'Ceará'), ('DF', 'Distrito Federal'), ('ES', 'Espírito Santo'), ('GO', 'Goiás'), ('MA', 'Maranhão'), ('MT', 'Mato Grosso'), ('MS', 'Mato Grosso do Sul'), ('MG', 'Minas Gerais'), ('PA', 'Pará'), ('PB', 'Paraíba'), ('PR', 'Paraná'), ('PE', 'Pernambuco'), ('PI', 'Piauí'), ('RJ', 'Rio de Janeiro'), ('RN', 'Rio Grande do Norte'), ('RS', 'Rio Grande do Sul'), ('RO', 'Rondônia'), ('RR', 'Roraima'), ('SC', 'Santa Catarina'), ('SP', 'São Paulo'), ('SE', 'Sergipe'), ('TO', 'Tocantins')], max_length=2)),
                ('uc_energia', models.CharField(blank=True, max_length=15, null=True, validators=[django.core.validators.MinLengthValidator(4), django.core.validators.MaxLengthValidator(15)], verbose_name='Matrícula de Energia')),
                ('uc_agua', models.CharField(blank=True, max_length=15, null=True, validators=[django.core.validators.MinLengthValidator(4), django.core.validators.MaxLengthValidator(15)], verbose_name='Matrícula de Saneamento')),
                ('data_registro', models.DateTimeField(default=datetime.datetime.now)),
                ('do_locador', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'Imóveis',
                'ordering': ['-nome'],
            },
        ),
        migrations.CreateModel(
            name='Locatario',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=100, verbose_name='Nome Completo')),
                ('docs', django_resized.forms.ResizedImageField(blank=True, crop=None, force_format='JPEG', keep_meta=True, null=True, quality=75, scale=0.5, size=[1280, None], upload_to='locatarios_docs/%Y/%m/', validators=[home.funcoes_proprias.tratar_imagem, django.core.validators.FileExtensionValidator], verbose_name='Documentos')),
                ('RG', models.CharField(blank=True, help_text='Digite apenas números', max_length=9, validators=[django.core.validators.MinLengthValidator(7), django.core.validators.MaxLengthValidator(9), django.core.validators.RegexValidator(message='Digite apenas números.', regex='^[0-9]*$')])),
                ('cript_cpf', models.BinaryField(blank=True, null=True)),
                ('ocupacao', models.CharField(max_length=85, verbose_name='Ocupação')),
                ('endereco_completo', models.CharField(blank=True, max_length=150, null=True, verbose_name='Endereço Completo')),
                ('telefone1', models.CharField(help_text='Celular/Digite apenas números', max_length=11, validators=[django.core.validators.MinLengthValidator(11), django.core.validators.MaxLengthValidator(11), django.core.validators.RegexValidator(message='Digite apenas números.', regex='^[0-9]*$')], verbose_name='Telefone 1')),
                ('telefone2', models.CharField(blank=True, help_text='Celular/Digite apenas números', max_length=11, null=True, validators=[django.core.validators.MinLengthValidator(11), django.core.validators.MaxLengthValidator(11), django.core.validators.RegexValidator(message='Digite apenas números.', regex='^[0-9]*$')], verbose_name='Telefone 2')),
                ('email', models.EmailField(blank=True, max_length=45, null=True)),
                ('nacionalidade', models.CharField(default='Brasileiro(a)', max_length=40)),
                ('estadocivil', models.IntegerField(choices=[(0, 'Solteiro(a)'), (1, 'Casado(a)'), (2, 'Separado(a)'), (3, 'Divorciado(a)'), (4, 'Viuvo(a)')], verbose_name='Estado Civil')),
                ('data_registro', models.DateTimeField(auto_now_add=True)),
                ('temporario', models.BooleanField(null=True)),
            ],
            options={
                'verbose_name_plural': 'Locatários',
            },
        ),
        migrations.CreateModel(
            name='Notificacao',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('objeto_id', models.PositiveIntegerField()),
                ('assunto', models.PositiveIntegerField(null=True)),
                ('data_registro', models.DateTimeField(auto_now_add=True)),
                ('lida', models.BooleanField(default=False)),
                ('apagada_oculta', models.BooleanField(default=False)),
                ('data_lida', models.DateTimeField(blank=True, null=True)),
                ('autor_classe', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype')),
                ('do_usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'Notificações',
                'ordering': ['-data_registro'],
            },
        ),
        migrations.CreateModel(
            name='UsuarioContratoModelo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data_criacao', models.DateTimeField(auto_now_add=True)),
                ('contrato_modelo', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='usuario_contrato_modelo', to='home.contratomodelo')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='usuario_contrato_modelo', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'Modelos de contratos-Usuários',
            },
        ),
        migrations.CreateModel(
            name='TempLink',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tempo_final', models.DateTimeField()),
                ('link_uuid', models.CharField(default=secrets.token_urlsafe, editable=False, max_length=45)),
                ('tipo', models.PositiveIntegerField(default=1)),
                ('do_usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='TempCodigo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tempo_final', models.DateTimeField()),
                ('codigo', models.CharField(default=home.funcoes_proprias.gerar_uuid_6, editable=False, max_length=8)),
                ('do_usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Sugestao',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data_registro', models.DateTimeField(auto_now=True)),
                ('corpo', models.TextField(max_length=1500, verbose_name='')),
                ('imagem', django_resized.forms.ResizedImageField(blank=True, crop=None, force_format='JPEG', keep_meta=True, quality=75, scale=0.5, size=[1280, None], upload_to='sugestoes_docs/%Y/%m/', validators=[home.funcoes_proprias.tratar_imagem, django.core.validators.FileExtensionValidator], verbose_name='Imagem(opcional)')),
                ('implementada', models.BooleanField(default=False)),
                ('aprovada', models.BooleanField(default=False)),
                ('data_implementada', models.DateTimeField(blank=True, null=True)),
                ('da_notificacao', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='home.notificacao')),
                ('do_usuario', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('likes', models.ManyToManyField(blank=True, related_name='Likes', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'Sugestões',
            },
        ),
        migrations.CreateModel(
            name='Slot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('gratuito', models.BooleanField(default=False)),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
                ('tickets', models.PositiveIntegerField(default=0)),
                ('da_notificacao', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='home.notificacao')),
                ('do_usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'Slots',
                'ordering': ('pk',),
            },
        ),
        migrations.CreateModel(
            name='Parcela',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('codigo', models.CharField(default=home.funcoes_proprias.gerar_uuid_8, editable=False, max_length=7, unique_for_month=True)),
                ('data_pagm_ref', models.DateField(help_text='Data referente ao vencimento do pagamento desta parcela')),
                ('tt_pago', models.CharField(default=0, max_length=9)),
                ('recibo_entregue', models.BooleanField(default=False)),
                ('apagada', models.BooleanField(default=False)),
                ('do_contrato', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='home.contrato')),
                ('do_imovel', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='home.imovei')),
                ('do_locatario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='home.locatario')),
                ('do_usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Pagamento',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('valor_pago', models.CharField(max_length=9, validators=[django.core.validators.RegexValidator(message='Digite apenas números.', regex='^[0-9]*$')], verbose_name='Valor Pago (R$) ')),
                ('data_pagamento', models.DateTimeField(verbose_name='Data do Pagamento')),
                ('data_de_recibo', models.DateTimeField(blank=True, null=True, verbose_name='Data em que foi marcado recibo entregue')),
                ('forma', models.IntegerField(choices=[(0, 'PIX'), (1, 'Din. Espécie'), (2, 'Boleto Banc.'), (3, 'Tranfer. Banc.')], verbose_name='Forma de Pagamento')),
                ('data_criacao', models.DateTimeField(auto_now_add=True)),
                ('ao_contrato', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='home.contrato', verbose_name='Do Contrato')),
                ('ao_locador', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('do_locatario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='home.locatario')),
            ],
        ),
        migrations.AddField(
            model_name='locatario',
            name='da_notificacao',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='home.notificacao'),
        ),
        migrations.AddField(
            model_name='locatario',
            name='do_locador',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.CreateModel(
            name='ImovGrupo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=35, verbose_name='Criar Grupo')),
                ('tipo', models.IntegerField(blank=True, choices=[(0, 'Casa'), (1, 'Apartamento'), (2, 'Kitnet'), (3, 'Box/Loja'), (4, 'Escritório'), (5, 'Depósito/Armazém'), (6, 'Galpão')], null=True, verbose_name='Tipo de Imóvel')),
                ('do_usuario', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('imoveis', models.ManyToManyField(blank=True, to='home.imovei')),
            ],
            options={
                'verbose_name_plural': 'Grupos de imóveis',
                'ordering': ('nome',),
            },
        ),
        migrations.AddField(
            model_name='imovei',
            name='grupo',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='home.imovgrupo'),
        ),
        migrations.CreateModel(
            name='Gasto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('valor', models.CharField(max_length=9, validators=[django.core.validators.RegexValidator(message='Digite apenas números.', regex='^[0-9]*$')], verbose_name='Valor Gasto (R$) ')),
                ('data', models.DateTimeField()),
                ('observacoes', models.TextField(blank=True, max_length=500, verbose_name='Observações')),
                ('comprovante', django_resized.forms.ResizedImageField(blank=True, crop=None, force_format='JPEG', keep_meta=True, quality=75, scale=0.5, size=[1280, None], upload_to='gastos_comprovantes/%Y/%m/', validators=[home.funcoes_proprias.tratar_imagem, django.core.validators.FileExtensionValidator], verbose_name='Comporvante')),
                ('data_criacao', models.DateTimeField(auto_now_add=True)),
                ('do_imovel', models.ForeignKey(blank=True, help_text='Deixe em branco para registrar um gasto avulso', null=True, on_delete=django.db.models.deletion.CASCADE, to='home.imovei')),
                ('do_locador', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='DevMensagen',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data_registro', models.DateTimeField(auto_now=True)),
                ('titulo', models.CharField(max_length=100)),
                ('mensagem', models.TextField()),
                ('resposta', models.TextField(blank=True)),
                ('tipo_msg', models.IntegerField(choices=[(1, 'Elogio'), (2, 'Reclamação'), (3, 'Dúvida'), (4, 'Report de bug')])),
                ('imagem', django_resized.forms.ResizedImageField(blank=True, crop=None, force_format='JPEG', keep_meta=True, quality=75, scale=0.5, size=[1280, None], upload_to='mensagens_ao_dev/%Y/%m/', validators=[home.funcoes_proprias.tratar_imagem, django.core.validators.FileExtensionValidator])),
                ('da_notificacao', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='home.notificacao')),
                ('do_usuario', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'Mensagens ao Dev',
            },
        ),
        migrations.AddField(
            model_name='contratomodelo',
            name='usuarios',
            field=models.ManyToManyField(blank=True, related_name='contratos_modelos', through='home.UsuarioContratoModelo', to=settings.AUTH_USER_MODEL),
        ),
        migrations.CreateModel(
            name='ContratoDocConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo_de_locacao', models.IntegerField(blank=True, choices=[(None, '-----------'), (1, 'residencial'), (2, 'não residencial')], null=True, verbose_name='Tipo de Locação')),
                ('caucao', models.IntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(3), django.core.validators.RegexValidator(message='Digite apenas números.', regex='^[0-9]*$')])),
                ('fiador_nome', models.CharField(blank=True, max_length=100, null=True, verbose_name='Nome Completo')),
                ('fiador_RG', models.CharField(blank=True, help_text='Digite apenas números', max_length=9, null=True, validators=[django.core.validators.MinLengthValidator(7), django.core.validators.MaxLengthValidator(9), django.core.validators.RegexValidator(message='Digite apenas números.', regex='^[0-9]*$')], verbose_name='RG')),
                ('fiador_cript_cpf', models.BinaryField(blank=True, null=True)),
                ('fiador_ocupacao', models.CharField(blank=True, max_length=85, null=True, verbose_name='Ocupação')),
                ('fiador_endereco_completo', models.CharField(blank=True, max_length=150, null=True, verbose_name='Endereço Completo')),
                ('fiador_nacionalidade', models.CharField(blank=True, max_length=40, null=True, verbose_name='Nacionalidade')),
                ('fiador_estadocivil', models.IntegerField(blank=True, choices=[(0, 'Solteiro(a)'), (1, 'Casado(a)'), (2, 'Separado(a)'), (3, 'Divorciado(a)'), (4, 'Viuvo(a)')], null=True, verbose_name='Estado Civil')),
                ('do_contrato', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='home.contrato')),
                ('do_modelo', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='home.contratomodelo', verbose_name='Modelo de contrato')),
            ],
            options={
                'verbose_name_plural': 'Configs de contratos',
            },
        ),
        migrations.AddField(
            model_name='contrato',
            name='do_imovel',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='home.imovei', verbose_name='No imóvel'),
        ),
        migrations.AddField(
            model_name='contrato',
            name='do_locador',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='contrato',
            name='do_locatario',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='home.locatario', verbose_name='Locatário'),
        ),
        migrations.CreateModel(
            name='Anotacoe',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titulo', models.CharField(max_length=100, verbose_name='Título')),
                ('data_registro', models.DateTimeField(blank=True)),
                ('texto', models.TextField(blank=True, null=True)),
                ('tarefa', models.BooleanField(default=False, help_text='Marque para adicionar este registro na sua lista de tarefas.')),
                ('feito', models.BooleanField(default=False)),
                ('da_notificacao', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='home.notificacao')),
                ('do_usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'Anotações',
            },
        ),
        migrations.AddField(
            model_name='usuario',
            name='contrato_ultimo',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='usuario_contrato_set', to='home.contrato'),
        ),
        migrations.AddField(
            model_name='usuario',
            name='groups',
            field=models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups'),
        ),
        migrations.AddField(
            model_name='usuario',
            name='recibo_ultimo',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='usuario_recibo_set', to='home.contrato'),
        ),
        migrations.AddField(
            model_name='usuario',
            name='user_permissions',
            field=models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions'),
        ),
        migrations.AddConstraint(
            model_name='locatario',
            constraint=models.UniqueConstraint(fields=('cript_cpf', 'do_locador'), name='cpf_locatario_por_usuario'),
        ),
        migrations.AddConstraint(
            model_name='imovei',
            constraint=models.UniqueConstraint(fields=('nome', 'do_locador'), name='nome_imovel_por_usuario'),
        ),
    ]
