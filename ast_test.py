import ast

lst = '["a", "b", "c"]'
parsed = ast.literal_eval(lst)
print(parsed)  # Output: ['a', 'b', 'c']