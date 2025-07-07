from __future__ import annotations

"""Упрощённый DSL для создания клавиатур, независимых от фреймворка.

Пользовательского кода:

    from tigro.keyboard import cb_btn, url_btn, inline_kb

    keyboard = inline_kb(
        [cb_btn("ℹ️ Помощь", "help"), cb_btn("⚙️ Настройки", "settings")]
    )

Получается словарь, который понимают *renderers*, и который легко
конвертировать в объекты aiogram или другого фреймворка.

SOLID
-----
SRP  – модуль отвечает только за конструирование абстрактных клавиатур.
OCP  – новые типы кнопок/клавиатур можно добавить отдельными функциями.
LSP  – любые функции возвращают согласованную структуру (dict).
ISP  – публичный интерфейс минимален (cb_btn, url_btn, inline_kb, reply_kb).
DIP  – остальной код зависит только от словаря, не от конкретного DSL.
"""

from typing import List, Dict, Any, Sequence

__all__ = (
    "cb_btn",
    "url_btn",
    "inline_kb",
    "reply_kb",
    "inline_kb_grid",
)


# ------------------------------------------------------------------
# Конструкторы кнопок
# ------------------------------------------------------------------

def cb_btn(text: str, data: str) -> Dict[str, str]:  # noqa: D401
    """Создать кнопку callback-data."""
    return {"text": text, "callback_data": data}


def url_btn(text: str, url: str) -> Dict[str, str]:  # noqa: D401
    """Создать кнопку с URL."""
    return {"text": text, "url": url}


# ------------------------------------------------------------------
# Конструкторы клавиатур
# ------------------------------------------------------------------

def _normalize(rows: Sequence[Any]) -> List[List[Dict[str, Any]]]:
    """Преобразовать произвольный ввод в список рядов кнопок."""
    norm_rows: List[List[Dict[str, Any]]] = []
    for row in rows:
        # Если пользователь передал одну кнопку (tuple/dict)
        if isinstance(row, dict):
            norm_rows.append([row])
        elif isinstance(row, (list, tuple)):
            # Список/кортеж из кнопок
            norm_rows.append([btn if isinstance(btn, dict) else btn for btn in row])
        else:
            raise TypeError(f"Unsupported row element: {row!r}")
    return norm_rows


def inline_kb(*rows: Any, row_width: int | None = None) -> Dict[str, Any]:  # noqa: D401
    """Сформировать dict для inline-клавиатуры.

    Примеры::
        inline_kb(cb_btn("One", "1"))
        inline_kb(*buttons, row_width=2)
    """
    data: Dict[str, Any] = {"inline_keyboard": _normalize(rows)}
    if row_width is not None:
        data["row_width"] = int(row_width)
    return data


def reply_kb(*rows: Any) -> Dict[str, Any]:  # noqa: D401
    """Сформировать dict для обычной клавиатуры."""
    return {"keyboard": _normalize(rows)}


# Helper for flatten group
def _flatten_group(grp: Any) -> List[Dict[str, Any]]:
    acc: List[Dict[str, Any]] = []

    def _extend_from(item: Any):  # noqa: WPS430
        if isinstance(item, dict):
            if "inline_keyboard" in item:
                for row in item["inline_keyboard"]:
                    acc.extend(row)
            elif "text" in item:
                acc.append(item)
            elif "cols" in item:
                pass  # ignore config dict here
            else:
                raise TypeError(f"Unsupported dict element: {item}")
        elif isinstance(item, (list, tuple)):
            for btn in item:
                _extend_from(btn)
        elif isinstance(item, int):
            pass  # config int
        else:
            raise TypeError(f"Unsupported element type: {type(item)}")

    _extend_from(grp)
    return acc


def inline_kb_grid(*groups: Any, cols: int | None = None) -> Dict[str, Any]:  # noqa: D401
    """Собрать клавиатуру сеткой из нескольких *групп*.

    Каждая *group*:
      • список/tuple/клавиатура;
      • может оканчиваться `int` или `{'cols': N}` — задаёт ширину именно этой группы;
    Если `cols=` передан аргументом, он используется как значение по умолчанию
    для групп без собственной конфигурации.
    """

    all_rows: List[List[Dict[str, Any]]] = []

    for grp in groups:
        local_items = list(grp) if isinstance(grp, (list, tuple)) else [grp]

        # 1. Определяем локальный cols
        local_cols = cols
        if local_items:
            tail = local_items[-1]
            if isinstance(tail, int):
                local_cols = tail
                local_items = local_items[:-1]
            elif isinstance(tail, dict) and "cols" in tail:
                local_cols = int(tail["cols"])
                local_items = local_items[:-1]

        if local_cols is None:
            local_cols = 1  # значение по умолчанию

        flat = _flatten_group(local_items)

        # 2. rows for this group
        group_rows = [flat[i : i + local_cols] for i in range(0, len(flat), local_cols)]
        all_rows.extend(group_rows)

    # row_width = max len first row or cols? we'll set to max local_cols for simplicity
    rw = cols or max(len(r) for r in all_rows) if all_rows else 1
    return inline_kb(*all_rows, row_width=rw) 