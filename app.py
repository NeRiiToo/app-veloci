from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, session, flash
import pandas as pd
from datetime import datetime
import os
import io
import csv
from functools import wraps

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui'  # Necessário para sessões

# Configuração dos arquivos de dados
EMPRESAS_FILE = 'empresas.csv'
ENTREGADORES_FILE = 'entregadores.csv'
ESCALA_FILE = 'modelo escala.xlsx'
DIARIAS_FILE = 'diarias.xlsx'
USUARIOS_FILE = 'usuarios.csv'

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session or session['permissao'] != 'ADM':
            return jsonify({'error': 'Acesso não autorizado'}), 403
        return f(*args, **kwargs)
    return decorated_function

def carregar_usuarios():
    if os.path.exists(USUARIOS_FILE):
        with open(USUARIOS_FILE, 'r', encoding='utf-8') as f:
            usuarios = list(csv.DictReader(f))
            # Converte a string de empresas em lista
            for usuario in usuarios:
                if 'empresas_vinculadas' in usuario:
                    if usuario['empresas_vinculadas']:
                        usuario['empresas_vinculadas'] = usuario['empresas_vinculadas'].split('|')
                    else:
                        usuario['empresas_vinculadas'] = []
                else:
                    usuario['empresas_vinculadas'] = []
            return usuarios
    return []

def salvar_usuarios(usuarios):
    # Converte a lista de empresas em string
    usuarios_para_salvar = []
    for usuario in usuarios:
        usuario_copy = usuario.copy()
        if 'empresas_vinculadas' in usuario_copy:
            usuario_copy['empresas_vinculadas'] = '|'.join(usuario_copy['empresas_vinculadas'])
        usuarios_para_salvar.append(usuario_copy)

    with open(USUARIOS_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['username', 'senha', 'permissao', 'empresas_vinculadas'])
        writer.writeheader()
        writer.writerows(usuarios_para_salvar)

def carregar_empresas():
    if os.path.exists(EMPRESAS_FILE):
        df = pd.read_csv(EMPRESAS_FILE)
        # Converte os valores numéricos e substitui NaN por 0
        df['taxa_total_cobrada'] = pd.to_numeric(df['taxa_total_cobrada'], errors='coerce').fillna(0)
        df['taxa_total_entregador'] = pd.to_numeric(df['taxa_total_entregador'], errors='coerce').fillna(0)
        # Garante que todas as colunas necessárias existam
        colunas_padrao = ['nome', 'veiculo', 'tipo_valor', 'minimo_garantido', 'taxa_total_cobrada', 'taxa_total_entregador', 'status']
        for coluna in colunas_padrao:
            if coluna not in df.columns:
                df[coluna] = ''
        # Define status como 'ativo' para registros sem status
        df.loc[df['status'].isna(), 'status'] = 'ativo'
        # Converte o DataFrame para dicionário
        empresas = df.to_dict('records')
        # Garante que não haja NaN no JSON
        for empresa in empresas:
            for key, value in empresa.items():
                if pd.isna(value):
                    if key in ['taxa_total_cobrada', 'taxa_total_entregador']:
                        empresa[key] = 0.0
                    else:
                        empresa[key] = ''
        return empresas
    return []

def salvar_empresas(df):
    df.to_csv(EMPRESAS_FILE, index=False)

def carregar_entregadores():
    if os.path.exists(ENTREGADORES_FILE):
        df = pd.read_csv(ENTREGADORES_FILE)
        # Garante que todas as colunas necessárias existam
        colunas_padrao = ['nome', 'cpf', 'status']
        for coluna in colunas_padrao:
            if coluna not in df.columns:
                df[coluna] = ''
        # Define status como 'ativo' para registros sem status
        df.loc[df['status'].isna(), 'status'] = 'ativo'
        # Converte CPF para string
        df['cpf'] = df['cpf'].astype(str)
        # Converte o DataFrame para dicionário
        entregadores = df.to_dict('records')
        # Garante que não haja NaN no JSON
        for entregador in entregadores:
            for key, value in entregador.items():
                if pd.isna(value):
                    entregador[key] = ''
        return entregadores
    return []

