from setuptools import setup, find_packages

setup(
    name="objdump",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "tree_sitter_languages>=1.8.0",
        "pytest>=7.0",
        "tqdm>=4.67.1",
        "genson>=1.0.0",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "objdump=objdump.cli:main",
        ],
    },
)
