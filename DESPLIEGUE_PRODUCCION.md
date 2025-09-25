# 🚀 DESPLIEGUE A PRODUCCIÓN - SISTEMA DE CRÉDITOS

Esta guía te ayudará a subir las actualizaciones de forma segura a producción.

## 📋 CHECKLIST PRE-DESPLIEGUE

### ✅ Verificaciones Locales Completadas:
- [x] **Lógica unificada** - Valorizador y sistema usan interés simple
- [x] **Validación de cédulas** - Acepta 5-10 dígitos 
- [x] **Cronogramas correctos** - Fechas reales y días de semana
- [x] **Modal de carga** - Se cierra automáticamente
- [x] **Cálculos matemáticos** - Verificados y consistentes
- [x] **Navegación** - Valorizador bien posicionado
- [x] **Base de datos limpia** - Datos de prueba eliminados

## 🔧 ARCHIVOS MODIFICADOS PARA SUBIR:

### **Archivos Principales:**
```
main/
├── creditos_utils.py          # ⭐ NUEVO - Funciones centralizadas
├── models.py                  # 🔄 MODIFICADO - Lógica actualizada
├── forms.py                   # 🔄 MODIFICADO - Validación cédulas
├── valorizador_views.py       # 🔄 MODIFICADO - Usa funciones centralizadas
├── templates/
│   ├── base.html             # 🔄 MODIFICADO - Navbar reordenado
│   ├── nuevo_credito.html    # 🔄 MODIFICADO - Calculadora actualizada
│   ├── creditos.html         # 🔄 MODIFICADO - Nueva modalidad
│   └── valorizador/
│       └── valorizador.html  # 🔄 MODIFICADO - Cronograma mejorado
└── migrations/
    └── 0011_actualizar_validacion_cedula.py  # ⭐ NUEVA
```

### **Scripts de Utilidad:**
```
migrar_creditos_existentes.py    # Para migrar datos existentes
backup_sistema.py                # Para backup antes del despliegue
GUIA_PRUEBAS.md                  # Para testing post-despliegue
```

## 🚀 PROCESO DE DESPLIEGUE

### **PASO 1: Backup de Producción** 
```bash
# En el servidor de producción:
python manage.py dumpdata > backup_pre_actualizacion_$(date +%Y%m%d_%H%M%S).json

# Verificar que el backup se creó:
ls -la backup_pre_actualizacion_*.json
```

### **PASO 2: Subir Archivos al Servidor**
```bash
# Opción A: Git (recomendado)
git add .
git commit -m "feat: Nueva lógica de créditos informales y validación cédulas 5-10 dígitos"
git push origin main

# En el servidor:
git pull origin main

# Opción B: SCP/SFTP (si no usas Git)
scp -r main/ usuario@servidor:/path/to/sistema-creditos/
```

### **PASO 3: Instalar Dependencias** (si hay nuevas)
```bash
# En el servidor de producción:
pip install -r requirements.txt
```

### **PASO 4: Aplicar Migraciones**
```bash
# En el servidor de producción:
python manage.py migrate

# Verificar migraciones:
python manage.py showmigrations main
```

### **PASO 5: Migrar Datos Existentes** (solo si hay datos)
```bash
# Si hay créditos existentes en producción:
python migrar_creditos_existentes.py

# ⚠️ IMPORTANTE: Este script preguntará 3 veces antes de proceder
```

### **PASO 6: Collectstatic** (si usas archivos estáticos)
```bash
python manage.py collectstatic --noinput
```

### **PASO 7: Reiniciar Servicios**
```bash
# Para Apache:
sudo systemctl restart apache2

# Para Nginx + Gunicorn:
sudo systemctl restart gunicorn
sudo systemctl restart nginx

# Para desarrollo (no usar en producción):
# python manage.py runserver 0.0.0.0:8000
```

## 🧪 VERIFICACIÓN POST-DESPLIEGUE

### **Pruebas Críticas a Realizar:**

1. **🧮 Valorizador**
   - [ ] Acceder a `/valorizador/`
   - [ ] Calcular crédito diario: $1,000,000, 20%, 30 días
   - [ ] Verificar cronograma con fechas correctas
   - [ ] Confirmar resaltado de fines de semana

2. **👥 Gestión de Clientes**
   - [ ] Crear cliente con cédula de 5 dígitos: `16789`
   - [ ] Crear cliente con cédula de 8 dígitos: `12345678`
   - [ ] Verificar que rechaza cédulas de 4 dígitos

3. **💳 Gestión de Créditos**
   - [ ] Crear crédito nuevo con calculadora en tiempo real
   - [ ] Verificar que usa la nueva lógica de interés simple
   - [ ] Desembolsar y verificar cronograma generado

4. **📊 Funcionalidad General**
   - [ ] Navegación fluida entre secciones
   - [ ] No errores en consola de navegador
   - [ ] No errores en logs del servidor

## ⚠️ PLAN DE ROLLBACK

Si algo sale mal, puedes revertir:

### **Rollback de Base de Datos:**
```bash
# Restaurar backup:
python manage.py flush --noinput
python manage.py loaddata backup_pre_actualizacion_YYYYMMDD_HHMMSS.json
```

### **Rollback de Código:**
```bash
# Si usas Git:
git revert HEAD
git push origin main

# En el servidor:
git pull origin main
python manage.py migrate
sudo systemctl restart apache2  # o tu servidor web
```

## 🔍 MONITOREO POST-DESPLIEGUE

### **Logs a Revisar:**
```bash
# Logs de Django (ajustar ruta según tu configuración):
tail -f /var/log/django/sistema_creditos.log

# Logs del servidor web:
tail -f /var/log/apache2/error.log
# o
tail -f /var/log/nginx/error.log
```

### **Métricas a Monitorear:**
- ✅ Tiempo de respuesta de páginas
- ✅ Errores 500/404
- ✅ Uso de memoria/CPU
- ✅ Conexiones a base de datos

## 📱 COMUNICACIÓN CON USUARIOS

### **Mensaje Sugerido:**
```
🚀 ACTUALIZACIÓN DEL SISTEMA

Estimados usuarios,

Hemos actualizado el sistema con las siguientes mejoras:

✅ Nuevo valorizador de créditos más preciso
✅ Soporte para cédulas desde 5 dígitos
✅ Cronogramas con fechas reales
✅ Interfaz mejorada y más rápida

La actualización ya está activa. Si encuentran algún 
inconveniente, reporten inmediatamente.

¡Gracias por su comprensión!
```

## 🎯 CRITERIOS DE ÉXITO

El despliegue es exitoso cuando:
- ✅ Todos los servicios responden correctamente
- ✅ No hay errores en logs durante 30 minutos
- ✅ Los usuarios pueden crear clientes y créditos
- ✅ El valorizador calcula correctamente
- ✅ Los cronogramas muestran fechas reales

## 🆘 CONTACTOS DE EMERGENCIA

En caso de problemas críticos:
- **Desarrollador:** [Tu contacto]
- **Servidor/Hosting:** [Contacto del proveedor]
- **Base de datos:** [Contacto del DBA si aplica]

---

## 🎉 NOTAS FINALES

Esta actualización representa una mejora significativa:
- **Lógica unificada** entre valorizador y sistema
- **Mayor precisión** en cálculos de créditos informales
- **Mejor experiencia** de usuario
- **Soporte completo** para cédulas colombianas

¡Buena suerte con el despliegue! 🍀