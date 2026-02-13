# Análisis del requerimiento del cliente vs sistema actual

**Objetivo:** Ver qué podemos adaptar del requerimiento a lo que ya está construido, sin empezar de cero. Se mantienen los **valorizadores y la lógica de cálculo** ya implementada.

---

## Definición en este sistema: “Línea de crédito”

**En este sistema, “línea de crédito” = las cuatro modalidades de plazo que ya usa el valorizador:** Diario, Semanal, Quincenal, Mensual (`Credito.tipo_plazo`: DIARIO, SEMANAL, QUINCENAL, MENSUAL). No se crean líneas de crédito distintas a estas; toda parametrización (productos, etc.) debe mapear a una de estas cuatro y usar la **misma lógica del valorizador** (`creditos_utils`, valorizador_views). Un eventual “cupo global” por cliente sería un concepto aparte y solo si el cliente lo pide.**

---

## 1. Resumen ejecutivo

| Área | En el requerimiento | Qué tenemos hoy | ¿Se puede adaptar? |
|------|---------------------|------------------|--------------------|
| **Cálculo de intereses por plazo** | Diario, semanal, quincenal, mensual parametrizado | Sí: `creditos_utils`, valorizador, `tipo_plazo` en Credito | ✅ **Mantener tal cual** |
| **Línea de crédito + múltiples desembolsos** | En este sistema: **línea = tipo_plazo** (diario/semanal/quincenal/mensual). Cupo global: solo si el cliente lo pide. | Un crédito = un desembolso; tipo_plazo ya define la “línea” (valorizador) | ✅ **Ya existe**: línea = tipo_plazo; múltiples créditos por cliente, cada uno con su línea (plazo). Cupo opcional después. |
| **Productos de crédito (CRUD)** | Productos con plazo min/max, tasa, base de cálculo | `tipo_plazo` fijo en código, tasa por crédito | ⚠️ **Adaptable**: modelo Producto que alimente la misma fórmula |
| **Scoring / evaluación crediticia** | Motor por reglas, aprobación automática, línea asignada | Aprobación manual (botón “Aprobar”) | ⚠️ **Adaptable**: scoring simple por puntos sin ML |
| **Cobranza y asignación** | Pipeline, cobradores, gestiones, priorización | TareaCobro, Cobrador, Ruta, agenda, prioridad | ✅ **Muy alineado**: extender con “gestiones” y priorización |
| **Pagos y orden de imputación** | Un pago se reparte: mora → intereses → capital (varias posiciones) | Un pago = un crédito (y opcionalmente una cuota) | ⚠️ **Fase 2**: mantener “pago a un crédito”; después motor de distribución |
| **Cartera y mora** | Segmentación por días, provisiones, KPIs | Cartera, `dias_mora`, `estado_mora`, reportes | ✅ **Adaptable**: reportes por rangos y provisiones |
| **Pagaré + carta instrucción** | Pagaré en blanco, carta, diligenciamiento, jurídico | No existe | ❌ **Nuevo** (módulo aparte) |
| **Usura (SFC, TEA, bloqueo)** | Cron, límite legal, bloqueo de producto | No existe | ❌ **Nuevo** (tarea + validación en productos) |
| **Frontend SPA (React/Vue)** | Opcional: “o el que estemos usando” | Django + templates | ✅ **Quedarnos con Django** de momento |

Conclusión: una parte importante del requerimiento se puede **adaptar sobre la base actual** (valorizadores, cobranza, cartera, clientes). **Línea de crédito** en este sistema = las cuatro modalidades del valorizador (diario, semanal, quincenal, mensual); no se crean líneas distintas. Otra parte es **evolución** (productos parametrizados, scoring). Y una parte es **nueva** (legal, usura, distribución de pagos multiposición, cupo global solo si el cliente lo pide).

---

## 2. Módulo por módulo (qué adaptar, qué dejar para después)

### Módulo 1: Configuración y parametrización

**Requerimiento:** CRUD de productos (nombre, plazo min/max, tasa, base de cálculo, estado), reglas de elegibilidad, tasas de mora, validación usura (SFC, TEA, bloqueo).

**Hoy:** Plazos y tasas en código y por crédito; mora con `tasa_mora` en el modelo.

**Sugerencia de adaptación:**

- **Productos de crédito:** Crear modelo `ProductoCredito` (nombre, plazo_min/max_dias, tasa_nominal, base_calculo, activo). El **valorizador y la lógica actual** siguen igual; solo que tasa y plazos salen del producto en lugar de estar fijos. En “nuevo crédito” se elige producto (o se mantiene tipo_plazo actual como default).
- **Reglas de elegibilidad y montos máximos por producto/segmento:** Se puede dejar para una segunda fase; al inicio se puede tener “todos los clientes pueden ver todos los productos activos”.
- **Tasas de mora:** Hoy ya hay `tasa_mora` en Credito. Se puede agregar un modelo/config “TasaMora” (porcentaje, vigencia) y usarlo al calcular mora.
- **Usura (SFC, TEA, bloqueo):** Es nuevo. Implica: fuente de dato SFC (archivo/cron), cálculo de TEA por producto, comparación con tope y bloqueo. Sugerencia: dejarlo para cuando el resto de productos y líneas esté estable; luego añadir validación y alertas en backoffice.

