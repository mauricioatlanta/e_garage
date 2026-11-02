# Reporte de Seguridad

**Fecha:** 2025-09-17 22:41:32

**Paquetes vulnerables:** 5
**Total vulnerabilidades:** 10

## Vulnerabilidades

### django v5.1.6

- **PYSEC-2025-13**
  - CVE: CVE-2025-26699
  - Versión segura: 4.2.20, 5.0.13, 5.1.7
  - An issue was discovered in Django 5.1 before 5.1.7, 5.0 before 5.0.13, and 4.2 before 4.2.20. The django.utils.text.wrap() method and wordwrap template filter are subject to a potential denial-of-service attack when used with very long strings.

- **PYSEC-2025-37**
  - CVE: CVE-2025-32873
  - Versión segura: 4.2.21, 5.1.9, 5.2.1
  - An issue was discovered in Django 4.2 before 4.2.21, 5.1 before 5.1.9, and 5.2 before 5.2.1. The django.utils.html.strip_tags() function is vulnerable to a potential denial-of-service (slow performance) when processing inputs containing large sequences of incomplete HTML tags. The template filter striptags is also vulnerable, because it is built on top of strip_tags().

- **PYSEC-2025-14**
  - CVE: CVE-2025-27556
  - Versión segura: 5.0.14, 5.1.8
  - An issue was discovered in Django 5.1 before 5.1.8 and 5.0 before 5.0.14. The NFKC normalization is slow on Windows. As a consequence, django.contrib.auth.views.LoginView, django.contrib.auth.views.LogoutView, and django.views.i18n.set_language are subject to a potential denial-of-service attack via certain inputs with a very large number of Unicode characters.

- **PYSEC-2025-47**
  - CVE: CVE-2025-48432
  - Versión segura: 4.2.22, 5.1.10, 5.2.2
  - An issue was discovered in Django 5.2 before 5.2.2, 5.1 before 5.1.10, and 4.2 before 4.2.22. Internal HTTP response logging does not escape request.path, which allows remote attackers to potentially manipulate log output via crafted URLs. This may lead to log injection or forgery when logs are viewed in terminals or processed by external systems.

- **GHSA-6w2r-r2m5-xq5w**
  - CVE: CVE-2025-57833
  - Versión segura: 4.2.24, 5.1.12, 5.2.6
  - An issue was discovered in Django 4.2 before 4.2.24, 5.1 before 5.1.12, and 5.2 before 5.2.6. FilteredRelation is subject to SQL injection in column aliases, using a suitably crafted dictionary, with dictionary expansion, as the **kwargs passed QuerySet.annotate() or QuerySet.alias().

### pillow v11.2.1

- **PYSEC-2025-61**
  - CVE: GHSA-xg8h-j46f-w952, CVE-2025-48379
  - Versión segura: 11.3.0
  - Pillow is a Python imaging library. In versions 11.2.0 to before 11.3.0, there is a heap buffer overflow when writing a sufficiently large (>64k encoded with default settings) image in the DDS format due to writing into a buffer without checking for available space. This only affects users who save untrusted data as a compressed DDS image. This issue has been patched in version 11.3.0.

### pypdf v5.4.0

- **GHSA-7hfw-26vp-jp8m**
  - CVE: CVE-2025-55197
  - Versión segura: 6.0.0
  - ### Impact An attacker who uses this vulnerability can craft a PDF which leads to the RAM being exhausted. This requires just reading the file if a series of FlateDecode filters is used on a malicious cross-reference stream. Other content streams are affected on explicit access.  ### Patches This has been fixed in [pypdf==6.0.0](https://github.com/py-pdf/pypdf/releases/tag/6.0.0).  ### Workarounds If you cannot upgrade yet, you might want to implement the workaround for `pypdf.filters.decompress` yourself: https://github.com/py-pdf/pypdf/blob/0dd57738bbdcdb63f0fb43d8a6b3d222b6946595/pypdf/filters.py#L72-L143  ### References This issue has been reported in #3429 and fixed in #3430.

