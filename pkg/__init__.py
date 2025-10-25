"""
Financial data extraction package.

This package contains modules for extracting financial statement data
from European companies' annual reports using OpenAI API.
"""

from .models import (
    Company, ProcessingResult, StatementType, FinancialStatement,
    FinancialDataPoint, ExtractedDocument
)
from .html_processor import HTMLPageProcessor
from .pdf_extractor import PDFExtractor
from .xlsx_extractor import XLSXExtractor
from .openai_extractor import OpenAIFinancialExtractor
from .csv_exporter import CSVExporter
from .reports_ranker import ReportsRanker
from .financial_agents import (
    FinancialAnalystAgent, FinancialReportsWriterAgent, CollaborativeFinancialExtractor
)
from .financial_schemas import ComprehensiveFinancialSchemas

__all__ = [
    'Company', 'ProcessingResult', 'StatementType', 'FinancialStatement',
    'FinancialDataPoint', 'ExtractedDocument', 'HTMLPageProcessor',
    'PDFExtractor', 'XLSXExtractor', 'OpenAIFinancialExtractor', 'CSVExporter', 'ReportsRanker',
    'FinancialAnalystAgent', 'FinancialReportsWriterAgent', 'CollaborativeFinancialExtractor',
    'ComprehensiveFinancialSchemas'
]
