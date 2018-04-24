# -*- coding: utf-8 -*-


"""setup.py: setuptools control."""


import re
from setuptools import setup


version = re.search(
    '^__version__\s*=\s*"(.*)"',
    open('fspdf/fspdf.py').read(),
    re.M
    ).group(1)


with open("README.md", "r") as f:
    readme = f.read()
    rx = re.compile('^## Description\n([^#]+)', re.MULTILINE)
    long_descr = rx.search(readme).group(1).strip()


setup(
    name="fspdf",
    packages=["fspdf"],
    entry_points={
        "console_scripts": ['fspdf = fspdf.fspdf:main']
        },
    version=version,
    install_requires=['Pillow'],
    description="Fill and sign any PDF.",
    long_description=long_descr,
    licsens="MIT",
    keywords="PDF forms fill sign annotate",
    author="Kai Eckert",
    author_email="hallo@kaiec.de",
    url="https://github.com/kaiec/fspdf/",
    )
