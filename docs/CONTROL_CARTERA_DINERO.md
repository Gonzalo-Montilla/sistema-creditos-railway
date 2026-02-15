# Control quirúrgico del dinero – Cartera y flujo de caja

Objetivo: tener una sola fuente de verdad para **lo que se presta**, **lo que se cobra** y **lo que se debe**, y poder conciliar en cualquier momento.

---

## 1. Qué hay hoy en el sistema

### Modelos que mueven dinero

| Concepto | Dónde está | Uso |
|----------|------------|-----|
| **Lo prestado** | `Credito.monto` (y `fecha_desembolso` cuando se entrega) | Monto desembolsado por crédito |
| **Lo que debe pagar el cliente** | `Credito.monto_total` | Monto total a pagar (capital + interés) |
| **Lo cobrado** | Tabla `Pago`: cada fila es un pago (monto, crédito, fecha) | Suma de pagos = total cobrado por crédito |
| **Lo que falta por cobrar** | Calculado: `monto_total - total_pagado()` = `saldo_pendiente()` | No se guarda en un campo; se calcula |

### Bloque “Gestión de cartera”

- **Gestión de cartera** (`gestion_cartera`): muestra **cartera total**, **al día**, **vencida**, % vencida, pagos del día, meta, créditos por mora. Usa **saldo pendiente** (suma de lo que falta por cobrar). Correcto para “dinero por recuperar”.
- **Cartera vencida** (`cartera_vencida`): listado de créditos en mora con filtros (estado mora, días, cobrador) y exportar Excel.
- **Actualizar cartera** (`actualizar_cartera`): recalcula `dias_mora`, `estado_mora`, `interes_moratorio` en cada crédito y opcionalmente genera `CarteraAnalisis` del día.
- **CarteraAnalisis** (modelo): guarda una “foto” diaria (cartera_total, cartera_al_dia, cartera_vencida, porcentaje vencida, pagos del día, etc.) para historial y gráficos.

### Dashboard principal

- Muestra total recaudado (Sum de `Pago.monto`), desembolsos del día, pagos del día, etc.

---

## 2. Inconsistencia importante detectada

- **Vista Gestión de cartera** calcula:
  - **Cartera total** = suma de **saldo_pendiente()** de cada crédito (lo que realmente falta por cobrar). ✅ Coherente con “control del dinero”.
- **Modelo CarteraAnalisis** (usado en “Actualizar cartera” y en cron):
  - **cartera_total** = Sum(**monto_total**) de todos los créditos activos.
  - Eso es “suma de deuda contratada”, no “suma de saldos pendientes”.

Ejemplo: un crédito con `monto_total` 1.000.000 y 500.000 ya pagados tiene **saldo** 500.000. La vista lo cuenta como 500.000; el análisis diario lo contaría como 1.000.000. Por eso:

- Lo que ves en **Gestión de cartera** (pantalla) es correcto para “cuánto me deben”.
- Cualquier reporte o historial que use **CarteraAnalisis** está usando otra definición de “cartera” y no sirve para conciliar dinero.

**Recomendación:** unificar todo en **saldo pendiente** (lo que falta por cobrar). CarteraAnalisis debería guardar suma de saldos, no suma de `monto_total`.

---

## 3. Ecuación de control del dinero (conciliación)

En un sistema sano debería cumplirse:

- **Total desembolsado** (suma de `Credito.monto` de créditos ya desembolsados)  
  ≈ **Total cobrado** (suma de `Pago.monto`) + **Saldo en cartera** (suma de `saldo_pendiente()` de créditos con saldo > 0)

Ajustes:

- Créditos **pagados** (saldo 0): ya no están “en cartera”; su monto fue desembolsado y luego cobrado.
- Créditos **cancelados/anulados** sin desembolso no cuentan en “total desembolsado”.
- Si hay **ajustes** (abonos, notas crédito, etc.) deben estar registrados como movimientos (por ejemplo como pagos o en una tabla de ajustes) para que la ecuación siga cerrando.

Hoy no existe una pantalla ni reporte que muestre explícitamente esta ecuación (desembolsado = cobrado + saldo).

---

## 4. Sugerencias para un control robusto

### A) Unificar definición de “cartera” (prioridad alta)

- En **CarteraAnalisis.generar_analisis_diario** (y cualquier método que llene cartera_total / cartera_al_dia / cartera_vencida):
  - No usar `Sum('monto_total')`.
  - Calcular, por cada crédito activo, `saldo_pendiente()` y sumar esos saldos para:
    - cartera_total
    - cartera_al_dia (solo créditos con estado_mora = AL_DIA)
    - cartera_vencida (resto)