def salvar_entregadores(df):
    df.to_csv(ENTREGADORES_FILE, index=False)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        senha = request.form.get('senha')
        
        usuarios = carregar_usuarios()
        for usuario in usuarios:
            if usuario['username'] == username and usuario['senha'] == senha:
                session['username'] = username
                session['permissao'] = usuario['permissao']
                return redirect(url_for('index'))
        
        return render_template('login.html', error='Usuário ou senha inválidos')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/cadastro_usuario', methods=['GET', 'POST'])
def cadastro_usuario():
    if not session.get('username'):
        return redirect(url_for('login'))
    
    if session.get('permissao') != 'ADM':
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username')
        senha = request.form.get('senha')
        permissao = request.form.get('permissao')
        empresas_vinculadas = request.form.getlist('empresas_vinculadas[]')

        if not username or not senha or not permissao:
            return jsonify({'success': False, 'error': 'Todos os campos são obrigatórios'})

        try:
            df = pd.read_csv(USUARIOS_FILE)
            if username in df['username'].values:
                return jsonify({'success': False, 'error': 'Nome de usuário já existe'})

            novo_usuario = {
                'username': username,
                'senha': senha,
                'permissao': permissao,
                'empresas_vinculadas': '|'.join(empresas_vinculadas) if empresas_vinculadas else ''
            }

            df = pd.concat([df, pd.DataFrame([novo_usuario])], ignore_index=True)
            df.to_csv(USUARIOS_FILE, index=False)
            return jsonify({'success': True})

        except Exception as e:
            print(f"Erro ao cadastrar usuário: {str(e)}")
            return jsonify({'success': False, 'error': 'Erro ao cadastrar usuário'})

    try:
        usuarios = pd.read_csv(USUARIOS_FILE)
        usuarios = usuarios.fillna('')
        usuarios_list = []
        
        # Processa cada usuário para converter a string de empresas em lista
        for _, row in usuarios.iterrows():
            usuario = row.to_dict()
            if usuario['empresas_vinculadas'] and isinstance(usuario['empresas_vinculadas'], str):
                usuario['empresas_vinculadas'] = usuario['empresas_vinculadas'].split('|')
            else:
                usuario['empresas_vinculadas'] = []
            usuarios_list.append(usuario)
        
        # Carrega apenas empresas ativas
        empresas = pd.read_csv(EMPRESAS_FILE)
        empresas = empresas[empresas['status'] == 'ativo']
        empresas_list = empresas['nome'].tolist()

        return render_template('cadastro_usuario.html', 
                             usuarios=usuarios_list, 
                             empresas=empresas_list, 
                             permissao=session.get('permissao'))
    except Exception as e:
        print(f"Erro ao carregar dados: {str(e)}")
        return redirect(url_for('index'))

@app.route('/excluir_usuario', methods=['POST'])
def excluir_usuario():
    if not session.get('username') or session.get('permissao') != 'ADM':
        return jsonify({'success': False, 'error': 'Acesso negado'})

    try:
        data = request.get_json()
        username = data.get('username')

        if not username:
            return jsonify({'success': False, 'error': 'Username não fornecido'})

        df = pd.read_csv(USUARIOS_FILE)
        
        # Não permitir excluir o último administrador
        if username in df[df['permissao'] == 'ADM']['username'].values:
            adm_count = len(df[df['permissao'] == 'ADM'])
            if adm_count <= 1:
                return jsonify({'success': False, 'error': 'Não é possível excluir o último administrador'})

        df = df[df['username'] != username]
        df.to_csv(USUARIOS_FILE, index=False)
        return jsonify({'success': True})

    except Exception as e:
        print(f"Erro ao excluir usuário: {str(e)}")
        return jsonify({'success': False, 'error': 'Erro ao excluir usuário'})

