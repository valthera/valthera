import click
import time
import subprocess
import os
import re
import readchar  # Cross-platform way to capture keyboard input
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table

console = Console()

# Define specific files to highlight in red
HIGHLIGHTED_FILES = {"important.txt", "config.json", "data.csv"}

# Highlight filenames starting with "doc" in blue
DOC_HIGHLIGHT_REGEX = r"^doc"

def list_directory(path):
    """Runs ls -la on a given directory and returns parsed output."""
    result = subprocess.run(f"ls -la '{path}'", shell=True, capture_output=True, text=True)
    output_lines = result.stdout.split("\n")
    entries = []

    for line in output_lines[1:]:  # Skip "total" line
        words = line.split(maxsplit=8)
        if len(words) < 9:
            continue
        
        permissions, links, owner, group, size, month, day, time_or_year, filename = words
        entries.append({
            "permissions": permissions,
            "links": links,
            "owner": owner,
            "group": group,
            "size": size,
            "date": f"{month} {day} {time_or_year}",
            "filename": filename,
            "is_dir": permissions.startswith("d")  # Check if it's a directory
        })

    return entries

def render_table(entries, selected_index):
    """Renders the directory listing as a rich table."""
    table = Table(title=f"📂 Browsing: {os.getcwd()}", show_lines=False)
    table.add_column("Permissions", style="cyan", no_wrap=True)
    table.add_column("Links", style="green", no_wrap=True)
    table.add_column("Owner", style="yellow", no_wrap=True)
    table.add_column("Group", style="yellow", no_wrap=True)
    table.add_column("Size", style="blue", no_wrap=True)
    table.add_column("Date", style="magenta", no_wrap=True)
    table.add_column("Filename", style="white", no_wrap=True)

    for i, entry in enumerate(entries):
        filename = entry["filename"]

        # Apply color highlighting
        if filename in HIGHLIGHTED_FILES:
            filename = f"[bold red]{filename}[/bold red]"
        elif re.match(DOC_HIGHLIGHT_REGEX, filename, re.IGNORECASE):
            filename = f"[bold blue]{filename}[/bold blue]"

        # Highlight selected row with a background color
        if i == selected_index:
            filename = f"[reverse]{filename}[/reverse]"

        table.add_row(
            entry["permissions"], entry["links"], entry["owner"], entry["group"],
            entry["size"], entry["date"], filename
        )

    console.clear()
    console.print(table)

def file_explorer():
    """Interactive file explorer with keyboard navigation."""
    selected_index = 0
    current_path = os.getcwd()

    while True:
        entries = list_directory(current_path)
        render_table(entries, selected_index)

        key = readchar.readkey()

        if key == readchar.key.UP:  # Move up
            selected_index = max(0, selected_index - 1)
        elif key == readchar.key.DOWN:  # Move down
            selected_index = min(len(entries) - 1, selected_index + 1)
        elif key == readchar.key.ENTER:  # Enter a directory
            if entries[selected_index]["is_dir"]:
                current_path = os.path.join(current_path, entries[selected_index]["filename"])
                os.chdir(current_path)
                selected_index = 0  # Reset selection when entering a new folder
        elif key == readchar.key.BACKSPACE or key == "q":  # Go back (Exit or navigate up)
            if current_path != "/":
                os.chdir("..")
                current_path = os.getcwd()
                selected_index = 0  # Reset selection
            else:
                break  # Exit if already in root

@click.command()
def main():
    """A Stylish CLI File Explorer"""
    file_explorer()

if __name__ == '__main__':
    main()
