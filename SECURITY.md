# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

We take the security of AgenticAIOPs seriously. If you believe you have found
a security vulnerability, please report it to us as follows:

- **Email**: adeel@agenticaiops.dev
- **Preferred**: Use the GitHub Security Advisory tab:
  https://github.com/adeelarshad/agenticaiops/security/advisories/new

Please do not report security vulnerabilities through public GitHub issues.

### What to include
- Description of the vulnerability
- Steps to reproduce
- Affected versions
- Any potential impact

### Response timeline
- **24 hours**: Acknowledgment of receipt
- **7 days**: Initial assessment and remediation plan
- **30 days**: Fix deployed (depending on severity)

## Disclosure Policy

We follow a coordinated disclosure process:
1. Reporter submits vulnerability details
2. We acknowledge and assess within 24 hours
3. We develop and test a fix
4. Fix is deployed and publicly disclosed
5. Reporter is credited (unless anonymous requested)

## Security Controls

- **SAST**: Semgrep + Bandit run on every PR
- **Secret scanning**: Gitleaks on every commit
- **Dependency scanning**: pip-audit weekly
- **Container scanning**: Trivy on every build
- **Runtime**: Network policies, RBAC, non-root containers