@app.route('/editar_usuario', methods=['POST'])
def editar_usuario():
    if not session.get('username') or session.get('permissao') != 'ADM':
        return jsonify({'success': False, 'error': 'Acesso negado'})

    try:
        username = request.form.get('username')
        nova_senha = request.form.get('senha')
        nova_permissao = request.form.get('permissao')
        empresas_vinculadas = request.form.getlist('empresas_vinculadas[]')

        if not username or not nova_permissao:
            return jsonify({'success': False, 'error': 'Dados incompletos'})

        df = pd.read_csv(USUARIOS_FILE)
        
        # Verificar se é o último administrador tentando mudar sua própria permissão
        if username in df[df['permissao'] == 'ADM']['username'].values:
            adm_count = len(df[df['permissao'] == 'ADM'])
            if adm_count <= 1 and nova_permissao != 'ADM':
                return jsonify({'success': False, 'error': 'Não é possível alterar a permissão do último administrador'})

        # Atualizar os dados do usuário
        mask = df['username'] == username
        df.loc[mask, 'permissao'] = nova_permissao
        if nova_senha:
            df.loc[mask, 'senha'] = nova_senha
        df.loc[mask, 'empresas_vinculadas'] = '|'.join(empresas_vinculadas) if empresas_vinculadas else ''

        df.to_csv(USUARIOS_FILE, index=False)
        return jsonify({'success': True})

    except Exception as e:
        print(f"Erro ao editar usuário: {str(e)}")
        return jsonify({'success': False, 'error': 'Erro ao editar usuário'})

def carregar_dados():
    try:
        if os.path.exists(EMPRESAS_FILE) and os.path.exists(ENTREGADORES_FILE):
            df_empresas = pd.read_csv(EMPRESAS_FILE)
            df_entregadores = pd.read_csv(ENTREGADORES_FILE)
            # Define os tipos de dados corretamente
            df_empresas['taxa_total_cobrada'] = pd.to_numeric(df_empresas['taxa_total_cobrada'], errors='coerce').fillna(0)
            df_empresas['taxa_total_entregador'] = pd.to_numeric(df_empresas['taxa_total_entregador'], errors='coerce').fillna(0)
            df_entregadores['cpf'] = df_entregadores['cpf'].astype(str)
            # Garante que todas as colunas existam
            colunas_padrao = ['tipo', 'nome', 'cpf', 'veiculo', 'tipo_valor', 'minimo_garantido', 'taxa_total_cobrada', 'taxa_total_entregador', 'status']
            for coluna in colunas_padrao:
                if coluna not in df_empresas.columns:
                    df_empresas[coluna] = ''
                if coluna not in df_entregadores.columns:
                    df_entregadores[coluna] = ''
            # Define status como 'ativo' para registros sem status
            df_empresas.loc[df_empresas['status'] == '', 'status'] = 'ativo'
            df_entregadores.loc[df_entregadores['status'] == '', 'status'] = 'ativo'
            return df_empresas, df_entregadores
    except Exception as e:
        print(f"Erro ao carregar dados: {str(e)}")
    return pd.DataFrame(columns=['tipo', 'nome', 'cpf', 'veiculo', 'tipo_valor', 'minimo_garantido', 'taxa_total_cobrada', 'taxa_total_entregador', 'status']), pd.DataFrame(columns=['nome', 'cpf', 'status'])

def salvar_dados(df_empresas, df_entregadores):
    # Converte os tipos de dados antes de salvar
    df_empresas['taxa_total_cobrada'] = pd.to_numeric(df_empresas['taxa_total_cobrada'], errors='coerce')
    df_empresas['taxa_total_entregador'] = pd.to_numeric(df_empresas['taxa_total_entregador'], errors='coerce')
    df_empresas['cpf'] = df_empresas['cpf'].astype(str)
    df_entregadores['cpf'] = df_entregadores['cpf'].astype(str)
    df_empresas.to_csv(EMPRESAS_FILE, index=False)
    df_entregadores.to_csv(ENTREGADORES_FILE, index=False)

def carregar_escala():
    if os.path.exists(ESCALA_FILE):
        return pd.read_excel(ESCALA_FILE)
    return pd.DataFrame(columns=[
        'Data e hora de início',
        'Data e hora de fim',
        'Empresa',
        'Tipo Veiculo',
        'Entregador',
        'CPF',
        'Taxa total cobrada',
        'Taxa total entregador',
        'Taxa mínima cobrada',
        'Taxa mínima entregador'
    ])

