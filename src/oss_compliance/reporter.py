"""
OSS Compliance Report Generator

Generates compliance reports in multiple formats (JSON, Markdown, Terminal).
"""

import json
from typing import Dict
from datetime import datetime


class ComplianceReporter:
    """
    Report generator for OSS compliance scanning results.
    
    Supports multiple output formats: terminal, JSON, Markdown.
    """
    
    def __init__(self):
        """Initialize the reporter."""
        pass
    
    def generate_report(self, scan_results: Dict, output_format: str = 'terminal') -> str:
        """
        Generate a compliance report in the specified format.
        
        Args:
            scan_results: Dictionary containing scan results
            output_format: Output format ('terminal', 'json', 'markdown')
        
        Returns:
            Formatted report as string
        """
        if output_format == 'json':
            return self.generate_json_report(scan_results)
        elif output_format == 'markdown':
            return self.generate_markdown_report(scan_results)
        elif output_format == 'terminal':
            return self.generate_terminal_report(scan_results)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")
    
    def generate_json_report(self, scan_results: Dict) -> str:
        """Generate JSON format report."""
        return json.dumps(scan_results, indent=2, default=str)
    
    def generate_markdown_report(self, scan_results: Dict) -> str:
        """Generate Markdown format report."""
        lines = []
        
        lines.append(f"# OSS Compliance Analysis Report")
        lines.append(f"")
        lines.append(f"**Repository:** {scan_results['repository_name']}")
        lines.append(f"**Scan Date:** {scan_results['scan_timestamp']}")
        lines.append(f"**Scan Type:** {scan_results['scan_type']}")
        lines.append(f"")
        lines.append(f"## Executive Summary")
        lines.append(f"")
        lines.append(f"- **Total Components:** {scan_results['total_components']}")
        lines.append(f"- **Compliant:** {scan_results['compliant_components']} ({scan_results['compliance_percentage']}%)")
        lines.append(f"- **Non-Compliant:** {scan_results['non_compliant_components']}")
        lines.append(f"")
        lines.append(f"## Component Analysis")
        lines.append(f"")
        lines.append(f"**Total Components:** {scan_results['total_components']}")
        lines.append(f"")
        
        # Break down by ecosystem
        ecosystem_counts = {}
        for mapping in scan_results.get('component_mappings', []):
            component = mapping.get('component', {})
            ecosystem = component.get('ecosystem', 'unknown')
            if mapping.get('compliance_status') == 'compliant':
                ecosystem_counts.setdefault(ecosystem, {'total': 0, 'compliant': 0, 'non_compliant': 0})
                ecosystem_counts[ecosystem]['compliant'] += 1
            else:
                ecosystem_counts.setdefault(ecosystem, {'total': 0, 'compliant': 0, 'non_compliant': 0})
                ecosystem_counts[ecosystem]['non_compliant'] += 1
            ecosystem_counts[ecosystem]['total'] += 1
        
        for ecosystem, counts in ecosystem_counts.items():
            lines.append(f"### {ecosystem.upper()} ({counts['total']} components)")
            lines.append(f"- **Total:** {counts['total']}")
            lines.append(f"- **Compliant:** {counts['compliant']}")
            lines.append(f"- **Non-Compliant:** {counts['non_compliant']}")
            lines.append(f"")
        
        lines.append(f"## Non-Compliant Components")
        lines.append(f"")
        
        non_compliant_components = [cm for cm in scan_results.get('component_mappings', []) 
                                   if cm.get('compliance_status') == 'non_compliant']
        
        for i, mapping in enumerate(non_compliant_components, 1):
            component = mapping.get('component', {})
            endpoint = mapping.get('actual_endpoint', {})
            lines.append(f"{i}. **{component.get('name', 'unknown')}**")
            lines.append(f"   - Ecosystem: {component.get('ecosystem', 'unknown')}")
            lines.append(f"   - Version: {component.get('version', 'unknown')}")
            lines.append(f"   - Source: {component.get('source_file', 'unknown')}")
            lines.append(f"   - Endpoint: {endpoint.get('url', 'unknown')}")
            lines.append(f"   - Type: {endpoint.get('type', 'unknown')}")
            lines.append(f"   - Recommendation: {mapping.get('recommendations', ['None'])[0] if mapping.get('recommendations') else 'None'}")
            lines.append(f"")
        
        return "\n".join(lines)
    
    def generate_terminal_report(self, scan_results: Dict) -> str:
        """Generate terminal-friendly report with ASCII art."""
        lines = []
        
        lines.append("=" * 70)
        lines.append("OSS Compliance Scan Results")
        lines.append("=" * 70)
        lines.append("")
        lines.append(f"Repository: {scan_results['repository_name']}")
        lines.append(f"Scan Type: {scan_results['scan_type']}")
        lines.append(f"Timestamp: {scan_results['scan_timestamp']}")
        lines.append("")
        lines.append("-" * 70)
        lines.append(f"Total Components: {scan_results['total_components']}")
        lines.append(f"Compliant: {scan_results['compliant_components']}")
        lines.append(f"Non-Compliant: {scan_results['non_compliant_components']}")
        lines.append(f"Compliance: {scan_results['compliance_percentage']}%")
        lines.append("-" * 70)
        lines.append("")
        
        # Severity breakdown based on component mappings
        severity_counts = {}
        for mapping in scan_results.get('component_mappings', []):
            endpoint = mapping.get('actual_endpoint', {})
            if not endpoint.get('compliant', True):
                severity = 'HIGH'  # Default to HIGH for non-compliant
            else:
                severity = 'INFO'
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        if severity_counts:
            lines.append("Findings by Severity:")
            for severity, count in sorted(severity_counts.items()):
                lines.append(f"  {severity}: {count}")
            lines.append("")
        
        # Top components (non-compliant)
        non_compliant_components = [cm for cm in scan_results.get('component_mappings', []) 
                                   if cm.get('compliance_status') == 'non_compliant']
        
        if non_compliant_components:
            lines.append("Top Non-Compliant Components:")
            for i, mapping in enumerate(non_compliant_components[:5], 1):
                component = mapping.get('component', {})
                lines.append(f"{i}. {component.get('name', 'unknown')} ({component.get('ecosystem', 'unknown')})")
            lines.append("")
        
        lines.append("=" * 70)
        
        return "\n".join(lines)