- Así, “cartera” siempre significa **dinero por recuperar**, y cuadra con la vista de Gestión de cartera y con la ecuación de conciliación.

### B) Vista o bloque “Resumen del dinero” / Conciliación (prioridad alta)

Una sola pantalla (o sección destacada en Gestión de cartera) que muestre:

- **Total desembolsado:** Sum(`Credito.monto`) donde estado en (DESEMBOLSADO, VENCIDO, PAGADO) y `fecha_desembolso` no nula.
- **Total cobrado histórico:** Sum(`Pago.monto`) de todos los pagos.
- **Saldo en cartera:** Sum(`saldo_pendiente()`) de créditos con estado DESEMBOLSADO/VENCIDO y saldo > 0.
- **Comprobación:**  
  `Total desembolsado ≈ Total cobrado + Saldo en cartera`  
  (se puede permitir una pequeña diferencia por redondeos; si es grande, alertar).

Opcional: desglose por cobrador o por período (desembolsado en el mes, cobrado en el mes).

### C) Validación al registrar pagos (prioridad media)

- Al crear un **Pago** (desde “Nuevo pago” o desde “Registrar cobro” en agenda):
  - Si `total_pagado + nuevo_pago > monto_total` del crédito:
    - Opción 1: rechazar el pago y avisar “supera el monto total del crédito”.
    - Opción 2: permitir pero marcar el crédito como “sobrepagado” o “ajuste” y dejar un aviso en pantalla.
- Así se evita que, por error, se “cobre de más” y se rompa la lógica de saldo.

### D) Reporte “Conciliación por crédito” (prioridad media)

- Export (Excel o PDF) con una fila por crédito (activo o cerrado) con al menos un pago o saldo:
  - ID crédito, cliente, monto (desembolsado), monto_total, total_pagado, saldo_pendiente, estado, estado_mora.
- Al final: totales (total desembolsado, total cobrado, total saldo) para comparar con el resumen global.
- Sirve para auditoría y para detectar créditos con datos raros (por ejemplo saldo negativo si en el futuro se relaja la validación).

### E) Historial / auditoría de movimientos de dinero (prioridad media-baja)

- Hoy cada **Pago** ya es un movimiento; el “historial” es la tabla Pago.
- Opcional: tabla **MovimientoCartera** (tipo: DESEMBOLSO | PAGO | AJUSTE, monto, crédito, usuario, fecha, referencia). Cada desembolso y cada pago (y en el futuro cada ajuste) podría generar una fila para:
  - Un solo lugar donde “todo lo que movió dinero” quede registrado.
  - Reportes de flujo de caja por período sin tocar varias tablas.
- Si no quieres otra tabla, al menos un **reporte de pagos** por rango de fechas (ya tienes recaudación por cobrador) y un **reporte de desembolsos** por rango de fechas ayuda a tener trazabilidad.

### F) Cronograma vs pagos (prioridad media-baja)

- Asegurar que, cuando se registra un pago, se actualice bien el **CronogramaPago** (cuota PAGADA/PARCIAL y monto_pagado). Ya lo haces en nuevo_pago y en procesar_cobro_completo.
- Opcional: una validación periódica (comando o vista de “integridad”): por cada crédito, suma de `Pago.monto` = suma de `CronogramaPago.monto_pagado` (o al menos que no sea menor). Si no cuadra, alertar para revisar.

### G) Botón “Actualizar cartera” y análisis diario

- Mantener el botón **Actualizar cartera** para recalcular mora e interés y, si se implementa A), para que **CarteraAnalisis** guarde saldos (no monto_total).
- El cron que genera análisis diario debería usar la misma lógica (saldos) para que el historial de cartera sea coherente con la pantalla y con la conciliación.

---

## 5. Orden sugerido de implementación

1. **Unificar cartera en saldo pendiente** (cambiar CarteraAnalisis y cualquier vista que use monto_total como “cartera”).
2. **Vista “Resumen del dinero”** con la ecuación desembolsado = cobrado + saldo y, si aplica, alerta cuando no cuadre.
3. **Validación en registro de pagos** para no superar monto_total (o manejar sobrepago de forma explícita).
4. **Reporte de conciliación por crédito** (Excel/PDF) con totales.
5. Opcional: auditoría de movimientos (tabla o reportes) y validación cronograma vs pagos.

Con esto tendrás un control quirúrgico: una sola definición de cartera, una ecuación clara de conciliación y validaciones que evitan inconsistencias al registrar dinero.
