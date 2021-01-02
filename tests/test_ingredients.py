import pytest

from recipe_parser import ingredients


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


def assert_quantities_equal(expected, actual):
    assert isinstance(actual, ingredients.Quantity)

    assert expected.amount == actual.amount
    assert expected.unit == actual.unit
    if expected.amount is not None:
        assert expected.approximate == actual.approximate


def assert_ingredients_equal(expected, actual):
    assert isinstance(actual, ingredients.Ingredient)

    assert_quantities_equal(expected.quantity, actual.quantity)
    assert expected.quantity == actual.quantity
    assert expected.name == actual.name
    assert expected.notes == actual.notes
    assert expected.optional == actual.optional
    assert_quantities_equal(expected.to_quantity, actual.to_quantity)
    assert_quantities_equal(expected.equivalent_quantity, actual.equivalent_quantity)


@pytest.mark.parametrize("ingredient_line, expected_result", [
    # Amount unit name
    ('2 tbsp chili powder', (2, 'tbsp', 'chili powder')),
    ('2tbsp chili powder', (2, 'tbsp', 'chili powder')),
    ('200 grams flour', (200, 'grams', 'flour')),
    ('½ teaspoons chili powder', (0.5, 'teaspoons', 'chili powder')),
    ('½teaspoons chili powder', (0.5, 'teaspoons', 'chili powder')),
    ('1/2 teaspoons chili powder', (0.5, 'teaspoons', 'chili powder')),
    ('1/2teaspoons chili powder', (0.5, 'teaspoons', 'chili powder')),
    ('2 ½ teaspoons chili powder', (2.5, 'teaspoons', 'chili powder')),
    ('2 ½teaspoons chili powder', (2.5, 'teaspoons', 'chili powder')),
    ('2 ½ teaspoons chili powder', (2.5, 'teaspoons', 'chili powder')),
    ('2 ½teaspoons chili powder', (2.5, 'teaspoons', 'chili powder')),
    ('2 1/2 teaspoons chili powder', (2.5, 'teaspoons', 'chili powder')),
    ('2 1/2teaspoons chili powder', (2.5, 'teaspoons', 'chili powder')),
    ('2 1/2 teaspoons chili powder', (2.5, 'teaspoons', 'chili powder')),
    ('2 1/2teaspoons chili powder', (2.5, 'teaspoons', 'chili powder')),
    ('2½ teaspoons chili powder', (2.5, 'teaspoons', 'chili powder')),
    ('2½teaspoons chili powder', (2.5, 'teaspoons', 'chili powder')),
    ('2½ teaspoons of chili powder', (2.5, 'teaspoons', 'chili powder')),
    ('2½ teaspoons Of chili powder', (2.5, 'teaspoons', 'chili powder')),

    # Amount name
    ('2 onions', (2, None, 'onions')),
    ('2 red onions', (2, None, 'red onions')),
    ('½ onions', (0.5, None, 'onions')),
    ('½ red onions', (0.5, None, 'red onions')),
    ('1/2 onions', (0.5, None, 'onions')),
    ('1/2 red onions', (0.5, None, 'red onions')),
    ('2 ½ onions', (2.5, None, 'onions')),
    ('2 ½ onions', (2.5, None, 'onions')),
    ('2 1/2 onions', (2.5, None, 'onions')),
    ('2 1/2 onions', (2.5, None, 'onions')),
    ('2 ½ red onions', (2.5, None, 'red onions')),
    ('2 ½ red onions', (2.5, None, 'red onions')),
    ('2 1/2 red onions', (2.5, None, 'red onions')),
    ('2 1/2 red onions', (2.5, None, 'red onions')),
    ('2½ onions', (2.5, None, 'onions')),

    # Name
    ('salt', (None, None, 'salt')),
    ('black pepper', (None, None, 'black pepper')),
    ('salt and black pepper to taste', (None, None, 'salt and black pepper to taste')),
])
def test_parses_ingredient_line(ingredient_line, expected_result):
    actual = ingredients.Ingredient.parse_line(ingredient_line)
    expected = ingredients.Ingredient(expected_result[2], ingredients.Quantity(expected_result[0], expected_result[1]))
    assert_ingredients_equal(expected, actual)


@pytest.mark.parametrize("ingredient_line, expected_result", [
    ('200 mL milk, room temperature', (200, 'mL', 'milk', 'room temperature')),
    ('200 mL milk (room temperature)', (200, 'mL', 'milk', 'room temperature')),
    ('200 mL whole milk, room temperature', (200, 'mL', 'whole milk', 'room temperature')),
    ('200 mL whole milk (room temperature)', (200, 'mL', 'whole milk', 'room temperature')),
    ('2 onions, diced', (2, None, 'onions', 'diced')),
    ('2 onions (diced)', (2, None, 'onions', 'diced')),
    ('2 blocks tofu, drained, diced, and frozen', (2, 'blocks', 'tofu', 'drained, diced, and frozen')),
    ('2 blocks tofu (drained, diced, and frozen)', (2, 'blocks', 'tofu', 'drained, diced, and frozen')),
])
def test_parses_ingredient_line_with_notes(ingredient_line, expected_result):
    actual = ingredients.Ingredient.parse_line(ingredient_line)
    expected = ingredients.Ingredient(expected_result[2], ingredients.Quantity(expected_result[0], expected_result[1]),
                                      notes=expected_result[3])
    assert_ingredients_equal(expected, actual)


