# Permisos y roles – Módulo de cobranza

Cuando definas usuarios y grupos en Django, puedes acotar quién ve qué en cobranza.

## Dónde se comprueba actualmente

- **`actualizar_tarea`** (Agenda: Cobrar / No encontrado / Reprogramar):  
  `request.user.is_staff or (hasattr(request.user, 'cobrador') and request.user.cobrador == tarea.cobrador)`  
  → Solo staff o el cobrador asignado puede cambiar la tarea.

- **Resto de vistas de cobranza** (panel supervisor, agenda, recaudación, reportes):  
  Solo `@login_required`; cualquier usuario logueado puede entrar.

## Sugerencia para cuando tengas grupos

1. Crear un grupo en Django Admin, por ejemplo: **"Supervisor cobranza"**.
2. En las vistas que quieras restringir a supervisores (por ejemplo panel supervisor, generar tareas, reporte tareas pendientes, exportar recaudación), añadir:

   ```python
   if not request.user.is_staff and not request.user.groups.filter(name='Supervisor cobranza').exists():
       return redirect('dashboard')  # o HttpResponseForbidden()
   ```

3. Para que un cobrador solo vea **su** agenda:  
   En `agenda_cobrador`, si el usuario tiene un perfil `cobrador` (OneToOne o FK), filtrar por `cobrador=request.user.cobrador` y no mostrar selector de cobrador (o solo su nombre).

4. Opcional: permisos por acción (ej. solo supervisores pueden “Revertir cobro” o “Anular tarea”).  
   Se puede usar `django.contrib.auth.decorators.user_passes_test` o comprobar el grupo dentro de la vista antes de ejecutar la acción sensible.

No es obligatorio implementar todo de entrada; con `is_staff` y el cobrador asignado en `actualizar_tarea` ya tienes un primer nivel de control.
