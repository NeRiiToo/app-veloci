// CSRF token para AJAX
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
const csrftoken = getCookie('csrftoken');

// Configura jQuery AJAX para enviar CSRF
$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});

// Configura fetch para enviar CSRF
const originalFetch = window.fetch;
window.fetch = function(url, options = {}) {
    if (options.method && !/^(GET|HEAD|OPTIONS|TRACE)$/i.test(options.method)) {
        options.headers = options.headers || {};
        if (options.headers instanceof Headers) {
            options.headers.set('X-CSRFToken', csrftoken);
        } else {
            options.headers['X-CSRFToken'] = csrftoken;
        }
    }
    return originalFetch(url, options);
};

// Toastr config
toastr.options = {
    closeButton: true, newestOnTop: true, progressBar: true,
    positionClass: "toast-top-right", timeOut: "5000",
};

let diariasTemporarias = [];
let todasDiarias = [];
let diariaEmEdicao = null;
let indiceEmEdicao = null;
let modoEdicao = false;

function showAlert(message, type = 'info') {
    const alertContainer = document.querySelector('.alert-container');
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.innerHTML = `${message}<button type="button" class="close" onclick="closeAlert(this.parentElement)">&times;</button>`;
    alertContainer.appendChild(alert);
    setTimeout(() => closeAlert(alert), 5000);
}

function closeAlert(alert) {
    if (!alert.classList.contains('hiding')) {
        alert.classList.add('hiding');
        setTimeout(() => { if (alert.parentElement) alert.parentElement.removeChild(alert); }, 300);
    }
}

