# Próxima sesión: UX, estilo y responsive

Plan de trabajo para la siguiente sesión. Tres pilares sin romper lo ya construido.

---

## 1. Experiencia de usuario (operadores)

**Objetivo:** Que el sistema sea fácil y rápido de usar para los operadores en el día a día.

- Revisar flujos críticos: login → agenda/cobranza → registrar cobro → cierre.
- Reducir clics y pasos donde sea posible (accesos directos, acciones en lista).
- Mensajes y etiquetas claros; evitar jerga técnica.
- Feedback inmediato (toast/alertas de éxito/error) sin recargar de más.
- Navegación predecible: menú estable, breadcrumbs donde ayude.
- No tocar lógica de negocio ni modelos; solo mejorar cómo se presenta y se interactúa.

---

## 2. Estilo profesional (sector financiero / empresarial)

**Objetivo:** Aspecto más llamativo, serio y acorde a una plataforma empresarial de créditos.

- Paleta y tipografía que transmitan confianza (azules/verdes oscuros, grises, buen contraste).
- Componentes consistentes: botones, cards, tablas, badges.
- Iconografía coherente (ej. Bootstrap Icons ya en uso).
- Espaciado y jerarquía visual claros; menos “admin genérico”, más “producto financiero”.
- Considerar un tema oscuro opcional más adelante si aplica.

---

## 3. Responsive / uso en celular

**Objetivo:** Uso cómodo en móviles, sobre todo para cobradores en campo.

- Menú y navegación usables en pantalla pequeña (hamburger, drawer o bottom nav).
- Tablas convertidas en cards o listas apiladas en móvil (sin scroll horizontal forzado).
- Formularios con campos grandes, botones táctiles, teclado numérico donde sea monto.
- Pantallas clave probadas en móvil: agenda del cobrador, registrar cobro, cierre de cobro diario.
- Viewport y meta tags correctos; evitar zoom no deseado en inputs.

---

## Orden sugerido en la sesión

1. **Responsive base** (menú + 2–3 vistas críticas para cobradores) para que el uso en celular sea viable.
2. **Estilo global** (variables CSS, tipografía, colores, componentes) para un look profesional.
3. **UX** (flujos, mensajes, atajos) sobre esa base ya responsive y con estilo definido.

---

## Archivos a tener en cuenta

- `main/templates/base.html` — estructura global, menú, meta viewport.
- `static/` — CSS y JS propios (si existen).
- Plantillas en `main/templates/` — cobranza, agenda, cierre diario, cartera.
- Bootstrap (versión actual del proyecto) — grid, utilidades, componentes.

---

*Documento creado para retomar en la próxima sesión.*

---

## Pendiente confirmado para próxima sesión (UX)

Se deja priorizado implementar un **paquete Quick Wins UX** sin tocar lógica de negocio:

1. Agenda del cobrador (móvil): botones más cómodos, jerarquía clara de acciones.
2. Cierre diario (móvil): cards con toda la información de desktop.
3. Feedback de carga en acciones críticas (login, cobrar, cerrar).
4. Validaciones visuales de monto (formato y errores antes de enviar).
5. Estados vacíos con mensajes accionables + CTA.
6. Consistencia visual en formularios, badges y microcopy.

### Criterio de trabajo
- Solo cambios en templates/CSS/JS de interfaz.
- Sin alterar reglas de negocio ni flujos de datos.
- Validar al final con `python manage.py check`.
