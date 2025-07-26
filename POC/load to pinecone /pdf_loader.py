#!/usr/bin/env python3
"""
PDF Processor - Convert PDFs to Markdown and load into Pinecone
"""
import os
import json
import time
import tiktoken
import argparse
import datetime
import base64
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
from pathlib import Path
from chunking_evaluation.chunking import ClusterSemanticChunker
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.document_loaders import PyPDFLoader
from pinecone import Pinecone
import logging
import frontmatter
import re
import glob
import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

import config

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("pdf_processor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def convert_pdf_to_markdown(pdf_path: str, output_dir: str) -> str:
    """
    Convert a PDF file to Markdown format using Mistral OCR and save it
    
    Args:
        pdf_path: Path to the PDF file
        output_dir: Directory to save the markdown file
        
    Returns:
        Path to the created markdown file
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Get file name without extension
    file_name = os.path.basename(pdf_path)
    base_name = os.path.splitext(file_name)[0]
    output_path = os.path.join(output_dir, f"{base_name}.md")
    images_dir = os.path.join(output_dir, f"{base_name}_images")
    os.makedirs(images_dir, exist_ok=True)
    
    logger.info(f"Converting {pdf_path} to markdown using Mistral OCR")
    
    try:
        # Check file size before processing
        file_size_mb = os.path.getsize(pdf_path) / (1024 * 1024)
        logger.info(f"File size: {file_size_mb:.2f} MB (Max allowed: {config.MAX_FILE_SIZE_MB} MB)")
        
        if file_size_mb > config.MAX_FILE_SIZE_MB:
            logger.warning(f"File size ({file_size_mb:.2f} MB) exceeds maximum allowed size ({config.MAX_FILE_SIZE_MB} MB)")
            logger.info("Splitting PDF into smaller chunks...")
            # TODO: Implement PDF splitting logic if needed
            # For now, proceed with the fallback method
            raise ValueError(f"File size ({file_size_mb:.2f} MB) exceeds maximum allowed size")
        
        # Try Mistral OCR first
        mistral_api_key = os.getenv("MISTRAL_API_KEY") or config.MISTRAL_API_KEY
        
        if mistral_api_key:
            try:
                from mistralai import Mistral, DocumentURLChunk
                
                # Initialize Mistral client
                client = Mistral(api_key=mistral_api_key)
                
                # Step 1: Upload file to Mistral
                logger.info(f"Uploading file to Mistral API: {file_name}")
                try:
                    with open(pdf_path, "rb") as f:
                        pdf_bytes = f.read()
                    
                    uploaded_file = client.files.upload(
                        file={
                            "file_name": file_name,
                            "content": pdf_bytes,
                        },
                        purpose="ocr"
                    )
                    logger.info(f"File uploaded successfully with ID: {uploaded_file.id}")
                except Exception as upload_error:
                    logger.error(f"Error uploading file to Mistral: {str(upload_error)}")
                    raise upload_error
                
                # Step 2: Get signed URL
                try:
                    signed_url = client.files.get_signed_url(file_id=uploaded_file.id, expiry=1)
                    logger.info(f"Obtained signed URL for file")
                except Exception as url_error:
                    logger.error(f"Error getting signed URL: {str(url_error)}")
                    raise url_error
                
                # Step 3: Process with OCR
                logger.info(f"Processing file with Mistral OCR API using model: {config.MISTRAL_OCR_MODEL}")
                try:
                    ocr_response = client.ocr.process(
                        document=DocumentURLChunk(document_url=signed_url.url),
                        model=config.MISTRAL_OCR_MODEL,
                        include_image_base64=True
                    )
                    logger.info(f"OCR processing complete with {len(ocr_response.pages)} pages")
                except Exception as ocr_error:
                    logger.error(f"Error during OCR processing: {str(ocr_error)}")
                    raise ocr_error
                
                # Step 4: Process OCR response to markdown
                logger.info("Generating Markdown from OCR response")
                
                # Extract metadata
                metadata = {
                    "title": base_name,
                    "source": pdf_path,
                    "file_name": file_name,
                    "file_extension": os.path.splitext(file_name)[1],
                    "file_size_bytes": os.path.getsize(pdf_path),
                    "file_size_mb": file_size_mb,
                    "ocr_engine": "mistral",
                    "document_type": "tourism",
                    "page_count": len(ocr_response.pages),
                    "processing_date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                # Process each page
                updated_markdown_pages = []
                image_counter = 1
                
                # Print the keys and attributes of the first page to understand the structure
                logger.debug(f"OCR response page structure: {dir(ocr_response.pages[0])}")
                
                for i, page in enumerate(ocr_response.pages, 1):
                    # Use index as page number since page_num is not available
                    logger.debug(f"Processing page {i}")
                    
                    # Access the markdown content - adjust if the attribute name differs
                    updated_markdown = page.markdown  # Assuming this attribute exists
                    
                    # Update image references and save images if available
                    if hasattr(page, 'images') and page.images:
                        for image_obj in page.images:
                            # Convert base64 to image
                            base64_str = image_obj.image_base64
                            if base64_str.startswith("data:"):
                                base64_str = base64_str.split(",", 1)[1]
                            image_bytes = base64.b64decode(base64_str)
                            
                            # Image extensions
                            ext = os.path.splitext(image_obj.id)[1] if os.path.splitext(image_obj.id)[1] else ".png"
                            new_image_name = f"{base_name}_img_{image_counter}{ext}"
                            image_counter += 1
                            
                            # Save image
                            image_output_path = os.path.join(images_dir, new_image_name)
                            with open(image_output_path, "wb") as f:
                                f.write(image_bytes)
                            
                            # Update markdown with relative image path
                            updated_markdown = updated_markdown.replace(
                                f"![{image_obj.id}]({image_obj.id})",
                                f"![{new_image_name}]({os.path.relpath(image_output_path, output_dir)})"
                            )
                    
                    # Add page number metadata
                    page_markdown = f"## Page {i}\n\n{updated_markdown}"
                    updated_markdown_pages.append(page_markdown)
                
                # Combine all pages
                full_text = "\n\n".join(updated_markdown_pages)
                
                # Create markdown content with YAML frontmatter
                md_content = "---\n"
                for key, value in metadata.items():
                    if value:  # Only include non-empty metadata
                        # Format the value properly for YAML
                        if isinstance(value, str) and ('\n' in value or ':' in value or '"' in value):
                            # Multi-line or special character content needs to be quoted
                            md_content += f'{key}: "{value.replace('"', '\\"')}"\n'
                        else:
                            md_content += f"{key}: {value}\n"
                md_content += "---\n\n"
                md_content += full_text
                
                # Write markdown file
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(md_content)
                
                logger.info(f"Successfully converted {pdf_path} to {output_path} using Mistral OCR")
                return output_path
                
            except Exception as e:
                logger.warning(f"Mistral OCR processing failed, falling back to PyPDF: {str(e)}")
        
        # Fallback to PyPDFLoader
        loader = PyPDFLoader(pdf_path)
        pages = loader.load()
        
        # Extract metadata from the PDF
        metadata = {}
        if pages and hasattr(pages[0], 'metadata'):
            metadata = pages[0].metadata.copy()
        
        # Add custom metadata
        metadata["file_path"] = pdf_path
        metadata["title"] = metadata.get("title", base_name)
        metadata["file_name"] = file_name
        metadata["file_extension"] = os.path.splitext(file_name)[1]
        metadata["file_size_bytes"] = os.path.getsize(pdf_path)
        metadata["processing_date"] = time.strftime("%Y-%m-%d")
        metadata["page_count"] = len(pages)
        metadata["ocr_engine"] = "pypdf"
        metadata["document_type"] = "tourism"
        
        # Process each page
        page_contents = []
        for i, page in enumerate(pages, 1):
            page_contents.append(f"## Page {i}\n\n{page.page_content}")
        
        # Combine all pages text
        text = "\n\n".join(page_contents)
        
        # Create markdown content with YAML frontmatter
        md_content = "---\n"
        for key, value in metadata.items():
            if value:  # Only include non-empty metadata
                # Format the value properly for YAML
                if isinstance(value, str) and ('\n' in value or ':' in value or '"' in value):
                    # Multi-line or special character content needs to be quoted
                    md_content += f'{key}: "{value.replace('"', '\\"')}"\n'
                else:
                    md_content += f"{key}: {value}\n"
        md_content += "---\n\n"
        md_content += text
        
        # Write markdown file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
            
        logger.info(f"Created markdown file: {output_path} using PyPDF")
        return output_path
        
    except Exception as e:
        logger.error(f"Error converting PDF to markdown: {str(e)}")
        return None


def _load_document(file_path: str):
    """
    Load a document from a file path (supports Markdown files)
    
    Args:
        file_path: Path to the document
        
    Returns:
        List of document objects
    """
    try:
        # Handle markdown files with frontmatter
        if (file_path.endswith('.md')):
            with open(file_path, 'r', encoding='utf-8') as f:
                # Parse frontmatter and content
                post = frontmatter.load(f)
                metadata = dict(post.metadata)
                content = post.content
                
                # Create document object
                from langchain.schema import Document
                return [Document(
                    page_content=content,
                    metadata={
                        'source': file_path,
                        **metadata
                    }
                )]
        else:
            # For other file types
            from langchain.document_loaders import TextLoader
            loader = TextLoader(file_path)
            return loader.load()
            
    except Exception as e:
        logger.error(f"Error loading document: {str(e)}")
        return []


def extract_metadata_from_text(text: str) -> Dict[str, Any]:
    """
    Extract additional metadata from the text content
    
    Args:
        text: Document text content
        
    Returns:
        Dictionary of extracted metadata
    """
    metadata = {}
    
    # Extract potential topics/categories using simple keyword frequency
    words = re.findall(r'\b\w+\b', text.lower())
    word_freq = {}
    for word in words:
        if len(word) > 3:  # Skip short words
            word_freq[word] = word_freq.get(word, 0) + 1
    
    # Get top keywords (excluding common words)
    common_words = {'from', 'this', 'that', 'with', 'have', 'they', 'will', 'would', 'been', 'there'}
    keywords = [word for word, count in sorted(word_freq.items(), key=lambda x: x[1], reverse=True) 
                if word not in common_words][:10]
    
    metadata['keywords'] = keywords
    
    # Try to extract a summary (first paragraph or two)
    paragraphs = [p for p in text.split('\n\n') if p.strip()]
    if paragraphs:
        summary = paragraphs[0]
        if len(paragraphs) > 1:
            summary += '\n\n' + paragraphs[1]
        metadata['summary'] = summary[:500]  # Limit to 500 chars
    
    # Extract location information that might be present
    location_patterns = [
        r'\b(?:in|at|from|to) ([A-Z][a-z]+(?: [A-Z][a-z]+)*)\b',  # Places following prepositions
        r'\b([A-Z][a-z]+(?: [A-Z][a-z]+)*) (?:Beach|Mountain|Park|Forest|Island|Castle|Palace|Temple|Museum)\b'  # Named locations
    ]
    
    locations = []
    for pattern in location_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            if isinstance(match, tuple):
                match = match[0]  # Extract from tuple if needed
            if match and match not in locations and len(match) > 3:
                locations.append(match)
    
    if locations:
        metadata['locations'] = locations[:10]  # Limit to top 10 locations
    
    # Try to detect tourism-related keywords
    tourism_keywords = ['tour', 'guide', 'travel', 'visit', 'attraction', 'tourist', 'vacation', 
                        'holiday', 'destination', 'sightseeing', 'accommodation', 'hotel', 
                        'resort', 'beach', 'mountain', 'adventure', 'excursion', 'trip']
    
    detected_keywords = []
    for keyword in tourism_keywords:
        if re.search(r'\b' + keyword + r'\w*\b', text.lower()):
            detected_keywords.append(keyword)
    
    if detected_keywords:
        metadata['tourism_keywords'] = detected_keywords
    
    # Try to extract any activities mentioned
    activity_patterns = [
        r'\b(?:enjoy|experience|try) (?:the )?([\w\s]+)\b',
        r'\b(?:activities|experiences) (?:include|such as|like) ([\w\s,]+)\b'
    ]
    
    activities = []
    for pattern in activity_patterns:
        matches = re.findall(pattern, text)
        activities.extend([m.strip() for m in matches if len(m.strip()) > 3])
    
    if activities:
        metadata['activities'] = activities[:10]  # Limit to top 10 activities
    
    return metadata


def chunk_cluster_with_embeddings(
    file_path: str,
    max_chunk_size: int = 500,
    model_name: str = "text-embedding-3-large",
    common_metadata: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Loads a document from a file path (supports Markdown files),
    chunks text using ClusterSemanticChunker, and prepares chunks for embeddings.
    
    Args:
        file_path: File path of the document (supports .md files)
        max_chunk_size: Maximum size of each chunk in tokens
        model_name: Name of the embedding model to use
        common_metadata: Common metadata to include with each chunk
        
    Returns:
        List of dictionaries containing chunk text and metadata
    """
    if common_metadata is None:
        common_metadata = {}
    
    # Load the document
    docs = _load_document(file_path)
    
    # Define token counting function (using tiktoken for OpenAI-compatible tokenization)
    def token_counter(text):
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))
    
    # Initialize the ClusterSemanticChunker
    text_splitter = ClusterSemanticChunker(
        max_chunk_size=max_chunk_size,
        length_function=token_counter
    )
    
    # Process each document
    result = []
    for doc in docs:
        # Split the document text
        chunks = text_splitter.split_text(doc.page_content)
        
        # Create embeddings for each chunk
        for i, chunk_text in enumerate(chunks):
            
            # Create metadata
            chunk_metadata = {
                "source": doc.metadata.get("source", file_path),
                "chunk_index": i,
                "total_chunks": len(chunks),
                "chunking_strategy": "cluster"
            }
            
            # Add document metadata
            for key, value in doc.metadata.items():
                if key != "source":  # Already included above
                    chunk_metadata[key] = value
            
            # Add any common metadata
            chunk_metadata.update(common_metadata)
            
            result.append({
                "text": chunk_text,
                "metadata": chunk_metadata
            })

    return result


