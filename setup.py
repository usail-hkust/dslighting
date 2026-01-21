"""
Setup script for DSLighting package.
"""
from setuptools import setup, find_packages
from pathlib import Path

# Read the contents of README file
this_directory = Path(__file__).parent
readme_file = this_directory / "PIP_DOC" / "README_PIP.md"

# Try to read README, fall back to simple description if not found
try:
    long_description = readme_file.read_text(encoding="utf-8")
except FileNotFoundError:
    long_description = "DSLighting - End-to-End Data Science Agent Framework"

# Version directly specified
__version__ = "2.4.0"

setup(
    name="dslighting",
    version=__version__,
    description="DSLighting 2.3.4 - Bug Fix: Agent initialization with factory pattern",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="DSLighting Team",
    license="AGPL-3.0",
    url="https://github.com/usail-hkust/dslighting",
    project_urls={
        "Homepage": "https://github.com/usail-hkust/dslighting",
        "Documentation": "https://luckyfan-cs.github.io/dslighting-web/api/getting-started.html",
        "Repository": "https://github.com/usail-hkust/dslighting",
        "Bug Tracker": "https://github.com/usail-hkust/dslighting/issues",
    },
    packages=find_packages(include=["dslighting*", "dsat*"]),
    py_modules=["dslighting_cli"],
    python_requires=">=3.10",
    install_requires=[
        "pandas>=1.5.0,<3.0.0",
        "pydantic>=2.10.0,<3.0.0",
        "python-dotenv>=1.0.0",
        "openai>=1.0.0",
        "anthropic>=0.34.0",
        "litellm>=1.80.0",
        "rich>=13.0.0",
        "transformers>=4.30.0",
        "torch>=2.0.0",
        "scikit-learn>=1.0.0,<2.0.0",
        "diskcache",
        "tenacity",
        "appdirs",
        "pyyaml",
        "tqdm",
        "py7zr",
        "nbformat>=5.0.0",
        "nbclient>=0.5.0",
        "ipykernel>=7.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-asyncio>=0.21",
            "pytest-cov>=4.0",
            "black>=23.0",
            "mypy>=1.0",
            "ruff>=0.1.0",
            "build>=0.10.0",
            "twine>=4.0.0",
        ],
    },
    include_package_data=True,
    package_data={
        "dslighting": ["*.yaml", "*.json", "datasets/**/*.csv", "registry/**/*.yaml", "registry/**/*.md"],
        "dsat": ["*.yaml", "*.json", "configs/*.yaml", "workflows/*.yaml"],
    },
    # Include README in source distribution
    include=["README_PIP.md", "README.md", "LICENSE"],
    entry_points={
        "console_scripts": [
            "dslighting=dslighting_cli:main",
            "dslighting-detect=dslighting_cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    keywords="data-science agent automation machine-learning ai",
)
