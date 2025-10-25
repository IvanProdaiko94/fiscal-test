"""
CSV export functionality for financial statements with comprehensive unit measurements.
"""

import os
import pandas as pd
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from .models import FinancialStatement, StatementType, ProcessingResult, FinancialDataPoint
from .financial_schemas import ComprehensiveFinancialSchemas

logger = logging.getLogger(__name__)


class UnitConverter:
    """Handles unit conversion and standardization for financial values."""
    
    # Unit multipliers (converting to base units)
    UNIT_MULTIPLIERS = {
        'thousands': 1_000,
        'millions': 1_000_000,
        'billions': 1_000_000_000,
        'trillions': 1_000_000_000_000,
        'k': 1_000,
        'm': 1_000_000,
        'b': 1_000_000_000,
        't': 1_000_000_000_000,
        'EUR': 1,
        'USD': 1,
        'GBP': 1,
        'CHF': 1,
        'SEK': 1,
        'NOK': 1,
        'DKK': 1
    }
    
    @classmethod
    def normalize_value(cls, value: Optional[float], unit: str) -> tuple[Optional[float], str]:
        """
        Normalize a financial value to a standard unit.
        Returns (normalized_value, normalized_unit)
        """
        if value is None:
            return None, unit
        
        # Extract unit information
        unit_lower = unit.lower().strip()
        
        # Find the appropriate multiplier
        multiplier = 1
        normalized_unit = unit
        
        for unit_key, mult in cls.UNIT_MULTIPLIERS.items():
            if unit_key in unit_lower:
                multiplier = mult
                # Keep currency but normalize the magnitude
                if unit_key in ['EUR', 'USD', 'GBP', 'CHF', 'SEK', 'NOK', 'DKK']:
                    normalized_unit = unit_key
                else:
                    # Extract currency from original unit
                    currency = cls._extract_currency(unit)
                    normalized_unit = currency if currency else 'EUR'
                break
        
        normalized_value = value * multiplier
        return normalized_value, normalized_unit
    
    @classmethod
    def _extract_currency(cls, unit: str) -> Optional[str]:
        """Extract currency from a unit string."""
        currencies = ['EUR', 'USD', 'GBP', 'CHF', 'SEK', 'NOK', 'DKK']
        unit_upper = unit.upper()
        
        for currency in currencies:
            if currency in unit_upper:
                return currency
        
        return None
    
    @classmethod
    def format_value_with_unit(cls, value: Optional[float], unit: str, display_unit: str = 'millions') -> str:
        """
        Format a value with appropriate unit for display.
        """
        if value is None:
            return "N/A"
        
        normalized_value, currency = cls.normalize_value(value, unit)
        
        if normalized_value is None:
            return "N/A"
        
        # Convert to display unit
        display_multiplier = cls.UNIT_MULTIPLIERS.get(display_unit, 1_000_000)
        display_value = normalized_value / display_multiplier
        
        return f"{display_value:,.2f} {currency} {display_unit}"


