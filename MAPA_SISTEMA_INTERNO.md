# Mapa interno del sistema de créditos (referencia para desarrollo)

Documento de contexto para continuar mejoras. No reemplaza la documentación de usuario.

---

## 1. Modelos y relaciones

- **Cliente**: KYC (nombres, apellidos, cédula única, celular, teléfono fijo, email, dirección, barrio, 2 referencias, fotos). `activo`, `fecha_registro`. Props: `nombre_completo`, `telefono` (alias de celular).
- **Codeudor**: OneToOne con Cliente (`related_name='codeudor'`). Mismos validadores cédula/celular. Fotos opcionales. Máximo 1 por cliente.
- **Credito**: FK Cliente, FK Cobrador (opcional). Estados: SOLICITADO → APROBADO → DESEMBOLSADO → PAGADO | RECHAZADO | VENCIDO. tipo_plazo: DIARIO, SEMANAL, QUINCENAL, MENSUAL. cantidad_cuotas, valor_cuota, monto_total, total_interes, descripcion_pago (calculados en save/calcular_cronograma). Mora: dias_mora, estado_mora (AL_DIA, MORA_TEMPRANA, MORA_ALTA, MORA_CRITICA), interes_moratorio, tasa_mora. En save(): si no hay cobrador se asigna por barrio/ruta (sugerir_cobrador); se calcula plazo_meses y si no hay valor_cuota se llama calcular_cronograma(). Lógica de cronograma y fechas en creditos_utils.
- **CronogramaPago**: FK Credito (related_name='cronograma'). numero_cuota, fecha_vencimiento, monto_cuota, monto_pagado, estado (PENDIENTE, PAGADA, VENCIDA, PARCIAL). unique_together (credito, numero_cuota).
- **Pago**: FK Credito, FK CronogramaPago (null/blank). monto, fecha_pago (auto_now_add), numero_cuota, observaciones.
- **CarteraAnalisis**: Snapshot diario de métricas (cartera total, al día, vencida, por estado mora, pagos del día, meta, cumplimiento). generar_analisis_diario() y generar_analisis_diario_seguro().
- **TareaCobro**: FK Cobrador, FK CronogramaPago (cuota a cobrar), fecha_asignacion. Estados: PENDIENTE, EN_PROCESO, COBRADO, NO_ENCONTRADO, NO_ESTABA, NO_PUDO_PAGAR, REPROGRAMADO, CANCELADO. Prioridad: ALTA, MEDIA, BAJA. marcar_como_cobrado(monto, obs, lat, lng) actualiza tarea, cuota (monto_pagado, estado PAGADA/PARCIAL), crea Pago, y si saldo crédito <= 0 pone crédito PAGADO. cambiar_estado() para no cobrado/reprogramado. generar_tareas_diarias(fecha): por cobrador activo con rutas; reprogramadas para fecha + cuotas que vencen ese día (credito__cobrador, fecha_vencimiento=fecha, estado PENDIENTE/PARCIAL); unique_together (cuota, fecha_asignacion).
- **Ruta**: nombre, descripcion, barrios (texto separado por comas), zona, activa. get_barrios_lista(). Cobradores: M2M con Cobrador (related_name='cobradores' en Ruta).
- **Cobrador**: datos personales, documento único, celular, email, direccion, rutas (M2M), fecha_ingreso, activo, comision_porcentaje, meta_diaria. OneToOne opcional con User (usuario). creditos_activos(), monto_por_cobrar_hoy(), etc.

---

## 2. Lógica de negocio central (creditos_utils.py)

- **calcular_credito_informal(monto, tasa_mensual, cantidad_cuotas, tipo_plazo)**: interés simple; tiempo_meses según tipo; valor_cuota = total/cuotas. Retorna dict parametros, calculos, resumen.
- **generar_cronograma_fechas(cantidad_cuotas, tipo_plazo, fecha_inicio)**: lista de dicts con numero_cuota, fecha_vencimiento, fecha_objeto, etc. DIARIO +i días, SEMANAL +i semanas, QUINCENAL +15*i, MENSUAL por mes.
- **calcular_plazo_en_meses(cantidad_cuotas, tipo_plazo)**.
- **generar_descripcion_credito(resultado_calculo)**.
- **validar_parametros_credito(...)**.

Credito.calcular_cronograma() usa calcular_credito_informal y actualiza valor_cuota, monto_total, total_interes, descripcion_pago. Credito.generar_cronograma() borra cronograma anterior y crea CronogramaPago con generar_cronograma_fechas.

---

## 3. Flujos principales

