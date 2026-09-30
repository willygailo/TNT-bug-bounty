-- ==============================================================================
-- TNT PH Bug Bounty Database Schema
-- Focus: Smart Communications / Talk 'N Text (PLDT Group) Asset & Vulnerability Tracking
-- Supports: Database branching, target recon, SNI/zero-rated bug hosts, and triage.
-- ==============================================================================

PRAGMA foreign_keys = ON;

-- 1. Database Branches (Main, Recon, Staging, Verified Findings)
CREATE TABLE IF NOT EXISTS branches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    parent_branch TEXT DEFAULT 'main',
    is_active INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 2. Target Assets (Domains, Subdomains, Gateways, Core Telecom Infrastructure)
CREATE TABLE IF NOT EXISTS targets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    branch_id INTEGER NOT NULL REFERENCES branches(id) ON DELETE CASCADE,
    domain TEXT NOT NULL,
    subdomain TEXT,
    full_url TEXT,
    asset_type TEXT CHECK (asset_type IN ('web', 'api', 'portal', 'gateway', 'payment', 'cdn', 'core')),
    ip_address TEXT,
    asn TEXT,
    cdn_provider TEXT,
    http_status INTEGER DEFAULT 0,
    ssl_valid INTEGER DEFAULT 0,
    status TEXT CHECK (status IN ('active', 'dead', 'protected', 'unresolvable', 'investigating')) DEFAULT 'active',
    technologies TEXT,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(branch_id, domain, subdomain)
);

-- 3. Bug Hosts / SNI Zero-Rated Hosts (Promo Bypass / Zero-Rated Testing)
CREATE TABLE IF NOT EXISTS bug_hosts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    branch_id INTEGER NOT NULL REFERENCES branches(id) ON DELETE CASCADE,
    host TEXT NOT NULL,
    sni_hostname TEXT,
    promo_category TEXT CHECK (promo_category IN ('ML10', 'GIGA_VIDEO', 'TIKTOK', 'FB_IG', 'UNLI_DATA', 'CODASHOP', 'GENERAL_ZERO_RATED', 'PROMO_BYPASS')),
    proxy_type TEXT CHECK (proxy_type IN ('Cloudflare', 'Fastly', 'Direct_SNI', 'Akamai', 'Imperva', 'Other')),
    http_status INTEGER DEFAULT 0,
    is_working INTEGER DEFAULT 1,
    response_time_ms REAL,
    header_signatures TEXT,
    notes TEXT,
    last_checked DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(branch_id, host, promo_category)
);

-- 4. Vulnerabilities / Findings Triage
CREATE TABLE IF NOT EXISTS vulnerabilities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    branch_id INTEGER NOT NULL REFERENCES branches(id) ON DELETE CASCADE,
    target_id INTEGER REFERENCES targets(id) ON DELETE SET NULL,
    title TEXT NOT NULL,
    vuln_type TEXT CHECK (vuln_type IN (
        'IDOR', 
        'API_AUTH_BYPASS', 
        'SUBDOMAIN_TAKEOVER', 
        'CORS_MISCONFIG', 
        'INFORMATION_DISCLOSURE', 
        'RATE_LIMIT_BYPASS', 
        'SQLI', 
        'XSS', 
        'SSRF', 
        'BUSINESS_LOGIC',
        'ZERO_RATED_DATA_LEAK'
    )) NOT NULL,
    severity TEXT CHECK (severity IN ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO')) NOT NULL,
    cvss_score REAL,
    cvss_vector TEXT,
    endpoint TEXT NOT NULL,
    reproduction_steps TEXT NOT NULL,
    impact TEXT NOT NULL,
    remediation TEXT,
    status TEXT CHECK (status IN ('draft', 'triage', 'validated', 'reported', 'resolved', 'duplicate', 'out_of_scope')) DEFAULT 'draft',
    poc_evidence TEXT,
    reported_date DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 5. Reconnaissance Scans & Probes
CREATE TABLE IF NOT EXISTS recon_scans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    branch_id INTEGER NOT NULL REFERENCES branches(id) ON DELETE CASCADE,
    scan_type TEXT NOT NULL,
    target_domain TEXT NOT NULL,
    discovered_count INTEGER DEFAULT 0,
    raw_output_path TEXT,
    tool_used TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 6. Audit & Branch Activity Log
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    branch_id INTEGER REFERENCES branches(id) ON DELETE CASCADE,
    action TEXT NOT NULL,
    details TEXT,
    performed_by TEXT DEFAULT 'Agent',
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for Fast Querying
CREATE INDEX IF NOT EXISTS idx_targets_branch ON targets(branch_id);
CREATE INDEX IF NOT EXISTS idx_targets_domain ON targets(domain);
CREATE INDEX IF NOT EXISTS idx_targets_status ON targets(status);
CREATE INDEX IF NOT EXISTS idx_bug_hosts_promo ON bug_hosts(promo_category);
CREATE INDEX IF NOT EXISTS idx_bug_hosts_working ON bug_hosts(is_working);
CREATE INDEX IF NOT EXISTS idx_vulns_severity ON vulnerabilities(severity);
CREATE INDEX IF NOT EXISTS idx_vulns_status ON vulnerabilities(status);
