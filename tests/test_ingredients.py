import pytest

from recipe_parser import ingredients, units, quantity


@pytest.mark.parametrize("str_num, expected_num", [
    ('2', 2),
    ('20', 20),
    ('205', 205),
    ('205.13', 205.13),
    ('2.3', 2.3),
    ('0.5', 0.5),
    ('.5', 0.5),
    ('1/2', 0.5),
    ('2 1/2', 2.5),
    ('2 1/2', 2.5),
    ('½', 0.5),
    ('2 ½', 2.5),
    ('2½', 2.5),
    ('2 ½', 2.5),
    ('1 /2', 0.5),
    ('1/ 2', 0.5),
    ('1 / 2', 0.5),
    ('not number', None),
    ('', None),
    ('has1number', None),
    ('12number', None),
    ('number13', None),
    (10, 10),
    (13.8, 13.8),
])
def test_converts_string_to_number(str_num, expected_num):
    assert ingredients.to_number(str_num) == expected_num


def assert_unit_equal(expected, actual):
    assert isinstance(actual, units.Unit)

    assert expected.name == actual.name
    assert expected.abbreviation == actual.abbreviation
    assert expected.plural_name == actual.plural_name
    assert expected.plural_abbreviation == actual.plural_abbreviation
    assert expected.other_representations == actual.other_representations


def assert_quantity_unit_equal(expected, actual):
    assert isinstance(actual, quantity.QuantityUnit)
    assert_unit_equal(expected.unit, actual.unit)
    assert expected.modifier == actual.modifier


def assert_quantity_equal(expected, actual, test_approximate=True):
    assert isinstance(actual, ingredients.Quantity)

    assert expected.amount == actual.amount
    assert_quantity_unit_equal(expected.unit, actual.unit)
    if test_approximate and expected.amount is not None:
        assert expected.approximate == actual.approximate


def assert_total_quantity_equal(expected, actual):
    assert isinstance(actual, ingredients.TotalQuantity)
    assert len(expected) == len(actual)

    for i, expected_quantity in enumerate(expected):
        assert_quantity_equal(expected_quantity, actual[i])


def assert_quantity_range_equal(expected, actual):
    if expected is None:
        assert expected == actual
    else:
        assert isinstance(actual, ingredients.QuantityRange)

        assert_total_quantity_equal(expected.from_quantity, actual.from_quantity)
        assert_total_quantity_equal(expected.to_quantity, actual.to_quantity)


def assert_complete_quantity_equal(expected, actual):
    assert isinstance(actual, ingredients.CompleteQuantity)

    assert_quantity_range_equal(expected.primary_quantity, actual.primary_quantity)

    assert len(expected.equivalent_quantities) == len(actual.equivalent_quantities)
    for expected_equivalent, actual_equivalent in zip(expected.equivalent_quantities, actual.equivalent_quantities):
        assert_quantity_range_equal(expected_equivalent, actual_equivalent)


def assert_ingredient_equal(expected, actual):
    assert isinstance(actual, ingredients.Ingredient)

    assert_complete_quantity_equal(expected.quantity, actual.quantity)
    assert expected.name == actual.name
    assert expected.notes == actual.notes
    assert expected.optional == actual.optional


def make_total_quantity(quantities):
    return ingredients.TotalQuantity([
        ingredients.Quantity(
            abs(quant[0]) if quant[0] else None,
            quantity.QuantityUnit(
                units.american_units[quant[1]] or units.NO_UNIT,
                quant[2] if len(quant) > 2 else None
            ),
            approximate=(quant[0] is not None and quant[0] < 0)
        )
        for quant in quantities
    ])


