import traceback

from tqdm import tqdm

from recipe_parser.ingredients import parse_ingredient_line


with open('ingredients.txt') as fp:
    ingredients = list({ingr: None for ingr in fp.read().splitlines()}.keys())


got_none = []
got_something = {}
for ingr in tqdm(ingredients[:100]):
    try:
        res = parse_ingredient_line(ingr)
        if res is None:
                got_none.append(ingr)
        else:
                got_something[ingr] = res
    except Exception as ex:
        print(ingr)
        print(f'\t{type(ex)} {ex}')
        traceback.print_tb(ex.__traceback__)


for k, v in got_something.items():
    print(k)
    print(v)
    print()
