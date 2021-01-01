import pytest

from recipe_parser import ingredients


@pytest.mark.parametrize("str_num, expected_num", [
    ('2', 2),
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
    ('2 tbsp chili powder', (2, 'tbsp', 'chili powder', None)),
    ('200 grams flour', (200, 'grams', 'flour', None)),
    ('½ teaspoons chili powder', (0.5, 'teaspoons', 'chili powder', None)),
    ('1/2 teaspoons chili powder', (0.5, 'teaspoons', 'chili powder', None)),
    ('2 ½ teaspoons chili powder', (2.5, 'teaspoons', 'chili powder', None)),
    ('2 ½ teaspoons chili powder', (2.5, 'teaspoons', 'chili powder', None)),
    ('2 1/2 teaspoons chili powder', (2.5, 'teaspoons', 'chili powder', None)),
    ('2 1/2 teaspoons chili powder', (2.5, 'teaspoons', 'chili powder', None)),
    ('2½ teaspoons chili powder', (2.5, 'teaspoons', 'chili powder', None)),

    # Amount name
    ('2 onions', (2, None, 'onions', None)),
    ('2 red onions', (2, None, 'red onions', None)),
    ('½ onions', (0.5, None, 'onions', None)),
    ('½ red onions', (0.5, None, 'red onions', None)),
    ('1/2 onions', (0.5, None, 'onions', None)),
    ('1/2 red onions', (0.5, None, 'red onions', None)),
    ('2 ½ onions', (2.5, None, 'onions', None)),
    ('2 ½ onions', (2.5, None, 'onions', None)),
    ('2 1/2 onions', (2.5, None, 'onions', None)),
    ('2 1/2 onions', (2.5, None, 'onions', None)),
    ('2 ½ red onions', (2.5, None, 'red onions', None)),
    ('2 ½ red onions', (2.5, None, 'red onions', None)),
    ('2 1/2 red onions', (2.5, None, 'red onions', None)),
    ('2 1/2 red onions', (2.5, None, 'red onions', None)),
    ('2½ onions', (2.5, None, 'onions', None)),

    # Name
    ('salt', (None, None, 'salt', None)),
    ('black pepper', (None, None, 'black pepper', None)),
    ('salt and black pepper to taste', (None, None, 'salt and black pepper to taste', None)),

])
def test_parses_ingredient_line(ingredient_line, expected_result):
    actual = ingredients.Ingredient.parse_line(ingredient_line)
    assert isinstance(actual, ingredients.Ingredient)
    assert expected_result == (actual.amount, actual.unit, actual.name, actual.notes)
