import time
import logging
from document_editor.utils import get_line_col
from document_editor.chunker import chunk_document, find_chunk_for_edit, reassemble_document

logger = logging.getLogger("document_editor")

def edit_document_directly(document: str, global_start: int, global_end: int, new_text: str) -> str:
    start_time = time.time()
    updated_document = document[:global_start] + new_text + document[global_end:]
    replaced_text = document[global_start:global_end]
    start_line, start_col = get_line_col(document, global_start)
    end_line, end_col = get_line_col(document, global_end)
    logger.info(f"Replaced text: '{replaced_text}' with '{new_text}' (Global positions: {global_start}-{global_end}, Lines: {start_line}-{end_line}, Columns: {start_col}-{end_col})")
    logger.info(f"Direct document edit completed in {time.time() - start_time:.2f} seconds")
    return updated_document

def search_and_replace_direct(document: str, search_str: str, replace_str: str, replace_all: bool = True) -> str:
    """
    Performs a search and replace operation directly on the entire document.
    If replace_all is True, all occurrences of search_str will be replaced;
    otherwise, only the first occurrence will be replaced.
    """
    start_time = time.time()
    occurrences = []
    pos = 0
    # Find all occurrences of the search string.
    while True:
        pos = document.find(search_str, pos)
        if pos == -1:
            break
        occurrences.append((pos, pos + len(search_str)))
        pos += len(search_str)
    
    if not occurrences:
        logger.warning(f"Search string '{search_str}' not found in document")
        return document
    
    if replace_all:
        for i, (start_pos, end_pos) in enumerate(occurrences):
            replaced_text = document[start_pos:end_pos]
            start_line, start_col = get_line_col(document, start_pos)
            end_line, end_col = get_line_col(document, end_pos)
            logger.info(f"Occurrence {i+1}: replacing '{replaced_text}' with '{replace_str}' (Global positions: {start_pos}-{end_pos}, Lines: {start_line}-{end_line}, Columns: {start_col}-{end_col})")
        updated_document = document.replace(search_str, replace_str)
    else:
        start_pos, end_pos = occurrences[0]
        replaced_text = document[start_pos:end_pos]
        start_line, start_col = get_line_col(document, start_pos)
        end_line, end_col = get_line_col(document, end_pos)
        logger.info(f"Occurrence 1: replacing '{replaced_text}' with '{replace_str}' (Global positions: {start_pos}-{end_pos}, Lines: {start_line}-{end_line}, Columns: {start_col}-{end_col})")
        updated_document = document[:start_pos] + replace_str + document[end_pos:]
    
    logger.info(f"Direct search and replace completed in {time.time() - start_time:.2f} seconds")
    return updated_document
