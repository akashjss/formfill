from setuptools import setup, find_packages

setup(
    name="formfill",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "anthropic",
        "pdf2image",
        "Pillow",
    ],
    entry_points={
        "console_scripts": [
            "formfill=formfill.cli:run_cli",
        ],
    },
    python_requires=">=3.8",
    author="William Horton",
    description="A CLI tool for automatically filling PDF forms using Claude",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    license="MIT",
    keywords="pdf form fill automation claude anthropic",
    url="",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
)