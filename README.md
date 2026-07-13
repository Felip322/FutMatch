# FutMatch

FutMatch é uma aplicação web Flask para equipes, organizadores e donos de quadras de futsal. O MVP atual foca em cadastro de times, feed social com imagens, curtidas e comentários AJAX, selos/conquistas automáticas, perfil público compartilhável, propostas diretas de amistoso, seleção de quadras cadastradas, busca por proximidade, bloqueio de conflito de horário na mesma quadra, confirmação de placar com comprovante, rankings por período, estatísticas por temporada, notificações e painel administrativo com denúncias, moderação de mídia e controle de badges.

## Tecnologias

Python 3.12, Flask, Flask-SQLAlchemy, Flask-Login, Flask-WTF, SQLite, Jinja2, HTML5, CSS3, JavaScript puro, Werkzeug, Bootstrap Icons, Leaflet/OpenStreetMap, Chart.js e pytest.

## Instalar

```bash
python -m venv venv
```

Windows:

```bash
venv\Scripts\activate
```

Linux:

```bash
source venv/bin/activate
```

```bash
pip install -r requirements.txt
copy .env.example .env
python scripts/seed_database.py
python run.py
```

## Credenciais de demonstracao

Administrador: `admin@futmatch.local` / `Admin123!`

Usuário: `usuario@futmatch.local` / `Usuario123!`

## Testes

```bash
pytest
```

## Estrutura

- `app/models`: modelos SQLAlchemy.
- `app/routes`: blueprints e APIs internas.
- `app/forms`: formularios WTForms com CSRF.
- `app/services`: Fair Play, notificacoes e estatisticas.
- `app/templates`: telas Jinja2.
- `app/static`: CSS e JavaScript.
- `scripts`: seed e criacao de admin.
- `tests`: testes basicos.

## Proximos passos

Adicionar upload visual completo, migracoes com Alembic, geolocalizacao por distancia real, melhorias no painel admin e PostgreSQL em producao.