def load_chunks_into_pinecone(
    chunks: List[Dict[str, Any]],
    collection_name: str,
    chunk_strategy: Optional[str] = "cluster"
):
    """
    Load chunks into Pinecone vector database
    
    Args:
        chunks: List of chunks with text and metadata
        collection_name: Name of the Pinecone collection
        chunk_strategy: Chunking strategy used
        
    Returns:
        Collection name
    """
    logger.info(f"Loading chunks into Pinecone collection: {collection_name}")
    logger.info(f"Number of chunks: {len(chunks)}")
    
    # Initialize Pinecone client with API key from environment variable
    pine_cone = os.getenv("PINECONE_API_KEY") or config.PINECONE_API_KEY
    if not pine_cone:
        raise ValueError("PINECONE_API_KEY environment variable not set")
    
    pc = Pinecone(api_key=pine_cone)
    
    # Check if index exists, if not create it
    try:
        # List indexes
        indexes = pc.list_indexes()
        
        # Create index if it doesn't exist
        if collection_name not in [index.name for index in indexes]:
            logger.info(f"Creating new Pinecone index: {collection_name}")
            pc.create_index(
                name=collection_name,
                dimension=config.DEFAULT_PINECONE_DIMENSION,
                metric=config.DEFAULT_PINECONE_METRIC,
                spec={
                    "serverless": {
                        "cloud": "aws",
                        "region": config.DEFAULT_PINECONE_REGION
                    }
                }
            )
    except Exception as e:
        logger.error(f"Error checking/creating index: {str(e)}")
    
    # Connect to the index
    index = pc.Index(name=collection_name)
    
    openai_api_key = os.getenv("OPENAI_API_KEY") or config.OPENAI_API_KEY
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    
    # Initialize embedding model
    embeddings = OpenAIEmbeddings(
        model=config.EMBEDDING_MODEL,
        openai_api_key=openai_api_key
    )
    
    # Prepare vectors for upsert
    vectors_to_upsert = []
    timestamp = int(time.time())
    
    for i, chunk in enumerate(chunks):
        # Extract the text field
        text_field = chunk.get("text", "")
        
        # Skip empty chunks
        if not text_field.strip():
            logger.warning(f"Skipping empty chunk {i}")
            continue
        
        # Extract metadata
        metadata = chunk.get("metadata", {})
        
        # Extract additional metadata from text content
        additional_metadata = extract_metadata_from_text(text_field)
        
        # COMPLETELY FLATTEN the structure - no nested objects at all
        flat_metadata = {}
        
        # Add the text content for searching (truncate if too long)
        max_text_length = 8000  # Pinecone may have limits on metadata size
        flat_metadata["text"] = text_field[:max_text_length]
        flat_metadata["chunk_strategy"] = chunk_strategy
        
        # Add chunk index and position information
        flat_metadata["chunk_index"] = i
        flat_metadata["chunk_count"] = len(chunks)
        
        # Add timestamp
        flat_metadata["timestamp"] = timestamp
        flat_metadata["processing_date"] = datetime.datetime.now().strftime("%Y-%m-%d")
        
        # Add document type for tourism
        flat_metadata["document_type"] = "tourism"
        
        # Add additional metadata
        for key, value in additional_metadata.items():
            # Convert lists to comma-separated strings for Pinecone compatibility
            if isinstance(value, list):
                flat_metadata[key] = ", ".join(str(v) for v in value)
            elif isinstance(value, (str, int, float, bool)):
                flat_metadata[key] = value
        
        # Flatten all metadata fields from original metadata
        for key, value in metadata.items():
            # Ensure all values are primitive types (string, number, boolean, or list of strings)
            if isinstance(value, (str, int, float, bool)):
                flat_metadata[key] = value
            elif isinstance(value, list) and all(isinstance(item, str) for item in value):
                flat_metadata[key] = ", ".join(value)
            else:
                # Convert any complex types to strings
                flat_metadata[key] = str(value)
        
        # Generate embedding with error handling
        try:
            embedding = embeddings.embed_query(text_field)
            doc_prefix = f"{collection_name}_{timestamp}"

            # Then create the chunk ID
            chunk_id = f"{doc_prefix}_chunk_{i}"
            
            vectors_to_upsert.append({
                "id": chunk_id,
                "values": embedding,
                "metadata": flat_metadata  # Completely flattened metadata
            })
        except Exception as e:
            logger.error(f"Error generating embedding for chunk {i}: {str(e)}")
    
    # Upsert in batches
    batch_size = 100
    total_vectors = len(vectors_to_upsert)
    total_batches = (total_vectors + batch_size - 1) // batch_size
    
    if total_vectors == 0:
        logger.warning("No valid vectors to upsert")
        return collection_name
    
    logger.info(f"Upserting {total_vectors} vectors in {total_batches} batches")
    
    for i in range(0, total_vectors, batch_size):
        batch = vectors_to_upsert[i:i+batch_size]
        try:
            index.upsert(vectors=batch)
            logger.info(f"Upserted batch {i//batch_size + 1}/{total_batches}")
        except Exception as e:
            logger.error(f"Error upserting batch {i//batch_size + 1}: {str(e)}")
    
    logger.info(f"Successfully loaded {total_vectors} vectors into Pinecone index '{collection_name}'")
    return collection_name


