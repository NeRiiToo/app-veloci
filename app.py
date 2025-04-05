from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, session, flash
import pandas as pd
from datetime import datetime
import os
import logging
from logging.handlers import RotatingFileHandler
import io
import csv
from functools import wraps

# Configuração do sistema de logs
def setup_logger():
    # Cria a pasta logs se não existir
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Configura o logger
    logger = logging.getLogger('sistema')
    logger.setLevel(logging.INFO)
    
    # Formato do log
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler para arquivo com rotação
    file_handler = RotatingFileHandler(
        'logs/sistema.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Handler para console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger

# Inicializa o logger
logger = setup_logger()

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui'  # Necessário para sessões

# Configuração dos arquivos de dados
EMPRESAS_FILE = 'empresas.csv'
ENTREGADORES_FILE = 'entregadores.csv'
ESCALA_FILE = 'modelo escala.xlsx'
DIARIAS_FILE = os.path.join('data', 'diarias.xlsx')
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
        
        # Log para debug
        print(f"Tentativa de login - Username: {username}")
        
        try:
            # Verifica se o arquivo existe
            if not os.path.exists(USUARIOS_FILE):
                print("Arquivo de usuários não encontrado")
                return render_template('login.html', error='Erro de configuração do sistema')
            
            # Carrega o arquivo de usuários
            df = pd.read_csv(USUARIOS_FILE)
            print(f"Usuários carregados: {len(df)}")
            
            # Verifica se o usuário existe
            usuarios_encontrados = df[df['username'] == username]
            if usuarios_encontrados.empty:
                print(f"Usuário não encontrado: {username}")
                return render_template('login.html', error='Usuário não encontrado')
            
            usuario = usuarios_encontrados.iloc[0]
            print(f"Senha fornecida: {senha}")
            print(f"Senha no banco: {usuario['senha']}")
            
            # Compara as senhas
            if str(usuario['senha']) == str(senha):
                session['username'] = username
                session['permissao'] = usuario['permissao']
                log_action('Login bem-sucedido', username)
                print(f"Login bem-sucedido para {username}")
                return redirect(url_for('index'))
            else:
                log_action('Tentativa de login falha - Senha incorreta', username)
                print(f"Senha incorreta para {username}")
                return render_template('login.html', error='Senha incorreta')
                
        except Exception as e:
            print(f"Erro no login: {str(e)}")
            log_error('Erro no login', username, str(e))
            return render_template('login.html', error=f'Erro ao fazer login: {str(e)}')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    if session.get('username'):
        log_action('Logout', session.get('username'))
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
            log_action('Tentativa de cadastro de usuário - Campos incompletos', session.get('username'))
            return jsonify({'success': False, 'error': 'Todos os campos são obrigatórios'})

        try:
            df = pd.read_csv(USUARIOS_FILE)
            if username in df['username'].values:
                log_action('Tentativa de cadastro de usuário - Usuário já existe', session.get('username'), username)
                return jsonify({'success': False, 'error': 'Nome de usuário já existe'})

            novo_usuario = {
                'username': username,
                'senha': senha,
                'permissao': permissao,
                'empresas_vinculadas': '|'.join(empresas_vinculadas) if empresas_vinculadas else ''
            }

            df = pd.concat([df, pd.DataFrame([novo_usuario])], ignore_index=True)
            df.to_csv(USUARIOS_FILE, index=False)
            log_action('Usuário cadastrado com sucesso', session.get('username'), username)
            return jsonify({'success': True})

        except Exception as e:
            log_error('Erro ao cadastrar usuário', session.get('username'), str(e))
            return jsonify({'success': False, 'error': 'Erro ao cadastrar usuário'})

    try:
        usuarios = pd.read_csv(USUARIOS_FILE)
        usuarios = usuarios.fillna('')
        usuarios_list = []
        
        for _, row in usuarios.iterrows():
            usuario = row.to_dict()
            if usuario['empresas_vinculadas'] and isinstance(usuario['empresas_vinculadas'], str):
                usuario['empresas_vinculadas'] = usuario['empresas_vinculadas'].split('|')
            else:
                usuario['empresas_vinculadas'] = []
            usuarios_list.append(usuario)
        
        empresas = pd.read_csv(EMPRESAS_FILE)
        empresas = empresas[empresas['status'] == 'ativo']
        empresas_list = empresas['nome'].tolist()

        return render_template('cadastro_usuario.html', 
                             usuarios=usuarios_list, 
                             empresas=empresas_list, 
                             permissao=session.get('permissao'))
    except Exception as e:
        log_error('Erro ao carregar dados de usuários', session.get('username'), str(e))
        return redirect(url_for('index'))

@app.route('/excluir_usuario', methods=['POST'])
def excluir_usuario():
    if not session.get('username') or session.get('permissao') != 'ADM':
        log_action('Tentativa de exclusão de usuário - Acesso negado', session.get('username'))
        return jsonify({'success': False, 'error': 'Acesso negado'})

    try:
        data = request.get_json()
        username = data.get('username')

        if not username:
            log_action('Tentativa de exclusão de usuário - Username não fornecido', session.get('username'))
            return jsonify({'success': False, 'error': 'Username não fornecido'})

        df = pd.read_csv(USUARIOS_FILE)
        
        # Não permitir excluir o último administrador
        if username in df[df['permissao'] == 'ADM']['username'].values:
            adm_count = len(df[df['permissao'] == 'ADM'])
            if adm_count <= 1:
                log_action('Tentativa de exclusão do último administrador', session.get('username'), username)
                return jsonify({'success': False, 'error': 'Não é possível excluir o último administrador'})

        df = df[df['username'] != username]
        df.to_csv(USUARIOS_FILE, index=False)
        log_action('Usuário excluído com sucesso', session.get('username'), username)
        return jsonify({'success': True})

    except Exception as e:
        log_error('Erro ao excluir usuário', session.get('username'), str(e))
        return jsonify({'success': False, 'error': 'Erro ao excluir usuário'})

@app.route('/editar_usuario', methods=['POST'])
def editar_usuario():
    if not session.get('username') or session.get('permissao') != 'ADM':
        log_action('Tentativa de edição de usuário - Acesso negado', session.get('username'))
        return jsonify({'success': False, 'error': 'Acesso negado'})

    try:
        username = request.form.get('username')
        nova_senha = request.form.get('senha')
        nova_permissao = request.form.get('permissao')
        empresas_vinculadas = request.form.getlist('empresas_vinculadas[]')

        if not username or not nova_permissao:
            log_action('Tentativa de edição de usuário - Dados incompletos', session.get('username'))
            return jsonify({'success': False, 'error': 'Dados incompletos'})

        df = pd.read_csv(USUARIOS_FILE)
        
        # Verificar se é o último administrador tentando mudar sua própria permissão
        if username in df[df['permissao'] == 'ADM']['username'].values:
            adm_count = len(df[df['permissao'] == 'ADM'])
            if adm_count <= 1 and nova_permissao != 'ADM':
                log_action('Tentativa de alterar permissão do último administrador', session.get('username'), username)
                return jsonify({'success': False, 'error': 'Não é possível alterar a permissão do último administrador'})

        # Atualizar os dados do usuário
        mask = df['username'] == username
        df.loc[mask, 'permissao'] = nova_permissao
        if nova_senha:
            df.loc[mask, 'senha'] = nova_senha
        df.loc[mask, 'empresas_vinculadas'] = '|'.join(empresas_vinculadas) if empresas_vinculadas else ''

        df.to_csv(USUARIOS_FILE, index=False)
        log_action('Usuário editado com sucesso', session.get('username'), username)
        return jsonify({'success': True})

    except Exception as e:
        log_error('Erro ao editar usuário', session.get('username'), str(e))
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
        arquivo_diarias = DIARIAS_FILE
        if os.path.exists(arquivo_diarias):
            df = pd.read_excel(arquivo_diarias)
            print(f"Arquivo de diárias carregado com sucesso. Registros encontrados: {len(df)}")
            return df
        else:
            print("Arquivo de diárias não encontrado. Criando DataFrame vazio.")
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
        print(f"Erro ao carregar arquivo de diárias: {str(e)}")
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
    try:
        # Garante que o diretório data existe
        if not os.path.exists('data'):
            os.makedirs('data')
        
        # Salva o arquivo na pasta data
        arquivo_diarias = DIARIAS_FILE
        df_diarias.to_excel(arquivo_diarias, index=False)
        print(f"Arquivo salvo com sucesso em: {arquivo_diarias}")
        return True
    except Exception as e:
        print(f"Erro ao salvar arquivo de diárias: {str(e)}")
        return False

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
            empresas = carregar_empresas()
            nova_empresa = {
                'nome': data['nome'],
                'veiculo': data['veiculo'],
                'tipo_valor': data['tipo_valor'],
                'minimo_garantido': data['minimo_garantido'],
                'taxa_total_cobrada': float(data['taxa_total_cobrada']),
                'taxa_total_entregador': float(data['taxa_total_entregador']),
                'taxa_total_cobrada_fim_semana': float(data['taxa_total_cobrada_fim_semana']) if data.get('taxa_total_cobrada_fim_semana') else None,
                'taxa_total_entregador_fim_semana': float(data['taxa_total_entregador_fim_semana']) if data.get('taxa_total_entregador_fim_semana') else None,
                'dias_diferentes': ','.join(map(str, data.get('dias_diferentes', []))),
                'status': 'ativo'
            }
            
            if not empresas:
                df = pd.DataFrame([nova_empresa])
            else:
                df = pd.DataFrame(empresas)
                df = pd.concat([df, pd.DataFrame([nova_empresa])], ignore_index=True)
            
            salvar_empresas(df)
            log_action('Empresa cadastrada', session.get('username'), f"Nome: {data['nome']}")
            return jsonify({'status': 'success'})
        
        elif tipo == 'entregador':
            entregadores = carregar_entregadores()
            novo_entregador = {
                'nome': data['nome'],
                'cpf': data['cpf'],
                'status': 'ativo'
            }
            
            if not entregadores:
                df = pd.DataFrame([novo_entregador])
            else:
                df = pd.DataFrame(entregadores)
                df = pd.concat([df, pd.DataFrame([novo_entregador])], ignore_index=True)
            
            salvar_entregadores(df)
            log_action('Entregador cadastrado', session.get('username'), f"Nome: {data['nome']}, CPF: {data['cpf']}")
            return jsonify({'status': 'success'})
        
        return jsonify({'status': 'error', 'message': 'Tipo inválido'})
    except Exception as e:
        log_error('Erro ao cadastrar', session.get('username'), str(e))
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/editar/empresa', methods=['POST'])
@admin_required
def api_editar_empresa():
    try:
        data = request.get_json()
        df = pd.DataFrame(carregar_empresas())
        
        # Verifica se a empresa existe
        if data['id'] not in df['nome'].values:
            log_action('Tentativa de edição de empresa - Empresa não encontrada', 
                      session.get('username'), f"ID: {data['id']}")
            return jsonify({'status': 'error', 'message': 'Empresa não encontrada'})
        
        idx = df[df['nome'] == data['id']].index[0]
        
        # Registra os valores antigos para o log
        empresa_antiga = df.iloc[idx].to_dict()
        
        # Atualiza os dados
        df.loc[idx, 'nome'] = data['nome']
        df.loc[idx, 'veiculo'] = data['veiculo']
        df.loc[idx, 'tipo_valor'] = data['tipo_valor']
        df.loc[idx, 'minimo_garantido'] = data['minimo_garantido']
        df.loc[idx, 'taxa_total_cobrada'] = float(data['taxa_total_cobrada'])
        df.loc[idx, 'taxa_total_entregador'] = float(data['taxa_total_entregador'])
        
        # Processa as taxas de fim de semana
        taxa_cobrada_fim_semana = data.get('taxa_total_cobrada_fim_semana')
        taxa_entregador_fim_semana = data.get('taxa_total_entregador_fim_semana')
        
        if taxa_cobrada_fim_semana:
            df.loc[idx, 'taxa_total_cobrada_fim_semana'] = float(taxa_cobrada_fim_semana)
        else:
            df.loc[idx, 'taxa_total_cobrada_fim_semana'] = None
            
        if taxa_entregador_fim_semana:
            df.loc[idx, 'taxa_total_entregador_fim_semana'] = float(taxa_entregador_fim_semana)
        else:
            df.loc[idx, 'taxa_total_entregador_fim_semana'] = None
        
        # Processa os dias diferentes
        dias_diferentes = data.get('dias_diferentes', [])
        if isinstance(dias_diferentes, list):
            df.loc[idx, 'dias_diferentes'] = ','.join(map(str, dias_diferentes))
        else:
            df.loc[idx, 'dias_diferentes'] = ''
        
        # Salva as alterações
        salvar_empresas(df)
        
        # Registra as alterações no log
        alteracoes = []
        for campo in ['nome', 'veiculo', 'tipo_valor', 'minimo_garantido', 'taxa_total_cobrada', 
                     'taxa_total_entregador', 'taxa_total_cobrada_fim_semana', 
                     'taxa_total_entregador_fim_semana', 'dias_diferentes']:
            valor_antigo = str(empresa_antiga.get(campo, ''))
            valor_novo = str(data.get(campo, ''))
            if valor_antigo != valor_novo:
                alteracoes.append(f"{campo}: {valor_antigo} -> {valor_novo}")
        
        log_action('Empresa editada', session.get('username'), 
                  f"Nome: {data['nome']}, Alterações: {', '.join(alteracoes)}")
        return jsonify({'status': 'success'})
    except Exception as e:
        log_error('Erro ao editar empresa', session.get('username'), str(e))
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/editar/entregador', methods=['POST'])
@admin_required
def api_editar_entregador():
    try:
        data = request.get_json()
        
        if not data:
            log_action('Tentativa de edição de entregador - Dados não fornecidos', session.get('username'))
            return jsonify({'status': 'error', 'message': 'Dados não fornecidos'})
            
        if 'id' not in data or 'nome' not in data or 'cpf' not in data:
            log_action('Tentativa de edição de entregador - Dados incompletos', session.get('username'))
            return jsonify({'status': 'error', 'message': 'Dados incompletos'})
        
        df = pd.DataFrame(carregar_entregadores())
        
        # Verifica se o entregador existe
        if data['id'] not in df['nome'].values:
            log_action('Tentativa de edição de entregador - Entregador não encontrado', 
                      session.get('username'), f"ID: {data['id']}")
            return jsonify({'status': 'error', 'message': 'Entregador não encontrado'})
        
        idx = df[df['nome'] == data['id']].index[0]
        
        # Registra os valores antigos para o log
        entregador_antigo = df.iloc[idx].to_dict()
        
        # Atualiza os dados
        df.loc[idx, 'nome'] = data['nome']
        df.loc[idx, 'cpf'] = data['cpf']
        df.loc[idx, 'status'] = 'ativo'
        
        # Registra as alterações no log antes de salvar
        alteracoes = []
        for campo in ['nome', 'cpf']:
            if str(entregador_antigo[campo]) != str(data[campo]):
                alteracoes.append(f"{campo}: {entregador_antigo[campo]} -> {data[campo]}")
        
        log_action('Entregador editado', session.get('username'), 
                  f"Nome: {data['nome']}, Alterações: {', '.join(alteracoes)}")
        
        # Salva as alterações
        salvar_entregadores(df)
        
        return jsonify({'status': 'success'})
    except Exception as e:
        erro = str(e)
        log_error('Erro ao editar entregador', session.get('username'), erro)
        return jsonify({'status': 'error', 'message': f'Erro ao editar entregador: {erro}'}), 500

@app.route('/api/excluir/empresa', methods=['POST'])
@admin_required
def api_excluir_empresa():
    try:
        data = request.get_json()
        nome = data.get('nome')
        
        empresas = carregar_empresas()
        df = pd.DataFrame(empresas)
        
        status_atual = df.loc[df['nome'] == nome, 'status'].iloc[0]
        novo_status = 'inativo' if status_atual == 'ativo' else 'ativo'
        df.loc[df['nome'] == nome, 'status'] = novo_status
        
        salvar_empresas(df)
        log_action('Status da empresa alterado', session.get('username'), 
                  f"Nome: {nome}, Status: {status_atual} -> {novo_status}")
        return jsonify({'status': 'success'})
    except Exception as e:
        log_error('Erro ao alterar status da empresa', session.get('username'), str(e))
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/excluir/entregador', methods=['POST'])
@admin_required
def api_excluir_entregador():
    try:
        data = request.get_json()
        nome = data.get('nome')
        
        if not nome:
            log_action('Tentativa de alterar status do entregador - Nome não fornecido', session.get('username'))
            return jsonify({'status': 'error', 'message': 'Nome não fornecido'})
        
        entregadores = carregar_entregadores()
        df = pd.DataFrame(entregadores)
        
        if nome not in df['nome'].values:
            log_action('Tentativa de alterar status do entregador - Entregador não encontrado', 
                      session.get('username'), nome)
            return jsonify({'status': 'error', 'message': 'Entregador não encontrado'})
        
        status_atual = df.loc[df['nome'] == nome, 'status'].iloc[0]
        novo_status = 'inativo' if status_atual == 'ativo' else 'ativo'
        df.loc[df['nome'] == nome, 'status'] = novo_status
        
        salvar_entregadores(df)
        log_action('Status do entregador alterado', session.get('username'), 
                  f"Nome: {nome}, Status: {status_atual} -> {novo_status}")
        return jsonify({'status': 'success'})
    except Exception as e:
        log_error('Erro ao alterar status do entregador', session.get('username'), str(e))
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
    try:
        df_diarias = carregar_diarias()
        data_inicial = request.args.get('data_inicial')
        data_final = request.args.get('data_final')
        
        data_inicial = datetime.strptime(data_inicial, '%Y-%m-%d').strftime('%Y-%m-%d')
        data_final = datetime.strptime(data_final, '%Y-%m-%d').strftime('%Y-%m-%d')
        
        df_periodo = df_diarias[
            (df_diarias['Data e hora de início'].str[:10] >= data_inicial) & 
            (df_diarias['Data e hora de início'].str[:10] <= data_final)
        ]
        
        output_file = f'escala_diarias_{data_inicial}_a_{data_final}.xlsx'
        df_periodo.to_excel(output_file, index=False)
        
        log_action('Relatório exportado', session.get('username'), 
                  f"Período: {data_inicial} até {data_final}")
        return send_file(output_file, as_attachment=True)
    except Exception as e:
        log_error('Erro ao exportar relatório', session.get('username'), str(e))
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/diarias', methods=['GET'])
def get_diarias():
    try:
        df_diarias = carregar_diarias()
        print(f"Total de diárias carregadas: {len(df_diarias)}")  # Log para debug
        
        if df_diarias.empty:
            print("DataFrame de diárias está vazio")  # Log para debug
            return jsonify([])
            
        # Verifica permissão do usuário atual
        usuario_atual = session.get('username')
        permissao_atual = session.get('permissao')
        print(f"Usuário atual: {usuario_atual}, Permissão: {permissao_atual}")  # Log para debug
        
        # Se for supervisor, filtra apenas suas diárias
        if permissao_atual == 'supervisor':
            print(f"Filtrando diárias para o supervisor: {usuario_atual}")  # Log para debug
            print(f"Valores únicos na coluna usuario_registro: {df_diarias['usuario_registro'].unique()}")  # Log para debug
            df_diarias = df_diarias[df_diarias['usuario_registro'].str.strip() == usuario_atual.strip()]
            print(f"Diárias após filtro: {len(df_diarias)}")  # Log para debug
        
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
            'Taxa mínima entregador',
            'usuario_registro'
        ]
        
        for coluna in colunas_necessarias:
            if coluna not in df_diarias.columns:
                df_diarias[coluna] = ''
        
        # Converte os valores numéricos e substitui NaN por 0
        df_diarias['Taxa total cobrada'] = pd.to_numeric(df_diarias['Taxa total cobrada'], errors='coerce').fillna(0)
        df_diarias['Taxa total entregador'] = pd.to_numeric(df_diarias['Taxa total entregador'], errors='coerce').fillna(0)
        
        # Remove a coluna usuario_registro do resultado final
        colunas_retorno = [col for col in colunas_necessarias if col != 'usuario_registro']
        diarias = df_diarias[colunas_retorno].to_dict('records')
        
        print(f"Total de diárias retornadas: {len(diarias)}")  # Log para debug
        return jsonify(diarias)
        
    except Exception as e:
        print(f"Erro ao obter diárias: {str(e)}")  # Log para debug
        return jsonify([])

