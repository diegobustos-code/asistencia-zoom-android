# Asistencia Zoom — versión Android

Versión móvil de "Procesador de Asistencia Zoom". Reutiliza la misma
lógica exacta que la versión de escritorio (`csv_processor.py`,
`roster_matcher.py`, `excel_exporter.py`), con una interfaz hecha en
**Kivy** en vez de Tkinter (porque Tkinter no existe en Android).

## Qué hace la app

- Al abrir la app, pide (de forma OBLIGATORIA, con un popup que no se
  puede cerrar sin completarlo) el mes de la asistencia que se va a
  procesar — se puede cambiar después con el botón "Cambiar mes".
- Abrir el CSV de participantes de Zoom (detecta el formato automáticamente,
  incluso si viene disfrazado de Excel).
- Abrir el listado oficial de socios (Excel).
- Cotejar ambos archivos y marcar "P"/"A" según asistencia — misma lógica
  exacta que la versión de escritorio.
- Buscar, filtrar por duración mínima, ajustar el umbral de "Presente",
  y ordenar.
- Exportar a CSV o Excel y compartirlo (WhatsApp, correo, Drive, etc.).
  Los archivos exportados quedan guardados SIEMPRE (se abra o no el
  diálogo de compartir) dentro de:
  ```
  Download / Asistencia Zoom / Cotejados      ← Exportar CSV / Exportar Excel
  Download / Asistencia Zoom / Por revisar    ← Pendientes
  ```
  y el nombre del archivo incluye el mes ingresado, por ejemplo
  `asistencia_Julio_2026.xlsx`.
- Interfaz adaptativa: funciona tanto en vertical como en horizontal;
  si los controles de arriba no caben todos en horizontal, esa barra se
  vuelve desplazable por separado, para que la tabla de resultados
  siempre tenga espacio para deslizarse.
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
5. **La app se instalaba pero se cerraba/quedaba en segundo plano sin
   ningún error visible en el celular.** Los celulares Honor/Huawei de
   prueba bloquean el acceso a `logcat` para apps de terceros. Se probó
   primero actualizar el NDK (sin efecto visible), y se agregó una
   pantalla de error visible en la propia app como herramienta de
   diagnóstico (ver más abajo). **Se terminó de diagnosticar probando en
   BlueStacks** (que sí permite logcat sin restricciones), revelando el
   error real:
   ```
   ModuleNotFoundError: No module named 'kivy.input'
   [CRITICAL] [App] Unable to get a Window, abort.
   ```
   Causa: se había pedido `kivy==2.3.1`, una versión más nueva de la que
   la "receta" de compilación de `python-for-android==2024.1.21` sabe
   armar de forma completa — terminaba empaquetando un Kivy incompleto,
   sin el submódulo `kivy.input` (necesario para crear la ventana).
   **Corregido** bajando a `kivy==2.2.1`, la combinación más probada y
   estable junto con esa versión de python-for-android.

## La herramienta de diagnóstico que hizo posible encontrar esto

Se modificó la app (`main.py` + `app_core.py`) para que, si algo fallara
al iniciar, en vez de cerrarse en silencio, muestre el error como texto
en pantalla completa. Esta vez el error de Kivy ocurrió tan temprano
(antes de que la propia ventana pudiera crearse) que ni siquiera esa
pantalla de emergencia alcanzó a mostrarse — pero gracias a poder ver el
log completo en BlueStacks (sin las restricciones de Honor/Huawei),
igual se pudo encontrar la causa exacta. Una vez arreglado este problema
de raíz, esa pantalla de emergencia queda funcionando normalmente como
red de seguridad para cualquier error futuro.

## Tips de depuración (por si hace falta en el futuro)

- **BlueStacks es mejor que un celular Honor/Huawei para depurar**: estos
  fabricantes bloquean el acceso a `logcat` de apps de terceros incluso
  por USB. BlueStacks no tiene esa restricción.
- Para conectar `adb` a BlueStacks: actívalo en BlueStacks (Configuración
  → Avanzado → Android Debug Bridge), luego `.\adb connect 127.0.0.1:5555`.
- Si tienes más de un dispositivo/emulador conectado a la vez, `adb` se
  confunde — usa `.\adb -s 127.0.0.1:5555 logcat` (indicando cuál) o
  desconecta los demás.
- **Cuidado con PowerShell y `>` para guardar logs**: por defecto guarda
  el archivo en UTF-16, no en texto plano, así que buscar palabras con
  Ctrl+F en el Bloc de notas puede no funcionar bien. Si pasa esto, se
  puede convertir a UTF-8 o simplemente compartir el archivo para
  revisarlo con otra herramienta.
- Busca siempre por el tag `python` en el logcat — ahí es donde aparecen
  los tracebacks reales de la app.

## Cómo adaptar el programa si Zoom cambia el formato del CSV
