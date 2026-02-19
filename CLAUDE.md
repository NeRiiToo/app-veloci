# CLAUDE.md - Sistema de Gerenciamento de Escalas (SGE) Veloci

## Projeto

Sistema web para gerenciamento de escalas de entregadores da Veloci. Controla cadastro de empresas, entregadores, diarias (turnos) e exportacao de relatorios.

## Stack Atual (MVP)

- **Backend**: Flask 3.0.2 (Python)
- **Frontend**: Bootstrap 5 + jQuery + AJAX
- **Templates**: Jinja2
- **Dados**: CSV (usuarios, empresas, entregadores) + Excel/XLSX (diarias)
- **Servidor**: Waitress (WSGI) na porta 5000
- **Concorrencia**: FileLock para acesso a arquivos

## Stack Alvo (Producao - ver PRD.md)

- **Backend**: Django
- **Banco**: PostgreSQL
- **Frontend**: Bootstrap 5 + HTMX
- **Infra**: Docker + Nginx

## Estrutura do Projeto

```
app.py              # Aplicacao principal Flask (1500+ linhas) - entry point
iniciar.py          # Script de inicializacao com Waitress
usuarios.csv        # Base de usuarios (username, senha SHA-256, permissao, empresas_vinculadas)
empresas.csv        # Base de empresas (nome, veiculo, taxas, status)
entregadores.csv    # Base de entregadores (nome, cpf, status)
data/diarias.xlsx   # Registros de diarias/escalas
templates/          # Templates Jinja2 (login, index, cadastros, cadastro_usuario, logs)
static/css/         # CSS customizado (cor primaria: #1B3B6F)
logs/sistema.log    # Log rotativo (10MB, 5 backups)
backup/             # Backups automaticos dos CSVs
```

## Comandos

```bash
# Iniciar o servidor
python iniciar.py

# Ou diretamente
python app.py

# Instalar dependencias
pip install -r requirements.txt
```

## Arquitetura da Aplicacao

### Autenticacao
- Login por sessao Flask
- Senhas hasheadas com SHA-256
- Dois niveis: `ADM` (acesso total) e `supervisor` (acesso restrito)
- Decorators: `@login_required`, `@admin_required`

### Rotas Principais
- `GET /` - Dashboard principal (index.html)
- `GET /cadastros` - Tela de cadastros (cadastros.html)
- `GET /cadastro_usuario` - Gestao de usuarios (admin only)
- `GET /logs` - Visualizacao de logs

### API REST (prefixo /api/)
- `GET /api/empresas`, `/api/empresas/ativas`, `/api/empresas/filtro`
- `GET /api/entregadores`, `/api/entregadores/ativos`
- `GET /api/diarias` - Listar diarias
- `POST /api/diaria` - Criar diaria
- `POST /api/diaria/editar` - Editar diaria
- `POST /api/diaria/remover` - Remover diaria
- `POST /api/cadastrar` - Cadastrar entregador
- `POST /api/empresa` - Criar empresa
- `GET /api/exportar` - Exportar CSV

### Dados
- Empresas tem taxas diferenciadas para dias uteis vs fim de semana
- Tipo de valor: `unico` (valor fixo) ou `hora` (por hora)
- Entregadores identificados por CPF (unique)
- Diarias vinculam entregador + empresa + horario + valor

## Convencoes

- Idioma do codigo: portugues (nomes de variaveis, funcoes, modelos)
- Idioma da interface: portugues brasileiro
- Formato de data: DD/MM/AAAA
- Moeda: BRL (R$)
- Backups automaticos antes de modificacoes em CSV
- Todas as acoes do usuario sao logadas em sistema.log

## Regras de Negocio Importantes

1. Entregador nao pode ter duas escalas no mesmo horario
2. Valor da diaria depende do dia da semana (util vs FDS) e tipo da empresa
3. Empresas e entregadores tem status ativo/inativo (soft delete)
4. Supervisores so veem empresas vinculadas ao seu perfil
5. Exclusao de empresa/entregador e logica (muda status para inativo)
