# FormFill

The [Claude Computer Use API](https://docs.anthropic.com/en/docs/build-with-claude/computer-use) doesn't require a full VM to be useful! Anthropic has an easy-to-run VM setup in their [quickstarts repo](https://github.com/anthropics/anthropic-quickstarts/tree/main/computer-use-demo), which I used some code from, but I wanted to explore if you could accomplish tasks with a more limited set of capabilities.

The API is really: input a picture of a computer screen, and get a described "action", including coordinates. So my theory was that I could use the same API and substitute an image of a PDF page as the "screenshot", use the move_mouse, click, and type actions to determine what text to put where, and then manually add the text myself in the background using the Pillow library in Python. And it turns out it works pretty well!

I hope this inspires more projects where the "screen" is a specific interface that the user wants to manipulate--I think there are a lot of interesting things to do in between "the LLM can only call APIs and can't use a UI" and "the LLM has complete control of a full VM with shell access".

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