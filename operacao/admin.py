from django.contrib import admin
from .models import Escala


@admin.register(Escala)
class EscalaAdmin(admin.ModelAdmin):
    list_display = ('entregador', 'empresa', 'data_inicio', 'data_fim', 'valor_cobrado', 'valor_entregador', 'usuario_registro')
    list_filter = ('empresa', 'data_inicio')
    search_fields = ('entregador__nome', 'empresa__nome')
    ordering = ('-data_inicio',)
    date_hierarchy = 'data_inicio'
