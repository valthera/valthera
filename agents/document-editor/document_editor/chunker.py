# chunker.py

import time
import logging

logger = logging.getLogger("document_editor")

def chunk_document(document: str, max_length: int, overlap: int) -> list[dict]:
    """
    Splits the document into chunks of at most `max_length` characters,
    with a specified number of overlapping characters between chunks.
    Each chunk is stored with its global start and end offsets.
    
    Parameters:
        document (str): The full text document.
        max_length (int): Maximum number of characters per chunk.
        overlap (int): Number of overlapping characters between chunks.
    
    Returns:
        list[dict]: A list of chunks, where each chunk is a dictionary
                    containing the keys "text", "start", and "end".
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
        # Move start forward, including overlap for context.
        start = end - overlap
    
    logger.info(f"Document chunking completed in {time.time() - start_time:.2f} seconds. Created {len(chunks)} chunks.")
    return chunks

def find_chunk_for_edit(chunks: list[dict], global_start: int, global_end: int) -> tuple[int, int, int]:
    """
    Locates the chunk that contains the global edit position and computes
    local indices (relative to that chunk).
    
    Assumes that the edit lies within a single chunk.
    
    Parameters:
        chunks (list[dict]): The list of document chunks.
        global_start (int): Global start position of the edit.
        global_end (int): Global end position of the edit.
    
    Returns:
        tuple[int, int, int]: A tuple containing:
                              - The index of the chunk,
                              - The local start index within the chunk,
                              - The local end index within the chunk.
    
    Raises:
        ValueError: If no chunk contains the edit.
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

def reassemble_document(chunks: list[dict]) -> str:
    """
    Reassembles the full document by concatenating chunk texts.
    This handles potential overlaps by using the start/end positions.
    
    Parameters:
        chunks (list[dict]): A list of document chunks.
    
    Returns:
        str: The reassembled full document.
    """
    logger.info("Reassembling document from chunks")
    start_time = time.time()
    
    # Sort chunks by their global start positions to ensure proper order.
    sorted_chunks = sorted(chunks, key=lambda x: x["start"])
    logger.info(f"Sorted {len(chunks)} chunks")
    
    if not sorted_chunks:
        logger.warning("No chunks to reassemble")
        return ""
    
    result = sorted_chunks[0]["text"]
    last_end = sorted_chunks[0]["end"]
    logger.info(f"Initialized with first chunk (length: {len(result)})")
    
    for i, chunk in enumerate(sorted_chunks[1:], 1):
        if chunk["start"] >= last_end:
            logger.debug(f"Chunk {i}: No overlap with previous chunk - appending")
            result += chunk["text"]
        else:
            overlap_size = last_end - chunk["start"]
            logger.debug(f"Chunk {i}: Overlap of {overlap_size} characters - appending non-overlapping part")
            result += chunk["text"][overlap_size:]
        last_end = chunk["end"]
    
    logger.info(f"Document reassembly completed in {time.time() - start_time:.2f} seconds")
    logger.info(f"Final document length: {len(result)} characters")
    return result