def process_pdf_folder(
    input_folder: str,
    output_folder: str,
    collection_name: str,
    max_chunk_size: int = 500,
    embedding_model: str = "text-embedding-3-large",
    num_workers: int = 4,
    dry_run: bool = False
):
    """
    Process all PDF files in a folder, convert to markdown, chunk, and load into Pinecone
    
    Args:
        input_folder: Folder containing PDF files
        output_folder: Folder to save markdown files
        collection_name: Name of the Pinecone collection
        max_chunk_size: Maximum size of each chunk in tokens
        embedding_model: Name of the embedding model to use
        num_workers: Number of worker threads
        dry_run: If True, don't upload to Pinecone
        
    Returns:
        Number of processed files
    """
    # Create output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)
    
    # Find all PDF files in the input folder
    pdf_files = glob.glob(os.path.join(input_folder, "*.pdf"))
    logger.info(f"Found {len(pdf_files)} PDF files in {input_folder}")
    
    if not pdf_files:
        logger.warning(f"No PDF files found in {input_folder}")
        return 0
    
    # Process files in parallel
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        # Submit conversion tasks
        future_to_file = {
            executor.submit(convert_pdf_to_markdown, pdf_file, output_folder): pdf_file
            for pdf_file in pdf_files
        }
        
        # Process results as they complete
        markdown_files = []
        for future in tqdm.tqdm(as_completed(future_to_file), total=len(pdf_files), desc="Converting PDFs"):
            pdf_file = future_to_file[future]
            try:
                markdown_file = future.result()
                if markdown_file:
                    markdown_files.append(markdown_file)
                    logger.info(f"Successfully converted {pdf_file} to {markdown_file}")
                else:
                    logger.error(f"Failed to convert {pdf_file}")
            except Exception as e:
                logger.error(f"Exception processing {pdf_file}: {str(e)}")
        
        logger.info(f"Successfully converted {len(markdown_files)} out of {len(pdf_files)} PDF files")
    
    # Process each markdown file
    all_chunks = []
    
    for md_file in tqdm.tqdm(markdown_files, desc="Processing markdown files"):
        try:
            # Common metadata for all chunks from this file
            file_name = os.path.basename(md_file)
            common_metadata = {
                "source_file": file_name,
                "file_path": md_file,
                "document_type": "tourism",
                "processed_date": datetime.datetime.now().isoformat()
            }
            
            # Chunk the markdown file
            chunks = chunk_cluster_with_embeddings(
                md_file,
                max_chunk_size=max_chunk_size,
                model_name=embedding_model,
                common_metadata=common_metadata
            )
            
            all_chunks.extend(chunks)
            logger.info(f"Generated {len(chunks)} chunks from {md_file}")
            
        except Exception as e:
            logger.error(f"Error processing markdown file {md_file}: {str(e)}")
    
    logger.info(f"Generated a total of {len(all_chunks)} chunks from {len(markdown_files)} markdown files")
    
    # Save all chunks to a JSON file for backup/debugging
    chunks_file = os.path.join(output_folder, f"all_chunks_{int(time.time())}.json")
    with open(chunks_file, 'w', encoding='utf-8') as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)
    logger.info(f"Saved all chunks to {chunks_file}")
    
    # Load chunks into Pinecone if not a dry run
    if not dry_run and all_chunks:
        try:
            load_chunks_into_pinecone(
                all_chunks,
                collection_name,
                chunk_strategy="cluster"
            )
            logger.info(f"Successfully loaded chunks into Pinecone collection: {collection_name}")
        except Exception as e:
            logger.error(f"Error loading chunks into Pinecone: {str(e)}")
    elif dry_run:
        logger.info("Dry run - skipping Pinecone upload")
    
    return len(markdown_files)


