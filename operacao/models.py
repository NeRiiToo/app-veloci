from django.db import models
from django.contrib.auth.models import User

from core.models import Empresa, Entregador


class Escala(models.Model):
    entregador = models.ForeignKey(Entregador, on_delete=models.PROTECT, related_name='escalas')
    empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, related_name='escalas')
    data_inicio = models.DateTimeField()
    data_fim = models.DateTimeField()
    valor_cobrado = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    valor_entregador = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    observacao = models.TextField(blank=True, default='')
    usuario_registro = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('entregador', 'data_inicio')
        indexes = [
            models.Index(fields=['data_inicio', 'empresa']),
        ]
        ordering = ['data_inicio']

    def __str__(self):
        return f'{self.entregador} - {self.empresa} ({self.data_inicio:%d/%m/%Y %H:%M})'
