import re
import unicodedata
from typing import AnyStr, Optional, Union, Iterable

import regex

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
    'ball', 'balls',
    'block', 'blocks',
    'box', 'boxes',
    'bunch', 'bunches',
    'can', 'cans',
    'cloves', 'clove'
    'cookie', 'cookies',
    'drop', 'drops',
    'dollop', 'dollops',
    'head', 'heads',
    'loaf', 'loaves',
    'pack', 'packs',
    'package', 'packages', 'pkg', 'pkgs',
    'pie', 'pies',
    'piece', 'pieces',
    'roll', 'rolls',
    'serving', 'servings',
    'slice', 'slices',
    'stalk', 'stalks',
    'stick', 'sticks',
]

_unit_modifier_pre_amount = ['scant']

_unit_modifier_pre_unit = [
    'medium', 'md', 'med',
    'large', 'lg',
    'small', 'sm',

    'heaping',
    'rounded',
    'scant',
]

_unit_modifier_post_unit = [r'\+']


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
    def __init__(self, amount: Optional[Number], unit: Optional[AnyStr], approximate: bool = False):
        self.amount = amount
        self.unit = unit
        self.approximate = approximate

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

    def is_empty(self):
        return not bool(self)

    def __str__(self):
        return f'{"~" if self.approximate else ""}{self.amount} {self.unit}'

    def __repr__(self):
        return f'{self.__class__.__name__}({self.amount!r}, {self.unit!r}, approximate={self.approximate!r})'


class TotalQuantity:
    def __init__(self, quantities: Iterable[Quantity] = tuple()):
        self.quantities = [q for q in quantities if not q.is_empty()]

    def __len__(self):
        return len(self.quantities)

    def __getitem__(self, item):
        return self.quantities[item]

    def __iter__(self):
        return iter(self.quantities)

    def __str__(self):
        return str(self.quantities)

    def __repr__(self):
        return f'{self.__class__.__name__}({self.quantities!r})'


NO_QUANTITY = Quantity(None, None)
NO_TOTAL_QUANTITY = TotalQuantity()