### requests v2.32.3

- **GHSA-9hjg-9r4m-mvj7**
  - CVE: CVE-2024-47081
  - Versión segura: 2.32.4
  - ### Impact  Due to a URL parsing issue, Requests releases prior to 2.32.4 may leak .netrc credentials to third parties for specific maliciously-crafted URLs.  ### Workarounds For older versions of Requests, use of the .netrc file can be disabled with `trust_env=False` on your Requests Session ([docs](https://requests.readthedocs.io/en/latest/api/#requests.Session.trust_env)).  ### References https://github.com/psf/requests/pull/6965 https://seclists.org/fulldisclosure/2025/Jun/2

### urllib3 v2.4.0

- **GHSA-48p4-8xcf-vxj5**
  - CVE: CVE-2025-50182
  - Versión segura: 2.5.0
  - urllib3 [supports](https://urllib3.readthedocs.io/en/2.4.0/reference/contrib/emscripten.html) being used in a Pyodide runtime utilizing the [JavaScript Fetch API](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API) or falling back on [XMLHttpRequest](https://developer.mozilla.org/en-US/docs/Web/API/XMLHttpRequest). This means you can use Python libraries to make HTTP requests from your browser or Node.js. Additionally, urllib3 provides [a mechanism](https://urllib3.readthedocs.io/en/2.4.0/user-guide.html#retrying-requests) to control redirects.  However, the `retries` and `redirect` parameters are ignored with Pyodide; the runtime itself determines redirect behavior.   ## Affected usages  Any code which relies on urllib3 to control the number of redirects for an HTTP request in a Pyodide runtime.   ## Impact  Redirects are often used to exploit SSRF vulnerabilities. An application attempting to mitigate SSRF or open redirect vulnerabilities by disabling redirects may remain vulnerable if a Pyodide runtime redirect mechanism is unsuitable.   ## Remediation  If you use urllib3 in Node.js, upgrade to a patched version of urllib3.  Unfortunately, browsers provide no suitable way which urllib3 can use: `XMLHttpRequest` provides no control over redirects, the Fetch API returns `opaqueredirect` responses lacking data when redirects are controlled manually. Expect default browser behavior for redirects.

- **GHSA-pq67-6m6q-mj2v**
  - CVE: CVE-2025-50181
  - Versión segura: 2.5.0
  - urllib3 handles redirects and retries using the same mechanism, which is controlled by the `Retry` object. The most common way to disable redirects is at the request level, as follows:  ```python resp = urllib3.request("GET", "https://httpbin.org/redirect/1", redirect=False) print(resp.status) # 302 ```  However, it is also possible to disable redirects, for all requests, by instantiating a `PoolManager` and specifying `retries` in a way that disable redirects:  ```python import urllib3  http = urllib3.PoolManager(retries=0)  # should raise MaxRetryError on redirect http = urllib3.PoolManager(retries=urllib3.Retry(redirect=0))  # equivalent to the above http = urllib3.PoolManager(retries=False)  # should return the first response  resp = http.request("GET", "https://httpbin.org/redirect/1") ```  However, the `retries` parameter is currently ignored, which means all the above examples don't disable redirects.  ## Affected usages  Passing `retries` on `PoolManager` instantiation to disable redirects or restrict their number.  By default, requests and botocore users are not affected.  ## Impact  Redirects are often used to exploit SSRF vulnerabilities. An application attempting to mitigate SSRF or open redirect vulnerabilities by disabling redirects at the PoolManager level will remain vulnerable.  ## Remediation  You can remediate this vulnerability with the following steps:   * Upgrade to a patched version of urllib3. If your organization would benefit from the continued support of urllib3 1.x, please contact [sethmichaellarson@gmail.com](mailto:sethmichaellarson@gmail.com) to discuss sponsorship or contribution opportunities.  * Disable redirects at the `request()` level instead of the `PoolManager()` level.
