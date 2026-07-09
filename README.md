# Forró Ruby — Backend (FastAPI)

API do sistema de gestão da banda Forró Ruby. FastAPI + SQLAlchemy async + PostgreSQL, rodando em Docker na porta **8012**.

## Como rodar

```bash
docker compose up -d --build
```

- API: http://localhost:8012/api/health
- Documentação interativa (Swagger): http://localhost:8012/docs

Na primeira subida o banco é criado e os 3 integrantes são cadastrados automaticamente (seed):

| Integrante | E-mail | Senha inicial |
|---|---|---|
| Davi Maciel (Sanfoneiro) | davi@forroruby.com | `forroruby2026` |
| Nágilla Silva (Cantora) | nagilla@forroruby.com | `forroruby2026` |
| Luid Ferreira (Tecladista e cantor) | luid@forroruby.com | `forroruby2026` |

> Troque a senha no primeiro acesso via `POST /api/auth/change-password`.

## Estrutura

```
app/
├── main.py            # criação do app, CORS, routers, lifespan (create_all + seed)
├── seed.py            # seed dos 3 integrantes
├── core/              # config (env), database (engine async), security (JWT/bcrypt)
├── models/            # SQLAlchemy: member, task, agenda, finance, timelog, study, content, repertoire
├── schemas/           # Pydantic v2 (validação de entrada/saída)
├── routers/           # endpoints por módulo
├── services/pdf.py    # PDF do repertório (reportlab, com logo)
└── assets/logo.png    # logo da banda usada no PDF
```

## Módulos da API (prefixo /api)

| Módulo | Rotas principais |
|---|---|
| auth | `POST /auth/login`, `POST /auth/login-json`, `GET /auth/me`, `POST /auth/change-password` |
| members | `GET /members` |
| tasks | CRUD `/tasks`, `POST /tasks/{id}/comments` — só o responsável edita; os outros comentam |
| agenda | CRUD `/events` (show/ensaio/lembrete/fixa), `PATCH /events/{id}/payouts/{pid}` (marcar parte recebida) |
| finance | `GET|POST|DELETE /finance/entries`, `GET /finance/summary` (saldo, cachês pendentes) |
| timelogs | `POST /timelogs/check-in|check-out`, `GET /timelogs`, `GET /timelogs/report` (meta diária 1h30) |
| study | CRUD `/study/materials` |
| content | CRUD `/content/posts` (cronograma) e `/content/video-ideas` |
| repertoire | CRUD `/repertoire` e `/repertoire/songs`, `GET /repertoire/{id}/pdf` |
| dashboard | `GET /dashboard` (alertas 24/48h + atrasadas, minhas tarefas, próximos eventos) |

## Regras de negócio implementadas

- Só o responsável (ou criador) edita/conclui/exclui a tarefa; os demais comentam (RN01).
- Alertas de prazo: atrasada, ≤24h (urgente), ≤48h (aviso) — `GET /api/dashboard` (RN03/RN04).
- Cachê só entra no saldo quando o show é marcado como **recebido**; o lançamento é criado automaticamente (RN06).
- Divisão do cachê: igual entre os 3, com controle individual de quem já recebeu (RN07).
- Meta diária de 1h30 de trabalho/estudo no relatório de horas (RN05 revisada).
- Tempo de show = soma das durações + intervalo configurável entre músicas (RN09); tom executado pode diferir do tom base (RN10).