No implementar nada aún; solo tener claro que “productos” y “mora parametrizada” encajan bien con lo actual.

---

### Módulo 2: Admisión y evaluación crediticia (scoring)

**Requerimiento:** Formulario dinámico, referencias, ingresos/egresos, huella, motor de scoring por reglas, asignación de línea de crédito.

**Hoy:** Cliente con datos personales, 2 referencias, codeudor; sin ingresos/egresos ni scoring; aprobación manual.

**Sugerencia de adaptación:**

- **Formulario:** Mantener el flujo actual de cliente + codeudor. Agregar campos de **ingresos y egresos declarados** (en Cliente o en un modelo “SituacionEconomica”) para poder usar “cuota/ingreso” en scoring.
- **Scoring por reglas:** Sin ML. Tabla de reglas (variable, condición, puntos) y umbrales (aprobado / rechazado / revisión manual). Al “solicitar” o “evaluar” crédito se calcula puntaje y se sugiere decisión. Se puede seguir aprobando manualmente al inicio y que el sistema solo “recomiende”.
- **Línea de crédito:** En este sistema línea = tipo_plazo (diario/semanal/quincenal/mensual). No hay “asignación de cupo” salvo que se pida después; el crédito se aprueba con una de las cuatro líneas y el valorizador calcula igual.
- **Huella (user agent, IP, fingerprint):** Se puede guardar en la solicitud o en el cliente (campos opcionales) para uso futuro; no es prioritario para MVP.

Prioridad sugerida: primero ingresos/egresos y scoring simple. Línea = tipo_plazo ya está; cupo solo si el cliente lo pide.

---

### Módulo 3: Administración de líneas de crédito

**Requerimiento del documento:** Línea por cliente (monto aprobado, utilizado, disponible, % uso), bloqueos, historial.

**En este sistema:** “Línea de crédito” = **tipo_plazo** (diario, semanal, quincenal, mensual). No hay modelo “LineaCredito” como cupo; cada crédito ya tiene su línea (su `tipo_plazo`) y el valorizador trabaja con esas cuatro líneas.

**Sugerencia de adaptación:**

- **No crear** un modelo “LineaCredito” (cupo global) salvo que el cliente lo pida explícitamente.
- Administración de “líneas” = administrar los **productos o parámetros por tipo_plazo** (ej. tasas por diario/semanal/quincenal/mensual), siempre usando la lógica del valorizador.
- Si más adelante piden cupo por cliente (monto aprobado, utilizado, disponible), entonces sí se podría añadir un modelo de cupo aparte; por ahora nos quedamos con línea = tipo_plazo.

---

### Módulo 4: Desembolsos y posiciones múltiples

**Requerimiento:** Solicitud de desembolso con producto, monto ≤ disponible, plazo; cada desembolso es una posición; interés por posición; liberación de cupo al pagar.

**Hoy:** “Nuevo crédito” con monto, plazo (tipo_plazo + cuotas), tasa; un crédito = un desembolso; valorizador ya calcula intereses.

**Sugerencia de adaptación:**

- **Mantener** que cada `Credito` sea una “posición” (un desembolso). No hace falta otro modelo de “Posicion” si no quieres duplicar; solo documentar que Credito = posición.
- **Interfaz:** En “nuevo crédito”: selector de **línea** = tipo_plazo (diario, semanal, quincenal, mensual) y/o producto si existe ProductoCredito; el **mismo valorizador** calcula. Cupo disponible solo si en el futuro se implementa modelo de cupo.
- **Cálculo de intereses:** Seguir con la lógica actual (valorizador / `creditos_utils`). Las cuatro líneas (tipo_plazo) son la base; cualquier producto solo parametriza tasa/plazo sobre esa base.
- **Liberación de cupo:** Solo aplica si más adelante se añade cupo por cliente; hoy cada crédito es independiente y el saldo se lleva por crédito.

Con esto “desembolsos múltiples” = varios créditos por cliente, cada uno con su línea (tipo_plazo); valorizador sin cambios.

---

### Módulo 5: Pagos y amortización multiposición

**Requerimiento:** Un pago con “motor de distribución”: mora → intereses corrientes → capital (mora más antigua, luego vigente), opción de abono a posición específica.

**Hoy:** Un pago se asocia a un crédito (y opcionalmente a una cuota). No hay distribución automática entre varios créditos.

