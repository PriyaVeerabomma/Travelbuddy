"""
Configuration for the PDF processor with Mistral OCR
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

# Mistral OCR settings
MISTRAL_OCR_MODEL = os.getenv("MISTRAL_OCR_MODEL", "mistral-ocr-latest")
MAX_FILE_SIZE_MB = 70  # Maximum file size in MB for OCR processing

# Embedding settings
EMBEDDING_MODEL = "text-embedding-3-large"

# Chunking settings
DEFAULT_CHUNK_SIZE = 500  # Maximum size of each chunk in tokens

# Pinecone settings
DEFAULT_PINECONE_REGION = "us-east-1"
DEFAULT_PINECONE_METRIC = "cosine"
DEFAULT_PINECONE_DIMENSION = 3072  # Dimension for text-embedding-3-large

# Processing settings
DEFAULT_NUM_WORKERS = 4  # Default number of worker threads