[app]

# --- Información básica de la app ---
title = Asistencia Zoom
package.name = asistenciazoom
package.domain = org.sindicato

source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0

# --- Dependencias que necesita la app dentro del APK ---
# (mismas librerías que usa la versión de escritorio + kivy + plyer para
# el selector de archivos nativo y el diálogo de "compartir" de Android)
# NOTA: se usa kivy==2.2.1 (no 2.3.1) porque es la combinación más
# probada y estable junto con python-for-android==2024.1.21 (ver
# GitHub Actions workflow). Pedir una versión de Kivy más nueva que la
# que esta "receta" de compilación conoce bien puede armar un paquete
# incompleto (por ejemplo, faltando el submódulo kivy.input, que es
# justamente lo que provocaba que la app se cerrara sola sin error).
requirements = python3,kivy==2.2.1,openpyxl==3.1.5,plyer,et_xmlfile

# --- Orientación e íconos ---
orientation = portrait
fullscreen = 0
# Si más adelante quieres un ícono propio, descomenta y agrega el archivo:
# icon.filename = %(source.dir)s/data/icon.png

# --- Permisos de Android ---
# El selector de archivos moderno (Storage Access Framework) y el diálogo
# de compartir no requieren permisos de almacenamiento en Android 10+.
android.permissions = INTERNET

# --- Configuración de compilación de Android ---
android.api = 33
android.minapi = 21
# NDK r27 (en vez de r25b): agrega por defecto el alineamiento de 16 KB
# que exigen los celulares Android 15 más nuevos (como los Honor donde
# la app se quedaba en pantalla negra / colgada sin ningún error visible).
android.ndk = 27c
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True
android.enable_androidx = True
android.gradle_dependencies = 
android.add_src = 
p4a.bootstrap = sdl2
p4a.local_recipes = ./recipes
p4a.dist_name = asistenciazoom

[buildozer]
log_level = 2
warn_on_root = 1
# Agrega esto:
android.sdk_path = ~/.buildozer/android/sdk
android.ndk_path = ~/.buildozer/android/ndk
