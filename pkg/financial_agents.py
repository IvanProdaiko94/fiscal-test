"""
AI Agents for Financial Data Extraction

This module implements specialized AI agents that collaborate to extract
financial data from annual reports with professional expertise.
"""

import json
import logging
import psutil
import os
from typing import List, Dict, Optional, Any
from openai import OpenAI
from .models import ExtractedDocument, StatementType, FinancialStatement, FinancialDataPoint
from .financial_schemas import ComprehensiveFinancialSchemas
from .csv_exporter import EnhancedCSVExporter

logger = logging.getLogger(__name__)


def log_memory_usage(stage: str):
    """Log current memory usage."""
    try:
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        memory_mb = memory_info.rss / 1024 / 1024
        logger.info(f"Memory usage at {stage}: {memory_mb:.2f} MB")
        
        # Also log system memory
        system_memory = psutil.virtual_memory()
        logger.info(f"System memory: {system_memory.percent}% used ({system_memory.available / 1024 / 1024 / 1024:.2f} GB available)")
        
        if memory_mb > 1000:  # More than 1GB
            logger.warning(f"High memory usage detected: {memory_mb:.2f} MB")
            
    except Exception as e:
        logger.debug(f"Could not get memory info: {e}")


class FinancialAnalystAgent:
    """Professional Financial Analyst Agent specialized in data extraction and analysis."""
    
    def __init__(self, client: OpenAI):
        self.client = client
        self.role = "Professional Financial Analyst"
        self.expertise = [
            "Financial statement analysis",
            "Accounting standards (IFRS, US GAAP)",
            "Financial metrics calculation",
            "Data validation and quality assurance",
            "Financial terminology standardization"
        ]
    
    def analyze_document(self, document: ExtractedDocument, statement_type: StatementType) -> Dict[str, Any]:
        """Analyze document and extract financial data with professional expertise."""
        log_memory_usage("start of analyze_document")
        logger.info(f"Starting document analysis for {statement_type.value}")
        logger.info(f"Document title: {document.title}")
        logger.info(f"Document year: {document.year}")
        logger.info(f"Document content length: {len(document.content)} characters")
        
        # Split document into chunks
        logger.info("Splitting document into chunks...")
        chunks = self._split_content_into_chunks(document.content, max_chunk_size=10000)
        logger.info(f"Created {len(chunks)} chunks for processing")
        log_memory_usage("after chunking")
        
        all_extracted_data = []
        
        for i, chunk in enumerate(chunks):
            log_memory_usage(f"before processing chunk {i+1}")
            logger.info(f"Processing chunk {i+1}/{len(chunks)} for {statement_type.value}")
            logger.info(f"Chunk {i+1} size: {len(chunk)} characters")
            
            try:
                logger.info(f"Creating analysis prompt for chunk {i+1}...")
                prompt = self._create_analysis_prompt(document, statement_type, chunk, i+1, len(chunks))
                logger.info(f"Prompt created, length: {len(prompt)} characters")
                log_memory_usage(f"after creating prompt for chunk {i+1}")
                
                logger.info(f"Making API call for chunk {i+1}...")
                logger.info(f"API call parameters: model=gpt-4o, max_tokens=6000, temperature=0.1")
                
                import time
                start_time = time.time()
                response = self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "system",
                            "content": self._get_system_prompt()
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.1,
                    max_tokens=6000,
                    response_format={
                        "type": "json_schema",
                        "json_schema": {
                            "name": f"financial_analysis_{statement_type.value}",
                            "schema": self._get_analysis_schema(statement_type)
                        }
                    },
                    timeout=120  # 2 minute timeout
                )
                end_time = time.time()
                logger.info(f"API call took {end_time - start_time:.2f} seconds")
                
                logger.info(f"API call completed for chunk {i+1}")
                log_memory_usage(f"after API call for chunk {i+1}")
                logger.info(f"Response received, parsing JSON...")
                chunk_data = json.loads(response.choices[0].message.content)
                logger.info(f"Successfully parsed chunk {i+1} data")
                all_extracted_data.append(chunk_data)
                log_memory_usage(f"after processing chunk {i+1}")
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing error in chunk {i+1}: {e}")
                logger.error(f"Raw response: {response.choices[0].message.content[:500]}...")
                continue
            except Exception as e:
                logger.error(f"Error processing chunk {i+1}: {e}")
                logger.error(f"Error type: {type(e).__name__}")
                
                # Check for specific OpenAI errors
                if hasattr(e, 'response'):
                    logger.error(f"OpenAI API error response: {e.response}")
                if hasattr(e, 'status_code'):
                    logger.error(f"HTTP status code: {e.status_code}")
                if hasattr(e, 'error'):
                    logger.error(f"OpenAI error details: {e.error}")
                
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                continue
        
        logger.info(f"Completed processing all chunks. Extracted data from {len(all_extracted_data)} chunks")
        
        # Merge all extracted data
        logger.info("Merging extracted data...")
        result = self._merge_extracted_data(all_extracted_data)
        logger.info(f"Data merging completed. Result keys: {list(result.keys())}")
        
        return result
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the Financial Analyst Agent."""
        return f"""You are a {self.role} with expertise in:
{', '.join(self.expertise)}

