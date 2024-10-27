# FormFill

FormFill is a CLI tool that uses LLMs to automatically fill out PDF forms.

## Installation

### Prerequisites

On Mac, pdf2image requires installation of poppler:
```bash
$ brew install poppler
```

### Installing FormFill

```bash
$ pip install -e .
```

### Authentication

You must provide your Anthropic API key via environment variable:
```bash
$ export ANTHROPIC_API_KEY=sk-ant-api-***
```

## Usage

FormFill can take input data either directly as a string or from a CSV file:

```bash
# Using a string input
$ formfill path/to/form.pdf -s "Name: John Smith, Age: 30, Occupation: Engineer"

# Using a file
$ formfill path/to/form.pdf -f data.csv
```

The filled form will be saved as `{original_name}_filled.pdf` in the same directory as the command is run.