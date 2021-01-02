import re
import unicodedata
from typing import AnyStr, Optional, Union

Number = Union[int, float]

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


def to_number(value: str) -> Optional[Number]:
    if isinstance(value, (int, float)):
        return value
    elif not isinstance(value, str):
        return None

    value = value.strip()
    if len(value) == 0:
        return None
    elif len(value) == 1:
        try:
            return unicodedata.numeric(value)
        except ValueError:
            return None
    elif len(value.split()) > 1:
        accumulated_value = 0
        for v in value.split():
            converted_number = to_number(v)
            if converted_number is None:
                return None
            else:
                accumulated_value += converted_number
        return accumulated_value
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
                if converted_char is None:
                    return None
                elif converted_char < 1:
                    accumulated_value += converted_char
                else:
                    accumulated_value = accumulated_value * 10 + converted_char
            return accumulated_value


class Quantity:
    def __init__(self, amount: Number, unit: AnyStr):
        self.amount = amount
        self.unit = unit

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        if self.amount != other.amount:
            return False
        if self.amount is None:
            return True
        else:
            return self.unit == other.unit

    def __bool__(self):
        return bool(self.amount or self.unit)

    def __str__(self):
        return f'{self.amount} {self.unit}'

    def __repr__(self):
        return f'{self.__class__.__name__}({self.amount!r}, {self.unit!r})'


NO_QUANTITY = Quantity(None, None)


class Ingredient:
    def __init__(self,
                 name: AnyStr,
                 quantity: Quantity = NO_QUANTITY,
                 notes: Optional[AnyStr] = None,
                 optional: bool = False,
                 to_quantity: Quantity = NO_QUANTITY,
                 ):
        self.name = name
        self.quantity = quantity
        self.notes = notes
        self.optional = optional
        self.to_quantity = to_quantity

    def equals(self, other, compare_notes=True, compare_optional=True):
        return isinstance(other, self.__class__) and \
               self.name == other.name and \
               self.quantity == other.quantity and \
               (not compare_notes or self.notes == other.notes) and \
               (not compare_optional or self.optional == other.optional) and \
               self.to_quantity == other.to_quantity

    def __str__(self):
        ingredient = []
        if self.quantity:
            ingredient.append(str(self.quantity))
            if self.to_quantity:
                ingredient.extend(['-', str(self.to_quantity)])

        ingredient.append(self.name)

        if self.notes:
            ingredient.append(f'({self.notes})')

        if self.optional:
            ingredient.append('(optional)')

        return ' '.join(ingredient)

    def __repr__(self):
        return f'{self.__class__.__name__}(name={self.name!r}, quantity={self.quantity!r}, notes={self.notes!r}, optional={self.optional!r}, to_quantity={self.to_quantity!r})'

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
        dash_regex = r'(?:[-\u2012-\u2015\u2053~]|to)'
        units_regex = '|'.join(units)
        ingredient_regex = fr'(?P<amount>{number_regex})?\s*(?P<unit1>{units_regex})?\.?(?:\s*{dash_regex}\s*(?P<to_amount>{number_regex}))?\s*(?P<unit2>{units_regex})?\.?\s+(?P<name>.+)'

        deoptionalized_ingredient_line = re.sub(r'\s*[,(]?\s*optional\s*\)?', '', ingredient_line, flags=re.IGNORECASE)
        optional = (ingredient_line != deoptionalized_ingredient_line)
        ingredient_line = deoptionalized_ingredient_line

        res = re.match(fr'\s*{ingredient_regex}\s*', ingredient_line, flags=re.IGNORECASE)
        if res:
            amount = to_number(res.group('amount'))
            amount_unit = res.group('unit1')

            to_amount = to_number(res.group('to_amount'))
            to_amount_unit = res.group('unit2')

            quantity = Quantity(amount, amount_unit or to_amount_unit)
            to_quantity = Quantity(to_amount, to_amount_unit)

            name = res.group('name')
        else:
            quantity = NO_QUANTITY
            to_quantity = NO_QUANTITY
            name = ingredient_line

        if name.lower().startswith('of'):
            name = name[2:].lstrip()

        name, note = cls._extract_note_from_name(name)

        return Ingredient(name, quantity, note, optional, to_quantity=to_quantity)
