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
├── plan.md                                       # Operational bug bounty roadmap
└── README.md
```

---

## 🌿 Database Branch System

The database supports isolated branch environments to separate confirmed assets from active scanning and vulnerability drafts:

| Branch | Description | Contents |
| :--- | :--- | :--- |
| **`main`** | Verified production targets, root domains, official APIs, and portals. | `tntph.com`, `smart.com.ph`, `my.smart.com.ph`, `api.smart.com.ph`, etc. |
| **`recon-stage`** | Staging branch for active subdomain enumeration and automated discovery. | `store.smart.com.ph`, `maya.ph`, `pldt.com.ph`, `smartnet.ph`, `simreg.tntph.com` |
| **`bug-hosts-branch`** | Catalog of zero-rated / SNI promo endpoints. | ML10, GIGA Video, TikTok, Free Facebook, Codashop |
| **`vuln-triage`** | Workspace for drafting and validating vulnerability findings. | IDOR, API authorization flaws, information disclosures |

---

## 🔍 Verified Telecom Architecture & Footprint

From passive HTTP header fingerprinting and live status probing:

| Host | Platform / Framework | Reverse Proxy / CDN | Key Security Headers |
| :--- | :--- | :--- | :--- |
| **`tntph.com`** | Microsoft ASP.NET (4.0.30319) | Citrix NetScaler ADC (`NSC_` cookie), Edge LB | HSTS, X-Frame-Options (SAMEORIGIN), nosniff |
| **`store.smart.com.ph`** | Salesforce Commerce Cloud (Demandware) | Cloudflare CDN (Singapore Edge) | HSTS, CSP (frame-ancestors 'self') |
| **`api.smart.com.ph`** | Telecom API Gateway | Upstream Reverse Proxy (HTTP 472 on root) | Gateway route/header protection |
| **`my.smart.com.ph`** | Oracle / WebLogic Self-Care | Akamai GHost | Akamai Edge security |

---

## 📊 Live Probe & Validation Status

Results from live HTTP/HTTPS status validation (`targets validate` & `hosts validate`):

### Target Assets:
- **`tntph.com`** – `HTTP 200 OK` (Live commercial portal)
- **`store.smart.com.ph`** – `HTTP 200 OK` (Live e-store portal)
- **`smart.com.ph`** – `HTTP 247` (Live with Akamai edge protection)
- **`my.smart.com.ph`** – `HTTP 247` (Live self-care portal)
- **`api.smart.com.ph`** – `HTTP 472` (Live API gateway requiring specific routes)
- **`maya.ph`** – `HTTP 200 OK` (Fintech partner portal)
- **`pldt.com.ph`** – `HTTP 200 OK` (Parent carrier backbone)

### Zero-Rated Bug Hosts (SNI):
- **`mobilelegends.com`** (ML10) – `HTTP 200 OK` ✅
- **`free.facebook.com`** (FB/IG) – `HTTP 200 OK` ✅
- **`v16.tiktokcdn.com`** (TikTok) – `HTTP 403 / Edge Active` ✅
- **`codashop.com`** (Carrier Billing) – `HTTP 401 / Active` ✅

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

# Validate live HTTP connectivity of all targets in the active branch
python3 scripts/tnt_db_manager.py targets validate

# Add a newly discovered target
python3 scripts/tnt_db_manager.py targets add gigalife.smart.com.ph --type api --cdn Cloudflare
```

### 4. Zero-Rated SNI / Bug Hosts
```bash
# Switch to bug hosts branch
python3 scripts/tnt_db_manager.py branch switch bug-hosts-branch

# List hosts by promo category (ML10, TIKTOK, FB_IG, etc.)
python3 scripts/tnt_db_manager.py hosts list --promo ML10

# Validate live connectivity (safe HTTP/HTTPS probe with latency check)
python3 scripts/tnt_db_manager.py hosts validate

# Add a new bug host candidate
python3 scripts/tnt_db_manager.py hosts add api.mobilelegends.com --promo ML10 --proxy Cloudflare
```

### 5. Vulnerability Logging & Triage
```bash
# Switch to vulnerability triage branch
python3 scripts/tnt_db_manager.py branch switch vuln-triage

# Record a new vulnerability finding
python3 scripts/tnt_db_manager.py vuln add \
  --title "Information Disclosure: ASP.NET Version Leaked in HTTP Headers" \
  --type INFORMATION_DISCLOSURE \
  --severity LOW \
  --cvss 3.1 \
  --endpoint "https://tntph.com" \
  --steps "1. Send GET request to https://tntph.com. 2. Observe x-aspnet-version header." \
  --impact "Leaks exact framework version 4.0.30319 to unauthenticated users." \
  --remediation "Disable enableVersionHeader in web.config." \
  --status triage

# View all logged findings
python3 scripts/tnt_db_manager.py vuln list
```

### 6. Export Intelligence Reports
```bash
# Generate Markdown report
python3 scripts/tnt_db_manager.py export --format markdown --output report.md

# Generate JSON database export
python3 scripts/tnt_db_manager.py export --format json --output database_export.json
```

---

## 🎯 OWASP Telecom API Assessment Checklist

When testing telecom self-care and payment APIs:

1. **BOLA / IDOR (Broken Object Level Authorization):**
   - Test endpoints taking subscriber mobile numbers (MSISDN: `09XXXXXXXXX`) or Account IDs.
   - Use two separate authorized test accounts (Account A vs. Account B) to ensure strict session-to-object ownership.
2. **SMS OTP / Rate Limiting:**
   - Audit OTP requests for login and load transfers against anti-automation bypasses.
3. **Information Disclosure:**
   - Inspect custom error responses on invalid paths to ensure internal stack traces or database queries are suppressed.
4. **JWT Security:**
   - Check algorithm strength (`alg`), expiration (`exp`), and claim integrity on mobile gateway tokens.

---

## 🤖 Antigravity Agent Skill Integration

The skill `tnt-bug-bounty-db` is installed in:
- **Project Scope:** [`.agents/skills/tnt-bug-bounty-db/SKILL.md`](file:///home/willygailo/Downloads/TNT%20bug%20bounty/.agents/skills/tnt-bug-bounty-db/SKILL.md)
- **Global Scope:** `~/.gemini/config/skills/tnt-bug-bounty-db/SKILL.md`
- **OpenCode Scope:** `~/.opencode/SKILLS/tnt-bug-bounty-db/SKILL.md`
- **Operational Roadmap:** [`plan.md`](file:///home/willygailo/Downloads/TNT%20bug%20bounty/plan.md)

When conversing with the agent, you can simply ask:
- *"List all TNT targets in the database"*
- *"Validate the targets in the main branch"*
- *"Switch to the bug-hosts branch and validate the hosts"*
- *"Add this new Smart PH API endpoint to the recon branch"*
- *"Triage an IDOR vulnerability for GigaLife"*
- *"Export our bug bounty report"*
