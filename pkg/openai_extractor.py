"""
OpenAI API integration for financial data extraction.
"""

import json
import logging
import time
from typing import List, Dict, Optional, Any
from openai import OpenAI
from .models import FinancialStatement, FinancialDataPoint, StatementType, ExtractedDocument


logger = logging.getLogger(__name__)


class OpenAIFinancialExtractor:
    """Handles financial data extraction using OpenAI API."""
    
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
    
    def extract_financial_data(self, document: ExtractedDocument, statement_type: StatementType) -> Optional[FinancialStatement]:
        """Extract financial data from a document using OpenAI with JSON schema and chunking."""
        try:
            # Split document into manageable chunks
            chunks = self._split_content_into_chunks(document.content, max_chunk_size=4000)
            logger.info(f"Processing {len(chunks)} chunks for {statement_type.value}")
            
            all_extracted_data = []
            
            for i, chunk in enumerate(chunks):
                logger.info(f"Processing chunk {i+1}/{len(chunks)} for {statement_type.value}")
                
                # Create a focused prompt for this chunk
                prompt = self._create_chunk_extraction_prompt(document, statement_type, chunk, i+1, len(chunks))
                
                # Define the JSON schema for the response
                schema = self._get_financial_data_schema(statement_type)
                
                try:
                    response = self.client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {
                                "role": "system",
                                "content": "You are a financial data extraction expert. Extract financial statement data and return it in the specified JSON format."
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        temperature=0.1,
                        max_tokens=1500,  # Reduced for chunks
                        timeout=30,  # Shorter timeout for chunks
                        response_format={
                            "type": "json_schema",
                            "json_schema": {
                                "name": f"financial_{statement_type.value}_chunk_{i+1}",
                                "schema": schema,
                                "strict": True
                            }
                        }
                    )
                    
                    # Parse the structured JSON response
                    content = response.choices[0].message.content
                    
                    try:
                        chunk_data = json.loads(content)
                        
                        # Validate the response against the schema
                        if self._validate_schema_response(chunk_data, statement_type):
                            all_extracted_data.append(chunk_data)
                            logger.info(f"Successfully processed chunk {i+1}")
                        else:
                            logger.warning(f"Chunk {i+1} failed schema validation")
                            
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse JSON response for chunk {i+1}: {e}")
                        continue
                        
                except Exception as e:
                    logger.error(f"Error processing chunk {i+1}: {e}")
                    continue
                
                # Small delay between chunks to prevent rate limiting
                if i < len(chunks) - 1:  # Don't delay after the last chunk
                    time.sleep(0.5)
            
            if not all_extracted_data:
                logger.error("No valid data extracted from any chunks")
                return None
            
            # Merge all extracted data from chunks
            merged_data = self._merge_chunk_data(all_extracted_data, document, statement_type)
            
            # Convert to FinancialStatement object
            return self._parse_financial_data(merged_data, document, statement_type)
            
        except Exception as e:
            logger.error(f"Error extracting financial data: {e}")
            return None
    
    def _create_extraction_prompt(self, document: ExtractedDocument, statement_type: StatementType) -> str:
        """Create a focused prompt for financial data extraction."""
        
        statement_prompts = {
            StatementType.INCOME_STATEMENT: """
            Extract Income Statement data from this annual report.
            
            Focus on consolidated financial statements. Extract these key line items:
            REVENUE: Revenue/Sales/Turnover/Net Sales
            COSTS: Cost of Sales/COGS/Cost of Revenue  
            PROFITABILITY: Gross Profit, Operating Expenses, Operating Income/EBIT
            FINANCIAL COSTS: Interest Expense, Interest Income, Net Interest
            TAXES: Income Tax Expense, Deferred Tax
            NET RESULTS: Net Income/Net Profit, Earnings Per Share
            
            Extract the most recent year's data from tables and financial statements.
            """,
            StatementType.BALANCE_SHEET: """
            Extract Balance Sheet data from this annual report.
            
            Focus on consolidated balance sheet. Extract these key line items:
            CURRENT ASSETS: Cash and Cash Equivalents, Accounts Receivable, Inventory, Other Current Assets
            NON-CURRENT ASSETS: Property Plant Equipment, Intangible Assets, Goodwill, Long-term Investments
            CURRENT LIABILITIES: Accounts Payable, Short-term Debt, Accrued Expenses
            NON-CURRENT LIABILITIES: Long-term Debt, Deferred Tax Liabilities, Pension Obligations
            EQUITY: Share Capital, Retained Earnings, Other Reserves, Total Equity
            
            Extract the most recent year's data from tables and financial statements.
            """,
            StatementType.CASH_FLOW_STATEMENT: """
            Extract Cash Flow Statement data from this annual report.
            
            Focus on consolidated cash flow statement. Extract these key line items:
            OPERATING: Net Income, Depreciation/Amortization, Changes in Working Capital, Operating Cash Flow
            INVESTING: Capital Expenditures, Purchase/Sale of Assets, Acquisitions, Investing Cash Flow
            FINANCING: Debt Issuance/Repayment, Dividends Paid, Share Repurchases, Financing Cash Flow
            NET CASH: Net Increase/Decrease in Cash, Cash at Beginning/End of Period
            
            Extract the most recent year's data from tables and financial statements.
            """
        }
        
        base_prompt = f"""
        {statement_prompts[statement_type]}
        
        Document: {document.title} ({document.year})
        
        Requirements:
        1. Extract values exactly as reported in the document
        2. Convert all values to EUR if possible
        3. Use null for missing values
        4. Extract the most recent year's data
        5. Focus on consolidated statements only
        
        Content to analyze:
        {self._get_relevant_content(document, statement_type)}
        
        Return the extracted data in the structured JSON format defined by the schema.
        """
        
        return base_prompt
    
    def _split_content_into_chunks(self, content: str, max_chunk_size: int = 4000) -> List[str]:
        """Split content into manageable chunks with overlap."""
        if len(content) <= max_chunk_size:
            return [content]
        
        chunks = []
        overlap = 500  # Overlap between chunks to maintain context
        
        # Limit total chunks to prevent memory issues
        max_chunks = 10
        step_size = max_chunk_size - overlap
        
        for i in range(0, min(len(content), max_chunks * step_size), step_size):
            chunk = content[i:i + max_chunk_size]
            chunks.append(chunk)
            
            # Break if we've reached the end or max chunks
            if i + max_chunk_size >= len(content) or len(chunks) >= max_chunks:
                break
        
        logger.info(f"Split content into {len(chunks)} chunks (max {max_chunk_size} chars each)")
        return chunks
    
    def _create_chunk_extraction_prompt(self, document: ExtractedDocument, statement_type: StatementType, chunk: str, chunk_num: int, total_chunks: int) -> str:
        """Create a focused prompt for a specific chunk."""
        
        statement_prompts = {
            StatementType.INCOME_STATEMENT: """
            Extract Income Statement data from this chunk of an annual report.
            
            Focus on consolidated financial statements. Extract these key line items:
            REVENUE: Revenue/Sales/Turnover/Net Sales
            COSTS: Cost of Sales/COGS/Cost of Revenue  
            PROFITABILITY: Gross Profit, Operating Expenses, Operating Income/EBIT
            FINANCIAL COSTS: Interest Expense, Interest Income, Net Interest
            TAXES: Income Tax Expense, Deferred Tax
            NET RESULTS: Net Income/Net Profit, Earnings Per Share
            
            Extract the most recent year's data from tables and financial statements.
            """,
            StatementType.BALANCE_SHEET: """
            Extract Balance Sheet data from this chunk of an annual report.
            
            Focus on consolidated balance sheet. Extract these key line items:
            CURRENT ASSETS: Cash and Cash Equivalents, Accounts Receivable, Inventory, Other Current Assets
            NON-CURRENT ASSETS: Property Plant Equipment, Intangible Assets, Goodwill, Long-term Investments
            CURRENT LIABILITIES: Accounts Payable, Short-term Debt, Accrued Expenses
            NON-CURRENT LIABILITIES: Long-term Debt, Deferred Tax Liabilities, Pension Obligations
            EQUITY: Share Capital, Retained Earnings, Other Reserves, Total Equity
            
            Extract the most recent year's data from tables and financial statements.
            """,
            StatementType.CASH_FLOW_STATEMENT: """
            Extract Cash Flow Statement data from this chunk of an annual report.
            
            Focus on consolidated cash flow statement. Extract these key line items:
            OPERATING: Net Income, Depreciation/Amortization, Changes in Working Capital, Operating Cash Flow
            INVESTING: Capital Expenditures, Purchase/Sale of Assets, Acquisitions, Investing Cash Flow
            FINANCING: Debt Issuance/Repayment, Dividends Paid, Share Repurchases, Financing Cash Flow
            NET CASH: Net Increase/Decrease in Cash, Cash at Beginning/End of Period
            
            Extract the most recent year's data from tables and financial statements.
            """
        }
        
        base_prompt = f"""
        {statement_prompts[statement_type]}
        
        Document: {document.title} ({document.year})
        Chunk: {chunk_num}/{total_chunks}
        
        Requirements:
        1. Extract values exactly as reported in this chunk
        2. Convert all values to EUR if possible
        3. Use null for missing values
        4. Extract the most recent year's data
        5. Focus on consolidated statements only
        
        Content to analyze:
        {chunk}
        
        Return the extracted data in the structured JSON format defined by the schema.
        """
        
        return base_prompt
    
    def _merge_chunk_data(self, chunk_data_list: List[Dict[str, Any]], document: ExtractedDocument, statement_type: StatementType) -> Dict[str, Any]:
        """Merge data from multiple chunks into a single consolidated response."""
        if not chunk_data_list:
            return {}
        
        # Use the first chunk as the base structure
        merged_data = chunk_data_list[0].copy()
        
        # Merge line items from all chunks
        all_line_items = []
        seen_line_items = set()
        
        for chunk_data in chunk_data_list:
            line_items = chunk_data.get("line_items", [])
            for item in line_items:
                line_item_name = item.get("line_item", "").strip().lower()
                
                # Avoid duplicates by checking line item names
                if line_item_name and line_item_name not in seen_line_items:
                    all_line_items.append(item)
                    seen_line_items.add(line_item_name)
                elif line_item_name in seen_line_items:
                    # If duplicate, keep the one with a value
                    for existing_item in all_line_items:
                        if existing_item.get("line_item", "").strip().lower() == line_item_name:
                            if existing_item.get("value") is None and item.get("value") is not None:
                                # Replace with the one that has a value
                                all_line_items.remove(existing_item)
                                all_line_items.append(item)
                            break
        
        merged_data["line_items"] = all_line_items
        
        logger.info(f"Merged {len(chunk_data_list)} chunks into {len(all_line_items)} unique line items")
        return merged_data
    
    def _get_financial_data_schema(self, statement_type: StatementType) -> Dict[str, Any]:
        """Get the JSON schema for financial data extraction based on statement type."""
        
        base_schema = {
            "type": "object",
            "properties": {
                "statement_type": {
                    "type": "string",
                    "enum": [statement_type.value],
                    "description": f"The type of financial statement being extracted: {statement_type.value}"
                },
                "year": {
                    "type": "integer",
                    "minimum": 2000,
                    "maximum": 2030,
                    "description": "The fiscal year of the financial statement"
                },
                "currency": {
                    "type": "string",
                    "enum": ["EUR", "USD", "GBP", "CHF", "SEK", "NOK", "DKK"],
                    "description": "The primary currency used in the financial statement"
                },
                "reporting_standard": {
                    "type": "string",
                    "enum": ["US GAAP", "IFRS", "Dutch GAAP", "Other"],
                    "description": "The accounting standard used (if identifiable)"
                },
                "line_items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "line_item": {
                                "type": "string",
                                "minLength": 1,
                                "maxLength": 200,
                                "description": "The exact name of the financial line item as it appears in the document"
                            },
                            "value": {
                                "type": ["number", "null"],
                                "description": "The financial value in the specified currency and unit"
                            },
                            "unit": {
                                "type": "string",
                                "enum": ["EUR", "USD", "GBP", "CHF", "SEK", "NOK", "DKK", "thousands", "millions", "billions"],
                                "description": "The unit of measurement for the value"
                            },
                            "category": {
                                "type": "string",
                                "enum": ["Revenue", "Costs", "Assets", "Liabilities", "Equity", "Operating", "Investing", "Financing", "Other"],
                                "description": "The category of the line item for better organization"
                            }
                        },
                        "required": ["line_item", "value", "unit", "category"],
                        "additionalProperties": False
                    },
                    "minItems": 5,
                    "maxItems": 150,
                    "description": "Array of financial line items with their values"
                }
            },
            "required": ["statement_type", "year", "currency", "reporting_standard", "line_items"],
            "additionalProperties": False
        }
        
        # Add statement-specific line item requirements
        if statement_type == StatementType.INCOME_STATEMENT:
            base_schema["properties"]["line_items"]["items"]["properties"]["line_item"]["description"] = (
                "Income statement line items such as Revenue, Cost of Sales, Gross Profit, "
                "Operating Expenses, Operating Income, Interest Expense, Net Income, etc."
            )
        elif statement_type == StatementType.BALANCE_SHEET:
            base_schema["properties"]["line_items"]["items"]["properties"]["line_item"]["description"] = (
                "Balance sheet line items such as Assets, Current Assets, Non-Current Assets, "
                "Liabilities, Current Liabilities, Non-Current Liabilities, Equity, Cash, etc."
            )
        elif statement_type == StatementType.CASH_FLOW_STATEMENT:
            base_schema["properties"]["line_items"]["items"]["properties"]["line_item"]["description"] = (
                "Cash flow statement line items such as Operating Cash Flow, Investing Cash Flow, "
                "Financing Cash Flow, Net Cash Flow, Cash at Beginning/End of Period, etc."
            )
        
        return base_schema
    
    def _validate_schema_response(self, data: Dict[str, Any], statement_type: StatementType) -> bool:
        """Validate that the response matches the expected schema."""
        try:
            # Check required fields
            if not isinstance(data, dict):
                logger.error("Response is not a dictionary")
                return False
            
            required_fields = ["statement_type", "year", "currency", "reporting_standard", "line_items"]
            for field in required_fields:
                if field not in data:
                    logger.error(f"Missing required field: {field}")
                    return False
            
            # Validate statement type
            if data.get("statement_type") != statement_type.value:
                logger.error(f"Statement type mismatch: expected {statement_type.value}, got {data.get('statement_type')}")
                return False
            
            # Validate year
            year = data.get("year")
            if not isinstance(year, int) or year < 2000 or year > 2030:
                logger.error(f"Invalid year: {year}")
                return False
            
            # Validate currency
            valid_currencies = ["EUR", "USD", "GBP", "CHF", "SEK", "NOK", "DKK"]
            if data.get("currency") not in valid_currencies:
                logger.error(f"Invalid currency: {data.get('currency')}")
                return False
            
            # Validate reporting standard (required)
            reporting_standard = data.get("reporting_standard")
            if not isinstance(reporting_standard, str) or len(reporting_standard.strip()) == 0:
                logger.error(f"Invalid reporting_standard: must be a non-empty string")
                return False
            
            valid_standards = ["US GAAP", "IFRS", "Dutch GAAP", "Other"]
            if reporting_standard not in valid_standards:
                logger.warning(f"Unknown reporting standard: {reporting_standard}")
            
            # Validate line items
            line_items = data.get("line_items")
            if not isinstance(line_items, list):
                logger.error("Invalid line_items: must be a list")
                return False
            
            if len(line_items) < 5:
                logger.warning(f"Only {len(line_items)} line items found, expected at least 5")
            elif len(line_items) > 150:
                logger.warning(f"Too many line items: {len(line_items)}, expected maximum 150")
            
            for i, item in enumerate(line_items):
                if not isinstance(item, dict):
                    logger.error(f"Invalid line item {i}: must be a dictionary")
                    return False
                
                # Check required fields
                required_item_fields = ["line_item", "value", "unit", "category"]
                for field in required_item_fields:
                    if field not in item:
                        logger.error(f"Invalid line item {i}: missing required field '{field}'")
                        return False
                
                # Validate line_item
                line_item = item.get("line_item")
                if not isinstance(line_item, str) or len(line_item.strip()) == 0:
                    logger.error(f"Invalid line item {i}: line_item must be a non-empty string")
                    return False
                
                # Validate value (can be number or null)
                value = item.get("value")
                if value is not None and not isinstance(value, (int, float)):
                    logger.error(f"Invalid line item {i}: value must be a number or null")
                    return False
                
                # Validate unit
                unit = item.get("unit")
                valid_units = ["EUR", "USD", "GBP", "CHF", "SEK", "NOK", "DKK", "thousands", "millions", "billions"]
                if unit not in valid_units:
                    logger.error(f"Invalid line item {i}: unit must be one of {valid_units}")
                    return False
                
                # Validate category (required)
                category = item.get("category")
                if not isinstance(category, str) or len(category.strip()) == 0:
                    logger.error(f"Invalid line item {i}: category must be a non-empty string")
                    return False
                
                valid_categories = ["Revenue", "Costs", "Assets", "Liabilities", "Equity", "Operating", "Investing", "Financing", "Other"]
                if category not in valid_categories:
                    logger.warning(f"Invalid category for line item {i}: {category}")
            
            logger.info(f"Schema validation passed for {statement_type.value} with {len(line_items)} line items")
            return True
            
        except Exception as e:
            logger.error(f"Schema validation error: {e}")
            return False
    
    def _get_relevant_content(self, document: ExtractedDocument, statement_type: StatementType) -> str:
        """Extract relevant content for the specific statement type."""
        content = document.content
        
        # If content is too long, try to find the relevant section
        if len(content) > 8000:  # Reduced threshold
            # Look for statement-specific keywords to find relevant sections
            statement_keywords = {
                StatementType.INCOME_STATEMENT: [
                    'consolidated income statement', 'consolidated statement of operations',
                    'consolidated profit and loss', 'income statement', 'profit and loss',
                    'statement of operations', 'statement of earnings', 'revenue', 'sales',
                    'operating income', 'net income', 'ebit', 'earnings before interest'
                ],
                StatementType.BALANCE_SHEET: [
                    'consolidated balance sheet', 'consolidated statement of financial position',
                    'balance sheet', 'statement of financial position', 'assets', 'liabilities',
                    'equity', 'shareholders equity', 'cash and cash equivalents', 'total assets',
                    'total liabilities', 'total equity'
                ],
                StatementType.CASH_FLOW_STATEMENT: [
                    'consolidated cash flow statement', 'consolidated statement of cash flows',
                    'cash flow statement', 'statement of cash flows', 'operating cash flow',
                    'investing cash flow', 'financing cash flow', 'net cash flow',
                    'cash from operations', 'cash from investing', 'cash from financing'
                ]
            }
            
            keywords = statement_keywords.get(statement_type, [])
            content_lower = content.lower()
            
            # Find the best section containing relevant keywords
            best_start = 0
            max_keyword_count = 0
            best_section = ""
            
            # Look for financial statements section first
            financial_section_markers = [
                'financial statements', 'consolidated financial statements',
                'notes to the financial statements', 'audited financial statements'
            ]
            
            financial_start = -1
            for marker in financial_section_markers:
                pos = content_lower.find(marker)
                if pos != -1:
                    financial_start = pos
                    break
            
            if financial_start != -1:
                # Extract from financial statements section (reduced size)
                financial_section = content[financial_start:financial_start + 8000]  # Reduced from 15000
                financial_section_lower = financial_section.lower()
                
                # Count keywords in financial section
                keyword_count = sum(1 for keyword in keywords if keyword in financial_section_lower)
                if keyword_count > 0:
                    best_section = financial_section
                    max_keyword_count = keyword_count
            
            # If no financial section found or it's not good enough, search entire document
            if not best_section or max_keyword_count < 2:  # Reduced threshold
                # Split content into chunks and find the most relevant one
                chunk_size = 4000  # Reduced from 6000
                for i in range(0, len(content), chunk_size):
                    chunk = content[i:i + chunk_size * 2]  # Overlap chunks
                    chunk_lower = chunk.lower()
                    
                    keyword_count = sum(1 for keyword in keywords if keyword in chunk_lower)
                    if keyword_count > max_keyword_count:
                        max_keyword_count = keyword_count
                        best_start = i
                        best_section = chunk
            
            # Use the best section found
            if best_section:
                content = best_section
            else:
                # Fallback: use the middle section of the document (reduced size)
                start = len(content) // 3
                content = content[start:start + 6000]  # Reduced from 10000
        
        return content[:6000]  # Final limit reduced from 10000
    
    def _parse_financial_data(self, data: Dict[str, Any], document: ExtractedDocument, statement_type: StatementType) -> FinancialStatement:
        """Parse the extracted financial data into a FinancialStatement object."""
        
        data_points = []
        currency = data.get("currency", "EUR")
        year = data.get("year", document.year or 2024)
        reporting_standard = data.get("reporting_standard", "Other")
        
        # Validate reporting standard
        if not reporting_standard or reporting_standard not in ["US GAAP", "IFRS", "Dutch GAAP", "Other"]:
            reporting_standard = "Other"
        
        # Log extraction details
        logger.info(f"Parsing {statement_type.value} for year {year} in {currency} ({reporting_standard})")
        
        # Validate the schema structure
        if not isinstance(data.get("line_items"), list):
            logger.error("Invalid schema: line_items is not a list")
            return None
        
        line_items = data.get("line_items", [])
        logger.info(f"Processing {len(line_items)} line items")
        
        for i, item in enumerate(line_items):
            # Validate required fields
            if not isinstance(item, dict):
                logger.warning(f"Skipping invalid line item {i}: {item}")
                continue
                
            line_item = item.get("line_item", "").strip()
            value = item.get("value")
            unit = item.get("unit", currency)
            category = item.get("category", "Other")
            
            # Validate category
            if not category or category not in ["Revenue", "Costs", "Assets", "Liabilities", "Equity", "Operating", "Investing", "Financing", "Other"]:
                category = "Other"
            
            # Skip empty line items
            if not line_item:
                logger.warning(f"Skipping empty line item {i}")
                continue
            
            # Convert value based on unit if needed
            converted_value = self._convert_value_by_unit(value, unit, currency)
            
            # Log significant line items
            if converted_value is not None and abs(converted_value) > 1000000:  # Values over 1M
                logger.debug(f"Large value found: {line_item} = {converted_value:,.0f} {currency}")
            
            data_point = FinancialDataPoint(
                line_item=line_item,
                value=converted_value,
                year=year,
                currency=currency
            )
            data_points.append(data_point)
        
        if not data_points:
            logger.error("No valid data points extracted")
            return None
        
        # Log summary
        non_null_values = sum(1 for dp in data_points if dp.value is not None)
        logger.info(f"Extracted {len(data_points)} line items ({non_null_values} with values)")
        
        return FinancialStatement(
            statement_type=statement_type,
            company_ticker="",  # Will be set by the caller
            year=year,
            data_points=data_points
        )
    
    def _convert_value_by_unit(self, value: Optional[float], unit: str, target_currency: str) -> Optional[float]:
        """Convert value based on unit to target currency."""
        if value is None:
            return None
        
        # Handle unit conversions (thousands, millions, billions)
        if unit == "thousands":
            return value * 1000
        elif unit == "millions":
            return value * 1000000
        elif unit == "billions":
            return value * 1000000000
        else:
            # Assume the value is already in the target currency
            return value
    
    def consolidate_statements(self, statements: List[FinancialStatement]) -> Dict[int, Dict[StatementType, FinancialStatement]]:
        """Consolidate multiple statements by year and type."""
        consolidated = {}
        
        for statement in statements:
            year = statement.year
            if year not in consolidated:
                consolidated[year] = {}
            
            consolidated[year][statement.statement_type] = statement
        
        return consolidated
    
    def clean_and_standardize(self, statements: Dict[int, Dict[StatementType, FinancialStatement]]) -> Dict[int, Dict[StatementType, FinancialStatement]]:
        """Clean and standardize financial statements."""
        cleaned = {}
        
        for year, year_statements in statements.items():
            cleaned[year] = {}
            
            for statement_type, statement in year_statements.items():
                # Remove duplicate line items and standardize names
                unique_items = {}
                for data_point in statement.data_points:
                    # Standardize line item names using statement-specific terminology
                    standardized_name = self._standardize_line_item_name(data_point.line_item, statement_type)
                    
                    # Create a new data point with standardized name
                    standardized_data_point = FinancialDataPoint(
                        line_item=standardized_name,
                        value=data_point.value,
                        year=data_point.year,
                        currency=data_point.currency
                    )
                    
                    if standardized_name not in unique_items:
                        unique_items[standardized_name] = standardized_data_point
                    else:
                        # If duplicate, keep the one with a value
                        if standardized_data_point.value is not None and unique_items[standardized_name].value is None:
                            unique_items[standardized_name] = standardized_data_point
                
                # Create cleaned statement
                cleaned_statement = FinancialStatement(
                    statement_type=statement_type,
                    company_ticker=statement.company_ticker,
                    year=year,
                    data_points=list(unique_items.values())
                )
                
                cleaned[year][statement_type] = cleaned_statement
        
        return cleaned
    
    def _standardize_line_item_name(self, name: str, statement_type: StatementType = None) -> str:
        """Standardize line item names using comprehensive financial terminology."""
        name_lower = name.lower().strip()
        
        # Get statement-specific standardizations
        if statement_type:
            standardizations = self._get_statement_specific_standardizations(statement_type)
        else:
            # Fallback to general standardizations
            standardizations = self._get_general_standardizations()
        
        # Try the exact match first
        if name_lower in standardizations:
            return standardizations[name_lower]
        
        # Try partial matches for compound terms
        for key, value in standardizations.items():
            if key in name_lower or name_lower in key:
                return value
        
        # Try fuzzy matching for common variations
        return self._fuzzy_match_line_item(name_lower, standardizations)
    
    def _get_statement_specific_standardizations(self, statement_type: StatementType) -> Dict[str, str]:
        """Get standardizations specific to each statement type."""
        
        if statement_type == StatementType.INCOME_STATEMENT:
            return {
                # Revenue variations
                "revenue": "Revenue",
                "sales": "Revenue",
                "turnover": "Revenue",
                "net sales": "Revenue",
                "total revenue": "Revenue",
                "gross revenue": "Revenue",
                "operating revenue": "Revenue",
                "service revenue": "Revenue",
                "product revenue": "Revenue",
                "other revenue": "Other Revenue",
                
                # Cost of Sales variations
                "cost of sales": "Cost of Sales",
                "cost of goods sold": "Cost of Sales",
                "cogs": "Cost of Sales",
                "cost of revenue": "Cost of Sales",
                "direct costs": "Cost of Sales",
                "cost of services": "Cost of Sales",
                
                # Gross Profit variations
                "gross profit": "Gross Profit",
                "gross margin": "Gross Profit",
                "gross income": "Gross Profit",
                
                # Operating Expenses variations
                "operating expenses": "Operating Expenses",
                "selling, general and administrative": "Operating Expenses",
                "sga": "Operating Expenses",
                "administrative expenses": "Operating Expenses",
                "selling expenses": "Operating Expenses",
                "general expenses": "Operating Expenses",
                "operating costs": "Operating Expenses",
                
                # Operating Income variations
                "operating income": "Operating Income",
                "operating profit": "Operating Income",
                "ebit": "Operating Income",
                "operating earnings": "Operating Income",
                "operating result": "Operating Income",
                
                # Interest variations
                "interest expense": "Interest Expense",
                "interest income": "Interest Income",
                "net interest expense": "Net Interest Expense",
                "net interest income": "Net Interest Income",
                "finance costs": "Interest Expense",
                "financial expenses": "Interest Expense",
                
                # Tax variations
                "income tax expense": "Income Tax Expense",
                "tax expense": "Income Tax Expense",
                "current tax": "Income Tax Expense",
                "deferred tax": "Deferred Tax",
                
                # Net Income variations
                "net income": "Net Income",
                "net profit": "Net Income",
                "profit after tax": "Net Income",
                "net earnings": "Net Income",
                "net result": "Net Income",
                "profit for the year": "Net Income",
                "earnings": "Net Income",
                
                # EPS variations
                "earnings per share": "Earnings Per Share",
                "eps": "Earnings Per Share",
                "basic earnings per share": "Basic Earnings Per Share",
                "diluted earnings per share": "Diluted Earnings Per Share"
            }
            
        elif statement_type == StatementType.BALANCE_SHEET:
            return {
                # Current Assets variations
                "cash and cash equivalents": "Cash and Cash Equivalents",
                "cash": "Cash and Cash Equivalents",
                "cash at bank": "Cash and Cash Equivalents",
                "bank deposits": "Cash and Cash Equivalents",
                "short-term investments": "Short-term Investments",
                "marketable securities": "Short-term Investments",
                "accounts receivable": "Accounts Receivable",
                "trade receivables": "Accounts Receivable",
                "debtors": "Accounts Receivable",
                "inventory": "Inventory",
                "stock": "Inventory",
                "work in progress": "Inventory",
                "finished goods": "Inventory",
                "raw materials": "Inventory",
                "prepaid expenses": "Prepaid Expenses",
                "other current assets": "Other Current Assets",
                "total current assets": "Total Current Assets",
                
                # Non-Current Assets variations
                "property, plant and equipment": "Property, Plant and Equipment",
                "ppe": "Property, Plant and Equipment",
                "fixed assets": "Property, Plant and Equipment",
                "tangible assets": "Property, Plant and Equipment",
                "intangible assets": "Intangible Assets",
                "goodwill": "Goodwill",
                "patents": "Intangible Assets",
                "trademarks": "Intangible Assets",
                "software": "Intangible Assets",
                "investments": "Investments",
                "long-term investments": "Long-term Investments",
                "other non-current assets": "Other Non-Current Assets",
                "total non-current assets": "Total Non-Current Assets",
                "total assets": "Total Assets",
                
                # Current Liabilities variations
                "accounts payable": "Accounts Payable",
                "trade payables": "Accounts Payable",
                "creditors": "Accounts Payable",
                "short-term debt": "Short-term Debt",
                "current portion of debt": "Short-term Debt",
                "accrued expenses": "Accrued Expenses",
                "other current liabilities": "Other Current Liabilities",
                "total current liabilities": "Total Current Liabilities",
                
                # Non-Current Liabilities variations
                "long-term debt": "Long-term Debt",
                "bonds payable": "Long-term Debt",
                "deferred tax liabilities": "Deferred Tax Liabilities",
                "pension obligations": "Pension Obligations",
                "other non-current liabilities": "Other Non-Current Liabilities",
                "total non-current liabilities": "Total Non-Current Liabilities",
                "total liabilities": "Total Liabilities",
                
                # Equity variations
                "share capital": "Share Capital",
                "common stock": "Share Capital",
                "ordinary shares": "Share Capital",
                "preferred shares": "Preferred Shares",
                "retained earnings": "Retained Earnings",
                "accumulated profits": "Retained Earnings",
                "reserves": "Reserves",
                "other reserves": "Other Reserves",
                "treasury shares": "Treasury Shares",
                "total equity": "Total Equity",
                "shareholders' equity": "Total Equity",
                "stockholders' equity": "Total Equity",
                "owners' equity": "Total Equity"
            }
            
        elif statement_type == StatementType.CASH_FLOW_STATEMENT:
            return {
                # Operating Cash Flow variations
                "operating cash flow": "Operating Cash Flow",
                "cash from operations": "Operating Cash Flow",
                "cash generated from operations": "Operating Cash Flow",
                "net cash from operating activities": "Operating Cash Flow",
                "cash flow from operations": "Operating Cash Flow",
                
                # Investing Cash Flow variations
                "investing cash flow": "Investing Cash Flow",
                "cash from investing": "Investing Cash Flow",
                "cash used in investing": "Investing Cash Flow",
                "net cash from investing activities": "Investing Cash Flow",
                "cash flow from investing": "Investing Cash Flow",
                "capital expenditures": "Capital Expenditures",
                "capex": "Capital Expenditures",
                "purchase of property, plant and equipment": "Capital Expenditures",
                "acquisitions": "Acquisitions",
                "purchase of investments": "Purchase of Investments",
                "sale of investments": "Sale of Investments",
                
                # Financing Cash Flow variations
                "financing cash flow": "Financing Cash Flow",
                "cash from financing": "Financing Cash Flow",
                "cash used in financing": "Financing Cash Flow",
                "net cash from financing activities": "Financing Cash Flow",
                "cash flow from financing": "Financing Cash Flow",
                "dividends paid": "Dividends Paid",
                "share repurchases": "Share Repurchases",
                "debt issuance": "Debt Issuance",
                "debt repayment": "Debt Repayment",
                "proceeds from borrowings": "Proceeds from Borrowings",
                "repayment of borrowings": "Repayment of Borrowings",
                
                # Net Cash Flow variations
                "net cash flow": "Net Cash Flow",
                "net increase in cash": "Net Increase in Cash",
                "net decrease in cash": "Net Decrease in Cash",
                "change in cash": "Change in Cash",
                "cash at beginning of period": "Cash at Beginning of Period",
                "cash at end of period": "Cash at End of Period",
                "cash and cash equivalents at beginning": "Cash at Beginning of Period",
                "cash and cash equivalents at end": "Cash at End of Period"
            }
        
        return {}
    
    def _get_general_standardizations(self) -> Dict[str, str]:
        """Get general standardizations that apply across all statement types."""
        return {
            "total": "Total",
            "net": "Net",
            "gross": "Gross",
            "operating": "Operating",
            "current": "Current",
            "non-current": "Non-Current",
            "long-term": "Long-term",
            "short-term": "Short-term",
            "other": "Other",
            "miscellaneous": "Other"
        }
    
    def _fuzzy_match_line_item(self, name: str, standardizations: Dict[str, str]) -> str:
        """Perform fuzzy matching for line items that don't have exact matches."""
        # Common word replacements
        replacements = {
            "&": "and",
            "and": "and",
            "of": "of",
            "the": "the",
            "in": "in",
            "on": "on",
            "at": "at",
            "for": "for",
            "with": "with",
            "from": "from",
            "to": "to"
        }
        
        # Clean up the name
        cleaned_name = name
        for old, new in replacements.items():
            cleaned_name = cleaned_name.replace(old, new)
        
        # Try to find partial matches
        for key, value in standardizations.items():
            if any(word in cleaned_name for word in key.split()):
                return value
        
        # If no match found, return the original name with proper capitalization
        return name.title()
