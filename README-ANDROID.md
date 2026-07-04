# Asistencia Zoom — versión Android

Esta es la versión móvil (Android) del "Procesador de Asistencia Zoom".
Usa exactamente la misma lógica de procesamiento que la versión de
escritorio (los archivos `csv_processor.py`, `roster_matcher.py` y
`excel_exporter.py` son idénticos), pero con una interfaz hecha en
**Kivy** en vez de Tkinter, porque Tkinter no existe en Android.

## Qué hace la app

- Abrir el CSV de participantes de Zoom (detecta automáticamente el
  formato, incluso si viene disfrazado de Excel).
- Abrir el listado oficial de socios (Excel).
- Cotejar ambos archivos y marcar "P"/"A" según asistencia — misma
  lógica exacta que la versión de escritorio.
- Buscar, filtrar por duración mínima, ajustar el umbral de "Presente",
  y ordenar por distintas columnas.
- Exportar a CSV o Excel y compartir el archivo directamente desde el
  celular (WhatsApp, correo, Google Drive, etc.) usando el diálogo
  nativo de Android para compartir.

---

## Paso 1 — Probar la app en tu PC antes de compilar (recomendado)

Compilar un APK toma tiempo (15-40 minutos), así que conviene primero
asegurarse de que la interfaz funciona bien en el propio computador.
Esto usa la MISMA app, solo que corriendo como programa de escritorio
normal (Kivy también funciona en Windows).

```
pip install -r requirements.txt
python main.py
```

Se abrirá una ventana con la interfaz. Pruébala igual que harías en el
celular: abrir el CSV de Zoom, abrir el Excel de socios, cotejar,
filtrar, exportar. Si algo se ve raro o falla, avísame antes de
compilar el APK — es mucho más rápido corregirlo así.

---

## Paso 2 — Subir el proyecto a GitHub

Necesitas una cuenta de GitHub (ya la tienes). Los pasos:

1. Entra a [github.com](https://github.com) y crea un **repositorio
   nuevo** (botón verde "New"). Ponle un nombre, por ejemplo
   `asistencia-zoom-android`. Puede ser privado o público, da lo mismo.
   **No** marques la opción de agregar un README (para que quede vacío).

2. En tu PC, abre una terminal **dentro de la carpeta de este proyecto**
   (la que contiene `main.py`, `buildozer.spec`, etc.) y ejecuta, uno por
   uno:

   ```
   git init
   git add .
   git commit -m "Primera version de la app Android"
   git branch -M main
   git remote add origin https://github.com/TU_USUARIO/asistencia-zoom-android.git
   git push -u origin main
   ```

   Reemplaza `TU_USUARIO` y el nombre del repositorio por los tuyos
   (GitHub te muestra estos comandos exactos apenas creas el
   repositorio, en la pantalla "…or push an existing repository from
   the command line").

   Si no tienes `git` instalado, descárgalo de
   [git-scm.com](https://git-scm.com/download/win) e instálalo primero
   (todas las opciones por defecto están bien).

---

## Paso 3 — Dejar que GitHub compile el APK automáticamente

Apenas subas el código, GitHub Actions empieza a compilar solo (el
archivo `.github/workflows/build-apk.yml` ya viene configurado para
esto). Para verlo:

1. Ve a tu repositorio en github.com.
2. Entra a la pestaña **"Actions"** (arriba).
3. Verás un proceso llamado "Compilar APK de Android" corriendo (círculo
   amarillo girando). **La primera vez puede tardar entre 20 y 40
   minutos** porque tiene que descargar todas las herramientas de
   Android desde cero. Las siguientes veces es más rápido.
4. Cuando termine (✅ verde), entra a esa ejecución y baja hasta la
   sección **"Artifacts"**. Ahí vas a ver un archivo llamado
   `AsistenciaZoom-APK` — descárgalo (es un .zip que contiene el .apk
   adentro).

Si el proceso termina en ❌ rojo, entra a ver el detalle del error (clic
en el paso que falló) y pásame el mensaje de error — es información
valiosa para ajustar la configuración.

---

## Paso 4 — Instalar el APK en el celular

1. Descomprime el .zip descargado; adentro está el archivo `.apk`.
2. Pásalo a tu celular Android (por WhatsApp Web, correo, cable USB,
   Google Drive, como prefieras).
3. Ábrelo desde el celular. Es probable que Android muestre una
   advertencia tipo "Por tu seguridad, tu teléfono no permite instalar
   aplicaciones desconocidas de esta fuente" — tendrás que ir a
   **Ajustes → permitir esta fuente** (Android te lleva directo a esa
   pantalla si tocas "Ajustes" en el mismo aviso). Es normal para
   cualquier app que no venga de Google Play, no significa que tenga
   virus.
4. Instala y abre la app.

---

## Qué esperar / limitaciones honestas

Esta es una app nueva construida sobre una tecnología (Kivy + Android)
que no se puede probar ni compilar dentro de este chat — no tengo forma
de generar un emulador de Android ni un dispositivo real para probarla
antes de dártela. Lo que sí probé exhaustivamente es:

- Toda la lógica de carga, cotejo, filtros, orden y exportación (idéntica
  a la versión de escritorio, con tus archivos reales).
- Que la interfaz Kivy se construye sin errores y responde a las
  interacciones (simulado en un entorno de escritorio Linux).

Lo que **no** pude probar (por no tener un dispositivo/emulador Android
disponible) y que es razonable que necesite un ajuste tras el primer
build real:
- El selector de archivos nativo de Android (`plyer.filechooser`) —
  en algunas versiones de Android puede requerir un pequeño ajuste en
  cómo se recibe la ruta del archivo elegido.
- El diálogo de "compartir" tras exportar (`plyer.share`) — si no
  aparece, el archivo de todas formas queda guardado dentro de la app y
  te aviso la ruta en pantalla.

Si algo de esto no funciona como se espera al probarlo en tu celular,
mándame una foto del error (o descríbelo) y lo ajustamos — es
información normal de una primera compilación real en Android.

---

## Si necesitas volver a compilar tras un cambio

Cada vez que subas cambios a la rama `main` de tu repositorio de GitHub
(`git add .` → `git commit -m "..."` → `git push`), el APK se vuelve a
compilar solo. Solo tienes que repetir el Paso 3 para descargar la
versión nueva.
