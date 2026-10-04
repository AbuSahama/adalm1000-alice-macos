# ALICE for ADALM1000 on macOS

A step-by-step source installation guide for ALICE Desktop 1.3.14 on an Apple Silicon Mac.

ALICE provides an oscilloscope and waveform generator interface for the Analog Devices ADALM1000 (M1K). Windows has a standalone installer. This guide runs ALICE's Python source on macOS and builds the device interface for Apple Silicon.

## What has been verified?

The source installation and compatibility fixes were used on an arm64 Mac with macOS 27.0.1 and Python 3.12. ALICE's oscilloscope and AWG control windows opened successfully. The installed NumPy version was 2.3.5, with libsmu 1.0.4 and libusb 1.0.29.

**Live measurements from an ADALM1000 have not yet been verified.** The Homebrew-based steps below are a portable adaptation of that installation, rather than a clean-machine installation tested end to end. Intel Macs are outside this guide's tested scope.

## 1. Prepare your Mac

You need an internet connection, sufficient space for the source and build dependencies, and an ADALM1000 with a USB data cable for the final hardware check.

Open Terminal and check your architecture:

```sh
uname -m
```

For this guide it should print `arm64`. Install Apple's command-line tools if needed:

```sh
xcode-select --install
```

If macOS says they are already installed, continue.

