import json

from IPython import get_ipython
from IPython.core.magic import register_cell_magic


@register_cell_magic
def capture_parameters(line, cell):
    shell = get_ipython()
    shell.run_cell(cell, silent=True)
    # We assume the last line is a tuple
    tup = [s.strip() for s in cell.strip().split("\n")[-1].split(",")]

    print(json.dumps({identifier: shell.user_ns[identifier] for identifier in tup if identifier}))
