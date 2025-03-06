# Document Editor

**Document Editor** is a CLI-based text editing tool designed for efficient document manipulation. It supports:

- **Position-based editing:** Replace text based on global character positions.
- **Search and replace:** Replace all or the first occurrence of a target string.
- **Line-range editing:** Replace content in a specified range of lines.
- **Chunking support:** Handle very large documents by processing them in chunks.
- **Detailed logging:** Track changes with global positions, line/column details, and more.

The package is built with Python and managed using [Poetry](https://python-poetry.org/).

## Installation

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/yourusername/document_editor.git
   cd document_editor
   ```

2. **Install Dependencies with Poetry:**

   ```bash
   poetry install
   ```

3. **Activate the Virtual Environment (Optional):**

   ```bash
   poetry shell
   ```

## Usage

The CLI entry point is provided via the `document_editor.cli` module. You can run the CLI commands using the `python -m document_editor.cli` command.

### Editing Modes

#### 1. Position-Based Editing

Replace text between two global character positions.

```bash
python -m document_editor.cli --position --start 10 --end 20 --new-text "replacement text"
```

*This command replaces text between character positions 10 and 20 with "replacement text".*

#### 2. Search and Replace

**a. Replace all occurrences:**

```bash
python -m document_editor.cli --search --search-str "old phrase" --new-text "new phrase"
```

*Replaces every occurrence of "old phrase" with "new phrase".*

**b. Replace only the first occurrence:**

```bash
python -m document_editor.cli --search --search-str "target" --new-text "replacement" --replace-first-only
```

*Replaces only the first occurrence of "target" with "replacement".*

#### 3. Line-Range Editing

Replace the contents of a range of lines (1-indexed).

```bash
python -m document_editor.cli --line-range --start-line 5 --end-line 7 --new-text "New content for these lines"
```

*This command replaces lines 5 to 7 with the provided new text.*

#### 4. Specifying Input and Output Files

You can customize file paths using the `--file` and `--output` options:

```bash
python -m document_editor.cli --search --search-str "find me" --new-text "replace me" --file input.txt --output result.txt
```

*Reads from `input.txt` and writes the updated document to `result.txt`.*

#### 5. Forcing Chunking

Force the chunked processing mode even for small documents:

```bash
python -m document_editor.cli --search --search-str "test" --new-text "example" --force-chunk
```

*This is useful for testing the chunked editing logic.*

## Logging

The package uses a dedicated logger configuration provided in `document_editor/logger_config.py`. Log messages are output to both the console and a file (`document_editor.log`). To adjust the logging level or format, update the configuration in that module.

## Package Structure

- **document_editor/**
  - **__init__.py** – Package initialization.
  - **cli.py** – CLI and argument parsing logic.
  - **editor.py** – High-level editing functions (position-based, search & replace, line-range).
  - **chunker.py** – Functions for chunking documents and reassembling them.
  - **utils.py** – Utility functions (e.g., line/column calculations).
  - **logger_config.py** – Logger configuration.
- **tests/** – Unit tests for the package.
