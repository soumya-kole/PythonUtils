from contextvars import ContextVar, copy_context
var = ContextVar("var", default="Hello!")
print(var.get())  # Output: Hello!
var.set("Hello, World!")
print(var.get())  # Output: Hello, World!
ctx = copy_context()
var.set("Hello, Pythonista!")
print(var.get())  # Output: Hello, Pythonista!
print(ctx.get(var))  # Output: Hello, World!
def show_var():
    print(f"Inside function: {var.get()}")

ctx.run(show_var)  # Output: Inside function: Hello, World!
print("Back in original context:", var.get())