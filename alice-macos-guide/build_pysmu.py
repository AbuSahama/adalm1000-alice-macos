"""Run from the installation folder with its virtual environment's Python."""
from pathlib import Path
from setuptools import setup, Extension
from Cython.Build import cythonize

root = Path.cwd()
source = root / 'libsmu/bindings/python'
runtime = root / 'runtime'
setup(
    name='pysmu', version='1.0.4',
    packages=['pysmu'], package_dir={'': str(source)},
    ext_modules=cythonize([Extension(
        'pysmu.libsmu', [str(source / 'pysmu/libsmu.pyx')],
        include_dirs=[str(root / 'libsmu/include'), str(runtime / 'include/libusb-1.0')],
        library_dirs=[str(runtime / 'lib')], libraries=['smu', 'usb-1.0'],
        language='c++', extra_compile_args=['-std=c++14'],
    )], compiler_directives={'language_level': 3}),
)
