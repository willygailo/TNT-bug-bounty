# Telecom Reconnaissance Methodology: TNT PH & Smart Communications

This reference manual outlines safe, defensive reconnaissance and asset management workflows for Philippine telecom targets under Smart Communications and Talk 'N Text (PLDT Group).

---

## 1. Scope & Primary Identity

| Entity | Primary Domains | Primary Autonomous Systems |
| :--- | :--- | :--- |
| **Talk 'N Text (TNT)** | `tntph.com`, `load.tntph.com`, `services.tntph.com` | Routed via Smart / PLDT ASNs |
| **Smart Communications** | `smart.com.ph`, `gigalife.smart.com.ph`, `api.smart.com.ph` | `AS10139` (Smart Broadband Inc.) |
| **PLDT Corporate** | `pldt.com.ph`, `pldthome.com` | `AS9299` (Philippine Long Distance Telephone Co.) |
| **Maya / PayMaya (Fintech)** | `maya.ph`, `app.maya.ph`, `paymaya.com` | Cloud-hosted (AWS / Cloudflare) |

---

## 2. Reconnaissance Workflow

### A. Subdomain Discovery
- Query Certificate Transparency logs for `*.tntph.com` and `*.smart.com.ph`.
- Cross-reference with API gateways:
  - `api.smart.com.ph`
  - `gigalife.smart.com.ph`
  - `gigapay.smart.com.ph`
  - `accounts.smart.com.ph` (OAuth 2.0 / SSO)

### B. CDN & Infrastructure Fingerprinting
- Identify reverse proxy layers:
  - **Cloudflare**: Common on public promo sites and brand portals.
  - **Akamai GHost**: Deployed on core subscriber self-care (`my.smart.com.ph`) and parent telecom sites.
  - **Imperva / Incapsula**: Common on banking and payment endpoints (`gigapay.smart.com.ph`).
  - **Direct Telecom IP**: Endpoints within `AS10139` / `AS9299` IP CIDRs.

### C. Zero-Rated & SNI Host Classification
In the Philippine telecom context, zero-rated bug hosts are endpoints whitelisted by the telco's deep packet inspection (DPI) / packet data network gateway (PGW) for specific promotional bundles:
- **ML10**: Mobile Legends game servers and API endpoints (`*.mobilelegends.com`).
- **GIGA Video**: YouTube & Google Video streaming caches (`*.googlevideo.com`).
- **TikTok Daily**: CDN endpoints hosted on Fastly / ByteDance edge (`*.tiktokcdn.com`, `*.tiktokv.com`).
- **Direct Carrier Billing**: Carrier payment gateways (`ph.codashop.com`, `direct.smart.com.ph`).

---

## 3. High-Value Telecom Vulnerability Patterns

1. **IDOR (Insecure Direct Object Reference) in Self-Care APIs**:
   - Parameter tampering on mobile numbers (MSISDN) or account numbers in REST/GraphQL queries.
   - Look for account balance, load transfer, or SIM details leaking without token verification.
2. **Broken Object Level Authorization (BOLA) in GigaLife APIs**:
   - Accessing another subscriber's active promo subscriptions or rewards points via API tampering.
3. **Subdomain Takeovers**:
   - Stale DNS CNAME records pointing to decommissioned AWS S3 buckets, GitHub Pages, or Azure Traffic Managers.
4. **CORS Misconfiguration**:
   - `Access-Control-Allow-Origin: *` with `Access-Control-Allow-Credentials: true` on subscriber profile endpoints.
5. **Zero-Rated Header Injection / Proxy Leaks**:
   - Misconfigured host headers or reverse proxies that allow unauthenticated internet routing through zero-rated gateways.
