# Install required libraries before running (only needed for semantic search feature):
# pip install llama-index

import os
import time
import logging
import argparse
from llama_index.core import Document
from llama_index.core import VectorStoreIndex

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("document_editor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("document_editor")

# === Added helper function get_line_col ===
def get_line_col(document: str, pos: int) -> tuple[int, int]:
    """
    Returns the line and column number (1-indexed) for a given global position in the document.
    """
    line = document.count("\n", 0, pos) + 1
    last_newline = document.rfind("\n", 0, pos)
    col = pos - (last_newline + 1) if last_newline != -1 else pos
    return line, col
# === End helper function ===

# === Added helper function get_global_positions_for_line_range ===
def get_global_positions_for_line_range(document: str, start_line: int, end_line: int) -> tuple[int, int]:
    """
    Returns the global start and end positions for the given line range (inclusive).
    Lines are 1-indexed. The replacement will remove all text from the start of start_line to the end of end_line.
    """
    lines = document.splitlines(keepends=True)
    if start_line < 1 or end_line > len(lines) or start_line > end_line:
        raise ValueError("Invalid line range specified")
    global_start = sum(len(lines[i]) for i in range(start_line - 1))
    global_end = sum(len(lines[i]) for i in range(end_line))
    return global_start, global_end
# === End helper function ===

def chunk_document(document: str, max_length: int, overlap: int) -> list[dict]:
    """
    Splits the document into chunks of at most `max_length` characters,
    with a specified number of overlapping characters between chunks.
    Each chunk is stored with its global start and end offsets.
    """
    logger.info(f"Chunking document of length {len(document)} with max_length={max_length}, overlap={overlap}")
    start_time = time.time()
    
    chunks = []
    start = 0
    doc_length = len(document)
    while start < doc_length:
        end = min(start + max_length, doc_length)
        chunk_text = document[start:end]
        chunks.append({"text": chunk_text, "start": start, "end": end})
        if end == doc_length:
            break
        # Move start forward while including overlap for context.
        start = end - overlap
    
    logger.info(f"Document chunking completed in {time.time() - start_time:.2f} seconds. Created {len(chunks)} chunks.")
    return chunks

def find_chunk_for_edit(chunks: list[dict], global_start: int, global_end: int) -> tuple[int, int, int]:
    """
    Locates the chunk that contains the global edit position and computes
    local indices (relative to that chunk).
    Assumes that the edit lies within a single chunk.
    """
    logger.info(f"Finding chunk for edit positions {global_start} to {global_end}")
    start_time = time.time()
    
    for i, chunk in enumerate(chunks):
        if chunk["start"] <= global_start < chunk["end"]:
            local_start = global_start - chunk["start"]
            local_end = min(global_end - chunk["start"], len(chunk["text"]))
            logger.info(f"Found edit in chunk {i} at local positions {local_start} to {local_end}. Took {time.time() - start_time:.2f} seconds.")
            return i, local_start, local_end
    
    logger.error(f"Edit position out of range. Took {time.time() - start_time:.2f} seconds.")
    raise ValueError("Edit position out of range")

def edit_chunk_directly(chunk: str, local_start: int, local_end: int, new_text: str) -> str:
    """
    Performs a direct text replacement in the chunk without using an LLM.
    """
    logger.info(f"Starting direct edit for positions {local_start} to {local_end}")
    start_time = time.time()
    
    # Get the text before and after the edit position
    text_before = chunk[:local_start]
    text_after = chunk[local_end:]
    
    # Create the edited chunk by combining the parts
    edited_chunk = text_before + new_text + text_after
    
    logger.info(f"Original text replaced: '{chunk[local_start:local_end]}'")
    logger.info(f"Direct edit completed in {time.time() - start_time:.2f} seconds")
    logger.info(f"Original chunk length: {len(chunk)}, Edited chunk length: {len(edited_chunk)}")
    
    return edited_chunk

def reassemble_document(chunks: list[dict]) -> str:
    """
    Reassembles the full document by concatenating chunk texts.
    This handles potential overlaps by using the start/end positions.
    """
    logger.info("Reassembling document from chunks")
    start_time = time.time()
    
    # Sort chunks by start position to ensure correct order
    sorted_chunks = sorted(chunks, key=lambda x: x["start"])
    logger.info(f"Sorted {len(chunks)} chunks")
    
    # Initialize with the first chunk
    if not sorted_chunks:
        logger.warning("No chunks to reassemble")
        return ""
    
    result = sorted_chunks[0]["text"]
    last_end = sorted_chunks[0]["end"]
    logger.info(f"Initialized with first chunk (length: {len(result)})")
    
    # Add remaining chunks, handling overlaps
    for i, chunk in enumerate(sorted_chunks[1:], 1):
        if chunk["start"] >= last_end:
            # No overlap, just append
            logger.debug(f"Chunk {i}: No overlap with previous chunk - appending")
            result += chunk["text"]
        else:
            # There's an overlap, only add the non-overlapping part
            overlap_size = last_end - chunk["start"]
            logger.debug(f"Chunk {i}: Overlap of {overlap_size} characters - appending non-overlapping part")
            result += chunk["text"][overlap_size:]
        last_end = chunk["end"]
    
    logger.info(f"Document reassembly completed in {time.time() - start_time:.2f} seconds")
    logger.info(f"Final document length: {len(result)} characters")
    return result

def edit_document_directly(document: str, global_start: int, global_end: int, new_text: str) -> str:
    """
    Performs a direct edit on the document without chunking.
    This is much faster for simple edits.
    """
    logger.info(f"Performing direct document edit at positions {global_start}:{global_end}")
    start_time = time.time()
    
    # Simple string replacement
    updated_document = document[:global_start] + new_text + document[global_end:]
    
    # Updated logging to include diff details
    replaced_text = document[global_start:global_end]
    start_line, start_col = get_line_col(document, global_start)
    end_line, end_col = get_line_col(document, global_end)
    logger.info(f"Replaced text: '{replaced_text}' with '{new_text}' (Global positions: {global_start}-{global_end}, "
                f"Lines: {start_line}-{end_line}, Columns: {start_col}-{end_col})")
    
    logger.info(f"Direct document edit completed in {time.time() - start_time:.2f} seconds")
    return updated_document

def find_all_occurrences(text: str, search_str: str) -> list[tuple[int, int]]:
    """
    Find all occurrences of search_str in text and return their start and end positions.
    """
    logger.info(f"Searching for all occurrences of '{search_str}'")
    start_time = time.time()
    
    occurrences = []
    start = 0
    while True:
        start = text.find(search_str, start)
        if start == -1:
            break
        end = start + len(search_str)
        occurrences.append((start, end))
        start = end  # Move past this occurrence
    
    logger.info(f"Found {len(occurrences)} occurrences in {time.time() - start_time:.2f} seconds")
    return occurrences

def search_and_replace_direct(document: str, search_str: str, replace_str: str, replace_all: bool = True) -> str:
    """
    Performs search and replace directly on the document.
    """
    logger.info(f"Performing search and replace: '{search_str}' -> '{replace_str}'")
    start_time = time.time()
    
    occurrences = find_all_occurrences(document, search_str)
    if not occurrences:
        logger.warning(f"Search string '{search_str}' not found in document")
        return document

    if replace_all:
        for i, (start_pos, end_pos) in enumerate(occurrences):
            replaced_text = document[start_pos:end_pos]
            start_line, start_col = get_line_col(document, start_pos)
            end_line, end_col = get_line_col(document, end_pos)
            logger.info(f"Occurrence {i+1}: replacing '{replaced_text}' with '{replace_str}' "
                        f"(Global positions: {start_pos}-{end_pos}, Lines: {start_line}-{end_line}, Columns: {start_col}-{end_col})")
        updated_document = document.replace(search_str, replace_str)
        logger.info(f"Replaced {len(occurrences)} occurrences in {time.time() - start_time:.2f} seconds")
    else:
        start_pos, end_pos = occurrences[0]
        replaced_text = document[start_pos:end_pos]
        start_line, start_col = get_line_col(document, start_pos)
        end_line, end_col = get_line_col(document, end_pos)
        logger.info(f"Occurrence 1: replacing '{replaced_text}' with '{replace_str}' "
                    f"(Global positions: {start_pos}-{end_pos}, Lines: {start_line}-{end_line}, Columns: {start_col}-{end_col})")
        updated_document = document[:start_pos] + replace_str + document[end_pos:]
        logger.info(f"Replaced 1 occurrence in {time.time() - start_time:.2f} seconds")
    
    return updated_document

def search_and_replace_chunked(document: str, search_str: str, replace_str: str, max_length: int, overlap: int, replace_all: bool = True) -> str:
    """
    Performs search and replace on chunked document to handle very large files.
    """
    logger.info(f"Performing chunked search and replace: '{search_str}' -> '{replace_str}'")
    start_time = time.time()
    
    # First, chunk the document
    chunks = chunk_document(document, max_length, overlap)
    
    # Find all occurrences (or just the first if replace_all is False)
    occurrences = find_all_occurrences(document, search_str)
    if not occurrences:
        logger.warning(f"Search string '{search_str}' not found in document")
        return document
    
    if not replace_all:
        occurrences = occurrences[:1]  # Keep only the first occurrence
    
    logger.info(f"Processing {len(occurrences)} occurrences")
    
    # For each occurrence, find the containing chunk and apply the edit
    for i, (start_pos, end_pos) in enumerate(occurrences):
        try:
            replaced_text = document[start_pos:end_pos]
            start_line, start_col = get_line_col(document, start_pos)
            end_line, end_col = get_line_col(document, end_pos)
            logger.info(f"Occurrence {i+1}: replacing '{replaced_text}' with '{replace_str}' "
                        f"(Global positions: {start_pos}-{end_pos}, Lines: {start_line}-{end_line}, Columns: {start_col}-{end_col})")
            chunk_index, local_start, local_end = find_chunk_for_edit(chunks, start_pos, end_pos)
            logger.info(f"Occurrence {i+1}/{len(occurrences)} found in chunk {chunk_index}")
            
            # Edit the chunk
            original_chunk = chunks[chunk_index]["text"]
            edited_chunk = edit_chunk_directly(original_chunk, local_start, local_end, replace_str)
            chunks[chunk_index]["text"] = edited_chunk
        except ValueError as e:
            logger.error(f"Error processing occurrence {i+1}: {e}")
    
    # Reassemble the document
    updated_document = reassemble_document(chunks)
    logger.info(f"Chunked search and replace completed in {time.time() - start_time:.2f} seconds")
    
    return updated_document

def main():
    # Set up command line arguments
    parser = argparse.ArgumentParser(description='Document Editor with Position-based, Line Range, and Search-Replace editing')
    parser.add_argument('--file', type=str, default="large_document.txt", help='Input file path')
    parser.add_argument('--output', type=str, default="updated_document.txt", help='Output file path')
    
    # Edit mode options (mutually exclusive)
    edit_group = parser.add_mutually_exclusive_group(required=True)
    edit_group.add_argument('--position', action='store_true', help='Use position-based editing')
    edit_group.add_argument('--search', action='store_true', help='Use search and replace')
    edit_group.add_argument('--line-range', action='store_true', help='Use line range based editing')
    
    # Position-based editing arguments
    parser.add_argument('--start', type=int, help='Start position for position-based editing')
    parser.add_argument('--end', type=int, help='End position for position-based editing')
    
    # Line range editing arguments
    parser.add_argument('--start-line', type=int, help='Start line for line range editing')
    parser.add_argument('--end-line', type=int, help='End line for line range editing')
    
    # Search and replace arguments
    parser.add_argument('--search-str', type=str, help='String to search for')
    parser.add_argument('--replace-first-only', action='store_true', help='Replace only the first occurrence')
    
    # New text argument (used by all modes)
    parser.add_argument('--new-text', type=str, help='Replacement text')
    
    # Chunking options
    parser.add_argument('--force-chunk', action='store_true', help='Force using chunks even for small documents')
    parser.add_argument('--max-chunk-size', type=int, default=2000, help='Maximum chunk size')
    parser.add_argument('--overlap', type=int, default=200, help='Overlap between chunks')
    
    args = parser.parse_args()
    
    logger.info("=== Document Editor Started ===")
    main_start_time = time.time()
    
    # 1. Load the document
    logger.info(f"Attempting to load document from {args.file}")
    file_start_time = time.time()
    try:
        with open(args.file, "r", encoding="utf-8") as f:
            document = f.read()
        logger.info(f"Document loaded in {time.time() - file_start_time:.2f} seconds")
        logger.info(f"Document length: {len(document)} characters")
    except FileNotFoundError:
        logger.error(f"{args.file} not found. Please create this file first.")
        return
    except UnicodeDecodeError:
        logger.error(f"Unable to decode {args.file} with UTF-8 encoding. Check file encoding.")
        return
    
    # Check which editing mode to use
    if args.position:
        # Position-based editing
        if args.start is None or args.end is None or args.new_text is None:
            logger.error("Position-based editing requires --start, --end, and --new-text arguments")
            return
        
        logger.info(f"Position-based edit: Replace text from positions {args.start} to {args.end} with '{args.new_text}'")
        
        # Decide whether to use chunking
        if len(document) < 1000000 and not args.force_chunk:
            logger.info("Using direct editing (no chunking)")
            try:
                updated_document = edit_document_directly(document, args.start, args.end, args.new_text)
            except Exception as e:
                logger.error(f"Error during direct editing: {e}")
                return
        else:
            logger.info("Using chunked editing approach")
            try:
                chunks = chunk_document(document, args.max_chunk_size, args.overlap)
                chunk_index, local_start, local_end = find_chunk_for_edit(chunks, args.start, args.end)
                replaced_text = document[args.start:args.end]
                start_line, start_col = get_line_col(document, args.start)
                end_line, end_col = get_line_col(document, args.end)
                logger.info(f"Replacing text: '{replaced_text}' with '{args.new_text}' (Global positions: {args.start}-{args.end}, Lines: {start_line}-{end_line}, Columns: {start_col}-{end_col})")
                original_chunk = chunks[chunk_index]["text"]
                edited_chunk = edit_chunk_directly(original_chunk, local_start, local_end, args.new_text)
                chunks[chunk_index]["text"] = edited_chunk
                updated_document = reassemble_document(chunks)
            except ValueError as e:
                logger.error(f"Error during chunked editing: {e}")
                return
    elif args.line_range:
        # Line range editing
        if args.start_line is None or args.end_line is None or args.new_text is None:
            logger.error("Line-range editing requires --start-line, --end-line, and --new-text arguments")
            return
        
        logger.info(f"Line-range edit: Replace lines {args.start_line} to {args.end_line} with '{args.new_text}'")
        try:
            global_start, global_end = get_global_positions_for_line_range(document, args.start_line, args.end_line)
        except ValueError as e:
            logger.error(f"Error computing global positions for line range: {e}")
            return
        try:
            # For line-range editing, we use direct editing.
            updated_document = edit_document_directly(document, global_start, global_end, args.new_text)
        except Exception as e:
            logger.error(f"Error during line-range editing: {e}")
            return
    else:
        # Search and replace mode
        if args.search_str is None or args.new_text is None:
            logger.error("Search and replace requires --search-str and --new-text arguments")
            return
        
        replace_all = not args.replace_first_only
        logger.info(f"Search and replace: '{args.search_str}' -> '{args.new_text}' (replace all: {replace_all})")
        
        # Decide whether to use chunking
        if len(document) < 1000000 and not args.force_chunk:
            logger.info("Using direct search and replace (no chunking)")
            try:
                updated_document = search_and_replace_direct(document, args.search_str, args.new_text, replace_all)
            except Exception as e:
                logger.error(f"Error during direct search and replace: {e}")
                return
        else:
            logger.info("Using chunked search and replace approach")
            try:
                updated_document = search_and_replace_chunked(
                    document, args.search_str, args.new_text, 
                    args.max_chunk_size, args.overlap, replace_all
                )
            except Exception as e:
                logger.error(f"Error during chunked search and replace: {e}")
                return
    
    # Write the updated document to file
    write_start_time = time.time()
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(updated_document)
    logger.info(f"Updated document written to {args.output} in {time.time() - write_start_time:.2f} seconds")
    logger.info("Document updated successfully.")
    logger.info(f"Total execution time: {time.time() - main_start_time:.2f} seconds")
    logger.info("=== Document Editor Finished ===")

# For backward compatibility, allow script to be run without args
def run_with_defaults():
    """
    Run with default parameters for backward compatibility
    """
    logger.info("=== Document Editor Started (Default Mode) ===")
    main_start_time = time.time()
    
    # 1. Load your large document (ensure it's UTF-8 encoded).
    logger.info("Attempting to load document")
    file_start_time = time.time()
    try:
        with open("large_document.txt", "r", encoding="utf-8") as f:
            document = f.read()
        logger.info(f"Document loaded in {time.time() - file_start_time:.2f} seconds")
        logger.info(f"Document length: {len(document)} characters")
    except FileNotFoundError:
        logger.error("large_document.txt not found. Please create this file first.")
        return
    except UnicodeDecodeError:
        logger.error("Unable to decode the file with UTF-8 encoding. Check file encoding.")
        return
    
    # Example usage: Uncomment one of the following editing examples
    
    # Example of position-based edit:
    # args: --position --start 10 --end 20 --new-text "replacement text"
    
    # Example of search and replace:
    # args: --search --search-str "document editing" --new-text "advanced manipulation"
    
    # Example of line-range edit:
    # args: --line-range --start-line 5 --end-line 7 --new-text "New content for these lines"
    
    # For this default run, we'll do a direct search and replace:
    search_string = "document editing"
    replace_string = "advanced text manipulation"
    
    logger.info(f"Search and replace parameters: Search='{search_string}', Replace='{replace_string}'")
    
    if len(document) < 1000000:  # Less than 1MB
        logger.info("Document is small enough for direct editing without chunking")
        try:
            updated_document = search_and_replace_direct(document, search_string, replace_string, True)
            write_start_time = time.time()
            with open("updated_document.txt", "w", encoding="utf-8") as f:
                f.write(updated_document)
            logger.info(f"Updated document written to file in {time.time() - write_start_time:.2f} seconds")
            logger.info("Document updated successfully.")
        except Exception as e:
            logger.error(f"Error during direct editing: {e}")
    else:
        logger.info("Using chunking approach for large document")
        max_length = 2000
        overlap = 200
        chunks = chunk_document(document, max_length, overlap)
        try:
            updated_document = search_and_replace_chunked(document, search_string, replace_string, max_length, overlap, True)
            write_start_time = time.time()
            with open("updated_document.txt", "w", encoding="utf-8") as f:
                f.write(updated_document)
            logger.info(f"Updated document written to file in {time.time() - write_start_time:.2f} seconds")
            logger.info("Document updated successfully.")
        except ValueError as e:
            logger.error(f"Error processing edit: {e}")
            return
    
    logger.info(f"Total execution time: {time.time() - main_start_time:.2f} seconds")
    logger.info("=== Document Editor Finished ===")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        main()  # Run with command line arguments
    else:
        run_with_defaults()  # Run with default parameters

"""
# Basic search and replace (all occurrences)
python -m document_editor.main --search --search-str "document editing" --new-text "advanced manipulation"

# Replace only the first occurrence
python -m document_editor.main --search --search-str "example" --new-text "sample" --replace-first-only

# Position-based editing
python -m document_editor.main --position --start 10 --end 20 --new-text "replacement text"

# Line-range based editing
python -m document_editor.main --line-range --start-line 5 --end-line 7 --new-text "New content for these lines"

# Specify input and output files
python -m document_editor.main --search --search-str "find me" --new-text "replace me" --file input.txt --output result.txt

# Force chunking even for small documents
python -m document_editor.main --search --search-str "test" --new-text "example" --force-chunk
"""
