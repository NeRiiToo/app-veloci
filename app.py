from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
from datetime import datetime
import os
import io

app = Flask(__name__)

# Configuração dos arquivos de dados
DADOS_FILE = 'dados.csv'
ESCALA_FILE = 'modelo escala.xlsx'
DIARIAS_FILE = 'diarias.xlsx'

def carregar_dados():
    try:
        if os.path.exists(DADOS_FILE):
            df = pd.read_csv(DADOS_FILE)
            # Define os tipos de dados corretamente
            df['taxa_total_cobrada'] = pd.to_numeric(df['taxa_total_cobrada'], errors='coerce').fillna(0)
            df['taxa_total_entregador'] = pd.to_numeric(df['taxa_total_entregador'], errors='coerce').fillna(0)
            df['cpf'] = df['cpf'].astype(str)
            # Garante que todas as colunas existam
            colunas_padrao = ['tipo', 'nome', 'cpf', 'veiculo', 'tipo_valor', 'minimo_garantido', 'taxa_total_cobrada', 'taxa_total_entregador', 'status']
            for coluna in colunas_padrao:
                if coluna not in df.columns:
                    df[coluna] = ''
            # Define status como 'ativo' para registros sem status
            df.loc[df['status'] == '', 'status'] = 'ativo'
            return df
    except Exception as e:
        print(f"Erro ao carregar dados: {str(e)}")
    return pd.DataFrame(columns=['tipo', 'nome', 'cpf', 'veiculo', 'tipo_valor', 'minimo_garantido', 'taxa_total_cobrada', 'taxa_total_entregador', 'status'])

def salvar_dados(df):
    # Converte os tipos de dados antes de salvar
    df['taxa_total_cobrada'] = pd.to_numeric(df['taxa_total_cobrada'], errors='coerce')
    df['taxa_total_entregador'] = pd.to_numeric(df['taxa_total_entregador'], errors='coerce')
    df['cpf'] = df['cpf'].astype(str)
    df.to_csv(DADOS_FILE, index=False)

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
def index():
    return render_template('index.html')

@app.route('/cadastros')
def cadastros():
    return render_template('cadastros.html')

@app.route('/api/empresas', methods=['GET'])
def get_empresas():
    try:
        df = carregar_dados()
        # Filtra apenas empresas ativas
        empresas = df[(df['tipo'] == 'empresa') & (df['status'] == 'ativo')].fillna('').to_dict('records')
        for empresa in empresas:
            empresa['taxa_total_cobrada'] = float(empresa.get('taxa_total_cobrada', 0))
            empresa['taxa_total_entregador'] = float(empresa.get('taxa_total_entregador', 0))
        return jsonify(empresas)
    except Exception as e:
        print(f"Erro ao obter empresas: {str(e)}")
        return jsonify([])

@app.route('/api/entregadores', methods=['GET'])
def get_entregadores():
    df = carregar_dados()
    # Filtra apenas entregadores ativos
    entregadores = df[(df['tipo'] == 'entregador') & (df['status'] == 'ativo')][['nome', 'cpf']].to_dict('records')
    return jsonify(entregadores)