def carregar_diarias():
    try:
        if os.path.exists(DIARIAS_FILE):
            df = pd.read_excel(DIARIAS_FILE)
            print(f"Arquivo de diárias carregado com sucesso. Registros encontrados: {len(df)}")  # Log para debug
            return df
        else:
            print("Arquivo de diárias não encontrado. Criando DataFrame vazio.")  # Log para debug
            return pd.DataFrame(columns=[
                'Data e hora de início',
                'Data e hora de fim',
                'Empresa',
                'Tipo Veiculo',
                'Entregador',
                'CPF',
                'Taxa total cobrada',
                'Taxa total entregador',
                'Taxa mínima cobrada',
                'Taxa mínima entregador'
            ])
    except Exception as e:
        print(f"Erro ao carregar arquivo de diárias: {str(e)}")  # Log para debug
        return pd.DataFrame(columns=[
            'Data e hora de início',
            'Data e hora de fim',
            'Empresa',
            'Tipo Veiculo',
            'Entregador',
            'CPF',
            'Taxa total cobrada',
            'Taxa total entregador',
            'Taxa mínima cobrada',
            'Taxa mínima entregador'
        ])

def salvar_diarias(df_diarias):
    df_diarias.to_excel(DIARIAS_FILE, index=False)

@app.route('/')
@login_required
def index():
    return render_template('index.html', permissao=session.get('permissao'))

@app.route('/cadastros')
@admin_required
def cadastros():
    return render_template('cadastros.html', permissao=session.get('permissao'))

@app.route('/api/empresas', methods=['GET'])
@admin_required
def api_empresas():
    empresas = carregar_empresas()
    # Retorna todos os registros, incluindo inativos, para a página de cadastros
    return jsonify(empresas)

@app.route('/api/entregadores', methods=['GET'])
@admin_required
def api_entregadores():
    entregadores = carregar_entregadores()
    # Retorna todos os registros, incluindo inativos, para a página de cadastros
    return jsonify(entregadores)

