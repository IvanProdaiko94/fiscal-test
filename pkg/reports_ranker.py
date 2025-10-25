"""
Reports ranking and selection utilities.
"""

import logging
from typing import List, Dict, Any, Tuple

from .models import ExtractedDocument

logger = logging.getLogger(__name__)


class ReportsRanker:
    """Ranks and selects the best reports for each year."""
    
    def __init__(self):
        # Priority order for report types (highest to lowest)
        self.priority_keywords = [
            'form 20f', '20-f', '20f', 'form20f',
            'annual report', 'annual', 'yearly',
            'financial report', 'consolidated',
            'statements', 'accounts'
        ]
    
    def rank_reports_for_company(self, ticker: str, reports: List[ExtractedDocument]) -> Dict[int, List[Tuple[int, ExtractedDocument]]]:
        """Rank reports for a company by year, returning best and secondary reports."""
        if not reports:
            logger.warning(f"No reports found for {ticker}")
            return {}
        
        # Group reports by year
        reports_by_year = {}
        for report in reports:
            year = report.year
            if year:
                if year not in reports_by_year:
                    reports_by_year[year] = []
                reports_by_year[year].append(report)
        
        # Rank reports for each year
        ranked_reports = {}
        for year, year_reports in reports_by_year.items():
            ranked_year_reports = self._rank_reports_for_year(year_reports)
            ranked_reports[year] = ranked_year_reports
            logger.info(f"Ranked {len(year_reports)} reports for {ticker} {year}")
        
        return ranked_reports
    
    def _rank_reports_for_year(self, year_reports: List[ExtractedDocument]) -> List[Tuple[int, ExtractedDocument]]:
        """Rank reports for a specific year by quality score."""
        if not year_reports:
            return []
        
        # Score each report
        scored_reports = []
        for report in year_reports:
            score = self._calculate_report_score(report)
            scored_reports.append((score, report))
        
        # Sort by score (highest first)
        scored_reports.sort(key=lambda x: x[0], reverse=True)
        
        return scored_reports
    
    def _calculate_report_score(self, report: ExtractedDocument) -> int:
        """Calculate a quality score for a report."""
        title = report.title.lower()
        url = report.url.lower()
        
        score = 0
        
        # File type priority: XLSX > PDF
        if url.endswith('.xlsx'):
            score += 200  # High priority for XLSX files
        elif url.endswith('.pdf'):
            score += 100  # Medium priority for PDF files
        
        # Base score from priority keywords
        for i, keyword in enumerate(self.priority_keywords):
            if keyword in title or keyword in url:
                # Higher score for higher priority keywords
                score += (len(self.priority_keywords) - i) * 10
                break
        
        # Bonus points for specific indicators
        if 'form' in title and '20' in title:
            score += 50
        if 'annual' in title:
            score += 30
        if 'consolidated' in title:
            score += 20
        if 'financial' in title:
            score += 15
        if 'statements' in title:
            score += 10
        
        # Penalty for transparency/disclosure reports (they should rank lower than main annual reports)
        if 'transparency' in title or 'disclosure' in title:
            score -= 25  # Penalty for transparency/disclosure reports
        
        # Penalty for quarterly reports
        quarterly_keywords = ['q1', 'q2', 'q3', 'q4', 'quarterly', 'quarter']
        for keyword in quarterly_keywords:
            if keyword in title or keyword in url:
                score -= 100  # Heavy penalty for quarterly reports
        
        return score
    
    def select_best_reports(self, ranked_reports: Dict[int, List[Tuple[int, ExtractedDocument]]]) -> Dict[str, Any]:
        """Select the best and secondary reports from ranked reports, organized by year."""
        years_covered = sorted(ranked_reports.keys())
        reports = []
        
        for year in years_covered:
            ranked_year_reports = ranked_reports[year]
            if not ranked_year_reports:
                continue
            
            year_selection = {
                'year': year,
                'best': [],
                'secondary': []
            }
            
            # Best report (the highest score)
            if len(ranked_year_reports) >= 1:
                best_score, best_report = ranked_year_reports[0]
                year_selection['best'].append(best_report)
                logger.info(f"Selected best report for {year}: {best_report.title} (score: {best_score})")
            
            # Secondary reports (next 2 highest scores)
            if len(ranked_year_reports) >= 2:
                secondary_score, secondary_report = ranked_year_reports[1]
                year_selection['secondary'].append(secondary_report)
                logger.info(f"Selected secondary report for {year}: {secondary_report.title} (score: {secondary_score})")
            
            if len(ranked_year_reports) >= 3:
                secondary_score2, secondary_report2 = ranked_year_reports[2]
                year_selection['secondary'].append(secondary_report2)
                logger.info(f"Selected secondary report for {year}: {secondary_report2.title} (score: {secondary_score2})")
            
            reports.append(year_selection)
        
        return {
            'years_covered': years_covered,
            'reports': reports
        }
    
    def process_company_reports(self, ticker: str, reports: List[ExtractedDocument]) -> Dict[str, Any]:
        """Process reports for a company and return best and secondary selections organized by year."""
        logger.info(f"Ranking reports for {ticker}")
        
        # Rank reports by year
        ranked_reports = self.rank_reports_for_company(ticker, reports)
        
        # Select best and secondary reports
        selection = self.select_best_reports(ranked_reports)
        
        # Count total reports selected
        total_best = sum(len(year_data['best']) for year_data in selection['reports'])
        total_secondary = sum(len(year_data['secondary']) for year_data in selection['reports'])
        
        logger.info(f"Selected {total_best} best and {total_secondary} secondary reports for {ticker} across {len(selection['years_covered'])} years")
        
        return selection
    
    def create_selection_summary(self, all_selections: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Create a summary of all report selections."""
        summary = {
            "discovery_info": {
                "total_companies": len(all_selections),
                "total_best_reports": 0,
                "total_secondary_reports": 0,
                "description": "Best and secondary annual report selection prioritizing FORM 20F, organized by year"
            },
            "companies": {}
        }
        
        for ticker, selection in all_selections.items():
            years_covered = selection.get('years_covered', [])
            reports = selection.get('reports', [])
            
            # Count total reports
            total_best = sum(len(year_data['best']) for year_data in reports)
            total_secondary = sum(len(year_data['secondary']) for year_data in reports)
            
            summary["discovery_info"]["total_best_reports"] += total_best
            summary["discovery_info"]["total_secondary_reports"] += total_secondary
            
            # Create company data with year-organized structure
            company_data = {
                "ticker": ticker,
                "years_covered": years_covered,
                "total_best_reports": total_best,
                "total_secondary_reports": total_secondary,
                "reports": []
            }
            
            # Organize reports by year
            for year_data in reports:
                company_data["reports"].append({
                    "year": year_data['year'],
                    "best": [
                        {
                            "title": report.title,
                            "url": report.url
                        } for report in year_data['best']
                    ],
                    "secondary": [
                        {
                            "title": report.title,
                            "url": report.url
                        } for report in year_data['secondary']
                    ]
                })
            
            summary["companies"][ticker] = company_data
        
        return summary
