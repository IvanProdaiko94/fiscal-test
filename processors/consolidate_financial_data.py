#!/usr/bin/env python3
"""
Program 4: Financial Data Consolidation and Verification

This program processes the CSV files created by Program 3 and performs:
1. Term consolidation (merging similar financial terms)
2. Data validation and verification
3. Quality assessment and reporting
4. Final data standardization
"""

import os
import json
import logging
import pandas as pd
from typing import Dict, List
from collections import defaultdict
import sys
import argparse
from pathlib import Path

# Add the parent directory to a Python path to import pkg modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pkg.financial_schemas import ComprehensiveFinancialSchemas

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('consolidation.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class FinancialTermConsolidator:
    """Consolidates similar financial terms and validates data quality."""
    
    def __init__(self):
        self.term_mappings = ComprehensiveFinancialSchemas.get_consolidation_mappings()
        self.consolidation_stats = defaultdict(int)
    
    def consolidate_terms(self, df: pd.DataFrame) -> pd.DataFrame:
        """Consolidate similar terms in a DataFrame."""
        logger.info(f"Consolidating terms in DataFrame with {len(df)} rows")
        
        # Create a mapping from all variations to standard terms
        term_to_standard = {}
        for standard_term, variations in self.term_mappings.items():
            for variation in variations:
                term_to_standard[variation.lower().strip()] = standard_term
        
        # Apply consolidation
        consolidated_rows = []
        consolidated_data = defaultdict(list)
        
        for _, row in df.iterrows():
            line_item = str(row.get('line_item', '')).strip()
            if not line_item:
                continue
                
            # Find the standard term
            standard_term = term_to_standard.get(line_item.lower(), line_item)
            
            # Group by standard term, year, and currency
            key = (standard_term, row.get('year'), row.get('currency'))
            
            if row.get('value') is not None and pd.notna(row.get('value')):
                consolidated_data[key].append({
                    'original_term': line_item,
                    'value': row.get('value'),
                    'confidence': row.get('confidence', 'Medium'),
                    'notes': row.get('notes', '')
                })
        
        # Create consolidated rows
        for (standard_term, year, currency), values in consolidated_data.items():
            if not values:
                continue
                
            # Calculate consolidated value (sum if multiple values)
            total_value = sum(v['value'] for v in values if v['value'] is not None)
            
            # Determine confidence level
            confidence_levels = [v['confidence'] for v in values]
            if 'High' in confidence_levels:
                final_confidence = 'High'
            elif 'Medium' in confidence_levels:
                final_confidence = 'Medium'
            else:
                final_confidence = 'Low'
            
            # Combine notes
            all_notes = [f"{v['original_term']}: {v['notes']}" for v in values if v['notes']]
            combined_notes = "; ".join(all_notes) if all_notes else ""
            
            consolidated_rows.append({
                'year': year,
                'ticker': df.iloc[0]['ticker'] if len(df) > 0 and 'ticker' in df.columns else '',
                'line_item': standard_term,
                'value': total_value,
                'currency': currency,
                'consolidated_from': len(values),
                'original_terms': [v['original_term'] for v in values],
                'confidence': final_confidence,
                'notes': combined_notes
            })
            
            self.consolidation_stats[f"{standard_term}"] += len(values) - 1
        
        result_df = pd.DataFrame(consolidated_rows)
        logger.info(f"Consolidated {len(df)} rows into {len(result_df)} rows")
        return result_df
    
    def validate_data_quality(self, df: pd.DataFrame) -> Dict[str, any]:
        """Validate data quality and return quality metrics."""
        logger.info("Validating data quality...")
        
        quality_report = {
            'total_rows': len(df),
            'missing_values': 0,
            'zero_values': 0,
            'duplicate_terms': 0,
            'quality_score': 0,
            'issues': []
        }
        
        # Check for missing values
        missing_values = df['value'].isna().sum()
        quality_report['missing_values'] = missing_values
        
        # Check for zero values
        zero_values = (df['value'] == 0).sum()
        quality_report['zero_values'] = zero_values
        
        # Check for duplicate terms within same year
        duplicates = df.groupby(['year', 'line_item']).size()
        duplicate_count = (duplicates > 1).sum()
        quality_report['duplicate_terms'] = duplicate_count
        
        # Calculate quality score (0-100)
        total_checks = len(df)
        issues = missing_values + duplicate_count
        quality_score = max(0, 100 - (issues / total_checks * 100)) if total_checks > 0 else 0
        quality_report['quality_score'] = round(quality_score, 2)
        
        # Add specific issues
        if missing_values > 0:
            quality_report['issues'].append(f"{missing_values} missing values found")
        if duplicate_count > 0:
            quality_report['issues'].append(f"{duplicate_count} duplicate terms found")
        
        logger.info(f"Quality score: {quality_score}/100")
        return quality_report


class FinancialDataProcessor:
    """Main processor for Program 4."""
    
    def __init__(self, input_dir: str = "output", output_dir: str = "consolidated_output"):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.consolidator = FinancialTermConsolidator()
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
    def find_csv_files_recursively(self, directory: str) -> List[str]:
        """Find all CSV files recursively in the given directory."""
        csv_files = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.csv'):
                    csv_files.append(os.path.join(root, file))
        return csv_files
    
    def get_relative_path(self, file_path: str, base_dir: str) -> str:
        """Get the relative path of a file from the base directory."""
        return os.path.relpath(file_path, base_dir)
    
    def create_output_directory_structure(self, relative_path: str) -> str:
        """Create the output directory structure matching the input structure."""
        output_path = os.path.join(self.output_dir, os.path.dirname(relative_path))
        os.makedirs(output_path, exist_ok=True)
        return output_path
    
    def process_all_csv_files(self):
        """Process all CSV files recursively in the input directory."""
        logger.info("Starting Program 4: Financial Data Consolidation and Verification")
        
        csv_files = self.find_csv_files_recursively(self.input_dir)
        logger.info(f"Found {len(csv_files)} CSV files to process recursively")
        
        all_quality_reports = []
        consolidation_summary = defaultdict(int)
        
        for csv_file_path in csv_files:
            relative_path = self.get_relative_path(csv_file_path, self.input_dir)
            logger.info(f"Processing {relative_path}...")
            
            try:
                # Read the CSV file
                df = pd.read_csv(csv_file_path)
                
                # Consolidate terms
                consolidated_df = self.consolidator.consolidate_terms(df)
                
                # Validate quality
                quality_report = self.consolidator.validate_data_quality(consolidated_df)
                quality_report['file'] = relative_path
                all_quality_reports.append(quality_report)
                
                # Create output directory structure
                output_dir_path = self.create_output_directory_structure(relative_path)
                
                # Save consolidated file with same name (no "consolidated_" prefix)
                filename = os.path.basename(relative_path)
                output_path = os.path.join(output_dir_path, filename)
                consolidated_df.to_csv(output_path, index=False)
                
                logger.info(f"Saved consolidated file: {relative_path}")
                logger.info(f"Quality score: {quality_report['quality_score']}/100")
                
                # Update consolidation summary
                consolidation_summary['files_processed'] += 1
                consolidation_summary['total_rows_before'] += len(df)
                consolidation_summary['total_rows_after'] += len(consolidated_df)
                consolidation_summary['terms_consolidated'] += sum(self.consolidator.consolidation_stats.values())
                
            except Exception as e:
                logger.error(f"Error processing {relative_path}: {e}")
                continue
        
        # Generate a summary report
        self._generate_summary_report(all_quality_reports, consolidation_summary)
        
        logger.info("Program 4 completed successfully!")
    
    def _generate_summary_report(self, quality_reports: List[Dict], consolidation_summary: Dict):
        """Generate a comprehensive summary report."""
        logger.info("Generating summary report...")
        
        summary = {
            'program': 'Program 4: Financial Data Consolidation and Verification',
            'processing_summary': consolidation_summary,
            'quality_reports': quality_reports,
            'consolidation_stats': dict(self.consolidator.consolidation_stats),
            'overall_quality_score': sum(r['quality_score'] for r in quality_reports) / len(quality_reports) if quality_reports else 0
        }
        
        logger.info(f"Overall summary: {summary}")


def main():
    """Main entry point for Program 4."""
    parser = argparse.ArgumentParser(
        description='Financial Data Consolidation and Verification',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python consolidate_financial_data.py output/
  python consolidate_financial_data.py output/ --output-dir consolidated_output/
  python consolidate_financial_data.py /path/to/csv/files/
        """
    )
    
    parser.add_argument(
        'input_folder',
        help='Input folder containing CSV files to process recursively'
    )
    
    parser.add_argument(
        '--output-dir',
        default='consolidated_output',
        help='Output directory for consolidated files (default: consolidated_output)'
    )
    
    args = parser.parse_args()
    
    # Validate input folder
    if not os.path.exists(args.input_folder):
        logger.error(f"Input folder does not exist: {args.input_folder}")
        sys.exit(1)
    
    if not os.path.isdir(args.input_folder):
        logger.error(f"Input path is not a directory: {args.input_folder}")
        sys.exit(1)
    
    # Create processor and run
    processor = FinancialDataProcessor(
        input_dir=args.input_folder,
        output_dir=args.output_dir
    )
    processor.process_all_csv_files()


if __name__ == "__main__":
    main()
