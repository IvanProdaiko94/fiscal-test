"""
XLSX extraction and document processing utilities.
"""

import pandas as pd
import io
from typing import List, Optional
import logging
import requests

from .models import ExtractedDocument, StatementType
from .http_client import HTTPClient

logger = logging.getLogger(__name__)


class XLSXExtractor:
    """Handles XLSX document extraction and processing."""
    
    def __init__(self):
        self.http_client = HTTPClient()
    
    def extract_text_from_xlsx_url(self, url: str) -> Optional[str]:
        """Extract text content from an XLSX URL."""
        try:
            response = self.http_client.make_request(url, timeout=30)
            if not response:
                logger.error(f"Failed to fetch XLSX from {url}")
                return None
            
            # Validate content type
            content_type = response.headers.get('content-type', '').lower()
            if 'excel' not in content_type and 'spreadsheet' not in content_type and not url.lower().endswith('.xlsx') \
                    and not url.lower().endswith('.xls'):
                logger.warning(f"Content may not be XLSX. Content-Type: {content_type}")
                # Don't fail here, let pandas try to read it anyway
            
            # Read the XLSX file
            xlsx_file = io.BytesIO(response.content)
            
            try:
                # Try to read all sheets
                excel_file = pd.ExcelFile(xlsx_file)
                all_text = []
                
                for sheet_name in excel_file.sheet_names:
                    try:
                        df = pd.read_excel(excel_file, sheet_name=sheet_name)
                        
                        # Convert DataFrame to text with better handling of NaN values
                        sheet_text = f"Sheet: {sheet_name}\n"
                        
                        # Create a more readable representation of the Excel data
                        # Try enhanced financial data extraction first
                        sheet_content = self._extract_financial_data_from_sheet(df)
                        sheet_text += sheet_content
                        sheet_text += "\n\n"
                        
                        all_text.append(sheet_text)
                        
                    except Exception as sheet_error:
                        logger.warning(f"Error reading sheet {sheet_name}: {sheet_error}")
                        continue
                
                extracted_text = '\n'.join(all_text).strip()
                if not extracted_text:
                    logger.warning("No text content extracted from XLSX")
                    return None
                    
                logger.info(f"Successfully extracted {len(extracted_text)} characters from XLSX")
                return extracted_text
                
            except Exception as excel_error:
                logger.error(f"Error reading XLSX file: {excel_error}")
                # Check if this might be a different file type
                if "not a zip file" in str(excel_error).lower() or "badzipfile" in str(excel_error).lower():
                    logger.warning(f"File appears to not be a valid XLSX/ZIP file: {url}")
                return None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error extracting XLSX from {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error extracting text from XLSX {url}: {e}")
            return None
    
    def extract_content_from_documents(self, documents: List[ExtractedDocument]) -> List[ExtractedDocument]:
        """Extract XLSX content from a list of documents."""
        processed_documents = []
        
        for document in documents:
            logger.info(f"Extracting content from XLSX: {document.title}")
            
            # Extract text content from XLSX
            content = self.extract_text_from_xlsx_url(document.url)
            
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
    
    def _dataframe_to_readable_text(self, df) -> str:
        """Convert DataFrame to readable text format, preserving numeric values."""
        if df.empty:
            return "Empty sheet"
        
        # Handle different data types appropriately
        df_formatted = df.copy()
        
        # Convert numeric columns to proper format
        for col in df_formatted.columns:
            if df_formatted[col].dtype in ['float64', 'int64', 'float32', 'int32']:
                # Format numeric columns to remove unnecessary decimal places
                df_formatted[col] = df_formatted[col].apply(
                    lambda x: f"{x:,.0f}" if pd.notna(x) and x == int(x) else f"{x:,.2f}" if pd.notna(x) else ""
                )
            else:
                # For non-numeric columns, replace NaN with empty string
                df_formatted[col] = df_formatted[col].fillna("")
        
        # Convert to string representation
        try:
            # Use to_string with proper formatting
            text = df_formatted.to_string(index=False, na_rep='', max_rows=None, max_cols=None)
            return text
        except Exception as e:
            logger.warning(f"Error formatting DataFrame: {e}")
            # Fallback to simple string conversion
            return str(df_formatted.fillna(''))
    
    def _extract_financial_data_from_sheet(self, df) -> str:
        """Extract financial data from a sheet with enhanced formatting."""
        if df.empty:
            return "Empty sheet"
        
        # Look for common financial statement patterns
        financial_text = []
        
        # Try to identify if this looks like a financial statement
        df_str = df.astype(str).to_string().lower()
        if any(keyword in df_str for keyword in ['revenue', 'income', 'profit', 'assets', 'liabilities', 'cash flow']):
            # This looks like a financial statement, format it nicely
            financial_text.append("=== FINANCIAL STATEMENT DATA ===")
            
            # Format each row
            for idx, row in df.iterrows():
                row_text = []
                for col in df.columns:
                    value = row[col]
                    if pd.notna(value):
                        if isinstance(value, (int, float)):
                            # Format numbers with commas
                            if value == int(value):
                                row_text.append(f"{value:,.0f}")
                            else:
                                row_text.append(f"{value:,.2f}")
                        else:
                            row_text.append(str(value))
                    else:
                        row_text.append("")
                
                financial_text.append(" | ".join(row_text))
        
        return "\n".join(financial_text) if financial_text else self._dataframe_to_readable_text(df)
