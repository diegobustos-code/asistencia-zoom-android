# Asistencia Zoom — versión Windows (.exe)

Versión de escritorio para Windows de "Procesador de Asistencia Zoom".
Reutiliza exactamente la misma lógica que la versión Android
(`csv_processor.py`, `roster_matcher.py`, `excel_exporter.py`), con una
interfaz hecha en **Tkinter** (viene incluido con Python, no requiere
instalar nada aparte) pensada para pantallas de PC.

## Qué hace (igual que la versión Android, en una ventana de escritorio)

- Pide el mes de la asistencia al abrir (obligatorio), con botón
  "Cambiar mes".
- Abrir el CSV de Zoom y el listado oficial de socios (Excel).
- Cotejar, buscar, filtrar por duración mínima, ajustar el umbral de
  "Presente" y ordenar.
- Exportar a CSV / Excel / Pendientes. Los archivos quedan SIEMPRE
  guardados y organizados en:
  ```
  Downloads / Asistencia Zoom / Cotejados      ← Exportar CSV / Exportar Excel
  Downloads / Asistencia Zoom / Por revisar    ← Pendientes
  ```
  con el mes en el nombre, ej. `asistencia_Julio_2026.xlsx`.
- Botón "Abrir archivo" en el pop-up de guardado (abre con Excel /
  LibreOffice / lo que Windows tenga asociado, o muestra el selector
  "Abrir con" si no hay ninguna app asociada) y botón "Abrir carpeta"
  para ir directo a la carpeta en el Explorador.
- Pop-ups con ✓ verde / ✕ roja según el resultado, igual que en el
  celular.
- Si algo falla al iniciar, se muestra el error en una ventana en vez
  de cerrarse en silencio (compilado en modo sin consola).

## Archivos de esta versión

```
├── desktop_app.py            # La app (interfaz Tkinter + toda la lógica)
├── csv_processor.py            # Compartido con la versión Android (sin cambios)
├── roster_matcher.py            # Compartido con la versión Android (sin cambios)
├── excel_exporter.py            # Compartido con la versión Android (sin cambios)
├── logo.png / logo.ico           # Logo (el .ico es el ícono del .exe)
├── requirements-desktop.txt       # Dependencias para compilar
└── .github/workflows/build-exe.yml   # Compila el .exe automáticamente en GitHub
```

## Cómo obtener el .exe (automático, con GitHub Actions)

Igual que con el APK: sube estos archivos a tu mismo repositorio de
GitHub (agrega `desktop_app.py`, `requirements-desktop.txt`, `logo.ico`
y coloca `build-exe.yml` dentro de `.github/workflows/`, junto a
`build-apk.yml`).

1. Sube los cambios con GitHub Desktop (Commit → Push origin), igual
   que ya haces con el APK.
2. Ve a la pestaña **Actions** en github.com → **"Compilar EXE de
   Windows"** → **"Run workflow"**.
3. Espera a que termine en verde (unos 3-5 minutos, mucho más rápido
   que el APK porque no hay que compilar ningún NDK).
4. Baja a **"Artifacts"** y descarga `AsistenciaZoom-EXE` — ahí adentro
   está `AsistenciaZoom.exe`, listo para copiar a cualquier PC con
   Windows y ejecutar con doble clic (no necesita instalar Python).

## Cómo probarlo en tu propia PC sin compilar nada (opcional)

Si tienes Python instalado en Windows:

```
pip install -r requirements-desktop.txt
python desktop_app.py
```

## Nota sobre Windows Defender / SmartScreen

Como el .exe no está firmado digitalmente (firmar un .exe cuesta dinero
y no es necesario para uso interno), es normal que la primera vez que
alguien lo abra, Windows muestre una advertencia tipo "Windows protegió
su PC". Se soluciona haciendo clic en **"Más información"** → **"Ejecutar
de todas formas"**. Esto es solo una advertencia por no tener firma
digital, no significa que el archivo tenga algún problema.
