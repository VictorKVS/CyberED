#!/usr/bin/env python3
"""CyberED ALINA IB: offline rule-based audit planner. No LLM, no network or active scanning."""
import argparse
import json
from pathlib import Path

PROFILES = {
    "ispdn": {"label": "ИСПДн", "regulations": ["152-ФЗ", "ПП РФ №1119", "ФСТЭК №21"], "notes": ["Установить уровень защищённости", "Проверить применимость актов ФСБ при использовании СКЗИ"]},
    "gis": {"label": "ГИС", "regulations": ["149-ФЗ", "ФСТЭК №117 (11.04.2025, актуальная редакция)"], "notes": ["Проверить класс защищённости и актуальные изменения", "ФСТЭК №17 — исторический"]},
    "kii": {"label": "Значимый объект КИИ", "regulations": ["187-ФЗ", "ФСТЭК №235", "ФСТЭК №239"], "notes": ["Проверить категорию значимости и область применимости"]},
    "other": {"label": "Иная ИС", "regulations": ["Нормативный профиль уточняется"], "notes": ["Не назначать меры без классификации и модели угроз"]},
}
NODES = {
    "workstation": ("Рабочая станция", "Вне OSI / L4–L7", ["Инвентаризация ПО", "Управление доступом", "Журналирование"]),
    "switch": ("Коммутатор", "L1–L2", ["Учёт портов", "VLAN и сегментация", "Контроль управления"]),
    "router": ("Маршрутизатор", "L3", ["ACL", "Защита управления", "Анализ маршрутов"]),
    "firewall": ("Межсетевой экран", "L3–L7", ["Правила потоков", "Журналы", "Проверка сертификата по применимости"]),
    "server": ("Сервер", "Вне OSI / L4–L7", ["Hardening", "Контроль привилегий", "Резервное копирование"]),
    "database": ("База данных", "L7 / данные", ["Доступ к данным", "Резервное копирование", "Журналирование"]),
    "hypervisor": ("Гипервизор", "Вне OSI", ["Изоляция ВМ", "Доступ администраторов", "Аудит конфигурации"]),
    "application": ("Приложение / API", "L7", ["Контроль доступа", "Проверка ввода", "Тестирование API"]),
}
def plan(payload):
    profile = payload.get("profile", "other")
    if profile not in PROFILES: raise ValueError("Unknown profile: " + str(profile))
    assets = payload.get("assets", [])
    if not isinstance(assets, list): raise ValueError("assets must be an array")
    findings = []
    for i, asset in enumerate(assets):
        if not isinstance(asset, dict): raise ValueError("asset must be an object")
        kind = asset.get("type", "")
        name = str(asset.get("name", f"asset-{i+1}"))
        if kind not in NODES:
            findings.append({"asset": name, "status": "UNKNOWN", "reason": "Тип узла не описан", "next_action": "Провести обследование"})
            continue
        label, osi, checks = NODES[kind]
        findings.append({"asset": name, "type": label, "osi": osi, "status": "NOT_TESTED", "checks": [{"title": c, "status": "NOT_TESTED", "evidence": None} for c in checks]})
    p = PROFILES[profile]
    return {"schema_version": "0.1", "mode": "PASSIVE", "profile": p["label"], "regulations_to_verify": p["regulations"], "regulatory_notes": p["notes"], "assets": findings, "required_next_steps": ["Подтвердить полномочия и границы", "Уточнить классификацию", "Проверить точные пункты и редакции", "Составить модель угроз по методике ФСТЭК", "Проверить применимость мер", "Проверить сертификаты конкретных СЗИ", "Согласовать испытания и собрать доказательства"], "limitations": ["Это план обследования, не результат аудита", "Нет автоматического назначения обязательных мер", "Нет сетевых запросов и активных проверок", "Нет подтверждения сертификатов и нормативных редакций"]}
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input",type=Path,help="JSON: profile and assets")
    ap.add_argument("-o","--output",type=Path)
    args=ap.parse_args()
    result=plan(json.loads(args.input.read_text(encoding="utf-8")))
    data=json.dumps(result,ensure_ascii=False,indent=2)
    if args.output: args.output.write_text(data+"\n",encoding="utf-8")
    else: print(data)
if __name__=="__main__": main()