@pytest.mark.parametrize("ingredient_line, expected_result", [
    # Without notes
    ('2 optional dollops of sour cream', (2, 'dollops', 'sour cream', None)),
    ('2 drops red food coloring, optional', (2, 'drops', 'red food coloring', None)),
    ('2 drops red food coloring (optional)', (2, 'drops', 'red food coloring', None)),

    # With notes
    ('200 mL milk, room temperature (optional)', (200, 'mL', 'milk', 'room temperature')),
    ('200 mL milk, room temperature, optional', (200, 'mL', 'milk', 'room temperature')),
    ('200 mL milk, room temperature optional', (200, 'mL', 'milk', 'room temperature')),
    ('200 mL milk (room temperature) (optional)', (200, 'mL', 'milk', 'room temperature')),
    ('200 mL milk (room temperature, optional)', (200, 'mL', 'milk', 'room temperature')),
    ('200 mL milk (room temperature), optional', (200, 'mL', 'milk', 'room temperature')),
])
def test_parses_optional_ingredient_line(ingredient_line, expected_result):
    actual = ingredients.Ingredient.parse_line(ingredient_line)
    expected = ingredients.Ingredient(expected_result[2], ingredients.Quantity(expected_result[0], expected_result[1]),
                                      notes=expected_result[3], optional=True)
    assert_ingredients_equal(expected, actual)


@pytest.mark.parametrize("ingredient_line, expected_result", [
    # number dash number
    ('2-3 tbsp chili powder', (2, 'tbsp', 3, 'tbsp', 'chili powder')),
    ('2-3tbsp chili powder', (2, 'tbsp', 3, 'tbsp', 'chili powder')),
    ('½-¾ teaspoons chili powder', (0.5, 'teaspoons', 0.75, 'teaspoons', 'chili powder')),
    ('1/2-3/4 teaspoons chili powder', (0.5, 'teaspoons', 0.75, 'teaspoons', 'chili powder')),
    ('2-3 tbsp chili powder', (2, 'tbsp', 3, 'tbsp', 'chili powder')),
    ('½-¾ teaspoons chili powder', (0.5, 'teaspoons', 0.75, 'teaspoons', 'chili powder')),
    ('1/2-3/4 teaspoons chili powder', (0.5, 'teaspoons', 0.75, 'teaspoons', 'chili powder')),
    ('2½-2¾ teaspoons chili powder', (2.5, 'teaspoons', 2.75, 'teaspoons', 'chili powder')),
    ('2 ½-2 ¾ teaspoons chili powder', (2.5, 'teaspoons', 2.75, 'teaspoons', 'chili powder')),
    ('2 1/2-2 3/4 teaspoons chili powder', (2.5, 'teaspoons', 2.75, 'teaspoons', 'chili powder')),

    # number dash number with spaces
    ('2 - 3 tbsp chili powder', (2, 'tbsp', 3, 'tbsp', 'chili powder')),
    ('½ - ¾ teaspoons chili powder', (0.5, 'teaspoons', 0.75, 'teaspoons', 'chili powder')),
    ('1/2 - 3/4 teaspoons chili powder', (0.5, 'teaspoons', 0.75, 'teaspoons', 'chili powder')),
    ('2 - 3 tbsp chili powder', (2, 'tbsp', 3, 'tbsp', 'chili powder')),
    ('½ - ¾ teaspoons chili powder', (0.5, 'teaspoons', 0.75, 'teaspoons', 'chili powder')),
    ('1/2 - 3/4 teaspoons chili powder', (0.5, 'teaspoons', 0.75, 'teaspoons', 'chili powder')),
    ('2½ - 2¾ teaspoons chili powder', (2.5, 'teaspoons', 2.75, 'teaspoons', 'chili powder')),
    ('2 ½ - 2 ¾ teaspoons chili powder', (2.5, 'teaspoons', 2.75, 'teaspoons', 'chili powder')),
    ('2 1/2 - 2 3/4 teaspoons chili powder', (2.5, 'teaspoons', 2.75, 'teaspoons', 'chili powder')),

    # number other-dashes number
    ('2~3 tbsp chili powder', (2, 'tbsp', 3, 'tbsp', 'chili powder')),
    ('2\u20123 tbsp chili powder', (2, 'tbsp', 3, 'tbsp', 'chili powder')),
    ('2\u20133 tbsp chili powder', (2, 'tbsp', 3, 'tbsp', 'chili powder')),
    ('2\u20143 tbsp chili powder', (2, 'tbsp', 3, 'tbsp', 'chili powder')),
    ('2\u20153 tbsp chili powder', (2, 'tbsp', 3, 'tbsp', 'chili powder')),
    ('2\u20533 tbsp chili powder', (2, 'tbsp', 3, 'tbsp', 'chili powder')),

    # number unit dash number unit
    ('2 tsp-3 tbsp chili powder', (2, 'tsp', 3, 'tbsp', 'chili powder')),
    ('2tsp-3 tbsp chili powder', (2, 'tsp', 3, 'tbsp', 'chili powder')),
    ('2tsp-3tbsp chili powder', (2, 'tsp', 3, 'tbsp', 'chili powder')),
    ('2 tsp-3tbsp chili powder', (2, 'tsp', 3, 'tbsp', 'chili powder')),
])
def test_parses_amount_range(ingredient_line, expected_result):
    actual = ingredients.Ingredient.parse_line(ingredient_line)
    expected = ingredients.Ingredient(expected_result[4], ingredients.Quantity(expected_result[0], expected_result[1]),
                                      to_quantity=ingredients.Quantity(expected_result[2], expected_result[3]))
    assert_ingredients_equal(expected, actual)


