import unicodedata
from typing import AnyStr, Optional, Union, Iterable

import regex

from recipe_parser.units import american_units, UnitsRegistry

Number = Union[int, float]


def to_number(value: str) -> Optional[Number]:
    if isinstance(value, (int, float)):
        return value
    elif not isinstance(value, str):
        return None

    value = value.strip()

    # Remove space(s) around a division (e.g. '1 /2' -> '1/2')
    pieces = list(reversed(value.split()))
    combined_pieces = []
    while pieces:
        piece = pieces.pop()
        if piece == '/':
            combined_pieces[-1] += piece + pieces.pop()
        elif piece.startswith('/'):
            combined_pieces[-1] += piece
        elif piece.endswith('/'):
            combined_pieces.append(piece + pieces.pop())
        else:
            combined_pieces.append(piece)
    value = ' '.join(combined_pieces)

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

    def __bool__(self):
        return any(bool(q) for q in self.quantities)

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


class QuantityRange:
    def __init__(self,
                 from_quantity: TotalQuantity = NO_TOTAL_QUANTITY,
                 to_quantity: TotalQuantity = NO_TOTAL_QUANTITY,
                 equivalent_to: Optional['QuantityRange'] = None,
                 ):
        self.from_quantity = from_quantity
        self.to_quantity = to_quantity
        self.equivalent_to = equivalent_to

    def equals(self, other, compare_equivalent_to=False):
        return isinstance(other, self.__class__) and self.from_quantity == other.from_quantity and self.to_quantity == other.to_quantity and (not compare_equivalent_to or self.equivalent_to == other.equivalent_to)

    def __eq__(self, other):
        return self.equals(other, True)

    def __str__(self):
        value = str(self.from_quantity)

        value += f' - {self.to_quantity}'

        value += f' ({self.equivalent_to})'

        return value

    def __repr__(self):
        return f'{self.__class__.__name__}(from_quantity={self.from_quantity!r}, to_quantity={self.to_quantity!r}, ' \
               f'equivalent_to={self.equivalent_to!r})'


NO_QUANTITY_RANGE = QuantityRange()


class Ingredient:
    def __init__(self,
                 name: AnyStr,
                 quantity: QuantityRange = NO_QUANTITY_RANGE,
                 notes: Optional[AnyStr] = None,
                 optional: bool = False,
                 ):
        self.name = name
        self.quantity = quantity
        self.notes = notes
        self.optional = optional

    def equals(self, other, compare_notes=True, compare_optional=True, compare_equivalent_quantity=False):
        return isinstance(other, self.__class__) and \
               self.name == other.name and \
               self.quantity.equals(other, compare_equivalent_to=compare_equivalent_quantity) and \
               (not compare_notes or self.notes == other.notes) and \
               (not compare_optional or self.optional == other.optional)

    def __eq__(self, other):
        return self.equals(other, True, True, True)

    def __str__(self):
        ingredient = []
        if self.quantity:
            ingredient.append(str(self.quantity))

        ingredient.append(self.name)

        if self.notes:
            ingredient.append(f'({self.notes})')

        if self.optional:
            ingredient.append('(optional)')

        return ' '.join(ingredient)

    def __repr__(self):
        attribs = ['name', 'quantity', 'notes', 'optional']
        attrib_list = ', '.join(f'{attrib}={getattr(self, attrib)!r}' for attrib in attribs)
        return f'{self.__class__.__name__}({attrib_list})'


class BasicIngredientParser:
    DEFAULT_OPTIONAL_REGEX = r'\s*[,(]?\s*optional\s*\)?'

    def __init__(self, *, optional_regex=DEFAULT_OPTIONAL_REGEX):
        self.optional_regex = optional_regex

    def __call__(self, text: str) -> Ingredient:
        deoptionalized_ingredient_line = self.deoptionalize_ingredient_line(text)
        optional = (text != deoptionalized_ingredient_line)
        text = deoptionalized_ingredient_line

        quantity = NO_QUANTITY_RANGE
        name = text

        if name.lower().startswith('of'):
            name = name[2:].lstrip()

        name, note = self.extract_note_from_name(name)

        return Ingredient(name, quantity, note, optional)

    def deoptionalize_ingredient_line(self, text) -> str:
        deoptionalized_ingredient_line = regex.sub(self.optional_regex, '', text, flags=regex.IGNORECASE)
        return deoptionalized_ingredient_line

    @staticmethod
    def partial_format(template, **kwargs):
        class DefaultDict(dict):
            def __missing__(self, key):
                return '{' + key + '}'

        return template.format_map(DefaultDict(**kwargs))

    @staticmethod
    def extract_note_from_name(name):
        i_comma = name.find(',')
        i_paren = name.find('(')

        def extract_comma(text, i):
            return text[:i].strip(), text[i + 1:].strip()

        def extract_paren(text, i):
            name = text[:i].strip()
            note = text[i + 1:].rstrip(')').strip()
            return name, note

        if i_comma == -1:
            if i_paren == -1:
                name, note = name, None
            else:
                name, note = extract_paren(name, i_paren)
        elif i_paren == -1:
            name, note = extract_comma(name, i_comma)
        elif i_paren < i_comma:
            name, note = extract_paren(name, i_paren)
        else:
            name, note = extract_comma(name, i_comma)

        if note is not None and len(note) == 0:
            note = None
        return name, note