### Login y auth
- login_view: POST username/password → authenticate → login → redirect dashboard. Si ya autenticado → dashboard.
- force_login_view: logout + mismo flujo (para “cambiar de usuario”).
- Todas las vistas de contenido con @login_required. Roles: is_staff (admin); Cobrador vinculado por User (hasattr request.user, 'cobrador'). En agenda/tareas se verifica puede_editar = is_staff or request.user.cobrador == cobrador.

### Cliente → Codeudor
- clientes: lista paginada (20), filtro activo=True. nuevo_cliente, editar_cliente (ClienteForm + FILES), eliminar_cliente (soft: activo=False). detalle_cliente muestra codeudor (si existe) y creditos del cliente. nuevo_codeudor (máx 1), editar_codeudor, eliminar_codeudor.
- buscar_cliente (GET cedula): JSON para AJAX. buscar_cliente_credito: igual para formulario de crédito.

### Crédito (ciclo de vida)
- nuevo_credito: CreditoForm con cedula_cliente; clean asigna cliente por cédula; save() dispara asignación de cobrador y cálculo de cronograma (valor_cuota etc.) pero NO genera filas de CronogramaPago aún (eso es al desembolsar).
- editar_credito: mismo form con instance.
- aprobar_credito: estado SOLICITADO → APROBADO, fecha_aprobacion.
- desembolsar_credito: estado APROBADO → DESEMBOLSADO, fecha_desembolso; llama credito.generar_cronograma() (crea CronogramaPago).
- rechazar_credito: SOLICITADO → RECHAZADO.
- obtener_datos_credito (AJAX), generar_pdf_cronograma.

### Pagos
- nuevo_pago: PagoForm (cedula_cliente, credito, monto, numero_cuota, observaciones). Validación: puede_recibir_pagos(), monto <= saldo_pendiente. Al guardar: si credito.esta_al_dia() → estado PAGADO. Redirección a confirmacion_pago(pago_id).
- confirmacion_pago: muestra pago, cliente, progreso, opción PDF y WhatsApp.
- buscar_creditos_cliente: AJAX por cédula para llenar créditos en formulario de pago.

### Cobro desde agenda (tareas)
- acceso_cobrador: pantalla de entrada cobrador.
- agenda_cobrador(cobrador_id=None): si no cobrador_id, intenta Cobrador.objects.get(usuario=request.user); si no existe, selector_cobrador. Fecha por GET. Tareas del cobrador para esa fecha; estadísticas (total, cobradas, monto). puede_editar en context.
- procesar_cobro_completo(tarea_id) (POST): validación de monto (Decimal, coma/punto, rango 50–50M). Crea Pago, actualiza credito (PAGADO si esta_al_dia), tarea (COBRADO, monto_cobrado, fecha_visita, lat/lng), cuota (monto_pagado, estado PAGADA/PARCIAL). Retorna JSON success + redirect_url a confirmacion-pago/<pago_id>/.
- actualizar_tarea(tarea_id) (POST): estado COBRADO → misma validación monto y llama tarea.marcar_como_cobrado(...); otros estados → cambiar_estado(nuevo_estado, obs, fecha_reprogramacion). JSON con tarea actualizada y opcionalmente pago.
- panel_supervisor: por fecha, lista cobradores con tareas del día, completadas, monto.
- generar_tareas_diarias (POST): TareaCobro.generar_tareas_diarias(fecha), redirect panel_supervisor.

### Cobradores y rutas
- cobradores, nuevo_cobrador, detalle_cobrador, editar_cobrador. rutas, nueva_ruta, detalle_ruta, editar_ruta. gestion_diaria_cobros.

### Cartera
- gestion_cartera: cálculos en vista (cartera_total desde saldo_pendiente por crédito, créditos al día/en mora, pagos del día, meta 5%, etc.). analisis_hoy como objeto dinámico. creditos_criticos, analisis_historico (vacío).
- cartera_vencida: filtros estado_mora, dias_mora_min, cobrador_id. Paginación.
- actualizar_cartera: actualiza estado cartera de créditos y redirige.
- exportar_cartera_excel, kpis_cobradores.

### Reportes
- recaudacion_cobradores: por rango de fechas y opcional cobrador. detalles_pagos_cobrador(cobrador_id).

### Usuarios (Django User)
- lista_usuarios, nuevo_usuario (form con is_staff → is_superuser), editar_usuario, eliminar_usuario, cambiar_password_usuario.

### Valorizador
- valorizador_views: valorizador (template), calcular_credito (POST JSON), comparar_modalidades (POST JSON). Usan creditos_utils.

### Media
- media_views: media_status (diagnóstico HTML), serve_media_file (producción). creditos/urls.py incluye media en DEBUG o re_path media/.

---

## 4. URLs (main/urls.py) – nombres clave

