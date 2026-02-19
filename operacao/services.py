from datetime import timedelta
from decimal import Decimal

from django.db.models import Q

from core.models import Empresa, Entregador, registrar_log
from operacao.models import Escala


def calcular_taxa(empresa: Empresa, data_inicio, data_fim) -> dict:
    """
    Calcula as taxas cobrada e do entregador para uma escala,
    considerando tipo de valor (unico/hora), dia da semana,
    dias diferentes e minimo garantido.
    """
    dia_semana = data_inicio.weekday()

    dias_diferentes = []
    if empresa.dias_diferentes:
        try:
            dias_diferentes = [int(d) for d in empresa.dias_diferentes.split(',') if d.strip()]
        except ValueError:
            dias_diferentes = []

    is_fds = dia_semana >= 5

    if dia_semana in dias_diferentes:
        taxa_cobrada = empresa.taxa_cobrada_fds if empresa.taxa_cobrada_fds is not None else empresa.taxa_total_cobrada
        taxa_entregador = empresa.taxa_entregador_fds if empresa.taxa_entregador_fds is not None else empresa.taxa_total_entregador
    elif is_fds and empresa.taxa_cobrada_fds is not None:
        taxa_cobrada = empresa.taxa_cobrada_fds
        taxa_entregador = empresa.taxa_entregador_fds if empresa.taxa_entregador_fds is not None else empresa.taxa_total_entregador
    else:
        taxa_cobrada = empresa.taxa_total_cobrada
        taxa_entregador = empresa.taxa_total_entregador

    if empresa.tipo_valor == 'hora':
        horas = Decimal(str((data_fim - data_inicio).total_seconds() / 3600))
        taxa_cobrada = round(taxa_cobrada * horas, 2)
        taxa_entregador = round(taxa_entregador * horas, 2)

    if empresa.minimo_garantido == 'S' and taxa_entregador < empresa.taxa_total_entregador:
        taxa_entregador = empresa.taxa_total_entregador

    return {
        'taxa_cobrada': taxa_cobrada,
        'taxa_entregador': taxa_entregador,
    }


def verificar_conflito_horario(entregador_id, data_inicio, data_fim, excluir_escala_id=None):
    """Verifica se existe conflito de horario para o entregador."""
    qs = Escala.objects.filter(
        entregador_id=entregador_id,
        data_inicio__lt=data_fim,
        data_fim__gt=data_inicio,
    )
    if excluir_escala_id:
        qs = qs.exclude(pk=excluir_escala_id)
    return qs.exists()


def criar_escala(entregador_id, empresa_id, data_inicio, data_fim, usuario):
    """Cria uma nova escala com validacoes completas."""
    # Validacao de periodo
    diff_hours = (data_fim - data_inicio).total_seconds() / 3600
    if data_fim <= data_inicio:
        raise ValueError('A data de fim deve ser maior que a data de inicio')
    if diff_hours > 8:
        raise ValueError('O periodo nao pode ser maior que 8 horas')
    if diff_hours < 0.5:
        raise ValueError('O periodo minimo e de 30 minutos')

    empresa = Empresa.objects.get(pk=empresa_id)
    if not empresa.ativo:
        raise ValueError('Empresa esta inativa')

    entregador = Entregador.objects.get(pk=entregador_id)
    if not entregador.ativo:
        raise ValueError('Entregador esta inativo')

    if verificar_conflito_horario(entregador_id, data_inicio, data_fim):
        raise ValueError(f'Ja existe uma diaria registrada para {entregador.nome} neste periodo')

    taxas = calcular_taxa(empresa, data_inicio, data_fim)

    escala = Escala.objects.create(
        entregador=entregador,
        empresa=empresa,
        data_inicio=data_inicio,
        data_fim=data_fim,
        valor_cobrado=taxas['taxa_cobrada'],
        valor_entregador=taxas['taxa_entregador'],
        usuario_registro=usuario,
    )

    registrar_log(
        'Diaria registrada', usuario.username,
        detalhes=f'Empresa: {empresa.nome}, Entregador: {entregador.nome}, '
                 f'Periodo: {data_inicio:%Y-%m-%d %H:%M:%S} ate {data_fim:%Y-%m-%d %H:%M:%S}, '
                 f'Taxa cobrada: {taxas["taxa_cobrada"]}, Taxa entregador: {taxas["taxa_entregador"]}',
        empresa=empresa.nome,
    )

    return escala


def editar_escala(escala_id, data_inicio, data_fim, empresa_id, entregador_id, usuario):
    """Edita uma escala existente com revalidacao."""
    escala = Escala.objects.get(pk=escala_id)

    if verificar_conflito_horario(entregador_id, data_inicio, data_fim, excluir_escala_id=escala_id):
        raise ValueError('Ja existe uma diaria para este entregador neste periodo')

    empresa = Empresa.objects.get(pk=empresa_id)
    entregador = Entregador.objects.get(pk=entregador_id)
    taxas = calcular_taxa(empresa, data_inicio, data_fim)

    escala.data_inicio = data_inicio
    escala.data_fim = data_fim
    escala.empresa = empresa
    escala.entregador = entregador
    escala.valor_cobrado = taxas['taxa_cobrada']
    escala.valor_entregador = taxas['taxa_entregador']
    escala.save()

    registrar_log(
        'Diaria editada', usuario.username,
        detalhes=f'Empresa: {empresa.nome}, Entregador: {entregador.nome}',
        empresa=empresa.nome,
    )

    return escala


def remover_escala(escala_id, usuario):
    """Remove uma escala."""
    escala = Escala.objects.get(pk=escala_id)
    info = f'Empresa: {escala.empresa.nome}, Entregador: {escala.entregador.nome}'
    empresa_nome = escala.empresa.nome
    escala.delete()

    registrar_log('Diaria removida', usuario.username, detalhes=info, empresa=empresa_nome)