class Ingredient:
    def __init__(self,
                 name: AnyStr,
                 quantity: TotalQuantity = NO_TOTAL_QUANTITY,
                 notes: Optional[AnyStr] = None,
                 optional: bool = False,
                 to_quantity: TotalQuantity = NO_TOTAL_QUANTITY,
                 equivalent_quantity: TotalQuantity = NO_TOTAL_QUANTITY,
                 ):
        self.name = name
        self.quantity = quantity
        self.notes = notes
        self.optional = optional
        self.to_quantity = to_quantity
        self.equivalent_quantity = equivalent_quantity

    def equals(self, other, compare_notes=True, compare_optional=True, compare_equivalent_quantity=False):
        return isinstance(other, self.__class__) and \
               self.name == other.name and \
               self.quantity == other.quantity and \
               (not compare_notes or self.notes == other.notes) and \
               (not compare_optional or self.optional == other.optional) and \
               self.to_quantity == other.to_quantity and \
               (not compare_equivalent_quantity or self.equivalent_quantity == other.equivalent_quantity)

    def __eq__(self, other):
        return self.equals(other, True, True, True)

    def __str__(self):
        ingredient = []
        if self.quantity:
            ingredient.append(str(self.quantity))
            if self.to_quantity:
                ingredient.extend(['-', str(self.to_quantity)])

        if self.equivalent_quantity:
            ingredient.append(f'({self.equivalent_quantity}')

        ingredient.append(self.name)

        if self.notes:
            ingredient.append(f'({self.notes})')

        if self.optional:
            ingredient.append('(optional)')

        return ' '.join(ingredient)

    def __repr__(self):
        attribs = ['name', 'quantity', 'notes', 'optional', 'to_quantity', 'equivalent_quantity']
        attrib_list = ', '.join(f'{attrib}={getattr(self, attrib)!r}' for attrib in attribs)
        return f'{self.__class__.__name__}({attrib_list})'

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

    @staticmethod
    def _partial_format(template, **kwargs):
        class DefaultDict(dict):
            def __missing__(self, key):
                return '{' + key + '}'

        return template.format_map(DefaultDict(**kwargs))

    @classmethod
    def parse_line(cls, ingredient_line: AnyStr) -> 'Ingredient':
        number_regex = r'[0-9\u2150-\u215E\u00BC-\u00BE,./\s]+'
        dash_regex = r'(?:[-\u2012-\u2015\u2053~]|to)'
        approx_regex = r'(?:~|about|approx(?:\.|imately)?)'
        units_regex = '|'.join(units)
        plus_regex = '|'.join([r'\+', 'and', 'plus', ','])

        quantity_regex_fmt = r'(?P<approx{label}>{approx_regex})?\s*(?P<amount{label}>{amount_regex})?\s*(?P<unit{label}>{unit_regex})?\.?'
        parse_quantity_regex = lambda res, label: (to_number(res.group(f'amount{label}')), res.group(f'unit{label}'), bool(res.group(f'approx{label}')))

        quantity_group_regex_fmt = quantity_regex_fmt + r'(?:\s*(?:' + plus_regex + r')\s*(?P<subsequent{label}>' + cls._partial_format(quantity_regex_fmt, label="{label}_subsequent") + '))*'

        ingredient_regex = quantity_group_regex_fmt.format(label='1', approx_regex=approx_regex, amount_regex=number_regex, unit_regex=units_regex) + \
                           fr'(?:\s*{dash_regex}\s*' + quantity_group_regex_fmt.format(label='2', approx_regex=approx_regex, amount_regex=number_regex, unit_regex=units_regex) + r')?'\
                           r'\s*(?:\(' + quantity_group_regex_fmt.format(label='_equiv1', approx_regex=approx_regex, amount_regex=number_regex, unit_regex=units_regex) + r'\))?' + \
                           r'\s+(?P<name>.+)'

        deoptionalized_ingredient_line = regex.sub(r'\s*[,(]?\s*optional\s*\)?', '', ingredient_line, flags=re.IGNORECASE)
        optional = (ingredient_line != deoptionalized_ingredient_line)
        ingredient_line = deoptionalized_ingredient_line

        res = regex.match(fr'\s*{ingredient_regex}\s*', ingredient_line, flags=re.IGNORECASE)
        if res:
            amount, amount_unit, amount_approx = parse_quantity_regex(res, '1')
            to_amount, to_amount_unit, to_amount_approx = parse_quantity_regex(res, '2')

            total_quantity = [Quantity(amount, amount_unit or to_amount_unit, approximate=amount_approx)]
            for subs in res.captures('subsequent1'):
                subs_res = regex.fullmatch(quantity_regex_fmt.format(label='', approx_regex=approx_regex, amount_regex=number_regex, unit_regex=units_regex), subs, flags=re.IGNORECASE)
                subs_amount, subs_amount_unit, subs_amount_approx = parse_quantity_regex(subs_res, '')
                total_quantity.append(Quantity(subs_amount, subs_amount_unit, approximate=subs_amount_approx))
            quantity = TotalQuantity(total_quantity)

            total_to_quantity = [Quantity(to_amount, to_amount_unit, approximate=to_amount_approx)]
            for subs in res.captures('subsequent2'):
                subs_res = regex.fullmatch(quantity_regex_fmt.format(label='', approx_regex=approx_regex, amount_regex=number_regex, unit_regex=units_regex), subs, flags=re.IGNORECASE)
                subs_amount, subs_amount_unit, subs_amount_approx = parse_quantity_regex(subs_res, '')
                total_to_quantity.append(Quantity(subs_amount, subs_amount_unit, approximate=subs_amount_approx))
            to_quantity = TotalQuantity(total_to_quantity)

            equivalent1_amount, equivalent1_unit, equivalent1_approx = parse_quantity_regex(res, '_equiv1')
            total_equivalent_quantity = [Quantity(equivalent1_amount, equivalent1_unit, approximate=equivalent1_approx)]
            for subs in res.captures('subsequent_equiv1'):
                subs_res = regex.fullmatch(quantity_regex_fmt.format(label='', approx_regex=approx_regex, amount_regex=number_regex, unit_regex=units_regex), subs, flags=re.IGNORECASE)
                subs_amount, subs_amount_unit, subs_amount_approx = parse_quantity_regex(subs_res, '')
                total_equivalent_quantity.append(Quantity(subs_amount, subs_amount_unit, approximate=subs_amount_approx))
            equivalent_quantity = TotalQuantity(total_equivalent_quantity)

            name = res.group('name')
        else:
            quantity = NO_TOTAL_QUANTITY
            to_quantity = NO_TOTAL_QUANTITY
            name = ingredient_line
            equivalent_quantity = NO_TOTAL_QUANTITY

        if name.lower().startswith('of'):
            name = name[2:].lstrip()

        name, note = cls._extract_note_from_name(name)

        return Ingredient(name, quantity, note, optional, to_quantity=to_quantity, equivalent_quantity=equivalent_quantity)
