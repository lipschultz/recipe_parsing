import unittest

from recipe_parser.ingredients import parse


class TestAmountUnitNameFormat(unittest.TestCase):
    def assertIngredientEqual(self, expected, actual, msg=None):
        expected_amount, expected_unit, expected_name = expected
        actual_amount, actual_unit, actual_name = actual
        self.assertEqual(expected_amount, actual_amount, f'Amount failed in {msg}')
        self.assertEqual(expected_unit, actual_unit, f'Unit failed in {msg}')
        self.assertEqual(expected_name, actual_name, f'Name failed in {msg}')

    def test_it_parses_amount_unit_name(self):
        cases = {
            '2 tbsp chili powder': (2, 'tbsp', 'chili powder'),
            '200 grams flour': (200, 'grams', 'flour'),
        }

        for input, expected in cases.items():
            actual = parse(input)
            self.assertIngredientEqual(expected, actual, input)

    def test_it_can_handle_fractional_amounts(self):
        cases = {
            '½ teaspoons chili powder': (0.5, 'teaspoons', 'chili powder'),
            '1/2 teaspoons chili powder': (0.5, 'teaspoons', 'chili powder'),
        }

        for input, expected in cases.items():
            actual = parse(input)
            self.assertIngredientEqual(expected, actual, input)
    
    def test_it_parses_mixed_fraction_amounts(self):
        cases = {
            '2 ½ teaspoons chili powder': (2.5, 'teaspoons', 'chili powder'),
            '2 1/2 teaspoons chili powder': (2.5, 'teaspoons', 'chili powder'),
            '2½ teaspoons chili powder': (2.5, 'teaspoons', 'chili powder'),
        }

        for input, expected in cases.items():
            actual = parse(input)
            self.assertIngredientEqual(expected, actual, input)

    def test_it_parses_ingredient_without_quantity(self):
        cases = [
            'salt',
            'black pepper',
            'salt and black pepper to taste',
        ]

        for input in cases:
            actual = parse(input)
            self.assertIngredientEqual((None, None, input), actual, input)


class TestAmountNameFormat(unittest.TestCase):
    def assertIngredientEqual(self, expected, actual, msg=None):
        expected_amount, expected_unit, expected_name = expected
        actual_amount, actual_unit, actual_name = actual
        self.assertEqual(expected_amount, actual_amount, f'Amount failed in {msg}')
        self.assertEqual(expected_unit, actual_unit, f'Unit failed in {msg}')
        self.assertEqual(expected_name, actual_name, f'Name failed in {msg}')

    def test_it_can_handle_fractional_amounts(self):
        cases = {
            '½ onions': (0.5, None, 'onions'),
            '½ red onions': (0.5, None, 'red onions'),
        }

        for input, expected in cases.items():
            actual = parse(input)
            self.assertIngredientEqual(expected, actual, input)
    
    def test_it_parses_mixed_fraction_amounts(self):
        cases = {
            '2 ½ onions': (2.5, None, 'onions'),
            '2 1/2 onions': (2.5, None, 'onions'),
            '2 ½ red onions': (2.5, None, 'red onions'),
            '2 1/2 red onions': (2.5, None, 'red onions'),
            '2½ onions': (2.5, None, 'onions'),
        }

        for input, expected in cases.items():
            actual = parse(input)
            self.assertIngredientEqual(expected, actual, input)

