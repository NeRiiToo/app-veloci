from django.urls import path

from operacao import views

urlpatterns = [
    path('api/diarias', views.api_diarias, name='api_diarias'),
    path('api/diaria', views.api_criar_diaria, name='api_criar_diaria'),
    path('api/diaria/editar', views.api_editar_diaria, name='api_editar_diaria'),
    path('api/diaria/remover', views.api_remover_diaria, name='api_remover_diaria'),
    path('api/diaria/replicar', views.api_replicar_escala, name='api_replicar_escala'),
    path('api/exportar', views.api_exportar, name='api_exportar'),
    path('api/logs', views.api_logs, name='api_logs'),
]
