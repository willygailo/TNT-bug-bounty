#!/usr/bin/env python3
"""
TNT PH Bug Bounty Database Manager
==================================
CLI tool for managing assets, bug hosts, database branches, and vulnerability triage
for Talk 'N Text & Smart Communications (PLDT Group) bug bounty initiatives.
"""

import argparse
import json
import os
import sqlite3
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "tnt_database.sqlite")
SCHEMA_PATH = os.path.join(BASE_DIR, "database", "schema.sql")
SEEDS_DIR = os.path.join(BASE_DIR, "database", "seeds")


def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def get_active_branch(conn):
    cur = conn.cursor()
    row = cur.execute("SELECT id, name FROM branches WHERE is_active = 1 LIMIT 1").fetchone()
    if row:
        return row["id"], row["name"]
    # Fallback to main or create it
    cur.execute("INSERT OR IGNORE INTO branches (name, description, is_active) VALUES ('main', 'Production/Verified Bug Bounty Inventory', 1)")
    cur.execute("UPDATE branches SET is_active = 1 WHERE name = 'main'")
    conn.commit()
    row = cur.execute("SELECT id, name FROM branches WHERE name = 'main'").fetchone()
    return row["id"], row["name"]


def init_db(args):
    """Initializes the database schema and loads seeds."""
    print("🚀 Initializing TNT PH Bug Bounty Database...")
    conn = get_connection()
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    cur = conn.cursor()
    cur.executescript(schema_sql)

    # Initialize default branches
    branches = [
        ("main", "Canonical, verified target assets and confirmed scope", 1),
        ("recon-stage", "Staging branch for automated subdomain enumeration and raw scans", 0),
        ("bug-hosts-branch", "Database branch for zero-rated SNI / promo bug hosts", 0),
        ("vuln-triage", "Active security vulnerability investigation and PoC drafts", 0),
    ]
    for b_name, b_desc, b_active in branches:
        cur.execute(
            "INSERT OR IGNORE INTO branches (name, description, is_active) VALUES (?, ?, ?)",
            (b_name, b_desc, b_active)
        )

    conn.commit()
    main_branch_id, _ = get_active_branch(conn)

    # Load targets seed into main branch
    targets_seed_file = os.path.join(SEEDS_DIR, "tnt_targets_seed.json")
    if os.path.exists(targets_seed_file):
        with open(targets_seed_file, "r", encoding="utf-8") as f:
            targets_data = json.load(f)
            for t in targets_data:
                cur.execute("""
                    INSERT OR IGNORE INTO targets (
                        branch_id, domain, subdomain, full_url, asset_type, ip_address, asn,
                        cdn_provider, http_status, ssl_valid, status, technologies, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    main_branch_id, t.get("domain"), t.get("subdomain"), t.get("full_url"),
                    t.get("asset_type", "web"), t.get("ip_address"), t.get("asn"),
                    t.get("cdn_provider"), t.get("http_status", 200), t.get("ssl_valid", 1),
                    t.get("status", "active"), t.get("technologies"), t.get("notes")
                ))

    # Load bug hosts seed into bug-hosts-branch
    bug_hosts_row = cur.execute("SELECT id FROM branches WHERE name = 'bug-hosts-branch'").fetchone()
    bug_hosts_branch_id = bug_hosts_row["id"] if bug_hosts_row else main_branch_id

    hosts_seed_file = os.path.join(SEEDS_DIR, "bug_hosts_seed.json")
    if os.path.exists(hosts_seed_file):
        with open(hosts_seed_file, "r", encoding="utf-8") as f:
            hosts_data = json.load(f)
            for h in hosts_data:
                cur.execute("""
                    INSERT OR IGNORE INTO bug_hosts (
                        branch_id, host, sni_hostname, promo_category, proxy_type,
                        http_status, is_working, response_time_ms, header_signatures, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    bug_hosts_branch_id, h.get("host"), h.get("sni_hostname"),
                    h.get("promo_category"), h.get("proxy_type"), h.get("http_status", 200),
                    h.get("is_working", 1), h.get("response_time_ms", 100.0),
                    h.get("header_signatures"), h.get("notes")
                ))

    # Log action
    cur.execute("INSERT INTO audit_log (branch_id, action, details) VALUES (?, 'INIT_DB', 'Initialized database schema and seed data')", (main_branch_id,))
    conn.commit()
    conn.close()
    print("✅ Database successfully initialized with default branches, targets, and bug host seeds!")