**Sugerencia de adaptación (por fases):**

- **Fase 1 (MVP):** Mantener “un pago = un crédito elegido por el usuario”. Es lo que ya tienes: el usuario elige a qué crédito aplica el pago. No implementar aún el motor de distribución.
- **Fase 2:** Si el cliente lo exige, introducir “Pago global”: el usuario ingresa un monto total y el sistema lo reparte con el orden mora → intereses → capital por posición (por ejemplo por antigüedad de vencimiento). Eso implica un servicio que cree varios movimientos (o varios Pagos) a partir de uno. Es cambio de modelo y de flujo; conviene definirlo bien (una pantalla específica “Pago multiposición” vs “Pago a un crédito”).

Recomendación: en la primera iteración **no** implementar el motor de distribución; sí dejar claro en documento/funcional que “por ahora el pago es a un crédito elegido” y que el motor queda para una siguiente versión.

---

### Módulo 6: Cobranza y gestión de cartera

**Requerimiento:** Segmentación por días de mora (1–15, 16–30, 31–60, 61+), pipeline por cobrador, registro de gestiones, acuerdos, módulo jurídico.

**Hoy:** TareaCobro, Cobrador, Ruta, agenda, prioridad (ALTA/MEDIA/BAJA), estados (COBRADO, NO_ENCONTRADO, etc.), `dias_mora` y `estado_mora` en Credito.

**Sugerencia de adaptación:**

- **Segmentación:** Ya tienes `estado_mora` y `dias_mora`. Mapear a “Niveles” del cliente (ej. Nivel 1: 1–15, Nivel 2: 16–30, etc.) en reportes y filtros; puede ser solo etiquetas/vistas sobre lo actual.
- **Pipeline / cola:** Ya existe la idea con TareaCobro por cobrador y fecha. **Priorización:** hoy es por prioridad (ALTA/MEDIA/BAJA). Se puede añadir un campo o fórmula “puntuación” (ej. monto × días_mora) y ordenar la agenda por eso.
- **Registro de gestiones:** Hoy hay observaciones y cambio de estado. Se puede agregar un modelo `GestionCobranza` (tarea, fecha, tipo: llamada/WhatsApp/visita, resultado: contactado/promesa/acuerdo, fecha_seguimiento) y vincularlo a TareaCobro o a Credito/Cliente. No sustituye lo actual; lo complementa.
- **Acuerdos (refinanciación/consolidación):** Es más de negocio y flujos; se puede dejar para después de tener líneas y productos claros.
- **Jurídico (certificación de saldo, pagaré, plantillas):** Ligado al Módulo 7; no implementar aún, solo tenerlo en el roadmap.

En resumen: cobranza actual se mantiene y se **enriquece** con segmentación por rangos, priorización y gestiones, sin rehacer todo.

---

### Módulo 7: Documentación legal (pagaré + carta instrucción)

**Requerimiento:** Pagaré en blanco (PDF, QR, campos), carta instrucción, almacenamiento (hash, timestamp), diligenciamiento automático.

**Hoy:** No hay nada de esto.

**Sugerencia:**

- **Nuevo módulo.** No se adapta algo existente; se agrega.
- Ya usas ReportLab para cronograma y recibo; se puede reutilizar para plantillas de pagaré y carta.
- Modelo para guardar: documento (PDF), tipo (pagaré_blanco, carta_instruccion, pagaré_diligenciado), referencia a cliente/línea, hash, fecha, estado.
- Orden sugerido: primero definir con el cliente el texto legal y el formato del pagaré; luego implementar generación y almacenamiento; diligenciamiento automático después.

No implementar hasta que el cliente confirme prioridad y redacción legal.

---

### Módulo 8: Reportes y analítica

**Requerimiento:** Cartera por edades, provisiones, originación, cobranza, rentabilidad, dashboard ejecutivo.

**Hoy:** Gestión de cartera, cartera vencida, KPIs cobradores, recaudación, dashboard con métricas básicas.

**Sugerencia de adaptación:**

- **Cartera por edades:** Con `dias_mora` ya se pueden hacer reportes por rangos (0, 1–15, 16–30, 31–60, 60+). Solo nuevas vistas o filtros.
- **Provisiones:** Parámetros (ej. % por rango de mora) y cálculo en reportes; no cambia el modelo de crédito.
- **Originación:** Contar solicitudes, aprobados, desembolsados por período; muchos datos ya están en Credito (fechas, estados).
- **Cobranza:** Ya hay recaudación por cobrador; se puede sumar “promesas cumplidas/incumplidas” cuando exista registro de gestiones.
- **Dashboard:** Ir añadiendo KPIs (cartera total, vencida, ingresos por intereses) usando los mismos modelos.

Todo esto es **evolución de reportes y dashboard**, no cambio de núcleo.

---

