"""Data models for OSS Check skill."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum


class Severity(str, Enum):
    """Finding severity levels."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class ComplianceStatus(str, Enum):
    """Compliance status for a component."""
    COMPLIANT = "compliant"
    COMPLIANT_RUNTIME = "compliant_runtime"
    TRANSLATED = "translated"
    NON_COMPLIANT = "non_compliant"


@dataclass
class Component:
    """Represents a single dependency component."""
    name: str
    version: str
    ecosystem: str
    manifest_file: str
    detected_endpoint: Optional[str] = None
    expected_endpoint: Optional[str] = None
    status: ComplianceStatus = ComplianceStatus.NON_COMPLIANT
    severity: Severity = Severity.HIGH
    runtime_evidence: bool = False
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "version": self.version,
            "ecosystem": self.ecosystem,
            "manifest_file": self.manifest_file,
            "detected_endpoint": self.detected_endpoint,
            "expected_endpoint": self.expected_endpoint,
            "status": self.status.value,
            "severity": self.severity.value,
            "runtime_evidence": self.runtime_evidence,
            "notes": self.notes,
        }


@dataclass
class Finding:
    """Represents a compliance finding."""
    component: Component
    message: str
    recommendation: str = ""
    affected_count: int = 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "component": self.component.to_dict(),
            "message": self.message,
            "recommendation": self.recommendation,
            "affected_count": self.affected_count,
        }


@dataclass
class ComplianceSummary:
    """Summary of compliance scan results."""
    total_components: int = 0
    compliant: int = 0
    compliant_runtime: int = 0
    translated: int = 0
    non_compliant: int = 0

    @property
    def compliance_percentage(self) -> float:
        """Calculate compliance percentage."""
        if self.total_components == 0:
            return 0.0
        compliant_total = self.compliant + self.compliant_runtime + self.translated
        return round((compliant_total / self.total_components) * 100, 2)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_components": self.total_components,
            "compliant": self.compliant,
            "compliant_runtime": self.compliant_runtime,
            "translated": self.translated,
            "non_compliant": self.non_compliant,
            "compliance_percentage": self.compliance_percentage,
        }


@dataclass
class ScanResult:
    """Complete scan result."""
    repository_name: str
    organization: str
    ref: str
    scan_timestamp: str
    summary: ComplianceSummary = field(default_factory=ComplianceSummary)
    components: List[Component] = field(default_factory=list)
    findings: List[Finding] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    jenkins_jobs_analyzed: int = 0
    runtime_configs_found: int = 0
    errors: List[str] = field(default_factory=list)
    verbose_details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "repository_name": self.repository_name,
            "organization": self.organization,
            "ref": self.ref,
            "scan_timestamp": self.scan_timestamp,
            "summary": self.summary.to_dict(),
            "components": [c.to_dict() for c in self.components],
            "findings": [f.to_dict() for f in self.findings],
            "recommendations": self.recommendations,
            "jenkins_jobs_analyzed": self.jenkins_jobs_analyzed,
            "runtime_configs_found": self.runtime_configs_found,
            "errors": self.errors,
            "verbose_details": self.verbose_details,
        }


@dataclass
class JenkinsJobInfo:
    """Information about a Jenkins job."""
    name: str
    url: str
    config_xml: Optional[str] = None
    last_build_number: Optional[int] = None
    registry_settings: Dict[str, str] = field(default_factory=dict)
    environment_variables: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "url": self.url,
            "last_build_number": self.last_build_number,
            "registry_settings": self.registry_settings,
            "environment_variables": self.environment_variables,
        }


@dataclass
class EcosystemManifest:
    """Represents a detected manifest file for an ecosystem."""
    ecosystem: str
    file_path: str
    content: str
    components: List[Component] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "ecosystem": self.ecosystem,
            "file_path": self.file_path,
            "component_count": len(self.components),
            "components": [c.to_dict() for c in self.components],
        }
