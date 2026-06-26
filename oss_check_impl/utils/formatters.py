from typing import Dict, Any


def format_terminal(report: Dict[str, Any], verbose: bool = False) -> str:
    s = []
    summary = report.get("summary", {})
    s.append("## OSS Compliance Summary")
    s.append(f"Total components: {summary.get('total_components', 0)}")
    s.append(f"Compliant: {summary.get('compliant', 0)}")
    s.append(f"Compliant (runtime): {summary.get('compliant_runtime', 0)}")
    s.append(f"Translated (Jenkins proxy): {summary.get('translated', 0)}")
    s.append(f"Non-compliant: {summary.get('non_compliant', 0)}")
    s.append(f"Compliance: {summary.get('compliance_percentage', 0.0)}%")
    if verbose:
        findings = report.get("findings", [])
        s.append("\nFindings (up to 20):")
        for f in findings[:20]:
            c = f.get("component", {})
            s.append(
                f"- {c.get('ecosystem')}: {c.get('name')}@{c.get('version')} "
                f"({c.get('manifest_file')}) — {f.get('message')}"
            )
    return "\n".join(s)


def format_markdown(report: Dict[str, Any], verbose: bool = False) -> str:
    s = []
    summary = report.get("summary", {})
    s.append("## OSS Compliance Summary\n")
    s.append("| Metric | Value |\n|---|---:|")
    s.append(f"| Total components | {summary.get('total_components', 0)} |")
    s.append(f"| Compliant | {summary.get('compliant', 0)} |")
    s.append(f"| Compliant (runtime) | {summary.get('compliant_runtime', 0)} |")
    s.append(f"| Translated (Jenkins proxy) | {summary.get('translated', 0)} |")
    s.append(f"| Non-compliant | {summary.get('non_compliant', 0)} |")
    s.append(f"| Compliance | {summary.get('compliance_percentage', 0.0)}% |\n")
    if verbose:
        findings = report.get("findings", [])
        s.append("### Findings (up to 50)\n")
        for f in findings[:50]:
            c = f.get("component", {})
            s.append(
                f"- `{c.get('ecosystem')}` {c.get('name')}@{c.get('version')} "
                f"(`{c.get('manifest_file')}`): {f.get('message')}"
            )
    return "\n".join(s)


def format_json(report: Dict[str, Any], verbose: bool = False) -> str:
    import json
    return json.dumps(report, indent=2)
