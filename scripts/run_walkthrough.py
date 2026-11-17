"""Execute the walkthrough into a separate, untracked file.

    make demo

Deliberately does **not** write back over `notebooks/walkthrough.ipynb`. The
first version of this did, and every `make demo` then left 5.6 MB of embedded
base64 sitting in a tracked file as an uncommitted change - which is precisely
the thing the tracked copy is kept clean to avoid, and an easy thing to commit
by accident.

The executed copy lands at `notebooks/walkthrough.run.ipynb`, which is
gitignored. Open that one to present from.
"""

from __future__ import annotations

import sys
import time
import warnings
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "notebooks" / "walkthrough.ipynb"
OUT = ROOT / "notebooks" / "walkthrough.run.ipynb"


def main() -> int:
    import logging

    import nbformat
    from nbclient import NotebookClient

    # The kernel's unencrypted-TCP notice is the first thing a reader would
    # otherwise see. It is about a local loopback socket, and is noise here.
    logging.getLogger("traitlets").setLevel(logging.ERROR)
    warnings.filterwarnings("ignore")

    if not SOURCE.exists():
        print(f"missing {SOURCE.name}; run `make notebook` first")
        return 1

    started = time.time()
    notebook = nbformat.read(str(SOURCE), as_version=4)
    client = NotebookClient(
        notebook, timeout=900, kernel_name="python3",
        resources={"metadata": {"path": str(ROOT)}}, allow_errors=True,
    )
    client.execute()
    nbformat.write(notebook, str(OUT))

    failures = [
        (i, output.get("ename"))
        for i, cell in enumerate(notebook.cells)
        for output in cell.get("outputs", [])
        if output.get("output_type") == "error"
    ]
    images = sum(
        1 for cell in notebook.cells for output in cell.get("outputs", [])
        if "image/png" in output.get("data", {})
    )

    print(f"executed {sum(1 for c in notebook.cells if c.cell_type == 'code')} "
          f"code cells in {time.time() - started:.0f}s, {images} figures")
    print(f"wrote {OUT.relative_to(ROOT)}  "
          f"({OUT.stat().st_size / 1e6:.1f} MB, untracked)")
    print(f"{SOURCE.relative_to(ROOT)} is unchanged and still output-free")

    if failures:
        for index, name in failures:
            print(f"  !! cell {index} raised {name}")
        return 1
    print("no cell raised")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