def make_ingredient(expected_info):
    expected_quantity = ingredients.CompleteQuantity(
        primary_quantity=ingredients.QuantityRange(
            from_quantity=make_total_quantity(expected_info[1].get('from', [])),
            to_quantity=make_total_quantity(expected_info[1].get('to', []))
        ),
        equivalent_quantities=[
            ingredients.QuantityRange(
                from_quantity=make_total_quantity(equiv.get('from', [])),
                to_quantity=make_total_quantity(equiv.get('to', []))
            )
            for equiv in expected_info[1].get('equiv', [])
        ]
    )
    return ingredients.Ingredient(
        expected_info[0],
        expected_quantity,
        notes=expected_info[2] if len(expected_info) >= 3 else None,
        optional=expected_info[3] if len(expected_info) >= 4 else False,
    )


@pytest.mark.parametrize("ingredient_line, expected_result", [
    # Amount unit name
    ('2 tbsp chili powder', ('chili powder', {'from': [(2, 'tbsp')]})),
    ('2 Tbsp chili powder', ('chili powder', {'from': [(2, 'tbsp')]})),
    ('2 Tbsp. chili powder', ('chili powder', {'from': [(2, 'tbsp')]})),
    ('2 tbsp. chili powder', ('chili powder', {'from': [(2, 'tbsp')]})),
    ('2tbsp chili powder', ('chili powder', {'from': [(2, 'tbsp')]})),
    ('200 grams flour', ('flour', {'from': [(200, 'grams')]})),
    ('½ teaspoons chili powder', ('chili powder', {'from': [(0.5, 'teaspoons')]})),
    ('½teaspoons chili powder', ('chili powder', {'from': [(0.5, 'teaspoons')]})),
    ('1/2 teaspoons chili powder', ('chili powder', {'from': [(0.5, 'teaspoons')]})),
    ('1/2teaspoons chili powder', ('chili powder', {'from': [(0.5, 'teaspoons')]})),
    ('2\u2009½ teaspoons chili powder', ('chili powder', {'from': [(2.5, 'teaspoons')]})),
    ('2\u2009½teaspoons chili powder', ('chili powder', {'from': [(2.5, 'teaspoons')]})),
    ('2 ½ teaspoons chili powder', ('chili powder', {'from': [(2.5, 'teaspoons')]})),
    ('2 ½teaspoons chili powder', ('chili powder', {'from': [(2.5, 'teaspoons')]})),
    ('2\u20091/2 teaspoons chili powder', ('chili powder', {'from': [(2.5, 'teaspoons')]})),
    ('2\u20091/2teaspoons chili powder', ('chili powder', {'from': [(2.5, 'teaspoons')]})),
    ('2 1/2 teaspoons chili powder', ('chili powder', {'from': [(2.5, 'teaspoons')]})),
    ('2 1/2teaspoons chili powder', ('chili powder', {'from': [(2.5, 'teaspoons')]})),
    ('2½ teaspoons chili powder', ('chili powder', {'from': [(2.5, 'teaspoons')]})),
    ('2½teaspoons chili powder', ('chili powder', {'from': [(2.5, 'teaspoons')]})),
    ('2½ teaspoons of chili powder', ('chili powder', {'from': [(2.5, 'teaspoons')]})),
    ('2½ teaspoons Of chili powder', ('chili powder', {'from': [(2.5, 'teaspoons')]})),
    ('8-oz steak', ('steak', {'from': [(8, 'oz')]})),

    # Amount unit name (with spaces in fraction)
    ('1 /2 teaspoons chili powder', ('chili powder', {'from': [(0.5, 'teaspoons')]})),
    ('1/ 2 teaspoons chili powder', ('chili powder', {'from': [(0.5, 'teaspoons')]})),
    ('1 /2teaspoons chili powder', ('chili powder', {'from': [(0.5, 'teaspoons')]})),
    ('1/ 2teaspoons chili powder', ('chili powder', {'from': [(0.5, 'teaspoons')]})),

    # Amount name
    ('2 onions', ('onions', {'from': [(2, None)]})),
    ('2 red onions', ('red onions', {'from': [(2, None)]})),
    ('½ onions', ('onions', {'from': [(0.5, None)]})),
    ('½ red onions', ('red onions', {'from': [(0.5, None)]})),
    ('1/2 onions', ('onions', {'from': [(0.5, None)]})),
    ('1/2 red onions', ('red onions', {'from': [(0.5, None)]})),
    ('2\u2009½ onions', ('onions', {'from': [(2.5, None)]})),
    ('2 ½ onions', ('onions', {'from': [(2.5, None)]})),
    ('2\u20091/2 onions', ('onions', {'from': [(2.5, None)]})),
    ('2 1/2 onions', ('onions', {'from': [(2.5, None)]})),
    ('2\u2009½ red onions', ('red onions', {'from': [(2.5, None)]})),
    ('2 ½ red onions', ('red onions', {'from': [(2.5, None)]})),
    ('2\u20091/2 red onions', ('red onions', {'from': [(2.5, None)]})),
    ('2 1/2 red onions', ('red onions', {'from': [(2.5, None)]})),
    ('2½ onions', ('onions', {'from': [(2.5, None)]})),

    # Name
    ('salt', ('salt', {'from': [(None, None)]})),
    ('black pepper', ('black pepper', {'from': [(None, None)]})),
    ('salt and black pepper to taste', ('salt and black pepper to taste', {'from': [(None, None)]})),
])
def test_parses_ingredient_line(ingredient_line, expected_result):
    actual = ingredients.parse_ingredient_line(ingredient_line)
    expected = make_ingredient(expected_result)
    assert_ingredient_equal(expected, actual)


