"""
Data models for financial statement extraction and processing.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from enum import Enum


class StatementType(Enum):
    """Types of financial statements."""
    INCOME_STATEMENT = "income_statement"
    BALANCE_SHEET = "balance_sheet"
    CASH_FLOW_STATEMENT = "cash_flow_statement"


@dataclass
class Company:
    """Company information model."""
    name: str
    ticker: str
    reports_link: str


@dataclass
class FinancialDataPoint:
    """Individual financial data point."""
    line_item: str
    value: Optional[float]
    year: int
    currency: str = "EUR"  # Default to EUR for European companies


@dataclass
class FinancialStatement:
    """Financial statement model."""
    statement_type: StatementType
    company_ticker: str
    year: int
    data_points: List[FinancialDataPoint]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for CSV export."""
        result = {"Line Item": [], "Value": [], "Currency": []}
        for point in self.data_points:
            result["Line Item"].append(point.line_item)
            result["Value"].append(point.value)
            result["Currency"].append(point.currency)
        return result


@dataclass
class ExtractedDocument:
    """Model for extracted document content."""
    url: str
    title: str
    content: str
    year: Optional[int] = None


@dataclass
class ProcessingResult:
    """Result of processing a company's financial data."""
    company: Company
    statements: Dict[int, Dict[StatementType, FinancialStatement]]
    errors: List[str]
    
    def get_statements_by_year(self, year: int) -> Dict[StatementType, FinancialStatement]:
        """Get all statements for a specific year."""
        return self.statements.get(year, {})
    
    def get_statement(self, year: int, statement_type: StatementType) -> Optional[FinancialStatement]:
        """Get a specific statement for a year."""
        year_data = self.statements.get(year, {})
        return year_data.get(statement_type)
