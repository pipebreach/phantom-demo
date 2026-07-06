# distributed build of mylib.core (comments and spacing differ from source
# on purpose: phantom's AST normalization must treat this as identical)
def greet(name):
    return "hello, " + name  # build the greeting

def add(a, b):
    return a + b
