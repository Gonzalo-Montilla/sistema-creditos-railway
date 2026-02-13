# Diagnóstico y mejoras de interfaz – Claridad y unificación

## Problemas detectados

### 1. Menú lateral (sidebar) disperso y poco claro
- **9 ítems al mismo nivel** sin agrupación. El usuario no entiende qué es “Recaudación” vs “Gestión Cartera” vs “Tareas de Cobro” vs “Cobradores”.
- No hay jerarquía visual: todo parece igual importancia.
- **Solución:** Agrupar en secciones con títulos (OPERACIONES, COBRANZA, CARTERA, HERRAMIENTAS, CONFIGURACIÓN).

### 2. Iconos inconsistentes
- Mezcla de **Font Awesome** (`fas fa-*`) y **Bootstrap Icons** (`bi bi-*`): Dashboard y Créditos/Pagos usan `fas`, Clientes y Cobradores usan `bi`.
- **Solución:** Unificar en **Bootstrap Icons** en todo el sistema (ya cargados, coherentes con Bootstrap 5).

### 3. Encabezados de página desiguales
- Unas páginas usan `<h1 class="page-title">`, otras `<h2>` sin clase.
- Botones de acción a veces arriba a la derecha, a veces dentro del card, a veces varios botones sueltos (ej. Cobradores: “Gestionar Rutas”, “Gestión Diaria”, “Nuevo Cobrador”).
- **Solución:** Patrón único: **barra de página** = título (h1) + acciones principales (máx. 2–3) a la derecha. Filtros/búsqueda debajo o dentro del contenido.

### 4. Demasiada información antes de la lista
- En **Créditos** y **Pagos**: 4 tarjetas de métricas grandes encima de la tabla; en móvil hay que hacer mucho scroll para ver la lista.
- **Solución:** En listas, priorizar la tabla. Métricas en una sola fila compacta o en un panel colapsable; o dejar solo 1 línea de resumen (ej. “Total: X | Hoy: Y”).

### 5. Sin breadcrumb (migas de pan)
- No se sabe “dónde estoy” en el sistema (ej. Clientes > Detalle de Juan Pérez).
- **Solución:** Añadir bloque opcional de breadcrumb en `base.html` y rellenarlo en las páginas clave.

### 6. Dashboard confuso
- “Acciones Rápidas” repite lo que ya está en el menú (Nuevo Cliente, Nuevo Crédito, etc.) y compite con las tarjetas clicables.
- Mezcla de iconos (fas) con el resto del sistema.
- **Solución:** Dashboard con métricas claras y 3 acciones principales visibles; mismo estilo de iconos (bi).

### 7. Footer y contenido
- Footer (CREDIFLOW, copyright) dentro del contenido puede quedar muy abajo o cortado.
- **Solución:** Mantener footer pero con margen consistente; opcionalmente hacerlo sticky al final de la vista.

---

## Cambios implementados (primera fase)

1. **Sidebar agrupado** por secciones con etiquetas en mayúsculas.
2. **Iconos unificados** a Bootstrap Icons en sidebar y dashboard.
3. **Dashboard simplificado**: iconos bi, “Acciones rápidas” reducidas a 3 y alineadas con el menú.
4. **Bloque de breadcrumb** en base y uso en algunas páginas (lista → detalle).
5. **Clase `.page-header`** en base para título + acciones de forma uniforme.

---

## Cambios sugeridos para siguientes fases

- Aplicar `.page-header` y breadcrumb en todas las listas y detalles.
- Reducir métricas en listas de Créditos y Pagos a una línea o panel colapsable.
- Unificar botones de “acción principal” (siempre mismo estilo: ej. `btn btn-primary` para la acción principal).
- Revisar textos de ayuda (“La búsqueda filtra en todos los clientes”) y colocarlos en tooltips o debajo del campo para no saturar el header del card.
