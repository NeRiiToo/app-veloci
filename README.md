# Sistema de Gerenciamento de Entregadores

Sistema web para gerenciamento de entregadores e empresas de delivery, desenvolvido com Python (Flask) e interface responsiva com Bootstrap.

## Funcionalidades

### Gestão de Usuários
- Cadastro de usuários com diferentes níveis de permissão (ADM/Supervisor)
- Login e controle de acesso
- Vinculação de empresas aos usuários supervisores

### Gestão de Empresas
- Cadastro de empresas com:
  - Nome da empresa
  - Tipo de veículo
  - Tipo de valor (Único/Variável)
  - Mínimo garantido
  - Taxa total cobrada
  - Taxa total entregador
  - Status (Ativo/Inativo)

### Gestão de Entregadores
- Cadastro de entregadores com:
  - Nome completo
  - CPF
  - Status (Ativo/Inativo)

### Registro de Diárias
- Data e hora de início/fim
- Empresa e entregador
- Tipo de veículo
- Taxas (total e mínima)
- Exportação de relatórios por período

### Recursos Adicionais
- Interface responsiva com Bootstrap
- Sistema de logs para todas as ações
- Tratamento de caracteres especiais
- Dropdowns com Select2 para melhor usabilidade
- Tabelas de visualização de dados
- Validações de dados e permissões

## Requisitos

- Python 3.7 ou superior
- pip (gerenciador de pacotes Python)

## Instalação

1. Clone o repositório:
```bash
git clone [URL_DO_REPOSITORIO]
cd [NOME_DO_DIRETORIO]
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

## Executando o Sistema

1. Inicie o servidor Flask:
```bash
python app.py
```

2. Acesse o sistema no navegador:
```
http://localhost:5000
```

## Estrutura do Projeto

```
.
├── app.py                  # Aplicação principal Flask
├── requirements.txt        # Dependências do projeto
├── usuarios.csv           # Dados dos usuários
├── empresas.csv          # Dados das empresas
├── entregadores.csv      # Dados dos entregadores
├── registros.csv         # Registro de diárias
├── logs/
│   └── sistema.log       # Logs do sistema
└── templates/
    ├── login.html        # Página de login
    ├── index.html        # Página principal
    ├── cadastros.html    # Gestão de cadastros
    └── cadastro_usuario.html  # Gestão de usuários
```

## Tecnologias Utilizadas

### Frontend
- HTML5
- CSS3 (Bootstrap 5)
- JavaScript
  - jQuery
  - Select2 (para dropdowns aprimorados)
  - AJAX para requisições assíncronas

### Backend
- Python 3.7+
- Flask (framework web)
- Pandas (manipulação de dados)
- Logging (sistema de logs)

### Armazenamento
- Arquivos CSV para persistência de dados
- Sistema de logs com rotação de arquivos

## Segurança
- Controle de sessão
- Validação de permissões
- Registro de todas as ações no sistema
- Proteção contra acessos não autorizados

## Contribuição

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/NovaFuncionalidade`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/NovaFuncionalidade`)
5. Abra um Pull Request 