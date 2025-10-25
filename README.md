# �� Financial Data Extraction Pipeline

> **Professional-grade AI-powered system for extracting structured financial data from annual reports**

[![Status](https://img.shields.io/badge/status-production--ready-brightgreen)]() [![Python](https://img.shields.io/badge/python-3.8%2B-blue)]() [![AI](https://img.shields.io/badge/AI-GPT--4o-purple)]()

## ⚡ Quick Start

### What It Does
Automatically discovers annual reports (PDFs/XLSX), extracts financial data using 3 AI agents, and outputs structured CSVs with quality validation.

### Run in 3 Commands
```bash
pip install -r requirements.txt
cp example.env .env  # Add your OpenAI API key
python main.py
```

**Output:** `output/{ticker}/{year}/*.csv` + quality reports

## 🏗️ Architecture

### Complete End-to-End Process

```
┌─────────────────────────────────────────────────────────────────────┐
│                      FINANCIAL DATA EXTRACTION PIPELINE              │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  📥 INPUT: Company Investor Relations URLs (input.json)              │
│                                                                       │
│  [Company URLs]                                                      │
│  • investor.adyen.com/financials                                    │
│  • asml.com/en/investors/annual-report                              │
└────────────────┬────────────────────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│  🔍 PROGRAM 1: SEARCH & DISCOVERY                                    │
│  ─────────────────────────────────────────────────────────────       │
│  1. Web Crawling                                                     │
│     └─ Queue-based crawling (max depth: 2)                          │
│     └─ Domain restriction, path filtering                           │
│                                                                       │
│  2. Link Discovery                                                   │
│     └─ Find PDF and XLSX links                                      │
│     └─ Extract years from filenames                                 │
│     └─ Detect report types (Annual, Form 20-F, etc.)                │
│                                                                       │
│  3. Smart Ranking                                                    │
│     └─ Multi-factor scoring:                                        │
│        • XLSX > PDF (better structure)                               │
│        • Form 20-F > Annual Report (more detail)                     │
│        • Consolidated > Individual (more complete)                   │
│        • Penalties for quarterly/transparency reports                │
└────────────────┬────────────────────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│  📋 OUTPUT: Ranked Report Metadata                                   │
│                                                                       │
│  reports/annual_reports_ranked.json                                  │
│  {                                                                   │
│    "companies": {                                                    │
│      "ADYEN": {                                                      │
│        "years_covered": [2024, 2023, 2022, ...],                    │
│        "reports": [                                                  │
│          {                                                           │
│            "year": 2024,                                             │
│            "best": [                                                 │
│              {"title": "Annual Report 2024",                         │
│               "url": "https://.../Annual_Report_2024.pdf"}           │
│            ],                                                        │
│            "secondary": [...]                                        │
│          }                                                           │
│        ]                                                             │
│      }                                                               │
│    }                                                                 │
│  }                                                                   │
└────────────────┬────────────────────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│  📄 PROGRAM 2: CONTENT EXTRACTION                                    │
│  ─────────────────────────────────────────────────────────────       │
│  1. Download Documents                                               │
│     └─ Fetch PDF and XLSX files from URLs                           │
│     └─ Handle errors with retry logic                               │
│                                                                       │
│  2. Extract Text Content                                             │
│     PDF Extraction:                                                  │
│     ├─ PyPDF2 (primary)                                              │
│     ├─ pdfplumber (fallback)                                        │
│     └─ Text cleaning and normalization                              │
│                                                                       │
│     XLSX Extraction:                                                 │
│     ├─ openpyxl (structured data)                                   │
│     └─ Row/column parsing                                           │
│                                                                       │
│  3. Save Extracted Content                                           │
│     └─ Metadata preservation (URL, title, year, ticker)             │
└────────────────┬────────────────────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│  📋 OUTPUT: Processed Text Files                                     │
│                                                                       │
│  processed_reports/                                                  │
│  ├─ ADYEN_2024_Annual_Report_2024_pdf.txt                           │
│  ├─ ADYEN_2023_Annual_Report_2023_pdf.txt                           │
│  ├─ ASML_2024_Annual_Report_2024_pdf.txt                            │
│  └─ ...                                                              │
│                                                                       │
│  File Format:                                                        │
│  URL: https://...                                                    │
│  Title: Annual Report 2024                                           │
│  Year: 2024                                                          │
│  Ticker: ADYEN                                                       │
│  File Type: PDF                                                      │
│  =================================================================    │
│  [Extracted text content...]                                         │
└────────────────┬────────────────────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│  🤖 PROGRAM 3: AI-POWERED EXTRACTION                                 │
│  ─────────────────────────────────────────────────────────────       │
│                                                                       │
│  For each document:                                                  │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Step 1: Content Chunking                                     │  │
│  │  ──────────────────────────────────────                      │  │
│  │  • Split large docs into 10K character chunks                │  │
│  │  • 500 char overlap preserves context                        │  │
│  │  • Handle memory efficiently                                 │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                           ↓                                          │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Step 2: Financial Analyst Agent (Extraction)                │  │
│  │  ───────────────────────────────────────────                 │  │
│  │  • Analyze each chunk with professional expertise            │  │
│  │  • Extract financial data following IFRS/US GAAP            │  │
│  │  • Identify and standardize terminology                      │  │
│  │  • Apply 300+ field mappings                                 │  │
│  │  • Assess confidence levels (High/Medium/Low)                │  │
│  │  • Output: Raw extractions with confidence scores            │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                           ↓                                          │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Step 3: Reports Writer Agent (Review)                       │  │
│  │  ──────────────────────────────────────                      │  │
│  │  • Review analyst's extractions                              │  │
│  │  • Validate against professional standards                   │  │
│  │  • Check consistency in terminology and formatting           │  │
│  │  • Identify missing critical information                     │  │
│  │  • Assign quality scores (1-10 scale)                        │  │
│  │  • Output: Reviewed & validated data                         │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                           ↓                                          │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Step 4: QA Agent (Verification)                             │  │
│  │  ────────────────────────────────────────                    │  │
│  │  • Final verification of extracted data                      │  │
│  │  • Validate mathematical consistency                         │  │
│  │  • Check completeness against standards                      │  │
│  │  • Assess overall quality and confidence                     │  │
│  │  • Generate quality report with recommendations              │  │
│  │  • Output: Verified data + quality metrics                   │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                           ↓                                          │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Step 5: Statement Generation                                │  │
│  │  ───────────────────────────                                 │  │
│  │  For each statement type:                                    │  │
│  │  • Income Statement                                          │  │
│  │  • Balance Sheet                                             │  │
│  │  • Cash Flow Statement                                       │  │
│  │                                                               │  │
│  │  Create FinancialStatement object with:                      │  │
│  │  • Standardized line items                                   │  │
│  │  • Numerical values with currency                            │  │
│  │  • Quality scores and confidence levels                      │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────┬────────────────────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│  📊 OUTPUT: Structured CSV Files                                     │
│                                                                       │
│  output/                                                             │
│  └─ ADYEN/                                                          │
│     └─ 2024/                                                        │
│        ├─ income_statement.csv                                      │
│        ├─ balance_sheet.csv                                         │
│        └─ cash_flow_statement.csv                                   │
│  └─ ASML/                                                           │
│     └─ 2024/                                                        │
│        ├─ income_statement.csv                                      │
│        ├─ balance_sheet.csv                                         │
│        └─ cash_flow_statement.csv                                   │
│                                                                       │
│  CSV Format:                                                         │
│  line_item,value,currency,year,category,ticker,found_in_document    │
│  Revenue,13652800000,EUR,2024,revenue,ADYEN,True                    │
│  Cost of Sales,4250000000,EUR,2024,costs,ADYEN,True                │
│  Gross Profit,9402800000,EUR,2024,profitability,ADYEN,True         │
└────────────────┬────────────────────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│  ✅ PROGRAM 4: CONSOLIDATION & VALIDATION                            │
│  ─────────────────────────────────────────────────────────────       │
│  1. Term Consolidation                                               │
│     └─ Merge similar terms (e.g., Revenue = Sales = Turnover)       │
│     └─ 300+ term mappings with fuzzy matching                       │
│     └─ Deduplication with value merging                             │
│                                                                       │
│  2. Data Quality Validation                                          │
│     └─ Check for missing values                                     │
│     └─ Validate mathematical consistency                            │
│     └─ Detect duplicates                                            │
│     └─ Quality scoring (0-100 scale)                                │
│                                                                       │
│  3. Generate Reports                                                 │
│     └─ Summary statistics                                            │
│     └─ Quality metrics per company/year                             │
│     └─ Issue tracking and recommendations                           │
└────────────────┬────────────────────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│  📊 FINAL OUTPUT: Consolidated & Validated Data                      │
│                                                                       │
│  consolidated_output/                                                │
│  ├─ consolidated_income_statement.csv                               │
│  ├─ consolidated_balance_sheet.csv                                  │
│  ├─ consolidated_cash_flow_statement.csv                            │
│  ├─ quality_summary.csv                                             │
│  └─ consolidation_summary.json                                      │
│                                                                       │
│  Quality Report Example:                                             │
│  {                                                                   │
│    "files_processed": 42,                                            │
│    "total_rows_before": 15000,                                       │
│    "total_rows_after": 8500,                                         │
│    "terms_consolidated": 6500,                                       │
│    "overall_quality_score": 87.5,                                    │
│    "quality_reports": [...]                                          │
│  }                                                                   │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  ✨ FINAL RESULT: Structured Financial Data Ready for Analysis       │
│                                                                       │
│  • 3 statement types per company/year                               │
│  • 300+ standardized financial line items                           │
│  • Quality scores and confidence levels                             │
│  • Multi-currency support (EUR, USD, GBP, etc.)                     │
│  • IFRS/US GAAP compliant                                           │
│  • Production-ready for financial analysis                          │
└─────────────────────────────────────────────────────────────────────┘
```

### The 4-Program Pipeline

| Program | Input | Output | Key Technology |
|---------|-------|--------|----------------|
| **Search Reports** | Company URLs | Ranked report list | Web crawling, ranking |
| **Process Reports** | Report URLs | Text content | PDF/XLSX extraction |
| **Transform Data** | Text content | Structured CSVs | 3 AI agents + JSON Schema |
| **Consolidate** | CSVs | Validated data | Term merging, QA scoring |

### Technology Stack
**Core:** Python 3.8+, Pandas, NumPy | **AI:** OpenAI GPT-4o (JSON Schema) | **Web:** BeautifulSoup4 | **PDF:** PyPDF2, pdfplumber | **Excel:** openpyxl

## 🧠 Key Innovations

### 🤖 Collaborative AI Agents

Three specialized agents work together:

```
Document Input
    ↓
┌─────────────────────────────┐
│ Financial Analyst Agent     │
│ - Chunk document            │
│ - Extract financial data    │
│ - Apply professional terms  │
│ - Assess confidence         │
└────────────┬────────────────┘
             ↓
┌─────────────────────────────┐
│ Reports Writer Agent        │
│ - Review extractions        │
│ - Validate quality          │
│ - Check consistency         │
│ - Assign quality scores     │
└────────────┬────────────────┘
             ↓
┌─────────────────────────────┐
│ QA Agent                    │
│ - Final verification        │
│ - Mathematical checks       │
│ - Completeness assessment   │
│ - Generate quality report   │
└────────────┬────────────────┘
             ↓
   Final Financial Statement
```

**Agent Roles:**
- **Financial Analyst** 📊 → Extracts data (IFRS/US GAAP expertise)
- **Reports Writer** ✍️ → Reviews quality (compliance, presentation)
- **QA Specialist** ✅ → Final verification (mathematical consistency, scoring)

### 🎯 Design Patterns

| Pattern | Benefit |
|---------|---------|
| **Pipeline Architecture** | Independent, testable, resilient modules |
| **Queue-Based Crawling** | Depth control, domain restriction, smart filtering |
| **Content Chunking** | 10K chars/chunk, 500 char overlap, memory efficient |
| **Smart Ranking** | XLSX > PDF, Form 20-F priority, auto best selection |
| **Schema-Driven** | Guaranteed structure, type safety, API validation |

### ⭐ Core Capabilities

- 🔍 **Auto-Discovery** - Finds reports automatically via web crawling
- 📄 **Multi-Format** - Handles PDF & XLSX with fallback strategies
- 🤖 **AI Extraction** - 3 collaborative agents for high accuracy
- ✅ **Quality Assured** - Multi-level validation (Extract → Review → Verify)
- 📊 **300+ Fields** - Comprehensive financial terminology mapping
- 🌍 **Standards** - IFRS/US GAAP, multi-currency support

## 📊 Technical Approach

### Content Chunking (Large Docs)
```python
Chunk 1: [0 - 10000 chars]
Chunk 2: [9500 - 19500] # 500 overlap preserves context
Chunk 3: [19000 - 29000] # Deduplicated when merging
```

### Extraction Flow
- **Context-Aware**: Each agent gets metadata, field mappings, quality expectations
- **Schema-Enforced**: JSON Schema ensures type safety, required fields, valid ranges
- **Adaptive**: Handles different structures, standards, currencies, languages

## 📁 Components

### Core Programs
- `processors/search_reports.py` - Discover & rank reports → `reports/annual_reports_ranked.json`
- `processors/process_reports.py` - Extract content from PDFs/XLSX → `processed_reports/*.txt`
- `processors/transform_statements.py` - AI extraction → `output/{ticker}/{year}/*.csv`
- `processors/consolidate_financial_data.py` - Quality assurance → `consolidated_output/*.csv`

### Supporting Packages
- `pkg/financial_agents.py` - 3 AI agents (Analyst, Writer, QA)
- `pkg/financial_schemas.py` - 300+ field mappings across 3 statement types
- `pkg/reports_ranker.py` - Multi-factor scoring for report selection
- `pkg/html_processor.py` - Queue-based web crawling

## 📊 Output Format

### Directory Structure
```
output/{ticker}/{year}/
  ├── income_statement.csv    # Revenue, costs, profitability
  ├── balance_sheet.csv       # Assets, liabilities, equity
  └── cash_flow_statement.csv # Operating, investing, financing
```

### CSV Columns
- `line_item`, `value`, `currency`, `year`, `category`, `ticker`, `found_in_document`

## 🚀 Usage

### Run Complete Pipeline
```bash
python main.py  # Executes all 4 programs
```

### Run Individual Programs
```bash
python processors/search_reports.py --input input.json --years-back 10
python processors/process_reports.py
python processors/transform_statements.py --input-folder processed_reports/
python processors/consolidate_financial_data.py
```

## 🏆 Highlights

- ✅ **Production-Ready** - Modular, testable, maintainable
- ✅ **Error Resilient** - Graceful handling, retry logic, detailed logging
- ✅ **Memory Efficient** - Chunk-based for large docs
- ✅ **Scalable** - Parallel processing capable
- ✅ **Professional** - IFRS/US GAAP, multi-currency, standard terminology

## 📝 Configuration

Edit `input.json`:
```json
[{
  "company_name": "Adyen",
  "ticker": "ADYEN",
  "reports_link": "https://investors.adyen.com/financials"
}]
```

Set environment: `OPENAI_API_KEY=your_key_here` in `.env`

---

**Authors:** Financial Data Engineering Team | **Version:** 1.0.0