@pytest.mark.parametrize("ingredient_line, expected_result", [
    ('200 mL milk, room temperature', ('milk', {'from': [(200, 'mL')]}, 'room temperature')),
    ('200 mL milk (room temperature)', ('milk', {'from': [(200, 'mL')]}, 'room temperature')),
    ('200 mL whole milk, room temperature', ('whole milk', {'from': [(200, 'mL')]}, 'room temperature')),
    ('200 mL whole milk (room temperature)', ('whole milk', {'from': [(200, 'mL')]}, 'room temperature')),
    ('2 onions, diced', ('onions', {'from': [(2, None)]}, 'diced')),
    ('2 onions (diced)', ('onions', {'from': [(2, None)]}, 'diced')),
    ('2 blocks tofu, drained, diced, and frozen', ('tofu', {'from': [(2, 'blocks')]}, 'drained, diced, and frozen')),
    ('2 blocks tofu (drained, diced, and frozen)', ('tofu', {'from': [(2, 'blocks')]}, 'drained, diced, and frozen')),
])
def test_parses_ingredient_line_with_notes(ingredient_line, expected_result):
    actual = ingredients.parse_ingredient_line(ingredient_line)
    expected = make_ingredient(expected_result)
    assert_ingredient_equal(expected, actual)


@pytest.mark.parametrize("ingredient_line, expected_result", [
    # Without notes
    ('2 optional dollops of sour cream', ('sour cream', {'from': [(2, 'dollops')]}, None, True)),
    ('2 drops red food coloring, optional', ('red food coloring', {'from': [(2, 'drops')]}, None, True)),
    ('2 drops red food coloring (optional)', ('red food coloring', {'from': [(2, 'drops')]}, None, True)),

    # With notes
    ('200 mL milk, room temperature (optional)', ('milk', {'from': [(200, 'mL')]}, 'room temperature', True)),
    ('200 mL milk, room temperature, optional', ('milk', {'from': [(200, 'mL')]}, 'room temperature', True)),
    ('200 mL milk, room temperature optional', ('milk', {'from': [(200, 'mL')]}, 'room temperature', True)),
    ('200 mL milk (room temperature) (optional)', ('milk', {'from': [(200, 'mL')]}, 'room temperature', True)),
    ('200 mL milk (room temperature, optional)', ('milk', {'from': [(200, 'mL')]}, 'room temperature', True)),
    ('200 mL milk (room temperature), optional', ('milk', {'from': [(200, 'mL')]}, 'room temperature', True)),
])
def test_parses_optional_ingredient_line(ingredient_line, expected_result):
    actual = ingredients.parse_ingredient_line(ingredient_line)
    expected = make_ingredient(expected_result)
    assert_ingredient_equal(expected, actual)


