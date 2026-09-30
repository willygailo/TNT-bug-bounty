---
name: tnt-bug-bounty-db
description: >-
  Manage, query, validate, and triage assets, bug hosts, and vulnerability findings in the TNT PH (Talk 'N Text / Smart Communications) bug bounty database branch. Use when analyzing TNT PH attack surface, searching telecom targets, validating zero-rated promo endpoints/SNI hosts, managing database branches, or drafting bug bounty reports.
---

# TNT PH Bug Bounty Database & Branch Management Skill

This skill provides operational procedures, CLI commands, and runbooks for managing the **TNT PH (Talk 'N Text / Smart Communications - PLDT Group)** bug bounty database, target assets, zero-rated SNI bug host branch, and vulnerability triage pipeline.

---

## When to Use This Skill

Activate this skill whenever the user asks to:
- Inspect, list, add, or search targets and subdomains under `*.tntph.com` or `*.smart.com.ph`.
- Switch, create, or inspect **database branches** (e.g., `main`, `recon-stage`, `bug-hosts-branch`, `vuln-triage`).
- Query or validate **zero-rated / SNI bug hosts** (ML10, GIGA Video, TikTok, FB/IG, Direct Carrier Billing).
- Triage and log newly identified vulnerabilities (IDOR, API auth bypass, subdomain takeover, CORS).
- Export formal bug bounty intelligence reports or vulnerability submission documents.

---

## Core Database Branch Architecture

The database uses SQLite with branch isolation:

| Branch Name | Role | Primary Contents |
| :--- | :--- | :--- |
| **`main`** | Verified Production Scope | Verified live target assets, primary domains, official gateways |
| **`recon-stage`** | Raw Reconnaissance | Newly scraped subdomains, CT log findings, unvalidated hosts |
| **`bug-hosts-branch`** | SNI / Zero-Rated Testing | Cellular promo bug hosts (ML10, TikTok, FreeNet, Codashop) |
| **`vuln-triage`** | Vulnerability Tracker | Security findings, reproduction steps, CVSS scores, remediation |

---

## Step-by-Step Operational Runbook

### 1. Check Database Status and Active Branch
Always verify the current active branch and target count before performing modifications:

```bash
python3 scripts/tnt_db_manager.py stats
python3 scripts/tnt_db_manager.py branch list
```

### 2. Branch Navigation & Creation
To switch to a specific branch:
```bash
python3 scripts/tnt_db_manager.py branch switch <branch_name>
```

To create a new isolated database branch (e.g. for a specific bug hunting session):
```bash
# Create an empty branch
python3 scripts/tnt_db_manager.py branch create <new_branch_name> --description "Description of focus"

# Or create a branch with all records copied from the active branch:
python3 scripts/tnt_db_manager.py branch create <new_branch_name> --copy-data
```

### 3. Querying & Adding Target Assets
List targets in the current branch:
```bash
# List all targets in active branch
python3 scripts/tnt_db_manager.py targets list

# Filter by asset type ('web', 'api', 'portal', 'gateway', 'payment', 'cdn', 'core')
python3 scripts/tnt_db_manager.py targets list --type api

# Filter by status ('active', 'dead', 'protected')
python3 scripts/tnt_db_manager.py targets list --status active
```

Add a newly discovered subdomain or gateway:
```bash
python3 scripts/tnt_db_manager.py targets add sub.domain.com \
  --domain smart.com.ph \
  --type api \
  --cdn Cloudflare \
  --notes "Discovered via CT logs"
```

### 4. Working with Bug Hosts (Zero-Rated / SNI Branch)
Switch to the bug hosts branch:
```bash
python3 scripts/tnt_db_manager.py branch switch bug-hosts-branch
python3 scripts/tnt_db_manager.py hosts list
```

Filter by promotional category:
```bash
python3 scripts/tnt_db_manager.py hosts list --promo ML10
python3 scripts/tnt_db_manager.py hosts list --promo TIKTOK
```

Perform automated live validation of all bug hosts (safe HTTP/HTTPS status probe):
```bash
python3 scripts/tnt_db_manager.py hosts validate
```

Add a new bug host candidate:
```bash
python3 scripts/tnt_db_manager.py hosts add api.partner.com \
  --promo ML10 \
  --sni api.partner.com \
  --proxy Cloudflare \
  --notes "Zero-rated mobile asset"
```

### 5. Triaging & Logging Vulnerabilities
When a valid vulnerability is confirmed, switch to `vuln-triage` or the relevant working branch and record the finding:

```bash
python3 scripts/tnt_db_manager.py vuln add \
  --title "IDOR in Subscriber Profile API" \
  --type IDOR \
  --severity HIGH \
  --cvss 7.5 \
  --endpoint "https://api.smart.com.ph/v2/subscribers/{msisdn}" \
  --steps "1. Send GET request with auth token A specifying msisdn B. 2. Observe victim profile returned." \
  --impact "Unauthorized disclosure of subscriber PII and account balance." \
  --remediation "Enforce server-side ownership verification between JWT subject and requested MSISDN." \
  --status triage
```

Review logged vulnerabilities:
```bash
python3 scripts/tnt_db_manager.py vuln list
```

### 6. Exporting Intelligence Reports
Generate a complete Markdown report for security review or bug bounty submission:
```bash
python3 scripts/tnt_db_manager.py export --format markdown --output tnt_bug_bounty_report.md
```

Export raw JSON database for programmatic processing:
```bash
python3 scripts/tnt_db_manager.py export --format json --output tnt_bug_bounty_export.json
```

---

## Detailed References

For comprehensive background context and reporting templates, consult:
- [Telecom Reconnaissance Methodology](./references/telecom_recon_methodology.md): Scope breakdown, ASN mapping, and zero-rated gateway mechanics.
- [Bug Bounty Reporting Guidelines](./references/reporting_guidelines.md): Submission format, CVSS scoring, and remediation templates.
