# Generated manually for initial schema

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Empresa',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=200, unique=True)),
                ('veiculo', models.CharField(max_length=100)),
                ('tipo_valor', models.CharField(choices=[('unico', 'Valor Único'), ('hora', 'Valor por Hora')], default='unico', max_length=10)),
                ('minimo_garantido', models.CharField(choices=[('S', 'Sim'), ('N', 'Não')], default='N', max_length=1)),
                ('taxa_total_cobrada', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('taxa_total_entregador', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('taxa_cobrada_fds', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('taxa_entregador_fds', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('dias_diferentes', models.CharField(blank=True, default='', max_length=50)),
                ('ativo', models.BooleanField(default=True)),
            ],
            options={
                'ordering': ['nome'],
            },
        ),
        migrations.CreateModel(
            name='Entregador',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=200)),
                ('cpf', models.CharField(max_length=14, unique=True)),
                ('ativo', models.BooleanField(default=True)),
                ('data_cadastro', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['nome'],
            },
        ),
        migrations.CreateModel(
            name='PerfilUsuario',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('e_supervisor', models.BooleanField(default=True)),
                ('empresas_vinculadas', models.ManyToManyField(blank=True, to='core.empresa')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='perfil', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