@pytest.mark.parametrize("ingredient_line, expected_result", [
    # number dash number
    ('2-3 tbsp chili powder', ('chili powder', {'from': [(2, 'tbsp')], 'to': [(3, 'tbsp')]})),
    ('2-3tbsp chili powder', ('chili powder', {'from': [(2, 'tbsp')], 'to': [(3, 'tbsp')]})),
    ('½-¾ teaspoons chili powder', ('chili powder', {'from': [(0.5, 'teaspoons')], 'to': [(0.75, 'teaspoons')]})),
    ('1/2-3/4 teaspoons chili powder', ('chili powder', {'from': [(0.5, 'teaspoons')], 'to': [(0.75, 'teaspoons')]})),
    ('2-3 tbsp chili powder', ('chili powder', {'from': [(2, 'tbsp')], 'to': [(3, 'tbsp')]})),
    ('½-¾ teaspoons chili powder', ('chili powder', {'from': [(0.5, 'teaspoons')], 'to': [(0.75, 'teaspoons')]})),
    ('1/2-3/4 teaspoons chili powder', ('chili powder', {'from': [(0.5, 'teaspoons')], 'to': [(0.75, 'teaspoons')]})),
    ('2½-2¾ teaspoons chili powder', ('chili powder', {'from': [(2.5, 'teaspoons')], 'to': [(2.75, 'teaspoons')]})),
    ('2 ½-2 ¾ teaspoons chili powder', ('chili powder', {'from': [(2.5, 'teaspoons')], 'to': [(2.75, 'teaspoons')]})),
    ('2 1/2-2 3/4 teaspoons chili powder', ('chili powder', {'from': [(2.5, 'teaspoons')], 'to': [(2.75, 'teaspoons')]})),

    # number dash number with spaces
    ('2 - 3 tbsp chili powder', ('chili powder', {'from': [(2, 'tbsp')], 'to': [(3, 'tbsp')]})),
    ('½ - ¾ teaspoons chili powder', ('chili powder', {'from': [(0.5, 'teaspoons')], 'to': [(0.75, 'teaspoons')]})),
    ('1/2 - 3/4 teaspoons chili powder', ('chili powder', {'from': [(0.5, 'teaspoons')], 'to': [(0.75, 'teaspoons')]})),
    ('2 - 3 tbsp chili powder', ('chili powder', {'from': [(2, 'tbsp')], 'to': [(3, 'tbsp')]})),
    ('½ - ¾ teaspoons chili powder', ('chili powder', {'from': [(0.5, 'teaspoons')], 'to': [(0.75, 'teaspoons')]})),
    ('1/2 - 3/4 teaspoons chili powder', ('chili powder', {'from': [(0.5, 'teaspoons')], 'to': [(0.75, 'teaspoons')]})),
    ('2½ - 2¾ teaspoons chili powder', ('chili powder', {'from': [(2.5, 'teaspoons')], 'to': [(2.75, 'teaspoons')]})),
    ('2 ½ - 2 ¾ teaspoons chili powder', ('chili powder', {'from': [(2.5, 'teaspoons')], 'to': [(2.75, 'teaspoons')]})),
    ('2 1/2 - 2 3/4 teaspoons chili powder', ('chili powder', {'from': [(2.5, 'teaspoons')], 'to': [(2.75, 'teaspoons')]})),

    # number other-dashes number
    ('2~3 tbsp chili powder', ('chili powder', {'from': [(2, 'tbsp')], 'to': [(3, 'tbsp')]})),
    ('2‒3 tbsp chili powder', ('chili powder', {'from': [(2, 'tbsp')], 'to': [(3, 'tbsp')]})),
    ('2–3 tbsp chili powder', ('chili powder', {'from': [(2, 'tbsp')], 'to': [(3, 'tbsp')]})),
    ('2—3 tbsp chili powder', ('chili powder', {'from': [(2, 'tbsp')], 'to': [(3, 'tbsp')]})),
    ('2―3 tbsp chili powder', ('chili powder', {'from': [(2, 'tbsp')], 'to': [(3, 'tbsp')]})),
    ('2⁓3 tbsp chili powder', ('chili powder', {'from': [(2, 'tbsp')], 'to': [(3, 'tbsp')]})),

    # number unit dash number unit
    ('2 tsp-3 tbsp chili powder', ('chili powder', {'from': [(2, 'tsp')], 'to': [(3, 'tbsp')]})),
    ('2tsp-3 tbsp chili powder', ('chili powder', {'from': [(2, 'tsp')], 'to': [(3, 'tbsp')]})),
    ('2tsp-3tbsp chili powder', ('chili powder', {'from': [(2, 'tsp')], 'to': [(3, 'tbsp')]})),
    ('2 tsp-3tbsp chili powder', ('chili powder', {'from': [(2, 'tsp')], 'to': [(3, 'tbsp')]})),
])
def test_parses_amount_range(ingredient_line, expected_result):
    actual = ingredients.parse_ingredient_line(ingredient_line)
    expected = make_ingredient(expected_result)
    assert_ingredient_equal(expected, actual)