function mostrarMensagem(tipo, mensagem) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${tipo} alert-dismissible fade show`;
    alertDiv.innerHTML = `${mensagem}<button type="button" class="btn-close" data-bs-dismiss="alert"></button>`;
    const container = document.querySelector('.container');
    container.insertBefore(alertDiv, container.firstChild);
    setTimeout(() => alertDiv.remove(), 5000);
}

function salvarDadosFormulario() {
    const form = document.getElementById('diariaForm');
    localStorage.setItem('formDiaria', JSON.stringify({
        data_inicio: form.data_inicio.value, data_fim: form.data_fim.value,
        empresa: form.empresa.value, entregador: form.entregador.value
    }));
}

function restaurarDadosFormulario() {
    const formData = localStorage.getItem('formDiaria');
    if (formData) {
        const dados = JSON.parse(formData);
        const form = document.getElementById('diariaForm');
        form.data_inicio.value = dados.data_inicio || '';
        form.data_fim.value = dados.data_fim || '';
        form.empresa.value = dados.empresa || '';
        $('.select2-search').val(dados.entregador || '').trigger('change');
    }
}

function initializeSelect2() {
    $('.select2-search').select2({
        theme: 'bootstrap-5', placeholder: 'Selecione ou digite para buscar',
        allowClear: true, language: { noResults: () => "Nenhum resultado encontrado", searching: () => "Buscando..." }
    }).on('change', salvarDadosFormulario);
}

function carregarDados() {
    carregarEmpresas(); carregarEntregadores(); carregarDiarias(); carregarFiltroEmpresas();
    setTimeout(() => { initializeSelect2(); restaurarDadosFormulario(); }, 500);
}

function carregarEmpresas() {
    fetch('/api/empresas/ativas').then(r => r.json()).then(data => {
        const select = document.querySelector('select[name="empresa"]');
        if (select) {
            select.innerHTML = '<option value="">Selecione uma empresa</option>';
            data.forEach(e => { const o = document.createElement('option'); o.value = e.nome; o.textContent = e.nome; select.appendChild(o); });
        }
    });
}

function carregarEntregadores() {
    fetch('/api/entregadores/ativos').then(r => r.json()).then(data => {
        const select = document.querySelector('select[name="entregador"]');
        if (select) {
            select.innerHTML = '<option value="">Selecione um entregador</option>';
            data.forEach(e => { const o = document.createElement('option'); o.value = e.nome; o.textContent = e.nome; select.appendChild(o); });
            $(select).trigger('change');
        }
    });
}

function carregarFiltroEmpresas() {
    fetch('/api/empresas/filtro').then(r => r.json()).then(data => {
        const select = document.getElementById('filtroEmpresa');
        select.innerHTML = '<option value="">Todas as empresas</option>';
        data.forEach(e => { select.innerHTML += `<option value="${e}">${e}</option>`; });
    });
}

function carregarDiarias() {
    fetch('/api/diarias').then(r => r.json()).then(data => {
        todasDiarias = data;
        atualizarTabelaDiarias(data);
    });
}

function atualizarTabelaDiarias(diarias) {
    const tbody = document.querySelector('#tabelaDiarias tbody');
    tbody.innerHTML = '';
    if (diarias && diarias.length > 0) {
        const sorted = [...diarias].sort((a, b) => new Date(a['Data e hora de inicio']) - new Date(b['Data e hora de inicio']));
        sorted.forEach(d => {
            const tr = document.createElement('tr');
            const id = JSON.stringify({
                data_inicio: d['Data e hora de inicio'], data_fim: d['Data e hora de fim'],
                empresa: d['Empresa'], entregador: d['Entregador']
            }).replace(/"/g, '&quot;');
            let html = `
                <td data-label="Data e hora de inicio">${formatarDataHora(d['Data e hora de inicio'])}</td>
                <td data-label="Data e hora de fim">${formatarDataHora(d['Data e hora de fim'])}</td>
                <td data-label="Empresa">${d['Empresa']}</td>
                <td data-label="Entregador">${d['Entregador']}</td>`;
            if (document.querySelector('meta[name="user-permission"]')?.content === 'ADM') {
                html += `
                    <td data-label="Tipo Veiculo">${d['Tipo Veiculo'] || ''}</td>
                    <td data-label="CPF">${d['CPF'] || ''}</td>
                    <td data-label="Taxa total cobrada">R$ ${typeof d['Taxa total cobrada'] === 'number' ? d['Taxa total cobrada'].toFixed(2) : '0.00'}</td>
                    <td data-label="Taxa total entregador">R$ ${typeof d['Taxa total entregador'] === 'number' ? d['Taxa total entregador'].toFixed(2) : '0.00'}</td>
                    <td data-label="Taxa minima cobrada">${d['Taxa minima cobrada'] === 'S' ? 'Sim' : 'Nao'}</td>
                    <td data-label="Taxa minima entregador">${d['Taxa minima entregador'] === 'S' ? 'Sim' : 'Nao'}</td>
                    <td data-label="Usuario">${d['usuario_registro'] || ''}</td>
                    <td data-label="Acoes">
                        <div class="btn-group">
                            <button class="btn btn-sm btn-primary" onclick='editarDiaria(${id})'>Editar</button>
                            <button class="btn btn-sm btn-danger" onclick='removerDiaria(${id})'>Remover</button>
                        </div>
                    </td>`;
            }
            tr.innerHTML = html;
            tbody.appendChild(tr);
        });
    } else {
        tbody.innerHTML = '<tr><td colspan="12" class="text-center">Nenhuma diaria encontrada</td></tr>';
    }
}

function editarDiariaTemporaria(index) {
    const d = diariasTemporarias[index];
    document.getElementById('data_inicio').value = d.data_inicio;
    document.getElementById('data_fim').value = d.data_fim;
    document.querySelector('select[name="empresa"]').value = d.empresa;
    $('.select2-search').val(d.entregador).trigger('change');
    modoEdicao = true; indiceEmEdicao = index;
    const btn = document.querySelector('button[onclick="adicionarDiariaTemporaria()"]');
    btn.textContent = 'Salvar Alteracoes'; btn.classList.add('btn-success'); btn.classList.remove('btn-primary');
    document.getElementById('diariaForm').scrollIntoView({ behavior: 'smooth' });
}

function adicionarDiariaTemporaria() {
    const form = document.getElementById('diariaForm');
    const fd = new FormData(form);
    if (!fd.get('data_inicio') || !fd.get('data_fim') || !fd.get('empresa') || !fd.get('entregador')) {
        mostrarMensagem('danger', 'Por favor, preencha todos os campos.'); return;
    }
    const di = new Date(fd.get('data_inicio')), df = new Date(fd.get('data_fim'));
    if (df <= di) { mostrarMensagem('danger', 'A data de fim deve ser maior que a data de inicio.'); return; }
    const dh = Math.abs(df - di) / (1000 * 60 * 60);
    if (dh > 8) { mostrarMensagem('danger', 'O periodo nao pode ser maior que 8 horas.'); return; }
    if (dh < 0.5) { mostrarMensagem('danger', 'O periodo minimo e de 30 minutos.'); return; }

    const check = modoEdicao ? diariasTemporarias.filter((_, i) => i !== indiceEmEdicao) : diariasTemporarias;
    if (check.some(d => {
        const a = new Date(d.data_inicio), b = new Date(d.data_fim);
        return d.entregador === fd.get('entregador') && ((di >= a && di < b) || (df > a && df <= b) || (di <= a && df >= b));
    })) { mostrarMensagem('danger', 'Ja existe uma diaria para este entregador neste periodo.'); return; }

    if (modoEdicao) {
        diariasTemporarias.splice(indiceEmEdicao, 1);
        modoEdicao = false; indiceEmEdicao = null;
        const btn = document.querySelector('button[onclick="adicionarDiariaTemporaria()"]');
        btn.textContent = 'Adicionar Diaria'; btn.classList.add('btn-primary'); btn.classList.remove('btn-success');
    }

    diariasTemporarias.push({ data_inicio: fd.get('data_inicio'), data_fim: fd.get('data_fim'), empresa: fd.get('empresa'), entregador: fd.get('entregador') });
    atualizarTabelaTemporaria();
    document.getElementById('btnEnviarEscala').disabled = false;

    const dIA = document.getElementById('data_inicio').value;
    const dFA = document.getElementById('data_fim').value;
    const eA = document.querySelector('select[name="empresa"]').value;
    $('.select2-search').val(null).trigger('change');
    document.getElementById('data_inicio').value = dIA;
    document.getElementById('data_fim').value = dFA;
    document.querySelector('select[name="empresa"]').value = eA;
    salvarDadosFormulario();
    mostrarMensagem('success', 'Diaria adicionada a lista. Clique em "Enviar Escala" para salvar.');
}

function editarDiaria(diaria) {
    diariaEmEdicao = { data_inicio: diaria['Data e hora de inicio'], data_fim: diaria['Data e hora de fim'], empresa: diaria['Empresa'], entregador: diaria['Entregador'] };
    document.getElementById('edit_data_inicio').value = formatarDataParaInput(diaria['Data e hora de inicio']);
    document.getElementById('edit_data_fim').value = formatarDataParaInput(diaria['Data e hora de fim']);
    document.getElementById('edit_empresa').value = diaria['Empresa'];
    carregarOpcoesEdicao().then(() => {
        $('#edit_entregador').val(diaria['Entregador']).trigger('change');
        new bootstrap.Modal(document.getElementById('editarDiariaModal')).show();
    });
}

function removerDiaria(diaria) {
    diariaEmEdicao = { data_inicio: diaria['Data e hora de inicio'], data_fim: diaria['Data e hora de fim'], empresa: diaria['Empresa'], entregador: diaria['Entregador'] };
    document.getElementById('removerDiariaDetalhes').innerHTML = `
        <strong>Empresa:</strong> ${diaria['Empresa']}<br>
        <strong>Entregador:</strong> ${diaria['Entregador']}<br>
        <strong>Inicio:</strong> ${formatarDataHora(diaria['Data e hora de inicio'])}<br>
        <strong>Fim:</strong> ${formatarDataHora(diaria['Data e hora de fim'])}`;
    new bootstrap.Modal(document.getElementById('removerDiariaModal')).show();
}

async function salvarEdicaoDiaria() {
    const fd = new FormData(document.getElementById('editarDiariaForm'));
    try {
        const r = await fetch('/api/diaria/editar', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ diaria_antiga: diariaEmEdicao, diaria_nova: { data_inicio: fd.get('data_inicio'), data_fim: fd.get('data_fim'), empresa: fd.get('empresa'), entregador: fd.get('entregador') } })
        });
        const res = await r.json();
        if (res.status === 'success') {
            mostrarMensagem('success', 'Diaria atualizada com sucesso!');
            bootstrap.Modal.getInstance(document.getElementById('editarDiariaModal')).hide();
            carregarDiarias();
        } else { mostrarMensagem('danger', 'Erro ao atualizar diaria: ' + res.message); }
    } catch (e) { mostrarMensagem('danger', 'Erro ao salvar edicao: ' + e.message); }
}

async function confirmarRemocaoDiaria() {
    try {
        const r = await fetch('/api/diaria/remover', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(diariaEmEdicao)
        });
        const res = await r.json();
        if (res.status === 'success') {
            mostrarMensagem('success', 'Diaria removida com sucesso!');
            bootstrap.Modal.getInstance(document.getElementById('removerDiariaModal')).hide();
            carregarDiarias();
        } else { mostrarMensagem('danger', 'Erro ao remover diaria: ' + res.message); }
    } catch (e) { mostrarMensagem('danger', 'Erro ao remover diaria: ' + e.message); }
}

function formatarDataParaInput(s) {
    try { return new Date(s).toISOString().slice(0, 16); } catch (e) { return ''; }
}

async function carregarOpcoesEdicao() {
    const [emps, ents] = await Promise.all([fetch('/api/empresas').then(r => r.json()), fetch('/api/entregadores').then(r => r.json())]);
    const se = document.getElementById('edit_empresa');
    se.innerHTML = '<option value="">Selecione</option>';
    emps.forEach(e => { se.innerHTML += `<option value="${e.nome}">${e.nome}</option>`; });
    const sn = document.getElementById('edit_entregador');
    sn.innerHTML = '<option value="">Selecione</option>';
    ents.forEach(e => { sn.innerHTML += `<option value="${e.nome}">${e.nome}</option>`; });
    $('#edit_entregador').select2({ theme: 'bootstrap-5', dropdownParent: $('#editarDiariaModal'), placeholder: 'Selecione', allowClear: true });
}

function atualizarTabelaTemporaria() {
    const tbody = document.querySelector('#tabelaDiariasTemp tbody');
    tbody.innerHTML = '';
    [...diariasTemporarias].sort((a, b) => new Date(a.data_inicio) - new Date(b.data_inicio)).forEach((d, i) => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td data-label="Data e Hora de Inicio">${formatarDataHora(d.data_inicio)}</td>
            <td data-label="Data e Hora de Fim">${formatarDataHora(d.data_fim)}</td>
            <td data-label="Empresa">${d.empresa}</td>
            <td data-label="Entregador">${d.entregador}</td>
            <td data-label="Acoes">
                <div class="btn-group">
                    <button class="btn btn-sm btn-primary" onclick="editarDiariaTemporaria(${i})">Editar</button>
                    <button class="btn btn-sm btn-danger" onclick="removerDiariaTemporaria(${i})">Remover</button>
                </div>
            </td>`;
        tbody.appendChild(tr);
    });
}