@app.route('/api/cadastrar', methods=['POST'])
@admin_required
def api_cadastrar():
    try:
        data = request.get_json()
        tipo = data.get('tipo')
        
        if tipo == 'empresa':
            empresas = carregar_empresas()  # Retorna lista de dicionários
            nova_empresa = {
                'nome': data['nome'],
                'veiculo': data['veiculo'],
                'tipo_valor': data['tipo_valor'],
                'minimo_garantido': data['minimo_garantido'],
                'taxa_total_cobrada': float(data['taxa_total_cobrada']),
                'taxa_total_entregador': float(data['taxa_total_entregador']),
                'status': 'ativo'
            }
            
            # Se empresas é uma lista vazia, cria um DataFrame com a nova empresa
            if not empresas:
                df = pd.DataFrame([nova_empresa])
            else:
                # Se já existem empresas, adiciona a nova
                df = pd.DataFrame(empresas)
                df = pd.concat([df, pd.DataFrame([nova_empresa])], ignore_index=True)
            
            salvar_empresas(df)
            return jsonify({'status': 'success'})
        
        elif tipo == 'entregador':
            entregadores = carregar_entregadores()  # Retorna lista de dicionários
            novo_entregador = {
                'nome': data['nome'],
                'cpf': data['cpf'],
                'status': 'ativo'
            }
            
            # Se entregadores é uma lista vazia, cria um DataFrame com o novo entregador
            if not entregadores:
                df = pd.DataFrame([novo_entregador])
            else:
                # Se já existem entregadores, adiciona o novo
                df = pd.DataFrame(entregadores)
                df = pd.concat([df, pd.DataFrame([novo_entregador])], ignore_index=True)
            
            salvar_entregadores(df)
            return jsonify({'status': 'success'})
        
        return jsonify({'status': 'error', 'message': 'Tipo inválido'})
    except Exception as e:
        print(f"Erro ao cadastrar: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/editar/empresa', methods=['POST'])
@admin_required
def api_editar_empresa():
    data = request.get_json()
    df = pd.DataFrame(carregar_empresas())  # Converte lista de dicionários para DataFrame
    
    # Encontra o índice da empresa a ser editada
    idx = df[df['nome'] == data['id']].index[0]
    
    # Atualiza os dados
    df.loc[idx, 'nome'] = data['nome']
    df.loc[idx, 'veiculo'] = data['veiculo']
    df.loc[idx, 'tipo_valor'] = data['tipo_valor']
    df.loc[idx, 'minimo_garantido'] = data['minimo_garantido']
    df.loc[idx, 'taxa_total_cobrada'] = data['taxa_total_cobrada']
    df.loc[idx, 'taxa_total_entregador'] = data['taxa_total_entregador']
    df.loc[idx, 'status'] = 'ativo'  # Garante que o status permaneça ativo
    
    salvar_empresas(df)
    return jsonify({'status': 'success'})

@app.route('/api/editar/entregador', methods=['POST'])
@admin_required
def api_editar_entregador():
    data = request.get_json()
    df = pd.DataFrame(carregar_entregadores())  # Converte lista de dicionários para DataFrame
    
    # Encontra o índice do entregador a ser editado
    idx = df[df['nome'] == data['id']].index[0]
    
    # Atualiza os dados
    df.loc[idx, 'nome'] = data['nome']
    df.loc[idx, 'cpf'] = data['cpf']
    df.loc[idx, 'status'] = 'ativo'  # Garante que o status permaneça ativo
    
    salvar_entregadores(df)
    return jsonify({'status': 'success'})

@app.route('/api/excluir/empresa', methods=['POST'])
@admin_required
def api_excluir_empresa():
    try:
        data = request.get_json()
        nome = data.get('nome')
        
        empresas = carregar_empresas()  # Já retorna uma lista de dicionários
        df = pd.DataFrame(empresas)
        
        # Em vez de excluir, altera o status para 'inativo' ou 'ativo'
        status_atual = df.loc[df['nome'] == nome, 'status'].iloc[0]
        novo_status = 'inativo' if status_atual == 'ativo' else 'ativo'
        df.loc[df['nome'] == nome, 'status'] = novo_status
        
        salvar_empresas(df)
        return jsonify({'status': 'success'})
    except Exception as e:
        print(f"Erro ao alterar status da empresa: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/excluir/entregador', methods=['POST'])
@admin_required
def api_excluir_entregador():
    try:
        data = request.get_json()
        nome = data.get('nome')
        
        entregadores = carregar_entregadores()  # Já retorna uma lista de dicionários
        df = pd.DataFrame(entregadores)
        
        # Em vez de excluir, altera o status para 'inativo' ou 'ativo'
        status_atual = df.loc[df['nome'] == nome, 'status'].iloc[0]
        novo_status = 'inativo' if status_atual == 'ativo' else 'ativo'
        df.loc[df['nome'] == nome, 'status'] = novo_status
        
        salvar_entregadores(df)
        return jsonify({'status': 'success'})
    except Exception as e:
        print(f"Erro ao alterar status do entregador: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/empresas/ativas', methods=['GET'])
def api_empresas_ativas():
    try:
        df = pd.DataFrame(carregar_empresas())
        # Filtra apenas registros ativos
        df = df[df['status'] == 'ativo']
        
        # Se o usuário for supervisor, filtra apenas as empresas vinculadas
        if session.get('permissao') == 'supervisor':
            usuarios = carregar_usuarios()
            usuario_atual = next((u for u in usuarios if u['username'] == session.get('username')), None)
            if usuario_atual and usuario_atual['empresas_vinculadas']:
                df = df[df['nome'].isin(usuario_atual['empresas_vinculadas'])]
        
        empresas = df.to_dict('records')
        print("Empresas ativas encontradas:", len(empresas))  # Log para debug
        return jsonify(empresas)
    except Exception as e:
        print(f"Erro ao carregar empresas ativas: {str(e)}")  # Log para debug
        return jsonify([])

@app.route('/api/entregadores/ativos', methods=['GET'])
def api_entregadores_ativos():
    try:
        df = pd.DataFrame(carregar_entregadores())
        # Filtra apenas registros ativos
        df = df[df['status'] == 'ativo']
        entregadores = df.to_dict('records')
        print("Entregadores ativos encontrados:", len(entregadores))  # Log para debug
        return jsonify(entregadores)
    except Exception as e:
        print(f"Erro ao carregar entregadores ativos: {str(e)}")  # Log para debug
        return jsonify([])

@app.route('/api/exportar', methods=['GET'])
def exportar_excel():
    # Carrega a planilha de diárias
    df_diarias = carregar_diarias()
    
    # Obtém as datas do período selecionado
    data_inicial = request.args.get('data_inicial')
    data_final = request.args.get('data_final')
    
    # Converte as datas para o formato correto
    data_inicial = datetime.strptime(data_inicial, '%Y-%m-%d').strftime('%Y-%m-%d')
    data_final = datetime.strptime(data_final, '%Y-%m-%d').strftime('%Y-%m-%d')
    
    # Filtra as diárias do período selecionado
    df_periodo = df_diarias[
        (df_diarias['Data e hora de início'].str[:10] >= data_inicial) & 
        (df_diarias['Data e hora de início'].str[:10] <= data_final)
    ]
    
    # Cria um arquivo Excel temporário com as diárias do período
    output_file = f'escala_diarias_{data_inicial}_a_{data_final}.xlsx'
    df_periodo.to_excel(output_file, index=False)
    
    return send_file(output_file, as_attachment=True)

@app.route('/api/diarias', methods=['GET'])
def get_diarias():
    try:
        df_diarias = carregar_diarias()
        if df_diarias.empty:
            return jsonify([])
            
        # Garante que todas as colunas necessárias existam
        colunas_necessarias = [
            'Data e hora de início',
            'Data e hora de fim',
            'Empresa',
            'Tipo Veiculo',
            'Entregador',
            'CPF',
            'Taxa total cobrada',
            'Taxa total entregador',
            'Taxa mínima cobrada',
            'Taxa mínima entregador'
        ]
        
        for coluna in colunas_necessarias:
            if coluna not in df_diarias.columns:
                df_diarias[coluna] = ''
        
        # Converte os valores numéricos e substitui NaN por 0
        df_diarias['Taxa total cobrada'] = pd.to_numeric(df_diarias['Taxa total cobrada'], errors='coerce').fillna(0)
        df_diarias['Taxa total entregador'] = pd.to_numeric(df_diarias['Taxa total entregador'], errors='coerce').fillna(0)
        
        # Converte para dicionário
        diarias = df_diarias[colunas_necessarias].to_dict('records')
        
        # Garante que não haja NaN no JSON
        for diaria in diarias:
            for key, value in diaria.items():
                if pd.isna(value):  # Verifica se é NaN
                    if key in ['Taxa total cobrada', 'Taxa total entregador']:
                        diaria[key] = 0.0
                    else:
                        diaria[key] = ''
        
        print("Diárias encontradas:", len(diarias))  # Log para debug
        return jsonify(diarias)
        
    except Exception as e:
        print(f"Erro ao obter diárias: {str(e)}")  # Log para debug
        return jsonify([])

@app.route('/api/diaria', methods=['POST'])
def api_diaria():
    try:
        data = request.get_json()
        
        # Carrega as informações da empresa e do entregador
        empresas = pd.DataFrame(carregar_empresas())
        entregadores = pd.DataFrame(carregar_entregadores())
        
        # Encontra a empresa e o entregador
        empresa = empresas[empresas['nome'] == data['empresa']].iloc[0]
        entregador = entregadores[entregadores['nome'] == data['entregador']].iloc[0]
        
        # Formata as datas para o formato desejado
        data_inicio = datetime.strptime(data['data_inicio'], '%Y-%m-%dT%H:%M').strftime('%Y-%m-%d %H:%M:%S')
        data_fim = datetime.strptime(data['data_fim'], '%Y-%m-%dT%H:%M').strftime('%Y-%m-%d %H:%M:%S')
        
        # Cria o registro da diária
        nova_diaria = {
            'Data e hora de início': data_inicio,
            'Data e hora de fim': data_fim,
            'Empresa': data['empresa'],
            'Tipo Veiculo': data['veiculo'],
            'Entregador': data['entregador'],
            'CPF': entregador['cpf'],
            'Taxa total cobrada': float(empresa['taxa_total_cobrada']),
            'Taxa total entregador': float(empresa['taxa_total_entregador']),
            'Taxa mínima cobrada': 'S' if empresa['minimo_garantido'] == 'S' else 'N',
            'Taxa mínima entregador': 'S' if empresa['minimo_garantido'] == 'S' else 'N'
        }
        
        # Carrega as diárias existentes
        df_diarias = carregar_diarias()
        
        # Adiciona a nova diária
        if df_diarias.empty:
            df_diarias = pd.DataFrame([nova_diaria])
        else:
            df_diarias = pd.concat([df_diarias, pd.DataFrame([nova_diaria])], ignore_index=True)
        
        # Salva o arquivo atualizado
        salvar_diarias(df_diarias)
        
        return jsonify({'status': 'success'})
    except Exception as e:
        print(f"Erro ao registrar diária: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True) 