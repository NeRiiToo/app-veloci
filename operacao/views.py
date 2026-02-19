import json
from datetime import datetime, timedelta

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST

from core.models import Empresa, Entregador, LogSistema, registrar_log
from core.views import admin_required
from operacao.models import Escala
from operacao.services import criar_escala, editar_escala, remover_escala
from operacao.selectors import exportar_csv


@login_required
def api_diarias(request):
    """Lista todas as diarias."""
    escalas = Escala.objects.select_related(
        'entregador', 'empresa', 'usuario_registro'
    ).all()

    diarias = []
    for e in escalas:
        diarias.append({
            'id': e.id,
            'Data e hora de inicio': timezone.localtime(e.data_inicio).strftime('%Y-%m-%d %H:%M:%S'),
            'Data e hora de fim': timezone.localtime(e.data_fim).strftime('%Y-%m-%d %H:%M:%S'),
            'Empresa': e.empresa.nome,
            'Entregador': e.entregador.nome,
            'Tipo Veiculo': e.empresa.veiculo,
            'CPF': e.entregador.cpf,
            'Taxa total cobrada': float(e.valor_cobrado),
            'Taxa total entregador': float(e.valor_entregador),
            'Taxa minima cobrada': e.empresa.minimo_garantido,
            'Taxa minima entregador': e.empresa.minimo_garantido,
            'usuario_registro': e.usuario_registro.username if e.usuario_registro else '',
        })

    return JsonResponse(diarias, safe=False)


@login_required
@require_POST
def api_criar_diaria(request):
    """Cria uma nova diaria."""
    try:
        data = json.loads(request.body)

        data_inicio = timezone.make_aware(datetime.strptime(data['data_inicio'], '%Y-%m-%dT%H:%M'))
        data_fim = timezone.make_aware(datetime.strptime(data['data_fim'], '%Y-%m-%dT%H:%M'))

        # Busca entregador e empresa pelo nome (compatibilidade com frontend)
        try:
            empresa = Empresa.objects.get(nome=data['empresa'])
        except Empresa.DoesNotExist:
            return JsonResponse({'error': 'Empresa nao encontrada'}, status=400)

        try:
            entregador = Entregador.objects.get(nome=data['entregador'])
        except Entregador.DoesNotExist:
            return JsonResponse({'error': 'Entregador nao encontrado'}, status=400)

        criar_escala(
            entregador_id=entregador.id,
            empresa_id=empresa.id,
            data_inicio=data_inicio,
            data_fim=data_fim,
            usuario=request.user,
        )
        return JsonResponse({'success': True})

    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        registrar_log('Erro ao salvar diaria', request.user.username, detalhes=str(e), nivel='ERROR', request=request)
        return JsonResponse({'error': f'Erro ao salvar diaria: {str(e)}'}, status=500)


@login_required
@require_POST
def api_editar_diaria(request):
    """Edita uma diaria existente."""
    try:
        dados = json.loads(request.body)
        diaria_antiga = dados['diaria_antiga']
        diaria_nova = dados['diaria_nova']

        # Encontra a escala original pelos dados antigos
        data_inicio_antiga = timezone.make_aware(datetime.strptime(diaria_antiga['data_inicio'], '%Y-%m-%d %H:%M:%S'))
        try:
            empresa_antiga = Empresa.objects.get(nome=diaria_antiga['empresa'])
            entregador_antigo = Entregador.objects.get(nome=diaria_antiga['entregador'])
        except (Empresa.DoesNotExist, Entregador.DoesNotExist):
            return JsonResponse({'status': 'error', 'message': 'Diaria nao encontrada'})

        escala = Escala.objects.filter(
            data_inicio=data_inicio_antiga,
            empresa=empresa_antiga,
            entregador=entregador_antigo,
        ).first()

        if not escala:
            return JsonResponse({'status': 'error', 'message': 'Diaria nao encontrada'})

        # Dados novos
        nova_data_inicio = timezone.make_aware(datetime.strptime(diaria_nova['data_inicio'], '%Y-%m-%dT%H:%M'))
        nova_data_fim = timezone.make_aware(datetime.strptime(diaria_nova['data_fim'], '%Y-%m-%dT%H:%M'))
        nova_empresa = Empresa.objects.get(nome=diaria_nova['empresa'])
        novo_entregador = Entregador.objects.get(nome=diaria_nova['entregador'])

        editar_escala(
            escala_id=escala.id,
            data_inicio=nova_data_inicio,
            data_fim=nova_data_fim,
            empresa_id=nova_empresa.id,
            entregador_id=novo_entregador.id,
            usuario=request.user,
        )

        return JsonResponse({'status': 'success'})

    except ValueError as e:
        return JsonResponse({'status': 'error', 'message': str(e)})
    except Exception as e:
        registrar_log('Erro ao editar diaria', request.user.username, detalhes=str(e), nivel='ERROR', request=request)
        return JsonResponse({'status': 'error', 'message': str(e)})


