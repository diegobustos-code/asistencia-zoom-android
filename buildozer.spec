[app]

# --- Información básica de la app ---
title = Asistencia Zoom
package.name = asistenciazoom
package.domain = org.sindicato

source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0

# --- Dependencias dentro del APK ---
requirements = python3,kivy==2.2.1,plyer==2.1.0,openpyxl==3.1.5,et_xmlfile

# --- Orientación e íconos ---
orientation = portrait
fullscreen = 0
# icon.filename = %(source.dir)s/data/icon.png

# --- Permisos de Android ---
android.permissions = INTERNET

# --- Configuración de compilación de Android ---
android.api = 31
android.minapi = 21
# Recomiendo NDK r25b o r27c según compatibilidad; python-for-android 2024.1.21 funciona bien con r25b/r27c.
android.ndk = 25b
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True
android.enable_androidx = True
p4a.bootstrap = sdl2
p4a.local_recipes = ./recipes
p4a.dist_name = asistenciazoom

[buildozer]
log_level = 2
warn_on_root = 1
android.sdk_path = ~/.buildozer/android/sdk
android.ndk_path = ~/.buildozer/android/ndk

