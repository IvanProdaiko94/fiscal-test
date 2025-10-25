"""
Comprehensive Financial Statement Schemas

This module defines comprehensive schemas for all financial statement types
with all possible fields that might appear in annual reports.
"""

from typing import Dict, List, Any
from enum import Enum

from pkg import StatementType


class FinancialFieldCategory(Enum):
    """Categories of financial fields."""
    REVENUE = "revenue"
    COSTS = "costs"
    PROFITABILITY = "profitability"
    ASSETS = "assets"
    LIABILITIES = "liabilities"
    EQUITY = "equity"
    CASH_FLOW = "cash_flow"
    RATIOS = "ratios"
    OTHER = "other"


class ComprehensiveFinancialSchemas:
    """Comprehensive schemas for all financial statement types."""
    
    @staticmethod
    def get_income_statement_schema() -> Dict[str, Any]:
        """Get comprehensive income statement schema."""
        return {
            "type": "object",
            "properties": {
                "statement_type": {
                    "type": "string",
                    "enum": ["income_statement"],
                    "description": "The type of financial statement"
                },
                "year": {
                    "type": "integer",
                    "minimum": 2000,
                    "maximum": 2030,
                    "description": "The fiscal year"
                },
                "currency": {
                    "type": "string",
                    "enum": ["EUR", "USD", "GBP", "CHF", "SEK", "NOK", "DKK"],
                    "description": "The reporting currency"
                },
                "reporting_standard": {
                    "type": "string",
                    "enum": ["IFRS", "US GAAP", "Dutch GAAP", "Other"],
                    "description": "The accounting standard used"
                },
                "quality_score": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 10,
                    "description": "Overall quality score (1-10)"
                },
                "review_notes": {
                    "type": "string",
                    "description": "Professional review notes"
                },
                "line_items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "line_item": {
                                "type": "string",
                                "description": "Standardized financial line item name"
                            },
                            "value": {
                                "type": ["number", "null"],
                                "description": "Financial value (null if not found)"
                            },
                            "unit": {
                                "type": "string",
                                "enum": ["EUR", "USD", "GBP", "CHF", "SEK", "NOK", "DKK", "thousands", "millions", "billions"],
                                "description": "Unit of measurement"
                            },
                            "category": {
                                "type": "string",
                                "enum": ["revenue", "costs", "profitability", "other"],
                                "description": "Category of the line item"
                            },
                            "quality_score": {
                                "type": "integer",
                                "minimum": 1,
                                "maximum": 10,
                                "description": "Quality score for this line item"
                            },
                            "notes": {
                                "type": "string",
                                "description": "Additional notes"
                            }
                        },
                        "required": ["line_item", "value", "unit", "category", "quality_score"],
                        "additionalProperties": False
                    },
                    "description": "Array of income statement line items"
                }
            },
            "required": ["statement_type", "year", "currency", "reporting_standard", "quality_score", "line_items"],
            "additionalProperties": False
        }
    
    @staticmethod
    def get_balance_sheet_schema() -> Dict[str, Any]:
        """Get comprehensive balance sheet schema."""
        return {
            "type": "object",
            "properties": {
                "statement_type": {
                    "type": "string",
                    "enum": ["balance_sheet"],
                    "description": "The type of financial statement"
                },
                "year": {
                    "type": "integer",
                    "minimum": 2000,
                    "maximum": 2030,
                    "description": "The fiscal year"
                },
                "currency": {
                    "type": "string",
                    "enum": ["EUR", "USD", "GBP", "CHF", "SEK", "NOK", "DKK"],
                    "description": "The reporting currency"
                },
                "reporting_standard": {
                    "type": "string",
                    "enum": ["IFRS", "US GAAP", "Dutch GAAP", "Other"],
                    "description": "The accounting standard used"
                },
                "quality_score": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 10,
                    "description": "Overall quality score (1-10)"
                },
                "review_notes": {
                    "type": "string",
                    "description": "Professional review notes"
                },
                "line_items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "line_item": {
                                "type": "string",
                                "description": "Standardized financial line item name"
                            },
                            "value": {
                                "type": ["number", "null"],
                                "description": "Financial value (null if not found)"
                            },
                            "unit": {
                                "type": "string",
                                "enum": ["EUR", "USD", "GBP", "CHF", "SEK", "NOK", "DKK", "thousands", "millions", "billions"],
                                "description": "Unit of measurement"
                            },
                            "category": {
                                "type": "string",
                                "enum": ["assets", "liabilities", "equity", "other"],
                                "description": "Category of the line item"
                            },
                            "quality_score": {
                                "type": "integer",
                                "minimum": 1,
                                "maximum": 10,
                                "description": "Quality score for this line item"
                            },
                            "notes": {
                                "type": "string",
                                "description": "Additional notes"
                            }
                        },
                        "required": ["line_item", "value", "unit", "category", "quality_score"],
                        "additionalProperties": False
                    },
                    "description": "Array of balance sheet line items"
                }
            },
            "required": ["statement_type", "year", "currency", "reporting_standard", "quality_score", "line_items"],
            "additionalProperties": False
        }
    
    @staticmethod
    def get_cash_flow_schema() -> Dict[str, Any]:
        """Get comprehensive cash flow statement schema."""
        return {
            "type": "object",
            "properties": {
                "statement_type": {
                    "type": "string",
                    "enum": ["cash_flow_statement"],
                    "description": "The type of financial statement"
                },
                "year": {
                    "type": "integer",
                    "minimum": 2000,
                    "maximum": 2030,
                    "description": "The fiscal year"
                },
                "currency": {
                    "type": "string",
                    "enum": ["EUR", "USD", "GBP", "CHF", "SEK", "NOK", "DKK"],
                    "description": "The reporting currency"
                },
                "reporting_standard": {
                    "type": "string",
                    "enum": ["IFRS", "US GAAP", "Dutch GAAP", "Other"],
                    "description": "The accounting standard used"
                },
                "quality_score": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 10,
                    "description": "Overall quality score (1-10)"
                },
                "review_notes": {
                    "type": "string",
                    "description": "Professional review notes"
                },
                "line_items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "line_item": {
                                "type": "string",
                                "description": "Standardized financial line item name"
                            },
                            "value": {
                                "type": ["number", "null"],
                                "description": "Financial value (null if not found)"
                            },
                            "unit": {
                                "type": "string",
                                "enum": ["EUR", "USD", "GBP", "CHF", "SEK", "NOK", "DKK", "thousands", "millions", "billions"],
                                "description": "Unit of measurement"
                            },
                            "category": {
                                "type": "string",
                                "enum": ["operating", "investing", "financing", "other"],
                                "description": "Category of the line item"
                            },
                            "quality_score": {
                                "type": "integer",
                                "minimum": 1,
                                "maximum": 10,
                                "description": "Quality score for this line item"
                            },
                            "notes": {
                                "type": "string",
                                "description": "Additional notes"
                            }
                        },
                        "required": ["line_item", "value", "unit", "category", "quality_score"],
                        "additionalProperties": False
                    },
                    "description": "Array of cash flow statement line items"
                }
            },
            "required": ["statement_type", "year", "currency", "reporting_standard", "quality_score", "line_items"],
            "additionalProperties": False
        }
    
    @staticmethod
    def get_comprehensive_field_mapping() -> Dict[str, List[str]]:
        """Get comprehensive mapping of all possible financial fields."""
        return {
            "income_statement": {
                "revenue": [
                    "Revenue", "Sales", "Turnover", "Net Sales", "Gross Revenue",
                    "Service Revenue", "Product Revenue", "Other Revenue",
                    "Operating Revenue", "Total Revenue", "Net Revenue",
                    "Non-interest Revenue", "Net Non-interest Revenue", "Interest Revenue",
                    "Fee Revenue", "Commission Revenue", "Subscription Revenue",
                    "Net System Sales", "Net Service and Field Option Sales", "Total Net Sales",
                    "Cloud", "Software Licenses", "Software Support", "Software Licenses and Support",
                    "Cloud and Software", "Services", "Total Revenue (IFRS)", "Total Revenue (non-IFRS)",
                    "Revenues", "Segment Revenue", "Share of More Predictable Revenue"
                ],
                "costs": [
                    "Cost of Sales", "Cost of Goods Sold", "COGS", "Cost of Revenue",
                    "Direct Costs", "Cost of Services", "Material Costs",
                    "Production Costs", "Manufacturing Costs", "Costs of Goods Sold",
                    "Costs Incurred from Financial Institutions", "Financial Institution Costs",
                    "Processing Costs", "Transaction Costs", "Service Costs",
                    "Cost of Cloud", "Cost of Software Licenses and Support", "Cost of Cloud and Software",
                    "Cost of System Sales", "Cost of Service and Field Option Sales", "Total Cost of Sales",
                    "Total Cost of Revenue", "Total Operating Expenses", "Personnel Expenses",
                    "Research and Development Costs", "Selling, General and Administrative Costs",
                    "Share-based Compensation Expense", "Share-based Payment Expenses",
                    "Social Securities and Pension Costs", "Other Operating Expenses",
                    "Finance Costs", "Finance Expense", "Interest Expense", "Income Tax Expense"
                ],
                "profitability": [
                    "Gross Profit", "Gross Margin", "Gross Income", "Cloud Gross Profit",
                    "Operating Expenses", "SG&A", "Selling, General and Administrative",
                    "Research and Development", "R&D Expenses", "Marketing Expenses",
                    "Administrative Expenses", "Other Operating Expenses", "Operating Income", "Operating Profit",
                    "EBIT", "Earnings Before Interest and Tax", "EBITDA",
                    "Interest Expense", "Finance Costs", "Financial Expenses", "Finance Expense",
                    "Interest Income", "Financial Income", "Finance Income", "Net Interest Expense",
                    "Net Interest Income", "Net Finance Income", "Other Financial Results",
                    "Income Tax Expense", "Tax Expense", "Income Taxes", "Provision for Income Taxes",
                    "Current Tax", "Deferred Tax Expense", "Deferred Tax",
                    "Net Income", "Net Profit", "Net Earnings", "Profit After Tax", "Net Income for the Period",
                    "Income Before Income Taxes", "Income Before Net Finance Income and Income Taxes",
                    "Income After Income Taxes", "Profit Before Tax", "Profit Before Tax from Continuing Operations",
                    "Profit After Tax from Continuing Operations", "Profit from Equity Method Investments",
                    "Earnings Per Share", "EPS", "Basic EPS", "Diluted EPS", "Basic Net Income per Ordinary Share",
                    "Diluted Net Income per Ordinary Share",
                    "Wages and Salaries", "Salaries", "Employee Costs",
                    "Social Securities and Pension Costs", "Pension Costs", "Social Security Costs",
                    "Amortization and Depreciation", "Depreciation", "Amortization", "Depreciation and Amortization",
                    "Other Income", "Other Income/(Expenses)", "Other Operating Income/Expense"
                ],
                "other": [
                    "Other Income", "Other Expenses", "Extraordinary Items",
                    "Discontinued Operations", "Minority Interest", "Non-controlling Interest"
                ]
            },
            "balance_sheet": {
                "assets": [
                    "Cash and Cash Equivalents", "Cash", "Cash and Bank", "Cash and Cash Equivalents at Beginning of Period",
                    "Cash and Cash Equivalents at End of Period", "Short-term Investments", "Marketable Securities",
                    "Accounts Receivable", "Trade Receivables", "Receivables", "Accounts Receivable, Net",
                    "Finance Receivables", "Finance Receivables, Net", "Inventory", "Stock", "Raw Materials", 
                    "Work in Progress", "Finished Goods", "Inventories, Net", "Prepaid Expenses", "Other Current Assets",
                    "Current Tax Assets", "Tax Assets", "Contract Assets", "Total Current Assets", 
                    "Property, Plant and Equipment", "PP&E", "Fixed Assets", "Tangible Assets", "Property, Plant and Equipment, Net",
                    "Intangible Assets", "Goodwill", "Other Intangible Assets, Net", "Right-of-use Assets",
                    "Deferred Tax Assets", "Other Assets", "Other Non-financial Assets", "Equity Method Investments",
                    "Total Non-current Assets", "Total Assets"
                ],
                "liabilities": [
                    "Accounts Payable", "Trade Payables", "Payables", "Accrued and Other Liabilities",
                    "Short-term Debt", "Current Portion of Long-term Debt", "Current Tax Liabilities",
                    "Tax Liabilities", "Contract Liabilities", "Total Current Liabilities", 
                    "Long-term Debt", "Financial Debts", "Bonds Payable", "Deferred Tax Liabilities",
                    "Deferred and Other Tax Liabilities", "Other Long-term Liabilities",
                    "Total Non-current Liabilities", "Total Liabilities"
                ],
                "equity": [
                    "Share Capital", "Common Stock", "Preferred Stock", "Issued Capital", "Issued and Outstanding Shares",
                    "Additional Paid-in Capital", "Share Premium", "Retained Earnings",
                    "Accumulated Other Comprehensive Income", "Other Components of Equity", "Treasury Stock",
                    "Treasury Shares at Cost", "Total Shareholders' Equity", "Total Equity",
                    "Equity Attributable to Owners of Parent", "Non-controlling Interests"
                ],
                "other": [
                    "Minority Interest", "Non-controlling Interest",
                    "Other Equity Items"
                ]
            },
            "cash_flow_statement": {
                "operating": [
                    "Operating Cash Flow", "Cash from Operations", "Net Cash from Operating Activities",
                    "Operating Activities", "Net Cash Flows from Operating Activities", "Cash Flows from Operating Activities",
                    "Depreciation", "Amortization", "Depreciation and Amortization", "Changes in Working Capital",
                    "Accounts Receivable Changes", "Inventory Changes", "Accounts Payable Changes",
                    "Interest Paid", "Interest Received", "Income Taxes Paid", "Income Taxes Paid, Net of Refunds"
                ],
                "investing": [
                    "Investing Cash Flow", "Cash from Investing", "Net Cash from Investing Activities",
                    "Investing Activities", "Net Cash Flows from Investing Activities", "Cash Flows from Investing Activities",
                    "Capital Expenditures", "CAPEX", "Property, Plant and Equipment", "Purchases of Plant and Equipment",
                    "Capitalization of Intangible Assets", "Acquisitions", "Disposals", "Investments",
                    "Cash Flows for Business Combinations", "Purchase of Intangible Assets"
                ],
                "financing": [
                    "Financing Cash Flow", "Cash from Financing", "Net Cash from Financing Activities",
                    "Financing Activities", "Net Cash Flows from Financing Activities", "Cash Flows from Financing Activities",
                    "Dividends Paid", "Share Repurchases", "Debt Issuance", "Debt Repayment", "Repayment of Debt",
                    "Equity Issuance", "Net Proceeds from Issuance of Shares", "Net Proceeds from Issuance of Notes"
                ],
                "other": [
                    "Net Cash Flow", "Cash at Beginning of Period",
                    "Cash at End of Period", "Foreign Exchange Effects"
                ]
            }
        }

    @staticmethod
    def get_analysis_schema(statement_type: StatementType) -> Dict[str, Any]:
        """Get JSON schema for analysis results."""
        return {
            "type": "object",
            "properties": {
                "statement_type": {
                    "type": "string",
                    "enum": [statement_type.value],
                    "description": "The type of financial statement"
                },
                "year": {
                    "type": "integer",
                    "minimum": 2000,
                    "maximum": 2030,
                    "description": "The fiscal year"
                },
                "currency": {
                    "type": "string",
                    "enum": ["EUR", "USD", "GBP", "CHF", "SEK", "NOK", "DKK"],
                    "description": "The reporting currency"
                },
                "reporting_standard": {
                    "type": "string",
                    "enum": ["IFRS", "US GAAP", "Dutch GAAP", "Other"],
                    "description": "The accounting standard used"
                },
                "confidence_level": {
                    "type": "string",
                    "enum": ["High", "Medium", "Low"],
                    "description": "Overall confidence in the extracted data"
                },
                "analysis_notes": {
                    "type": "string",
                    "description": "Professional analysis notes and observations"
                },
                "line_items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "line_item": {
                                "type": "string",
                                "description": "Standardized financial line item name"
                            },
                            "value": {
                                "type": ["number", "null"],
                                "description": "Financial value (null if not found)"
                            },
                            "unit": {
                                "type": "string",
                                "enum": ["EUR", "USD", "GBP", "CHF", "SEK", "NOK", "DKK", "thousands", "millions", "billions"],
                                "description": "Unit of measurement"
                            },
                            "confidence": {
                                "type": "string",
                                "enum": ["High", "Medium", "Low"],
                                "description": "Confidence level for this specific value"
                            },
                            "notes": {
                                "type": "string",
                                "description": "Additional notes about this line item"
                            }
                        },
                        "required": ["line_item", "value", "unit", "confidence"],
                        "additionalProperties": False
                    },
                    "description": "Array of financial line items"
                }
            },
            "required": ["statement_type", "year", "currency", "reporting_standard", "confidence_level", "line_items"],
            "additionalProperties": False
        }

    @staticmethod
    def get_review_schema(statement_type: StatementType) -> Dict[str, Any]:
        """Get JSON schema for review results."""
        return {
            "type": "object",
            "properties": {
                "statement_type": {
                    "type": "string",
                    "enum": [statement_type.value],
                    "description": "The type of financial statement"
                },
                "year": {
                    "type": "integer",
                    "minimum": 2000,
                    "maximum": 2030,
                    "description": "The fiscal year"
                },
                "currency": {
                    "type": "string",
                    "enum": ["EUR", "USD", "GBP", "CHF", "SEK", "NOK", "DKK"],
                    "description": "The reporting currency"
                },
                "reporting_standard": {
                    "type": "string",
                    "enum": ["IFRS", "US GAAP", "Dutch GAAP", "Other"],
                    "description": "The accounting standard used"
                },
                "quality_score": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 10,
                    "description": "Overall quality score (1-10)"
                },
                "review_notes": {
                    "type": "string",
                    "description": "Professional review notes and recommendations"
                },
                "line_items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "line_item": {
                                "type": "string",
                                "description": "Standardized financial line item name"
                            },
                            "value": {
                                "type": ["number", "null"],
                                "description": "Financial value (null if not found)"
                            },
                            "unit": {
                                "type": "string",
                                "enum": ["EUR", "USD", "GBP", "CHF", "SEK", "NOK", "DKK", "thousands", "millions", "billions"],
                                "description": "Unit of measurement"
                            },
                            "quality_score": {
                                "type": "integer",
                                "minimum": 1,
                                "maximum": 10,
                                "description": "Quality score for this line item (1-10)"
                            },
                            "review_notes": {
                                "type": "string",
                                "description": "Review notes for this line item"
                            }
                        },
                        "required": ["line_item", "value", "unit", "quality_score"],
                        "additionalProperties": False
                    },
                    "description": "Array of reviewed financial line items"
                }
            },
            "required": ["statement_type", "year", "currency", "reporting_standard", "quality_score", "line_items"],
            "additionalProperties": False
        }

    @staticmethod
    def get_verification_schema() -> Dict[str, Any]:
        """Get JSON schema for verification results."""
        return {
            "type": "object",
            "properties": {
                "verification_status": {
                    "type": "string",
                    "description": "Overall verification status: PASSED, FAILED, or NEEDS_REVIEW"
                },
                "quality_score": {
                    "type": "number",
                    "minimum": 1,
                    "maximum": 10,
                    "description": "Overall quality score from 1 (poor) to 10 (excellent)"
                },
                "mathematical_consistency": {
                    "type": "string",
                    "description": "Assessment of mathematical consistency"
                },
                "completeness_assessment": {
                    "type": "string",
                    "description": "Assessment of data completeness"
                },
                "issues_found": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of any issues or inconsistencies found"
                },
                "recommendations": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Specific recommendations for improvement"
                },
                "confidence_level": {
                    "type": "string",
                    "enum": ["HIGH", "MEDIUM", "LOW"],
                    "description": "Overall confidence in the extracted data"
                },
                "verified_data": {
                    "type": "object",
                    "description": "The verified and corrected financial data"
                }
            },
            "required": ["verification_status", "quality_score", "confidence_level", "verified_data"]
        }
    
    @staticmethod
    def get_consolidation_mappings() -> Dict[str, List[str]]:
        """
        Get precise term consolidation mappings for Program 4.
        
        Each group contains terms that are semantically identical and should be consolidated.
        Definitions are provided to ensure accurate consolidation.
        """
        return {
            # REVENUE TERMS - All represent income from business operations
            # Definition: Money received from selling goods/services
            "Revenue": [
                "Revenue", "Sales", "Turnover", "Net Sales", "Gross Revenue", "Total Revenue",
                "Net Revenue", "Non-interest Revenue", "Net Non-interest Revenue", "Interest Revenue",
                "Fee Revenue", "Commission Revenue", "Subscription Revenue", "Service Revenue",
                "Product Revenue", "Operating Revenue", "Net System Sales", "Net Service and Field Option Sales",
                "Total Net Sales", "Cloud", "Software Licenses", "Software Support",
                "Software Licenses and Support", "Cloud and Software", "Services", "Revenues",
                "Segment Revenue", "Share of More Predictable Revenue"
            ],
            
            # COST OF SALES TERMS - All represent direct costs of producing goods/services
            # Definition: Direct costs attributable to production of goods/services sold
            "Cost of Sales": [
                "Cost of Sales", "Cost of Goods Sold", "COGS", "Cost of Revenue", "Costs of Goods Sold",
                "Costs Incurred from Financial Institutions", "Financial Institution Costs",
                "Processing Costs", "Transaction Costs", "Service Costs", "Cost of Cloud",
                "Cost of Software Licenses and Support", "Cost of Cloud and Software",
                "Cost of System Sales", "Cost of Service and Field Option Sales", "Total Cost of Sales",
                "Total Cost of Revenue", "Direct Costs", "Cost of Services", "Material Costs",
                "Production Costs", "Manufacturing Costs"
            ],
            
            # OPERATING EXPENSES TERMS - All represent indirect business costs
            # Definition: Costs not directly tied to production but necessary for operations
            "Operating Expenses": [
                "Operating Expenses", "Total Operating Expenses", "Personnel Expenses",
                "Research and Development Costs", "R&D Expenses", "Selling, General and Administrative Costs",
                "SG&A", "Marketing Expenses", "Administrative Expenses", "Other Operating Expenses",
                "Share-based Compensation Expense", "Share-based Payment Expenses",
                "Social Securities and Pension Costs", "Pension Costs", "Social Security Costs",
                "Wages and Salaries", "Salaries", "Employee Costs"
            ],
            
            # GROSS PROFIT TERMS - All represent revenue minus cost of sales
            # Definition: Revenue minus direct costs of goods/services sold
            "Gross Profit": [
                "Gross Profit", "Gross Margin", "Gross Income", "Cloud Gross Profit"
            ],
            
            # OPERATING INCOME TERMS - All represent profit from core operations
            # Definition: Gross profit minus operating expenses (before interest and taxes)
            "Operating Income": [
                "Operating Income", "Operating Profit", "Income from Operations", "EBIT",
                "Earnings Before Interest and Tax"
            ],
            
            # NET INCOME TERMS - All represent final profit after all expenses
            # Definition: Total profit after all expenses, taxes, and interest
            "Net Income": [
                "Net Income", "Net Profit", "Net Earnings", "Profit After Tax", "Net Income for the Period",
                "Income After Income Taxes", "Profit Before Tax", "Profit Before Tax from Continuing Operations",
                "Profit After Tax from Continuing Operations", "Profit from Equity Method Investments"
            ],
            
            # INTEREST INCOME TERMS - All represent income from interest
            # Definition: Income earned from interest on investments or loans
            "Interest Income": [
                "Interest Income", "Financial Income", "Finance Income", "Net Interest Income",
                "Net Finance Income", "Other Financial Results"
            ],
            
            # INTEREST EXPENSE TERMS - All represent costs of borrowing
            # Definition: Cost of borrowing money (interest paid on debt)
            "Interest Expense": [
                "Interest Expense", "Finance Costs", "Financial Expenses", "Finance Expense",
                "Net Interest Expense"
            ],
            
            # INCOME TAX EXPENSE TERMS - All represent taxes on income
            # Definition: Taxes owed on company's taxable income
            "Income Tax Expense": [
                "Income Tax Expense", "Tax Expense", "Income Taxes", "Provision for Income Taxes",
                "Current Tax", "Deferred Tax Expense", "Deferred Tax"
            ],
            
            # CASH AND CASH EQUIVALENTS TERMS - All represent liquid assets
            # Definition: Highly liquid assets that can be quickly converted to cash
            "Cash and Cash Equivalents": [
                "Cash and Cash Equivalents", "Cash", "Cash and Bank", "Cash and Cash Equivalents at Beginning of Period",
                "Cash and Cash Equivalents at End of Period"
            ],
            
            # ACCOUNTS RECEIVABLE TERMS - All represent money owed by customers
            # Definition: Money customers owe for goods/services already delivered
            "Accounts Receivable": [
                "Accounts Receivable", "Trade Receivables", "Receivables", "Accounts Receivable, Net",
                "Finance Receivables", "Finance Receivables, Net"
            ],
            
            # INVENTORY TERMS - All represent goods held for sale
            # Definition: Goods and materials held for production or sale
            "Inventory": [
                "Inventory", "Stock", "Raw Materials", "Work in Progress", "Finished Goods", "Inventories, Net"
            ],
            
            # PROPERTY, PLANT AND EQUIPMENT TERMS - All represent fixed assets
            # Definition: Long-term physical assets used in business operations
            "Property, Plant and Equipment": [
                "Property, Plant and Equipment", "PP&E", "Fixed Assets", "Tangible Assets",
                "Property, Plant and Equipment, Net"
            ],
            
            # INTANGIBLE ASSETS TERMS - All represent non-physical assets
            # Definition: Non-physical assets with value (patents, trademarks, goodwill)
            "Intangible Assets": [
                "Intangible Assets", "Goodwill", "Other Intangible Assets, Net", "Right-of-use Assets"
            ],
            
            # ACCOUNTS PAYABLE TERMS - All represent money owed to suppliers
            # Definition: Money owed to suppliers for goods/services received
            "Accounts Payable": [
                "Accounts Payable", "Trade Payables", "Payables", "Accrued and Other Liabilities"
            ],
            
            # SHORT-TERM DEBT TERMS - All represent debt due within one year
            # Definition: Debt obligations due within 12 months
            "Short-term Debt": [
                "Short-term Debt", "Current Portion of Long-term Debt"
            ],
            
            # LONG-TERM DEBT TERMS - All represent debt due after one year
            # Definition: Debt obligations due after 12 months
            "Long-term Debt": [
                "Long-term Debt", "Financial Debts", "Bonds Payable"
            ],
            
            # SHARE CAPITAL TERMS - All represent equity from share issuance
            # Definition: Money received from issuing shares to investors
            "Share Capital": [
                "Share Capital", "Common Stock", "Preferred Stock", "Issued Capital", "Issued and Outstanding Shares"
            ],
            
            # RETAINED EARNINGS TERMS - All represent accumulated profits
            # Definition: Profits kept in the company rather than distributed as dividends
            "Retained Earnings": [
                "Retained Earnings", "Additional Paid-in Capital", "Share Premium"
            ],
            
            # TREASURY STOCK TERMS - All represent company's own shares held
            # Definition: Company's own shares that have been repurchased and held
            "Treasury Stock": [
                "Treasury Stock", "Treasury Shares at Cost"
            ],
            
            # OPERATING CASH FLOW TERMS - All represent cash from operations
            # Definition: Cash generated from core business operations
            "Operating Cash Flow": [
                "Operating Cash Flow", "Cash from Operations", "Net Cash from Operating Activities",
                "Operating Activities", "Net Cash Flows from Operating Activities", "Cash Flows from Operating Activities"
            ],
            
            # INVESTING CASH FLOW TERMS - All represent cash from investments
            # Definition: Cash flows from buying/selling assets and investments
            "Investing Cash Flow": [
                "Investing Cash Flow", "Cash from Investing", "Net Cash from Investing Activities",
                "Investing Activities", "Net Cash Flows from Investing Activities", "Cash Flows from Investing Activities"
            ],
            
            # FINANCING CASH FLOW TERMS - All represent cash from financing
            # Definition: Cash flows from debt, equity, and dividend transactions
            "Financing Cash Flow": [
                "Financing Cash Flow", "Cash from Financing", "Net Cash from Financing Activities",
                "Financing Activities", "Net Cash Flows from Financing Activities", "Cash Flows from Financing Activities"
            ],
            
            # CAPITAL EXPENDITURES TERMS - All represent spending on fixed assets
            # Definition: Money spent on acquiring or upgrading fixed assets
            "Capital Expenditures": [
                "Capital Expenditures", "CAPEX", "Purchases of Plant and Equipment",
                "Capitalization of Intangible Assets", "Purchase of Intangible Assets"
            ],
            
            # DIVIDENDS PAID TERMS - All represent cash distributions to shareholders
            # Definition: Cash payments made to shareholders as profit distribution
            "Dividends Paid": [
                "Dividends Paid", "Dividends"
            ],
            
            # SHARE REPURCHASES TERMS - All represent company buying back its own shares
            # Definition: Company repurchasing its own shares from the market
            "Share Repurchases": [
                "Share Repurchases", "Shares Buyback", "Stock Buyback", "Share Buyback"
            ],
            
            # DEPRECIATION AND AMORTIZATION TERMS - All represent asset value reduction
            # Definition: Systematic reduction in value of assets over time
            "Depreciation and Amortization": [
                "Depreciation and Amortization", "Amortization and Depreciation", "Depreciation", "Amortization"
            ],
            
            # TOTAL ASSETS TERMS - All represent sum of all assets
            # Definition: Total value of all company assets
            "Total Assets": [
                "Total Assets", "Total Current Assets", "Total Non-current Assets"
            ],
            
            # TOTAL LIABILITIES TERMS - All represent sum of all debts
            # Definition: Total value of all company debts and obligations
            "Total Liabilities": [
                "Total Liabilities", "Total Current Liabilities", "Total Non-current Liabilities"
            ],
            
            # TOTAL EQUITY TERMS - All represent shareholders' ownership value
            # Definition: Total value of shareholders' ownership in the company
            "Total Equity": [
                "Total Equity", "Total Shareholders' Equity", "Equity Attributable to Owners of Parent"
            ]
        }