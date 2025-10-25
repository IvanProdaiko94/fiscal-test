"""
Program 3: Transform PDFs to Financial Statements

This program takes processed PDF documents and extracts structured financial
statement data using collaborative AI agents (Financial Analyst + Reports Writer),
then exports to CSV files organized by company/year/statement_type structure.
"""

import logging
import os
import sys
import argparse
import pandas as pd
from typing import List, Dict, Optional, Tuple
from dotenv import load_dotenv

# Add the parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pkg.models import Company, ExtractedDocument, StatementType
from pkg.financial_agents import CollaborativeFinancialExtractor
from pkg.financial_schemas import ComprehensiveFinancialSchemas

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('transform_statements.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Handles document loading and parsing."""
    
    @staticmethod
    def load_processed_documents_from_folder(input_folder: str) -> Dict[str, List[ExtractedDocument]]:
        """Load all processed documents from the input folder."""
        if not os.path.exists(input_folder):
            logger.error(f"Input folder not found: {input_folder}")
            return {}
            
        all_documents = {}
        txt_files = [f for f in os.listdir(input_folder) if f.endswith('.txt')]
        logger.info(f"Found {len(txt_files)} text files in {input_folder}")
        
        for txt_file in txt_files:
            document = DocumentProcessor._parse_document_file(input_folder, txt_file)
            if document:
                ticker = DocumentProcessor._extract_ticker_from_filename(txt_file)
                if ticker not in all_documents:
                    all_documents[ticker] = []
                all_documents[ticker].append(document)
                logger.info(f"Loaded document: {document.title} ({document.year}) for {ticker}")
        
        logger.info(f"Loaded processed documents for {len(all_documents)} companies")
        return all_documents
    
    @staticmethod
    def _parse_document_file(input_folder: str, txt_file: str) -> Optional[ExtractedDocument]:
        """Parse a single document file."""
        file_path = os.path.join(input_folder, txt_file)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            if len(lines) < 5:
                logger.warning(f"Skipping {txt_file}: insufficient content")
                return None
            
            # Extract metadata
            url = lines[0].replace('URL: ', '') if lines[0].startswith('URL: ') else ""
            title = lines[1].replace('Title: ', '') if lines[1].startswith('Title: ') else ""
            year_line = lines[2].replace('Year: ', '') if lines[2].startswith('Year: ') else ""
            
            # Extract year
            year = None
            try:
                year = int(year_line) if year_line.isdigit() else None
            except ValueError:
                pass
            
            # Skip separator line and get actual content
            actual_content = '\n'.join(lines[5:])
            
            if not actual_content.strip():
                logger.warning(f"Skipping {txt_file}: no content found")
                return None
            
            return ExtractedDocument(
                url=url,
                title=title,
                content=actual_content,
                year=year
            )
            
        except Exception as e:
            logger.error(f"Error processing file {txt_file}: {e}")
            return None
    
    @staticmethod
    def _extract_ticker_from_filename(filename: str) -> str:
        """Extract ticker from filename."""
        # Expected format: TICKER_YEAR_Title.txt
        parts = filename.split('_')
        return parts[0] if parts else "UNKNOWN"


class CSVExporter:
    """Handles CSV export with comprehensive field structure."""
    
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        self.schemas = ComprehensiveFinancialSchemas()
        os.makedirs(output_dir, exist_ok=True)
    
    def save_document_results(self, ticker: str, year: int, statements: Dict[StatementType, any]) -> bool:
        """Save results for a single document with comprehensive field structure."""
        try:
            year_dir = os.path.join(self.output_dir, ticker, str(year))
            os.makedirs(year_dir, exist_ok=True)
            
            success_count = 0
            for statement_type, statement in statements.items():
                if self._create_comprehensive_csv(statement_type, statement, year_dir, ticker, year):
                    success_count += 1
            
            logger.info(f"Saved {success_count}/{len(statements)} statements for {ticker} {year}")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Error saving results for {ticker} ({year}): {e}")
            return False
    
    def _create_comprehensive_csv(self, statement_type: StatementType, statement: any, 
                                year_dir: str, ticker: str, year: int) -> bool:
        """Create a comprehensive CSV with all possible financial fields."""
        try:
            filename = f"{statement_type.value}.csv"
            filepath = os.path.join(year_dir, filename)
            
            # Get comprehensive field mapping
            field_mapping = self.schemas.get_comprehensive_field_mapping()
            statement_fields = field_mapping.get(statement_type.value, {})
            
            # Create comprehensive data structure
            comprehensive_data = []
            currency = statement.data_points[0].currency if statement.data_points else "EUR"
            
            for category, field_names in statement_fields.items():
                for field_name in field_names:
                    matching_value = self._find_matching_value(field_name, statement.data_points)
                    
                    comprehensive_data.append({
                        'line_item': field_name,
                        'value': matching_value,
                        'currency': currency,
                        'year': year,
                        'category': category,
                        'ticker': ticker,
                        'found_in_document': matching_value is not None
                    })
            
            # Create DataFrame and save
            df = pd.DataFrame(comprehensive_data)
            df.to_csv(filepath, index=False)
            
            logger.info(f"Created comprehensive CSV with {len(comprehensive_data)} fields for {statement_type.value}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating CSV for {statement_type.value}: {e}")
            return False
    
    def _find_matching_value(self, field_name: str, data_points: List[any]) -> Optional[float]:
        """Find matching value for a field name."""
        for data_point in data_points:
            if self._is_field_match(field_name, data_point.line_item):
                return data_point.value
        return None
    
    def _is_field_match(self, field_name: str, extracted_line_item: str) -> bool:
        """Check if field name matches extracted line item using fuzzy matching."""
        field_lower = field_name.lower()
        extracted_lower = extracted_line_item.lower()
        
        # Direct match
        if field_lower == extracted_lower:
            return True
        
        # Partial match for key terms
        field_keywords = field_lower.split()
        matching_keywords = sum(1 for keyword in field_keywords if keyword in extracted_lower)
        return matching_keywords >= len(field_keywords) * 0.6  # 60% keyword match threshold


class FinancialStatementTransformer:
    """Transforms processed PDFs into structured financial statements using collaborative AI agents."""
    
    def __init__(self, openai_api_key: str, output_dir: str = "./output"):
        self.collaborative_extractor = CollaborativeFinancialExtractor(openai_api_key)
        self.csv_exporter = CSVExporter(output_dir)
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
    
    def process_single_document(self, document: ExtractedDocument, ticker: str) -> Dict[StatementType, any]:
        """Process a single document using collaborative AI agents."""
        logger.info(f"Processing document: {document.title} ({document.year}) for {ticker}")
        
        statements = {}
        for statement_type in [StatementType.INCOME_STATEMENT, StatementType.BALANCE_SHEET, StatementType.CASH_FLOW_STATEMENT]:
            logger.info(f"Collaborative extraction of {statement_type.value} for {ticker} ({document.year})")
            
            try:
                statement = self.collaborative_extractor.extract_financial_data(document, statement_type)
                if statement:
                    statement.company_ticker = ticker
                    statements[statement_type] = statement
                    logger.info(f"Successfully extracted {statement_type.value} with {len(statement.data_points)} line items")
                else:
                    logger.warning(f"Failed to extract {statement_type.value} for {ticker} ({document.year})")
            except Exception as e:
                logger.error(f"Error extracting {statement_type.value} for {ticker} ({document.year}): {e}")
        
        return statements
    
    def process_and_save_document(self, document: ExtractedDocument, ticker: str) -> bool:
        """Process a single document and save results immediately."""
        statements = self.process_single_document(document, ticker)
        
        if statements:
            success = self.csv_exporter.save_document_results(ticker, document.year, statements)
            if success:
                logger.info(f"Successfully processed and saved: {document.title} ({document.year})")
            return success
        else:
            logger.warning(f"No statements extracted for {ticker} ({document.year})")
            return False


def create_companies_from_documents(all_documents: Dict[str, List[ExtractedDocument]]) -> Dict[str, Company]:
    """Create company objects from document metadata."""
    companies = {}
    
    for ticker, documents in all_documents.items():
        if documents:
            first_doc = documents[0]
            company_name = first_doc.title.replace('Annual Report', '').strip()
            if not company_name:
                company_name = ticker
            
            companies[ticker] = Company(
                name=company_name,
                ticker=ticker,
                reports_link=""  # Not needed for transformation
            )
            logger.info(f"Created company: {company_name} ({ticker})")
    
    return companies


def main():
    """Main execution function for Program 3."""
    parser = argparse.ArgumentParser(description='Transform PDFs to Financial Statements using AI Agents')
    parser.add_argument('--input-folder', '-i', 
                       default='./processed_pdfs',
                       help='Input folder containing processed PDF documents (default: ./processed_pdfs)')
    parser.add_argument('--output-folder', '-o', 
                       default='./output',
                       help='Output folder for CSV files (default: ./output)')
    
    args = parser.parse_args()
    
    logger.info("Starting Program 3: Financial Statement Transformation with AI Agents")
    logger.info(f"Input folder: {args.input_folder}")
    logger.info(f"Output folder: {args.output_folder}")
    
    # Check for the OpenAI API key
    openai_api_key = os.getenv('OPENAI_API_KEY')
    if not openai_api_key or openai_api_key == 'your_openai_api_key_here':
        logger.error("OPENAI_API_KEY environment variable not set or using default value")
        logger.error("Please set your OpenAI API key in the .env file")
        return
    
    try:
        # Check if input folder exists
        if not os.path.exists(args.input_folder):
            logger.error(f"Input folder not found: {args.input_folder}")
            logger.error("Please run Program 2 first to process PDFs")
            return

        # Initialize transformer
        transformer = FinancialStatementTransformer(openai_api_key, args.output_folder)
        
        # Load processed documents
        logger.info("Loading processed documents from folder...")
        all_documents = DocumentProcessor.load_processed_documents_from_folder(args.input_folder)
        
        if not all_documents:
            logger.error("No processed documents loaded. Please check the input folder contains .txt files.")
            return
        
        # Create company objects
        logger.info("Creating company information from documents...")
        companies = create_companies_from_documents(all_documents)
        
        # Process documents using collaborative AI agents
        logger.info("Processing documents using collaborative AI agents (Financial Analyst + Reports Writer)...")
        
        total_processed = 0
        total_successful = 0
        total_errors = 0
        
        for ticker, documents in all_documents.items():
            company = companies.get(ticker)
            if not company:
                logger.warning(f"Company information not found for {ticker}")
                continue
            
            logger.info(f"Processing {len(documents)} documents for {company.name} ({ticker})")
            
            for document in documents:
                total_processed += 1
                logger.info(f"Processing document {total_processed}: {document.title} ({document.year})")
                logger.info("Using collaborative AI agents: Financial Analyst → Reports Writer → Comprehensive CSV")
                
                # Process and save immediately using collaborative agents
                success = transformer.process_and_save_document(document, ticker)
                
                if success:
                    total_successful += 1
                else:
                    total_errors += 1
        
        # Print final summary
        logger.info(f"Collaborative AI processing completed!")
        logger.info(f"Total documents processed: {total_processed}")
        logger.info(f"Successfully processed: {total_successful}")
        logger.info(f"Failed: {total_errors}")
        logger.info(f"Success rate: {(total_successful/total_processed*100):.1f}%" if total_processed > 0 else "N/A")
        logger.info("All CSV files contain comprehensive field structure with blank fields for missing data")
    
    except Exception as e:
        logger.error(f"Fatal error in Program 3: {e}")
        raise


if __name__ == "__main__":
    main()