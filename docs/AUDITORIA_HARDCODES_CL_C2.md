# Auditoría C.2 — Hardcodes `/cl/...` login y signup en templates

Patrones: `/cl/es/accounts/login/`, `/cl/es/accounts/signup/`, `/cl/accounts/login/`, `/cl/accounts/signup/`  
Ámbito: `templates/`, `deploy_atlantareciclajes/templates/`

---

## Salida cruda (Path:LineNum: Line)

```
templates\public\landing_chile_completa.html:128:      <a href="/cl/es/accounts/login/" class="bg-slate-700 ...
templates\public\landing_chile_completa.html:642:        <a href="/cl/es/accounts/signup/" class="w-full block ...
templates\public\landing_chile_completa.html:673:        <a href="/cl/es/accounts/signup/" ...
templates\public\landing_chile_completa.html:707:        <a href="/cl/es/accounts/signup/" ...
templates\public\landing_chile_completa.html:738:        <a href="/cl/es/accounts/signup/" ...

deploy_atlantareciclajes\templates\templates\auth\signup.html:1024:    // /cl/es/accounts/signup/ → 'CL'

deploy_atlantareciclajes\templates\templates\cl\es\account\signup.html:685:            <a href="/cl/es/accounts/login/">Iniciar sesión</a>

deploy_atlantareciclajes\templates\templates\cl\es\onboarding\bienvenida.html:317:        <a href="/cl/es/accounts/login/" class="futuristic-button">
deploy_atlantareciclajes\templates\templates\cl\es\onboarding\bienvenida.html:320:        <a href="/cl/es/accounts/signup/" ...
deploy_atlantareciclajes\templates\templates\cl\es\onboarding\bienvenida.html:323:        <a href="/cl/es/accounts/signup/" ...
deploy_atlantareciclajes\templates\templates\cl\es\onboarding\bienvenida.html:359:        <a href="/cl/es/accounts/signup/" ...
deploy_atlantareciclajes\templates\templates\cl\es\onboarding\bienvenida.html:362:        <a href="/cl/es/accounts/signup/" ...
deploy_atlantareciclajes\templates\templates\cl\es\onboarding\bienvenida.html:534:          <a href="/cl/es/accounts/signup/" ...
deploy_atlantareciclajes\templates\templates\cl\es\onboarding\bienvenida.html:549:          <a href="/cl/es/accounts/signup/" ...
deploy_atlantareciclajes\templates\templates\cl\es\onboarding\bienvenida.html:568:          <a href="/cl/es/accounts/signup/" ...
deploy_atlantareciclajes\templates\templates\cl\es\onboarding\bienvenida.html:587:          <a href="/cl/es/accounts/signup/" ...
deploy_atlantareciclajes\templates\templates\cl\es\onboarding\bienvenida.html:676:        <a href="/cl/es/accounts/signup/" ...
deploy_atlantareciclajes\templates\templates\cl\es\onboarding\bienvenida.html:679:        <a href="/cl/es/accounts/signup/" ...

deploy_atlantareciclajes\templates\templates\public\landing_chile_completa.html:125:      <a href="/cl/es/accounts/login/" ...
deploy_atlantareciclajes\templates\templates\public\landing_chile_completa.html:157:          <a href="/cl/es/accounts/signup/" ...
deploy_atlantareciclajes\templates\templates\public\landing_chile_completa.html:548:        <a href="/cl/es/accounts/signup/" ...
deploy_atlantareciclajes\templates\templates\public\landing_chile_completa.html:579:        <a href="/cl/es/accounts/signup/" ...
deploy_atlantareciclajes\templates\templates\public\landing_chile_completa.html:613:        <a href="/cl/es/accounts/signup/" ...
deploy_atlantareciclajes\templates\templates\public\landing_chile_completa.html:644:        <a href="/cl/es/accounts/signup/" ...
deploy_atlantareciclajes\templates\templates\public\landing_chile_completa.html:711:          <a href="/cl/es/accounts/signup/" ...
```

---

## Regla de decisión

- **Si el archivo es CL** (ruta `cl/es/`, `landing_chile`, etc.) → puede quedarse hardcode; luego se puede mejorar con `{% url %}`.
- **Si el archivo es de otro país** (uy, ec, mx, co, us, etc.) → BUG, corregir.

---

## Clasificación por archivo

| Archivo | Tipo | Decisión |
|---------|------|----------|
| `templates\public\landing_chile_completa.html` | **CL** (landing Chile) | **OK** — puede quedar o pasarse a `{% url %}` luego. |
| `deploy_atlantareciclajes\...\auth\signup.html` L.1024 | Comentario JS `// /cl/es/accounts/signup/ → 'CL'` | **OK** — no es link, documenta mapeo path→país. |
| `deploy_atlantareciclajes\...\cl\es\account\signup.html` | **CL** (`cl/es/account/signup`) | **OK** |
| `deploy_atlantareciclajes\...\cl\es\onboarding\bienvenida.html` | **CL** (`cl/es/onboarding`) | **OK** |
| `deploy_atlantareciclajes\...\public\landing_chile_completa.html` | **CL** (landing Chile) | **OK** |

---

## Conclusión

- **Bugs (otro país con /cl/):** **0**
- **CL-only o comentario:** todos los hallazgos.

Lista cerrada para tocar en esta auditoría: **ningún archivo**.  
Se puede pasar a **Opción A** (footer `base.html` → `{% url 'legal' %}`) sin sorpresas.

---

## Cómo re-ejecutar

```powershell
cd e:\projecto\e_garage
.\scripts\auditar_hardcodes_cl_templates.ps1
```

O con grep (ripgrep):

```bash
rg "/cl/es/accounts/login/|/cl/es/accounts/signup/|/cl/accounts/login/|/cl/accounts/signup/" --type-add 'html:*.html' -t html templates/ deploy_atlantareciclajes/templates/ -n
```
