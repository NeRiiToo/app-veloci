from django.contrib import admin
from .models import Empresa, Entregador, PerfilUsuario


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'veiculo', 'tipo_valor', 'minimo_garantido', 'taxa_total_entregador', 'ativo')
    list_filter = ('ativo', 'tipo_valor', 'minimo_garantido')
    search_fields = ('nome',)
    ordering = ('nome',)


@admin.register(Entregador)
class EntregadorAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cpf', 'ativo', 'data_cadastro')
    list_filter = ('ativo',)
    search_fields = ('nome', 'cpf')
    ordering = ('nome',)


@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ('user', 'e_supervisor')
    list_filter = ('e_supervisor',)
    filter_horizontal = ('empresas_vinculadas',)
