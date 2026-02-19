from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import PerfilUsuario


class Command(BaseCommand):
    help = 'Cria um usuario admin padrao se nenhum existir'

    def handle(self, *args, **kwargs):
        if not User.objects.filter(is_superuser=True).exists():
            user = User.objects.create_superuser(
                username='admin',
                password='admin123',
                email='',
            )
            PerfilUsuario.objects.create(user=user, e_supervisor=False)
            self.stdout.write(self.style.SUCCESS(
                'Admin padrao criado: usuario=admin, senha=admin123 — TROQUE A SENHA!'
            ))
        else:
            self.stdout.write('Admin ja existe, nenhuma acao necessaria.')
