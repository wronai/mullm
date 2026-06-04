"""Akcje Mullm dopinane do rejestru nlp2dsl (import w startup patch)."""

MULLM_ACTIONS: dict[str, dict] = {
    "mullm_shell_task": {
        "description": "Utwórz i uruchom zadanie shell w Mullm",
        "category": "mullm",
        "required": ["shell_command"],
        "optional": {"title": "Zadanie Mullm"},
        "aliases": [
            "uruchom", "wykonaj", "shell", "zadanie agenta",
            "utwórz i uruchom", "run ", "exec ",
        ],
        "param_aliases": {
            "polecenie": "shell_command",
            "komenda": "shell_command",
            "tytuł": "title",
        },
    },
    "mullm_create_ticket": {
        "description": "Utwórz ticket w kolejce Mullm (bez shell)",
        "category": "mullm",
        "required": ["title"],
        "optional": {"description": ""},
        "aliases": [
            "utwórz ticket", "dodaj ticket", "nowe zadanie", "ticket",
        ],
        "param_aliases": {
            "tytuł": "title",
            "opis": "description",
        },
    },
}