Your role is to:
1. Analyze financial documents with professional accuracy
2. Extract financial data following accounting standards
3. Identify and standardize financial terminology
4. Validate data consistency and completeness
5. Provide detailed analysis of financial metrics

Guidelines:
- Use professional financial terminology
- Follow IFRS and US GAAP standards
- Be precise with numerical values
- CRITICAL: Values in parentheses "(numeric value)" represent NEGATIVE numbers
- Identify missing or unclear data
- Provide context for unusual values
- Maintain consistency across statements

TABLE DATA HANDLING:
- Financial data may be presented in tabular format with columns for different years
- When you see table data like "Line Item | 2019 | 2020 | 2021", focus ONLY on the target year column
- Extract values from the correct year column, ignoring other years
- Handle both tabular (XLSX) and narrative (PDF) data formats appropriately

NUMBER SCALE AND UNIT INTERPRETATION:
- CRITICAL: Numbers may be in different scales (millions, billions, thousands, units)
- Look for scale indicators in: column headers, row headers, table footnotes, or next to numbers
- Common patterns: "(€, in millions)", "(in thousands)", "€ millions", "$ billions", "in €m"
- Examples: "Revenue (€ millions)" means multiply by 1,000,000; "(in thousands)" means multiply by 1,000
- Always identify and record the scale/unit for each extracted value
- If scale is unclear, note it as "scale unknown" and extract the raw number
- Convert to standard units when possible (e.g., always report in base currency units)
- Pay attention to currency symbols (€, $, £) and accounting standards (US GAAP, IFRS)
"""
    
    def _create_analysis_prompt(self, document: ExtractedDocument, statement_type: StatementType, chunk: str, chunk_num: int, total_chunks: int) -> str:
        """Create an analysis prompt for a specific statement type and chunk."""
        # Get comprehensive field mappings for better extraction
        field_mapping = ComprehensiveFinancialSchemas.get_comprehensive_field_mapping()
        statement_fields = field_mapping.get(statement_type.value, {})
        
        # Create field guidance text
        field_guidance = ""
        for category, fields in statement_fields.items():
            field_guidance += f"\n{category.upper()}:\n"
            for field in fields[:10]:  # Limit to the first 10 fields per category
                field_guidance += f"- {field}\n"
            if len(fields) > 10:
                field_guidance += f"- ... and {len(fields) - 10} more {category} fields\n"
        
        base_prompt = f"""
Analyze this annual report document and extract {statement_type.value} data.

Document Information:
- Title: {document.title}
- Year: {document.year}
- URL: {document.url}
- Chunk: {chunk_num}/{total_chunks}

IMPORTANT: Only extract financial data for Full Year {document.year} (FY{document.year}).
Do NOT extract data from other years, quarters, or periods.

Document Content (Chunk {chunk_num}):
{chunk}

Instructions:
1. Extract ONLY financial line items for Full Year {document.year} (FY{document.year})
2. Ignore quarterly data, previous years, or future projections
3. Look specifically for "{document.year}" year-end values
4. Standardize terminology to professional standards
5. Identify the reporting currency and accounting standard
6. Provide confidence level for each extracted value
7. IMPORTANT: Values in parentheses "(numeric value)" represent NEGATIVE numbers

