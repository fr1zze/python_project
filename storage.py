import json
from pathlib import Path


def load_data(filename: Path) -> list[dict]:
    """Загрузить список из JSON-файла."""
    try:
        with filename.open("r", encoding="utf-8") as file:
            data = json.load(file)

    except FileNotFoundError:
        return []

    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(
            f"Не удалось прочитать {filename}: {error}"
        ) from error

    if not isinstance(data, list):
        raise ValueError(
            f"В файле {filename} должен быть список"
        )

    return data


def save_data(filename: Path, data: list[dict]) -> None:
    """Сохранить список в JSON-файл."""
    try:
        filename.parent.mkdir(parents=True, exist_ok=True)

        with filename.open("w", encoding="utf-8") as file:
            json.dump(
                data,
                file,
                ensure_ascii=False,
                indent=2,
            )

    except OSError as error:
        raise ValueError(
            f"Не удалось сохранить {filename}: {error}"
        ) from error