function formatarDataHora(dh) {
    if (!dh) return '';
    try { return new Date(dh).toLocaleString('pt-BR'); } catch (e) { return dh; }
}

function removerDiariaTemporaria(i) {
    diariasTemporarias.splice(i, 1);
    atualizarTabelaTemporaria();
    if (diariasTemporarias.length === 0) document.getElementById('btnEnviarEscala').disabled = true;
}

async function enviarEscala() {
    const btn = document.getElementById('btnEnviarEscala');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Enviando...';
    const resultados = [], falhas = [];
    for (const d of diariasTemporarias) {
        try {
            const r = await fetch('/api/diaria', {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(d)
            });
            const res = await r.json();
            if (res.success) resultados.push(d); else falhas.push({ diaria: d, erro: res.error });
        } catch (e) { falhas.push({ diaria: d, erro: e.message }); }
    }
    if (falhas.length === 0) {
        mostrarMensagem('success', 'Todas as diarias foram registradas com sucesso!');
        diariasTemporarias = [];
        atualizarTabelaTemporaria();
        carregarDiarias();
        const dI = document.getElementById('data_inicio').value;
        const dF = document.getElementById('data_fim').value;
        const eV = document.querySelector('select[name="empresa"]').value;
        $('.select2-search').val(null).trigger('change');
        document.getElementById('data_inicio').value = dI;
        document.getElementById('data_fim').value = dF;
        document.querySelector('select[name="empresa"]').value = eV;
        salvarDadosFormulario();
    } else {
        let msg = 'Ocorreram erros ao registrar algumas diarias:<br>';
        falhas.forEach(f => { msg += `<br>- ${f.diaria.entregador} (${f.diaria.empresa}): ${f.erro}`; });
        mostrarMensagem('danger', msg);
        diariasTemporarias = diariasTemporarias.filter(d => !resultados.some(r => r.data_inicio === d.data_inicio && r.data_fim === d.data_fim && r.empresa === d.empresa && r.entregador === d.entregador));
        atualizarTabelaTemporaria();
    }
    btn.disabled = diariasTemporarias.length === 0;
    btn.innerHTML = 'Enviar Escala';
}

