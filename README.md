# Sistema de Gerenciamento de Escalas - Veloci

Sistema web para gerenciamento de entregadores e empresas de delivery, desenvolvido com Python (Flask) e interface responsiva com Bootstrap.

## Funcionalidades

### Gestão de Usuários
- Cadastro de usuários com diferentes níveis de permissão:
  - Administrador (ADM): Acesso total ao sistema
  - Supervisor: Acesso limitado às empresas vinculadas
- Login e controle de acesso com sessão
- Vinculação de múltiplas empresas aos usuários supervisores
- Alteração de senha
- Exclusão de usuários (com proteção para último administrador)

### Gestão de Empresas
- Cadastro completo de empresas com:
  - Nome da empresa
  - Tipo de veículo
  - Tipo de valor (Único/Por Hora)
  - Mínimo garantido (Sim/Não)
  - Taxa total cobrada (dias úteis)
  - Taxa total entregador (dias úteis)
  - Taxa total cobrada (fim de semana)
  - Taxa total entregador (fim de semana)
  - Dias específicos com valores diferentes
  - Status (Ativo/Inativo)
- Edição de todas as informações da empresa
- Ativação/Desativação de empresas
- Visualização em tabela com filtros

### Gestão de Entregadores
- Cadastro de entregadores com:
  - Nome completo
  - CPF (com validação)
  - Status (Ativo/Inativo)
- Edição de dados do entregador
- Ativação/Desativação de entregadores
- Visualização em tabela com filtros

### Registro de Diárias
- Registro completo de diárias com:
  - Data e hora de início/fim
  - Seleção de empresa e entregador
  - Tipo de veículo
  - Taxas aplicadas (normal ou fim de semana)
  - Cálculo automático baseado no tipo de valor
- Exportação de relatórios por período
- Validações de horários e disponibilidade

### Sistema de Logs
- Registro detalhado de todas as ações no sistema:
  - Login/Logout de usuários
  - Cadastros e alterações de empresas
  - Cadastros e alterações de entregadores
  - Registro de diárias
  - Exportação de relatórios
- Filtros avançados de logs por:
  - Nível (Info, Erro, Aviso)
  - Usuário
  - Empresa
  - Período (Data inicial/final)
- Visualização colorida por tipo de log
- Exportação de logs filtrados

### Interface e Usabilidade
- Design responsivo com Bootstrap 5
- Menus dinâmicos baseados na permissão do usuário
- Dropdowns aprimorados com Select2
- Validações em tempo real
- Mensagens de feedback para todas as ações
- Modais para edição rápida
- Tabelas interativas com ordenação

## Requisitos Técnicos

### Frontend
- HTML5
- CSS3 (Bootstrap 5)
- JavaScript
  - jQuery 3.6.0
  - Select2 4.1.0
  - AJAX para requisições assíncronas
  - Validações client-side

### Backend
- Python 3.7+
- Flask (framework web)
- Bibliotecas Python:
  - pandas: manipulação de dados
  - logging: sistema de logs
  - werkzeug: segurança e utilitários
  - datetime: manipulação de datas

### Armazenamento
- Arquivos CSV para persistência:
  - usuarios.csv: dados dos usuários
  - empresas.csv: dados das empresas
  - entregadores.csv: dados dos entregadores
  - registros.csv: registro de diárias
- Sistema de logs:
  - Arquivo sistema.log
  - Rotação automática de logs

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

3. Configure as permissões dos diretórios:
```bash
chmod 755 logs/
chmod 644 *.csv
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
├── static/                # Arquivos estáticos
│   ├── css/              # Estilos CSS
│   └── js/               # Scripts JavaScript
├── templates/            # Templates HTML
│   ├── index.html        # Página principal
│   ├── login.html        # Página de login
│   ├── cadastros.html    # Gestão de cadastros
│   ├── cadastro_usuario.html  # Gestão de usuários
│   └── logs.html         # Visualização de logs
├── usuarios.csv          # Dados dos usuários
├── empresas.csv         # Dados das empresas
├── entregadores.csv     # Dados dos entregadores
├── registros.csv        # Registro de diárias
└── logs/
    └── sistema.log      # Logs do sistema
```

## Segurança

- Autenticação de usuários com sessão
- Controle de acesso baseado em permissões
- Proteção contra CSRF
- Validação de dados em ambos os lados
- Sanitização de inputs
- Logs detalhados de todas as ações
- Backup automático dos arquivos CSV

## Manutenção

- Logs rotacionados automaticamente
- Backup diário dos arquivos CSV
- Validação periódica de integridade
- Limpeza automática de sessões expiradas

## Suporte

Para suporte ou dúvidas, entre em contato:
- Email: [EMAIL_SUPORTE]
- Telefone: [TELEFONE_SUPORTE]

## Licença

Este projeto está sob a licença [TIPO_LICENCA].

## Contribuição

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/NovaFuncionalidade`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/NovaFuncionalidade`)
5. Abra um Pull Request 