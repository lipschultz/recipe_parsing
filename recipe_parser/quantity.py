import unicodedata
from typing import AnyStr, Optional, Union, Iterable

from recipe_parser.units import Unit

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
    def __init__(self, amount: Optional[Number], unit: Union[None, AnyStr, Unit], approximate: bool = False):
        self.amount = amount
        self.raw_unit = unit
        self.approximate = approximate

    @property
    def unit(self):
        if isinstance(self.raw_unit, Unit):
            return self.raw_unit.name
        else:
            return self.raw_unit

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
        return bool(self.amount or self.raw_unit)

    def is_empty(self):
        return not bool(self)

    def __str__(self):
        return f'{"~" if self.approximate else ""}{self.amount} {self.unit}'

    def __repr__(self):
        return f'{self.__class__.__name__}({self.amount!r}, {self.raw_unit!r}, approximate={self.approximate!r})'


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
                 ):
        self.from_quantity = from_quantity
        self.to_quantity = to_quantity

    def equals(self, other):
        return isinstance(other, self.__class__) and self.from_quantity == other.from_quantity and self.to_quantity == other.to_quantity

    def __eq__(self, other):
        return self.equals(other)

    def __str__(self):
        value = str(self.from_quantity)

        value += f' - {self.to_quantity}'

        return value

    def __repr__(self):
        return f'{self.__class__.__name__}(from_quantity={self.from_quantity!r}, to_quantity={self.to_quantity!r})'


NO_QUANTITY_RANGE = QuantityRange()


class CompleteQuantity:
    def __init__(self, primary_quantity: QuantityRange = NO_QUANTITY_RANGE, equivalent_quantities: Iterable[QuantityRange] = ()):
        self.primary_quantity = primary_quantity
        self.equivalent_quantities = list(equivalent_quantities)

    def equals(self, other, compare_equivalent_to=False):
        return isinstance(other, self.__class__) and \
               self.primary_quantity == other.primary_quantity and \
               (not compare_equivalent_to or set(self.equivalent_quantities) == set(other.equivalent_quantities))

    def __eq__(self, other):
        return self.equals(other, True)

    def __str__(self):
        value = str(self.primary_quantity)

        if self.equivalent_quantities:
            value += f' {tuple(self.equivalent_quantities)!s}'

        return value

    def __repr__(self):
        return f'{self.__class__.__name__}(primary_quantity={self.primary_quantity!r}, equivalent_quantities={self.equivalent_quantities!r})'


NO_COMPLETE_QUANTITY = CompleteQuantity()
