"""
Data Classification Module (NIST SP 800-60 / FIPS 199 Aligned)
==============================================================
System: Engram Context Ecology Platform
Author: Zimax Networks LC

Enterprise data classification based on:
- NIST SP 800-60: Guide for Mapping Types of Information
- FIPS 199: Standards for Security Categorization
- NIST AI RMF: AI Risk Management Framework

Classification is applied at ingestion time and stored as metadata
for RBAC, retention policies, and compliance reporting.
"""

import logging
from enum import Enum
from typing import List, Optional, Dict, Any, Set
from dataclasses import dataclass, field
from pathlib import Path
import re

logger = logging.getLogger(__name__)


class SensitivityLevel(Enum):
    """
    NIST SP 800-60 / FIPS 199 Impact Levels
    
    Based on potential impact to organizational operations, assets,
    or individuals if confidentiality is compromised.
    """
    HIGH = "high"
    """
    Severe or catastrophic adverse effect.
    Examples: Safety protocols, credentials, critical infrastructure specs
    Decay Rate: 0.01 (eternal retention)
    """
    
    MODERATE = "moderate"
    """
    Serious adverse effect.
    Examples: Business reports, contracts, internal procedures
    Decay Rate: 0.30
    """
    
    LOW = "low"
    """
    Limited adverse effect.
    Examples: Meeting notes, general communications, public docs
    Decay Rate: 0.80
    """


class DataCategory(Enum):
    """
    Data type categories for compliance mapping.
    """
    PII = "pii"           # Personally Identifiable Information
    PHI = "phi"           # Protected Health Information (HIPAA)
    CUI = "cui"           # Controlled Unclassified Information
    PCI = "pci"           # Payment Card Industry data
    PROPRIETARY = "prop"  # Business-sensitive/trade secrets
    SAFETY = "safety"     # Safety-critical information
    CREDENTIAL = "cred"   # Authentication/authorization data
    PUBLIC = "public"     # No restrictions
    INTERNAL = "internal" # General internal use


# Keyword patterns for automatic classification
SENSITIVITY_PATTERNS: Dict[SensitivityLevel, Set[str]] = {
    SensitivityLevel.HIGH: {
        # Safety and critical operations
        "safety", "hazard", "emergency", "critical", "lockout", "tagout",
        "iso 45001", "osha", "incident", "fatality",
        # Credentials and security
        "password", "credential", "secret", "api_key", "token", "private_key",
        "ssh", "certificate", "encryption",
        # Regulated data
        "hipaa", "phi", "ssn", "social security", "medical record",
        "pci", "credit card", "cvv", "cardholder",
    },
    SensitivityLevel.MODERATE: {
        # Business confidential
        "confidential", "proprietary", "internal only", "restricted",
        "trade secret", "nda", "contract", "agreement",
        # Technical specifications
        "specification", "datasheet", "schematic", "blueprint",
        "engineering", "technical manual", "procedure",
        # Financial
        "financial", "budget", "revenue", "forecast", "p&l",
    },
    SensitivityLevel.LOW: {
        # General content
        "meeting notes", "minutes", "agenda", "public",
        "press release", "announcement", "newsletter",
    },
}

CATEGORY_PATTERNS: Dict[DataCategory, Set[str]] = {
    DataCategory.PII: {
        "name", "email", "phone", "address", "date of birth", "dob",
        "employee id", "ssn", "social security", "passport", "driver license",
    },
    DataCategory.PHI: {
        "medical", "diagnosis", "treatment", "patient", "healthcare",
        "prescription", "lab result", "clinical", "hipaa",
    },
    DataCategory.PCI: {
        "credit card", "debit card", "cvv", "expiration", "cardholder",
        "payment", "transaction", "merchant",
    },
    DataCategory.SAFETY: {
        "safety", "hazard", "emergency", "lockout", "tagout", "ppe",
        "incident", "osha", "iso 45001", "risk assessment",
    },
    DataCategory.CREDENTIAL: {
        "password", "credential", "secret", "api key", "token",
        "private key", "certificate", "oauth",
    },
}


