import csv
from datetime import datetime

from django.http import StreamingHttpResponse
from django.utils import timezone

from operacao.models import Escala


def listar_escalas(data_inicial=None, data_final=None, empresa_id=None, entregador_id=None):
    """Lista escalas com filtros opcionais."""
    qs = Escala.objects.select_related('entregador', 'empresa', 'usuario_registro').all()

    if data_inicial:
        qs = qs.filter(data_inicio__date__gte=data_inicial)
    if data_final:
        qs = qs.filter(data_inicio__date__lte=data_final)
    if empresa_id:
        qs = qs.filter(empresa_id=empresa_id)
    if entregador_id:
        qs = qs.filter(entregador_id=entregador_id)

    return qs


def _formatar_decimal(valor):
    """Formata decimal no padrão brasileiro: vírgula como separador, sem zeros desnecessários."""
    s = f'{float(valor):.2f}'.rstrip('0').rstrip('.')
    return s.replace('.', ',')


class Echo:
    """Pseudo-buffer que retorna o valor escrito — para StreamingHttpResponse."""
    def write(self, value):
        return value


def exportar_csv(data_inicial, data_final, empresa_ids=None):
    """Gera um StreamingHttpResponse com CSV das escalas no periodo."""
    qs = listar_escalas(data_inicial=data_inicial, data_final=data_final)
    if empresa_ids:
        qs = qs.filter(empresa_id__in=empresa_ids)

    pseudo_buffer = Echo()
    writer = csv.writer(pseudo_buffer, delimiter=';')

    def rows():
        # Primeira linha com BOM (UTF-8 com BOM para compatibilidade com Excel)
        yield writer.writerow([
            'Data e hora de início',
            'Data e hora de fim',
            'Empresa',
            'Tipo Veiculo',
            'Entregador',
            'CPF',
            'Taxa total cobrada',
            'Taxa total entregador',
            'Taxa mínima cobrada',
            'Taxa mínima entregador',
        ]).encode('utf-8-sig')
        for e in qs.iterator():
            dt_inicio = timezone.localtime(e.data_inicio)
            dt_fim = timezone.localtime(e.data_fim)
            yield writer.writerow([
                dt_inicio.strftime('%d/%m/%Y %H:%M'),
                dt_fim.strftime('%d/%m/%Y %H:%M'),
                e.empresa.nome,
                e.empresa.veiculo,
                e.entregador.nome,
                e.entregador.cpf,
                _formatar_decimal(e.valor_cobrado),
                _formatar_decimal(e.valor_entregador),
                e.empresa.minimo_garantido,
                e.empresa.minimo_garantido,
            ]).encode('utf-8')

    response = StreamingHttpResponse(rows(), content_type='text/csv; charset=utf-8')
    filename = f'escala_diarias_{data_inicial}_a_{data_final}.csv'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