@pytest.mark.parametrize("ingredient_line, expected_result", [
    ('1 cup (240 mL) canola or other vegetable oil', (1, 'cup', 'canola or other vegetable oil', 240, 'mL')),
    ('1 1/4 cup (295 mL) canola or other vegetable oil', (1.25, 'cup', 'canola or other vegetable oil', 295, 'mL')),
    ('1 ¼ cup (295 mL) canola or other vegetable oil', (1.25, 'cup', 'canola or other vegetable oil', 295, 'mL')),
    ('1¼ cup (295 mL) canola or other vegetable oil', (1.25, 'cup', 'canola or other vegetable oil', 295, 'mL')),

    ('240 mL (1 cup) canola or other vegetable oil', (240, 'mL', 'canola or other vegetable oil', 1, 'cup')),
    ('295 mL (1 1/4 cup) canola or other vegetable oil', (295, 'mL', 'canola or other vegetable oil', 1.25, 'cup')),
    ('295 mL (1 ¼ cup) canola or other vegetable oil', (295, 'mL', 'canola or other vegetable oil', 1.25, 'cup')),
    ('295 mL (1¼ cup) canola or other vegetable oil', (295, 'mL', 'canola or other vegetable oil', 1.25, 'cup')),
])
def test_parses_ingredient_line_with_equivalent_quantity(ingredient_line, expected_result):
    actual = ingredients.Ingredient.parse_line(ingredient_line)
    expected = ingredients.Ingredient(expected_result[2], ingredients.Quantity(expected_result[0], expected_result[1]),
                                      equivalent_quantity=ingredients.Quantity(expected_result[3], expected_result[4]))
    assert_ingredients_equal(expected, actual)


@pytest.mark.parametrize("ingredient_line, expected_result", [
    ('1 cup (~240 mL) canola or other vegetable oil', (1, 'cup', None, None, 'canola or other vegetable oil', -240, 'mL')),
    ('~1 cup (240 mL) canola or other vegetable oil', (-1, 'cup', None, None, 'canola or other vegetable oil', 240, 'mL')),
    ('~1 cup (~240 mL) canola or other vegetable oil', (-1, 'cup', None, None, 'canola or other vegetable oil', -240, 'mL')),

    # Other ways of indicating approximately
    ('about 1 cup canola or other vegetable oil', (-1, 'cup', None, None, 'canola or other vegetable oil', None, None)),
    ('approx 1 cup canola or other vegetable oil', (-1, 'cup', None, None, 'canola or other vegetable oil', None, None)),
    ('approx. 1 cup canola or other vegetable oil', (-1, 'cup', None, None, 'canola or other vegetable oil', None, None)),
    ('approximately 1 cup canola or other vegetable oil', (-1, 'cup', None, None, 'canola or other vegetable oil', None, None)),

    # Range
    ('~2~3 tbsp chili powder', (-2, 'tbsp', 3, 'tbsp', 'chili powder', None, None)),
    ('~2~ about 3 tbsp chili powder', (-2, 'tbsp', -3, 'tbsp', 'chili powder', None, None)),
])
def test_parses_ingredient_line_with_approximate_quantity(ingredient_line, expected_result):
    actual = ingredients.Ingredient.parse_line(ingredient_line)
    expected = ingredients.Ingredient(
        expected_result[4],
        ingredients.Quantity(abs(expected_result[0]), expected_result[1], approximate=expected_result[0] < 0),
        to_quantity=ingredients.Quantity(
            abs(expected_result[2]) if expected_result[2] is not None else None,
            expected_result[3],
            approximate=expected_result[2] is None or expected_result[2] < 0
        ),
        equivalent_quantity=ingredients.Quantity(
            abs(expected_result[5]) if expected_result[5] is not None else None,
            expected_result[6],
            approximate=expected_result[5] is None or expected_result[5] < 0
        ),
    )
    assert_ingredients_equal(expected, actual)