class EnhancedCSVExporter:
    """Enhanced CSV exporter with comprehensive unit measurements and data processing."""
    
    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.unit_converter = UnitConverter()
    
    def export_company_data(self, result: ProcessingResult) -> List[str]:
        """Export all financial statements for a company to CSV files with comprehensive data."""
        exported_files = []
        
        # Export individual statements
        for year, year_statements in result.statements.items():
            for statement_type, statement in year_statements.items():
                filename = self._generate_filename(
                    result.company.ticker, 
                    year, 
                    statement_type
                )
                
                filepath = os.path.join(self.output_dir, filename)
                
                try:
                    self._export_statement_to_csv(statement, filepath)
                    exported_files.append(filepath)
                    logger.info(f"Exported {filename}")
                except Exception as e:
                    logger.error(f"Error exporting {filename}: {e}")
        
        # Export consolidated data
        consolidated_file = self._export_consolidated_data(result)
        if consolidated_file:
            exported_files.append(consolidated_file)
        
        return exported_files
    
    def export_agent_processed_data(self, agent_data: Dict[str, Any], company_ticker: str, year: int) -> str:
        """
        Export data processed by financial agents with comprehensive unit information.
        
        Args:
            agent_data: Raw data from financial agents
            company_ticker: Company ticker symbol
            year: Financial year
            
        Returns:
            Path to exported CSV file
        """
        filename = f"{company_ticker}_{year}_agent_processed_data.csv"
        filepath = os.path.join(self.output_dir, filename)
        
        try:
            # Process agent data into structured format
            processed_rows = self._process_agent_data(agent_data, company_ticker, year)
            
            # Create DataFrame
            df = pd.DataFrame(processed_rows)
            
            # Add metadata columns
            df['export_timestamp'] = datetime.now().isoformat()
            df['data_source'] = 'financial_agents'
            df['processing_version'] = '1.0'
            
            # Export to CSV
            df.to_csv(filepath, index=False)
            logger.info(f"Exported agent processed data to {filename}")
            
            return filepath
            
        except Exception as e:
            logger.error(f"Error exporting agent processed data: {e}")
            raise
    
    def _process_agent_data(self, agent_data: Dict[str, Any], company_ticker: str, year: int) -> List[Dict[str, Any]]:
        """Process raw agent data into structured rows for CSV export."""
        rows = []
        
        # Extract basic information
        statement_type = agent_data.get('statement_type', 'unknown')
        currency = agent_data.get('currency', 'EUR')
        reporting_standard = agent_data.get('reporting_standard', 'Unknown')
        quality_score = agent_data.get('quality_score', 0)
        review_notes = agent_data.get('review_notes', '')
        
        # Process line items
        line_items = agent_data.get('line_items', [])
        
        for item in line_items:
            line_item = item.get('line_item', '')
            value = item.get('value')
            unit = item.get('unit', currency)
            category = item.get('category', 'other')
            item_quality_score = item.get('quality_score', 0)
            notes = item.get('notes', '')
            
            # Normalize value and unit
            normalized_value, normalized_unit = self.unit_converter.normalize_value(value, unit)
            
            # Create row
            row = {
                'company_ticker': company_ticker,
                'year': year,
                'statement_type': statement_type,
                'line_item': line_item,
                'raw_value': value,
                'raw_unit': unit,
                'normalized_value': normalized_value,
                'normalized_unit': normalized_unit,
                'value_in_millions': self.unit_converter.format_value_with_unit(value, unit, 'millions'),
                'value_in_billions': self.unit_converter.format_value_with_unit(value, unit, 'billions'),
                'category': category,
                'quality_score': item_quality_score,
                'notes': notes,
                'reporting_standard': reporting_standard,
                'overall_quality_score': quality_score,
                'review_notes': review_notes
            }
            
            rows.append(row)
        
        return rows
    
    def _generate_filename(self, ticker: str, year: int, statement_type: StatementType) -> str:
        """Generate filename according to the specified format."""
        return f"{ticker}_{year}_{statement_type.value}.csv"
    
    def _export_statement_to_csv(self, statement: FinancialStatement, filepath: str):
        """Export a single financial statement to CSV with enhanced data."""
        rows = []
        
        for data_point in statement.data_points:
            # Normalize value and unit
            normalized_value, normalized_unit = self.unit_converter.normalize_value(
                data_point.value, 
                data_point.currency
            )
            
            row = {
                'company_ticker': statement.company_ticker,
                'year': statement.year,
                'statement_type': statement.statement_type.value,
                'line_item': data_point.line_item,
                'raw_value': data_point.value,
                'raw_currency': data_point.currency,
                'normalized_value': normalized_value,
                'normalized_unit': normalized_unit,
                'value_in_millions': self.unit_converter.format_value_with_unit(
                    data_point.value, 
                    data_point.currency, 
                    'millions'
                ),
                'value_in_billions': self.unit_converter.format_value_with_unit(
                    data_point.value, 
                    data_point.currency, 
                    'billions'
                ),
                'export_timestamp': datetime.now().isoformat()
            }
            
            rows.append(row)
        
        # Create DataFrame and export
        df = pd.DataFrame(rows)
        df.to_csv(filepath, index=False)
    
    def _export_consolidated_data(self, result: ProcessingResult) -> Optional[str]:
        """Export consolidated data across all years and statement types."""
        filename = f"{result.company.ticker}_consolidated_financial_data.csv"
        filepath = os.path.join(self.output_dir, filename)
        
        try:
            all_rows = []
            
            for year, year_statements in result.statements.items():
                for statement_type, statement in year_statements.items():
                    for data_point in statement.data_points:
                        normalized_value, normalized_unit = self.unit_converter.normalize_value(
                            data_point.value, 
                            data_point.currency
                        )
                        
                        row = {
                            'company_ticker': result.company.ticker,
                            'company_name': result.company.name,
                            'year': year,
                            'statement_type': statement_type.value,
                            'line_item': data_point.line_item,
                            'raw_value': data_point.value,
                            'raw_currency': data_point.currency,
                            'normalized_value': normalized_value,
                            'normalized_unit': normalized_unit,
                            'value_in_millions': self.unit_converter.format_value_with_unit(
                                data_point.value, 
                                data_point.currency, 
                                'millions'
                            ),
                            'value_in_billions': self.unit_converter.format_value_with_unit(
                                data_point.value, 
                                data_point.currency, 
                                'billions'
                            ),
                            'export_timestamp': datetime.now().isoformat()
                        }
                        
                        all_rows.append(row)
            
            if all_rows:
                df = pd.DataFrame(all_rows)
                df.to_csv(filepath, index=False)
                logger.info(f"Exported consolidated data to {filename}")
                return filepath
            
        except Exception as e:
            logger.error(f"Error exporting consolidated data: {e}")
        
        return None


# Backward compatibility
CSVExporter = EnhancedCSVExporter