@pytest.mark.parametrize("ingredient_line, expected_result", [
    ('1 cup (240 mL) canola or other vegetable oil', ('canola or other vegetable oil', {'from': [(1, 'cup')], 'equiv': [{'from': [(240, 'mL')]}]})),
    ('1 1/4 cup (295 mL) canola or other vegetable oil', ('canola or other vegetable oil', {'from': [(1.25, 'cup')], 'equiv': [{'from': [(295, 'mL')]}]})),
    ('1 ¼ cup (295 mL) canola or other vegetable oil', ('canola or other vegetable oil', {'from': [(1.25, 'cup')], 'equiv': [{'from': [(295, 'mL')]}]})),
    ('1¼ cup (295 mL) canola or other vegetable oil', ('canola or other vegetable oil', {'from': [(1.25, 'cup')], 'equiv': [{'from': [(295, 'mL')]}]})),

    ('240 mL (1 cup) canola or other vegetable oil', ('canola or other vegetable oil', {'from': [(240, 'mL')], 'equiv': [{'from': [(1, 'cup')]}]})),
    ('295 mL (1 1/4 cup) canola or other vegetable oil', ('canola or other vegetable oil', {'from': [(295, 'mL')], 'equiv': [{'from': [(1.25, 'cup')]}]})),
    ('295 mL (1 ¼ cup) canola or other vegetable oil', ('canola or other vegetable oil', {'from': [(295, 'mL')], 'equiv': [{'from': [(1.25, 'cup')]}]})),
    ('295 mL (1¼ cup) canola or other vegetable oil', ('canola or other vegetable oil', {'from': [(295, 'mL')], 'equiv': [{'from': [(1.25, 'cup')]}]})),
])
def test_parses_ingredient_line_with_equivalent_quantity(ingredient_line, expected_result):
    actual = ingredients.parse_ingredient_line(ingredient_line)
    expected = make_ingredient(expected_result)
    assert_ingredient_equal(expected, actual)