def processar_taxas_empresa(empresa, data_inicio):
    try:
        # Converte a data de início para objeto datetime
        data = datetime.strptime(data_inicio, '%Y-%m-%d %H:%M:%S')
        dia_semana = data.weekday()  # 0 = segunda, 6 = domingo
        
        # Verifica se o dia da semana está na lista de dias diferentes
        dias_diferentes = empresa.get('dias_diferentes', [])
        if isinstance(dias_diferentes, str):
            # Se for string, converte para lista de números
            dias_diferentes = [int(d) for d in dias_diferentes.split(',') if d.isdigit()]
        
        if dia_semana in dias_diferentes:
            taxa_total_cobrada = float(empresa.get('taxa_total_cobrada_fim_semana', empresa['taxa_total_cobrada']))
            taxa_total_entregador = float(empresa.get('taxa_total_entregador_fim_semana', empresa['taxa_total_entregador']))
        else:
            taxa_total_cobrada = float(empresa['taxa_total_cobrada'])
            taxa_total_entregador = float(empresa['taxa_total_entregador'])
            
        return {
            'taxa_total_cobrada': taxa_total_cobrada,
            'taxa_total_entregador': taxa_total_entregador,
            'minimo_garantido': empresa['minimo_garantido']
        }
    except Exception as e:
        print(f"Erro ao processar taxas da empresa: {str(e)}")
        return {
            'taxa_total_cobrada': 0.0,
            'taxa_total_entregador': 0.0,
            'minimo_garantido': 'N'
        }

