[33mcommit d6f9d0150e571421cb02992689ccc179d51a90b3[m[33m ([m[1;32mfeat/document-types-ot-pres-rec-themes[m[33m)[m
Author: Mauricio Alvarado <tu_correo@ejemplo.com>
Date:   Thu Sep 25 01:33:43 2025 -0300

    Fix AJAX endpoints: Add country-aware URLs with language segment
    
    - Replace hardcoded URLs with dynamic data-attributes using country_url tag
    - Fix 404 errors by including /es/ language segment in URLs
    - Update JavaScript to read endpoints from dataset instead of hardcode
    - Add validation for critical endpoints in JavaScript
    - Verify URL resolution works for both Chile (/cl/es/) and USA (/us/)
    - All AJAX endpoints now work correctly in both countries


[33mcommit 68758741814c780de72ece9471e881a352d0054d[m
Author: Mauricio Alvarado <tu_correo@ejemplo.com>
Date:   Sun Sep 7 17:56:43 2025 -0300

    chore: organiza backups y limpia estructura del proyecto
    
    - Mueve e_garage.zip y egarage.zip a _backup/
    - Confirma que gestion_taller es el paquete principal válido
    - No hay conflictos de imports o namespaces
    - Proyecto funcionando correctamente con manage.py apuntando a gestion_taller.settings


[33mcommit f824554df92a3521360d8cc7004b29c5267e4958[m[33m ([m[1;31morigin/chore/templates-refactor-country-lang[m[33m)[m
Author: Mauricio Alvarado <tu_correo@ejemplo.com>
Date:   Tue Sep 2 10:06:17 2025 -0400

    refactor(templates): implement canonical country/lang structure with fallbacks


[33mcommit 1883ebcf3de9d2da52b5244d3692a561177a9576[m
Author: Mauricio Alvarado <tu_correo@ejemplo.com>
Date:   Sun Jul 13 21:12:54 2025 -0400

    Primer commit - proyecto e_garage

 create mode 100644 manage.py
