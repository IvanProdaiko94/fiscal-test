"""
Program 1: Discover Annual Report PDF Links

This program searches company investor relations websites for annual report PDF links
and creates a JSON file with metadata for later download and processing.
"""

import json
import logging
import os
import sys
import argparse
from datetime import datetime
from typing import List, Dict, Any

# Add the parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pkg.models import Company, ExtractedDocument
from pkg.html_processor import HTMLPageProcessor
from pkg.reports_ranker import ReportsRanker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('search_reports.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class AnnualReportSearcher:
    """Searches for annual reports on company websites."""
    
    def __init__(self, output_dir: str = "reports", years_back: int = 10):
        self.html_processor = HTMLPageProcessor()
        self.reports_ranker = ReportsRanker()
        self.output_dir = output_dir
        self.years_back = years_back
        self.min_year = self._calculate_min_year()
        os.makedirs(self.output_dir, exist_ok=True)
        
        logger.info(f"Year boundary: Searching for reports from {self.min_year} to {datetime.now().year - 1} (excluding current year)")
    
    def _calculate_min_year(self) -> int:
        """Calculate the minimum acceptable year based on the years_back parameter."""
        current_year = datetime.now().year
        min_year = current_year - self.years_back - 1
        return min_year

    def search_company_reports(self, company: Company) -> List[ExtractedDocument]:
        """Search for annual reports for a specific company within the year boundary."""
        logger.info(f"Searching for annual reports: {company.name} ({company.ticker})")

        try:
            # Find annual reports using the HTML processor (without downloading content)
            all_documents = self.html_processor.find_annual_reports(company.reports_link)
            
            # Filter documents by year boundary
            filtered_documents = self._filter_documents_by_year(all_documents)

            if filtered_documents:
                logger.info(f"Found {len(filtered_documents)} annual reports for {company.name} (within {self.years_back} years)")
                for doc in filtered_documents:
                    logger.info(f"  - {doc.title} ({doc.year}) - {doc.url}")
                
                # Log filtered out documents
                filtered_out = len(all_documents) - len(filtered_documents)
                if filtered_out > 0:
                    logger.info(f"  Filtered out {filtered_out} reports outside year boundary ({self.min_year}-{datetime.now().year - 1}) or current year")
            else:
                logger.warning(f"No annual reports found for {company.name} within year boundary")

            return filtered_documents

        except Exception as e:
            logger.error(f"Error searching reports for {company.name}: {e}")
            return []
    
    def _filter_documents_by_year(self, documents: List[ExtractedDocument]) -> List[ExtractedDocument]:
        """Filter documents to only include those within the year boundary, excluding current year."""
        filtered = []
        current_year = datetime.now().year
        
        for doc in documents:
            if doc.year and self.min_year <= doc.year < current_year:
                filtered.append(doc)
            elif doc.year:
                logger.debug(f"Filtered out document {doc.title} ({doc.year}) - outside year boundary or current year")
        
        return filtered

    def search_all_companies(self, companies: List[Company]) -> Dict[str, Dict[str, Any]]:
        """Search for annual reports for all companies and rank them."""
        all_reports = {}
        all_selections = {}

        for company in companies:
            reports = self.search_company_reports(company)
            all_reports[company.ticker] = reports
            
            # Rank and select best reports for this company
            if reports:
                selection = self.reports_ranker.process_company_reports(company.ticker, reports)
                all_selections[company.ticker] = selection
            else:
                all_selections[company.ticker] = {'years_covered': [], 'reports': []}

        return all_selections

    def save_reports_metadata(self, all_selections: Dict[str, Dict[str, Any]]) -> str:
        """Save the ranked and selected reports metadata to JSON file."""
        # Create a selection summary
        selection_summary = self.reports_ranker.create_selection_summary(all_selections)
        
        # Add discovery info
        selection_summary["discovery_info"]["discovery_date"] = __import__('datetime').datetime.now().isoformat()
        selection_summary["discovery_info"]["description"] = "Ranked and selected annual report PDF links with best and secondary options"

        # Save to JSON file
        output_file = os.path.join(self.output_dir, "annual_reports_ranked.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(selection_summary, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved ranked reports metadata to {output_file}")
        return output_file

def load_companies_from_json(filepath: str) -> List[Company]:
    """Load company data from a JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    companies = []
    for item in data:
        company = Company(
            name=item['company_name'],
            ticker=item['ticker'],
            reports_link=item['reports_link']
        )
        companies.append(company)

    return companies


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Discover annual report PDF links on company websites",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python search_reports.py --input ../input.json
  python search_reports.py -i ../input.json --years-back 5
  python search_reports.py -i ../input.json -y 15  # Search 15 years back
  python search_reports.py  # Uses default ../input.json and 10 years back
        """
    )

    parser.add_argument(
        '--input', '-i',
        type=str,
        default='./input.json',
        help='Path to the input JSON file containing company data (default: ./input.json)'
    )

    parser.add_argument(
        '--output', '-o',
        type=str,
        default='./reports',
        help='Output directory for found reports (default: ./reports)'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )

    parser.add_argument(
        '--years-back', '-y',
        type=int,
        default=10,
        help='Number of years back to search for reports (default: 10, e.g., 2014-2025 for 10 years)'
    )

    return parser.parse_args()


def main():
    """Main execution function for Program 1."""
    # Parse command line arguments
    args = parse_arguments()

    # Configure logging level based on verbose flag
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.info("Starting Program 1: Annual Report Link Discovery")
    logger.info(f"Input file: {args.input}")
    logger.info(f"Output directory: {args.output}")
    logger.info(f"Years back: {args.years_back}")

    try:
        # Check if input file exists
        if not os.path.exists(args.input):
            logger.error(f"Input file not found: {args.input}")
            return

        # Load companies
        companies = load_companies_from_json(args.input)
        logger.info(f"Loaded {len(companies)} companies")

        if not companies:
            logger.error("No companies found in input.json")
            return

        # Initialize searcher with a year boundary
        searcher = AnnualReportSearcher(args.output, args.years_back)
        
        # Discover and rank annual report links
        logger.info("Discovering and ranking annual report PDF links...")
        all_selections = searcher.search_all_companies(companies)
        
        # Save results
        metadata_file = searcher.save_reports_metadata(all_selections)

        # Print summary
        total_best = sum(
            sum(len(year_data['best']) for year_data in selection.get('reports', []))
            for selection in all_selections.values()
        )
        total_secondary = sum(
            sum(len(year_data['secondary']) for year_data in selection.get('reports', []))
            for selection in all_selections.values()
        )
        logger.info(f"Discovery and ranking completed successfully!")
        logger.info(f"Selected {total_best} best and {total_secondary} secondary reports across {len(companies)} companies")
        logger.info(f"Metadata saved to: {metadata_file}")
        logger.info("Next step: Use the download program to fetch and process these PDFs")
        
        # Print company summaries
        for company in companies:
            selection = all_selections.get(company.ticker, {'years_covered': [], 'reports': []})
            years_covered = selection.get('years_covered', [])
            reports = selection.get('reports', [])
            
            # Count reports by year
            best_count = sum(len(year_data['best']) for year_data in reports)
            secondary_count = sum(len(year_data['secondary']) for year_data in reports)
            
            logger.info(f"{company.name} ({company.ticker}): {best_count} best, {secondary_count} secondary, years: {years_covered}")
    
    except Exception as e:
        logger.error(f"Fatal error in Program 1: {e}")
        raise


if __name__ == "__main__":
    main()
