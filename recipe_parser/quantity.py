import unicodedata
from typing import Optional, Union, Iterable

from recipe_parser.units import Unit, NO_UNIT

Number = Union[int, float]


def to_number(value: str) -> Optional[Number]:
    if isinstance(value, (int, float)) or value is None:
        return value
    elif not isinstance(value, str):
        raise TypeError(f'Unsupported type for converting to number: {value!r} (type: {type(value)})')

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


class QuantityUnit:
    def __init__(self, unit, modifier=None):
        self.unit = unit
        self.modifier = modifier

    @classmethod
    def to_quantity_unit(cls, value):
        if isinstance(value, QuantityUnit):
            return value
        elif isinstance(value, Unit):
            return cls(value)
        elif isinstance(value, str):
            return cls(Unit(value, None))
        elif value is None:
            return cls(NO_UNIT)
        else:
            raise TypeError(f'Cannot convert to QuantityUnit, unrecognized type: {type(value)}')

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.unit == other.unit and self.modifier == other.modifier

    def __bool__(self):
        # It's possible for modifier to be non-None while unit is None -- `2 large eggs` has no unit, but a modifier
        return bool(self.unit) or bool(self.modifier)

    def __str__(self):
        value = ''
        if self.modifier is not None:
            value += f'{self.modifier} '

        return value + str(self.unit)

    def __repr__(self):
        return f'{self.__class__.__name__}(unit={self.unit!r}, modifier={self.modifier!r})'

    def to_simple(self, for_unit=None, for_modifier=None) -> dict:
        """
        `for_unit` indicates how to transform the unit.  Options are:
            - `'name'` = Get the name of the unit
            - `'abbreviation'` = Get the abbreviation for the unit
            - `None` = Same as `'name'` (default)
        `for_modifier` indicates how to handle the modifier if one exists.  Options are:
            - `'separate'` = Store the modifier in a separate key ('modifier') in the dictionary returned
            - `'with-unit'` = Store the modifier with the unit (e.g. 'scant tbsp')
            - `'ignore'` = Ignore the modifier
            - `None` = Same as `'with-unit'` (default)
        """
        representation = {}
        for_unit = for_unit or 'name'
        if for_unit == 'name':
            representation['unit'] = self.unit.name
        elif for_unit == 'abbreviation':
            representation['unit'] = self.unit.abbreviation
        else:
            raise ValueError(f'Unrecognized value for for_unit: {for_unit!r}')

        for_modifier = for_modifier or 'with-unit'
        if self.modifier is not None:
            if for_modifier == 'separate':
                representation['modifier'] = self.modifier
            elif for_modifier == 'with-unit':
                representation['unit'] = self.modifier + ' ' + representation['unit']
            elif for_modifier != 'ignore':
                raise ValueError(f'Unrecognized value for for_modifier: {for_modifier!r}')

        return representation


NO_QUANTITY_UNIT = QuantityUnit(None)


class Quantity:
    def __init__(self, amount: Optional[Number], unit: Optional[QuantityUnit], approximate: bool = False):
        self.amount = amount
        self.unit = QuantityUnit.to_quantity_unit(unit)
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

    def to_simple(self, for_unit=None, for_modifier=None) -> dict:
        return {
            'amount': self.amount,
            **self.unit.to_simple(for_unit=for_unit, for_modifier=for_modifier),
            'approximate': self.approximate,
        }


class TotalQuantity:
    def __init__(self, quantities: Iterable[Quantity] = tuple()):
        self.quantities = [q for q in quantities if not q.is_empty()]

    @classmethod
    def to_total_quantity(cls, value):
        if isinstance(value, TotalQuantity):
            return value
        elif isinstance(value, Quantity):
            return TotalQuantity([value])
        elif isinstance(value, Iterable) and not isinstance(value, str) and isinstance(value[0], Quantity):
            return TotalQuantity(value)
        else:
            raise TypeError(f'Cannot convert to TotalQuantity, unrecognized type ({type(value)}: {value!r}')

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

    def to_simple(self, for_unit=None, for_modifier=None):
        if len(self.quantities) > 1:
            raise NotImplementedError('TotalQuantity currently only supports one quantity')

        return self.quantities[0].to_simple(for_unit=for_unit, for_modifier=for_modifier)


NO_QUANTITY = Quantity(None, None)
NO_TOTAL_QUANTITY = TotalQuantity()