async function replicarEscala() {
    const dataInicio = document.getElementById('data_inicio').value;
    const dataFim = document.getElementById('data_fim').value;
    const empresa = document.querySelector('select[name="empresa"]').value;

    if (!dataInicio || !dataFim || !empresa) {
        mostrarMensagem('danger', 'Preencha Data Inicio, Data Fim e Empresa para replicar.');
        return;
    }

    const btn = document.getElementById('btnReplicarEscala');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Buscando...';

    try {
        const r = await fetch('/api/diaria/replicar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ data_inicio: dataInicio, data_fim: dataFim, empresa: empresa })
        });
        const res = await r.json();
        if (r.ok && res.success) {
            if (res.diarias.length === 0) {
                mostrarMensagem('warning', 'Nenhuma escala encontrada nos 7 dias anteriores para esta empresa.');
                return;
            }
            let adicionadas = 0;
            let ignoradas = 0;
            for (const d of res.diarias) {
                const di = new Date(d.data_inicio);
                const df = new Date(d.data_fim);
                const conflito = diariasTemporarias.some(t => {
                    const a = new Date(t.data_inicio), b = new Date(t.data_fim);
                    return t.entregador === d.entregador && ((di >= a && di < b) || (df > a && df <= b) || (di <= a && df >= b));
                });
                if (conflito) { ignoradas++; continue; }
                diariasTemporarias.push(d);
                adicionadas++;
            }
            atualizarTabelaTemporaria();
            document.getElementById('btnEnviarEscala').disabled = diariasTemporarias.length === 0;
            let msg = `${adicionadas} diaria(s) adicionada(s) a lista.`;
            if (ignoradas > 0) msg += ` ${ignoradas} ignorada(s) por conflito de horario.`;
            msg += ' Revise e clique em "Enviar Escala" para salvar.';
            mostrarMensagem('success', msg);
        } else {
            mostrarMensagem('danger', res.error || 'Erro ao buscar escalas.');
        }
    } catch (e) {
        mostrarMensagem('danger', 'Erro ao replicar escalas: ' + e.message);
    } finally {
        btn.disabled = false;
        btn.innerHTML = 'Replicar Escala';
    }
}