@pytest.mark.parametrize("ingredient_line, expected_result", [
    ('1 cup (~240 mL) canola or other vegetable oil', ('canola or other vegetable oil', {'from': [(1, 'cup')], 'equiv': [{'from': [(-240, 'mL')]}]})),
    ('~1 cup (240 mL) canola or other vegetable oil', ('canola or other vegetable oil', {'from': [(-1, 'cup')], 'equiv': [{'from': [(240, 'mL')]}]})),
    ('~1 cup (~240 mL) canola or other vegetable oil', ('canola or other vegetable oil', {'from': [(-1, 'cup')], 'equiv': [{'from': [(-240, 'mL')]}]})),

    # Other ways of indicating approximately
    ('about 1 cup canola or other vegetable oil', ('canola or other vegetable oil', {'from': [(-1, 'cup')]})),
    ('approx 1 cup canola or other vegetable oil', ('canola or other vegetable oil', {'from': [(-1, 'cup')]})),
    ('approx. 1 cup canola or other vegetable oil', ('canola or other vegetable oil', {'from': [(-1, 'cup')]})),
    ('approximately 1 cup canola or other vegetable oil', ('canola or other vegetable oil', {'from': [(-1, 'cup')]})),
    ('1 cup +/- canola or other vegetable oil', ('canola or other vegetable oil', {'from': [(-1, 'cup')]})),
    ('1 cup (+/-) canola or other vegetable oil', ('canola or other vegetable oil', {'from': [(-1, 'cup')]})),

    # Range
    ('~2~3 tbsp chili powder', ('chili powder', {'from': [(-2, 'tbsp')], 'to': [(3, 'tbsp')]})),
    ('~2~ about 3 tbsp chili powder', ('chili powder', {'from': [(-2, 'tbsp')], 'to': [(-3, 'tbsp')]})),
])
def test_parses_ingredient_line_with_approximate_quantity(ingredient_line, expected_result):
    actual = ingredients.parse_ingredient_line(ingredient_line)
    expected = make_ingredient(expected_result)
    assert_ingredient_equal(expected, actual)


@pytest.mark.parametrize("ingredient_line, expected_result", [
    ('1 cup + 2 tbsp canola or other vegetable oil', ('canola or other vegetable oil', {'from': [(1, 'cup'), (2, 'tbsp')]})),
    ('1 cup + 2 tbsp + 1 tsp canola or other vegetable oil', ('canola or other vegetable oil', {'from': [(1, 'cup'), (2, 'tbsp'), (1, 'tsp')]})),
    ('1 cup + ~2 tbsp + 1 tsp canola or other vegetable oil', ('canola or other vegetable oil', {'from': [(1, 'cup'), (-2, 'tbsp'), (1, 'tsp')]})),

    # Other ways of combining amount values
    ('1 cup plus 2 tbsp canola or other vegetable oil', ('canola or other vegetable oil', {'from': [(1, 'cup'), (2, 'tbsp')]})),
    ('1 cup and 2 tbsp canola or other vegetable oil', ('canola or other vegetable oil', {'from': [(1, 'cup'), (2, 'tbsp')]})),
    ('1 cup, 2 tbsp canola or other vegetable oil', ('canola or other vegetable oil', {'from': [(1, 'cup'), (2, 'tbsp')]})),

    # Equivalent
    ('1 cup + ~2 tbsp + 1 tsp (6 oz) canola or other vegetable oil', ('canola or other vegetable oil', {'from': [(1, 'cup'), (-2, 'tbsp'), (1, 'tsp')], 'equiv': [{'from': [(6, 'oz')]}]})),

    # Range
    ('1 cup + ~2 tbsp + 1 tsp - 1 1/4 cup canola or other vegetable oil', ('canola or other vegetable oil', {'from': [(1, 'cup'), (-2, 'tbsp'), (1, 'tsp')], 'to': [(1.25, 'cup')]})),
    ('1 cup + ~2 tbsp + 1 tsp - 1 cup + 3 tbsp canola or other vegetable oil', ('canola or other vegetable oil', {'from': [(1, 'cup'), (-2, 'tbsp'), (1, 'tsp')], 'to': [(1, 'cup'), (3, 'tbsp')]})),
    ('1 cup + ~2 tbsp + 1 tsp ~ 1 cup + 3 tbsp canola or other vegetable oil', ('canola or other vegetable oil', {'from': [(1, 'cup'), (-2, 'tbsp'), (1, 'tsp')], 'to': [(1, 'cup'), (3, 'tbsp')]})),

    # Range with equivalent
    ('1 cup + ~2 tbsp + 1 tsp - 1 cup + 3 tbsp (14.5 oz) canola or other vegetable oil', ('canola or other vegetable oil', {'from': [(1, 'cup'), (-2, 'tbsp'), (1, 'tsp')], 'to': [(1, 'cup'), (3, 'tbsp')], 'equiv': [{'from': [(14.5, 'oz')]}]})),
])
def test_parses_ingredient_line_where_ingredient_has_multiple_amount_values(ingredient_line, expected_result):
    actual = ingredients.parse_ingredient_line(ingredient_line)
    expected = make_ingredient(expected_result)
    assert_ingredient_equal(expected, actual)


