function getCookie(name) {
    let v = null;
    if (document.cookie && document.cookie !== '') {
        document.cookie.split(';').forEach(c => {
            c = c.trim();
            if (c.substring(0, name.length + 1) === (name + '='))
                v = decodeURIComponent(c.substring(name.length + 1));
        });
    }
    return v;
}
const csrftoken = getCookie('csrftoken');
const originalFetch = window.fetch;
window.fetch = function(url, options = {}) {
    if (options.method && !/^(GET|HEAD|OPTIONS|TRACE)$/i.test(options.method)) {
        options.headers = options.headers || {};
        options.headers['X-CSRFToken'] = csrftoken;
    }
    return originalFetch(url, options);
};

$(document).ready(function() {
    carregarDados();
});

function carregarDados() { carregarEmpresas(); carregarEntregadores(); }

function carregarEmpresas() {
    fetch('/api/empresas').then(r => r.json()).then(data => {
        const tbody = document.querySelector('#tabelaEmpresas tbody');
        tbody.innerHTML = '';
        data.forEach(e => {
            const tr = document.createElement('tr');
            if (e.status === 'inativo') tr.classList.add('table-secondary');
            tr.innerHTML = `
                <td data-label="Nome">${e.nome || ''}</td>
                <td data-label="Veiculo">${e.veiculo || ''}</td>
                <td data-label="Taxa Cobrada">R$ ${parseFloat(e.taxa_total_cobrada).toFixed(2)}</td>
                <td data-label="Taxa Entregador">R$ ${parseFloat(e.taxa_total_entregador).toFixed(2)}</td>
                <td data-label="Taxa Cobrada (FDS)">${e.taxa_total_cobrada_fim_semana ? 'R$ ' + parseFloat(e.taxa_total_cobrada_fim_semana).toFixed(2) : '-'}</td>
                <td data-label="Taxa Entregador (FDS)">${e.taxa_total_entregador_fim_semana ? 'R$ ' + parseFloat(e.taxa_total_entregador_fim_semana).toFixed(2) : '-'}</td>
                <td data-label="Minimo Garantido">${e.minimo_garantido === 'S' ? 'Sim' : 'Nao'}</td>
                <td data-label="Status"><span class="badge ${e.status === 'ativo' ? 'bg-success' : 'bg-secondary'}">${e.status || ''}</span></td>
                <td data-label="Acoes">
                    <div class="btn-group">
                        <button class="btn btn-sm btn-primary" onclick="editarEmpresa('${e.nome}')">Editar</button>
                        <button class="btn btn-sm ${e.status === 'ativo' ? 'btn-danger' : 'btn-success'}" onclick="excluirEmpresa('${e.nome}')">${e.status === 'ativo' ? 'Desativar' : 'Ativar'}</button>
                    </div>
                </td>`;
            tbody.appendChild(tr);
        });
    });
}

function carregarEntregadores() {
    fetch('/api/entregadores').then(r => r.json()).then(data => {
        const tbody = document.querySelector('#tabelaEntregadores tbody');
        tbody.innerHTML = '';
        data.forEach(e => {
            const tr = document.createElement('tr');
            if (e.status === 'inativo') tr.classList.add('table-secondary');
            tr.innerHTML = `
                <td data-label="Nome">${e.nome || ''}</td>
                <td data-label="CPF">${e.cpf || ''}</td>
                <td data-label="Status"><span class="badge ${e.status === 'ativo' ? 'bg-success' : 'bg-secondary'}">${e.status || ''}</span></td>
                <td data-label="Acoes">
                    <div class="btn-group">
                        <button class="btn btn-sm btn-primary" onclick="editarEntregador('${e.nome}')">Editar</button>
                        <button class="btn btn-sm ${e.status === 'ativo' ? 'btn-danger' : 'btn-success'}" onclick="excluirEntregador('${e.nome}')">${e.status === 'ativo' ? 'Desativar' : 'Ativar'}</button>
                    </div>
                </td>`;
            tbody.appendChild(tr);
        });
    });
}

function cadastrarEmpresa() {
    const fd = new FormData(document.getElementById('empresaForm'));
    const dados = {
        tipo: 'empresa', nome: fd.get('nome'), veiculo: fd.get('veiculo'),
        tipo_valor: fd.get('tipo_valor'), minimo_garantido: fd.get('minimo_garantido'),
        taxa_total_cobrada: fd.get('taxa_total_cobrada'), taxa_total_entregador: fd.get('taxa_total_entregador'),
        taxa_total_cobrada_fim_semana: fd.get('taxa_total_cobrada_fim_semana'),
        taxa_total_entregador_fim_semana: fd.get('taxa_total_entregador_fim_semana'),
        dias_diferentes: Array.from(fd.getAll('dias_diferentes')).map(Number)
    };
    fetch('/api/cadastrar', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(dados) })
        .then(r => r.json()).then(d => {
            if (d.status === 'success') { alert('Empresa cadastrada com sucesso!'); document.getElementById('empresaForm').reset(); carregarEmpresas(); }
            else alert('Erro: ' + d.message);
        });
}

function cadastrarEntregador() {
    const fd = new FormData(document.getElementById('entregadorForm'));
    fetch('/api/cadastrar', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ tipo: 'entregador', nome: fd.get('nome'), cpf: fd.get('cpf') }) })
        .then(r => r.json()).then(d => {
            if (d.status === 'success') { alert('Entregador cadastrado com sucesso!'); document.getElementById('entregadorForm').reset(); carregarEntregadores(); }
            else alert('Erro: ' + d.message);
        });
}

