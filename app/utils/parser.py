import re

def parse_food_input(text: str) -> tuple[str | None, int | None]:
    text = text.strip().lower()
    if not text:
        return None, None

    # Регулярка ищет число в конце строки с возможными единицами измерения
    match = re.search(r'(\d+(?:\.\d+)?)\s*([гkгр]|грамм|гр|кг)?\s*$', text, re.IGNORECASE)
    
    if not match:
        # Если числа нет, возвращаем весь текст как название
        return text.strip(), None

    weight_str = match.group(1)
    unit_str = match.group(2)
    name_part = text[:match.start()].strip()

    # Если текста перед числом нет (пользователь ввел просто "200"), считаем это названием
    if not name_part:
        return text.strip(), None

    try:
        weight = float(weight_str.replace(',', '.'))
        
        # Если пользователь указал "кг", переводим в граммы
        if unit_str and unit_str.lower() == 'кг':
            weight *= 1000
            
        weight = int(weight)
        
        if weight <= 0:
            return name_part, None
            
        return name_part, weight
    except (ValueError, TypeError):
        return name_part, None