@app.route('/api/cadastrar', methods=['POST'])
def cadastrar():
    try:
        dados = request.json
        df = carregar_dados()
        
        # Garante que o mínimo garantido seja S ou N
        minimo_garantido = dados.get('minimo_garantido', '')
        if minimo_garantido.lower() == 'sim':
            minimo_garantido = 'S'
        elif minimo_garantido.lower() == 'não' or minimo_garantido.lower() == 'nao':
            minimo_garantido = 'N'
        
        novo_registro = pd.DataFrame([{
            'tipo': dados['tipo'],
            'nome': dados['nome'],
            'cpf': str(dados.get('cpf', '')),
            'veiculo': dados.get('veiculo', ''),
            'tipo_valor': dados.get('tipo_valor', ''),
            'minimo_garantido': minimo_garantido,
            'taxa_total_cobrada': float(dados.get('taxa_total_cobrada', 0)),
            'taxa_total_entregador': float(dados.get('taxa_total_entregador', 0)),
            'status': 'ativo'
        }])
        
        df = pd.concat([df, novo_registro], ignore_index=True)
        salvar_dados(df)
        return jsonify({'status': 'success'})
    except Exception as e:
        print(f"Erro ao cadastrar: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/diaria', methods=['POST'])
def registrar_diaria():
    dados = request.json
    df_diarias = carregar_diarias()
    
    # Busca o CPF do entregador e as informações da empresa no cadastro
    df_entregadores = carregar_dados()
    entregador_info = df_entregadores[
        (df_entregadores['tipo'] == 'entregador') & 
        (df_entregadores['nome'] == dados['entregador'])
    ].iloc[0]
    
    empresa_info = df_entregadores[
        (df_entregadores['tipo'] == 'empresa') & 
        (df_entregadores['nome'] == dados['empresa'])
    ].iloc[0]
    
    # Formata as datas para o padrão aaaa-mm-dd hh:mm:ss
    data_inicio = datetime.strptime(dados['data_inicio'], '%Y-%m-%dT%H:%M').strftime('%Y-%m-%d %H:%M:%S')
    data_fim = datetime.strptime(dados['data_fim'], '%Y-%m-%dT%H:%M').strftime('%Y-%m-%d %H:%M:%S')
    
    # Calcula as taxas baseado no tipo de valor
    if empresa_info['tipo_valor'] == 'unico':
        taxa_total_cobrada = empresa_info['taxa_total_cobrada']
        taxa_total_entregador = empresa_info['taxa_total_entregador']
    else:  # valor por hora
        # Calcula a diferença em horas
        inicio = datetime.strptime(data_inicio, '%Y-%m-%d %H:%M:%S')
        fim = datetime.strptime(data_fim, '%Y-%m-%d %H:%M:%S')
        diferenca = fim - inicio
        horas = diferenca.total_seconds() / 3600
        
        # Calcula as taxas
        taxa_total_cobrada = float(empresa_info['taxa_total_cobrada']) * horas
        taxa_total_entregador = float(empresa_info['taxa_total_entregador']) * horas
    
    novo_registro = pd.DataFrame([{
        'Data e hora de início': data_inicio,
        'Data e hora de fim': data_fim,
        'Empresa': dados['empresa'],
        'Tipo Veiculo': dados['veiculo'],
        'Entregador': dados['entregador'],
        'CPF': entregador_info['cpf'],
        'Taxa total cobrada': taxa_total_cobrada,
        'Taxa total entregador': taxa_total_entregador,
        'Taxa mínima cobrada': empresa_info['minimo_garantido'],
        'Taxa mínima entregador': empresa_info['minimo_garantido']
    }])
    
    # Adiciona o novo registro à planilha de diárias
    df_diarias = pd.concat([df_diarias, novo_registro], ignore_index=True)
    salvar_diarias(df_diarias)
    
    return jsonify({'status': 'success'})

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
            'Taxa mínima cobrada'
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

@app.route('/api/editar/empresa', methods=['POST'])
def editar_empresa():
    dados = request.get_json()
    try:
        df = carregar_dados()
        
        # Encontra o índice da empresa pelo nome antigo e tipo 'empresa'
        idx = df[(df['nome'] == dados['id']) & (df['tipo'] == 'empresa')].index[0]
        
        # Atualiza os dados
        df.loc[idx, 'nome'] = dados['nome']
        df.loc[idx, 'veiculo'] = dados['veiculo']
        df.loc[idx, 'tipo_valor'] = dados['tipo_valor']
        df.loc[idx, 'minimo_garantido'] = dados['minimo_garantido']
        df.loc[idx, 'taxa_total_cobrada'] = float(dados['taxa_total_cobrada'])
        df.loc[idx, 'taxa_total_entregador'] = float(dados['taxa_total_entregador'])
        
        # Salva os dados atualizados
        df.to_csv('dados.csv', index=False)
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/excluir/empresa', methods=['POST'])
def excluir_empresa():
    dados = request.get_json()
    try:
        df = carregar_dados()
        
        # Marca a empresa como excluída ao invés de remover
        idx = df[(df['nome'] == dados['nome']) & (df['tipo'] == 'empresa')].index[0]
        df.loc[idx, 'status'] = 'excluido'
        
        # Salva os dados atualizados
        salvar_dados(df)
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/editar/entregador', methods=['POST'])
def editar_entregador():
    dados = request.get_json()
    try:
        df = carregar_dados()
        
        # Encontra o índice do entregador pelo nome antigo e tipo 'entregador'
        idx = df[(df['nome'] == dados['id']) & (df['tipo'] == 'entregador')].index[0]
        
        # Atualiza os dados
        df.loc[idx, 'nome'] = dados['nome']
        df.loc[idx, 'cpf'] = str(dados['cpf'])
        
        # Salva os dados atualizados
        df.to_csv('dados.csv', index=False)
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/excluir/entregador', methods=['POST'])
def excluir_entregador():
    dados = request.get_json()
    try:
        df = carregar_dados()
        
        # Marca o entregador como excluído ao invés de remover
        idx = df[(df['nome'] == dados['nome']) & (df['tipo'] == 'entregador')].index[0]
        df.loc[idx, 'status'] = 'excluido'
        
        # Salva os dados atualizados
        salvar_dados(df)
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/exportar')
def exportar_diarias():
    try:
        # Obtém os parâmetros da query string
        data_inicial = request.args.get('data_inicial')
        data_final = request.args.get('data_final')
        empresas = request.args.get('empresas', '').split(',')

        if not data_inicial or not data_final:
            return jsonify({'status': 'error', 'message': 'Datas não fornecidas'}), 400

        # Carrega os dados
        df_diarias = carregar_diarias()
        
        # Converte as datas para datetime
        df_diarias['Data e hora de início'] = pd.to_datetime(df_diarias['Data e hora de início'])
        df_diarias['Data e hora de fim'] = pd.to_datetime(df_diarias['Data e hora de fim'])
        
        # Converte as datas do filtro para datetime
        data_inicial = pd.to_datetime(data_inicial)
        data_final = pd.to_datetime(data_final + ' 23:59:59')
        
        # Filtra as diárias pelo período
        df_filtrado = df_diarias[
            (df_diarias['Data e hora de início'].dt.date >= data_inicial.date()) &
            (df_diarias['Data e hora de fim'].dt.date <= data_final.date())
        ]

        # Filtra por empresas se houver empresas selecionadas
        if empresas and empresas[0]:  # Verifica se há empresas selecionadas
            df_filtrado = df_filtrado[df_filtrado['Empresa'].isin(empresas)]

        if df_filtrado.empty:
            return jsonify({'status': 'error', 'message': 'Nenhuma diária encontrada no período'}), 404

        # Cria um buffer para salvar o arquivo Excel
        output = io.BytesIO()
        
        # Salva o DataFrame filtrado no buffer
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_filtrado.to_excel(writer, index=False, sheet_name='Diárias')
        
        output.seek(0)
        
        # Define o nome do arquivo com a data atual
        hoje = datetime.now().strftime('%Y%m%d')
        nome_arquivo = f'diarias_{hoje}.xlsx'

        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=nome_arquivo
        )

    except Exception as e:
        print(f'Erro ao exportar diárias: {str(e)}')
        return jsonify({'status': 'error', 'message': 'Erro ao exportar diárias'}), 500

if __name__ == '__main__':
    app.run(debug=True) 