@app.route('/api/diaria', methods=['POST'])
def api_diaria():
    try:
        data = request.get_json()
        
        empresas = pd.DataFrame(carregar_empresas())
        entregadores = pd.DataFrame(carregar_entregadores())
        
        empresa = empresas[empresas['nome'] == data['empresa']].iloc[0]
        entregador = entregadores[entregadores['nome'] == data['entregador']].iloc[0]
        
        data_inicio = datetime.strptime(data['data_inicio'], '%Y-%m-%dT%H:%M')
        data_fim = datetime.strptime(data['data_fim'], '%Y-%m-%dT%H:%M')
        
        # Calcula a diferença de horas se o tipo_valor for 'hora'
        if empresa['tipo_valor'] == 'hora':
            diferenca_horas = (data_fim - data_inicio).total_seconds() / 3600  # Converte para horas
            # Processa as taxas considerando o dia da semana
            taxas = processar_taxas_empresa(empresa, data_inicio.strftime('%Y-%m-%d %H:%M:%S'))
            # Multiplica as taxas pela quantidade de horas
            taxa_total_cobrada = taxas['taxa_total_cobrada'] * diferenca_horas
            taxa_total_entregador = taxas['taxa_total_entregador'] * diferenca_horas
        else:
            # Se não for por hora, usa as taxas normalmente
            taxas = processar_taxas_empresa(empresa, data_inicio.strftime('%Y-%m-%d %H:%M:%S'))
            taxa_total_cobrada = taxas['taxa_total_cobrada']
            taxa_total_entregador = taxas['taxa_total_entregador']
        
        nova_diaria = {
            'Data e hora de início': data_inicio.strftime('%Y-%m-%d %H:%M:%S'),
            'Data e hora de fim': data_fim.strftime('%Y-%m-%d %H:%M:%S'),
            'Empresa': data['empresa'],
            'Tipo Veiculo': data['veiculo'],
            'Entregador': data['entregador'],
            'CPF': entregador['cpf'],
            'Taxa total cobrada': taxa_total_cobrada,
            'Taxa total entregador': taxa_total_entregador,
            'Taxa mínima cobrada': 'S' if taxas['minimo_garantido'] == 'S' else 'N',
            'Taxa mínima entregador': 'S' if taxas['minimo_garantido'] == 'S' else 'N'
        }
        
        df_diarias = carregar_diarias()
        
        if df_diarias.empty:
            df_diarias = pd.DataFrame([nova_diaria])
        else:
            df_diarias = pd.concat([df_diarias, pd.DataFrame([nova_diaria])], ignore_index=True)
        
        if salvar_diarias(df_diarias):
            log_action('Diária registrada', session.get('username'), 
                      f"Empresa: {data['empresa']}, Entregador: {data['entregador']}, "
                      f"Período: {data_inicio} até {data_fim}")
            return jsonify({'status': 'success'})
        else:
            erro_msg = "Erro ao salvar diária no arquivo. Verifique as permissões da pasta 'data'."
            log_error('Erro ao registrar diária', session.get('username'), erro_msg)
            return jsonify({'status': 'error', 'message': erro_msg}), 500
            
    except Exception as e:
        erro_msg = str(e)
        log_error('Erro ao registrar diária', session.get('username'), erro_msg)
        return jsonify({'status': 'error', 'message': erro_msg}), 500