function abrirModalExportar() {
    fetch('/api/empresas').then(r => r.json()).then(data => {
        const select = $('#exportarEmpresas');
        select.empty().append(new Option('Todas as empresas', 'todas'));
        data.forEach(e => select.append(new Option(e.nome, e.nome)));
        select.select2({ theme: 'bootstrap-5', width: '100%', placeholder: 'Selecione', allowClear: true }).val(null).trigger('change');
    });
    new bootstrap.Modal(document.getElementById('exportarModal')).show();
}

function exportarDiarias() {
    const fd = new FormData(document.getElementById('exportarForm'));
    const di = fd.get('data_inicial'), df = fd.get('data_final');
    const emps = $('#exportarEmpresas').val() || [];
    if (!di || !df) { alert('Preencha as datas.'); return; }
    if (di > df) { alert('Data inicial maior que final.'); return; }
    let url = `/api/exportar?data_inicial=${di}&data_final=${df}`;
    if (!emps.includes('todas') && emps.length > 0) url += `&empresas=${emps.join(',')}`;
    window.location.href = url;
    bootstrap.Modal.getInstance(document.getElementById('exportarModal')).hide();
}

function aplicarFiltros() {
    const empresa = document.getElementById('filtroEmpresa').value;
    const di = document.getElementById('filtroDataInicial').value;
    const df = document.getElementById('filtroDataFinal').value;
    let filtered = [...todasDiarias];
    if (empresa) filtered = filtered.filter(d => d['Empresa'] === empresa);
    if (di) filtered = filtered.filter(d => d['Data e hora de inicio'].split(' ')[0] >= di);
    if (df) filtered = filtered.filter(d => d['Data e hora de inicio'].split(' ')[0] <= df);
    atualizarTabelaDiarias(filtered);
}

function limparFiltros() {
    document.getElementById('filtroEmpresa').value = '';
    document.getElementById('filtroDataInicial').value = '';
    document.getElementById('filtroDataFinal').value = '';
    atualizarTabelaDiarias(todasDiarias);
}

function atualizarLimitesDataFim() {
    const di = document.getElementById('data_inicio');
    const df = document.getElementById('data_fim');
    if (di.value) {
        const inicio = new Date(di.value);
        df.min = inicio.toISOString().slice(0, 16);
        const max = new Date(inicio); max.setHours(max.getHours() + 8);
        df.max = max.toISOString().slice(0, 16);
        if (df.value && new Date(df.value) > max) df.value = df.max;
    }
}

document.getElementById('diariaForm').addEventListener('submit', function(e) {
    e.preventDefault();
    adicionarDiariaTemporaria();
});

document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('diariaForm').querySelectorAll('input, select').forEach(el => el.addEventListener('change', salvarDadosFormulario));
    carregarDados();
});
