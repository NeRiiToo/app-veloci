# Generated manually for initial schema

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('core', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Escala',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data_inicio', models.DateTimeField()),
                ('data_fim', models.DateTimeField()),
                ('valor_cobrado', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('valor_entregador', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('observacao', models.TextField(blank=True, default='')),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
                ('entregador', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='escalas', to='core.entregador')),
                ('empresa', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='escalas', to='core.empresa')),
                ('usuario_registro', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['data_inicio'],
            },
        ),
        migrations.AlterUniqueTogether(
            name='escala',
            unique_together={('entregador', 'data_inicio')},
        ),
        migrations.AddIndex(
            model_name='escala',
            index=models.Index(fields=['data_inicio', 'empresa'], name='operacao_escala_dt_emp_idx'),
        ),
    ]