@app.route('/api/empresa', methods=['POST'])
def api_empresa():
    try:
        data = request.get_json()
        
        # Carrega as empresas existentes
        df_empresas = carregar_empresas()
        
        # Verifica se a empresa já existe
        if data['nome'] in df_empresas['nome'].values:
            return jsonify({'status': 'error', 'message': 'Empresa já existe'})
        
        # Cria um novo registro
        nova_empresa = {
            'nome': data['nome'],
            'veiculo': data['veiculo'],
            'tipo_valor': 'unico',  # Mantido para compatibilidade
            'minimo_garantido': data['minimo_garantido'],
            'taxa_total_cobrada': float(data['taxa_total_cobrada']),
            'taxa_total_entregador': float(data['taxa_total_entregador']),
            'taxa_total_cobrada_fim_semana': float(data['taxa_total_cobrada_fim_semana']) if data.get('taxa_total_cobrada_fim_semana') else None,
            'taxa_total_entregador_fim_semana': float(data['taxa_total_entregador_fim_semana']) if data.get('taxa_total_entregador_fim_semana') else None,
            'dias_diferentes': ','.join(map(str, data.get('dias_diferentes', []))),
            'status': 'ativo'
        }
        
        # Adiciona a nova empresa ao DataFrame
        df_empresas = pd.concat([df_empresas, pd.DataFrame([nova_empresa])], ignore_index=True)
        
        # Salva as empresas
        salvar_empresas(df_empresas)
        
        log_action('Empresa cadastrada', session.get('username'), f"Empresa: {data['nome']}")
        return jsonify({'status': 'success'})
    except Exception as e:
        log_error('Erro ao cadastrar empresa', session.get('username'), str(e))
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/empresa/<nome>', methods=['PUT'])
def atualizar_empresa(nome):
    try:
        data = request.get_json()
        df_empresas = carregar_empresas()
        
        # Encontra o índice da empresa
        idx = df_empresas[df_empresas['nome'] == nome].index[0]
        
        # Atualiza os dados da empresa
        df_empresas.at[idx, 'veiculo'] = data['veiculo']
        df_empresas.at[idx, 'minimo_garantido'] = data['minimo_garantido']
        df_empresas.at[idx, 'taxa_total_cobrada'] = float(data['taxa_total_cobrada'])
        df_empresas.at[idx, 'taxa_total_entregador'] = float(data['taxa_total_entregador'])
        df_empresas.at[idx, 'taxa_total_cobrada_fim_semana'] = float(data['taxa_total_cobrada_fim_semana']) if data.get('taxa_total_cobrada_fim_semana') else None
        df_empresas.at[idx, 'taxa_total_entregador_fim_semana'] = float(data['taxa_total_entregador_fim_semana']) if data.get('taxa_total_entregador_fim_semana') else None
        df_empresas.at[idx, 'dias_diferentes'] = ','.join(map(str, data.get('dias_diferentes', [])))
        
        # Salva as alterações
        salvar_empresas(df_empresas)
        
        log_action('Empresa atualizada', session.get('username'), f"Empresa: {nome}")
        return jsonify({'status': 'success'})
    except Exception as e:
        log_error('Erro ao atualizar empresa', session.get('username'), str(e))
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/logs')
@admin_required
def logs():
    return render_template('logs.html', permissao=session.get('permissao'))

