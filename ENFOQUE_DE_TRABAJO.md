# Enfoque de trabajo – Sistema crédito rotativo

Cómo enfocar el desarrollo siguiendo el orden de ideas del análisis (sin empezar de cero, reutilizando valorizadores y flujos actuales).

---

## Definición importante: “Línea de crédito” en este sistema

**En este sistema, “línea de crédito” = las cuatro modalidades de plazo que ya usa el valorizador:**

- **Diario**
- **Semanal**
- **Quincenal**
- **Mensual**

Es decir: **línea = tipo_plazo** (`Credito.tipo_plazo`: DIARIO, SEMANAL, QUINCENAL, MENSUAL). No se crean “líneas de crédito” distintas a estas; toda la lógica de plazos, cuotas e intereses sigue apoyada en el **valorizador existente** (`creditos_utils`, `valorizador_views`). Cualquier producto o parametrización que agreguemos debe mapear a una de estas cuatro líneas y usar la misma lógica del valorizador.

---

## Principios

1. **No reemplazar lo que ya funciona:** valorizador, cronograma, cobranza base, clientes, créditos.
2. **Línea = tipo_plazo:** diario, semanal, quincenal, mensual; no introducir un concepto distinto de “cupo global” salvo que el cliente lo pida explícitamente.
3. **Añadir capas:** productos (opcional) → scoring → legal, sin reescribir el núcleo.
4. **MVP primero:** flujo completo “solicitud → desembolso por línea (plazo) → pagos → cobranza” con lo mínimo; después refinamiento.

---

## Orden de trabajo (enfoque recomendado)

### Paso 0 – Validación con el cliente (antes de codificar)

- Confirmar que el **valorizador actual** (diario/semanal/quincenal/mensual) es el que se usará.
- Confirmar si en MVP el pago puede ser **“a un crédito elegido”** o si desde el inicio debe ser **“pago global con reparto automático”**.
- Definir prioridad: ¿productos y línea primero, o scoring/legal desde el inicio?

---

### Fase 1 – Base parametrizada (sin cupo; línea = tipo_plazo)

**Objetivo:** Parametrizar productos que mapean a las **cuatro líneas ya existentes** (diario, semanal, quincenal, mensual) y usan el **mismo valorizador**; no crear concepto de “cupo global”.

| # | Enfoque de trabajo | Detalle |
|---|--------------------|--------|
| 1.1 | **Modelo ProductoCredito (opcional)** | Si se implementa: nombre, **tipo_plazo** (DIARIO/SEMANAL/QUINCENAL/MENSUAL), plazo_min/max_cuotas, tasa_nominal, activo. Cada producto corresponde a una **línea** = un tipo_plazo; la base de cálculo y la fórmula son las del valorizador actual. |
| 1.2 | **Vincular “nuevo crédito” al producto o seguir con tipo_plazo** | Al crear crédito: elegir producto (que fija tipo_plazo y tasa) o, como hoy, elegir directamente tipo_plazo y tasa. El **mismo valorizador** (`creditos_utils`, `generar_cronograma_fechas`, `calcular_credito_informal`) calcula cuotas e intereses. |
| 1.3 | **No crear “LineaCredito” (cupo)** | En este sistema no hay cupo global por cliente; “línea” = diario/semanal/quincenal/mensual. Si en el futuro el cliente pide cupo, se evaluaría entonces. |
| 1.4 | **Reportes de cartera por rangos** | Usar dias_mora para reportes 0, 1-15, 16-30, 31-60, 60+. Opcional: parámetro de provisiones por rango. |

**Entregable Fase 1:** Productos (si se implementan) alineados a las cuatro líneas del valorizador; nuevo crédito sigue usando la misma lógica de cálculo; reportes de cartera por rangos.

---

### Fase 2 – Evaluación crediticia y cobranza

**Objetivo:** Scoring simple; cobranza más rica (gestiones y priorización). “Línea” sigue siendo tipo_plazo (diario/semanal/quincenal/mensual).

| # | Enfoque de trabajo | Detalle |
|---|--------------------|--------|
| 2.1 | **Ingresos y egresos** | Campos en Cliente (o modelo SituacionEconomica): ingresos_mensuales, egresos_mensuales. Usar en scoring y en “cuota/ingreso”. |
| 2.2 | **Motor de scoring por reglas** | Tabla de reglas (variable, condición, puntos) y umbrales (aprobado / rechazado / revisión). Al evaluar solicitud: calcular puntaje y mostrar recomendación; decisión final puede seguir siendo manual. |
| 2.3 | **Aprobar crédito (sin cupo)** | Al aprobar: flujo actual. No hay “asignación de línea de cupo”; el crédito se crea con una de las cuatro líneas (tipo_plazo) y el valorizador calcula igual. |
| 2.4 | **Gestiones de cobranza** | Modelo GestionCobranza: tarea (o cliente/crédito), fecha, tipo (llamada, WhatsApp, visita), resultado (contactado, promesa, acuerdo), fecha_seguimiento. Listar en detalle de tarea/cliente. |
| 2.5 | **Priorización en agenda** | En la cola del cobrador: ordenar por criterio (ej. monto_en_mora × días_mora o por nivel de mora). Ajustar generación de tareas o vista de agenda. |

**Entregable Fase 2:** Evaluación con puntaje y recomendación; cobranza con gestiones y priorización.

---

### Fase 3 – Legal y usura

**Objetivo:** Documentos legales (pagaré, carta instrucción) y control de usura cuando esté definido.

| # | Enfoque de trabajo | Detalle |
|---|--------------------|--------|
| 3.1 | **Pagaré en blanco + carta instrucción** | Plantillas PDF (ReportLab); generación bajo demanda; almacenamiento con referencia a cliente/crédito; opcional: hash, timestamp. |
| 3.2 | **Diligenciamiento (si aplica)** | Cuando se envíe a jurídico: generar PDF con monto total adeudado y fecha; guardar como “pagaré diligenciado”. |
| 3.3 | **Usura (cuando definan fuente)** | Tarea programada que consuma certificación SFC; calcular TEA por producto; bloquear producto si TEA > tope; alerta en backoffice. |

**Entregable Fase 3:** Generación de pagaré y carta; opcionalmente validación de usura y bloqueo de productos.

---

### Después del MVP

- **Motor de distribución de pagos:** un pago que se reparte automáticamente (mora → intereses → capital) entre varias posiciones, si el cliente lo confirma.
- **Refinanciación / consolidación** de posiciones.
- **2FA, JWT** para administradores si lo piden.
- **Integraciones:** API bancaria, WhatsApp, email (según prioridad del cliente).

---

## Cómo usar este enfoque día a día

1. **Sprint / iteración:** Tomar solo los ítems de una fase (ej. 1.1 a 1.4).
2. **No saltar fases:** Tener productos (si aplica) alineados a las cuatro líneas (tipo_plazo) antes de scoring; valorizador siempre como referencia.
3. **Cada ítem:** Diseño breve (modelos, pantallas) → implementación → revisión con lo ya existente (valorizador, flujo de crédito).
4. **Documentar** en el mismo repo qué está “adaptado” (producto, línea) y qué es “nuevo” (legal, usura), para no mezclar suposiciones.

Así el trabajo queda enfocado en el orden indicado y alineado con el análisis previo.
