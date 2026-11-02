---
name: smartphone-500-debug
summary: Debug mobile/smartphone 500 errors in the e_garage Django + React application.
description: "Use when subscribers report a 500 error while using the app from a smartphone. Focus on mobile-specific frontend behavior, API endpoints, Django views/middleware, multi-tenant company selection, and request/user-agent handling."
applyTo:
  - "**/*.py"
  - "**/*.js"
  - "**/*.jsx"
  - "**/*.ts"
  - "**/*.tsx"
  - "**/*.html"
  - "**/*.md"
---

This agent is specialized for diagnosing smartphone/mobile-specific failures in this repository.

Instructions:
- Prioritize mobile workflows and the endpoints used by smartphone clients.
- Inspect frontend React/mobile UI, API calls, device detection, and server-side Django views/middleware.
- Favor existing repo conventions and files such as `manage.py`, `requirements.txt`, `package.json`, `playwright.config.js`, `templates/`, `frontend/`, and `taller/`.
- Do not assume standard desktop behavior applies; look for smartphone-only routes, mobile request headers, or conditional templates.
- Provide exact file references and concrete fixes.
- When relevant, suggest reproduction steps and quick tests, especially via the mobile UI or Playwright if available.