Install Homebrew using the instructions at [brew.sh](https://brew.sh). Install **Python 3.12 from [python.org's macOS downloads](https://www.python.org/downloads/macos/)**, including its Tkinter support. This guide deliberately uses Python 3.12; newer Python versions have not been checked with these older bindings.

Verify the Python installation:

```sh
/Library/Frameworks/Python.framework/Versions/3.12/bin/python3 --version
/Library/Frameworks/Python.framework/Versions/3.12/bin/python3 -m tkinter
```

The second command should open a small Tk test window. Close it before continuing.

## 2. Install build dependencies

```sh
brew install libusb boost pkg-config
```

| Component | Purpose |
| --- | --- |
| Python | Runs ALICE |
| Tkinter | Displays windows and controls; supplied with the Python installer |
| NumPy | Numerical calculations and signal data |
| libusb | USB communication |
| libsmu | Controls and reads the ADALM1000 |
| pysmu | Python interface to libsmu |
| Boost | Headers needed to compile libsmu |
| Cython, setuptools, wheel | Build the Python interface |

## 3. Create an installation folder

Use a path without spaces for these build steps. Keep this folder in place after installation because the environment and libraries contain absolute paths.

```sh
mkdir -p "$HOME/Documents/ALICE-M1K"
cd "$HOME/Documents/ALICE-M1K"
/Library/Frameworks/Python.framework/Versions/3.12/bin/python3 -m venv venv
./venv/bin/python -m pip install 'numpy==2.3.5' 'Cython==0.29.37' setuptools wheel
```

Download this guide's `patch_alice.py` and `build_pysmu.py` into that folder. In GitHub, open each file, choose **Raw**, and save the file using its exact filename.

## 4. Download the official sources

The revisions below reproduce the source versions used for this installation.

```sh
git clone --branch Version-1.3 https://github.com/analogdevicesinc/alice.git source
git -C source checkout 27247167ed6459d97eb5cecb864bd1aa168cc459
git clone https://github.com/analogdevicesinc/libsmu.git libsmu
git -C libsmu checkout dbb484f004d9eb5251aa4667f5cf09b3ff5610e2
```

## 5. Build the native library

This builds libsmu directly, avoiding the upstream build configuration's hard-coded Intel architecture. It installs the resulting library in your installation folder.

Run these commands in the same Terminal window, from `ALICE-M1K`:

```sh
mkdir -p runtime/lib runtime/include
ln -s "$(brew --prefix libusb)/include/libusb-1.0" runtime/include/libusb-1.0
ln -s "$(brew --prefix libusb)/lib/libusb-1.0.dylib" runtime/lib/libusb-1.0.dylib
./venv/bin/python - <<'PY'
from pathlib import Path
source = Path('libsmu/dist/version.hpp.in').read_text()
for key, value in {
    'LIBSMU_VERSION_MAJOR': '1',
    'LIBSMU_VERSION_MINOR': '0',
    'LIBSMU_VERSION_PATCH': '4',
    'LIBSMU_VERSION_STR': '1.0.4',
}.items():
    source = source.replace('@' + key + '@', value)
Path('libsmu/include/libsmu/version.hpp').write_text(source)
PY
clang++ -dynamiclib -fPIC -std=c++14 -O2 \
  -Ilibsmu/include \
  -I"$(brew --prefix boost)/include" \
  -Iruntime/include/libusb-1.0 \
  libsmu/src/*.cpp \
  -Lruntime/lib -lusb-1.0 \
  -Wl,-install_name,"$PWD/runtime/lib/libsmu.dylib" \
  -o runtime/lib/libsmu.dylib
```

Compiler warnings may appear. If the command ends with an error, resolve it before proceeding.

## 6. Build and install pysmu

```sh
ARCHFLAGS='-arch arm64' ./venv/bin/python build_pysmu.py bdist_wheel
./venv/bin/python -m pip install --no-deps dist/pysmu-*.whl
```

The `ARCHFLAGS` setting ensures the interface matches the native Apple Silicon libraries.

## 7. Apply the Python compatibility fixes

```sh
./venv/bin/python patch_alice.py source
```

The helper fixes four issues found in this installation:

- `IntVar(0)` and similar calls incorrectly treat the number as a Tk window; they become `IntVar(value=0)`.
- Mac font/menu code references `tkinter` without importing the module.
- An old `numpy.complex` alias becomes the equivalent built-in `complex` type.
- Invalid string escape warnings are corrected while preserving the strings' output.

Original versions are saved beside changed files with the suffix `.original`. The patch can be run again safely.

## 8. Check the installation

```sh
./venv/bin/python - <<'PY'
import numpy
import tkinter
import pysmu
print('NumPy:', numpy.__version__)
print('pysmu:', pysmu.__version__)
session = pysmu.Session()
print('ADALM1000 boards detected:', len(session.devices))
PY
```

With no connected board, `0` is expected. To check hardware detection, close other software using the board, connect it with a USB data cable, and repeat the check. A detected board should produce a count of at least `1`.

## 9. Launch ALICE

```sh
cd source
../venv/bin/python alice-desktop-1.3.pyw
```

You should see an **ALICE DeskTop 1.3.14: ALM1000 Oscilloscope** window and AWG controls. macOS may show **Python** in the menu bar.

A blank plot marked **Stopped** confirms the interface has opened, but does not establish that the hardware is working. Board detection and live acquisition are separate checks. Before pressing **Run** or enabling outputs, connect your experiment according to the official user guide.

## 10. Create a double-click launcher

Return to the installation folder:

```sh
cd "$HOME/Documents/ALICE-M1K"
cat > 'Launch ALICE.command' <<'SH'
#!/bin/zsh
set -e
ALICE_DIR="$(cd -- "$(dirname -- "$0")" && pwd)"
cd "$ALICE_DIR/source"
exec "$ALICE_DIR/venv/bin/python" alice-desktop-1.3.pyw
SH
chmod +x 'Launch ALICE.command'
```

Double-click `Launch ALICE.command` in Finder whenever you want to use ALICE.

## Troubleshooting

**`AttributeError: 'int' object has no attribute '_root'`**: apply `patch_alice.py` to the source directory you are actually launching.

**`NameError: name 'tkinter' is not defined`**: apply the same patch, then restart ALICE.

**`ModuleNotFoundError: No module named 'pysmu'`**: use the virtual environment's Python and repeat step 6. Installing an unrelated package named `pysmu` is not a substitute for building Analog Devices' bindings.

**Missing libsmu or libusb library**: confirm step 5 succeeded and the installation folder has not moved. Homebrew's libusb installation must also remain present.

**Wrong architecture**: check `uname -m` and use `ARCHFLAGS='-arch arm64'` during step 6. Avoid mixing Intel and Apple Silicon libraries.

**No board detected**: try a known USB data cable and another port or adapter. Close other applications using the board and reconnect it. An open ALICE window alone does not prove board detection.

**Tk window does not open**: repeat the Tk test in step 1 using the Python.org Python 3.12 installation. Some Python distributions omit Tkinter.

## Official references

- [ALICE Version-1.3 source](https://github.com/analogdevicesinc/alice/tree/Version-1.3)
- [libsmu source and macOS build instructions](https://github.com/analogdevicesinc/libsmu)
- [ALICE Desktop user's guide](https://wiki.analog.com/university/tools/m1k/alice/desk-top-users-guide)

This is a community installation guide, not an official Analog Devices installer. Upstream software retains its own licenses; this folder contains instructions and helper scripts rather than redistributed ALICE binaries.

## Put this guide on GitHub

Create a repository or open an existing one. Choose **Add file → Upload files**, and upload this folder's `README.md`, `patch_alice.py`, `build_pysmu.py`, and `.gitignore` into an `alice-macos-guide` directory. Commit the files. GitHub displays `README.md` automatically when someone opens the directory.

Do not upload your virtual environment, downloaded dependency sources, configuration files, or compiled installation folder.
