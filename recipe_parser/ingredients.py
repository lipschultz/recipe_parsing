import re
import unicodedata
from typing import AnyStr, Tuple, Optional


_units_weights = [
    'pound', 'pounds', 'lb', 'lbs',
    'ounce', 'ounces', 'oz',
    'gram', 'grams', 'g', 'grm', 'grms', 'gr',
    'milligram', 'milligrams', 'mg',
    'kilogram', 'kilograms', 'kg', 'kilo', 'kilos',
]

_units_volumes = [
    'tablespoon', 'tablespoons', 'tbsp', 'T', 'tbs', 'tbsps', 'tb',
    'teaspoon', 'teaspoons', 'tsp', 't', 'tsps',
    'cup', 'cups', 'c',
    'pint', 'pints', 'pt', 'p',
    'quart', 'quarts', 'qt',
    'gallon', 'gallons', 'gal',
    'fluid ounce', 'fluid ounces', 'fl oz', 'fl. oz.', 'oz. fl.',
    'liter', 'litre', 'liters', 'litres', 'l', 'L',
    'milliliter', 'millilitre', 'milliliters', 'millilitres', 'ml', 'mL',
    'centiliter', 'centilitre', 'centiliters', 'centilitres', 'cl', 'cL',
    'deciliter', 'decilitre', 'deciliters', 'decilitres', 'dl', 'dL',
]

_units_length = [
    'centimeter', 'centimetre', 'centimeters', 'centimetres', 'cm',
    'inch', 'inches', 'in'
]

_units_amounts = [
    'serving', 'servings',
    'loaf', 'loaves',
    'cookie', 'cookies',
    'ball', 'balls',
    'piece', 'pieces',
    'slice', 'slices',
    'pie', 'pies',
    'stick', 'sticks',
    'package', 'packages', 'pkg', 'pkgs',
    'box', 'boxes',
    'can', 'cans',
    'head', 'heads',
    'cloves', 'clove'
    'medium', 'md', 'med',
    'large', 'lg',
    'small', 'sm',
    'drop', 'drops',
    'bunches', 'bunch',
    'pack', 'packs',
    'stalk', 'stalks',
]


units = _units_weights + _units_volumes + _units_length + _units_amounts


def to_number(value: AnyStr) -> Optional[float]:
    value = value.strip()
    if len(value) == 1:
        return unicodedata.numeric(value)
    elif len(value.split()) > 1:
        return sum(to_number(v) for v in value.split())
    elif '/' in value:
        numer, denom = value.split('/', 1)
        return float(numer) / float(denom)
    else:
        try:
            return float(value.replace(',', ''))
        except ValueError:
            accumulated_value = 0
            for char in value:
                converted_char = to_number(char)
                if converted_char < 1:
                    accumulated_value += converted_char
                else:
                    accumulated_value = accumulated_value * 10 + converted_char
            return accumulated_value


Ingredient = Tuple[Optional[float], Optional[str], str]


def parse(ingredient_line: AnyStr) -> Ingredient:
    number_regex = r'[0-9\u2150-\u215E\u00BC-\u00BE,./\s]+'
    units_regex = '|'.join(units)
    ingredient_regexes = fr'(?P<amount>{number_regex})?\s*(?P<unit>{units_regex})?\.?\s+(?P<name>.+)\s*'

    res = re.match(fr'\s*{ingredient_regexes}', ingredient_line, flags=re.IGNORECASE)
    if res:
        amount = res.group('amount')
        unit = res.group('unit')
        name = res.group('name')
        return to_number(amount), unit, name
    else:
        return (None, None, ingredient_line)
