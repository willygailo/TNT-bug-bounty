# 🛡️ TNT PH Bug Bounty Database & Branch Management

A specialized intelligence database, branching system, and Agent Skill designed for tracking assets, zero-rated SNI endpoints, and vulnerability triage across **Talk 'N Text (TNT)** and **Smart Communications (PLDT Group)** properties.

---

## 📂 Project Architecture

```text
TNT bug bounty/
├── .agents/
│   └── skills/
│       └── tnt-bug-bounty-db/
│           ├── SKILL.md                          # Antigravity Agent Skill
│           └── references/
│               ├── telecom_recon_methodology.md  # Telecom asset & recon guide
│               └── reporting_guidelines.md       # Responsible disclosure template
├── database/
│   ├── schema.sql                                # SQLite schema definition
│   ├── seeds/
│   │   ├── tnt_targets_seed.json                 # Pre-seeded telecom target assets
│   │   └── bug_hosts_seed.json                   # Zero-rated SNI & promo hosts
│   └── tnt_database.sqlite                       # Active SQLite database
├── scripts/
│   └── tnt_db_manager.py                         # Full CLI management tool
└── README.md
```

---

## 🌿 Database Branch System

The database supports isolated branch environments to separate confirmed assets from active scanning and vulnerability drafts:

| Branch | Description |
| :--- | :--- |
| **`main`** | Verified production targets, root domains, official APIs, and portals. |
| **`recon-stage`** | Staging branch for active subdomain enumeration and automated discovery. |
| **`bug-hosts-branch`** | Catalog of zero-rated / SNI promo endpoints (ML10, GIGA, TikTok, FB, etc.). |
| **`vuln-triage`** | Workspace for drafting and validating vulnerability findings (IDOR, API flaws). |

---

## ⚡ Quick CLI Commands

### 1. Database Overview & Statistics
```bash
python3 scripts/tnt_db_manager.py stats
```

### 2. Branch Operations
```bash
# List all branches
python3 scripts/tnt_db_manager.py branch list

# Switch active branch
python3 scripts/tnt_db_manager.py branch switch bug-hosts-branch

# Create a new branch copied from current active branch
python3 scripts/tnt_db_manager.py branch create my-recon-session --copy-data
```

### 3. Target Assets Management
```bash
# List targets in current branch
python3 scripts/tnt_db_manager.py targets list

# Filter by asset type ('web', 'api', 'portal', 'payment', 'gateway')
python3 scripts/tnt_db_manager.py targets list --type api

# Add a newly discovered target
python3 scripts/tnt_db_manager.py targets add gigalife.smart.com.ph --type api --cdn Cloudflare
```

### 4. Zero-Rated SNI / Bug Hosts
```bash
# Switch to bug hosts branch
python3 scripts/tnt_db_manager.py branch switch bug-hosts-branch

# List hosts by promo
python3 scripts/tnt_db_manager.py hosts list --promo ML10

# Validate live connectivity (safe HTTP/HTTPS probe)
python3 scripts/tnt_db_manager.py hosts validate
```

### 5. Vulnerability Logging & Triage
```bash
python3 scripts/tnt_db_manager.py vuln add \
  --title "IDOR in Subscriber Profile API" \
  --type IDOR \
  --severity HIGH \
  --cvss 7.5 \
  --endpoint "https://api.smart.com.ph/v2/subscribers/{msisdn}" \
  --steps "1. Send GET request with auth token A. 2. Specify victim MSISDN B." \
  --impact "PII and load balance disclosure." \
  --remediation "Enforce server-side ownership verification." \
  --status triage
```

### 6. Export Intelligence Reports
```bash
# Generate Markdown report
python3 scripts/tnt_db_manager.py export --format markdown --output report.md

# Generate JSON database export
python3 scripts/tnt_db_manager.py export --format json --output database_export.json
```

---

## 🤖 Antigravity Agent Skill Integration

The skill `tnt-bug-bounty-db` is installed in:
- **Project Scope:** [`.agents/skills/tnt-bug-bounty-db/SKILL.md`](file:///home/willygailo/Downloads/TNT%20bug%20bounty/.agents/skills/tnt-bug-bounty-db/SKILL.md)
- **Global Scope:** `~/.gemini/config/skills/tnt-bug-bounty-db/SKILL.md`
- **OpenCode Scope:** `~/.opencode/SKILLS/tnt-bug-bounty-db/SKILL.md`

When conversing with the agent, you can simply ask:
- *"List all TNT targets in the database"*
- *"Switch to the bug-hosts branch and validate the hosts"*
- *"Add this new Smart PH API endpoint to the recon branch"*
- *"Triage an IDOR vulnerability for GigaLife"*
- *"Export our bug bounty report"*