## 3. Restricciones técnicas y no funcionales

- **Backend Python / PostgreSQL:** Ya alineado (Django, soporte PostgreSQL).
- **Frontend:** Cliente dijo “o el que estemos usando”; **mantener Django + templates** y seguir mejorando la UI como hasta ahora.
- **JWT + 2FA:** Actualmente sesión Django. 2FA y/o JWT se pueden añadir después si lo piden.
- **Logs de auditoría:** Añadir registro de quién/hora/IP en acciones críticas (desembolso, pago, cambio de línea); no implica rehacer la app.
- **APIs bancarias, WhatsApp, email:** Hoy hay enlace WhatsApp en confirmación de pago; integraciones profundas son nuevas y se pueden priorizar cuando definan medios de pago (requerimiento punto 5).

---

## 4. Criterios de aceptación MVP (revisados con lo que tenemos)

Lo que el cliente pide vs qué podríamos ofrecer en una primera versión **adaptada**:

| Criterio cliente | En nuestra adaptación |
|------------------|------------------------|
| Admin crea productos con plazos y tasas; bloqueo por usura | Productos (si se implementan) alineados a las cuatro líneas (tipo_plazo); usura en fase 2 (opcional en MVP). |
| Cliente evaluado, línea asignada, múltiples desembolsos | Scoring simple; “línea” = tipo_plazo (diario/semanal/quincenal/mensual); múltiples créditos por cliente, cada uno con su línea; mismo valorizador. Cupo solo si lo piden. |
| Intereses por posición y estado consolidado | Ya: un crédito = una posición; estado consolidado = suma por cliente o por línea. |
| Pago con orden de imputación (mora → intereses → capital) | MVP: pago a un crédito elegido (como ahora). Fase 2: motor de distribución si lo confirman. |
| Cobranza: asignación y gestiones | Mantener y extender: gestiones (llamada, visita, resultado, seguimiento) y priorización. |
| Pagaré + carta instrucción válidos | Módulo nuevo (generación + almacenamiento); diligenciamiento después. |
| Dashboard con KPIs (cartera, vencida, ingresos) | Ampliar el dashboard actual con esos KPIs. |

---

## 5. Orden sugerido (sin implementar aún)

1. **Alineación con el cliente**  
   - Confirmar que el valorizador actual (diario/semanal/quincenal/mensual) es el que se usará.  
   - Definir si en MVP el pago es “siempre a un crédito elegido” o si desde el inicio quieren “pago global con distribución”.  
   - Prioridad de: productos, línea, scoring, legal, usura.

2. **Fase 1 – Base parametrizada (línea = tipo_plazo; sin tocar valorizador)**  
   - Modelo `ProductoCredito` (opcional) alineado a las cuatro líneas (DIARIO, SEMANAL, QUINCENAL, MENSUAL); “nuevo crédito” usa producto o tipo_plazo actual.  
   - No modelo de cupo; “línea” = tipo_plazo.  
   - Reportes de cartera por rangos de mora y, si aplica, provisiones básicas.

3. **Fase 2 – Evaluación y cobranza**  
   - Campos ingresos/egresos; scoring por reglas; recomendación aprobado/rechazado/revisión.  
   - Aprobar crédito con una de las cuatro líneas (tipo_plazo); valorizador igual.  
   - Gestiones de cobranza (tipo, resultado, seguimiento) y priorización en agenda.

4. **Fase 3 – Legal y usura**  
   - Generación de pagaré en blanco y carta instrucción (plantillas + almacenamiento).  
   - Validación usura (cuando definan fuente SFC y regla de tope) y bloqueo de productos.

5. **Después**  
   - Motor de distribución de pagos multiposición (si lo confirman).  
   - Refinanciación/consolidación, 2FA, integraciones bancarias/WhatsApp, etc.

---

## 6. Preguntas que convendría resolver con el cliente

- ¿El cálculo de intereses debe quedar **exactamente** como está hoy (valorizador actual) o habrá cambios de base (360/365, etc.)?  
- ¿En el primer entregable el pago puede ser “siempre a un crédito elegido por el usuario” o es indispensable desde el día 1 el “pago global con reparto automático”?  
- En este sistema línea = tipo_plazo (diario/semanal/quincenal/mensual). ¿Necesitan en algún momento “cupo global” por cliente (monto aprobado, utilizado, disponible) o trabajamos solo con las cuatro líneas actuales?  
- ¿Pagaré + carta instrucción son MVP o se pueden dejar para después de tener productos, línea y cobranza mejorada?  
- ¿Usura (SFC, TEA, bloqueo) es requisito legal inmediato o se puede dejar para una segunda fase?

Cuando tengas sus respuestas (o prioridades), se puede bajar esto a **tareas concretas** (modelos, pantallas, flujos) sin implementar hasta que tú lo indiques.
