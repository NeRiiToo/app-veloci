# Sistema de Gerenciamento de Escalas - Veloci

Sistema web para gerenciamento de escalas de entregadores da Veloci. Controla cadastro de empresas, entregadores, diarias (turnos) e exportacao de relatorios.

## Stack

- **Backend**: Django 5.1 (Python 3.12)
- **Banco de dados**: PostgreSQL 16
- **Frontend**: Bootstrap 5 + jQuery + Select2 + AJAX
- **Templates**: Jinja2/Django Templates
- **Servidor**: Gunicorn (WSGI)
- **Infra**: Docker + Docker Compose
- **Arquivos estaticos**: WhiteNoise

## Funcionalidades

### Gestao de Usuarios
- Cadastro com niveis de permissao: **ADM** (acesso total) e **Supervisor** (acesso restrito)
- Login e controle de acesso com sessao Django
- Vinculacao de multiplas empresas aos supervisores
- Alteracao de senha e exclusao (com protecao para ultimo administrador)

### Gestao de Empresas
- Cadastro com nome, tipo de veiculo, tipo de valor (unico/por hora), minimo garantido
- Taxas diferenciadas para dias uteis e fim de semana
- Dias especificos com valores diferentes
- Ativacao/desativacao (soft delete)

### Gestao de Entregadores
- Cadastro com nome e CPF (unico)
- Importacao em massa via CSV
- Ativacao/desativacao (soft delete)

### Registro de Diarias (Escalas)
- Registro com data/hora de inicio e fim, empresa e entregador
- Calculo automatico de taxas baseado no tipo de valor e dia da semana
- Validacao de conflito de horario por entregador
- Validacao de periodo (minimo 30min, maximo 8h)
- Exportacao de relatorios por periodo em CSV

### Sistema de Logs
- Registro de todas as acoes do usuario no banco de dados (tabela `core_logsistema`)
- Filtros por nivel (Info, Erro, Aviso), usuario, empresa e periodo
- Visualizacao colorida por tipo de log

## Estrutura do Projeto

```
manage.py                   # Entry point Django
veloci/                     # Configuracao do projeto Django
    settings.py
    urls.py
    wsgi.py
core/                       # App: autenticacao, empresas, entregadores, logs
    models.py               # Empresa, Entregador, PerfilUsuario, LogSistema
    views.py                # Views de auth, cadastros e APIs
    urls.py
    admin.py
    management/             # Comandos customizados (ensure_admin)
    migrations/
operacao/                   # App: escalas/diarias
    models.py               # Escala
    views.py                # APIs de diarias, exportacao, logs
    services.py             # Logica de negocio (criar/editar/remover escala)
    selectors.py            # Queries e exportacao CSV
    urls.py
    admin.py
    migrations/
templates/                  # Templates HTML
    base.html
    login.html
    index.html              # Dashboard principal
    cadastros.html          # Gestao de empresas e entregadores
    cadastro_usuario.html   # Gestao de usuarios (admin)
    logs.html               # Visualizacao de logs
static/
    css/                    # Estilos (cor primaria: #1B3B6F)
    js/                     # Scripts (index, cadastros, cadastro_usuario, logs)
Dockerfile
docker-compose.yml
requirements.txt
```

## Instalacao e Execucao

### Com Docker (recomendado)

```bash
docker compose up --build
```

O sistema estara disponivel em `http://localhost:8000`. O banco PostgreSQL, migracoes e usuario admin sao configurados automaticamente.

### Sem Docker (desenvolvimento local)

1. Crie e ative um ambiente virtual:
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows
```

2. Instale as dependencias:
```bash
pip install -r requirements.txt
```

3. Configure as variaveis de ambiente:
```bash
export DATABASE_URL=postgres://usuario:senha@localhost:5432/veloci
export DJANGO_SECRET_KEY=sua-chave-secreta
export DJANGO_DEBUG=True
```

4. Rode as migracoes e inicie o servidor:
```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Variaveis de Ambiente

| Variavel | Descricao | Padrao |
|---|---|---|
| `DATABASE_URL` | Connection string do PostgreSQL | — |
| `DJANGO_SECRET_KEY` | Chave secreta do Django | — |
| `DJANGO_DEBUG` | Modo debug | `False` |

## Dependencias

```
django==5.1.5
psycopg2-binary==2.9.9
gunicorn==21.2.0
dj-database-url==2.1.0
whitenoise==6.8.2
```

## Seguranca

- Autenticacao com sessao Django
- Controle de acesso por decorators (`@login_required`, `@admin_required`)
- Supervisores so acessam empresas vinculadas ao seu perfil
- Protecao CSRF em todos os formularios
- Auditoria completa de acoes no banco de dados
