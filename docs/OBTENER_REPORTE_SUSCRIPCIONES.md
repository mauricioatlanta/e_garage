# 📊 Cómo Obtener el Reporte de Suscripciones

## ⚠️ Problema Actual

Hay un error de configuración con allauth que impide ejecutar comandos de Django directamente. Sin embargo, el servidor web está funcionando, lo que significa que Django SÍ puede conectarse a la base de datos.

## ✅ Solución: Crear un Endpoint de Administración

La mejor solución es crear un endpoint temporal en Django que muestre el reporte. Esto funcionará porque el servidor web ya está corriendo.

### Opción 1: Usar el Panel de Administración de Django

Si tienes acceso al panel de administración:

1. Ve a: `https://atlantareciclajes.pythonanywhere.com/admin/`
2. Inicia sesión como superusuario
3. Desde allí puedes ver las empresas y suscripciones

### Opción 2: Crear un Endpoint Temporal

Crea una vista temporal que muestre el reporte. Esto funcionará porque el servidor web ya está corriendo.

### Opción 3: Verificar Credenciales en PythonAnywhere Dashboard

1. Ve a https://www.pythonanywhere.com/
2. Click en "Databases"
3. Busca tu base de datos
4. Verifica el usuario y contraseña
5. Luego ejecuta el script con las credenciales correctas

## 🔍 Verificar Credenciales desde el Dashboard

En el dashboard de PythonAnywhere:

1. Ve a "Databases"
2. Busca la base de datos `atlantareciclajes$egarage`
3. Verás el usuario y podrás resetear la contraseña si es necesario
4. Usa esas credenciales en el script

## 📝 Script Final con Credenciales Correctas

Una vez que tengas las credenciales correctas del dashboard, ejecuta:

```bash
cd /home/atlantareciclajes/apps/egarage/current

python << 'ENDPYTHON'
import pymysql

# REEMPLAZA ESTOS VALORES CON LOS DEL DASHBOARD
DB_HOST = "atlantareciclajes.mysql.pythonanywhere-services.com"
DB_NAME = "atlantareciclajes$egarage".replace("$", "")
DB_USER = "atlantareciclajes"  # Verifica en dashboard
DB_PASSWORD = "TU_CONTRASEÑA_AQUI"  # Obtén del dashboard
DB_PORT = 3306

try:
    connection = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        port=DB_PORT,
        cursorclass=pymysql.cursors.DictCursor
    )
    
    print("=" * 80)
    print("📊 REPORTE DE SUSCRIPCIONES ACTIVAS")
    print("=" * 80)
    
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) as total FROM taller_empresa WHERE suscripcion_activa = 1")
        total_empresas = cursor.fetchone()["total"]
        
        cursor.execute("SELECT COUNT(*) as total FROM taller_suscripcion WHERE activa = 1")
        total_suscripciones = cursor.fetchone()["total"]
        
        cursor.execute("SELECT COUNT(*) as total FROM taller_trialregistro WHERE prueba_activa = 1")
        total_trials = cursor.fetchone()["total"]
        
        print(f"\n📈 ESTADÍSTICAS GENERALES")
        print(f"Total Empresas Activas: {total_empresas}")
        print(f"Total Suscripciones Activas: {total_suscripciones}")
        print(f"Total Trials Activos: {total_trials}")
        
        cursor.execute("""
            SELECT pais, COUNT(*) as total,
                   SUM(CASE WHEN plan = 'trial' THEN 1 ELSE 0 END) as trials
            FROM taller_empresa
            WHERE suscripcion_activa = 1
            GROUP BY pais
            ORDER BY pais
        """)
        paises = cursor.fetchall()
        
        print("\n🌍 RESUMEN POR PAÍS:")
        for row in paises:
            print(f"  {row['pais']}: {row['total']} empresas ({row['trials']} trials)")
        
        for row in paises:
            pais_codigo = row["pais"]
            print(f"\n{'=' * 80}")
            print(f"🌍 PAÍS: {pais_codigo}")
            print("=" * 80)
            
            cursor.execute("""
                SELECT e.nombre_taller, e.plan, u.username, u.email, 
                       e.fecha_inicio, e.fecha_fin
                FROM taller_empresa e
                LEFT JOIN auth_user u ON e.user_id = u.id
                WHERE e.pais = %s AND e.suscripcion_activa = 1
                ORDER BY e.nombre_taller
            """, (pais_codigo,))
            
            empresas = cursor.fetchall()
            
            for idx, emp in enumerate(empresas, 1):
                es_trial = "TRIAL" if emp["plan"] == "trial" else emp["plan"].upper()
                print(f"\n  {idx}. ✅ {emp['nombre_taller']}")
                print(f"     Usuario: {emp['username']}")
                print(f"     Email: {emp['email']}")
                print(f"     Plan: {es_trial}")
                print(f"     Fecha Inicio: {emp['fecha_inicio']}")
                print(f"     Fecha Fin: {emp['fecha_fin']}")
    
    connection.close()
    print("\n✅ Reporte completado")
    
except Exception as e:
    print(f"❌ Error: {e}")
ENDPYTHON
```

## 🎯 Próximos Pasos

1. **Verifica las credenciales en el dashboard de PythonAnywhere**
2. **Reemplaza `TU_CONTRASEÑA_AQUI` con la contraseña correcta**
3. **Ejecuta el script**

O si prefieres, puedo crear un endpoint en Django que muestre este reporte cuando accedas desde el navegador. ¿Qué prefieres?



