import json

from IPython import get_ipython
from IPython.core.magic import register_cell_magic
from IPython.core.magic_arguments import argument, magic_arguments
from IPython.display import Markdown, display


@magic_arguments()
@argument(
    "-m",
    "--markdown",
    action="store_true",
    help="Print the code to markdown, in addition to running",
)
@argument("-o", "--output", type=str, help="A variable name to save the result as")
@argument(
    "-q", "--quiet", action="store_true", help="Whether to hide the result printout"
)

@register_cell_magic
def capture_parameters(line, cell):
    shell = get_ipython()
    shell.run_cell(cell, silent=True)
    # We assume the last line is a tuple
    tup = [s.strip() for s in cell.strip().split("\n")[-1].split(",")]

    print(
        json.dumps(
            {identifier: shell.user_ns[identifier] for identifier in tup if identifier}
        )
    )
