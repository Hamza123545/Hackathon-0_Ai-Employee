"""
Cross-Domain Classifier (Gold Tier)

Rule-based classifier for determining action item domain (personal, business, accounting, social_media).
"""

import re
from pathlib import Path
from typing import Literal, Optional

DomainType = Literal["personal", "business", "accounting", "social_media"]


class Classifier:
    """
    Classifies action items by domain using rules from Company_Handbook.md.
    
    Domains:
    - personal: Personal emails, messages, tasks
    - business: Business communications, partnerships, sales
    - accounting: Financial transactions, invoices, expenses
    - social_media: Social media posts, engagement tracking
    """
    
    def __init__(self, handbook_path: Optional[Path] = None):
        """
        Initialize Classifier.
        
        Args:
            handbook_path: Path to Company_Handbook.md. If None, searches in vault.
        """
        self.handbook_path = handbook_path
        self.rules = self._load_rules()
    
    def _load_rules(self) -> dict[str, list[dict]]:
        """
        Load classification rules from Company_Handbook.md.
        
        Returns:
            Dictionary mapping domain to list of rule dictionaries
        """
        if self.handbook_path is None:
            # Try to find Company_Handbook.md in common locations
            from .config import Config
            config = Config()
            handbook_path = config.vault_path / "Company_Handbook.md"
        else:
            handbook_path = Path(self.handbook_path)
        
        if not handbook_path.exists():
            # Return default rules if handbook not found
            return self._get_default_rules()
        
        # Parse Company_Handbook.md for domain rules
        rules = {
            "personal": [],
            "business": [],
            "accounting": [],
            "social_media": []
        }
        
        try:
            content = handbook_path.read_text(encoding='utf-8')
            
            # Extract domain-specific rules from handbook
            # Look for sections like "## Personal Domain Rules" or "## Business Domain Rules"
            domain_sections = {
                "personal": r"##\s*Personal\s+Domain\s+Rules?",
                "business": r"##\s*Business\s+Domain\s+Rules?",
                "accounting": r"##\s*Accounting\s+Domain\s+Rules?",
                "social_media": r"##\s*Social\s+Media\s+Domain\s+Rules?"
            }
            
            for domain, pattern in domain_sections.items():
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    # Extract rules from this section until next ##
                    section_start = match.end()
                    next_section = re.search(r"^##\s+", content[section_start:], re.MULTILINE)
                    section_end = section_start + (next_section.start() if next_section else len(content))
                    section_content = content[section_start:section_end]
                    
                    # Extract keywords and patterns from section
                    rules[domain] = self._parse_section_rules(section_content)
        except Exception as e:
            # If parsing fails, use default rules
            print(f"Warning: Failed to parse Company_Handbook.md: {e}")
            return self._get_default_rules()
        
        return rules
    
    def _parse_section_rules(self, section_content: str) -> list[dict]:
        """
        Parse rules from a section of Company_Handbook.md.
        
        Args:
            section_content: Content of the section
        
        Returns:
            List of rule dictionaries with 'type' (keyword/pattern) and 'value'
        """
        rules = []
        
        # Look for keywords (e.g., "- invoice", "- expense", "- payment")
        keyword_pattern = r"[-*]\s*([a-zA-Z0-9\s]+)"
        keywords = re.findall(keyword_pattern, section_content)
        for keyword in keywords:
            keyword = keyword.strip().lower()
            if keyword:
                rules.append({"type": "keyword", "value": keyword})
        
        # Look for regex patterns (e.g., "pattern: .*invoice.*")
        pattern_pattern = r"pattern:\s*(.+?)(?:\n|$)"
        patterns = re.findall(pattern_pattern, section_content, re.IGNORECASE)
        for pattern in patterns:
            pattern = pattern.strip()
            if pattern:
                rules.append({"type": "pattern", "value": pattern})
        
        return rules
    
    def _get_default_rules(self) -> dict[str, list[dict]]:
        """
        Get default classification rules if Company_Handbook.md is not available.
        
        Returns:
            Dictionary mapping domain to list of rule dictionaries
        """
        return {
            "accounting": [
                {"type": "keyword", "value": "invoice"},
                {"type": "keyword", "value": "expense"},
                {"type": "keyword", "value": "payment"},
                {"type": "keyword", "value": "receipt"},
                {"type": "keyword", "value": "xero"},
                {"type": "keyword", "value": "accounting"},
                {"type": "keyword", "value": "financial"},
                {"type": "pattern", "value": r"\$\d+\.?\d*"},  # Dollar amounts
                {"type": "pattern", "value": r"paid\s+\$"},  # "Paid $X"
            ],
            "social_media": [
                {"type": "keyword", "value": "facebook"},
                {"type": "keyword", "value": "instagram"},
                {"type": "keyword", "value": "twitter"},
                {"type": "keyword", "value": "post"},
                {"type": "keyword", "value": "engagement"},
                {"type": "keyword", "value": "social media"},
                {"type": "keyword", "value": "hashtag"},
            ],
            "business": [
                {"type": "keyword", "value": "partnership"},
                {"type": "keyword", "value": "client"},
                {"type": "keyword", "value": "customer"},
                {"type": "keyword", "value": "sales"},
                {"type": "keyword", "value": "business"},
                {"type": "keyword", "value": "meeting"},
                {"type": "keyword", "value": "proposal"},
            ],
            "personal": [
                # Personal is the default fallback
            ]
        }
    
    def classify(
        self,
        title: str,
        content: str = "",
        source: str = "",
        metadata: Optional[dict] = None
    ) -> DomainType:
        """
        Classify an action item by domain.
        
        Args:
            title: Action item title
            content: Action item content/description
            source: Source of action item (gmail, whatsapp, linkedin, etc.)
            metadata: Additional metadata
        
        Returns:
            Domain type: "personal", "business", "accounting", or "social_media"
        """
        # Combine title and content for analysis
        text = f"{title} {content}".lower()
        
        # Check each domain in priority order (accounting > social_media > business > personal)
        for domain in ["accounting", "social_media", "business", "personal"]:
            if self._matches_domain(text, domain, source, metadata):
                return domain
        
        # Default to personal if no match
        return "personal"
    
    def _matches_domain(
        self,
        text: str,
        domain: DomainType,
        source: str,
        metadata: Optional[dict]
    ) -> bool:
        """
        Check if text matches rules for a given domain.
        
        Args:
            text: Text to analyze (lowercase)
            domain: Domain to check
            source: Source of action item
            metadata: Additional metadata
        
        Returns:
            True if text matches domain rules
        """
        rules = self.rules.get(domain, [])
        
        # If no rules for this domain, return False (except for personal which is default)
        if not rules and domain != "personal":
            return False
        
        # Check each rule
        for rule in rules:
            rule_type = rule.get("type")
            rule_value = rule.get("value", "").lower()
            
            if rule_type == "keyword":
                # Check if keyword appears in text
                if rule_value in text:
                    return True
            elif rule_type == "pattern":
                # Check if regex pattern matches
                try:
                    if re.search(rule_value, text, re.IGNORECASE):
                        return True
                except re.error:
                    # Invalid regex pattern, skip
                    continue
        
        # Special case: personal domain is default fallback
        if domain == "personal":
            return True
        
        return False
    
    def classify_file(self, file_path: Path) -> DomainType:
        """
        Classify an action item file by reading its content.
        
        Args:
            file_path: Path to action item file
        
        Returns:
            Domain type
        """
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Extract title from frontmatter or first line
            title = ""
            if content.startswith("---"):
                # Has frontmatter
                frontmatter_end = content.find("---", 3)
                if frontmatter_end > 0:
                    frontmatter = content[3:frontmatter_end]
                    title_match = re.search(r"title:\s*(.+)", frontmatter, re.IGNORECASE)
                    if title_match:
                        title = title_match.group(1).strip()
                    content = content[frontmatter_end + 3:].strip()
            
            # If no title from frontmatter, use first line
            if not title:
                first_line = content.split("\n")[0].strip()
                title = first_line.lstrip("#").strip()
            
            # Extract source from filename or metadata
            source = file_path.stem.split("-")[-1] if "-" in file_path.stem else ""
            
            return self.classify(title, content, source)
        except Exception as e:
            print(f"Warning: Failed to classify file {file_path}: {e}")
            return "personal"


# Default classifier instance
default_classifier = Classifier()