@app.route('/api/logs')
@admin_required
def api_logs():
    try:
        # Obtém os parâmetros de filtro
        nivel = request.args.get('nivel', 'todos')
        usuario = request.args.get('usuario', '')
        empresa = request.args.get('empresa', '')
        data_inicial = request.args.get('data_inicial', '')
        data_final = request.args.get('data_final', '')

        # Lê o arquivo de log
        logs = []
        if os.path.exists('logs/sistema.log'):
            with open('logs/sistema.log', 'r', encoding='utf-8') as f:
                for linha in f:
                    try:
                        # Parseia a linha do log
                        partes = linha.strip().split(' - ')
                        if len(partes) >= 3:
                            timestamp = partes[0]
                            level = partes[1]
                            message = ' - '.join(partes[2:])  # Junta o resto da mensagem

                            # Extrai informações adicionais
                            username = None
                            details = None
                            empresa_log = None
                            
                            # Procura por "Usuário:" na mensagem
                            if 'Usuário:' in message:
                                user_part = message.split('Usuário:')[1].split(' - ')[0].strip()
                                username = user_part
                            
                            # Procura por "Detalhes:" na mensagem
                            if 'Detalhes:' in message:
                                details = message.split('Detalhes:')[1].strip()
                                
                                # Procura pela empresa nos detalhes
                                if 'Empresa:' in details:
                                    empresa_log = details.split('Empresa:')[1].split(',')[0].strip()
                                elif 'Nome:' in details:
                                    empresa_log = details.split('Nome:')[1].split(',')[0].strip()

                            # Aplica os filtros
                            if nivel != 'todos' and level != nivel:
                                continue
                                
                            # Filtro de usuário
                            if usuario and (not username or usuario != username):
                                continue
                                
                            # Filtro de empresa
                            if empresa and empresa_log:
                                # Remove possíveis prefixos
                                empresa_log = empresa_log.replace('Nome: ', '').replace('Empresa: ', '')
                                if empresa != empresa_log:
                                    continue

                            # Adiciona o log à lista
                            log_entry = {
                                'timestamp': timestamp,
                                'level': level,
                                'message': message,
                                'username': username,
                                'details': details,
                                'empresa': empresa_log,
                                'raw': linha.strip()
                            }
                            logs.append(log_entry)
                    except Exception as e:
                        print(f"Erro ao processar linha do log: {str(e)}")
                        continue

        # Ordena os logs por data (mais recentes primeiro)
        logs.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # Obtém lista de usuários dos logs
        usuarios_logs = list(set(log['username'] for log in logs if log['username']))
        
        # Obtém lista de usuários cadastrados
        usuarios_cadastrados = []
        if os.path.exists(USUARIOS_FILE):
            df_usuarios = pd.read_csv(USUARIOS_FILE)
            usuarios_cadastrados = df_usuarios['username'].tolist()
        
        # Combina as duas listas e remove duplicatas
        usuarios = list(set(usuarios_logs + usuarios_cadastrados))
        usuarios.sort()  # Ordena alfabeticamente
        
        # Obtém lista de empresas dos logs
        empresas_logs = list(set(log['empresa'] for log in logs if log['empresa']))
        
        # Obtém lista de empresas cadastradas
        empresas_cadastradas = []
        if os.path.exists(EMPRESAS_FILE):
            df_empresas = pd.read_csv(EMPRESAS_FILE)
            empresas_cadastradas = df_empresas['nome'].tolist()
        
        # Combina as duas listas e remove duplicatas
        empresas = list(set(empresas_logs + empresas_cadastradas))
        empresas.sort()  # Ordena alfabeticamente
        
        return jsonify({
            'logs': logs,
            'usuarios': usuarios,
            'empresas': empresas
        })
    except Exception as e:
        log_error('Erro ao carregar logs', session.get('username'), str(e))
        return jsonify({'error': str(e)}), 500

