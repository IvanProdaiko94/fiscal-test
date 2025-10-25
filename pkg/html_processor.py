"""
HTML page processing and link discovery utilities.
"""

from typing import List, Optional, Dict, Set
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
import logging
from collections import deque

from .models import ExtractedDocument
from .http_client import HTTPClient

logger = logging.getLogger(__name__)


class HTMLPageProcessor:
    """Handles HTML page processing and link discovery using a queue-based approach."""
    
    def __init__(self):
        self.http_client = HTTPClient()
        
        # Queue-based processing
        self.url_queue = deque()  # URLs to process (url, depth)
        self.visited_urls: Set[str] = set()  # URLs we've already processed
        self.found_documents: List[ExtractedDocument] = []  # Documents we've found
        self.max_depth = 2  # Maximum depth for link following
        self.base_domain: Optional[str] = None  # Base domain to restrict crawling to
        
        # Paths to ignore (non-relevant for financial documents)
        self.ignore_paths = [
            '/careers', '/contact', '/contact-us', '/about', '/news', '/press',
            '/media', '/blog', '/support', '/help', '/faq', '/terms', '/privacy',
            '/legal', '/cookies', '/sitemap', '/search', '/login', '/register',
            '/account', '/profile', '/settings', '/cart', '/checkout', '/shop',
            '/store', '/products', '/services', '/solutions', '/technology',
            '/innovation', '/research', '/development', '/sustainability',
            '/environment', '/social', '/governance', '/esg', '/community',
            '/foundation', '/charity', '/donate', '/volunteer', '/events',
            '/webinar', '/conference', '/training', '/education', '/university',
            '/partnership', '/alliance', '/network', '/membership', '/awards',
            '/recognition', '/testimonials', '/case-study', '/success-story',
            '/gallery', '/photos', '/videos', '/podcast', '/webcast', '/live',
            '/stream', '/broadcast', '/tv', '/radio', '/magazine', '/newsletter',
            '/subscription', '/rss', '/feed', '/api/auth', '/api/user', '/api/login', '/developer', '/docs',
            '/documentation', '/guide', '/tutorial', '/manual', '/handbook',
            '/whitepaper', '/ebook', '/brochure', '/catalog', '/portfolio',
            '/showcase', '/demo', '/trial', '/free', '/premium', '/pro',
            '/enterprise', '/business', '/corporate', '/institutional'
        ]
        
        # Document-related substrings to prioritize
        self.document_substrings = [
            '/download', '/report', '/document', '/file', '/pdf', '/xlsx',
            '/annual', '/financial', '/statements', '/investor', '/archive',
            '/publication', '/publications', '/reports', '/documents'
        ]
        
        # Document-related keywords for link text matching
        self.document_keywords = [
            'download', 'report', 'document', 'annual', 'financial', 'pdf', 'xlsx'
        ]
        
        # Social media domains to skip
        self.social_domains = [
            'facebook.com', 'fb.com', 'instagram.com', 'twitter.com', 'x.com',
            'linkedin.com', 'youtube.com', 'youtu.be', 'tiktok.com', 'snapchat.com',
            'pinterest.com', 'reddit.com', 'telegram.org', 'whatsapp.com',
            'wechat.com', 'weibo.com', 'vk.com', 'tumblr.com', 'flickr.com', 'vimeo.com',
        ]
        
        # Social media keywords for link text matching
        self.social_keywords = [
            'facebook', 'instagram', 'twitter', 'linkedin', 'youtube',
            'follow us', 'like us', 'share', 'social media', 'connect with us'
        ]
        
        # Financial keywords for XLSX validation
        self.financial_keywords = [
            'financial', 'statements', 'accounts', 'report', 'data'
        ]
    
    def find_annual_reports(self, reports_url: str) -> List[ExtractedDocument]:
        """Find and extract annual report documents using queue-based processing."""
        try:
            # Initialize the queue with the initial URL
            self.url_queue.clear()
            self.visited_urls.clear()
            self.found_documents.clear()
            
            # Extract and set the base domain from the initial URL
            self.base_domain = self._extract_base_domain(reports_url)
            logger.info(f"Restricting crawling to base domain: {self.base_domain}")
            
            self.url_queue.append((reports_url, 0))  # Start with depth 0
            logger.info(f"Starting queue-based processing with initial URL: {reports_url} (max depth: {self.max_depth})")
            
            # Process the queue until it's empty
            while self.url_queue:
                current_url, current_depth = self.url_queue.popleft()
                
                # Skip if already visited
                if current_url in self.visited_urls:
                    logger.debug(f"Skipping already visited URL: {current_url}")
                    continue
                
                logger.info(f"Processing URL from queue: {current_url} (depth {current_depth}/{self.max_depth})")
                
                # Process the current URL
                self._process_url_from_queue(current_url, current_depth)
                
                # Mark as visited
                self.visited_urls.add(current_url)
            
            logger.info(f"Queue processing complete. Found {len(self.found_documents)} documents")
            return self.found_documents
            
        except Exception as e:
            logger.error(f"Error in queue-based processing: {e}")
            return []
    
    def _process_url_from_queue(self, url: str, current_depth: int) -> None:
        """Process a single URL from the queue."""
        try:
            # Get the page content
            response = self.http_client.make_request(url)
            if not response:
                logger.warning(f"Failed to get content for {url}, skipping")
                return
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Check headers for hidden documents first
            self._check_headers_for_documents(url)
            
            # Find direct document links on the page
            self._find_direct_documents(url, soup)
            
            # Find and validate links to add to queue (only if we haven't reached max depth)
            if current_depth < self.max_depth:
                self._find_and_queue_links(url, soup, current_depth)
            else:
                logger.debug(f"Reached max depth {self.max_depth}, not following links from {url}")
            
        except Exception as e:
            logger.error(f"Error processing URL {url}: {e}")
    
    def _check_headers_for_documents(self, url: str) -> None:
        """Check HTTP headers for hidden documents."""
        try:
            response = self.http_client.make_request(url)
            if not response:
                return

            for header in ['Content-Disposition', 'Content-Description']:
                # Check Content-Disposition header
                header_value = response.headers.get(header, '')
                if header_value:
                    filename = self._extract_filename_from_disposition(header_value)
                    if filename and self._is_annual_report(filename=filename):
                        year = self._extract_year_from_filename(filename)
                        doc = ExtractedDocument(
                            url=url,
                            title=filename,
                            content="",
                            year=year
                        )
                        self.found_documents.append(doc)
                        logger.info(f"Found document via headers: {filename}")
            
            # Check Content-Type header
            content_type = response.headers.get('Content-Type', '').lower()
            if 'pdf' in content_type or 'excel' in content_type or 'spreadsheet' in content_type:
                filename = self._extract_filename_from_url(url) or url.split('/')[-1]
                if self._is_annual_report(url=url, filename=filename):
                    year = self._extract_year_from_filename(filename) or self._extract_year_from_text(url)
                    doc = ExtractedDocument(
                        url=url,
                        title=filename,
                        content="",
                        year=year
                    )
                    self.found_documents.append(doc)
                    logger.info(f"Found document via Content-Type: {filename}")
        
        except Exception as e:
            logger.debug(f"Error checking headers for {url}: {e}")
    
    def _find_direct_documents(self, base_url: str, soup: BeautifulSoup) -> None:
        """Find direct PDF and XLSX links on the page."""
        # Find PDF and XLSX links
        pdf_links = soup.find_all('a', href=re.compile(r'\.pdf$', re.IGNORECASE))
        xlsx_links = soup.find_all('a', href=re.compile(r'\.xlsx$', re.IGNORECASE))
        
        logger.info(f"Found {len(pdf_links)} PDF links and {len(xlsx_links)} XLSX links on page")
        
        # Process PDF links
        for link in pdf_links:
            doc = self._process_document_link(link, base_url, 'PDF')
            if doc:
                self.found_documents.append(doc)
        
        # Process XLSX links
        for link in xlsx_links:
            doc = self._process_document_link(link, base_url, 'XLSX')
            if doc:
                self.found_documents.append(doc)
    
    def _find_and_queue_links(self, base_url: str, soup: BeautifulSoup, current_depth: int) -> None:
        """Find links on the page and add valid ones to the queue."""
        all_links = soup.find_all('a', href=True)
        logger.info(f"Found {len(all_links)} total links on page")
        
        next_depth = current_depth + 1
        
        for link in all_links:
            href = link.get('href')
            link_text = link.get_text(strip=True)
            
            if not href or not link_text:
                continue
            
            # Skip non-web links
            if href.lower().startswith(('mailto:', 'tel:', 'javascript:', '#')):
                continue
            
            # Skip social media links
            if self._is_social_media_link(href, link_text):
                continue
            
            # Convert to absolute URL
            link_url = urljoin(base_url, href)
            
            # Skip if not within the same base domain
            if not self._is_same_domain(link_url):
                logger.debug(f"Skipping external domain: {link_text} -> {link_url}")
                continue
            
            # Skip non-relevant URLs
            if self._should_skip_url(link_url):
                continue
            
            # Skip if already visited
            if link_url in self.visited_urls:
                continue
            
            # Skip if already in queue
            if any(url == link_url for url, _ in self.url_queue):
                continue
            
            # Add to queue for processing with incremented depth
            self.url_queue.append((link_url, next_depth))
            logger.debug(f"Added to queue: {link_text} -> {link_url} (depth {next_depth})")
    
    def _process_document_link(self, link, base_url: str, file_type: str) -> Optional[ExtractedDocument]:
        """Process a single document link (PDF or XLSX)."""
        href = link.get('href')
        if not href:
            return None
        
        # Convert relative URLs to absolute
        full_url = urljoin(base_url, href)
        
        # Skip if we've already found this document
        if any(doc.url == full_url for doc in self.found_documents):
            logger.debug(f"Skipping duplicate {file_type}: {full_url}")
            return None
        
        # Extract year from URL or link text
        year = self._extract_year_from_link(link, full_url)
        
        # Skip quarterly reports
        if self._is_quarter_report(link, full_url):
            logger.debug(f"Skipping quarterly report {file_type}: {href}")
            return None
        
        # Check if this looks like an annual report
        if self._is_annual_report(link=link, url=full_url):
            title = link.get_text(strip=True) or link.get('title', '')
            if title.lower().endswith(file_type.lower()):
                title = title[:-len(file_type)]
            
            logger.info(f"Found {file_type} annual report: {title} ({year}) - {full_url}")
            
            return ExtractedDocument(
                url=full_url,
                title=title,
                content="",
                year=year
            )
        else:
            logger.debug(f"Skipping non-annual report {file_type}: {href}")
            return None
    

    def _should_skip_url(self, url: str) -> bool:
        """Check if URL should be skipped based on non-relevant paths."""
        url_lower = url.lower()
        return any(ignore_path in url_lower for ignore_path in self.ignore_paths)
    
    def _is_social_media_link(self, href: str, link_text: str) -> bool:
        """Check if a link is a social media link that should be skipped."""
        href_lower = href.lower()
        text_lower = link_text.lower()
        
        # Check if URL contains social media domains
        for domain in self.social_domains:
            if domain in href_lower:
                return True
        
        # Check for social media keywords in the link text
        for keyword in self.social_keywords:
            if keyword in text_lower:
                return True
        
        return False
    
    def _extract_filename_from_disposition(self, disposition: str) -> Optional[str]:
        """Extract filename from Content-Disposition header."""
        import re
        
        # Look for filename= or filename*= patterns
        patterns = [
            r'filename\*?=["\']?([^"\';\s]+)',
            r'filename\*?=([^;\s]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, disposition, re.IGNORECASE)
            if match:
                filename = match.group(1).strip()
                # Remove quotes if present
                filename = filename.strip('"\'')
                return filename
        
        return None
    
    def _extract_filename_from_url(self, url: str) -> Optional[str]:
        """Extract filename from URL."""
        from urllib.parse import urlparse, unquote
        
        parsed = urlparse(url)
        path = unquote(parsed.path)
        
        # Get the last part of the path
        filename = path.split('/')[-1]
        
        # Check if it looks like a filename
        if '.' in filename and len(filename) > 3:
            return filename
        
        return None
    
    @staticmethod
    def _is_annual_report(text: str = None, url: str = None, filename: str = None, link=None) -> bool:
        """Check if text/URL/filename/link indicates an annual report."""
        # Handle different input types
        if link is not None:
            # Legacy support for link object
            text = link.get_text(strip=True)
            if url is None:
                url = link.get('href', '')

        if HTMLPageProcessor._is_quarter_report(link, url):
            return False
        
        # Also check filename for quarterly indicators
        if filename:
            filename_lower = filename.lower()
            for keyword in HTMLPageProcessor._get_quarterly_keywords():
                if keyword in filename_lower:
                    return False
        
        # Combine all text sources for analysis
        all_text = []
        if text:
            all_text.append(text.lower())
        if url:
            all_text.append(url.lower())
        if filename:
            all_text.append(filename.lower())
        
        # If filename is provided, check file extension first
        if filename:
            filename_lower = filename.lower()
            # Must be PDF or XLSX for filename-based checks
            if not (filename_lower.endswith('.pdf') or filename_lower.endswith('.xlsx')):
                return False
        
        # For URLs without visible extensions, check if they look like document endpoints
        # (e.g., /download, /api/asset, etc.)
        if url and not filename:
            url_lower = url.lower()
            if not (url_lower.endswith('.pdf') or url_lower.endswith('.xlsx')):
                return False
        
        # Comprehensive annual report keywords
        annual_keywords = HTMLPageProcessor._get_annual_keywords()
        
        # Check if any annual keywords are present in any text source
        for text_part in all_text:
            for keyword in annual_keywords:
                if keyword in text_part:
                    return True
        
        return False
    
    def _extract_year_from_filename(self, filename: str) -> Optional[int]:
        """Extract year from filename."""
        return HTMLPageProcessor._extract_year_from_text(filename)

    @staticmethod
    def _extract_year_from_text(text: str) -> Optional[int]:
        """Extract year from text."""
        import re
        
        # Find all potential years in the text
        year_matches = re.findall(r'(20\d{2})', text)
        
        if not year_matches:
            return None
        
        # Filter valid years (2000-2099)
        valid_years = [int(year) for year in year_matches if 2000 <= int(year) <= 2099]
        
        if not valid_years:
            return None
        
        # If we have multiple years, prefer the last occurrence (usually the report year)
        # Example: "20190326-CO-Investor_Relations-Annual_Report_2018-Document.pdf"
        # Date: 20190326, Report Year: 2018 -> return 2018
        if len(valid_years) > 1:
            # Return the last occurrence (usually the report year in the filename)
            return valid_years[-1]
        
        return valid_years[0]
    
    @staticmethod
    def _extract_year_from_link(link, url: str) -> Optional[int]:
        """Extract year from link text or URL."""
        # Try to find year in link text
        link_text = link.get_text(strip=True)
        year = HTMLPageProcessor._extract_year_from_text(link_text)
        if year:
            return year
        
        # Try to find year in URL
        return HTMLPageProcessor._extract_year_from_text(url)

    @staticmethod
    def _is_quarter_report(link, url: str) -> bool:
        """Determine if a link is likely a quarterly report."""
        link_text = link.get_text(strip=True).lower() if link else ""
        url_lower = url.lower() if url else ""

        # Check if any quarterly keywords are present
        for keyword in HTMLPageProcessor._get_quarterly_keywords():
            if keyword in link_text or keyword in url_lower:
                return True

        return False

    @staticmethod
    def _get_quarterly_keywords() -> List[str]:
        """Get the list of quarterly/half-yearly keywords."""
        return [
            'q1', 'q2', 'q3', 'q4',
            'h1', 'h2', 'h3', 'h4',
            'quarterly', 'quarter', 'half yearly',
            'half year', 'half-yearly', 'half-year', 'half',
        ]

    @staticmethod
    def _get_annual_keywords() -> List[str]:
        """Get the list of annual report keywords."""
        return [
            'annual', 'yearly', 'year-end', 'annual-report', 'annual_report', 'financial-report',
            'financial statements', 'consolidated', 'statements', 'integrated',
            'balance sheet', 'income statement', 'cash flow', 'profit and loss',
            'p&l', 'accounts', 'financial report', 'balance', 'income', 'cash',
            'profit', 'loss', 'sheet', 'flow', 'report', 'financial'
        ]
    
    def _extract_base_domain(self, url: str) -> str:
        """Extract the base domain from a URL."""
        from urllib.parse import urlparse
        
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # Remove port if present
        if ':' in domain:
            domain = domain.split(':')[0]
        
        # Extract base domain (e.g., 'example.com' from 'subdomain.example.com')
        parts = domain.split('.')
        if len(parts) >= 2:
            # Take the last two parts (domain.tld)
            base_domain = '.'.join(parts[-2:])
        else:
            base_domain = domain
        
        return base_domain
    
    def _is_same_domain(self, url: str) -> bool:
        """Check if a URL belongs to the same base domain."""
        if not self.base_domain:
            return True  # If no base domain set, allow all
        
        try:
            url_domain = self._extract_base_domain(url)
            return url_domain == self.base_domain
        except Exception:
            logger.debug(f"Error extracting domain from URL: {url}")
            return False