TABLE DATA STRUCTURE GUIDANCE:
- If you see tabular data with columns for different years (e.g., "2019 | 2020 | 2021"), focus ONLY on the column for {document.year}
- Look for patterns like: "Line Item | 2019 | 2020 | 2021" and extract only the {document.year} values
- Table format example: "Net sales | 8,996.20 | 10,316.60 | 13,652.80" → Extract only the {document.year} value
- If data is in narrative format, extract the {document.year} values from the text

NUMBER SCALE INTERPRETATION (CRITICAL):
- ALWAYS identify the scale/unit for each number before extracting
- Look for scale indicators in: column headers, row headers, table footnotes, or next to numbers
- Common patterns: "(€, in millions)", "(in thousands)", "€ millions", "$ billions", "in €m", "€m", "$bn"
- Examples: 
  * "Year ended December 31 (€, in millions)" → multiply by 1,000,000
  * "(in thousands)" → multiply by 1,000
  * "€ millions" → multiply by 1,000,000
  * "$ billions" → multiply by 1,000,000,000
- If scale is unclear, extract the raw number and note "scale unknown"
- Always record both the raw number AND the scale/unit for each value
- Pay attention to currency symbols (€, $, £) and accounting standards (US GAAP, IFRS)

CRITICAL: Focus on FY{document.year} data only. Extract EVERY financial value you find for the {document.year} full year.

Expected Field Categories and Examples:
{field_guidance}

Look for variations of these field names and extract all financial data you find, but ONLY for Full Year {document.year}.
"""
        
        if statement_type == StatementType.INCOME_STATEMENT:
            return base_prompt + f"""

Income Statement Focus Areas for FY{document.year}:
- Revenue/Sales for {document.year} (all revenue streams)
- Cost of Goods Sold/Cost of Sales for {document.year}
- Gross Profit for {document.year}
- Operating Expenses (SG&A, R&D, etc.) for {document.year}
- Operating Income/EBIT for {document.year}
- Interest Expense/Income for {document.year}
- Tax Expense for {document.year}
- Net Income for {document.year}
- Earnings Per Share for {document.year}
- Any other income statement items for {document.year}

REMEMBER: Only extract values for Full Year {document.year}. Ignore quarterly data or other years.
"""
        
        elif statement_type == StatementType.BALANCE_SHEET:
            return base_prompt + f"""

Balance Sheet Focus Areas for FY{document.year}:
- Current Assets as of {document.year} year-end (Cash, Receivables, Inventory, etc.)
- Non-Current Assets as of {document.year} year-end (PP&E, Intangibles, etc.)
- Current Liabilities as of {document.year} year-end (Payables, Short-term debt, etc.)
- Non-Current Liabilities as of {document.year} year-end (Long-term debt, etc.)
- Shareholders' Equity as of {document.year} year-end
- Any other balance sheet items as of {document.year} year-end

REMEMBER: Only extract values as of {document.year} year-end. Ignore quarterly data or other years.
"""
        
        elif statement_type == StatementType.CASH_FLOW_STATEMENT:
            return base_prompt + f"""

Cash Flow Statement Focus Areas for FY{document.year}:
- Operating Cash Flow for {document.year}
- Investing Cash Flow for {document.year}
- Financing Cash Flow for {document.year}
- Net Cash Flow for {document.year}
- Cash at Beginning of {document.year}
- Cash at End of {document.year}
- Any other cash flow items for {document.year}

