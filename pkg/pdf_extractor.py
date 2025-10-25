"""
PDF extraction and document processing utilities.
"""

import pypdf
import io
from typing import List, Optional
import logging

from .models import ExtractedDocument, StatementType
from .http_client import HTTPClient

logger = logging.getLogger(__name__)


class PDFExtractor:
    """Handles PDF document extraction and processing."""
    
    def __init__(self):
        self.http_client = HTTPClient()
    
    def extract_text_from_pdf_url(self, url: str) -> Optional[str]:
        """Extract text content from a PDF URL."""
        try:
            response = self.http_client.make_request(url, timeout=30)
            if not response:
                logger.error(f"Failed to fetch PDF from {url}")
                return None
            
            pdf_file = io.BytesIO(response.content)
            pdf_reader = pypdf.PdfReader(pdf_file)
            
            text_content = ""
            for page in pdf_reader.pages:
                text_content += page.extract_text() + "\n"
            
            return text_content.strip()
        except Exception as e:
            logger.error(f"Error extracting text from PDF {url}: {e}")
            return None
    
    def extract_content_from_documents(self, documents: List[ExtractedDocument]) -> List[ExtractedDocument]:
        """Extract PDF content from a list of documents."""
        processed_documents = []
        
        for document in documents:
            logger.info(f"Extracting content from PDF: {document.title}")
            
            # Extract text content from PDF
            content = self.extract_text_from_pdf_url(document.url)
            
            if content:
                # Create a new document with extracted content
                processed_document = ExtractedDocument(
                    url=document.url,
                    title=document.title,
                    content=content,
                    year=document.year,
                )
                processed_documents.append(processed_document)
                logger.info(f"Successfully extracted {len(content)} characters from {document.title}")
            else:
                logger.warning(f"Failed to extract content from {document.title}")
        
        return processed_documents
    
    def classify_document(self, document: ExtractedDocument) -> Optional[StatementType]:
        """Classify a document to determine its statement type."""
        content_lower = document.content.lower()
        title_lower = document.title.lower()
        
        # Income Statement keywords
        income_keywords = [
            'income statement', 'profit and loss', 'p&l', 'revenue', 'sales',
            'operating income', 'net income', 'earnings', 'profit'
        ]
        
        # Balance Sheet keywords
        balance_keywords = [
            'balance sheet', 'statement of financial position', 'assets',
            'liabilities', 'equity', 'shareholders equity'
        ]
        
        # Cash Flow Statement keywords
        cashflow_keywords = [
            'cash flow', 'statement of cash flows', 'operating cash flow',
            'investing cash flow', 'financing cash flow'
        ]
        
        # Check for an income statement
        for keyword in income_keywords:
            if keyword in content_lower or keyword in title_lower:
                return StatementType.INCOME_STATEMENT
        
        # Check for a balance sheet
        for keyword in balance_keywords:
            if keyword in content_lower or keyword in title_lower:
                return StatementType.BALANCE_SHEET
        
        # Check for a cash flow statement
        for keyword in cashflow_keywords:
            if keyword in content_lower or keyword in title_lower:
                return StatementType.CASH_FLOW_STATEMENT
        
        return None
