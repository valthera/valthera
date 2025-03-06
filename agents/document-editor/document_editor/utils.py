# utils.py

def get_line_col(document: str, pos: int) -> tuple[int, int]:
    line = document.count("\n", 0, pos) + 1
    last_newline = document.rfind("\n", 0, pos)
    col = pos - (last_newline + 1) if last_newline != -1 else pos
    return line, col

def get_global_positions_for_line_range(document: str, start_line: int, end_line: int) -> tuple[int, int]:
    lines = document.splitlines(keepends=True)
    if start_line < 1 or end_line > len(lines) or start_line > end_line:
        raise ValueError("Invalid line range specified")
    global_start = sum(len(lines[i]) for i in range(start_line - 1))
    global_end = sum(len(lines[i]) for i in range(end_line))
    return global_start, global_end
