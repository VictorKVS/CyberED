# FATHER Agent Learning Pipeline v0.1

## Три независимых механизма
1. RAG: approved knowledge → chunking → embedding/index → retrieval with citations. Изменения весов модели нет.
2. Agent improvement: версии промптов, правил и инструментов через PR; replay задач и regression tests, сравнение метрик.
3. LLM fine-tuning: отдельный, проверенный, обезличенный датасет SFT/LoRA; holdout test set; модель допускается только после оценки.

## Структура кейса
case_id, task_id, environment_fingerprint (без идентификаторов хоста), objective, inputs, retrieved_sources, plan_revision, gate1_decision, approved_actions, execution_logs_ref, gate2_results, failure_analysis, corrective_action, evidence_refs, reviewer, status, timestamps.

## Поток
CAPTURED → VALIDATED → REVIEWED → APPROVED → INDEXED → EVALUATED.
Непроверенный вывод GPT остаётся CANDIDATE. Изменение промпта/политики создаёт PR. Критические изменения требуют человека. Исполнение TIMA требует отдельного GATE-1, даже если знания и промпт одобрены.

## Метрики
- pass_rate на независимых сценариях;
- доля ответов с проверяемыми источниками;
- доля необоснованных утверждений;
- точность соблюдения GATE-1;
- воспроизводимость и время устранения ошибок.

## Границы хранения
Git: промпты, схемы, обезличенные кейсы, тесты, manifest evidence.
Не Git: пароли, токены, ключи, чувствительные логи, персональные данные, образы ВМ, дампы сети.
