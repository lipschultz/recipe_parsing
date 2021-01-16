import itertools
from typing import Iterable, Optional

import regex


class Unit:
    def __init__(self, name, abbreviation, plural_name=None, plural_abbreviation=None, other_representations=tuple()):
        self.name = name
        self.abbreviation = abbreviation
        self.plural_name = plural_name
        self.plural_abbreviation = plural_abbreviation
        self.other_representations = other_representations

    def __str__(self):
        return self.name

    def __repr__(self):
        attr_names = ('name', 'abbreviation', 'plural_name', 'plural_abbreviation', 'other_representations')
        attrs = ', '.join(f'{name}={getattr(self, name)!r}' for name in attr_names)
        return f'{self.__class__.__name__}({attrs})'

    def __eq__(self, other):
        if isinstance(other, Unit):
            return all(representation in other for representation in self)
        else:
            return other in self

    def __bool__(self):
        return any(self)

    def get_name_for(self, value):
        if value == 1 or self.plural_name is None:
            return self.name
        else:
            return self.plural_name

    def get_abbreviation_for(self, value):
        if value == 1:
            return self.abbreviation or self.name
        else:
            return self.plural_abbreviation or self.abbreviation or self.plural_name or self.name

    def __iter__(self):
        return (
            u
            for u in (self.name, self.abbreviation, self.plural_name, self.plural_abbreviation, *self.other_representations)
            if u is not None
        )


_units_weights = [
    Unit('pound', 'lb', 'pounds', 'lbs'),
    Unit('ounce', 'oz', 'ounces'),
    Unit('gram', 'g', 'grams', other_representations=('grm', 'grms', 'gr')),
    Unit('milligram', 'mg', 'milligrams'),
    Unit('kilogram', 'kg', 'kilograms', other_representations=('kilo', 'kilos')),
]

_units_volumes = [
    Unit('tablespoon', 'tbsp', 'tablespoons', other_representations=('T', 'tbs', 'tbsps', 'tb')),
    Unit('teaspoon', 'tsp', 'teaspoons', other_representations=('t', 'tsps')),
    Unit('cup', 'c', 'cups'),
    Unit('pint', 'pt', 'pints', other_representations=('p',)),
    Unit('quart', 'qt', 'quarts'),
    Unit('gallon', 'gal', 'gallons'),
    Unit('fluid ounce', 'fl oz', 'fluid ounces', other_representations=('fl. oz.', 'oz. fl.')),
    Unit('liter', 'L', 'liters', other_representations=('litre', 'litres', 'l')),
    Unit('milliliter', 'mL', 'milliliters', other_representations=('millilitre', 'millilitres', 'ml')),
    Unit('centiliter', 'cL', 'centiliters', other_representations=('centilitre', 'centilitres', 'cl')),
    Unit('deciliter', 'dL', 'deciliters', other_representations=('decilitre', 'decilitres', 'dl')),
]

_units_length = [
    Unit('centimeter', 'cm', 'centimeters', other_representations=('centimetre', 'centimetres')),
    Unit('inch', 'in', 'inches'),
]

_units_amounts = [
    Unit('ball', None, 'balls'),
    Unit('block', None, 'blocks'),
    Unit('box', None, 'boxes'),
    Unit('bunch', None, 'bunches'),
    Unit('can', None, 'cans'),
    Unit('cloves', None, 'clove'),
    Unit('cookie', None, 'cookies'),
    Unit('drop', None, 'drops'),
    Unit('dollop', None, 'dollops'),
    Unit('head', None, 'heads'),
    Unit('loaf', None, 'loaves'),
    Unit('pack', None, 'packs'),
    Unit('package', 'pkg', 'packages', 'pkgs'),
    Unit('pie', None, 'pies'),
    Unit('piece', None, 'pieces'),
    Unit('pinch', None, 'pinches'),
    Unit('roll', None, 'rolls'),
    Unit('serving', None, 'servings'),
    Unit('slice', None, 'slices'),
    Unit('stalk', None, 'stalks'),
    Unit('stick', None, 'sticks'),
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


_all_units = _units_weights + _units_volumes + _units_length + _units_amounts


class UnitsRegistry:
    def __init__(self, units: Iterable[Unit]):
        self.units = list(units)
        self._units_map = None

    def transform_for_regex(self, unit):
        return unit.replace(' ', r'\s+').replace('.', r'\.')

    def normalize_for_lookup(self, unit):
        if not isinstance(unit, str):
            return unit
        try:
            return regex.sub(r'\s+', ' ', unit)
        except TypeError as ex:
            print(ex)
            print('unit:', unit)
            raise

    def all_units_as_strings(self) -> Iterable[str]:
        return itertools.chain.from_iterable(self.units)

    def all_units_as_regex_strings(self) -> Iterable[str]:
        return (self.transform_for_regex(unit) for unit in self.all_units_as_strings())

    def __getitem__(self, item) -> Optional[Unit]:
        if self._units_map is None:
            self._units_map = {}
            for unit in self.units:
                unit_map = {self.normalize_for_lookup(u): unit for u in unit}

                existing_units = {u: (v, self._units_map.get(u)) for u, v in unit_map.items()}
                existing_units = {u: (new, existing) for u, (new, existing) in existing_units.items() if
                                  existing is not None}
                if existing_units:
                    print(f'Warning: Some units already exist:')
                    print('\n'.join(f'\t{u}:\n\t\tnew: {new!r}\n\t\texisting: {existing!r}' for u, (new, existing) in
                                    existing_units.items()))
                    for u in existing_units:
                        unit_map.pop(u)

                self._units_map.update(unit_map)

        item = self.normalize_for_lookup(item)
        if item is None:
            return None

        # First, case-sensitive search, then case-insensitive search in case of non-standard capitalization
        return self._units_map.get(item, self._units_map.get(item.lower()))


american_units = UnitsRegistry(_all_units)
