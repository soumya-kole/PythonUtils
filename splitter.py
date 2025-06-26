from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from typing import List, Dict, Any


def normalize_page_data(pages_data: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    """
    Convert page data from the format where page numbers are keys
    to the expected format with 'page' and 'content' keys.

    Args:
        pages_data: List of dicts where each dict has page number as key and content as value

    Returns:
        List of dicts with 'page' and 'content' keys
    """
    normalized_data = []

    for page_dict in pages_data:
        # Each dictionary should have exactly one key-value pair
        for page_num, content in page_dict.items():
            normalized_data.append({
                "page": int(page_num),  # Convert string page number to int
                "content": content
            })

    return normalized_data


def chunk_text_with_page_metadata(
        pages_data: List[Dict[str, Any]],
        chunk_size: int = 1000,
        chunk_overlap: int = 200
) -> List[Document]:
    """
    Chunk text while preserving page metadata.

    Args:
        pages_data: List of dicts with 'page' and 'content' keys
        chunk_size: Maximum size of each chunk
        chunk_overlap: Number of characters to overlap between chunks

    Returns:
        List of Document objects with page metadata
    """
    # Normalize data if needed
    if pages_data and not all('page' in d and 'content' in d for d in pages_data):
        pages_data = normalize_page_data(pages_data)

    # Initialize the text splitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", " ", ""]
    )

    all_chunks = []

    # Process each page
    for page_data in pages_data:
        page_num = page_data["page"]
        content = page_data["content"]

        # Create a Document object for the page
        page_document = Document(
            page_content=content,
            metadata={"page": page_num}
        )

        # Split the page content into chunks
        page_chunks = text_splitter.split_documents([page_document])

        # Add chunk index within the page for better tracking
        for i, chunk in enumerate(page_chunks):
            chunk.metadata.update({
                "page": page_num,
                "chunk_index": i,
                "source_page": page_num  # Alternative key name
            })

        all_chunks.extend(page_chunks)

    return all_chunks


def chunk_all_content_with_page_tracking(
        pages_data: List[Dict[str, Any]],
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        page_separator: str = "\n\n"
) -> List[Document]:
    """
    Best approach: Combine all content for optimal chunking while tracking page metadata.
    This gives RecursiveCharacterTextSplitter full control over split points.
    """
    # Normalize data if needed
    if pages_data and not all('page' in d and 'content' in d for d in pages_data):
        pages_data = normalize_page_data(pages_data)

    # Step 1: Build the complete text and track page boundaries
    full_text = ""
    page_map = []  # Maps character positions to page numbers

    for i, page_data in enumerate(pages_data):
        content = page_data["content"]
        page_num = page_data["page"]

        # Record the start position for this page
        start_pos = len(full_text)

        # Add the content
        full_text += content

        # Record the end position for this page
        end_pos = len(full_text)

        # Map each character position to its page number
        for pos in range(start_pos, end_pos):
            if pos >= len(page_map):
                page_map.extend([None] * (pos - len(page_map) + 1))
            page_map[pos] = page_num

        # Add separator between pages (except last page)
        if i < len(pages_data) - 1:
            full_text += page_separator
            # Map separator characters to None (they don't belong to any page)
            separator_start = len(full_text) - len(page_separator)
            for pos in range(separator_start, len(full_text)):
                if pos >= len(page_map):
                    page_map.extend([None] * (pos - len(page_map) + 1))
                page_map[pos] = None

    # Step 2: Let RecursiveCharacterTextSplitter do its magic
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""]  # Standard hierarchy
    )

    chunks = text_splitter.split_text(full_text)

    # Step 3: Map each chunk back to its source pages
    documents = []
    search_start = 0

    for chunk_idx, chunk_text in enumerate(chunks):
        # Find where this chunk appears in the full text
        chunk_start = full_text.find(chunk_text, search_start)
        if chunk_start == -1:
            # Fallback: search from beginning
            chunk_start = full_text.find(chunk_text)

        chunk_end = chunk_start + len(chunk_text)

        # Determine which pages this chunk spans
        pages_in_chunk = set()
        for pos in range(chunk_start, min(chunk_end, len(page_map))):
            if page_map[pos] is not None:
                pages_in_chunk.add(page_map[pos])

        pages_list = sorted(list(pages_in_chunk))

        # Create comprehensive metadata
        metadata = {
            "chunk_index": chunk_idx,
            "pages": pages_list,
            "primary_page": pages_list[0] if pages_list else None,
            "spans_multiple_pages": len(pages_list) > 1,
            "char_start": chunk_start,
            "char_end": chunk_end,
            "chunk_length": len(chunk_text)
        }

        # Backward compatibility: add single page number if chunk is from one page
        if len(pages_list) == 1:
            metadata["page"] = pages_list[0]

        documents.append(Document(
            page_content=chunk_text,
            metadata=metadata
        ))

        # Update search position for next chunk
        search_start = chunk_start + 1

    return documents


