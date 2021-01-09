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


all_units = _units_weights + _units_volumes + _units_length + _units_amounts