REMEMBER: Only extract values for Full Year {document.year}. Ignore quarterly data or other years.
"""
        
        return base_prompt
    
    def _split_content_into_chunks(self, content: str, max_chunk_size: int = 10000) -> List[str]:
        """Split content into simple chunks."""
        logger.info(f"Splitting content of {len(content)} characters into chunks of max {max_chunk_size} characters")
        
        if len(content) <= max_chunk_size:
            logger.info("Content fits in single chunk")
            return [content]
        
        chunks = []
        # Use a reasonable overlap that's smaller than chunk size
        overlap = min(500, max_chunk_size // 4)  # 25% of chunk size or 500 chars, whichever is smaller
        logger.info(f"Using overlap of {overlap} characters between chunks")
        
        start = 0
        chunk_count = 0
        while start < len(content):
            end = min(start + max_chunk_size, len(content))
            chunk = content[start:end]
            chunks.append(chunk)
            chunk_count += 1
            
            logger.info(f"Created chunk {chunk_count}: {len(chunk)} characters (start: {start}, end: {end})")
            
            # Move start position with overlap
            if end >= len(content):
                # We've reached the end
                break
            
            # Calculate next start position with overlap
            start = end - overlap
            
            # Safety check: ensure we always move forward
            if start <= 0:
                start = end  # Move to end of current chunk
            if start >= len(content):
                break
        
        logger.info(f"Split content into {len(chunks)} chunks total")
        return chunks
    
    def _merge_extracted_data(self, all_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Merge data extracted from multiple chunks."""
        if not all_data:
            return {}
        
        # Use the first chunk's metadata as base
        merged_data = all_data[0].copy()
        
        # Merge line items from all chunks
        all_line_items = []
        seen_items = set()  # To avoid duplicates
        
        for chunk_data in all_data:
            for item in chunk_data.get('line_items', []):
                line_item = item.get('line_item', '').lower().strip()
                if line_item and line_item not in seen_items:
                    all_line_items.append(item)
                    seen_items.add(line_item)
        
        merged_data['line_items'] = all_line_items
        
        # Update analysis notes
        merged_data['analysis_notes'] = f"Processed {len(all_data)} chunks. Extracted {len(all_line_items)} unique line items."
        
        logger.info(f"Merged data from {len(all_data)} chunks: {len(all_line_items)} unique line items")
        return merged_data
    
    def _get_analysis_schema(self, statement_type: StatementType) -> Dict[str, Any]:
        """Get JSON schema for analysis results using centralized schemas."""
        return ComprehensiveFinancialSchemas.get_analysis_schema(statement_type)
    
    def export_processed_data_to_csv(self, agent_data: Dict[str, Any], company_ticker: str, year: int, output_dir: str = "output") -> str:
        """
        Export data processed by this agent to CSV with comprehensive unit measurements.
        
        Args:
            agent_data: Raw data processed by the agent
            company_ticker: Company ticker symbol
            year: Financial year
            output_dir: Output directory for CSV files
            
        Returns:
            Path to exported CSV file
        """
        try:
            csv_exporter = EnhancedCSVExporter(output_dir)
            filepath = csv_exporter.export_agent_processed_data(agent_data, company_ticker, year)
            logger.info(f"Successfully exported agent processed data to: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Failed to export agent processed data to CSV: {e}")
            raise


class FinancialReportsWriterAgent:
    """Professional Financial Reports Writer Agent specialized in report structuring and validation."""
    
    def __init__(self, client: OpenAI):
        self.client = client
        self.role = "Professional Financial Reports Writer"
        self.expertise = [
            "Financial report structuring",
            "Data presentation and formatting",
            "Report validation and quality control",
            "Financial terminology consistency",
            "Regulatory compliance"
        ]
    
    def review_and_validate(self, analyst_data: Dict[str, Any], document: ExtractedDocument, statement_type: StatementType) -> Dict[str, Any]:
        """Review and validate the analyst's work, ensuring quality and completeness."""
        prompt = self._create_review_prompt(analyst_data, document, statement_type)
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": self._get_system_prompt()
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,
                max_tokens=4000,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": f"financial_review_{statement_type.value}",
                        "schema": self._get_review_schema(statement_type)
                    }
                }
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"Financial Reports Writer Agent error: {e}")
            return analyst_data  # Return original data if the review fails
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the Financial Reports Writer Agent."""
        return f"""You are a {self.role} with expertise in:
{', '.join(self.expertise)}

Your role is to:
1. Review financial data extracted by analysts
2. Ensure data quality and consistency
3. Validate against professional standards
4. Structure data for optimal presentation
5. Identify any missing critical information
6. Ensure regulatory compliance

Guidelines:
- Maintain high standards for financial reporting
- Ensure consistency in terminology and formatting
- Validate numerical accuracy and completeness
- CRITICAL: Values in parentheses "(numeric value)" represent NEGATIVE numbers
- Flag any potential issues or inconsistencies
- Provide clear, professional feedback

