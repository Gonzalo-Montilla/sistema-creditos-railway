from django.urls import path
from . import views
from . import valorizador_views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('force-login/', views.force_login_view, name='force_login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard-negocio/', views.dashboard_negocio, name='dashboard_negocio'),
    
    # Clientes
    path('clientes/', views.clientes, name='clientes'),
    path('exportar-clientes-excel/', views.exportar_clientes_excel, name='exportar_clientes_excel'),
    path('nuevo-cliente/', views.nuevo_cliente, name='nuevo_cliente'),
    path('editar-cliente/<int:cliente_id>/', views.editar_cliente, name='editar_cliente'),
    path('eliminar-cliente/<int:cliente_id>/', views.eliminar_cliente, name='eliminar_cliente'),
    path('reactivar-cliente/<int:cliente_id>/', views.reactivar_cliente, name='reactivar_cliente'),
    path('detalle-cliente/<int:cliente_id>/', views.detalle_cliente, name='detalle_cliente'),
    path('buscar-cliente/', views.buscar_cliente, name='buscar_cliente'),
    path('habeas-data/solicitar/', views.solicitar_habeas_data, name='solicitar_habeas_data'),
    path('habeas-data/validar/', views.validar_otp_habeas_data, name='validar_otp_habeas_data'),
    path('habeas-data/descargar/<str:tipo>/<int:objeto_id>/', views.descargar_habeas_data, name='descargar_habeas_data'),
    path('habeas-data/regenerar/', views.regenerar_habeas_data, name='regenerar_habeas_data'),
    path('renovacion/solicitar/', views.solicitar_firma_renovacion, name='solicitar_firma_renovacion'),
    path('renovacion/validar/', views.validar_otp_renovacion_view, name='validar_otp_renovacion'),
    path('renovacion/descargar/<int:credito_id>/', views.descargar_renovacion, name='descargar_renovacion'),
    path('retanqueo/credito/<int:credito_id>/', views.retanqueo_credito, name='retanqueo_credito'),
    path('retanqueo-documento/solicitar/', views.solicitar_firma_retanqueo, name='solicitar_firma_retanqueo'),
    path('retanqueo-documento/validar/', views.validar_otp_retanqueo_view, name='validar_otp_retanqueo'),
    path('retanqueo-documento/descargar/<int:credito_id>/', views.descargar_retanqueo, name='descargar_retanqueo'),

    # Codeudores
    path('nuevo-codeudor/<int:cliente_id>/', views.nuevo_codeudor, name='nuevo_codeudor'),
    path('editar-codeudor/<int:codeudor_id>/', views.editar_codeudor, name='editar_codeudor'),
    path('eliminar-codeudor/<int:codeudor_id>/', views.eliminar_codeudor, name='eliminar_codeudor'),
    
    # Créditos
    path('creditos/', views.creditos, name='creditos'),
    path('exportar-creditos-excel/', views.exportar_creditos_excel, name='exportar_creditos_excel'),
    path('nuevo-credito/', views.nuevo_credito, name='nuevo_credito'),
    path('editar-credito/<int:credito_id>/', views.editar_credito, name='editar_credito'),
    path('aprobar-credito/<int:credito_id>/', views.aprobar_credito, name='aprobar_credito'),
    path('rechazar-credito/<int:credito_id>/', views.rechazar_credito, name='rechazar_credito'),
    path('desembolsar-credito/<int:credito_id>/', views.desembolsar_credito, name='desembolsar_credito'),
    path('pagare/solicitar/', views.solicitar_firma_pagare, name='solicitar_firma_pagare'),
    path('pagare/validar/', views.validar_otp_pagare_view, name='validar_otp_pagare'),
    path('pagare/descargar/<int:credito_id>/', views.descargar_pagare, name='descargar_pagare'),
    path('pagare/regenerar/', views.regenerar_pagare, name='regenerar_pagare'),
    path('buscar-cliente-credito/', views.buscar_cliente_credito, name='buscar_cliente_credito'),
    path('obtener-datos-credito/<int:credito_id>/', views.obtener_datos_credito, name='obtener_datos_credito'),
    path('obtener-pagos-credito/<int:credito_id>/', views.obtener_pagos_credito, name='obtener_pagos_credito'),
    path('generar-pdf-cronograma/<int:credito_id>/', views.generar_pdf_cronograma, name='generar_pdf_cronograma'),
    path('resumen-credito/<int:credito_id>/', views.resumen_credito_json, name='resumen_credito_json'),
    
    # Pagos
    path('pagos/', views.pagos, name='pagos'),
    path('exportar-pagos-excel/', views.exportar_pagos_excel, name='exportar_pagos_excel'),
    path('nuevo-pago/', views.nuevo_pago, name='nuevo_pago'),
    path('detalle-pago/<int:pago_id>/', views.detalle_pago, name='detalle_pago'),
    path('generar-recibo-pdf/<int:pago_id>/', views.generar_recibo_pdf, name='generar_recibo_pdf'),
    path('buscar-creditos-cliente/', views.buscar_creditos_cliente, name='buscar_creditos_cliente'),
    path('confirmacion-pago/<int:pago_id>/', views.confirmacion_pago, name='confirmacion_pago'),
    
    # Cobradores
    path('cobradores/', views.cobradores, name='cobradores'),
    path('nuevo-cobrador/', views.nuevo_cobrador, name='nuevo_cobrador'),
    path('detalle-cobrador/<int:cobrador_id>/', views.detalle_cobrador, name='detalle_cobrador'),
    path('editar-cobrador/<int:cobrador_id>/', views.editar_cobrador, name='editar_cobrador'),
    
    # Rutas
    path('rutas/', views.rutas, name='rutas'),
    path('nueva-ruta/', views.nueva_ruta, name='nueva_ruta'),
    path('detalle-ruta/<int:ruta_id>/', views.detalle_ruta, name='detalle_ruta'),
    path('editar-ruta/<int:ruta_id>/', views.editar_ruta, name='editar_ruta'),
    
    # Gestión diaria de cobros
    path('gestion-diaria-cobros/', views.gestion_diaria_cobros, name='gestion_diaria_cobros'),
    
    # Gestión de cartera
    path('gestion-cartera/', views.gestion_cartera, name='gestion_cartera'),
    path('resumen-dinero/', views.resumen_dinero, name='resumen_dinero'),
    path('cartera-vencida/', views.cartera_vencida, name='cartera_vencida'),
    path('clientes-en-mora/', views.clientes_en_mora, name='clientes_en_mora'),
    path('actualizar-cartera/', views.actualizar_cartera, name='actualizar_cartera'),
    path('exportar-cartera-excel/', views.exportar_cartera_excel, name='exportar_cartera_excel'),
    path('kpis-cobradores/', views.kpis_cobradores, name='kpis_cobradores'),
    
    # Reportes de recaudación
    path('recaudacion-cobradores/', views.recaudacion_cobradores, name='recaudacion_cobradores'),
    path('exportar-recaudacion-excel/', views.exportar_recaudacion_excel, name='exportar_recaudacion_excel'),
    path('reporte-tareas-pendientes/', views.reporte_tareas_pendientes, name='reporte_tareas_pendientes'),
    path('detalles-pagos-cobrador/<int:cobrador_id>/', views.detalles_pagos_cobrador, name='detalles_pagos_cobrador'),
    
    # Sistema de tareas de cobro
    path('cobrador/', views.acceso_cobrador, name='acceso_cobrador'),
    path('tareas/agenda/', views.agenda_cobrador, name='agenda_cobrador'),
    path('tareas/agenda/<int:cobrador_id>/', views.agenda_cobrador, name='agenda_cobrador_especifico'),
    path('tareas/cobrar/<int:tarea_id>/', views.procesar_cobro_completo, name='procesar_cobro_completo'),
    path('tareas/actualizar/<int:tarea_id>/', views.actualizar_tarea, name='actualizar_tarea'),
    path('tareas/supervisor/', views.panel_supervisor, name='panel_supervisor'),
    path('tareas/generar/', views.generar_tareas_diarias, name='generar_tareas_diarias'),
    # Cierre de cobro diario
    path('cierre-cobro-diario/', views.cierre_cobro_diario, name='cierre_cobro_diario'),
    path('cierre-cobro-diario/cobrador/<int:cobrador_id>/', views.resumen_cierre_cobrador, name='resumen_cierre_cobrador'),
    path('cierre-cobro-diario/cerrar/', views.cerrar_cobro_cobrador, name='cerrar_cobro_cobrador'),
    
    # Gestión de Usuarios
    path('usuarios/', views.lista_usuarios, name='lista_usuarios'),
    path('nuevo-usuario/', views.nuevo_usuario, name='nuevo_usuario'),
    path('editar-usuario/<int:user_id>/', views.editar_usuario, name='editar_usuario'),
    path('eliminar-usuario/<int:user_id>/', views.eliminar_usuario, name='eliminar_usuario'),
    path('cambiar-password/<int:user_id>/', views.cambiar_password_usuario, name='cambiar_password_usuario'),
    
    # Valorizador de créditos
    path('valorizador/', valorizador_views.valorizador, name='valorizador'),
    path('valorizador/calcular/', valorizador_views.calcular_credito, name='calcular_credito'),
    path('valorizador/comparar/', valorizador_views.comparar_modalidades, name='comparar_modalidades'),
]
