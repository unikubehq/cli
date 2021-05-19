import os

from setuptools import find_packages, setup

base_dir = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(base_dir, "VERSION")) as f:
    VERSION = f.read()

DESCRIPTION = "Unikube CLI"


setup(
    name="unikube",
    description=DESCRIPTION,
    version=VERSION,
    py_modules=["unikube"],
    install_requires=[
        "click==7.1.2",
        "colorama~=0.4.4",
        "inquirer~=2.7.0",
        "tabulate~=0.8.7",
        "pydantic~=1.7.3",
        "pyyaml~=5.3.1",
        "tinydb~=3.15.2",
        "requests~=2.25.1",
        "pyjwt[crypto]~=2.0.1",
        "gql~=0.4.0",
        "semantic-version~=2.8.4",
        "kubernetes>=11.0.0",
        "retrying~=1.3.3",
    ],
    python_requires="~=3.7",
    packages=find_packages(),
    author="Michael Schilonka",
    author_email="michael@blueshoe.de",
    include_package_data=True,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "Programming Language :: Python :: 3.8",
    ],
    entry_points="""
        [console_scripts]
        unikube=unikube:cli
    """,
)