TABLE DATA VALIDATION:
- Verify that extracted data comes from the correct year column in tabular format
- Ensure no data from other years (previous/future) is included
- Validate that table structure was properly interpreted
- Check that currency units and accounting standards are correctly identified
- Confirm data consistency between tabular and narrative formats

NUMBER SCALE VALIDATION:
- CRITICAL: Verify that number scales (millions, billions, thousands) are correctly interpreted
- Check that scale indicators from headers/footnotes are properly applied
- Validate that extracted values make sense given the scale (e.g., revenue shouldn't be 13.65 if it's in millions)
- Ensure consistent scale reporting across all line items
- Flag any values that seem incorrect due to scale misinterpretation
- Verify currency symbols and accounting standards are properly identified
- Check for scale conversion errors or missing scale information
"""
    
    def _create_review_prompt(self, analyst_data: Dict[str, Any], document: ExtractedDocument, statement_type: StatementType) -> str:
        """Create a review prompt for validating analyst work."""
        return f"""
Review the financial data extracted by the Financial Analyst for {statement_type.value}.

Original Document:
- Title: {document.title}
- Year: {document.year}

CRITICAL: Verify that ALL extracted data is for Full Year {document.year} (FY{document.year}) ONLY.

Analyst's Extraction Results:
{json.dumps(analyst_data, indent=2)}

Review Tasks:
1. Validate that ALL data is for Full Year {document.year} (FY{document.year})
2. Check for any quarterly data, previous years, or future projections that should be excluded
3. Validate the accuracy of extracted data for FY{document.year}
4. Check for consistency in terminology and formatting
5. Ensure all critical line items for FY{document.year} are captured
6. Verify numerical values make sense for {document.year}
7. Identify any missing important data for FY{document.year}
8. IMPORTANT: Verify that values in parentheses "(numeric value)" are correctly treated as NEGATIVE numbers
9. TABLE DATA VALIDATION: If the original data was in table format, verify that only {document.year} column values were extracted
10. NUMBER SCALE VALIDATION: Verify that number scales (millions, billions, thousands) are correctly interpreted
11. Check that scale indicators from headers/footnotes are properly applied to all values
12. Validate that extracted values make sense given the scale (e.g., revenue shouldn't be 13.65 if it's in millions)
13. Ensure consistent scale reporting across all line items
14. Provide quality assessment
15. Suggest improvements if needed

Focus on:
- Data completeness and accuracy for FY{document.year} ONLY
- Professional presentation standards
- Regulatory compliance
- Consistency across the statement
- Clear identification of any gaps or issues
- Ensuring NO data from other years is included

