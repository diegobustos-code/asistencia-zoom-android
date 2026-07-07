[app]

# --- Información básica de la app ---
title = Asistencia Zoom
package.name = asistenciazoom
package.domain = org.sindicato

source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0

# --- Dependencias que necesita la app dentro del APK ---
# NOTA: se fijan explícitamente TANTO "python3" (la versión que se
# empaqueta dentro de la app) COMO "hostpython3" (el intérprete que usa
# python-for-android para compilar durante el proceso de build) a la
# MISMA versión (3.11.6). python-for-android exige que ambas coincidan
# exactamente ("python3 should have same version as hostpython3"); si
# solo se fija una, la otra toma automáticamente la más nueva disponible
# (ej. 3.14), la cual eliminó módulos viejos como "cgi" que todavía usan
# algunas herramientas de empaquetado de Kivy/Cython, rompiendo la
# compilación. Python 3.11 es la versión ampliamente probada y estable
# para este tipo de compilación.
# También se usa kivy==2.2.1 (no 2.3.1) porque es la combinación más
# probada y estable junto con python-for-android==2024.1.21 (ver
# GitHub Actions workflow).
requirements = python3==3.11.6,hostpython3==3.11.6,kivy==2.2.1,openpyxl==3.1.5,plyer==2.1.0,et_xmlfile

# --- Orientación e íconos ---
orientation = portrait
fullscreen = 0
# Si más adelante quieres un ícono propio, descomenta y agrega el archivo:
# icon.filename = %(source.dir)s/data/icon.png

# --- Permisos de Android ---
# El selector de archivos moderno (Storage Access Framework) y el diálogo
# de compartir no requieren permisos de almacenamiento en Android 10+.

android.permissions = INTERNET,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE


# --- Configuración de compilación de Android ---
android.api = 33
android.minapi = 21
# NDK 25b: es el recomendado y probado por python-for-android v2024.01.21
# (el propio log de compilación lo confirma: "Recommended android's NDK
# version by p4a is: 25b"). Se había probado subir a NDK 27c pensando en
# el requisito de "páginas de memoria de 16 KB" de Android 15, pero esa
# versión de NDK es INCOMPATIBLE con el código SDL2 que trae empaquetado
# esta versión de p4a (falla con "'ALooper_pollAll' is unavailable").
# Como la causa real y CONFIRMADA del crash original fue el problema de
# kivy.input (ya resuelto bajando a kivy==2.2.1), y la teoría de las
# páginas de 16 KB nunca se llegó a confirmar, se vuelve al NDK que esta
# versión de p4a realmente soporta.
android.ndk = 25b
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True
android.enable_androidx = True

# --- Versión de python-for-android a usar ---
# CRÍTICO: sin esto, Buildozer siempre clona la rama "master" de
# python-for-android en GitHub (la más reciente y cambiante), sin
# importar qué versión se haya intentado fijar con "pip install
# python-for-android==..." en el workflow (ese pip install no tiene
# efecto real sobre qué código usa Buildozer). Esto explica por qué cada
# compilación se comportó distinto: siempre tomaba lo último que hubiera
# en esa rama en ese momento. Se fija aquí una versión de release
# congelada y estable.
p4a.branch = v2024.01.21

[buildozer]
log_level = 2
warn_on_root = 1
