$(document).ready(function() {
    $('.select2').select2({ theme: 'bootstrap-5', width: '100%' });
});

function carregarLogs() {
    const nivel = document.getElementById('nivelFilter').value;
    const usuario = document.getElementById('usuarioFilter').value;
    const empresa = document.getElementById('empresaFilter').value;
    const dataInicial = document.getElementById('dataInicial').value;
    const dataFinal = document.getElementById('dataFinal').value;

    const params = new URLSearchParams();
    if (nivel !== 'todos') params.append('nivel', nivel);
    if (usuario) params.append('usuario', usuario);
    if (empresa) params.append('empresa', empresa);
    if (dataInicial) params.append('data_inicial', dataInicial);
    if (dataFinal) params.append('data_final', dataFinal);

    fetch('/api/logs?' + params.toString())
        .then(response => response.json())
        .then(data => {
            const usuarioSelect = document.getElementById('usuarioFilter');
            const usuarioAtual = usuarioSelect.value;
            usuarioSelect.innerHTML = '<option value="">Todos os usuários</option>';
            data.usuarios.forEach(user => {
                usuarioSelect.add(new Option(user, user, false, user === usuarioAtual));
            });
            usuarioSelect.disabled = false;

            const empresaSelect = document.getElementById('empresaFilter');
            const empresaAtual = empresaSelect.value;
            empresaSelect.innerHTML = '<option value="">Todas as empresas</option>';
            data.empresas.forEach(emp => {
                empresaSelect.add(new Option(emp, emp, false, emp === empresaAtual));
            });
            empresaSelect.disabled = false;

            const container = document.getElementById('logContainer');
            container.innerHTML = '';

            if (data.logs.length === 0) {
                container.innerHTML = '<div class="alert alert-info">Nenhum log encontrado com os filtros selecionados.</div>';
            } else {
                data.logs.forEach(log => {
                    const entry = document.createElement('div');
                    entry.className = 'log-entry';
                    const span = document.createElement('span');
                    span.className = log.level === 'ERROR' ? 'log-error' : (log.level === 'WARNING' ? 'log-warning' : 'log-info');
                    span.textContent = log.raw;
                    entry.appendChild(span);
                    container.appendChild(entry);
                });
            }

            document.getElementById('nivelFilter').disabled = false;
            document.getElementById('dataInicial').disabled = false;
            document.getElementById('dataFinal').disabled = false;
        })
        .catch(error => {
            console.error('Erro ao carregar logs:', error);
            alert('Erro ao carregar logs do sistema');
        });
}

function limparFiltros() {
    document.getElementById('nivelFilter').value = 'todos';
    document.getElementById('usuarioFilter').value = '';
    document.getElementById('empresaFilter').value = '';
    document.getElementById('dataInicial').value = '';
    document.getElementById('dataFinal').value = '';
    document.getElementById('nivelFilter').disabled = false;
    document.getElementById('usuarioFilter').disabled = false;
    document.getElementById('empresaFilter').disabled = false;
    document.getElementById('dataInicial').disabled = false;
    document.getElementById('dataFinal').disabled = false;
    carregarLogs();
}

document.addEventListener('DOMContentLoaded', function() { carregarLogs(); });
