#!/usr/bin/env python3
"""
Financial Data Extraction Pipeline - Master Orchestrator

This comprehensive script orchestrates the complete financial data extraction pipeline:
1. Search for annual reports on company websites
2. Download and process PDFs and XLSX files
3. Transform documents to structured financial statements using AI agents
4. Consolidate and verify financial data quality

The pipeline processes multiple companies and generates standardized CSV outputs
with comprehensive financial data suitable for analysis and reporting.
"""

import subprocess
import sys
import os
import logging
import json
import time
import argparse
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from dotenv import load_dotenv

# Configure comprehensive logging
def setup_logging(log_level: str = "INFO", log_file: str = "financial_pipeline.log") -> logging.Logger:
    """Set up comprehensive logging configuration."""
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s'
    )
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # File handler with detailed format
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(detailed_formatter)
    
    # Console handler with simple format
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(simple_formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    root_logger.handlers.clear()
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    return root_logger

logger = logging.getLogger(__name__)


class PipelineConfig:
    """Configuration management for the financial data pipeline."""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config = self._load_default_config()
        if config_file and os.path.exists(config_file):
            self._load_config_file(config_file)
        self._validate_config()
    
    def _load_default_config(self) -> Dict:
        """Load default configuration."""
        return {
            "input_file": "input.json",
            "output_directories": {
                "reports": "reports",
                "processed_reports": "processed_reports", 
                "output": "output",
                "consolidated_output": "consolidated_output"
            },
            "search_settings": {
                "years_back": 10,
                "verbose": False
            },
            "processing_settings": {
                "max_retries": 3,
                "retry_delay": 5,
                "timeout": 300
            },
            "ai_settings": {
                "model": "gpt-4",
                "temperature": 0.1,
                "max_tokens": 4000
            }
        }
    
    def _load_config_file(self, config_file: str):
        """Load configuration from JSON file."""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                file_config = json.load(f)
            self.config.update(file_config)
            logger.info(f"Loaded configuration from {config_file}")
        except Exception as e:
            logger.warning(f"Failed to load config file {config_file}: {e}")
    
    def _validate_config(self):
        """Validate configuration values."""
        required_dirs = ["reports", "processed_reports", "output", "consolidated_output"]
        for dir_name in required_dirs:
            if dir_name not in self.config["output_directories"]:
                logger.warning(f"Missing output directory configuration: {dir_name}")
    
    def get(self, key: str, default=None):
        """Get configuration value with dot notation support."""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value


class PipelineExecutor:
    """Executes the financial data extraction pipeline with comprehensive error handling."""
    
    def __init__(self, config: PipelineConfig):
        self.config = config
        self.start_time = None
        self.program_results = {}
        self.stats = {
            "total_programs": 4,
            "successful_programs": 0,
            "failed_programs": 0,
            "total_runtime": 0,
            "program_runtimes": {}
        }
    
    def check_prerequisites(self) -> Tuple[bool, List[str]]:
        """Check all prerequisites and return (success, error_messages)."""
        logger.info("🔍 Checking prerequisites...")
        errors = []
        
        # Check input file
        input_file = self.config.get("input_file")
        if not os.path.exists(input_file):
            errors.append(f"Input file not found: {input_file}")
        
        # Check .env file
        if not os.path.exists('.env'):
            errors.append(".env file not found. Please create it from example.env")
        
        # Check OpenAI API key
        load_dotenv()
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if not openai_api_key or openai_api_key == 'your_openai_api_key_here':
            errors.append("OPENAI_API_KEY not set in .env file")
        
        # Check Python dependencies
        try:
            import pandas
            import requests
            import openai
            logger.info("✓ Python dependencies verified")
        except ImportError as e:
            errors.append(f"Missing Python dependency: {e}")
        
        # Check output directories
        for dir_name, dir_path in self.config.get("output_directories", {}).items():
            try:
                os.makedirs(dir_path, exist_ok=True)
                logger.info(f"✓ Output directory ready: {dir_path}")
            except Exception as e:
                errors.append(f"Cannot create output directory {dir_path}: {e}")
        
        if errors:
            logger.error("❌ Prerequisites check failed:")
            for error in errors:
                logger.error(f"  • {error}")
            return False, errors
        else:
            logger.info("✅ All prerequisites met")
            return True, []
    
    def run_program(self, program_name: str, script_path: str, *args, **kwargs) -> Tuple[bool, Dict]:
        """Run a single program with comprehensive error handling and monitoring."""
        logger.info(f"🚀 Starting {program_name}...")
        program_start_time = time.time()
        
        result = {
            "success": False,
            "runtime": 0,
            "exit_code": None,
            "stdout": "",
            "stderr": "",
            "error": None
        }
        
        try:
            # Check if script exists
            if not os.path.exists(script_path):
                error_msg = f"Script not found: {script_path}"
                logger.error(f"❌ {error_msg}")
                result["error"] = error_msg
                return False, result
            
            # Prepare command
            cmd = [sys.executable, script_path] + list(args)
            logger.debug(f"Executing command: {' '.join(cmd)}")
            
            # Run with timeout
            timeout = self.config.get("processing_settings.timeout", 300)
            process_result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False  # Don't raise exception on non-zero exit
            )
            
            result["exit_code"] = process_result.returncode
            result["stdout"] = process_result.stdout
            result["stderr"] = process_result.stderr
            result["runtime"] = time.time() - program_start_time
            
            if process_result.returncode == 0:
                logger.info(f"✅ {program_name} completed successfully in {result['runtime']:.1f}s")
                result["success"] = True
                if process_result.stdout.strip():
                    logger.debug(f"Output: {process_result.stdout.strip()}")
            else:
                logger.error(f"❌ {program_name} failed with exit code {process_result.returncode}")
                if process_result.stderr.strip():
                    logger.error(f"Error output: {process_result.stderr.strip()}")
                result["success"] = False
            
        except subprocess.TimeoutExpired:
            error_msg = f"Program timed out after {timeout} seconds"
            logger.error(f"⏰ {program_name} {error_msg}")
            result["error"] = error_msg
            result["runtime"] = time.time() - program_start_time
            
        except Exception as e:
            error_msg = f"Unexpected error: {e}"
            logger.error(f"💥 {program_name} failed with exception: {error_msg}")
            result["error"] = error_msg
            result["runtime"] = time.time() - program_start_time
        
        return result["success"], result
    
    def execute_pipeline(self, resume_from: Optional[int] = None) -> bool:
        """Execute the complete pipeline with optional resume capability."""
        self.start_time = time.time()
        
        logger.info("🎯 Starting Financial Data Extraction Pipeline")
        logger.info("=" * 80)
        logger.info(f"Pipeline started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Configuration: {json.dumps(self.config.config, indent=2)}")
        
        # Check prerequisites
        prereq_success, prereq_errors = self.check_prerequisites()
        if not prereq_success:
            logger.error("❌ Prerequisites not met. Pipeline aborted.")
            return False
        
        # Define programs with their configurations
        programs = [
            {
                "name": "Program 1: Annual Report Search",
                "script": "processors/search_reports.py",
                "args": [
                    "--input", self.config.get("input_file"),
                    "--output", self.config.get("output_directories.reports"),
                    "--years-back", str(self.config.get("search_settings.years_back"))
                ],
                "description": "Discovers annual report PDF links on company websites"
            },
            {
                "name": "Program 2: Report Download and Processing", 
                "script": "processors/process_reports.py",
                "args": [],
                "description": "Downloads and extracts text from PDF and XLSX documents"
            },
            {
                "name": "Program 3: Financial Statement Transformation",
                "script": "processors/transform_statements.py", 
                "args": [
                    "--input-folder", self.config.get("output_directories.processed_reports"),
                    "--output-folder", self.config.get("output_directories.output")
                ],
                "description": "Transforms documents to structured financial statements using AI agents"
            },
            {
                "name": "Program 4: Financial Data Consolidation and Verification",
                "script": "processors/consolidate_financial_data.py",
                "args": [
                    self.config.get("output_directories.output"),
                    "--output-dir", self.config.get("output_directories.consolidated_output")
                ],
                "description": "Consolidates terms and validates data quality"
            }
        ]
        
        # Execute programs
        start_index = resume_from or 0
        for i, program in enumerate(programs[start_index:], start=start_index):
            logger.info(f"\n{'='*25} {program['name']} {'='*25}")
            logger.info(f"Description: {program['description']}")
            
            success, result = self.run_program(
                program['name'], 
                program['script'], 
                *program['args']
            )
            
            # Store results
            self.program_results[i] = {
                "program": program['name'],
                "success": success,
                "result": result
            }
            
            # Update statistics
            if success:
                self.stats["successful_programs"] += 1
            else:
                self.stats["failed_programs"] += 1
            
            self.stats["program_runtimes"][program['name']] = result["runtime"]
            
            # Stop pipeline on failure unless resume is enabled
            if not success and not resume_from:
                logger.error(f"🛑 Pipeline stopped due to failure in {program['name']}")
                break
        
        # Calculate total runtime
        self.stats["total_runtime"] = time.time() - self.start_time
        
        # Generate final report
        self._generate_final_report()
        
        return self.stats["successful_programs"] == self.stats["total_programs"]
    
    def _generate_final_report(self):
        """Generate comprehensive final report."""
        logger.info("\n" + "=" * 80)
        logger.info("📊 PIPELINE EXECUTION REPORT")
        logger.info("=" * 80)
        
        # Overall statistics
        logger.info(f"Total programs: {self.stats['total_programs']}")
        logger.info(f"Successful: {self.stats['successful_programs']}")
        logger.info(f"Failed: {self.stats['failed_programs']}")
        logger.info(f"Success rate: {(self.stats['successful_programs']/self.stats['total_programs']*100):.1f}%")
        logger.info(f"Total runtime: {self.stats['total_runtime']:.1f} seconds")
        
        # Program details
        logger.info("\n📋 Program Execution Details:")
        for i, (program_name, result) in self.program_results.items():
            status = "✅ SUCCESS" if result["success"] else "❌ FAILED"
            runtime = result["result"]["runtime"]
            logger.info(f"  {i+1}. {program_name}: {status} ({runtime:.1f}s)")
            
            if not result["success"] and result["result"]["error"]:
                logger.info(f"     Error: {result['result']['error']}")
        
        # Output locations
        if self.stats["successful_programs"] > 0:
            logger.info("\n📁 Output Files Generated:")
            output_dirs = self.config.get("output_directories", {})
            for dir_name, dir_path in output_dirs.items():
                if os.path.exists(dir_path):
                    file_count = len([f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f))])
                    logger.info(f"  • {dir_name}/: {file_count} files")
        
        # Log files
        logger.info("\n📝 Log Files Created:")
        log_files = [
            "financial_pipeline.log",
            "search_reports.log", 
            "process_reports.log",
            "transform_statements.log",
            "consolidation.log"
        ]
        for log_file in log_files:
            if os.path.exists(log_file):
                logger.info(f"  • {log_file}")
        
        # Save detailed report to JSON
        report_data = {
            "pipeline_execution": {
                "start_time": datetime.fromtimestamp(self.start_time).isoformat(),
                "end_time": datetime.now().isoformat(),
                "total_runtime": self.stats["total_runtime"],
                "success_rate": self.stats["successful_programs"] / self.stats["total_programs"] * 100
            },
            "program_results": self.program_results,
            "statistics": self.stats,
            "configuration": self.config.config
        }
        
        report_file = f"pipeline_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"\n📄 Detailed report saved to: {report_file}")


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Financial Data Extraction Pipeline - Master Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                                    # Run complete pipeline
  python main.py --config config.json              # Use custom configuration
  python main.py --resume-from 2                    # Resume from program 3
  python main.py --log-level DEBUG                  # Enable debug logging
  python main.py --years-back 5                     # Search 5 years back
        """
    )
    
    parser.add_argument(
        '--config', '-c',
        type=str,
        help='Path to configuration JSON file'
    )
    
    parser.add_argument(
        '--resume-from',
        type=int,
        choices=[0, 1, 2, 3],
        help='Resume pipeline from specific program (0-3)'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Set logging level (default: INFO)'
    )
    
    parser.add_argument(
        '--years-back',
        type=int,
        help='Number of years back to search for reports'
    )
    
    parser.add_argument(
        '--input-file',
        type=str,
        help='Path to input JSON file with company data'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    return parser.parse_args()


def main():
    """Main entry point for the financial data extraction pipeline."""
    args = parse_arguments()
    
    # Set up logging
    log_level = "DEBUG" if args.verbose else args.log_level
    logger = setup_logging(log_level)
    
    try:
        # Initialize configuration
        config = PipelineConfig(args.config)
        
        # Override config with command line arguments
        if args.years_back:
            config.config["search_settings"]["years_back"] = args.years_back
        if args.input_file:
            config.config["input_file"] = args.input_file
        
        # Initialize and execute pipeline
        executor = PipelineExecutor(config)
        success = executor.execute_pipeline(resume_from=args.resume_from)
        
        if success:
            logger.info("🎉 Pipeline completed successfully!")
            return 0
        else:
            logger.error("💥 Pipeline failed!")
            return 1
            
    except KeyboardInterrupt:
        logger.warning("⚠️ Pipeline interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"💥 Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