def branch_cmd(args):
    conn = get_connection()
    cur = conn.cursor()
    active_id, active_name = get_active_branch(conn)

    if args.action == "list":
        rows = cur.execute("SELECT id, name, description, is_active, created_at FROM branches ORDER BY id ASC").fetchall()
        print("\n🌿 [TNT Bug Bounty Database Branches]")
        print("-" * 75)
        for r in rows:
            prefix = "👉 *" if r["is_active"] else "   "
            print(f"{prefix} [{r['name']}] - {r['description']} (Created: {r['created_at'][:10]})")
        print("-" * 75)
        print(f"Current active branch: {active_name}\n")

    elif args.action == "create":
        name = args.name.strip().lower()
        desc = args.description or f"Branch derived from {active_name}"
        try:
            cur.execute("INSERT INTO branches (name, description, parent_branch, is_active) VALUES (?, ?, ?, 0)",
                        (name, desc, active_name))
            conn.commit()
            print(f"✅ Created branch '{name}' from '{active_name}'")
            if args.copy_data:
                new_id = cur.lastrowid
                cur.execute("""
                    INSERT INTO targets (branch_id, domain, subdomain, full_url, asset_type, ip_address, asn, cdn_provider, http_status, ssl_valid, status, technologies, notes)
                    SELECT ?, domain, subdomain, full_url, asset_type, ip_address, asn, cdn_provider, http_status, ssl_valid, status, technologies, notes
                    FROM targets WHERE branch_id = ?
                """, (new_id, active_id))
                cur.execute("""
                    INSERT INTO bug_hosts (branch_id, host, sni_hostname, promo_category, proxy_type, http_status, is_working, response_time_ms, header_signatures, notes)
                    SELECT ?, host, sni_hostname, promo_category, proxy_type, http_status, is_working, response_time_ms, header_signatures, notes
                    FROM bug_hosts WHERE branch_id = ?
                """, (new_id, active_id))
                conn.commit()
                print(f"📦 Copied all assets and bug hosts from '{active_name}' to '{name}'")
        except sqlite3.IntegrityError:
            print(f"❌ Branch '{name}' already exists.")

    elif args.action == "switch":
        name = args.name.strip().lower()
        target = cur.execute("SELECT id FROM branches WHERE name = ?", (name,)).fetchone()
        if not target:
            print(f"❌ Branch '{name}' not found.")
        else:
            cur.execute("UPDATE branches SET is_active = 0")
            cur.execute("UPDATE branches SET is_active = 1 WHERE name = ?", (name,))
            cur.execute("INSERT INTO audit_log (branch_id, action, details) VALUES (?, 'SWITCH_BRANCH', ?)",
                        (target["id"], f"Switched to branch {name}"))
            conn.commit()
            print(f"🔀 Switched active database branch to '{name}'.")

    conn.close()


