import unicodedata
from typing import AnyStr, Tuple, Optional


def to_number(value: AnyStr) -> Optional[float]:
    try:
        try:
            decomposition = unicodedata.decomposition(value)
            if 'fraction' in decomposition:
                frac_split = decomposition.split()
                amount = round(float(frac_split[1].replace('003', '')) / float(frac_split[3].replace('003', '')), 3)
            else:
                amount = float(value.replace(',', '.'))
        except TypeError:
            if '/' in value:
                numerator, denominator = value.split('/', 1)
                amount = round(float(numerator) / float(denominator), 3)
            else:
                try:
                    amount = float(value.replace(',', '.'))
                except ValueError:
                    amount = 0
                    for v in value:
                        converted_value = to_number(v)
                        if converted_value is None:
                            amount = None
                            break
                        elif converted_value < 1:
                            amount += converted_value
                        else:
                            amount = amount * 10 + converted_value
    except ValueError:
        amount = None
    return amount


def parse(ingredient_line: AnyStr) -> Tuple[float, str, str]:
    ingredient_split = ingredient_line.split()
    amount = None
    unit = None

    numeric_value = to_number(ingredient_split[0])
    if numeric_value is None:
        ingredient = " ".join(ingredient_split)
    else:
        amount = numeric_value
        i_after = 1
        numeric_value = to_number(ingredient_split[1])
        if numeric_value is not None:
            amount += numeric_value
            i_after += 1

        if len(ingredient_split[i_after:]) > 1:
            unit = ingredient_split[i_after]
            i_after += 1
        ingredient = " ".join(ingredient_split[i_after:])
    return (amount, unit, ingredient)
