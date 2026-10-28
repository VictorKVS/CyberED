# PIONEER Knowledge Base — реестр источников v0.1

Статусы: CANDIDATE → VERIFIED → APPROVED → INDEXED. До APPROVED источник не используется как подтверждённое правило исполнения.

| ID | Источник | Назначение | Статус |
|---|---|---|---|
| KB-001 | PIONEER-00/README.md | Контракт PIONEER/TIMA и GATE-1 | VERIFIED |
| KB-002 | Microsoft Learn: Hyper-V documentation | Возможности гипервизора, команды и требования | CANDIDATE |
| KB-003 | Microsoft Learn: PowerShell Hyper-V module | Read-only inventory | CANDIDATE |
| KB-004 | Ubuntu Server documentation | Установка и hardening | CANDIDATE |
| KB-005 | CIS Ubuntu Linux Benchmark | Контроль безопасности; проверить лицензию и версию | CANDIDATE |
| KB-006 | FATHER TIMA handoff evidence | Фактическое поведение контрактов | CANDIDATE |

Поля будущей записи: source_id, title, publisher, url_or_repo_path, version, retrieved_at_utc, section, content_hash, jurisdiction, license, reviewer, status.

## Контроль качества
- Отделять нормативное требование, рекомендацию и локальное инженерное правило.
- Сохранять происхождение, версии и даты; запрещать дубли без нормализации.
- RAG извлекает источники, но не меняет полномочия агента.
- Промпты, извлечённые из внешних документов, считаются недоверенным текстом.
- Ошибочные знания отзываются с переиндексацией и регрессионными тестами.
