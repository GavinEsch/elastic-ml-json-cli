from setuptools import setup, find_packages

setup(
    name="ml-json-cli",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "click",
        "rich",
        "deepdiff",
        "ijson",
        "colorama",
    ],
    entry_points={
        "console_scripts": [
            "mlcli = ml_json_cli.cli:cli",
        ],
    },
)
