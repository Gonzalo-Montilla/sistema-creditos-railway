# 🧪 GUÍA DE PRUEBAS LOCALES - SISTEMA DE CRÉDITOS

Esta guía te ayudará a probar exhaustivamente el sistema antes de subirlo a producción.

## 🚀 INICIAR SERVIDOR DE DESARROLLO

```bash
python manage.py runserver
```

El sistema estará disponible en: `http://127.0.0.1:8000/`

## ✅ LISTA DE PRUEBAS REQUERIDAS

### 1. **PRUEBAS DEL VALORIZADOR** 🧮
- [ ] **Acceder al valorizador**: `/valorizador/`
- [ ] **Probar cálculo diario**: 
  - Monto: $1,000,000
  - Tasa mensual: 20%
  - Tipo: Diario, 30 cuotas
  - ✅ **Resultado esperado**: Cuota ≈ $33,333
- [ ] **Probar cálculo semanal**:
  - Monto: $500,000
  - Tasa mensual: 15%
  - Tipo: Semanal, 8 cuotas
  - ✅ **Resultado esperado**: Cuota ≈ $76,389
- [ ] **Probar cálculo quincenal**:
  - Monto: $300,000
  - Tasa mensual: 10%
  - Tipo: Quincenal, 6 cuotas
  - ✅ **Resultado esperado**: Cuota ≈ $65,000
- [ ] **Probar cálculo mensual**:
  - Monto: $200,000
  - Tasa mensual: 5%
  - Tipo: Mensual, 12 cuotas
  - ✅ **Resultado esperado**: Cuota ≈ $20,833

### 2. **CRONOGRAMA DE PAGOS** 📅
- [ ] **Verificar fechas correctas** según tipo de plazo
- [ ] **Resaltado de fines de semana** (filas amarillas)
- [ ] **Días de la semana correctos** (no todos "jueves")
- [ ] **Alerta de fines de semana** al final del cronograma

### 3. **GESTIÓN DE CLIENTES** 👥
- [ ] **Crear cliente nuevo**:
  - Nombres, apellidos, cédula
  - Celular, dirección, barrio
  - Subir fotos de documentos
- [ ] **Editar cliente existente**
- [ ] **Búsqueda por cédula** en formularios
- [ ] **Visualización de documentos**

### 4. **GESTIÓN DE CRÉDITOS** 💳
- [ ] **Crear crédito nuevo**:
  - Buscar cliente por cédula
  - Configurar monto, tasa mensual
  - Seleccionar tipo de plazo y cuotas
  - **Verificar calculadora en tiempo real**
- [ ] **Estados de crédito**:
  - SOLICITADO → APROBADO → DESEMBOLSADO
  - Generar cronograma automático al desembolsar
- [ ] **Visualización en lista de créditos**:
  - Mostrar modalidad (ej: "30 diarios")
  - Tasa mensual correcta

### 5. **CÁLCULOS MATEMÁTICOS** 🔢
**Fórmula de interés simple aplicada:**
- Interés = Capital × Tasa Mensual × Tiempo (meses)
- Total = Capital + Interés
- Cuota = Total ÷ Número de cuotas

**Verificar conversiones de tiempo:**
- Diario: cuotas ÷ 30 = meses
- Semanal: cuotas ÷ 4.33 = meses  
- Quincenal: cuotas ÷ 2 = meses
- Mensual: cuotas = meses

### 6. **CRONOGRAMAS REALES** 📊
- [ ] **Al desembolsar un crédito**:
  - Se genera cronograma automáticamente
  - Fechas de vencimiento correctas
  - Detección de fines de semana
- [ ] **Pagos**:
  - Registrar pagos contra cuotas específicas
  - Actualización de estados

### 7. **CASOS DE PRUEBA ESPECÍFICOS** 🎯

#### Caso 1: Crédito Diario Típico
- **Cliente**: Juan Pérez, CC 12345678
- **Crédito**: $500,000 al 25% mensual, 30 días
- **Resultado esperado**: 
  - Tiempo: 1 mes
  - Interés: $125,000
  - Total: $625,000
  - Cuota diaria: $20,833

