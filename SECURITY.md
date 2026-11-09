# Security Policy

## Local & Offline Privacy Guarantee

**نَصّ | NASS** is strictly designed as an offline, local-first desktop application.
- All optical character recognition and document parsing tasks execute 100% on the local CPU/device.
- No documents, extracted texts, images, or metrics are sent across any network or cloud API.
- Network operations are strictly limited to user-initiated downloads of official Tesseract language packs from GitHub releases when explicitly requested via the Language Manager.

---

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

---

## Reporting a Vulnerability

If you discover a security vulnerability within NASS, please do **NOT** open a public issue. Instead, report it privately:

1. Send an email to **[ibrahim.salha19@gmail.com](mailto:ibrahim.salha19@gmail.com)** with the subject line:
   `[SECURITY] Vulnerability in NASS - <Brief Description>`
2. Include detailed reproduction steps, potential impact, and your environment details.
3. You will receive an initial response within 48 hours acknowledging receipt.
4. We will coordinate remediation and a release before publicly disclosing the issue.
