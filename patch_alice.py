"""Apply Python 3 compatibility fixes without changing instrument settings."""
from pathlib import Path
import re
import sys

folder = Path(sys.argv[1])
if not (folder / 'alice-desktop-1.3.pyw').is_file():
    raise SystemExit('Pass the ALICE source directory as the argument.')
for path in folder.glob('*.pyw'):
    original = path.read_bytes()
    fixed = re.sub(rb'\b(IntVar|DoubleVar|StringVar|BooleanVar)\(\s*([-+]?\d+(?:\.\d+)?)\s*\)', rb'\1(value=\2)', original)
    fixed = fixed.replace(b"'<\\>\\n'", b"'<\\\\>\\n'")
    if b'tkinter.' in fixed and b'    import tkinter\n' not in fixed:
        fixed = fixed.replace(b'    from tkinter.font import *', b'    import tkinter\n    import tkinter.font\n    from tkinter.font import *')
    fixed = re.sub(rb'\bnumpy\.complex\b', b'complex', fixed)
    if fixed != original:
        backup = path.with_suffix(path.suffix + '.original')
        if not backup.exists():
            backup.write_bytes(original)
        path.write_bytes(fixed)
        print('Patched', path.name)
