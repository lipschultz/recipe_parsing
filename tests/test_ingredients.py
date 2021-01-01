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
])
def test_converts_string_to_number(str_num, expected_num):
    assert ingredients.to_number(str_num) == expected_num


@pytest.mark.parametrize("ingredient_line, expected_result", [
    # Amount unit name
    ('2 tbsp chili powder', (2, 'tbsp', 'chili powder')),
    ('200 grams flour', (200, 'grams', 'flour')),
    ('½ teaspoons chili powder', (0.5, 'teaspoons', 'chili powder')),
    ('1/2 teaspoons chili powder', (0.5, 'teaspoons', 'chili powder')),
    ('2 ½ teaspoons chili powder', (2.5, 'teaspoons', 'chili powder')),
    ('2 ½ teaspoons chili powder', (2.5, 'teaspoons', 'chili powder')),
    ('2 1/2 teaspoons chili powder', (2.5, 'teaspoons', 'chili powder')),
    ('2 1/2 teaspoons chili powder', (2.5, 'teaspoons', 'chili powder')),
    ('2½ teaspoons chili powder', (2.5, 'teaspoons', 'chili powder')),

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
    #
    # # Optional
    # ('2 optional dollops of sour cream', (2, 'dollops', 'of sour cream', {'optional': True})),
    # ('2 drops red food coloring, optional', (2, 'drops', 'red food coloring', {'optional': True}))
])
def test_parses_ingredient_line(ingredient_line, expected_result):
    actual = ingredients.Ingredient.parse_line(ingredient_line)
    assert isinstance(actual, ingredients.Ingredient)
    assert expected_result + (None, False) == (actual.amount, actual.unit, actual.name, actual.notes, actual.optional)


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
    assert isinstance(actual, ingredients.Ingredient)
    assert expected_result + (False,) == (actual.amount, actual.unit, actual.name, actual.notes, actual.optional)