def targets_cmd(args):
    conn = get_connection()
    cur = conn.cursor()
    active_id, active_name = get_active_branch(conn)

    if args.action == "list":
        query = "SELECT * FROM targets WHERE branch_id = ?"
        params = [active_id]
        if args.type:
            query += " AND asset_type = ?"
            params.append(args.type)
        if args.status:
            query += " AND status = ?"
            params.append(args.status)
        query += " ORDER BY domain ASC, subdomain ASC"

        rows = cur.execute(query, params).fetchall()
        print(f"\n🎯 [Targets in Branch: '{active_name}'] (Total: {len(rows)})")
        print("-" * 90)
        print(f"{'Target/Host':<35} {'Type':<10} {'CDN/Provider':<15} {'Status':<10} {'HTTP':<6}")
        print("-" * 90)
        for r in rows:
            host = r["subdomain"] or r["domain"]
            print(f"{host:<35} {r['asset_type'] or '-':<10} {r['cdn_provider'] or '-':<15} {r['status']:<10} {r['http_status']}")
        print("-" * 90 + "\n")

    elif args.action == "add":
        subdomain = args.subdomain if args.subdomain else (args.target if args.target != args.domain else None)
        full_url = args.url or f"https://{args.target}"
        try:
            cur.execute("""
                INSERT INTO targets (branch_id, domain, subdomain, full_url, asset_type, cdn_provider, status, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (active_id, args.domain, subdomain, full_url, args.type, args.cdn, args.status, args.notes))
            conn.commit()
            print(f"✅ Added target '{args.target}' to branch '{active_name}'.")
        except sqlite3.IntegrityError:
            print(f"❌ Target '{args.target}' already exists in branch '{active_name}'.")

    conn.close()


def hosts_cmd(args):
    conn = get_connection()
    cur = conn.cursor()
    active_id, active_name = get_active_branch(conn)

    if args.action == "list":
        query = "SELECT * FROM bug_hosts WHERE branch_id = ?"
        params = [active_id]
        if args.promo:
            query += " AND promo_category = ?"
            params.append(args.promo.upper())
        if args.working_only:
            query += " AND is_working = 1"
        query += " ORDER BY promo_category ASC, host ASC"

        rows = cur.execute(query, params).fetchall()
        print(f"\n📡 [Bug Hosts / Zero-Rated SNI in Branch: '{active_name}'] (Total: {len(rows)})")
        print("-" * 95)
        print(f"{'Host':<30} {'SNI Host':<28} {'Promo':<15} {'Proxy':<12} {'Working':<8}")
        print("-" * 95)
        for r in rows:
            status_symbol = "✅ YES" if r["is_working"] else "❌ NO"
            print(f"{r['host']:<30} {r['sni_hostname'] or '-':<28} {r['promo_category']:<15} {r['proxy_type'] or '-':<12} {status_symbol:<8}")
        print("-" * 95 + "\n")

    elif args.action == "add":
        try:
            cur.execute("""
                INSERT INTO bug_hosts (branch_id, host, sni_hostname, promo_category, proxy_type, is_working, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (active_id, args.host, args.sni or args.host, args.promo.upper(), args.proxy, 1, args.notes))
            conn.commit()
            print(f"✅ Added bug host '{args.host}' ({args.promo.upper()}) to branch '{active_name}'.")
        except sqlite3.IntegrityError:
            print(f"❌ Host '{args.host}' already registered under promo '{args.promo}' in this branch.")

    elif args.action == "validate":
        print(f"🔍 Validating bug hosts in branch '{active_name}'...")
        rows = cur.execute("SELECT id, host, sni_hostname FROM bug_hosts WHERE branch_id = ?", (active_id,)).fetchall()
        for r in rows:
            target_url = f"https://{r['host']}"
            req = urllib.request.Request(target_url, headers={"User-Agent": "Mozilla/5.0 (TNT-BugBounty-Validator/1.0)"})
            start_t = time.time()
            try:
                with urllib.request.urlopen(req, timeout=5) as response:
                    elapsed = round((time.time() - start_t) * 1000, 2)
                    code = response.getcode()
                    cur.execute("UPDATE bug_hosts SET http_status = ?, is_working = 1, response_time_ms = ?, last_checked = CURRENT_TIMESTAMP WHERE id = ?",
                                (code, elapsed, r["id"]))
                    print(f"  [200 OK] {r['host']:<30} ({elapsed}ms)")
            except urllib.error.HTTPError as e:
                elapsed = round((time.time() - start_t) * 1000, 2)
                cur.execute("UPDATE bug_hosts SET http_status = ?, is_working = 1, response_time_ms = ?, last_checked = CURRENT_TIMESTAMP WHERE id = ?",
                            (e.code, elapsed, r["id"]))
                print(f"  [{e.code}] {r['host']:<30} ({elapsed}ms)")
            except Exception as ex:
                cur.execute("UPDATE bug_hosts SET http_status = 0, is_working = 0, last_checked = CURRENT_TIMESTAMP WHERE id = ?", (r["id"],))
                print(f"  [FAIL] {r['host']:<30} (Unreachable: {str(ex)[:25]})")
        conn.commit()
        print("✅ Validation complete.")

    conn.close()


def vuln_cmd(args):
    conn = get_connection()
    cur = conn.cursor()
    active_id, active_name = get_active_branch(conn)

    if args.action == "list":
        rows = cur.execute("""
            SELECT v.*, t.domain, t.subdomain
            FROM vulnerabilities v
            LEFT JOIN targets t ON v.target_id = t.id
            WHERE v.branch_id = ?
            ORDER BY 
                CASE v.severity 
                    WHEN 'CRITICAL' THEN 1 
                    WHEN 'HIGH' THEN 2 
                    WHEN 'MEDIUM' THEN 3 
                    WHEN 'LOW' THEN 4 
                    ELSE 5 
                END
        """, (active_id,)).fetchall()
        print(f"\n🛡️ [Vulnerabilities Triage in Branch: '{active_name}'] (Total: {len(rows)})")
        print("-" * 100)
        print(f"{'Title':<35} {'Severity':<10} {'CVSS':<6} {'Type':<22} {'Status':<12}")
        print("-" * 100)
        for r in rows:
            print(f"{r['title'][:33]:<35} {r['severity']:<10} {r['cvss_score'] or '-':<6} {r['vuln_type']:<22} {r['status']:<12}")
        print("-" * 100 + "\n")

    elif args.action == "add":
        cur.execute("""
            INSERT INTO vulnerabilities (
                branch_id, title, vuln_type, severity, cvss_score, endpoint,
                reproduction_steps, impact, remediation, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            active_id, args.title, args.type.upper(), args.severity.upper(),
            args.cvss, args.endpoint, args.steps, args.impact, args.remediation, args.status
        ))
        conn.commit()
        print(f"✅ Successfully recorded vulnerability '{args.title}' [{args.severity.upper()}] in branch '{active_name}'.")

    conn.close()


def export_cmd(args):
    conn = get_connection()
    cur = conn.cursor()
    active_id, active_name = get_active_branch(conn)

    targets = [dict(r) for r in cur.execute("SELECT * FROM targets WHERE branch_id = ?", (active_id,)).fetchall()]
    hosts = [dict(r) for r in cur.execute("SELECT * FROM bug_hosts WHERE branch_id = ?", (active_id,)).fetchall()]
    vulns = [dict(r) for r in cur.execute("SELECT * FROM vulnerabilities WHERE branch_id = ?", (active_id,)).fetchall()]

    if args.format == "json":
        export_data = {
            "branch": active_name,
            "exported_at": datetime.now(datetime.timezone.utc).isoformat(),
            "targets_count": len(targets),
            "bug_hosts_count": len(hosts),
            "vulnerabilities_count": len(vulns),
            "targets": targets,
            "bug_hosts": hosts,
            "vulnerabilities": vulns
        }
        output_path = args.output or f"tnt_export_{active_name}.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2)
        print(f"✅ Exported JSON database to {output_path}")

    elif args.format == "markdown":
        output_path = args.output or f"tnt_report_{active_name}.md"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(f"# 🛡️ TNT PH Bug Bounty Intelligence Report\n")
            f.write(f"**Database Branch:** `{active_name}` | **Generated:** {datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n")

            f.write(f"## 1. Executive Summary\n")
            f.write(f"- **Total Target Assets Monitored:** {len(targets)}\n")
            f.write(f"- **Active Bug Hosts / SNI Endpoints:** {len([h for h in hosts if h['is_working']])} / {len(hosts)}\n")
            f.write(f"- **Vulnerabilities Recorded:** {len(vulns)}\n\n")

            f.write(f"## 2. Target Assets Inventory\n\n")
            f.write(f"| Asset / Host | Type | CDN / Infrastructure | Status |\n")
            f.write(f"| :--- | :--- | :--- | :--- |\n")
            for t in targets:
                f.write(f"| `{t['subdomain'] or t['domain']}` | {t['asset_type']} | {t['cdn_provider'] or 'Direct'} | {t['status']} |\n")

            f.write(f"\n## 3. Bug Hosts / Zero-Rated SNI Catalog\n\n")
            f.write(f"| Host | SNI Hostname | Promo Category | Proxy Type | Live Status |\n")
            f.write(f"| :--- | :--- | :--- | :--- | :--- |\n")
            for h in hosts:
                st = "Active (200)" if h["is_working"] else "Inactive"
                f.write(f"| `{h['host']}` | `{h['sni_hostname']}` | {h['promo_category']} | {h['proxy_type']} | {st} |\n")

            if vulns:
                f.write(f"\n## 4. Vulnerabilities & Findings Triage\n\n")
                for v in vulns:
                    f.write(f"### [{v['severity']}] {v['title']}\n")
                    f.write(f"- **Type:** `{v['vuln_type']}` | **CVSS v3.1:** `{v['cvss_score']}` | **Status:** `{v['status']}`\n")
                    f.write(f"- **Endpoint:** `{v['endpoint']}`\n\n")
                    f.write(f"**Impact:**\n{v['impact']}\n\n")
                    f.write(f"**Reproduction Steps:**\n{v['reproduction_steps']}\n\n")
                    f.write(f"**Remediation:**\n{v['remediation'] or 'N/A'}\n\n---\n")

        print(f"✅ Exported Markdown report to {output_path}")

    conn.close()


def stats_cmd(args):
    conn = get_connection()
    cur = conn.cursor()
    active_id, active_name = get_active_branch(conn)

    targets_cnt = cur.execute("SELECT count(*) as c FROM targets WHERE branch_id = ?", (active_id,)).fetchone()["c"]
    hosts_cnt = cur.execute("SELECT count(*) as c FROM bug_hosts WHERE branch_id = ?", (active_id,)).fetchone()["c"]
    vuln_cnt = cur.execute("SELECT count(*) as c FROM vulnerabilities WHERE branch_id = ?", (active_id,)).fetchone()["c"]
    branches_cnt = cur.execute("SELECT count(*) as c FROM branches").fetchone()["c"]

    print("\n📊 [TNT PH Bug Bounty Database Overview]")
    print("=" * 45)
    print(f" Active Branch:           {active_name}")
    print(f" Total Branches:          {branches_cnt}")
    print(f" Monitored Targets:       {targets_cnt}")
    print(f" Zero-Rated / Bug Hosts:  {hosts_cnt}")
    print(f" Logged Vulnerabilities:  {vuln_cnt}")
    print("=" * 45 + "\n")
    conn.close()


def main():
    parser = argparse.ArgumentParser(description="TNT PH Bug Bounty Database & Branch CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # init
    init_parser = subparsers.add_parser("init", help="Initialize DB schema and seed data")
    init_parser.set_defaults(func=init_db)

    # branch
    branch_parser = subparsers.add_parser("branch", help="Manage database branches")
    branch_sub = branch_parser.add_subparsers(dest="action", required=True)

    b_list = branch_sub.add_parser("list", help="List database branches")
    b_list.set_defaults(func=branch_cmd)

    b_create = branch_sub.add_parser("create", help="Create new branch")
    b_create.add_argument("name", help="Branch name")
    b_create.add_argument("--description", help="Description")
    b_create.add_argument("--copy-data", action="store_true", help="Copy records from active branch")
    b_create.set_defaults(func=branch_cmd)

    b_switch = branch_sub.add_parser("switch", help="Switch active branch")
    b_switch.add_argument("name", help="Target branch name")
    b_switch.set_defaults(func=branch_cmd)

    # targets
    target_parser = subparsers.add_parser("targets", help="Manage target assets")
    t_sub = target_parser.add_subparsers(dest="action", required=True)

    t_list = t_sub.add_parser("list", help="List targets")
    t_list.add_argument("--type", help="Filter by asset type")
    t_list.add_argument("--status", help="Filter by status")
    t_list.set_defaults(func=targets_cmd)

    t_add = t_sub.add_parser("add", help="Add target")
    t_add.add_argument("target", help="Domain or subdomain")
    t_add.add_argument("--domain", default="smart.com.ph", help="Root domain")
    t_add.add_argument("--subdomain", help="Subdomain")
    t_add.add_argument("--type", default="web", choices=["web", "api", "portal", "gateway", "payment", "cdn", "core"])
    t_add.add_argument("--cdn", default="Direct", help="CDN provider")
    t_add.add_argument("--url", help="Full URL")
    t_add.add_argument("--status", default="active")
    t_add.add_argument("--notes", default="")
    t_add.set_defaults(func=targets_cmd)

    # hosts
    hosts_parser = subparsers.add_parser("hosts", help="Manage bug hosts / zero-rated SNI")
    h_sub = hosts_parser.add_subparsers(dest="action", required=True)

    h_list = h_sub.add_parser("list", help="List bug hosts")
    h_list.add_argument("--promo", help="Filter by promo category")
    h_list.add_argument("--working-only", action="store_true", help="Only show working hosts")
    h_list.set_defaults(func=hosts_cmd)

    h_add = h_sub.add_parser("add", help="Add bug host")
    h_add.add_argument("host", help="Host/Domain")
    h_add.add_argument("--promo", required=True, help="Promo category (ML10, TIKTOK, FB_IG, etc.)")
    h_add.add_argument("--sni", help="SNI hostname")
    h_add.add_argument("--proxy", default="Cloudflare", choices=["Cloudflare", "Fastly", "Direct_SNI", "Akamai", "Imperva", "Other"])
    h_add.add_argument("--notes", default="")
    h_add.set_defaults(func=hosts_cmd)

    h_val = h_sub.add_parser("validate", help="Validate live status of bug hosts")
    h_val.set_defaults(func=hosts_cmd)

    # vuln
    vuln_parser = subparsers.add_parser("vuln", help="Triage vulnerabilities")
    v_sub = vuln_parser.add_subparsers(dest="action", required=True)

    v_list = v_sub.add_parser("list", help="List vulnerabilities")
    v_list.set_defaults(func=vuln_cmd)

    v_add = v_sub.add_parser("add", help="Record vulnerability finding")
    v_add.add_argument("--title", required=True, help="Title of vulnerability")
    v_add.add_argument("--type", required=True, help="Vulnerability type (IDOR, API_AUTH_BYPASS, etc.)")
    v_add.add_argument("--severity", required=True, choices=["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"])
    v_add.add_argument("--cvss", type=float, default=7.5, help="CVSS score")
    v_add.add_argument("--endpoint", required=True, help="Vulnerable endpoint URL")
    v_add.add_argument("--steps", required=True, help="Reproduction steps")
    v_add.add_argument("--impact", required=True, help="Security impact")
    v_add.add_argument("--remediation", default="", help="Recommended remediation")
    v_add.add_argument("--status", default="triage", choices=["draft", "triage", "validated", "reported", "resolved"])
    v_add.set_defaults(func=vuln_cmd)

    # export
    exp_parser = subparsers.add_parser("export", help="Export report or database snapshot")
    exp_parser.add_argument("--format", default="markdown", choices=["markdown", "json"])
    exp_parser.add_argument("--output", help="Output file path")
    exp_parser.set_defaults(func=export_cmd)

    # stats
    stats_parser = subparsers.add_parser("stats", help="Database statistics")
    stats_parser.set_defaults(func=stats_cmd)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
