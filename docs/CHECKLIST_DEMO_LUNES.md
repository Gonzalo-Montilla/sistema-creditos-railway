# Checklist demo lunes (10-15 min antes)

## 1) Entorno y servidor

```powershell
cd "C:\Proyectos\sistema-creditos"
.\start_local.ps1 -CheckOnly
```

Si OK, ejecutar:

```powershell
.\start_local.ps1
```

## 2) Smoke test tecnico rapido (sin login manual)

En otra terminal:

```powershell
cd "C:\Proyectos\sistema-creditos"
.\demo_smoke_check.ps1
```

Debe mostrar rutas clave en verde y mensaje final de OK.

## 2.1) Auditoria de integridad operativa (recomendada)

En la misma terminal:

```powershell
cd "C:\Proyectos\sistema-creditos"
python manage.py auditar_operacion
```

Si reporta hallazgos corregibles, ejecutar:

```powershell
python manage.py auditar_operacion --fix
```

Objetivo: validar coherencia entre pagos, cuotas y tareas antes de la presentacion.

## 3) Recorrido funcional recomendado para demo

1. Login.
2. Crear/consultar cliente.
3. Crear credito nuevo (tipo operacion visible).
4. Aprobacion y flujo de documento correcto segun tipo:
   - Nuevo -> pagare
   - Renovacion -> doc. renovacion
   - Retanqueo -> doc. retanqueo
5. Desembolso.
6. Agenda del cobrador (acciones y registro de cobro).
7. Cierre de cobro diario con arqueo.

## 4) Verificacion de documentos PDF

- Revisar que textos legales se vean justificados en:
  - Habeas Data
  - Pagare
  - Renovacion
  - Retanqueo

## 5) Plan de contingencia

- Si algo falla en entorno local:
  1) `deactivate`
  2) borrar `.venv`
  3) `.\start_local.ps1`

- Si un flujo da error:
  - tomar captura del mensaje
  - validar URL y estado del registro
  - continuar demo por otro caso ya preparado
