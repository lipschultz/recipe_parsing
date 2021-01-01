import re
import unicodedata
from typing import AnyStr, Optional

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
    'block', 'blocks',
    'drop', 'drops',
    'dollop', 'dollops'
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


class Ingredient:
    def __init__(self,
                 name: AnyStr,
                 amount: Optional[float] = None,
                 unit: Optional[AnyStr] = None,
                 notes: Optional[AnyStr] = None,
                 optional: bool = False
                 ):
        self.name = name
        self.amount = amount
        self.unit = unit
        self.notes = notes
        self.optional = optional

    @staticmethod
    def _extract_note_from_name(text):
        i_comma = text.find(',')
        i_paren = text.find('(')

        def extract_comma(text, i):
            return text[:i].strip(), text[i + 1:].strip()

        def extract_paren(text, i):
            name = text[:i].strip()
            note = text[i + 1:].rstrip(')').strip()
            return name, note

        if i_comma == -1:
            if i_paren == -1:
                name, note = text, None
            else:
                name, note = extract_paren(text, i_paren)
        elif i_paren == -1:
            name, note = extract_comma(text, i_comma)
        elif i_paren < i_comma:
            name, note = extract_paren(text, i_paren)
        else:
            name, note = extract_comma(text, i_comma)

        if note is not None and len(note) == 0:
            note = None
        return name, note

    @classmethod
    def parse_line(cls, ingredient_line: AnyStr) -> 'Ingredient':
        number_regex = r'[0-9\u2150-\u215E\u00BC-\u00BE,./\s]+'
        units_regex = '|'.join(units)
        ingredient_regex = fr'(?P<amount>{number_regex})?\s*(?P<unit>{units_regex})?\.?\s+(?P<name>.+)'

        deoptionalized_ingredient_line = re.sub(r'\s*[,(]?\s*optional\s*\)?', '', ingredient_line, flags=re.IGNORECASE)
        optional = (ingredient_line != deoptionalized_ingredient_line)
        ingredient_line = deoptionalized_ingredient_line

        res = re.match(fr'\s*{ingredient_regex}\s*', ingredient_line, flags=re.IGNORECASE)
        if res:
            amount = to_number(res.group('amount'))
            unit = res.group('unit')
            name = res.group('name')
        else:
            amount = None
            unit = None
            name = ingredient_line

        if name.lower().startswith('of'):
            name = name[2:].lstrip()

        name, note = cls._extract_note_from_name(name)

        return Ingredient(name, amount, unit, note, optional)
