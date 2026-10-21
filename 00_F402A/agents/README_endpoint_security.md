# FATHER Endpoint Security Agent — архитектура и лицензии

## Назначение
Локальный агент для Windows и Astra Linux. Три изолированных режима: AUDIT (только чтение), PLAN (обоснованный план исправлений), APPLY (только утверждённые изменения с журналом и откатом). **Реализован пока только AUDIT v0.1.** Режимы PLAN/APPLY — проект.

## Прототип
`00_F402A/agents/endpoint_security_audit.py` — стандартная библиотека Python, локальная работа, JSON-отчёт, отсутствие передачи данных, отсутствие изменений конфигурации. По умолчанию чувствительные сведения пропускаются; `--include-details` разрешён только для согласованного учебного стенда, поскольку в stdout могут оказаться учётные записи, IP и правила. Отчёты не коммитить в публичный репозиторий.

Запуск:
```powershell
python .\00_F402A\agents\endpoint_security_audit.py --out "$env:TEMP\cybered-audit.json"
```
```bash
python3 00_F402A/agents/endpoint_security_audit.py --out "$HOME/cybered-audit.json"
```
Запускать из корня репозитория. Утилиты могут отсутствовать, часть команд потребует повышенных прав; это фиксируется как ошибка/недоступность. Для реального аудита следует расширить сбор до нормализованных структурированных значений, верифицировать настройки и протестировать на каждой редакции ОС. Прототип не оценивает защищённость количественно.

## Каталог источников и продуктов (проверено 2026-10-21)
- Microsoft Security Compliance Toolkit: https://learn.microsoft.com/windows/security/operating-system-security/device-management/windows-security-configuration-framework/security-compliance-toolkit-10 — официальные baseline и LGPO/Policy Analyzer, отдельные условия Microsoft.
- Astra Linux PARSEC/MIC: https://docs.astralinux.ru/latest/szi/szi/mic/ — встроенный МКЦ; лицензирование ОС и редакции проверять по поставке.
- Astra audit: https://docs.astralinux.ru/latest/szi/szi/aea/
- Wazuh: https://documentation.wazuh.com/current/quickstart.html — open source GPLv2/Apache 2.0; части движка AGPLv3, проверять компонентные лицензии.
- osquery: https://github.com/osquery/osquery/blob/master/LICENSE — Apache-2.0 OR GPL-2.0-only.
- RedCheck: https://www.redcheck.ru/licensing/ — коммерческий, базовая/профессиональная/экспертная/корпоративная редакции, по IP или модулям; https://www.redcheck.ru/downloads/ — 30-дневная демоверсия до 5 IP, коммерческое использование демо ограничено лицензионными условиями, ФСТЭК №3172 до 23.06.2030 (по данным производителя).
- Сканер-ВС 7: https://scaner-vs.ru/ — коммерческий Base/Enterprise; лицензирование по IP, демо до 4 IP и сроком до 31.12.2026 по сайту производителя.
- Positive Technologies: https://ptsecurity.com/docs/certificates/ — проверять срок и точную сертифицированную версию MaxPatrol/XSpider.
- CIS-CAT Pro: https://github.com/CISecurity/CCPA-Docs/blob/master/docs/Configuration%20Guide.md — требует CIS SecureSuite Membership.

## Целевая архитектура
Endpoint collectors → normalization → rules/baselines → evidence store → risk engine → approval queue → remediator → verification/rollback → CyberED dashboard.
Windows: MMC/PowerShell/Get-Acl/auditpol/Defender/Firewall/GPO. Astra: id/getfacl/auditd/systemctl/nft/PARSEC при поддержке. Не смешивать состояние ОС, соответствие нормативам, лицензию и сертификацию.
Меры по 152-ФЗ, 187-ФЗ, приказам ФСТЭК №17/21/239 и актуальным требованиям связывать через отдельный каталог требований с версией и датой действия, без автоматического утверждения о соответствии.

## Требования к APPLY (не реализован)
Только разрешённые операции, точная идентификация тестового узла, пред-проверка, резервирование настроек, dry-run, подтверждение человеком, таймаут, транзакционный журнал, проверка после изменения и план отката. Не выполнять массовые изменения прав, паролей, PAM, sudoers, PARSEC, GPO и firewall без тестов.
