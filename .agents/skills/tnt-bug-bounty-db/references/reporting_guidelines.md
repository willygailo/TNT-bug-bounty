# Bug Bounty Vulnerability Reporting Guidelines: TNT PH & Smart Communications

This guideline provides the standardized structure for drafting and submitting security vulnerabilities discovered across Smart Communications and Talk 'N Text properties.

---

## 1. Vulnerability Report Template

### Title
`[Vulnerability Type] on [Vulnerable Domain/Endpoint] leads to [Clear Security Impact]`
*Example:* `[IDOR] on api.smart.com.ph/v1/subscriber/profile exposes customer PII and promo balance`

### Metadata
- **Target Asset:** `https://api.smart.com.ph`
- **Vulnerability Category:** Insecure Direct Object Reference (IDOR)
- **CVSS v3.1 Score:** `7.5 (High)`
- **CVSS Vector:** `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N`
- **Discovery Date:** YYYY-MM-DD

---

## 2. Executive Summary
Provide a 2-3 sentence overview explaining what the issue is, where it resides, and what an attacker can achieve.

---

## 3. Step-by-Step Proof of Concept (PoC)

1. **Prerequisites:** State required tools or accounts (e.g. two test accounts with test MSISDNs).
2. **Request Definition:** Include HTTP request headers, method, and parameters.
```http
GET /api/v2/subscribers/09191234567/balance HTTP/1.1
Host: api.smart.com.ph
Authorization: Bearer <Attacker_JWT_Token>
```
3. **Response Definition:** Highlight the exposed data or unexpected response.
```json
{
  "status": "success",
  "data": {
    "msisdn": "09191234567",
    "account_name": "Juan Dela Cruz",
    "load_balance": 250.00,
    "active_promos": ["TNT_GIGA_VIDEO_99"]
  }
}
```
4. **Observation:** Note why this violates authorization boundaries.

---

## 4. Impact Analysis
- Explain realistic impact on confidentiality, integrity, or availability.
- Clarify why this matters to the telecom subscriber and the organization (e.g. data privacy compliance, financial loss).

---

## 5. Remediation Recommendation
- Detail code-level fixes (e.g. server-side session-to-object ownership verification, principle of least privilege, strict CORS policies).
