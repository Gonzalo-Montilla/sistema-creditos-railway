# 🏗️ ARQUITECTURA TÉCNICA DEL SISTEMA
**Sistema de Gestión y Cobro de Créditos**

## 📊 STACK TECNOLÓGICO

### **Backend**
- **Framework:** Django 4.x
- **Base de datos:** SQLite (desarrollo) / PostgreSQL (producción)
- **Autenticación:** Django Auth con roles personalizados
- **APIs:** Django REST para comunicación asíncrona
- **Validaciones:** Django Forms + validadores personalizados

### **Frontend**
- **Framework CSS:** Bootstrap 5.3
- **JavaScript:** Vanilla JS + Fetch API
- **Iconos:** FontAwesome 6
- **Geolocalización:** HTML5 Geolocation API
- **Modales:** Bootstrap 5 Modal componente

---

## 🗄️ MODELOS DE DATOS

### **Usuario Extendido (User)**
```python
class User(AbstractUser):
    TIPO_USUARIO_CHOICES = [
        ('ADMIN', 'Administrador'),
        ('COBRADOR', 'Cobrador'),
    ]
    tipo_usuario = models.CharField(max_length=20, choices=TIPO_USUARIO_CHOICES, default='COBRADOR')
    telefono = models.CharField(max_length=15, blank=True, null=True)
    activo = models.BooleanField(default=True)
```

### **Cliente**
```python
class Cliente(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    cedula = models.CharField(max_length=20, unique=True)
    telefono = models.CharField(max_length=15)
    direccion = models.TextField()
    email = models.EmailField(blank=True, null=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)
```

### **Crédito**
```python
class Credito(models.Model):
    ESTADO_CHOICES = [
        ('ACTIVO', 'Activo'),
        ('PAGADO', 'Pagado'),
        ('VENCIDO', 'Vencido'),
        ('CANCELADO', 'Cancelado'),
    ]
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    monto_total = models.DecimalField(max_digits=10, decimal_places=2)
    tasa_interes = models.DecimalField(max_digits=5, decimal_places=2)
    numero_cuotas = models.IntegerField()
    monto_cuota = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_inicio = models.DateField()
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='ACTIVO')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
```

### **Cuota**
```python
class Cuota(models.Model):
    ESTADO_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('PAGADA', 'Pagada'),
        ('VENCIDA', 'Vencida'),
    ]
    credito = models.ForeignKey(Credito, on_delete=models.CASCADE)
    numero_cuota = models.IntegerField()
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_vencimiento = models.DateField()
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='PENDIENTE')
```

### **Pago**
```python
class Pago(models.Model):
    cuota = models.ForeignKey(Cuota, on_delete=models.CASCADE)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_pago = models.DateTimeField(auto_now_add=True)
    metodo_pago = models.CharField(max_length=50, default='EFECTIVO')
    observaciones = models.TextField(blank=True, null=True)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    latitud = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitud = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
```

### **TareaCobro**
```python
class TareaCobro(models.Model):
    ESTADO_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('COBRADO', 'Cobrado'),
        ('NO_ENCONTRADO', 'No Encontrado'),
        ('REPROGRAMADO', 'Reprogramado'),
    ]
    cuota = models.ForeignKey(Cuota, on_delete=models.CASCADE)
    cobrador = models.ForeignKey(User, on_delete=models.CASCADE)
    fecha_programada = models.DateField()
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='PENDIENTE')
    observaciones = models.TextField(blank=True, null=True)
    fecha_visita = models.DateTimeField(null=True, blank=True)
```

---

## 🔐 SISTEMA DE AUTENTICACIÓN Y ROLES

### **Decoradores de Autorización**
```python
def admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.tipo_usuario != 'ADMIN':
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def cobrador_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.tipo_usuario not in ['ADMIN', 'COBRADOR']:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return _wrapped_view
```

### **Mixins de Autorización**
- `LoginRequiredMixin` - Todas las vistas requieren autenticación
- `AdminRequiredMixin` - Solo administradores
- `CobradorRequiredMixin` - Administradores y cobradores

---

## 🛣️ ARQUITECTURA DE URLs

### **URL Principal (urls.py)**
```python
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.dashboard, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('clientes/', include('main.urls.clientes')),
    path('creditos/', include('main.urls.creditos')),
    path('pagos/', include('main.urls.pagos')),
    path('tareas/', include('main.urls.tareas')),
]
```

### **URLs por Módulo**
- **Clientes:** `/clientes/` - CRUD completo
- **Créditos:** `/creditos/` - Gestión de créditos y cuotas
- **Pagos:** `/pagos/` - Registro independiente de pagos
- **Tareas:** `/tareas/` - Agenda y gestión de cobradores

---

## 🎯 VISTAS PRINCIPALES