Provide your review and any necessary corrections. Remove any data that is not for Full Year {document.year}.
"""
    
    def _get_review_schema(self, statement_type: StatementType) -> Dict[str, Any]:
        """Get JSON schema for review results using centralized schemas."""
        # Use the appropriate schema based on a statement type
        if statement_type == StatementType.INCOME_STATEMENT:
            return ComprehensiveFinancialSchemas.get_income_statement_schema()
        elif statement_type == StatementType.BALANCE_SHEET:
            return ComprehensiveFinancialSchemas.get_balance_sheet_schema()
        elif statement_type == StatementType.CASH_FLOW_STATEMENT:
            return ComprehensiveFinancialSchemas.get_cash_flow_schema()
        else:
            # Fallback to analysis schema
            return ComprehensiveFinancialSchemas.get_analysis_schema(statement_type)


class FinancialQualityAssuranceAgent:
    """Professional Financial Quality Assurance Agent specialized in final verification and validation."""
    
    def __init__(self, client: OpenAI):
        self.client = client
        self.role = "Professional Financial Quality Assurance Specialist"
        self.expertise = [
            "Financial data validation and verification",
            "Cross-statement consistency analysis",
            "Mathematical validation of financial statements",
            "Completeness and accuracy assessment",
            "Quality scoring and confidence evaluation",
            "Regulatory compliance verification"
        ]
    
    def final_verification(self, reviewed_data: Dict[str, Any], document: ExtractedDocument, statement_type: StatementType) -> Dict[str, Any]:
        """Perform final verification and quality assessment of extracted financial data."""
        prompt = self._create_verification_prompt(reviewed_data, document, statement_type)
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": self._get_system_prompt()
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,
                max_tokens=4000,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": f"financial_qa_verification_{statement_type.value}",
                        "schema": ComprehensiveFinancialSchemas.get_verification_schema()
                    }
                }
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"Financial Quality Assurance Agent error: {e}")
            return reviewed_data  # Return original data if verification fails
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the Financial Quality Assurance Agent."""
        return f"""You are a {self.role} with expertise in:
{', '.join(self.expertise)}

Your role is to:
1. Perform final verification of extracted financial data
2. Validate mathematical consistency and accuracy
3. Check completeness against professional standards
4. Assess overall data quality and confidence
5. Identify any remaining issues or inconsistencies
6. Provide final quality score and recommendations

Guidelines:
- Apply rigorous quality standards for financial reporting
- Verify mathematical relationships and consistency
- Ensure compliance with accounting standards
- CRITICAL: Values in parentheses "(numeric value)" represent NEGATIVE numbers
- Provide detailed quality assessment
- Flag any data that doesn't meet professional standards

TABLE DATA QUALITY ASSURANCE:
- Perform final verification that only target year data was extracted from tables
- Validate that table structure was correctly interpreted across all agents
- Ensure mathematical consistency in tabular data relationships
- Verify currency units and accounting standards are properly handled
- Confirm no cross-contamination between different years in tabular format
- Assess overall data integrity from both tabular and narrative sources

NUMBER SCALE QUALITY ASSURANCE:
- CRITICAL: Final verification of number scale interpretation across all agents
- Validate that scale indicators (millions, billions, thousands) are consistently applied
- Check mathematical relationships make sense given the scales (e.g., Revenue - COGS = Gross Profit)
- Verify that values are reasonable for the company size and industry
- Ensure no scale conversion errors or misinterpretations
- Confirm currency symbols and accounting standards are correctly identified
- Flag any inconsistencies in scale reporting between different line items
- Provide final quality score based on scale accuracy and consistency
- Give specific recommendations for improvement
"""
    
    def _create_verification_prompt(self, reviewed_data: Dict[str, Any], document: ExtractedDocument, statement_type: StatementType) -> str:
        """Create a verification prompt for final quality assessment."""
        return f"""
Perform final quality assurance verification for {statement_type.value} data.

Original Document:
- Title: {document.title}
- Year: {document.year}

CRITICAL: Verify that ALL data is for Full Year {document.year} (FY{document.year}) ONLY.

Reviewed Financial Data:
{json.dumps(reviewed_data, indent=2)}

Quality Assurance Tasks:
1. Verify ALL data is for Full Year {document.year} (FY{document.year})
2. Validate mathematical consistency and accuracy
3. Check for completeness against professional standards
4. Verify that values in parentheses are correctly treated as negative numbers
5. TABLE DATA VERIFICATION: If source data was tabular, confirm only {document.year} column was used
6. NUMBER SCALE VERIFICATION: Final verification of number scale interpretation across all agents
7. Validate that scale indicators (millions, billions, thousands) are consistently applied
8. Check mathematical relationships make sense given the scales (e.g., Revenue - COGS = Gross Profit)
9. Verify that values are reasonable for the company size and industry
10. Ensure no scale conversion errors or misinterpretations
11. Assess data quality and confidence levels
12. Identify any remaining inconsistencies or issues
13. Provide final quality score (1-10)
14. Give specific recommendations for improvement

Focus on:
- Mathematical accuracy and consistency
- Completeness of critical line items
- Professional presentation standards
- Regulatory compliance
- Data integrity and reliability
- Final quality assessment

Provide your final verification report with quality score and recommendations.
"""