class IngredientParser(BasicIngredientParser):
    def __init__(self,
                 *,
                 approx_regex=r'(?:~|about|approx(?:\.|imately)?)',
                 amount_regex=r'[0-9\u2150-\u215E\u00BC-\u00BE,./\s]+',
                 units_registry: UnitsRegistry = american_units,
                 plus_regex='|'.join([r'\+', 'and', 'plus', ',']),
                 dash_regex=r'(?:[-\u2012-\u2015\u2053~]|to)',
                 optional_regex=BasicIngredientParser.DEFAULT_OPTIONAL_REGEX,
                 ):
        super().__init__(optional_regex=optional_regex)
        self.approx_regex = approx_regex
        self.amount_regex = amount_regex
        self.units_registry = units_registry
        self.plus_regex = plus_regex
        self.dash_regex = dash_regex

    @property
    def units_regex(self):
        return '|'.join(self.units_registry.all_units_as_regex_strings())

    @property
    def quantity_regex_raw_fmt(self):
        return r'(?P<approx{label}>{approx_regex})?\s*(?P<amount{label}>{amount_regex})?\s*(?P<unit{label}>{unit_regex})?\.?'

    @property
    def quantity_regex_fmt(self):
        return self.partial_format(
            self.quantity_regex_raw_fmt,
            approx_regex=self.approx_regex,
            amount_regex=self.amount_regex,
            unit_regex=self.units_regex,
        )

    def get_quantity_regex(self, label):
        return self.quantity_regex_fmt.format(label=label)

    def parse_quantity_match(self, res, label) -> Quantity:
        return Quantity(to_number(res.group(f'amount{label}')), res.group(f'unit{label}'), bool(res.group(f'approx{label}')))

    @property
    def quantity_total_regex_raw_fmt(self):
        return self.quantity_regex_raw_fmt +\
               r'(?:\s*(?:{plus_regex})\s*(?P<subsequent{label}>' + self.partial_format(self.quantity_regex_raw_fmt, label="{label}_subsequent") + '))*'

    @property
    def quantity_total_regex_fmt(self):
        return self.partial_format(
            self.quantity_total_regex_raw_fmt,
            approx_regex=self.approx_regex,
            amount_regex=self.amount_regex,
            unit_regex=self.units_regex,
            plus_regex=self.plus_regex,
        )

    def get_quantity_total_regex(self, label):
        return self.quantity_total_regex_fmt.format(label=label)

    def parse_quantity_total_match(self, res, label) -> TotalQuantity:
        total_quantity = [self.parse_quantity_match(res, label)]
        for subs in res.captures(f'subsequent{label}'):
            subs_res = regex.fullmatch(self.get_quantity_regex(''), subs, flags=regex.IGNORECASE)
            total_quantity.append(self.parse_quantity_match(subs_res, ''))
        return TotalQuantity(total_quantity)

    @property
    def quantity_range_regex_raw_fmt(self):
        return self.partial_format(self.quantity_total_regex_raw_fmt, label="{label}from") + \
               r'(?:\s*{dash_regex}\s*' + \
               self.partial_format(self.quantity_total_regex_raw_fmt, label="{label}to") + \
               r')?' + \
               r'\s*(?:\(' + self.partial_format(self.quantity_total_regex_raw_fmt, label="{label}equivalent") + r'\))?'

    @property
    def quantity_range_regex_fmt(self):
        return self.partial_format(
            self.quantity_range_regex_raw_fmt,
            approx_regex=self.approx_regex,
            amount_regex=self.amount_regex,
            unit_regex=self.units_regex,
            plus_regex=self.plus_regex,
            dash_regex=self.dash_regex,
        )

    def get_quantity_range_regex(self, label=''):
        return self.quantity_range_regex_fmt.format(label=label)

    def parse_quantity_range_match(self, res, label=''):
        from_quantity = self.parse_quantity_total_match(res, f"{label}from")
        to_quantity = self.parse_quantity_total_match(res, f"{label}to")

        if len(from_quantity) and from_quantity[0].unit is None and len(to_quantity):
            from_quantity[0].unit = to_quantity[0].unit

        equivalent_quantity = self.parse_quantity_total_match(res, f"{label}equivalent")
        if equivalent_quantity:
            # FIXME: this equivalent should be able to be a range
            equivalent_quantity = QuantityRange(equivalent_quantity)
        else:
            equivalent_quantity = None
        return QuantityRange(from_quantity, to_quantity, equivalent_quantity)

    @property
    def regex_raw_fmt(self):
        return self.quantity_range_regex_raw_fmt + r'\s+(?P<name>.+)'

    @property
    def regex_fmt(self):
        return self.partial_format(
            self.regex_raw_fmt,
            approx_regex=self.approx_regex,
            amount_regex=self.amount_regex,
            unit_regex=self.units_regex,
            plus_regex=self.plus_regex,
            dash_regex=self.dash_regex,
        )

    def get_regex(self, label=''):
        return self.regex_fmt.format(label=label)

    def parse_match(self, res, label=''):
        quantity = self.parse_quantity_range_match(res, label=label)

        name = res.group('name')
        if name.lower().startswith('of'):
            name = name[2:].lstrip()

        name, note = self.extract_note_from_name(name)

        return quantity, name, note

    def parse(self, text):
        deoptionalized_ingredient_line = self.deoptionalize_ingredient_line(text)
        optional = (text != deoptionalized_ingredient_line)
        text = deoptionalized_ingredient_line

        res = regex.fullmatch(fr'\s*{self.get_regex()}\s*', text, flags=regex.IGNORECASE)
        if res:
            quantity, name, note = self.parse_match(res)
            return Ingredient(name, quantity, note, optional)
        else:
            return None

    def __call__(self, text):
        return self.parse(text)


DEFAULT_INGREDIENT_PARSERS = [IngredientParser(), BasicIngredientParser()]


def parse_ingredient_line(ingredient_line, parsers=None) -> Optional[Ingredient]:
    parsers = parsers or DEFAULT_INGREDIENT_PARSERS
    for parser in parsers:
        parsed_ingredient = parser(ingredient_line)
        if parsed_ingredient is not None:
            return parsed_ingredient