### **Dashboard (Vista Principal)**
```python
@login_required
def dashboard(request):
    context = {
        'total_clientes': Cliente.objects.filter(activo=True).count(),
        'creditos_activos': Credito.objects.filter(estado='ACTIVO').count(),
        'cuotas_vencidas': Cuota.objects.filter(estado='VENCIDA').count(),
        'tareas_pendientes': TareaCobro.objects.filter(estado='PENDIENTE').count(),
        'pagos_hoy': Pago.objects.filter(fecha_pago__date=timezone.now().date()).count(),
    }
    return render(request, 'dashboard.html', context)
```

### **Vistas de Pagos (Unificadas)**
```python
@login_required
def nuevo_pago(request):
    # Lógica común para ambos flujos de pago
    
@login_required 
@require_http_methods(["POST"])
def cobrar_tarea(request, tarea_id):
    # Reutiliza la lógica de nuevo_pago
```

### **Vistas de Agenda**
```python
@login_required
@cobrador_required
def agenda_cobrador(request):
    # Filtro por fecha y cobrador
    # Interface de tarjetas con modales
```

---

## 💾 FLUJO DE DATOS

### **Creación de Crédito**
1. **Input:** Datos del cliente + parámetros del crédito
2. **Proceso:** Cálculo automático de cuotas
3. **Output:** Crédito + Cuotas + Tareas de cobro generadas

### **Registro de Pago**
1. **Input:** Monto + Cuota + Ubicación GPS (opcional)
2. **Proceso:** Validación + Actualización de estados
3. **Output:** Pago registrado + Estados actualizados + Confirmación

### **Gestión de Tareas**
1. **Input:** Fecha + Filtros + Acciones del usuario
2. **Proceso:** Consultas filtradas + Actualizaciones AJAX
3. **Output:** Lista actualizada + Modales interactivos

---

## 🎨 ARQUITECTURA FRONTEND

### **Template Base (base.html)**
- Layout responsive con sidebar
- Navegación contextual por rol
- Scripts y estilos globales
- Sistema de alertas

### **Componentes JavaScript**
```javascript
// Geolocalización
function obtenerUbicacionActual() { ... }

// Modales dinámicos
function marcarCobrado(tareaId) { ... }

// Comunicación AJAX
function enviarFormularioCobroCompleto() { ... }

// Validaciones cliente
function validarFormulario() { ... }
```

### **Estilos CSS Personalizados**
- Variables CSS para consistencia
- Clases utilitarias específicas
- Responsive design con breakpoints
- Animaciones suaves

---

## 📱 CARACTERÍSTICAS TÉCNICAS

### **Responsive Design**
- **Desktop:** Sidebar expandido + contenido amplio
- **Tablet:** Sidebar colapsado + navegación optimizada  
- **Mobile:** Hamburger menu + tarjetas apiladas

### **Performance**
- **Paginación:** 20 elementos por página
- **Lazy loading:** Cargar contenido según necesidad
- **Consultas optimizadas:** Select_related y prefetch_related
- **Cache:** Headers de cache para recursos estáticos

### **Seguridad**
- **CSRF Protection:** Tokens en todos los formularios
- **SQL Injection:** ORM de Django previene
- **XSS Protection:** Escape automático de templates
- **Autorización:** Decoradores y mixins en todas las vistas

### **APIs Internas**
- **Formato:** JSON para respuestas AJAX
- **Validación:** Esquemas consistentes
- **Errores:** Manejo estructurado con códigos HTTP
- **Logging:** Registro detallado para debugging

---

## 🔧 CONFIGURACIÓN Y DEPLOYMENT

### **Settings por Ambiente**
```python
# Desarrollo
DEBUG = True
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3'}}

# Producción
DEBUG = False  
DATABASES = {'default': {'ENGINE': 'django.db.backends.postgresql'}}
ALLOWED_HOSTS = ['tu-dominio.com']
```

### **Dependencias (requirements.txt)**
```
Django>=4.0,<5.0
Pillow>=8.0.0
django-bootstrap5>=21.0.0
psycopg2-binary>=2.9.0  # Para PostgreSQL
gunicorn>=20.0.0  # Para producción
```

### **Migraciones**
- ✅ **0001_initial** - Modelos base
- ✅ **0002_add_geolocation** - Campos GPS en Pago
- ✅ **0003_user_extension** - Tipos de usuario
- ✅ **0004_tarea_cobro** - Sistema de tareas

---

## 📊 MÉTRICAS Y MONITOREO

### **Logs Implementados**
- **Auth:** Login/logout de usuarios
- **Pagos:** Registro y validación de pagos
- **Errores:** Excepciones y fallos de sistema
- **Performance:** Consultas lentas y bottlenecks

### **Indicadores Clave (KPIs)**
- **Operacionales:** Pagos/día, tareas completadas, clientes activos
- **Financieros:** Montos cobrados, cuotas vencidas, morosidad
- **Técnicos:** Tiempo de respuesta, errores por minuto, uptime

---

*Documento técnico actualizado - 23/09/2025*