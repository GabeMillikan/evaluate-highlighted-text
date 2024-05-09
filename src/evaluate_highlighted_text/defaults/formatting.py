def formatting(number: int | float) -> str:
    if isinstance(number, int):
        return f"{number:d}"

    return f"{number:.14g}"