@pytest.mark.parametrize("ingredient_line, expected_result", [
    ('a cup of water', ('water', {'from': [(1, 'cup')]})),
    ('about a cup of water', ('water', {'from': [(-1, 'cup')]})),
    ('a pinch of salt', ('salt', {'from': [(1, 'pinch')]})),
])
def test_parses_ingredient_line_where_quantity_amount_is_words(ingredient_line, expected_result):
    actual = ingredients.parse_ingredient_line(ingredient_line)
    expected = make_ingredient(expected_result)
    assert_ingredient_equal(expected, actual)


@pytest.mark.parametrize("ingredient_line, expected_result", [
    ('1 scant Tbsp. lemon juice', ('lemon juice', {'from': [(1, 'tbsp', 'scant')]})),
    ('2 rounded Tbsp. cornstarch', ('cornstarch', {'from': [(2, 'tbsp', 'rounded')]})),
    ('1 heaping tablespoon of red pepper flakes', ('red pepper flakes', {'from': [(1, 'tbsp', 'heaping')]})),
    ('2 large bags of chocolate chips', ('chocolate chips', {'from': [(2, 'bag', 'large')]})),
    ('2 large eggs', ('eggs', {'from': [(2, None, 'large')]})),
])
def test_parses_ingredient_line_unit_is_modified(ingredient_line, expected_result):
    actual = ingredients.parse_ingredient_line(ingredient_line)
    expected = make_ingredient(expected_result)
    assert_ingredient_equal(expected, actual)


@pytest.mark.parametrize("ingredient_line, expected_result", [
    ('2 16-oz cans of crushed tomatoes', ('crushed tomatoes', {'from': [(2, 'cans', '16-oz')]})),
    ('2 16oz cans of crushed tomatoes', ('crushed tomatoes', {'from': [(2, 'cans', '16oz')]})),
    ('2 16 oz cans of crushed tomatoes', ('crushed tomatoes', {'from': [(2, 'cans', '16 oz')]})),
    ('2 (16-oz) cans of crushed tomatoes', ('crushed tomatoes', {'from': [(2, 'cans', '(16-oz)')]})),
    ('2 (16oz) cans of crushed tomatoes', ('crushed tomatoes', {'from': [(2, 'cans', '(16oz)')]})),
    ('2 (16 oz) cans of crushed tomatoes', ('crushed tomatoes', {'from': [(2, 'cans', '(16 oz)')]})),
    # ('16-oz can of crushed tomatoes', ('crushed tomatoes', {'from': [(16, 'oz')]})),
    # ('a 16-oz can of crushed tomatoes', ('crushed tomatoes', {'from': [(1, 'can', '16-oz')]})),
])
def test_parses_ingredient_line_with_unit_size(ingredient_line, expected_result):
    actual = ingredients.parse_ingredient_line(ingredient_line)
    expected = make_ingredient(expected_result)
    assert_ingredient_equal(expected, actual)


"""
Additional cases:
equivalences:
    2 cups all-purpose flour (250 grams)
    1 1/4 cups canola or other vegetable oil (295 ml)
    3 cups grated peeled carrots (300 grams, 5 to 6 medium carrots)
    1 cup lightly packed brown sugar (200 grams)
notes/comments:
    1 cup lightly packed brown sugar
unit size:
    Scant 1/4 cup white candy coating, such as Wilton Candy Melts
    a scant 1/2 teaspoon crumbled dried sage
    a couple dashes of cayenne pepper
    a few dashes of cayenne pepper
"""
