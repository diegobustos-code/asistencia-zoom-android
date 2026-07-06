# Asistencia Zoom — versión Android

Versión móvil de "Procesador de Asistencia Zoom". Reutiliza la misma
lógica exacta que la versión de escritorio (`csv_processor.py`,
`roster_matcher.py`, `excel_exporter.py`), con una interfaz hecha en
**Kivy** en vez de Tkinter (porque Tkinter no existe en Android).

## Qué hace la app

- Abrir el CSV de participantes de Zoom (detecta el formato automáticamente,
  incluso si viene disfrazado de Excel).
- Abrir el listado oficial de socios (Excel).
- Cotejar ambos archivos y marcar "P"/"A" según asistencia — misma lógica
  exacta que la versión de escritorio.
- Buscar, filtrar por duración mínima, ajustar el umbral de "Presente",
  y ordenar.
- Exportar a CSV o Excel y compartirlo (WhatsApp, correo, Drive, etc.).
- **Si algo falla al iniciar, la app muestra el error como texto en
  pantalla completa** en vez de cerrarse en silencio (ver sección final).

## Estructura del proyecto

```
├── main.py               # Punto de entrada "blindado": atrapa cualquier
│                          # error al iniciar y lo muestra en pantalla
├── app_core.py            # La app real (interfaz Kivy + toda la lógica)
├── csv_processor.py        # Igual que en la versión de escritorio
├── roster_matcher.py        # Igual que en la versión de escritorio
├── excel_exporter.py        # Igual que en la versión de escritorio
├── buildozer.spec           # Configuración de compilación para Android
├── requirements.txt          # Para probar la app en tu PC antes de compilar
└── .github/workflows/build-apk.yml   # Compila el APK automáticamente en GitHub
```

---

## Paso 1 — Probar la app en tu PC (opcional pero recomendado)

```
pip install -r requirements.txt
python main.py
```

Se abre una ventana de escritorio con la misma interfaz. Útil para
detectar errores obvios sin esperar la compilación (aunque **no** prueba
el comportamiento específico de Android — eso solo se ve compilando el
APK real).

---

## Paso 2 — Subir/actualizar el proyecto en GitHub

Si ya tienes el repositorio creado (de una vez anterior), simplemente
reemplaza TODOS los archivos de esta carpeta por los tuyos y vuelve a
subir los cambios con GitHub Desktop:

1. Copia estos archivos dentro de tu carpeta local del proyecto,
   reemplazando los que ya existían (presta atención especial a que
   `app_core.py` es un archivo **nuevo** que no tenías antes).
2. Abre GitHub Desktop → verás la lista de archivos modificados/nuevos.
3. Escribe una descripción del cambio (ej. "Agregar pantalla de error y
   ajustar NDK") → **Commit to main**.
4. **Push origin** (arriba a la derecha).

Si es la primera vez, sigue las instrucciones completas del Paso 2 de la
versión anterior de este documento (crear repositorio, etc.)

---

## Paso 3 — Compilar

Ve a la pestaña **Actions** de tu repositorio en github.com →
"Compilar APK de Android" → **"Run workflow"** (no uses "Re-run jobs" de
una ejecución vieja, siempre usa "Run workflow" para asegurarte de que
toma los archivos más recientes).

Gracias al caché ya configurado, si el NDK no cambió respecto a la
última vez, debería ser más rápido que la primera vez (aun así, cuenta
con 15-30 minutos).

Al terminar en verde, baja a **"Artifacts"** y descarga `AsistenciaZoom-APK`.

---

## Qué se ha corregido hasta ahora (bitácora)

Por transparencia, esto es lo que ya identificamos y corregimos en
rondas anteriores:

1. **Acción de compilación de terceros rota** → se reemplazó por un
   workflow que instala Buildozer directamente (sin depender de acciones
   externas de comunidad).
2. **`ModuleNotFoundError: No module named 'openpyxl'`** → causado por
   compilar con una versión de Python/venv que no tenía las dependencias
   instaladas antes de empaquetar. Corregido asegurando
   `pip install -r requirements.txt` antes de compilar.
3. **Error de compilación por versión de `python-for-android` demasiado
   nueva** (intentaba instalar paquetes internos como `android` que ya
   no existen en PyPI) → se fijó la versión `python-for-android==2024.1.21`,
   más estable.
4. **"Android Gradle plugin requires Java 17. You are currently using
   Java 11"** → la máquina de GitHub trae varias versiones de Java a la
   vez; se agregó el paso `actions/setup-java@v4` para forzar Java 17.
   **Confirmado que esto funcionó**: con este cambio, la compilación
   llegó hasta el final y generó el APK instalable.
5. **La app se instala pero se cierra/queda en segundo plano sin ningún
   error visible en el celular** (problema actual) — los celulares
   Honor/Huawei de prueba bloquean el acceso a `logcat` para apps de
   terceros, así que no hay forma de ver el error con las herramientas
   normales de depuración. Se probó actualizar el NDK a una versión más
   reciente (compatible con el requisito de "páginas de memoria de 16 KB"
   de Android 15) sin éxito visible. **Se descartó que sea un problema de
   `openpyxl` faltante** (se confirmó en el log que se instaló
   correctamente).

## La nueva herramienta de diagnóstico: pantalla de error visible

Como no se puede ver el log en estos celulares, se modificó la app para
que, si algo fallara al iniciar (incluso un error de importación de
alguna librería), en vez de cerrarse en silencio **muestre el error como
texto en la pantalla completa del celular**, con instrucciones de sacarle
una foto.

**Esto es clave para el siguiente paso**: cuando instales esta nueva
versión del APK,
- Si la pantalla de error **aparece**: perfecto, sácale una foto completa
  (usa el scroll si el texto no entra todo) y compártela — con eso vamos
  a saber exactamente qué corregir, con certeza, en vez de adivinar.
- Si la app **sigue haciendo lo mismo de antes** (se cierra/queda en
  segundo plano SIN mostrar ni siquiera esta pantalla de error): es una
  señal importante también — significa que el problema ocurre en un nivel
  más profundo que el propio código Python (probablemente algo nativo de
  Android/gráficos, antes de que Python alcance a ejecutar nuestro código
  de manejo de errores). Avísame si pasa esto para probar el siguiente
  ajuste (por ejemplo, cambiar la versión de SDL2/Kivy usada, o el modo de
  arranque de la app).

Cualquiera de los dos resultados nos da información útil — ya no
estaríamos a ciegas.
