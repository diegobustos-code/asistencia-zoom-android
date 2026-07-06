[app]
title = Asistencia Zoom
package.name = asistenciazoom
package.domain = org.sindicato

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,txt
version = 1.0

# Dependencias — NO incluir et_xmlfile (es transitiva de openpyxl)
requirements = python3,kivy==2.2.1,plyer==2.1.0,openpyxl==3.1.5

orientation = portrait
fullscreen = 0

android.permissions = INTERNET,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE

android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a,armeabi-v7a
android.allow_backup = True
android.enable_androidx = True

# Fuerza recompilacion de kivy si la version cambia
android.add_compile_options = "sourceCompatibility = JavaVersion.VERSION_17" "targetCompatibility = JavaVersion.VERSION_17"

[buildozer]
log_level = 2
warn_on_root = 1
