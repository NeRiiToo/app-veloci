let modalEditar;

document.addEventListener('DOMContentLoaded', function() {
    modalEditar = new bootstrap.Modal(document.getElementById('modalEditar'));

    $('.empresas-select').select2({
        theme: 'bootstrap-5',
        placeholder: 'Selecione as empresas',
        allowClear: true,
        language: { noResults: function() { return "Nenhuma empresa encontrada"; } }
    });

    $('.empresas-select-modal').select2({
        theme: 'bootstrap-5',
        placeholder: 'Selecione as empresas',
        allowClear: true,
        dropdownParent: $('#modalEditar'),
        language: { noResults: function() { return "Nenhuma empresa encontrada"; } }
    });

    const formCadastro = document.getElementById('formCadastro');
    if (formCadastro) {
        formCadastro.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(formCadastro);
            fetch('/api/cadastrar_usuario', { method: 'POST', body: formData })
                .then(response => response.json())
                .then(data => {
                    if (data.success) { location.reload(); }
                    else { alert(data.error || 'Erro ao cadastrar usuário'); }
                })
                .catch(error => { console.error('Erro:', error); alert('Erro ao cadastrar usuário'); });
        });
    }
});

function getCookie(name) {
    let v = document.cookie.match('(^|;) ?' + name + '=([^;]*)(;|$)');
    return v ? v[2] : null;
}

function selecionarTodasEmpresas() {
    const opts = []; $('.empresas-select option').each(function() { opts.push($(this).val()); });
    $('.empresas-select').val(opts).trigger('change');
}
function limparSelecaoEmpresas() { $('.empresas-select').val(null).trigger('change'); }
function selecionarTodasEmpresasModal() {
    const opts = []; $('.empresas-select-modal option').each(function() { opts.push($(this).val()); });
    $('.empresas-select-modal').val(opts).trigger('change');
}
function limparSelecaoEmpresasModal() { $('.empresas-select-modal').val(null).trigger('change'); }

function editarUsuarioFromButton(button) {
    let empresas = [];
    try { empresas = JSON.parse(button.dataset.empresas || '[]'); } catch (e) {}
    document.querySelector('#edit_username').value = button.dataset.username;
    document.querySelector('#edit_senha').value = '';
    document.querySelector('#edit_permissao').value = button.dataset.permissao;
    $('.empresas-select-modal').val(empresas).trigger('change');
    modalEditar.show();
}

function salvarEdicao() {
    const form = document.getElementById('formEditar');
    const formData = new FormData(form);
    fetch('/editar_usuario', { method: 'POST', body: formData })
        .then(response => response.json())
        .then(data => {
            if (data.success) { location.reload(); }
            else { alert(data.error || 'Erro ao editar usuário'); }
        })
        .catch(error => { console.error('Erro:', error); alert('Erro ao editar usuário'); });
}

function excluirUsuario(username) {
    if (!confirm('Tem certeza que deseja excluir este usuário?')) return;
    const csrf = getCookie('csrftoken');
    fetch('/excluir_usuario', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf || '' },
        body: JSON.stringify({ username: username })
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) { location.reload(); }
            else { alert(data.error || 'Erro ao excluir usuário'); }
        })
        .catch(error => { console.error('Erro:', error); alert('Erro ao excluir usuário'); });
}