class QuantityRange:
    def __init__(self,
                 from_quantity: TotalQuantity = NO_TOTAL_QUANTITY,
                 to_quantity: TotalQuantity = NO_TOTAL_QUANTITY,
                 ):
        self.from_quantity = from_quantity
        self.to_quantity = to_quantity

    def equals(self, other):
        return isinstance(other, self.__class__) and \
               self.from_quantity == other.from_quantity and \
               self.to_quantity == other.to_quantity

    def __eq__(self, other):
        return self.equals(other)

    @classmethod
    def to_quantity_range(cls, value):
        if isinstance(value, QuantityRange):
            return value
        elif isinstance(value, TotalQuantity):
            return QuantityRange(value)
        else:
            return QuantityRange(TotalQuantity.to_total_quantity(value))

    def __str__(self):
        value = str(self.from_quantity)

        value += f' - {self.to_quantity}'

        return value

    def __repr__(self):
        return f'{self.__class__.__name__}(from_quantity={self.from_quantity!r}, to_quantity={self.to_quantity!r})'

    def to_simple(self, for_range=None, for_unit=None, for_modifier=None) -> dict:
        """
        `for_range` indicates how to handle both a `from_quantity` and `to_quantity`.  Options are:
            - `'from'` = use just the `from_quantity`
            - `'to'` = use just the `to_quantity`.  If `to_quantity` is empty, then use `from_quantity`
            - `'range'` = return both the `from_quantity` and `to_quantity`
            - `None` = same as `'from'` (default)
        """
        representation = {}
        if for_range == 'from' or for_range is None:
            representation['quantity'] = self.from_quantity.to_simple(for_unit=for_unit, for_modifier=for_modifier)
        elif for_range == 'to':
            if self.to_quantity == NO_TOTAL_QUANTITY or self.to_quantity is None:
                representation['quantity'] = self.from_quantity.to_simple(for_unit=for_unit, for_modifier=for_modifier)
            else:
                representation['quantity'] = self.to_quantity.to_simple(for_unit=for_unit, for_modifier=for_modifier)
        elif for_range == 'range':
            representation['quantity'] = {
                'from': self.from_quantity.to_simple(for_unit=for_unit, for_modifier=for_modifier),
                'to': self.to_quantity.to_simple(for_unit=for_unit, for_modifier=for_modifier),
            }
        else:
            raise ValueError(f'Unrecognized value for for_range: {for_range!r}')

        return representation



NO_QUANTITY_RANGE = QuantityRange()


class CompleteQuantity:
    def __init__(self,
                 primary_quantity: QuantityRange = NO_QUANTITY_RANGE,
                 equivalent_quantities: Iterable[QuantityRange] = ()
                 ):
        self.primary_quantity = primary_quantity
        self.equivalent_quantities = list(equivalent_quantities)

    def equals(self, other, compare_equivalent_to=False):
        return isinstance(other, self.__class__) and \
               self.primary_quantity == other.primary_quantity and \
               (not compare_equivalent_to or set(self.equivalent_quantities) == set(other.equivalent_quantities))

    def __eq__(self, other):
        return self.equals(other, True)

    @classmethod
    def to_complete_quantity(cls, value):
        if isinstance(value, CompleteQuantity):
            return value
        elif isinstance(value, QuantityRange):
            return cls(value)
        else:
            return cls(QuantityRange.to_quantity_range(value))

    def __str__(self):
        value = str(self.primary_quantity)

        if self.equivalent_quantities:
            value += f' {tuple(self.equivalent_quantities)!s}'

        return value

    def __repr__(self):
        attrs = ('primary_quantity', 'equivalent_quantities')
        str_attrs = ', '.join(f'{attr}={getattr(self, attr)!r}' for attr in attrs)
        return f'{self.__class__.__name__}({str_attrs})'

    def to_simple(self, for_equivalent_quantities=None, for_range=None, for_unit=None, for_modifier=None) -> dict:
        """
        `for_equivalent_quantities` indicates how to handle any equivalent quantities.  Options are:
            - `'ignore'` = ignore the equivalent quantities
            - `'include'` = include the equivalent quantities as a list, pointed to by the key `'equivalent'`
            - `None` = same as `'include'` (default)
        """
        representation = {
            'primary': self.primary_quantity.to_simple(for_range=for_range, for_unit=for_unit, for_modifier=for_modifier)['quantity']
        }

        if for_equivalent_quantities == 'include' or for_equivalent_quantities is None:
            representation['equivalent'] = [q.to_simple(for_range=for_range, for_unit=for_unit, for_modifier=for_modifier)['quantity'] for q in self.equivalent_quantities]
        elif for_equivalent_quantities != 'ignore':
            raise ValueError(f'Unrecognized value for for_equivalent_quantities: {for_equivalent_quantities!r}')

        return representation


NO_COMPLETE_QUANTITY = CompleteQuantity()
