import re


def parse_food_input(text: str) -> tuple[str | None, int | None]:
    text = text.strip().lower()
    if not text:
        return None, None

    # Ищем число в конце (с возможными "г", "грамм", "гр", точкой)
    match = re.search(r'(\d+(?:\.\d+)?)\s*([гkгр]|грамм|гр)?\s*$', text, re.IGNORECASE)
    if not match:
        return text.strip(), None

    weight_str = match.group(1)
    name_part = text[:match.start()].strip()

    try:
        weight = int(float(weight_str))
        if weight <= 0:
            return name_part, None
        return name_part, weight
    except (ValueError, TypeError):
        return name_part, None