function editarEmpresa(nome) {
    fetch('/api/empresas').then(r => r.json()).then(data => {
        const e = data.find(x => x.nome === nome);
        if (e) {
            document.getElementById('empresa_id').value = e.nome;
            document.getElementById('empresa_nome').value = e.nome;
            document.getElementById('empresa_veiculo').value = e.veiculo;
            document.getElementById('empresa_tipo_valor').value = e.tipo_valor;
            document.getElementById('empresa_minimo_garantido').value = e.minimo_garantido;
            document.getElementById('empresa_taxa_cobrada').value = e.taxa_total_cobrada;
            document.getElementById('empresa_taxa_entregador').value = e.taxa_total_entregador;
            document.getElementById('empresa_taxa_cobrada_fim_semana').value = e.taxa_total_cobrada_fim_semana || '';
            document.getElementById('empresa_taxa_entregador_fim_semana').value = e.taxa_total_entregador_fim_semana || '';
            document.querySelectorAll('#editarEmpresaForm input[name="dias_diferentes"]').forEach(cb => cb.checked = false);
            if (e.dias_diferentes) {
                e.dias_diferentes.split(',').map(Number).forEach(d => {
                    const cb = document.querySelector(`#editarEmpresaForm input[name="dias_diferentes"][value="${d}"]`);
                    if (cb) cb.checked = true;
                });
            }
            new bootstrap.Modal(document.getElementById('editarEmpresaModal')).show();
        }
    });
}

function salvarEdicaoEmpresa() {
    const fd = new FormData(document.getElementById('editarEmpresaForm'));
    const dados = {
        id: fd.get('id'), nome: fd.get('nome'), veiculo: fd.get('veiculo'),
        tipo_valor: fd.get('tipo_valor'), minimo_garantido: fd.get('minimo_garantido'),
        taxa_total_cobrada: fd.get('taxa_total_cobrada'), taxa_total_entregador: fd.get('taxa_total_entregador'),
        taxa_total_cobrada_fim_semana: fd.get('taxa_total_cobrada_fim_semana') || null,
        taxa_total_entregador_fim_semana: fd.get('taxa_total_entregador_fim_semana') || null,
        dias_diferentes: Array.from(fd.getAll('dias_diferentes')).map(Number)
    };
    fetch('/api/editar/empresa', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(dados) })
        .then(r => r.json()).then(d => {
            if (d.status === 'success') { alert('Empresa atualizada!'); bootstrap.Modal.getInstance(document.getElementById('editarEmpresaModal')).hide(); carregarDados(); }
            else alert('Erro: ' + d.message);
        });
}

function excluirEmpresa(nome) {
    if (confirm('Alterar status desta empresa?')) {
        fetch('/api/excluir/empresa', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ nome }) })
            .then(r => r.json()).then(d => { if (d.status === 'success') { alert('Status alterado!'); carregarDados(); } else alert('Erro: ' + d.message); });
    }
}

function editarEntregador(nome) {
    fetch('/api/entregadores').then(r => r.json()).then(data => {
        const e = data.find(x => x.nome === nome);
        if (e) {
            document.getElementById('entregador_id').value = e.nome;
            document.getElementById('entregador_nome').value = e.nome;
            document.getElementById('entregador_cpf').value = e.cpf;
            new bootstrap.Modal(document.getElementById('editarEntregadorModal')).show();
        }
    });
}

function salvarEdicaoEntregador() {
    const fd = new FormData(document.getElementById('editarEntregadorForm'));
    fetch('/api/editar/entregador', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ id: fd.get('id'), nome: fd.get('nome'), cpf: fd.get('cpf') }) })
        .then(r => r.json()).then(d => {
            if (d.status === 'success') { alert('Entregador atualizado!'); bootstrap.Modal.getInstance(document.getElementById('editarEntregadorModal')).hide(); carregarDados(); }
            else alert('Erro: ' + d.message);
        });
}

function excluirEntregador(nome) {
    if (confirm('Alterar status deste entregador?')) {
        fetch('/api/excluir/entregador', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ nome }) })
            .then(r => r.json()).then(d => { if (d.status === 'success') { alert('Status alterado!'); carregarDados(); } else alert('Erro: ' + d.message); });
    }
}

function importarCSV() {
    const input = document.getElementById('csvEntregadores');
    const resultado = document.getElementById('resultadoImportacao');

    if (!input.files || !input.files[0]) {
        resultado.style.display = 'block';
        resultado.innerHTML = '<div class="alert alert-warning">Selecione um arquivo CSV.</div>';
        return;
    }

    const fd = new FormData();
    fd.append('arquivo', input.files[0]);

    resultado.style.display = 'block';
    resultado.innerHTML = '<div class="alert alert-info">Importando...</div>';

    fetch('/api/entregadores/importar', { method: 'POST', body: fd })
        .then(r => r.json())
        .then(d => {
            if (d.status === 'success') {
                resultado.innerHTML = `<div class="alert alert-success">
                    <strong>Importação concluída!</strong><br>
                    Importados: <strong>${d.importados}</strong> &nbsp;|&nbsp;
                    Ignorados (duplicados ou sem nome): <strong>${d.ignorados}</strong>
                </div>`;
                input.value = '';
                carregarEntregadores();
            } else {
                resultado.innerHTML = `<div class="alert alert-danger">Erro: ${d.message}</div>`;
            }
        })
        .catch(() => {
            resultado.innerHTML = '<div class="alert alert-danger">Erro ao enviar o arquivo.</div>';
        });
}
