# Security policy

Please report suspected vulnerabilities through GitHub private vulnerability reporting when it is enabled
for this repository, rather than opening a public issue. Include the affected version, reproduction steps,
impact, and any known mitigation. Do not include real secrets, personal data, or confidential project
content in a report.

Applied AI Rig generates engineering records and performs structural checks. It is not a security scanner,
secret vault, runtime policy engine, or compliance certification tool.

The project CI scans the complete committed Git history with a checksum-pinned Gitleaks binary. This
reduces accidental credential exposure but does not make the Rig or its generated records a secrets vault.
