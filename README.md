# Sistema de Gerenciamento de Entregadores

Sistema web para gerenciamento de entregadores e empresas de delivery, desenvolvido com Python (Flask) e interface responsiva com Bootstrap.

## Funcionalidades

- Cadastro de Empresas
  - Nome da empresa
  - Tipo de veículo
- Cadastro de Entregadores
  - Nome completo
  - CPF
- Registro de Diárias
  - Data e hora de início/fim
  - Empresa e entregador
  - Tipo de veículo
  - Taxas (total e mínima)
- Exportação para Excel
- Interface responsiva
- Tratamento de caracteres especiais
- Dropdowns com autopreenchimento
- Tabelas de visualização de dados

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
├── app.py              # Aplicação principal Flask
├── requirements.txt    # Dependências do projeto
├── dados.csv          # Arquivo de armazenamento de dados
└── templates/
    └── index.html     # Interface do usuário
```

## Tecnologias Utilizadas

- Frontend:
  - HTML5
  - CSS3 (Bootstrap 5)
  - JavaScript (jQuery, Select2)
- Backend:
  - Python 3.7+
  - Flask
  - Pandas
  - OpenPyXL

## Contribuição

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request 