- login, force_login, logout, dashboard.
- clientes, nuevo_cliente, editar_cliente, eliminar_cliente, detalle_cliente, buscar_cliente.
- nuevo_codeudor, editar_codeudor, eliminar_codeudor.
- creditos, nuevo_credito, editar_credito, aprobar_credito, rechazar_credito, desembolsar_credito, buscar_cliente_credito, obtener_datos_credito, generar_pdf_cronograma.
- pagos, nuevo_pago, detalle_pago, generar_recibo_pdf, buscar_creditos_cliente, confirmacion_pago.
- cobradores, nuevo_cobrador, detalle_cobrador, editar_cobrador.
- rutas, nueva_ruta, detalle_ruta, editar_ruta.
- gestion_diaria_cobros.
- gestion_cartera, cartera_vencida, actualizar_cartera, exportar_cartera_excel, kpis_cobradores.
- recaudacion_cobradores, detalles_pagos_cobrador.
- acceso_cobrador, agenda_cobrador, agenda_cobrador_especifico, procesar_cobro_completo, actualizar_tarea, panel_supervisor, generar_tareas_diarias.
- lista_usuarios, nuevo_usuario, editar_usuario, eliminar_usuario, cambiar_password_usuario.
- valorizador, calcular_credito, comparar_modalidades.

---

## 5. Formularios (main/forms.py)

- ClienteForm, CodeudorForm: ModelForm con widgets Bootstrap.
- CreditoForm: cedula_cliente (CharField), cliente (Hidden, asignado en clean). clean_cedula_cliente, clean (cliente, monto>0, tasa>=0, cuotas>0). cobrador queryset activos.
- PagoForm: cedula_cliente, cliente_encontrado (Hidden). credito queryset inicial none; en clean validación credito, monto (50–50M), numero_cuota, puede_recibir_pagos, monto <= saldo.
- CobradorForm, RutaForm (y otros para cobradores/rutas).
- Usuarios: formularios inline en views (nuevo_usuario, editar_usuario) con is_staff.

---

## 6. Templates

- base.html: sidebar (Dashboard, Valorizador, Clientes, Créditos, Pagos, Recaudación, Cartera, Tareas/Agenda, Cobradores/Rutas, Usuarios, Media status, Cerrar sesión). Bloque title, content. Bootstrap 5, Bootstrap Icons, Font Awesome, Poppins. Menú activo por request.resolver_match.url_name.
- login.html (sin base). dashboard.html. clientes.html, nuevo_cliente.html, editar_cliente.html, detalle_cliente.html, confirmar_eliminar_cliente.html. Templates codeudor, crédito, pago, confirmacion_pago. cobradores/, rutas/, cartera/, tareas/ (agenda_cobrador, selector_cobrador, panel_supervisor, acceso_cobrador). usuarios/. valorizador/valorizador.html.
- includes/pagination.html.

---

## 7. Comandos de gestión

- crear_superusuario_auto: admin / admin123 si no existe.
- generar_tareas_diarias: TareaCobro.generar_tareas_diarias(fecha) con --verbose.
- ejecutar_tareas_automaticas: (ejecutar_tareas_automaticas, usado por cron).
- revisar_cronograma, identificar_montos_erroneos, corregir_credito_problematico, crear_datos_prueba_tareas.

---

## 8. Settings (creditos/settings.py)

- SECRET_KEY, DEBUG, ALLOWED_HOSTS desde env. DATABASE_URL → PostgreSQL (dj_database_url), si no SQLite. INSTALLED_APPS: main, whitenoise, opcional django_crontab. MEDIA/STATIC, WhiteNoise. LOGIN_URL, LOGIN_REDIRECT_URL. CRONJOBS si django_crontab.

---

## 9. Detalles importantes para cambios

- Dos puntos de registro de pago: (1) nuevo_pago (form completo, redirección a confirmacion_pago); (2) desde agenda: procesar_cobro_completo (JSON, crea Pago y actualiza tarea/cuota/crédito) o actualizar_tarea con estado COBRADO (usa tarea.marcar_como_cobrado). Mantener consistencia: mismo criterio de actualización de cuota (PAGADA/PARCIAL) y crédito (PAGADO si saldo 0).
- Cronograma: se genera solo al desembolsar (generar_cronograma). Al crear crédito solo se calculan valor_cuota, monto_total (calcular_cronograma en save no crea filas CronogramaPago).
- Permisos: solo is_staff y “cobrador dueño de la tarea” en agenda/actualizar_tarea/procesar_cobro_completo. Resto de vistas solo @login_required.
- Cobrador.user: OneToOne opcional; si existe, agenda_cobrador sin cobrador_id usa request.user para obtener cobrador.