def main():
    """Main entry point for the application"""
    parser = argparse.ArgumentParser(description='Process PDF files to Pinecone')
    
    parser.add_argument('--input', '-i', required=True, help='Input folder containing PDF files')
    parser.add_argument('--output', '-o', required=True, help='Output folder for markdown files')
    parser.add_argument('--collection', '-c', required=True, help='Pinecone collection name')
    parser.add_argument('--chunk-size', '-s', type=int, default=config.DEFAULT_CHUNK_SIZE, 
                        help=f'Max chunk size in tokens (default: {config.DEFAULT_CHUNK_SIZE})')
    parser.add_argument('--workers', '-w', type=int, default=config.DEFAULT_NUM_WORKERS, 
                        help=f'Number of worker threads (default: {config.DEFAULT_NUM_WORKERS})')
    parser.add_argument('--dry-run', '-d', action='store_true', help='Do not upload to Pinecone')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Configure logging based on verbosity
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Check if environment variables are set
    if not os.getenv("OPENAI_API_KEY") and not config.OPENAI_API_KEY and not args.dry_run:
        logger.error("OPENAI_API_KEY environment variable or config setting not set")
        return 1
    
    if not os.getenv("PINECONE_API_KEY") and not config.PINECONE_API_KEY and not args.dry_run:
        logger.error("PINECONE_API_KEY environment variable or config setting not set")
        return 1
    
    # Process the PDF folder
    try:
        processed_files = process_pdf_folder(
            input_folder=args.input,
            output_folder=args.output,
            collection_name=args.collection,
            max_chunk_size=args.chunk_size,
            num_workers=args.workers,
            dry_run=args.dry_run
        )
        
        logger.info(f"Successfully processed {processed_files} files")
        return 0
        
    except Exception as e:
        logger.error(f"Error processing PDF folder: {str(e)}")
        return 1


if __name__ == "__main__":
    exit(main())