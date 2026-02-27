import ast, os
def extract_functions(file_path):
    try:
        with open(file_path, "r") as f:
            tree = ast.parse(f.read())
    except:
        return []
    functions = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            functions.append({
                "name": node.name,
                "args": [arg.arg for arg in node.args.args],
                "lineno": node.lineno
            })
    return functions