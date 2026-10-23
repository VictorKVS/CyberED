# ALINA — ветка производства визуальных ассетов

Ветка: `feature/alina-avatar-assets` (от `feature/osi-security-atlas-ru`).

## Производственная линия
`source contact sheet → crop → WEBP frames → manifest → QC → website integration → browser QA`.

Исходник не изменяем. Результаты помещаем в `docs/osi/stage1/assets/alina/frames/`, карту состояний в `assets/alina/manifest.json`.

Запуск:
```powershell
python -m pip install Pillow
python 'docs/osi/stage1/assets/alina/tools/build_avatar_assets.py' 'path/to/contact-sheet.png' --out 'docs/osi/stage1/assets/alina'
```

Состояния: neutral, smile, speech_a/b/c, question, listening, thinking, explaining, warning, nod, eyes_closed, eyes_open, blink, profile, laptop, documents, final_pose.

## Важно
Сгенерированный коллаж не является синхронизированной покадровой анимацией: позы, фон и масштаб меняются. Для плавного моргания/разговора потребуется фиксированная базовая поза и новые согласованные кадры, либо видеогенерация/Live2D/рендерер аватара. Не выдавать нарезку за готовый lip-sync.

## Проверки
- 39 изображений (включая вариации); названия и порядок совпадают с manifest.
- Визуальный QA каждого crop (без подписей и соседних панелей).
- Лицо, очки и эмблема стабильны.
- Нет надписей CyberED/CuberED в UI или одежде.
- Оптимизация для мобильных устройств; lazy-load для второстепенных кадров.
- Условия использования и лицензирование перед коммерческим запуском.
