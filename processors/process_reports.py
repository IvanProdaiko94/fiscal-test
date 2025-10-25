"""
Program 2: Download and Process Reports

This program downloads PDF and XLSX documents found by Program 1 and extracts
their text content for further processing.
"""

import json
import logging
import os
import sys
from typing import List, Dict, Any, Optional

# Add the parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pkg.models import ExtractedDocument
from pkg.pdf_extractor import PDFExtractor
from pkg.xlsx_extractor import XLSXExtractor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('process_reports.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class ReportProcessor:
    """Downloads and processes PDF and XLSX documents."""
    
    def __init__(self):
        self.pdf_extractor = PDFExtractor()
        self.xlsx_extractor = XLSXExtractor()
        self.output_dir = "processed_reports"
        os.makedirs(self.output_dir, exist_ok=True)
    
    def load_reports_metadata(self, metadata_file: str) -> Dict[str, Any]:
        """Load the reports metadata from Program 1."""
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            # Extract companies data from the new structure
            companies_data = metadata.get('companies', {})
            logger.info(f"Loaded metadata for {len(companies_data)} companies")
            
            # Count total reports from the new structure
            total_reports = 0
            for company_data in companies_data.values():
                reports = company_data.get('reports', [])
                for year_data in reports:
                    total_reports += len(year_data.get('best', [])) + len(year_data.get('secondary', []))
            
            logger.info(f"Total reports found: {total_reports}")
            
            return companies_data
        except Exception as e:
            logger.error(f"Error loading metadata from {metadata_file}: {e}")
            return {}
    
    def find_best_reports_for_company(self, ticker: str, company_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find the best report for each year for a company from the array structure."""
        reports = company_data.get('reports', [])
        if not reports:
            logger.warning(f"No reports found for {ticker}")
            return []
        
        # Extract the best reports from the array structure
        best_reports = []
        for year_data in reports:
            year = year_data.get('year')
            best_reports_for_year = year_data.get('best', [])
            
            if best_reports_for_year:
                # Take the first (best) report for this year
                best_report = best_reports_for_year[0]
                simplified_report = {
                    'year': year,
                    'url': best_report.get('url'),
                    'title': best_report.get('title')
                }
                best_reports.append(simplified_report)
                logger.info(f"Selected best report for {ticker} {year}: {best_report.get('title', 'Unknown')} -> {best_report.get('url')}")
        
        logger.info(f"Selected {len(best_reports)} best reports for {ticker}")
        return best_reports

    def _select_best_report_for_year(self, year_reports: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Select the best report from a list of reports for the same year."""
        if not year_reports:
            return None
        
        # Priority order for report types
        priority_keywords = [
            'form 20f', '20-f', '20f', 'form20f',
            'annual report', 'annual', 'yearly',
            'financial report', 'consolidated',
            'statements', 'accounts'
        ]
        
        # Score each report based on title and URL
        scored_reports = []
        for report in year_reports:
            title = report.get('title', '').lower()
            url = report.get('url', '').lower()
            
            score = 0
            for i, keyword in enumerate(priority_keywords):
                if keyword in title or keyword in url:
                    # Higher score for higher priority keywords
                    score += (len(priority_keywords) - i) * 10
                    break
            
            # Bonus points for specific indicators
            if 'form' in title and '20' in title:
                score += 50
            if 'annual' in title:
                score += 30
            if 'consolidated' in title:
                score += 20
            
            scored_reports.append((score, report))
        
        # Sort by score (highest first) and return the best
        scored_reports.sort(key=lambda x: x[0], reverse=True)
        best_report = scored_reports[0][1]
        
        logger.debug(f"Selected report with score {scored_reports[0][0]}: {best_report.get('title', 'Unknown')}")
        return best_report
    
    
    def process_single_document(self, url: str, title: str, year: Optional[int], ticker: str) -> Optional[ExtractedDocument]:
        """Process a single document (PDF or XLSX)."""
        logger.info(f"Processing document: {title} ({year}) from {ticker}")
        
        try:
            # Simple logic: check URL extension first
            url_lower = url.lower()
            
            if url_lower.endswith('.pdf'):
                # Try PDF extraction
                logger.info(f"URL ends with .pdf, trying PDF extraction for {url}")
                content = self.pdf_extractor.extract_text_from_pdf_url(url)
                file_type = "PDF"
            elif url_lower.endswith('.xlsx') or url_lower.endswith('.xls'):
                # Try XLSX extraction
                logger.info(f"URL ends with .xlsx/.xls, trying XLSX extraction for {url}")
                content = self.xlsx_extractor.extract_text_from_xlsx_url(url)
                file_type = "XLSX"
            else:
                # Unclear extension - try PDF first, then XLSX
                logger.info(f"Unclear file extension for {url}, trying PDF first, then XLSX")
                
                # Try PDF first
                logger.info(f"Trying PDF extraction first for {url}")
                content = self.pdf_extractor.extract_text_from_pdf_url(url)
                if content:
                    file_type = "PDF"
                    logger.info(f"Successfully extracted as PDF: {url}")
                else:
                    # Try XLSX if PDF failed
                    logger.info(f"PDF extraction failed, trying XLSX extraction for {url}")
                    content = self.xlsx_extractor.extract_text_from_xlsx_url(url)
                    if content:
                        file_type = "XLSX"
                        logger.info(f"Successfully extracted as XLSX: {url}")
                    else:
                        # Skip if both failed
                        logger.warning(f"Both PDF and XLSX extraction failed for {url}")
                        return None
            
            if not content:
                logger.warning(f"Failed to extract content from {url}")
                return None
            
            # Create document object
            document = ExtractedDocument(
                url=url,
                title=title,
                content=content,
                year=year
            )
            
            # Save content to a file for debugging
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            content_file = os.path.join(self.output_dir, f"{ticker}_{year}_{safe_title}_{file_type.lower()}.txt")
            
            with open(content_file, 'w', encoding='utf-8') as f:
                f.write(f"URL: {url}\n")
                f.write(f"Title: {title}\n")
                f.write(f"Year: {year}\n")
                f.write(f"Ticker: {ticker}\n")
                f.write(f"File Type: {file_type}\n")
                f.write("=" * 50 + "\n")
                f.write(content)
            
            logger.info(f"Saved {file_type} content to {content_file}")
            return document
            
        except Exception as e:
            logger.error(f"Error processing document {url}: {e}")
            return None
    
    def process_company_reports(self, ticker: str, company_data: Dict[str, Any]) -> List[ExtractedDocument]:
        """Process the best reports for a single company."""
        # Find the best reports for this company
        best_reports = self.find_best_reports_for_company(ticker, company_data)
        
        if not best_reports:
            logger.warning(f"No best reports selected for {ticker}")
            return []
        
        logger.info(f"Processing {len(best_reports)} best reports for {ticker}")
        
        processed_documents = []
        
        for report in best_reports:
            url = report.get('url')
            year = report.get('year')
            
            if not url:
                logger.warning(f"Skipping report with no URL for year {year}")
                continue
            
            # Create a title from the year since we only have year and url
            title = f"Annual Report {year}"
            
            document = self.process_single_document(url, title, year, ticker)
            if document:
                processed_documents.append(document)
        
        logger.info(f"Successfully processed {len(processed_documents)}/{len(best_reports)} best reports for {ticker}")
        return processed_documents
    
    def process_all_reports(self, companies_data: Dict[str, Any]) -> Dict[str, List[ExtractedDocument]]:
        """Process the best reports for all companies."""
        all_processed = {}
        all_best_reports = {}
        
        for ticker, company_data in companies_data.items():
            logger.info(f"Processing best reports for {ticker}")
            
            # Get the best reports selection for this company
            best_reports = self.find_best_reports_for_company(ticker, company_data)
            all_best_reports[ticker] = best_reports
            
            # Process the selected reports
            processed_docs = self.process_company_reports(ticker, company_data)
            all_processed[ticker] = processed_docs
        
        return all_processed


def main():
    """Main execution function for Program 2."""
    logger.info("Starting Program 2: Report Download and Processing")
    
    try:
        metadata_file = "./reports/annual_reports_ranked.json"
        if not os.path.exists(metadata_file):
            logger.error(f"Metadata file not found: {metadata_file}")
            logger.error("Please run Program 1 first to search for annual reports")
            return
        
        # Initialize processor
        processor = ReportProcessor()
        
        # Load reports metadata
        logger.info("Loading reports metadata...")
        companies_data = processor.load_reports_metadata(metadata_file)
        
        if not companies_data:
            logger.error("No companies data loaded. Please check the metadata file.")
            return
        
        # Process best reports for all companies
        logger.info("Processing best reports for all companies...")
        all_processed = processor.process_all_reports(companies_data)

        # Print summary
        total_processed = sum(len(docs) for docs in all_processed.values())
        total_content = sum(sum(len(doc.content) for doc in docs) for docs in all_processed.values())
        
        logger.info(f"Report processing completed successfully!")
        logger.info(f"Processed {total_processed} best documents across {len(all_processed)} companies")
        logger.info(f"Total content length: {total_content:,} characters")

        # Print company summaries
        for ticker, documents in all_processed.items():
            years = sorted(list(set(d.year for d in documents if d.year)))
            content_length = sum(len(doc.content) for doc in documents)
            logger.info(f"{ticker}: {len(documents)} documents, years: {years}, content: {content_length:,} chars")
    
    except Exception as e:
        logger.error(f"Fatal error in Program 2: {e}")
        raise


if __name__ == "__main__":
    main()
