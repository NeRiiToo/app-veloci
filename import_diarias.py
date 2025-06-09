import pandas as pd
import re
from datetime import datetime

# Função para extrair informações da linha de log
def parse_log_line(line):
    # Regex para extrair os detalhes da diária
    pattern = r'Empresa: (.*?), Entregador: (.*?), Período: (.*?) até (.*?), Taxa cobrada: (.*?), Taxa entregador: (.*?)$'
    match = re.search(pattern, line)
    
    if match:
        empresa, entregador, data_inicio, data_fim, taxa_cobrada, taxa_entregador = match.groups()
        
        # Converter strings de data para objetos datetime
        data_inicio = datetime.strptime(data_inicio.strip(), '%Y-%m-%d %H:%M:%S')
        data_fim = datetime.strptime(data_fim.strip(), '%Y-%m-%d %H:%M:%S')
        
        # Converter taxas para float
        taxa_cobrada = float(taxa_cobrada)
        taxa_entregador = float(taxa_entregador)
        
        return {
            'empresa': empresa.strip(),
            'entregador': entregador.strip(),
            'data_inicio': data_inicio,
            'data_fim': data_fim,
            'taxa_cobrada': taxa_cobrada,
            'taxa_entregador': taxa_entregador
        }
    return None

# Carregar dados dos entregadores e empresas
entregadores_df = pd.read_csv('entregadores.csv')
empresas_df = pd.read_csv('empresas.csv')

# Criar dicionário de CPF por nome de entregador
cpf_por_entregador = dict(zip(entregadores_df['nome'], entregadores_df['cpf']))

# Ler o arquivo de log
diarias = []
with open('logs/sistema.log', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    
    # Começar da linha 1033
    for line in lines[1032:]:  # índice 1032 corresponde à linha 1033
        if 'Ação: Diária registrada' in line and 'ERROR' not in line:
            dados = parse_log_line(line)
            if dados:
                # Adicionar CPF do entregador
                cpf = cpf_por_entregador.get(dados['entregador'])
                if cpf:
                    dados['cpf_entregador'] = cpf
                diarias.append(dados)

# Criar DataFrame com as diárias
df_diarias = pd.DataFrame(diarias)

# Tentar carregar diárias existentes
try:
    existing_df = pd.read_excel('data/diarias.xlsx')
    # Concatenar com as novas diárias
    df_diarias = pd.concat([existing_df, df_diarias], ignore_index=True)
except:
    pass  # Se o arquivo não existir, usar apenas as novas diárias

# Salvar no arquivo Excel
df_diarias.to_excel('data/diarias.xlsx', index=False)

print(f"Importação concluída. {len(diarias)} diárias foram processadas.") 