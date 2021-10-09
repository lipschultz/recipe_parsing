from typing import Optional, Iterable, Union

import regex

from recipe_parser.quantity import CompleteQuantity, NO_COMPLETE_QUANTITY, Quantity, to_number, TotalQuantity, \
    QuantityRange, QuantityUnit
from recipe_parser import units as units_module


class Ingredient:
    def __init__(self,
                 name: str,
                 quantity: CompleteQuantity = NO_COMPLETE_QUANTITY,
                 notes: Optional[str] = None,
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

    def __call__(self, text: str) -> Optional[Ingredient]:
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
                note = None
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


FRACTION_REGEX = r'(?:[\u2150-\u215E\u00BC-\u00BE]|(?:\d+\s*/\s*\d+))'
DECIMAL_REGEX = r'\d*(?:\.\d*)?'
NUMBER_REGEX = fr'(?:{DECIMAL_REGEX})?\s*(?:{FRACTION_REGEX})?'


class UnitSizeIngredientParser(BasicIngredientParser):
    def __init__(self,
                 units: units_module.UnitsRegistry,
                 unit_modifiers: Union[Iterable, str],
                 *,
                 approx_regex_pre_amount=r'(?:~|about|approx(?:\.|imately)?)',
                 amount_regex=fr'{NUMBER_REGEX}|a',
                 approx_regex_post_unit=r'(:?\(?\+/-\)?)',
                 optional_regex=BasicIngredientParser.DEFAULT_OPTIONAL_REGEX,
                 ):
        super().__init__(optional_regex=optional_regex)
        self.units = units
        self.unit_modifiers = [unit_modifiers] if isinstance(unit_modifiers, str) else list(unit_modifiers)

        self.approx_regex_pre_amount = approx_regex_pre_amount
        self.amount_regex = amount_regex
        self.approx_regex_post_unit = approx_regex_post_unit

    @property
    def units_regex(self):
        return '|'.join(self.units.all_units_as_regex_strings())

    @property
    def unit_modifiers_regex(self):
        return '|'.join(self.unit_modifiers)

    @property
    def quantity_regex_raw_fmt(self):
        return r'(?P<approxPreAmount{label}>{approx_regex_pre_amount})?\s*' \
               r'(?P<amount{label}>{amount_regex})??\s*' \
               r'(?P<pre_unit_mod{label}>{unit_modifiers_regex})?\s*' \
               r'(?P<unit{label}>{unit_regex})\.?\s*' \
               r'(?P<approxPostUnit{label}>{approx_regex_post_unit})?'

    @property
    def quantity_regex_fmt(self):
        return self.partial_format(
            self.quantity_regex_raw_fmt,
            approx_regex_pre_amount=self.approx_regex_pre_amount,
            amount_regex=self.amount_regex,
            unit_modifiers_regex=self.unit_modifiers_regex,
            unit_regex=self.units_regex,
            approx_regex_post_unit=self.approx_regex_post_unit,
        )

    def get_quantity_regex(self, label):
        return self.quantity_regex_fmt.format(label=label)

    def parse_quantity_match(self, res, label) -> CompleteQuantity:
        unit_modification = res.group(f'pre_unit_mod{label}')
        unit = self.units[res.group(f'unit{label}')]
        if unit is None:
            unit = units_module.NO_UNIT
        quantity_unit = QuantityUnit(unit, unit_modification)

        approximate = bool(res.group(f'approxPreAmount{label}')) or bool(res.group(f'approxPostUnit{label}'))

        amount = res.group(f'amount{label}')
        if isinstance(amount, str) and amount.lower() == 'a':
            # FIXME: This shouldn't be hard-coded -- maybe make a dictionary of regex -> value in __init__?
            amount = 1

        return CompleteQuantity.to_complete_quantity(Quantity(to_number(amount), quantity_unit, approximate))

    @property
    def regex_raw_fmt(self):
        return self.quantity_regex_raw_fmt + r'\s+(?P<name>.+)'

    @property
    def regex_fmt(self):
        return self.partial_format(
            self.regex_raw_fmt,
            approx_regex_pre_amount=self.approx_regex_pre_amount,
            amount_regex=self.amount_regex,
            unit_modifiers_regex=self.unit_modifiers_regex,
            unit_regex=self.units_regex,
            approx_regex_post_unit=self.approx_regex_post_unit,
        )

    def get_regex(self, label=''):
        regex_pattern = self.regex_fmt.format(label=label)
        return regex_pattern

    def parse_match(self, res, label=''):
        quantity = self.parse_quantity_match(res, label=label)

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


class IngredientParser(BasicIngredientParser):
    def __init__(self,
                 *,
                 approx_regex_pre_amount=r'(?:~|about|approx(?:\.|imately)?)',
                 amount_regex=r'[0-9\u2150-\u215E\u00BC-\u00BE,./\s]+|a',
                 amount_required=False,
                 units_registry: units_module.UnitsRegistry = units_module.american_units,
                 approx_regex_post_unit=r'(:?\(?\+/-\)?)',
                 plus_regex='|'.join([r'\+', 'and', 'plus', ',']),
                 dash_regex=r'(?:[-\u2012-\u2015\u2053~]|to)',
                 optional_regex=BasicIngredientParser.DEFAULT_OPTIONAL_REGEX,
                 pre_unit_modifiers='|'.join(units_module.pre_unit_modifiers_sml +
                                             units_module.pre_unit_modifiers_volume),
                 ):
        super().__init__(optional_regex=optional_regex)
        self.approx_regex_pre_amount = approx_regex_pre_amount
        self.amount_regex = amount_regex
        self.amount_required = amount_required
        self.units_registry = units_registry
        self.approx_regex_post_unit = approx_regex_post_unit
        self.plus_regex = plus_regex
        self.dash_regex = dash_regex
        self.pre_unit_modifiers = pre_unit_modifiers

    @property
    def units_regex(self):
        return '|'.join(self.units_registry.all_units_as_regex_strings())

    @property
    def quantity_regex_raw_fmt(self):
        return r'(?P<approxPreAmount{label}>{approx_regex_pre_amount})?\s*' \
               r'(?P<amount{label}>{amount_regex}){amount_required}\s*' \
               r'(?P<pre_unit_mod{label}>{pre_unit_mod_regex})?\s*' \
               r'(?P<unit{label}>{unit_regex})?\.?\s*' \
               r'(?P<approxPostUnit{label}>{approx_regex_post_unit})?'

    @property
    def quantity_regex_fmt(self):
        return self.partial_format(
            self.quantity_regex_raw_fmt,
            approx_regex_pre_amount=self.approx_regex_pre_amount,
            amount_regex=self.amount_regex,
            amount_required=self.amount_required if isinstance(self.amount_required, str) else ('' if self.amount_required else '?'),
            pre_unit_mod_regex=self.pre_unit_modifiers,
            unit_regex=self.units_regex,
            approx_regex_post_unit=self.approx_regex_post_unit,
        )

    def get_quantity_regex(self, label):
        return self.quantity_regex_fmt.format(label=label)

    def parse_quantity_match(self, res, label) -> Quantity:
        unit_modification = res.group(f'pre_unit_mod{label}')
        unit = self.units_registry[res.group(f'unit{label}')]
        if unit is None:
            unit = units_module.NO_UNIT
        quantity_unit = QuantityUnit(unit, unit_modification)

        approximate = bool(res.group(f'approxPreAmount{label}')) or bool(res.group(f'approxPostUnit{label}'))

        amount = res.group(f'amount{label}')
        if isinstance(amount, str) and amount.lower() == 'a':
            # FIXME: This shouldn't be hard-coded -- maybe make a dictionary of regex -> value in __init__?
            amount = 1

        return Quantity(to_number(amount), quantity_unit, approximate)

    @property
    def quantity_total_regex_raw_fmt(self):
        return r'{quantity_regex}(?:\s*(?:{plus_regex})\s*(?P<subsequent{label}>{quantity_regex_subsequent}))*'

    @property
    def quantity_total_regex_fmt(self):
        return self.partial_format(
            self.quantity_total_regex_raw_fmt,
            quantity_regex=self.quantity_regex_fmt,
            plus_regex=self.plus_regex,
            quantity_regex_subsequent=self.partial_format(self.quantity_regex_fmt, label="{label}_subsequent"),
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
        return r'{quantity_total_from_regex}(?:\s*{dash_regex}\s*{quantity_total_to_regex})?' + \
               r'\s*(?:\({quantity_total_equivalent_regex}\))?'

    @property
    def quantity_range_regex_fmt(self):
        return self.partial_format(
            self.quantity_range_regex_raw_fmt,
            quantity_total_from_regex=self.partial_format(self.quantity_total_regex_fmt, label="{label}from"),
            dash_regex=self.dash_regex,
            quantity_total_to_regex=self.partial_format(self.quantity_total_regex_fmt, label="{label}to"),
            quantity_total_equivalent_regex=self.partial_format(self.quantity_total_regex_fmt, label="{label}equivalent"),
        )

    def get_quantity_range_regex(self, label=''):
        return self.quantity_range_regex_fmt.format(label=label)

    def parse_quantity_range_match(self, res, label=''):
        from_quantity = self.parse_quantity_total_match(res, f"{label}from")
        to_quantity = self.parse_quantity_total_match(res, f"{label}to")

        if len(from_quantity) != 0 and not from_quantity[0].unit and len(to_quantity) != 0:
            from_quantity[0].unit = to_quantity[0].unit
            if to_quantity[0].amount is None:
                # This is probably a case of, e.g., "8-oz steak": "8" went to from_quantity and "oz" went to to_quantity
                to_quantity = TotalQuantity()

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
        return r'{quantity_range_regex}\s+(?P<name>.+)'

    @property
    def regex_fmt(self):
        return self.partial_format(
            self.regex_raw_fmt,
            quantity_range_regex=self.quantity_range_regex_fmt,
        )

    def get_regex(self, label=''):
        return self.regex_fmt.format(label=label)

    def parse_match(self, res, label=''):
        quantity = self.parse_quantity_range_match(res, label=label)

        name = res.group('name').strip()
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


class IngredientBeforeQuantity(IngredientParser):
    def __init__(self,
                 *,
                 approx_regex_pre_amount=r'(?:~|about|approx(?:\.|imately)?)',
                 amount_regex=r'[0-9\u2150-\u215E\u00BC-\u00BE,./\s]+|a',
                 amount_required=True,
                 units_registry: units_module.UnitsRegistry = units_module.american_units,
                 approx_regex_post_unit=r'(:?\(?\+/-\)?)',
                 plus_regex='|'.join([r'\+', 'and', 'plus', ',']),
                 dash_regex=r'(?:[-\u2012-\u2015\u2053~]|to)',
                 optional_regex=BasicIngredientParser.DEFAULT_OPTIONAL_REGEX,
                 pre_unit_modifiers='|'.join(units_module.pre_unit_modifiers_sml +
                                             units_module.pre_unit_modifiers_volume),
                 ingredient_quantity_separator_regex=r'[-\u2012-\u2015\u2053~]',
                 ):
        super().__init__(approx_regex_pre_amount=approx_regex_pre_amount, amount_regex=amount_regex,
                         amount_required=amount_required, units_registry=units_registry,
                         approx_regex_post_unit=approx_regex_post_unit, plus_regex=plus_regex, dash_regex=dash_regex,
                         optional_regex=optional_regex, pre_unit_modifiers=pre_unit_modifiers)
        self.ingredient_quantity_separator_regex = ingredient_quantity_separator_regex

    @property
    def regex_raw_fmt(self):
        return r'(?P<name>.+?)\s*{ingredient_quantity_separator_regex}?\s*' + self.quantity_range_regex_fmt

    @property
    def regex_fmt(self):
        return self.partial_format(
            super().regex_fmt,
            ingredient_quantity_separator_regex=self.ingredient_quantity_separator_regex,
        )


DEFAULT_BULLET_REGEXES = [
    r'^(\s*[-*]\s*)',
]


def strip_bullet_points(ingredient_line, patterns: Union[bool, str, Iterable[str]] = True):
    """
    Remove a bullet point from the ingredient line.

    Loop over patterns, using regex.sub to attempt to replace any matches
    with an empty string.  Once a pattern changes the ingredient_line,
    the new ingredient_line will be returned.

    If `patterns` is True, then DEFAULT_BULLET_REGEXES will be used.  If
    `patterns` is falsey, then this function will return the original
    ingredient_line.
    """
    if not patterns:
        return ingredient_line

    if patterns is True:
        patterns = DEFAULT_BULLET_REGEXES
    elif isinstance(patterns, str):
        patterns = [patterns]

    for pattern in patterns:
        result = regex.sub(pattern, '', ingredient_line)
        if result != ingredient_line:
            return result
    return ingredient_line


DEFAULT_INGREDIENT_PARSERS = [
    UnitSizeIngredientParser(
        units=units_module.item_units,
        unit_modifiers=fr"\(?{NUMBER_REGEX}"
                       r"(?:-|\s+)?"
                       fr"(?:{'|'.join(units_module.weight_units.all_units_as_regex_strings())})\)?",
    ),
    IngredientParser(),
    IngredientBeforeQuantity(),
    BasicIngredientParser()
]


def parse_ingredient_line(ingredient_line, parsers=None, strip_bullets=True) -> Optional[Ingredient]:
    parsers = parsers or DEFAULT_INGREDIENT_PARSERS

    ingredient_line = strip_bullet_points(ingredient_line, strip_bullets)
    for parser in parsers:
        parsed_ingredient = parser(ingredient_line)
        if parsed_ingredient is not None:
            return parsed_ingredient
    return None
