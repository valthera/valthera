# cli.py

import argparse
import time
from document_editor.editor import edit_document_directly, search_and_replace_direct
from document_editor.utils import get_global_positions_for_line_range

from document_editor.logger_config import setup_logger
logger = setup_logger()

def main():
    parser = argparse.ArgumentParser(description='Document Editor CLI')
    parser.add_argument('--file', type=str, default="large_document.txt", help='Input file path')
    parser.add_argument('--output', type=str, default="updated_document.txt", help='Output file path')
    
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--position', action='store_true', help='Use position-based editing')
    mode.add_argument('--search', action='store_true', help='Use search and replace')
    mode.add_argument('--line-range', action='store_true', help='Use line range based editing')
    
    parser.add_argument('--start', type=int, help='Start position for position-based editing')
    parser.add_argument('--end', type=int, help='End position for position-based editing')
    parser.add_argument('--start-line', type=int, help='Start line for line range editing')
    parser.add_argument('--end-line', type=int, help='End line for line range editing')
    parser.add_argument('--search-str', type=str, help='String to search for')
    parser.add_argument('--replace-first-only', action='store_true', help='Replace only the first occurrence')
    parser.add_argument('--new-text', type=str, help='Replacement text')
    parser.add_argument('--force-chunk', action='store_true', help='Force using chunks even for small documents')
    parser.add_argument('--max-chunk-size', type=int, default=2000, help='Maximum chunk size')
    parser.add_argument('--overlap', type=int, default=200, help='Overlap between chunks')
    
    args = parser.parse_args()
    
    logger.info("=== Document Editor Started ===")
    main_start_time = time.time()
    
    # Load the document, then delegate based on the editing mode
    with open(args.file, "r", encoding="utf-8") as f:
        document = f.read()
    
    if args.position:
        # Call the appropriate editor function for position-based editing
        updated_document = edit_document_directly(document, args.start, args.end, args.new_text)
    elif args.line_range:
        global_start, global_end = get_global_positions_for_line_range(document, args.start_line, args.end_line)
        updated_document = edit_document_directly(document, global_start, global_end, args.new_text)
    elif args.search:
        # Similar branching for search and replace (not shown for brevity)
        updated_document = search_and_replace_direct(document, args.search_str, args.new_text, not args.replace_first_only)
    
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(updated_document)
    
    logger.info("=== Document Editor Finished ===")
    logger.info(f"Total execution time: {time.time() - main_start_time:.2f} seconds")

if __name__ == "__main__":
    main()
