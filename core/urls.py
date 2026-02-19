from django.urls import path

from core import views

urlpatterns = [
    # Auth
    path('login', views.login_view, name='login'),
    path('logout', views.logout_view, name='logout'),

    # Pages
    path('', views.index_view, name='index'),
    path('cadastros', views.cadastros_view, name='cadastros'),
    path('cadastro_usuario', views.cadastro_usuario_view, name='cadastro_usuario'),
    path('logs', views.logs_view, name='logs'),

    # API Usuarios
    path('api/cadastrar_usuario', views.api_cadastrar_usuario, name='api_cadastrar_usuario'),
    path('editar_usuario', views.api_editar_usuario, name='editar_usuario'),
    path('excluir_usuario', views.api_excluir_usuario, name='excluir_usuario'),

    # API Empresas
    path('api/empresas', views.api_empresas, name='api_empresas'),
    path('api/empresas/ativas', views.api_empresas_ativas, name='api_empresas_ativas'),
    path('api/empresas/filtro', views.api_empresas_filtro, name='api_empresas_filtro'),
    path('api/editar/empresa', views.api_editar_empresa, name='api_editar_empresa'),
    path('api/excluir/empresa', views.api_excluir_empresa, name='api_excluir_empresa'),

    # API Entregadores
    path('api/entregadores', views.api_entregadores, name='api_entregadores'),
    path('api/entregadores/ativos', views.api_entregadores_ativos, name='api_entregadores_ativos'),
    path('api/entregadores/importar', views.api_importar_entregadores, name='api_importar_entregadores'),
    path('api/editar/entregador', views.api_editar_entregador, name='api_editar_entregador'),
    path('api/excluir/entregador', views.api_excluir_entregador, name='api_excluir_entregador'),

    # API Cadastrar (empresa ou entregador)
    path('api/cadastrar', views.api_cadastrar, name='api_cadastrar'),
]