#### Caso 2: Crédito Semanal
- **Cliente**: María García, CC 87654321
- **Crédito**: $1,000,000 al 20% mensual, 12 semanas
- **Resultado esperado**:
  - Tiempo: 2.77 meses
  - Interés: $554,000
  - Total: $1,554,000
  - Cuota semanal: $129,500

#### Caso 3: Crédito Quincenal
- **Cliente**: Pedro López, CC 11223344
- **Crédito**: $300,000 al 15% mensual, 4 quincenas
- **Resultado esperado**:
  - Tiempo: 2 meses
  - Interés: $90,000
  - Total: $390,000
  - Cuota quincenal: $97,500

### 8. **PRUEBAS DE VALIDACIÓN** ⚠️
- [ ] **Montos inválidos**: $0, valores negativos
- [ ] **Tasas inválidas**: valores negativos
- [ ] **Cuotas inválidas**: 0, valores negativos
- [ ] **Cédulas inexistentes** en formularios
- [ ] **Campos requeridos** vacíos

### 9. **COMPATIBILIDAD Y RENDIMIENTO** 💻
- [ ] **Navegadores**: Chrome, Firefox, Edge
- [ ] **Responsividad**: Móvil, tablet, desktop
- [ ] **Velocidad**: Cálculos en tiempo real fluidos
- [ ] **Carga de archivos**: Fotos de documentos

## 🐛 ERRORES CONOCIDOS A VERIFICAR

1. **Modal de carga se queda abierto**: ❌ Corregido
2. **Días todos aparecen como "jueves"**: ❌ Corregido  
3. **Falta resaltado de fines de semana**: ❌ Corregido
4. **Cálculos inconsistentes**: ❌ Corregido con lógica unificada

## 📝 REGISTRO DE PRUEBAS

### Formato de reporte:
```
FECHA: [DD/MM/YYYY]
PRUEBA: [Nombre de la prueba]
ESTADO: ✅ EXITOSA / ❌ FALLIDA
DETALLES: [Descripción de resultados]
ERRORES ENCONTRADOS: [Si aplica]
```

## 🚀 PREPARACIÓN PARA PRODUCCIÓN

Cuando todas las pruebas estén ✅:

### 1. **Backup de Base de Datos**
```bash
python manage.py dumpdata > backup_antes_produccion.json
```

### 2. **Verificación Final**
- [ ] Todos los tests pasados
- [ ] No errores en consola de navegador
- [ ] No errores en logs de Django
- [ ] Rendimiento aceptable

### 3. **Archivos para Producción**
- [ ] `creditos_utils.py` - Funciones centralizadas
- [ ] `models.py` - Modelo actualizado
- [ ] `forms.py` - Formularios actualizados
- [ ] Templates actualizados
- [ ] `migrar_creditos_existentes.py` - Para migrar datos en producción

### 4. **Migración en Producción**
```bash
# En el servidor de producción:
python manage.py migrate
python migrar_creditos_existentes.py  # Solo si hay datos existentes
```

## 🎯 CRITERIOS DE ÉXITO

El sistema está listo para producción cuando:
- ✅ Todos los cálculos son matemáticamente correctos
- ✅ Valorizador y sistema de créditos usan la misma lógica
- ✅ Cronogramas muestran fechas reales y días correctos
- ✅ No hay errores de JavaScript o Python
- ✅ La experiencia de usuario es fluida
- ✅ Los formularios validan correctamente los datos

## 💡 TIPS PARA PRUEBAS

1. **Usa datos realistas**: Montos típicos colombianos ($100,000 - $5,000,000)
2. **Prueba casos extremos**: Montos muy altos, muchas cuotas
3. **Verifica fórmulas**: Usa calculadora externa para comparar
4. **Testa en diferentes dispositivos**
5. **Documenta cualquier comportamiento extraño**

¡Éxito con las pruebas! 🍀