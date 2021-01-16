from typing import AnyStr, Optional

import regex

from recipe_parser.quantity import CompleteQuantity, NO_COMPLETE_QUANTITY, Quantity, to_number, TotalQuantity, \
    QuantityRange
from recipe_parser.units import american_units, UnitsRegistry


class Ingredient:
    def __init__(self,
                 name: AnyStr,
                 quantity: CompleteQuantity = NO_COMPLETE_QUANTITY,
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

        quantity = NO_COMPLETE_QUANTITY
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
                 approx_regex_pre_amount=r'(?:~|about|approx(?:\.|imately)?)',
                 amount_regex=r'[0-9\u2150-\u215E\u00BC-\u00BE,./\s]+|a',
                 units_registry: UnitsRegistry = american_units,
                 approx_regex_post_unit=r'(:?\(?\+/-\)?)',
                 plus_regex='|'.join([r'\+', 'and', 'plus', ',']),
                 dash_regex=r'(?:[-\u2012-\u2015\u2053~]|to)',
                 optional_regex=BasicIngredientParser.DEFAULT_OPTIONAL_REGEX,
                 ):
        super().__init__(optional_regex=optional_regex)
        self.approx_regex_pre_amount = approx_regex_pre_amount
        self.amount_regex = amount_regex
        self.units_registry = units_registry
        self.approx_regex_post_unit = approx_regex_post_unit
        self.plus_regex = plus_regex
        self.dash_regex = dash_regex

    @property
    def units_regex(self):
        return '|'.join(self.units_registry.all_units_as_regex_strings())

    @property
    def quantity_regex_raw_fmt(self):
        return r'(?P<approxPreAmount{label}>{approx_regex_pre_amount})?\s*(?P<amount{label}>{amount_regex})?\s*(?P<unit{label}>{unit_regex})?\.?\s*(?P<approxPostUnit{label}>{approx_regex_post_unit})?'

    @property
    def quantity_regex_fmt(self):
        return self.partial_format(
            self.quantity_regex_raw_fmt,
            approx_regex_pre_amount=self.approx_regex_pre_amount,
            amount_regex=self.amount_regex,
            unit_regex=self.units_regex,
            approx_regex_post_unit=self.approx_regex_post_unit,
        )

    def get_quantity_regex(self, label):
        return self.quantity_regex_fmt.format(label=label)

    def parse_quantity_match(self, res, label) -> Quantity:
        unit = res.group(f'unit{label}')
        approximate = bool(res.group(f'approxPreAmount{label}')) or bool(res.group(f'approxPostUnit{label}'))
        amount = res.group(f'amount{label}')
        if isinstance(amount, str) and amount.lower() == 'a':
            amount = 1

        return Quantity(to_number(amount), self.units_registry[unit], approximate)

    @property
    def quantity_total_regex_raw_fmt(self):
        return self.quantity_regex_raw_fmt + \
               r'(?:\s*(?:{plus_regex})\s*(?P<subsequent{label}>' + \
               self.partial_format(self.quantity_regex_raw_fmt, label="{label}_subsequent") + '))*'

    @property
    def quantity_total_regex_fmt(self):
        return self.partial_format(
            self.quantity_total_regex_raw_fmt,
            approx_regex_pre_amount=self.approx_regex_pre_amount,
            amount_regex=self.amount_regex,
            unit_regex=self.units_regex,
            approx_regex_post_unit=self.approx_regex_post_unit,
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
            approx_regex_pre_amount=self.approx_regex_pre_amount,
            amount_regex=self.amount_regex,
            unit_regex=self.units_regex,
            approx_regex_post_unit=self.approx_regex_post_unit,
            plus_regex=self.plus_regex,
            dash_regex=self.dash_regex,
        )

    def get_quantity_range_regex(self, label=''):
        return self.quantity_range_regex_fmt.format(label=label)

    def parse_quantity_range_match(self, res, label=''):
        from_quantity = self.parse_quantity_total_match(res, f"{label}from")
        to_quantity = self.parse_quantity_total_match(res, f"{label}to")

        if len(from_quantity) and from_quantity[0].unit is None and len(to_quantity):
            from_quantity[0].raw_unit = to_quantity[0].raw_unit

        quantity_range = QuantityRange(from_quantity, to_quantity)

        equivalent_quantity = self.parse_quantity_total_match(res, f"{label}equivalent")
        if equivalent_quantity:
            # FIXME: this equivalent should be able to be a range
            equivalent_quantity = [QuantityRange(equivalent_quantity)]
        else:
            equivalent_quantity = []
        complete_quantity = CompleteQuantity(quantity_range, equivalent_quantity)
        return complete_quantity

    @property
    def regex_raw_fmt(self):
        return self.quantity_range_regex_raw_fmt + r'\s+(?P<name>.+)'

    @property
    def regex_fmt(self):
        return self.partial_format(
            self.regex_raw_fmt,
            approx_regex_pre_amount=self.approx_regex_pre_amount,
            amount_regex=self.amount_regex,
            unit_regex=self.units_regex,
            approx_regex_post_unit=self.approx_regex_post_unit,
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