@login_required
@require_POST
def api_remover_diaria(request):
    """Remove uma diaria."""
    try:
        diaria = json.loads(request.body)

        data_inicio = timezone.make_aware(datetime.strptime(diaria['data_inicio'], '%Y-%m-%d %H:%M:%S'))
        try:
            empresa = Empresa.objects.get(nome=diaria['empresa'])
            entregador = Entregador.objects.get(nome=diaria['entregador'])
        except (Empresa.DoesNotExist, Entregador.DoesNotExist):
            return JsonResponse({'status': 'error', 'message': 'Diaria nao encontrada'})

        escala = Escala.objects.filter(
            data_inicio=data_inicio,
            empresa=empresa,
            entregador=entregador,
        ).first()

        if not escala:
            return JsonResponse({'status': 'error', 'message': 'Diaria nao encontrada'})

        remover_escala(escala.id, request.user)
        return JsonResponse({'status': 'success'})

    except Exception as e:
        registrar_log('Erro ao remover diaria', request.user.username, detalhes=str(e), nivel='ERROR', request=request)
        return JsonResponse({'status': 'error', 'message': str(e)})


@login_required
@require_POST
def api_replicar_escala(request):
    """Busca escalas da semana anterior e retorna deslocadas em 7 dias (sem salvar)."""
    try:
        data = json.loads(request.body)
        data_inicio_str = data.get('data_inicio')
        data_fim_str = data.get('data_fim')
        empresa_nome = data.get('empresa')

        if not data_inicio_str or not data_fim_str or not empresa_nome:
            return JsonResponse({'error': 'Preencha data inicio, data fim e empresa.'}, status=400)

        data_inicio = timezone.make_aware(datetime.strptime(data_inicio_str, '%Y-%m-%dT%H:%M'))
        data_fim = timezone.make_aware(datetime.strptime(data_fim_str, '%Y-%m-%dT%H:%M'))

        try:
            empresa = Empresa.objects.get(nome=empresa_nome)
        except Empresa.DoesNotExist:
            return JsonResponse({'error': 'Empresa nao encontrada'}, status=400)

        # Periodo de referencia: 7 dias antes
        ref_inicio = data_inicio - timedelta(days=7)
        ref_fim = data_fim - timedelta(days=7)

        escalas_ref = Escala.objects.select_related('entregador').filter(
            empresa=empresa,
            data_inicio__gte=ref_inicio,
            data_inicio__lt=ref_fim,
        )

        diarias = []
        for escala in escalas_ref:
            nova_inicio = escala.data_inicio + timedelta(days=7)
            nova_fim = escala.data_fim + timedelta(days=7)
            diarias.append({
                'data_inicio': timezone.localtime(nova_inicio).strftime('%Y-%m-%dT%H:%M'),
                'data_fim': timezone.localtime(nova_fim).strftime('%Y-%m-%dT%H:%M'),
                'empresa': empresa_nome,
                'entregador': escala.entregador.nome,
            })

        return JsonResponse({'success': True, 'diarias': diarias})

    except Exception as e:
        return JsonResponse({'error': f'Erro ao buscar escalas: {str(e)}'}, status=500)


@login_required
def api_exportar(request):
    """Exporta diarias como CSV."""
    try:
        data_inicial = request.GET.get('data_inicial')
        data_final = request.GET.get('data_final')

        if not data_inicial or not data_final:
            return JsonResponse({'status': 'error', 'message': 'Datas sao obrigatorias'}, status=400)

        data_inicial = datetime.strptime(data_inicial, '%Y-%m-%d').date()
        data_final = datetime.strptime(data_final, '%Y-%m-%d').date()

        empresas_str = request.GET.get('empresas')
        empresa_ids = None
        if empresas_str:
            nomes = empresas_str.split(',')
            empresa_ids = list(Empresa.objects.filter(nome__in=nomes).values_list('id', flat=True))

        registrar_log('Relatorio exportado', request.user.username, detalhes=f'Periodo: {data_inicial} ate {data_final}', request=request)

        return exportar_csv(data_inicial, data_final, empresa_ids)

    except Exception as e:
        registrar_log('Erro ao exportar relatorio', request.user.username, detalhes=str(e), nivel='ERROR', request=request)
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@admin_required
def api_logs(request):
    """Retorna os logs do sistema."""
    qs = LogSistema.objects.all()

    nivel = request.GET.get('nivel', 'todos')
    if nivel != 'todos':
        qs = qs.filter(nivel=nivel)

    usuario = request.GET.get('usuario', '')
    if usuario:
        qs = qs.filter(usuario=usuario)

    empresa = request.GET.get('empresa', '')
    if empresa:
        qs = qs.filter(empresa=empresa)

    data_inicial = request.GET.get('data_inicial', '')
    if data_inicial:
        qs = qs.filter(timestamp__date__gte=data_inicial)

    data_final = request.GET.get('data_final', '')
    if data_final:
        qs = qs.filter(timestamp__date__lte=data_final)

    logs = []
    for log in qs[:1000]:
        logs.append({
            'timestamp': timezone.localtime(log.timestamp).strftime('%Y-%m-%d %H:%M:%S'),
            'level': log.nivel,
            'message': f'Acao: {log.acao} - Usuario: {log.usuario}' + (f' - Detalhes: {log.detalhes}' if log.detalhes else ''),
            'username': log.usuario,
            'details': log.detalhes,
            'empresa': log.empresa,
            'raw': str(log),
        })

    usuarios = sorted(
        LogSistema.objects.values_list('usuario', flat=True).distinct()
    )
    empresas = sorted(
        v for v in LogSistema.objects.values_list('empresa', flat=True).distinct() if v
    )

    return JsonResponse({'logs': logs, 'usuarios': usuarios, 'empresas': empresas})
