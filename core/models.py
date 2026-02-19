from django.db import models
from django.contrib.auth.models import User


class Empresa(models.Model):
    nome = models.CharField(max_length=200, unique=True)
    veiculo = models.CharField(max_length=100)
    tipo_valor = models.CharField(
        max_length=10,
        choices=[('unico', 'Valor Único'), ('hora', 'Valor por Hora')],
        default='unico',
    )
    minimo_garantido = models.CharField(
        max_length=1,
        choices=[('S', 'Sim'), ('N', 'Não')],
        default='N',
    )
    taxa_total_cobrada = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    taxa_total_entregador = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    taxa_cobrada_fds = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    taxa_entregador_fds = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    dias_diferentes = models.CharField(max_length=50, blank=True, default='')
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ['nome']

    def __str__(self):
        return self.nome


class Entregador(models.Model):
    nome = models.CharField(max_length=200)
    cpf = models.CharField(max_length=14, unique=True)
    ativo = models.BooleanField(default=True)
    data_cadastro = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['nome']

    def __str__(self):
        return self.nome


class PerfilUsuario(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    e_supervisor = models.BooleanField(default=True)
    empresas_vinculadas = models.ManyToManyField(Empresa, blank=True)

    def __str__(self):
        return f'{self.user.username} ({"Supervisor" if self.e_supervisor else "ADM"})'

    @property
    def permissao(self):
        if self.user.is_superuser or not self.e_supervisor:
            return 'ADM'
        return 'supervisor'


class LogSistema(models.Model):
    NIVEL_CHOICES = [
        ('INFO', 'Info'),
        ('ERROR', 'Erro'),
        ('WARNING', 'Aviso'),
    ]

    timestamp = models.DateTimeField(auto_now_add=True)
    nivel = models.CharField(max_length=10, choices=NIVEL_CHOICES, default='INFO')
    acao = models.CharField(max_length=200)
    usuario = models.CharField(max_length=150)
    detalhes = models.TextField(blank=True, default='')
    empresa = models.CharField(max_length=200, blank=True, default='')
    ip = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['usuario']),
            models.Index(fields=['empresa']),
            models.Index(fields=['nivel']),
        ]

    def __str__(self):
        return f'{self.timestamp:%Y-%m-%d %H:%M:%S} - {self.nivel} - {self.acao}'


def registrar_log(acao, usuario, detalhes='', empresa='', nivel='INFO', request=None):
    ip = None
    if request:
        ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR'))
        if ip and ',' in ip:
            ip = ip.split(',')[0].strip()
    LogSistema.objects.create(
        nivel=nivel,
        acao=acao,
        usuario=usuario,
        detalhes=detalhes,
        empresa=empresa,
        ip=ip,
    )