@dataclass
class ClassificationResult:
    """Result of data classification analysis."""
    sensitivity_level: SensitivityLevel
    categories: List[DataCategory]
    confidence: float  # 0.0 to 1.0
    matched_patterns: List[str] = field(default_factory=list)
    decay_rate: float = 0.80
    requires_encryption: bool = False
    retention_days: Optional[int] = None
    compliance_frameworks: List[str] = field(default_factory=list)
    
    def to_metadata(self) -> Dict[str, Any]:
        """Convert to metadata dict for storage."""
        return {
            "sensitivity_level": self.sensitivity_level.value,
            "data_categories": [c.value for c in self.categories],
            "classification_confidence": self.confidence,
            "decay_rate": self.decay_rate,
            "requires_encryption": self.requires_encryption,
            "retention_days": self.retention_days,
            "compliance_frameworks": self.compliance_frameworks,
            "nist_impact_level": self.sensitivity_level.value.upper(),
        }


class DataClassifier:
    """
    Classifies data based on content analysis and filename heuristics.
    
    Classification Strategy:
    1. Filename keywords (fast, first-pass)
    2. Content pattern matching (thorough)
    3. File type heuristics (fallback)
    
    Follows "high watermark" principle: if any indicator suggests
    HIGH sensitivity, the overall classification is HIGH.
    """
    
    # Decay rates by sensitivity
    DECAY_RATES = {
        SensitivityLevel.HIGH: 0.01,      # Eternal
        SensitivityLevel.MODERATE: 0.30,  # Months
        SensitivityLevel.LOW: 0.80,       # Days
    }
    
    # Retention periods (days) by sensitivity
    RETENTION_DAYS = {
        SensitivityLevel.HIGH: 2555,     # 7 years
        SensitivityLevel.MODERATE: 365,  # 1 year
        SensitivityLevel.LOW: 90,        # 3 months
    }
    
    def __init__(self):
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Pre-compile regex patterns for efficiency."""
        self._sensitivity_regex = {}
        for level, keywords in SENSITIVITY_PATTERNS.items():
            pattern = "|".join(re.escape(k) for k in keywords)
            self._sensitivity_regex[level] = re.compile(pattern, re.IGNORECASE)
        
        self._category_regex = {}
        for category, keywords in CATEGORY_PATTERNS.items():
            pattern = "|".join(re.escape(k) for k in keywords)
            self._category_regex[category] = re.compile(pattern, re.IGNORECASE)
    
    def classify(
        self,
        filename: str,
        content: Optional[str] = None,
        file_extension: Optional[str] = None,
        explicit_level: Optional[SensitivityLevel] = None,
    ) -> ClassificationResult:
        """
        Classify data based on available information.
        
        Args:
            filename: Name of the file
            content: Optional text content for deep analysis
            file_extension: File extension (if not in filename)
            explicit_level: User-specified override
            
        Returns:
            ClassificationResult with sensitivity and categories
        """
        if explicit_level:
            # User override - trust but verify categories
            return self._build_result(
                explicit_level,
                self._detect_categories(filename, content),
                confidence=1.0,
                matched_patterns=["user_override"],
            )
        
        matched_patterns = []
        detected_level = SensitivityLevel.LOW
        
        # Filename analysis
        filename_lower = filename.lower()
        
        # Check for HIGH indicators first (high watermark principle)
        for level in [SensitivityLevel.HIGH, SensitivityLevel.MODERATE, SensitivityLevel.LOW]:
            if self._sensitivity_regex[level].search(filename_lower):
                if level.value < detected_level.value or detected_level == SensitivityLevel.LOW:
                    detected_level = level
                    matched_patterns.extend(
                        m.group() for m in self._sensitivity_regex[level].finditer(filename_lower)
                    )
                break
        
        # Content analysis (if provided)
        if content:
            content_level, content_patterns = self._analyze_content(content)
            # High watermark: take highest level
            if self._level_priority(content_level) > self._level_priority(detected_level):
                detected_level = content_level
            matched_patterns.extend(content_patterns)
        
        # Detect categories
        categories = self._detect_categories(filename, content)
        
        # Calculate confidence
        confidence = min(1.0, 0.5 + (len(matched_patterns) * 0.1))
        
        return self._build_result(detected_level, categories, confidence, matched_patterns)
    
    def _analyze_content(self, content: str) -> tuple[SensitivityLevel, List[str]]:
        """Analyze content for sensitivity indicators."""
        content_lower = content.lower()[:10000]  # Limit analysis scope
        matched = []
        
        for level in [SensitivityLevel.HIGH, SensitivityLevel.MODERATE]:
            matches = self._sensitivity_regex[level].findall(content_lower)
            if matches:
                matched.extend(matches[:5])  # Limit pattern count
                return level, matched
        
        return SensitivityLevel.LOW, matched
    
    def _detect_categories(
        self,
        filename: str,
        content: Optional[str],
    ) -> List[DataCategory]:
        """Detect applicable data categories."""
        categories = set()
        text = filename.lower()
        if content:
            text += " " + content.lower()[:5000]
        
        for category, regex in self._category_regex.items():
            if regex.search(text):
                categories.add(category)
        
        # Default to INTERNAL if no specific category
        if not categories:
            categories.add(DataCategory.INTERNAL)
        
        return list(categories)
    
    def _level_priority(self, level: SensitivityLevel) -> int:
        """Priority score for high-watermark comparison."""
        return {"high": 3, "moderate": 2, "low": 1}[level.value]
    
    def _build_result(
        self,
        level: SensitivityLevel,
        categories: List[DataCategory],
        confidence: float,
        matched_patterns: List[str],
    ) -> ClassificationResult:
        """Build classification result with computed fields."""
        # Determine compliance frameworks
        frameworks = []
        if DataCategory.PHI in categories:
            frameworks.append("HIPAA")
        if DataCategory.PCI in categories:
            frameworks.append("PCI-DSS")
        if DataCategory.CUI in categories:
            frameworks.append("NIST 800-171")
        if DataCategory.SAFETY in categories:
            frameworks.append("ISO 45001")
        if level == SensitivityLevel.HIGH:
            frameworks.append("NIST SP 800-60")
        
        return ClassificationResult(
            sensitivity_level=level,
            categories=categories,
            confidence=confidence,
            matched_patterns=list(set(matched_patterns))[:10],
            decay_rate=self.DECAY_RATES[level],
            requires_encryption=level == SensitivityLevel.HIGH,
            retention_days=self.RETENTION_DAYS[level],
            compliance_frameworks=frameworks,
        )
    
    def classify_by_extension(self, extension: str) -> SensitivityLevel:
        """
        Default classification hints by file extension.
        These are overridden by content/filename analysis.
        """
        extension = extension.lower().lstrip(".")
        
        # High sensitivity extensions
        if extension in {"pem", "key", "p12", "pfx", "crt", "csr"}:
            return SensitivityLevel.HIGH
        
        # Moderate (technical/business docs)
        if extension in {"pdf", "docx", "xlsx", "pptx"}:
            return SensitivityLevel.MODERATE
        
        return SensitivityLevel.LOW


# Singleton instance
data_classifier = DataClassifier()


# Convenience function for router integration
def classify_document(
    filename: str,
    content: Optional[str] = None,
    explicit_level: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Classify a document and return metadata dict.
    
    Args:
        filename: Name of the file
        content: Optional text content
        explicit_level: Optional user override ("high", "moderate", "low")
        
    Returns:
        Dict with classification metadata
    """
    level = None
    if explicit_level:
        level = SensitivityLevel(explicit_level.lower())
    
    result = data_classifier.classify(filename, content, explicit_level=level)
    return result.to_metadata()
