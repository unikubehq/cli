import os

from setuptools import find_packages, setup

base_dir = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(base_dir, "VERSION")) as f:
    VERSION = f.read()


with open(os.path.join(base_dir, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

DESCRIPTION = "This is the unikube.io command line interface"


setup(
    name="unikube",
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type="text/markdown",
    version=VERSION,
    py_modules=["unikube"],
    install_requires=[
        "click==8.0.4",
        "click-spinner==0.1.10",
        "colorama~=0.4.4",
        "inquirerpy>=0.3.3,<0.4.0",
        "tabulate~=0.8.9",
        "pydantic>=1.7.3,<1.10.0",
        "pyyaml>=5.4",
        "tinydb>=3.15.2,<4.8.0",
        "requests>=2.25.1,<2.28.0",
        "pyjwt[crypto]>=2.0.1,<2.4.0",
        "gql>=3.0,<3.2",
        "semantic-version>=2.8.4,<2.10.0",
        "kubernetes>=11.0.0,<22.0.0",
        "retrying~=1.3.3",
        "oic==1.3.0",
        "python-slugify>=5.0.2,<6.2.0",
        "click-didyoumean~=0.3.0",
        "requests-toolbelt~=0.9.1",
    ],
    python_requires="~=3.7",
    packages=find_packages(),
    url="https://github.com/unikubehq/cli",
    project_urls={
        "Source": "https://github.com/unikubehq/cli",
        "Documentation": "https://cli.unikube.io",
        "Bug Tracker": "https://github.com/unikubehq/cli/issues",
    },
    author="Michael Schilonka",
    author_email="michael@blueshoe.de",
    include_package_data=True,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "Programming Language :: Python :: 3.8",
    ],
    entry_points={"console_scripts": ["unikube=unikube.commands:cli"]},
)
