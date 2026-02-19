from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST

from core.models import Empresa, Entregador, PerfilUsuario, registrar_log


def _is_admin(user):
    if user.is_superuser:
        return True
    perfil = getattr(user, 'perfil', None)
    return perfil and not perfil.e_supervisor


def admin_required(view_func):
    """Decorator que exige login + permissao ADM."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('/login')
        if not _is_admin(request.user):
            return JsonResponse({'error': 'Acesso nao autorizado'}, status=403)
        return view_func(request, *args, **kwargs)
    return wrapper


# ---------- AUTH ----------

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        senha = request.POST.get('senha')
        user = authenticate(request, username=username, password=senha)
        if user is not None:
            login(request, user)
            registrar_log('Login bem-sucedido', username, request=request)
            return redirect('/')
        else:
            registrar_log('Tentativa de login falha', username, nivel='WARNING', request=request)
            return render(request, 'login.html', {'error': 'Usuario ou senha incorretos'})
    return render(request, 'login.html')


def logout_view(request):
    if request.user.is_authenticated:
        registrar_log('Logout', request.user.username, request=request)
    logout(request)
    return redirect('/login')


# ---------- PAGES ----------

@login_required
def index_view(request):
    perfil = getattr(request.user, 'perfil', None)
    permissao = perfil.permissao if perfil else 'ADM'
    return render(request, 'index.html', {'permissao': permissao})


@admin_required
def cadastros_view(request):
    perfil = getattr(request.user, 'perfil', None)
    permissao = perfil.permissao if perfil else 'ADM'
    return render(request, 'cadastros.html', {'permissao': permissao})


@admin_required
def cadastro_usuario_view(request):
    perfil = getattr(request.user, 'perfil', None)
    permissao = perfil.permissao if perfil else 'ADM'
    empresas = list(Empresa.objects.filter(ativo=True).values_list('nome', flat=True))

    usuarios_list = []
    for user in User.objects.all():
        p = getattr(user, 'perfil', None)
        emps = list(p.empresas_vinculadas.values_list('nome', flat=True)) if p else []
        usuarios_list.append({
            'username': user.username,
            'permissao': p.permissao if p else 'ADM',
            'empresas_vinculadas': emps,
        })

    return render(request, 'cadastro_usuario.html', {
        'permissao': permissao,
        'empresas': empresas,
        'usuarios': usuarios_list,
    })


@admin_required
def logs_view(request):
    perfil = getattr(request.user, 'perfil', None)
    permissao = perfil.permissao if perfil else 'ADM'
    return render(request, 'logs.html', {'permissao': permissao})


# ---------- API USUARIOS ----------

@admin_required
@require_POST
def api_cadastrar_usuario(request):
    username = request.POST.get('username')
    senha = request.POST.get('senha')
    permissao = request.POST.get('permissao')
    empresas_nomes = request.POST.getlist('empresas_vinculadas[]')

    if not username or not senha or not permissao:
        return JsonResponse({'success': False, 'error': 'Todos os campos sao obrigatorios'})

    if User.objects.filter(username=username).exists():
        return JsonResponse({'success': False, 'error': 'Nome de usuario ja existe'})

    user = User.objects.create_user(username=username, password=senha)
    if permissao == 'ADM':
        user.is_superuser = True
        user.is_staff = True
        user.save()

    perfil = PerfilUsuario.objects.create(
        user=user,
        e_supervisor=(permissao == 'supervisor'),
    )
    if empresas_nomes:
        empresas = Empresa.objects.filter(nome__in=empresas_nomes)
        perfil.empresas_vinculadas.set(empresas)

    registrar_log('Usuario cadastrado', request.user.username, detalhes=username, request=request)
    return JsonResponse({'success': True})


@admin_required
@require_POST
def api_editar_usuario(request):
    username = request.POST.get('username')
    nova_senha = request.POST.get('senha')
    nova_permissao = request.POST.get('permissao')
    empresas_nomes = request.POST.getlist('empresas_vinculadas[]')

    if not username or not nova_permissao:
        return JsonResponse({'success': False, 'error': 'Dados incompletos'})

    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Usuario nao encontrado'})

    # Nao permitir alterar permissao do ultimo admin
    if user.is_superuser and nova_permissao != 'ADM':
        admin_count = User.objects.filter(is_superuser=True).count()
        if admin_count <= 1:
            return JsonResponse({'success': False, 'error': 'Nao e possivel alterar a permissao do ultimo administrador'})

    if nova_senha:
        user.set_password(nova_senha)

    if nova_permissao == 'ADM':
        user.is_superuser = True
        user.is_staff = True
    else:
        user.is_superuser = False
        user.is_staff = False
    user.save()

    perfil, _ = PerfilUsuario.objects.get_or_create(user=user)
    perfil.e_supervisor = (nova_permissao == 'supervisor')
    perfil.save()
    if empresas_nomes:
        empresas = Empresa.objects.filter(nome__in=empresas_nomes)
        perfil.empresas_vinculadas.set(empresas)
    else:
        perfil.empresas_vinculadas.clear()

    registrar_log('Usuario editado', request.user.username, detalhes=username, request=request)
    return JsonResponse({'success': True})


@admin_required
@require_POST
def api_excluir_usuario(request):
    import json
    data = json.loads(request.body)
    username = data.get('username')

    if not username:
        return JsonResponse({'success': False, 'error': 'Username nao fornecido'})

    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Usuario nao encontrado'})

    if user.is_superuser:
        admin_count = User.objects.filter(is_superuser=True).count()
        if admin_count <= 1:
            return JsonResponse({'success': False, 'error': 'Nao e possivel excluir o ultimo administrador'})

    user.delete()
    registrar_log('Usuario excluido', request.user.username, detalhes=username, request=request)
    return JsonResponse({'success': True})


# ---------- API EMPRESAS ----------

@admin_required
def api_empresas(request):
    empresas = list(Empresa.objects.all().values(
        'id', 'nome', 'veiculo', 'tipo_valor', 'minimo_garantido',
        'taxa_total_cobrada', 'taxa_total_entregador',
        'taxa_cobrada_fds', 'taxa_entregador_fds',
        'dias_diferentes', 'ativo',
    ))
    for e in empresas:
        e['status'] = 'ativo' if e.pop('ativo') else 'inativo'
        e['taxa_total_cobrada'] = float(e['taxa_total_cobrada'])
        e['taxa_total_entregador'] = float(e['taxa_total_entregador'])
        e['taxa_total_cobrada_fim_semana'] = float(e.pop('taxa_cobrada_fds')) if e['taxa_cobrada_fds'] else None
        e['taxa_total_entregador_fim_semana'] = float(e.pop('taxa_entregador_fds')) if e['taxa_entregador_fds'] else None
    return JsonResponse(empresas, safe=False)


@login_required
def api_empresas_ativas(request):
    qs = Empresa.objects.filter(ativo=True)

    perfil = getattr(request.user, 'perfil', None)
    if perfil and perfil.e_supervisor:
        qs = qs.filter(perfilusuario=perfil)

    empresas = list(qs.values(
        'id', 'nome', 'veiculo', 'tipo_valor', 'minimo_garantido',
        'taxa_total_cobrada', 'taxa_total_entregador',
        'taxa_cobrada_fds', 'taxa_entregador_fds',
        'dias_diferentes',
    ))
    for e in empresas:
        e['status'] = 'ativo'
        e['taxa_total_cobrada'] = float(e['taxa_total_cobrada'])
        e['taxa_total_entregador'] = float(e['taxa_total_entregador'])
        e['taxa_total_cobrada_fim_semana'] = float(e.pop('taxa_cobrada_fds')) if e['taxa_cobrada_fds'] else None
        e['taxa_total_entregador_fim_semana'] = float(e.pop('taxa_entregador_fds')) if e['taxa_entregador_fds'] else None
    return JsonResponse(empresas, safe=False)


@login_required
def api_empresas_filtro(request):
    qs = Empresa.objects.filter(ativo=True)

    perfil = getattr(request.user, 'perfil', None)
    if perfil and perfil.e_supervisor:
        qs = qs.filter(perfilusuario=perfil)

    nomes = list(qs.values_list('nome', flat=True))
    return JsonResponse(nomes, safe=False)


@admin_required
@require_POST
def api_cadastrar(request):
    import json
    data = json.loads(request.body)
    tipo = data.get('tipo')

    if tipo == 'empresa':
        campos = ['nome', 'veiculo', 'tipo_valor', 'minimo_garantido', 'taxa_total_cobrada', 'taxa_total_entregador']
        for campo in campos:
            if not data.get(campo):
                return JsonResponse({'status': 'error', 'message': f'Campo {campo} e obrigatorio'}, status=400)

        if Empresa.objects.filter(nome=data['nome']).exists():
            return JsonResponse({'status': 'error', 'message': 'Empresa ja cadastrada'}, status=400)

        dias_diferentes = data.get('dias_diferentes', [])
        empresa = Empresa.objects.create(
            nome=data['nome'],
            veiculo=data['veiculo'],
            tipo_valor=data['tipo_valor'],
            minimo_garantido=data['minimo_garantido'],
            taxa_total_cobrada=float(data['taxa_total_cobrada']),
            taxa_total_entregador=float(data['taxa_total_entregador']),
            taxa_cobrada_fds=float(data['taxa_total_cobrada_fim_semana']) if data.get('taxa_total_cobrada_fim_semana') else None,
            taxa_entregador_fds=float(data['taxa_total_entregador_fim_semana']) if data.get('taxa_total_entregador_fim_semana') else None,
            dias_diferentes=','.join(map(str, dias_diferentes)),
        )
        registrar_log('Empresa cadastrada', request.user.username, detalhes=f'Nome: {data["nome"]}', empresa=data['nome'], request=request)
        return JsonResponse({'status': 'success'})

    elif tipo == 'entregador':
        nome = data.get('nome')
        cpf = data.get('cpf')
        if not nome or not cpf:
            return JsonResponse({'status': 'error', 'message': 'Nome e CPF sao obrigatorios'}, status=400)

        if Entregador.objects.filter(cpf=cpf).exists():
            return JsonResponse({'status': 'error', 'message': 'CPF ja cadastrado'}, status=400)

        Entregador.objects.create(nome=nome, cpf=cpf)
        registrar_log('Entregador cadastrado', request.user.username, detalhes=f'Nome: {nome}, CPF: {cpf}', request=request)
        return JsonResponse({'status': 'success'})

    return JsonResponse({'status': 'error', 'message': 'Tipo invalido'}, status=400)


@admin_required
@require_POST
def api_editar_empresa(request):
    import json
    data = json.loads(request.body)

    try:
        empresa = Empresa.objects.get(nome=data['id'])
    except Empresa.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Empresa nao encontrada'})

    empresa.nome = data['nome']
    empresa.veiculo = data['veiculo']
    empresa.tipo_valor = data['tipo_valor']
    empresa.minimo_garantido = data['minimo_garantido']
    empresa.taxa_total_cobrada = float(data['taxa_total_cobrada'])
    empresa.taxa_total_entregador = float(data['taxa_total_entregador'])
    empresa.taxa_cobrada_fds = float(data['taxa_total_cobrada_fim_semana']) if data.get('taxa_total_cobrada_fim_semana') else None
    empresa.taxa_entregador_fds = float(data['taxa_total_entregador_fim_semana']) if data.get('taxa_total_entregador_fim_semana') else None

    dias_diferentes = data.get('dias_diferentes', [])
    empresa.dias_diferentes = ','.join(map(str, dias_diferentes)) if isinstance(dias_diferentes, list) else ''

    empresa.save()
    registrar_log('Empresa editada', request.user.username, detalhes=f'Nome: {data["nome"]}', empresa=data['nome'], request=request)
    return JsonResponse({'status': 'success'})


@admin_required
@require_POST
def api_editar_entregador(request):
    import json
    data = json.loads(request.body)

    if not data or 'id' not in data or 'nome' not in data or 'cpf' not in data:
        return JsonResponse({'status': 'error', 'message': 'Dados incompletos'})

    try:
        entregador = Entregador.objects.get(nome=data['id'])
    except Entregador.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Entregador nao encontrado'})

    entregador.nome = data['nome']
    entregador.cpf = data['cpf']
    entregador.ativo = True
    entregador.save()
    registrar_log('Entregador editado', request.user.username, detalhes=f'Nome: {data["nome"]}', request=request)
    return JsonResponse({'status': 'success'})


@admin_required
@require_POST
def api_excluir_empresa(request):
    import json
    data = json.loads(request.body)
    nome = data.get('nome')

    try:
        empresa = Empresa.objects.get(nome=nome)
    except Empresa.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Empresa nao encontrada'})

    empresa.ativo = not empresa.ativo
    empresa.save()
    novo_status = 'ativo' if empresa.ativo else 'inativo'
    registrar_log('Status da empresa alterado', request.user.username, detalhes=f'Nome: {nome}, Status: {novo_status}', empresa=nome, request=request)
    return JsonResponse({'status': 'success'})


@admin_required
@require_POST
def api_excluir_entregador(request):
    import json
    data = json.loads(request.body)
    nome = data.get('nome')

    if not nome:
        return JsonResponse({'status': 'error', 'message': 'Nome nao fornecido'})

    try:
        entregador = Entregador.objects.get(nome=nome)
    except Entregador.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Entregador nao encontrado'})

    entregador.ativo = not entregador.ativo
    entregador.save()
    novo_status = 'ativo' if entregador.ativo else 'inativo'
    registrar_log('Status do entregador alterado', request.user.username, detalhes=f'Nome: {nome}, Status: {novo_status}', request=request)
    return JsonResponse({'status': 'success'})


@admin_required
@require_POST
def api_importar_entregadores(request):
    import csv
    import io

    arquivo = request.FILES.get('arquivo')
    if not arquivo:
        return JsonResponse({'status': 'error', 'message': 'Nenhum arquivo enviado'}, status=400)

    try:
        conteudo = arquivo.read().decode('utf-8-sig')
    except UnicodeDecodeError:
        arquivo.seek(0)
        conteudo = arquivo.read().decode('latin-1')

    # Detecta separador
    primeira_linha = conteudo.split('\n')[0]
    separador = ';' if ';' in primeira_linha else ','

    reader = csv.DictReader(io.StringIO(conteudo), delimiter=separador)

    # Normaliza nomes das colunas
    colunas = [c.strip().lower() for c in (reader.fieldnames or [])]
    if 'nome' not in colunas or 'cpf' not in colunas:
        return JsonResponse({'status': 'error', 'message': 'CSV deve conter as colunas Nome e CPF'}, status=400)

    importados = 0
    ignorados = 0

    for row in reader:
        row_norm = {k.strip().lower(): v.strip() for k, v in row.items() if k}
        nome = row_norm.get('nome', '')
        cpf = row_norm.get('cpf', '')

        if not nome or not cpf:
            ignorados += 1
            continue

        if Entregador.objects.filter(cpf=cpf).exists():
            ignorados += 1
            continue

        Entregador.objects.create(nome=nome, cpf=cpf)
        importados += 1

    registrar_log('Importacao CSV de entregadores', request.user.username, detalhes=f'importados={importados}, ignorados={ignorados}', request=request)
    return JsonResponse({'status': 'success', 'importados': importados, 'ignorados': ignorados})


@admin_required
def api_entregadores(request):
    entregadores = list(Entregador.objects.all().values('id', 'nome', 'cpf', 'ativo'))
    for e in entregadores:
        e['status'] = 'ativo' if e.pop('ativo') else 'inativo'
    return JsonResponse(entregadores, safe=False)


@login_required
def api_entregadores_ativos(request):
    entregadores = list(Entregador.objects.filter(ativo=True).values('id', 'nome', 'cpf'))
    for e in entregadores:
        e['status'] = 'ativo'
    return JsonResponse(entregadores, safe=False)