class CollaborativeFinancialExtractor:
    """Orchestrates collaboration between Financial Analyst, Reports Writer, and Quality Assurance agents."""
    
    def __init__(self, openai_api_key: str):
        self.client = OpenAI(api_key=openai_api_key)
        self.analyst = FinancialAnalystAgent(self.client)
        self.writer = FinancialReportsWriterAgent(self.client)
        self.qa_agent = FinancialQualityAssuranceAgent(self.client)
    
    def extract_financial_data(self, document: ExtractedDocument, statement_type: StatementType) -> Optional[FinancialStatement]:
        """Extract financial data using collaborative AI agents."""
        log_memory_usage("start of collaborative extraction")
        logger.info(f"Starting collaborative extraction for {statement_type.value}")
        logger.info(f"Document: {document.title} ({document.year})")
        logger.info(f"Document content length: {len(document.content)} characters")
        
        try:
            # Step 1: Financial Analyst extracts data
            logger.info("Financial Analyst analyzing document...")
            logger.info("Calling analyst.analyze_document()...")
            
            analyst_data = self.analyst.analyze_document(document, statement_type)
            log_memory_usage("after analyst analysis")
            logger.info(f"Analyst analysis completed. Data keys: {list(analyst_data.keys()) if analyst_data else 'None'}")
            
            if not analyst_data:
                logger.warning("Financial Analyst failed to extract data")
                return None
            
            # Step 2: Financial Reports Writer reviews and validates
            logger.info("Financial Reports Writer reviewing data...")
            logger.info("Calling writer.review_and_validate()...")
            
            reviewed_data = self.writer.review_and_validate(analyst_data, document, statement_type)
            logger.info(f"Writer review completed. Data keys: {list(reviewed_data.keys()) if reviewed_data else 'None'}")
            
            if not reviewed_data:
                logger.warning("Financial Reports Writer review failed, using analyst data")
                reviewed_data = analyst_data
            
            # Step 3: Financial Quality Assurance Agent performs final verification
            logger.info("Financial Quality Assurance Agent performing final verification...")
            logger.info("Calling qa_agent.final_verification()...")
            
            verified_data = self.qa_agent.final_verification(reviewed_data, document, statement_type)
            logger.info(f"QA verification completed. Verification status: {verified_data.get('verification_status', 'UNKNOWN')}")
            logger.info(f"Quality score: {verified_data.get('quality_score', 'N/A')}/10")
            logger.info(f"Confidence level: {verified_data.get('confidence_level', 'UNKNOWN')}")
            
            if not verified_data:
                logger.warning("Financial Quality Assurance verification failed, using reviewed data")
                verified_data = reviewed_data
            
            # Step 4: Convert to FinancialStatement object
            logger.info("Converting to FinancialStatement object...")
            final_data = verified_data.get('verified_data', verified_data)
            result = self._convert_to_financial_statement(final_data, document)
            logger.info(f"Conversion completed. Result: {type(result)}")
            
            # Log final quality metrics
            if 'quality_score' in verified_data:
                logger.info(f"Final quality score: {verified_data['quality_score']}/10")
            if 'issues_found' in verified_data and verified_data['issues_found']:
                logger.warning(f"Issues found during verification: {verified_data['issues_found']}")
            if 'recommendations' in verified_data and verified_data['recommendations']:
                logger.info(f"QA recommendations: {verified_data['recommendations']}")
            
            return result
            
        except Exception as e:
            logger.error(f"Collaborative extraction failed: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None
    
    def _convert_to_financial_statement(self, data: Dict[str, Any], document: ExtractedDocument) -> Optional[FinancialStatement]:
        """Convert extracted data to FinancialStatement object."""
        try:
            # Extract basic information
            year = data.get('year', document.year)
            currency = data.get('currency', 'EUR')
            
            # Convert line items to FinancialDataPoint objects
            data_points = []
            for item in data.get('line_items', []):
                data_point = FinancialDataPoint(
                    line_item=item.get('line_item', ''),
                    value=item.get('value'),
                    year=year,
                    currency=currency
                )
                data_points.append(data_point)
            
            # Create FinancialStatement
            statement = FinancialStatement(
                statement_type=StatementType(data.get('statement_type', '')),
                company_ticker="",  # Will be set by caller
                year=year,
                data_points=data_points
            )
            
            logger.info(f"Successfully converted to FinancialStatement with {len(data_points)} line items")
            return statement
            
        except Exception as e:
            logger.error(f"Error converting to FinancialStatement: {e}")
            return None