def chunk_all_content_optimized(
        pages_data: List[Dict[str, Any]],
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        preserve_page_breaks: bool = True
) -> List[Document]:
    """
    Memory-optimized version for large documents.
    Uses page boundaries instead of character-level mapping.
    """
    # Normalize data if needed
    if pages_data and not all('page' in d and 'content' in d for d in pages_data):
        pages_data = normalize_page_data(pages_data)

    # Build page boundaries
    page_boundaries = []
    full_text = ""

    for i, page_data in enumerate(pages_data):
        content = page_data["content"]
        page_num = page_data["page"]

        start_pos = len(full_text)
        full_text += content
        end_pos = len(full_text)

        page_boundaries.append({
            "page": page_num,
            "start": start_pos,
            "end": end_pos,
            "content": content
        })

        # Add page separator
        if i < len(pages_data) - 1:
            if preserve_page_breaks:
                full_text += "\n\n"  # Preserve page breaks
            else:
                full_text += " "  # Minimal separation

    # Chunk the full text
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len
    )

    chunks = text_splitter.split_text(full_text)

    # Map chunks to pages efficiently
    documents = []
    search_pos = 0

    for chunk_idx, chunk_text in enumerate(chunks):
        # Find chunk position
        chunk_start = full_text.find(chunk_text, search_pos)
        if chunk_start == -1:
            chunk_start = full_text.find(chunk_text)

        chunk_end = chunk_start + len(chunk_text)

        # Find overlapping pages
        overlapping_pages = []
        for boundary in page_boundaries:
            # Check if chunk overlaps with this page
            if (chunk_start < boundary["end"] and chunk_end > boundary["start"]):
                overlapping_pages.append(boundary["page"])

        # Create metadata
        metadata = {
            "chunk_index": chunk_idx,
            "pages": overlapping_pages,
            "primary_page": overlapping_pages[0] if overlapping_pages else None,
            "spans_multiple_pages": len(overlapping_pages) > 1,
            "char_start": chunk_start,
            "char_end": chunk_end
        }

        if len(overlapping_pages) == 1:
            metadata["page"] = overlapping_pages[0]

        documents.append(Document(
            page_content=chunk_text,
            metadata=metadata
        ))

        search_pos = chunk_start + 1

    return documents


# Example usage
if __name__ == "__main__":
    # Your sample data format
    sample_pages = [
        {
            "1": "This is the content of page 1. It contains important information about machine learning algorithms. The introduction covers basic concepts and terminology that will be used throughout the document. Next page"},
        {
            "2": " continues the discussion with supervised learning methods. We explore decision trees, random forests, and support vector machines. Each algorithm has its own strengths and weaknesses. His name is "},
        {
            "3": "Soumyabrata Kole. The final page concludes with unsupervised learning techniques. Clustering algorithms like K-means and hierarchical clustering are discussed. We also cover dimensionality reduction methods."
        },
        {
            "5": "Make this sample text longer to ensure it spans multiple chunks. This is to test the chunking functionality effectively. The content should be substantial enough to demonstrate how the text is split into manageable pieces while preserving page metadata. It should be very clear how each chunk relates to the original pages. This is important for understanding the context of each chunk in relation to the document as a whole."
        }

    ]

    print("Optimal Chunking with Page Tracking")
    print("=" * 60)

    # Test with different chunk sizes to see the difference
    for chunk_size in [600]:
        print(f"\nChunk Size: {chunk_size}")
        print("-" * 40)

        chunks = chunk_all_content_with_page_tracking(
            sample_pages,
            chunk_size=chunk_size,
            chunk_overlap=20
        )

        for i, chunk in enumerate(chunks):
            pages = chunk.metadata.get('pages', [])
            spans_multiple = chunk.metadata.get('spans_multiple_pages', False)

            print(f"Chunk {i}:")
            # print(f"  Pages: {pages} {'(spans multiple)' if spans_multiple else ''}")
            # print(f"  Content: {chunk.page_content}")
            # print(f"  Length: {len(chunk.page_content)} chars")
            # print()
            print(chunk)
            print(chunk.metadata)


# Utility functions for analysis
def analyze_chunking_results(chunks: List[Document]) -> Dict[str, Any]:
    """Analyze the chunking results for insights."""
    total_chunks = len(chunks)
    single_page_chunks = sum(1 for c in chunks if not c.metadata.get('spans_multiple_pages', False))
    multi_page_chunks = total_chunks - single_page_chunks

    page_distribution = {}
    for chunk in chunks:
        pages = chunk.metadata.get('pages', [])
        for page in pages:
            page_distribution[page] = page_distribution.get(page, 0) + 1

    return {
        "total_chunks": total_chunks,
        "single_page_chunks": single_page_chunks,
        "multi_page_chunks": multi_page_chunks,
        "page_distribution": page_distribution,
        "avg_chunk_length": sum(len(c.page_content) for c in chunks) / total_chunks if chunks else 0
    }


# Additional utility functions
def filter_chunks_by_page(chunks: List[Document], page_number: int) -> List[Document]:
    """Filter chunks that belong to a specific page."""
    return [
        chunk for chunk in chunks
        if chunk.metadata.get("page") == page_number or
           page_number in chunk.metadata.get("pages", [])
    ]


def get_chunk_page_info(chunk: Document) -> Dict[str, Any]:
    """Extract page information from a chunk."""
    metadata = chunk.metadata
    return {
        "single_page": metadata.get("page"),
        "multiple_pages": metadata.get("pages"),
        "primary_page": metadata.get("primary_page"),
        "spans_multiple": metadata.get("spans_multiple_pages", False)
    }