def log_action(action, username, details=None):
    """
    Registra uma ação no log do sistema
    """
    try:
        message = f"Ação: {action}"
        if username:
            message += f" - Usuário: {username}"
        if details:
            message += f" - Detalhes: {details}"
        logger.info(message)
    except Exception as e:
        print(f"Erro ao registrar log: {str(e)}")

def log_error(error, username, details=None):
    """
    Registra um erro no log do sistema
    """
    try:
        message = f"Erro: {error}"
        if username:
            message += f" - Usuário: {username}"
        if details:
            message += f" - Detalhes: {details}"
        logger.error(message)
    except Exception as e:
        print(f"Erro ao registrar log de erro: {str(e)}")

@app.route('/api/empresas/filtro', methods=['GET'])
def get_empresas_filtro():
    try:
        df_empresas = pd.DataFrame(carregar_empresas())
        
        # Se for supervisor, filtra apenas empresas vinculadas
        if session.get('permissao') == 'supervisor':
            # Carrega usuários para verificar vinculações
            usuarios = carregar_usuarios()
            usuario_atual = next((u for u in usuarios if u['username'] == session.get('username')), None)
            
            if usuario_atual and usuario_atual['empresas_vinculadas']:
                # Filtra apenas empresas vinculadas ao supervisor
                df_empresas = df_empresas[df_empresas['nome'].isin(usuario_atual['empresas_vinculadas'])]
        
        # Filtra apenas empresas ativas
        df_empresas = df_empresas[df_empresas['status'] == 'ativo']
        
        # Retorna lista de empresas
        empresas = df_empresas['nome'].tolist()
        return jsonify(empresas)
        
    except Exception as e:
        print(f"Erro ao carregar empresas para filtro: {str(e)}")
        return jsonify([])

if __name__ == '__main__':
    app.run(debug=True) 