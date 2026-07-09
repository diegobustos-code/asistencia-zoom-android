[app]

# --- Información básica de la app ---
title = Asistencia Zoom
package.name = asistenciazoom
package.domain = org.sindicato

source.dir = .
source.include_exts = py,png,jpg,kv,atlas
# Este es el número de versión que ves en pantalla / en la info de la
# app instalada. Súbelo cada vez que compiles una versión nueva para
# poder distinguirlas (ej. 1.14, 1.15, ...). Esto por sí solo NO
# soluciona el error al actualizar sobre una instalación anterior — ver
# la nota sobre la "firma" (keystore) más abajo y en build-apk.yml.
version = 1.14

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
# Se agrega "androidstorage4kivy": es un paquete Python puro (sin
# compilación nativa propia, así que no agrega riesgo de romper la
# compilación) que permite copiar los archivos exportados a la carpeta
# PÚBLICA "Download" del celular. Es necesario porque desde Android 10
# en adelante ya no se puede escribir directamente en carpetas públicas
# con un simple open()/os.path — hay que pasar por la API oficial de
# almacenamiento compartido de Android, que es justo lo que envuelve
# este paquete.
requirements = python3==3.11.6,hostpython3==3.11.6,kivy==2.2.1,openpyxl==3.1.5,plyer==2.1.0,et_xmlfile,androidstorage4kivy

# --- Orientación e íconos ---
# "portrait" bloqueaba la rotación por completo (el celular ignoraba el
# sensor de giro). Buildozer NO acepta el valor "all" (por eso falló la
# última compilación: "[app] 'all' is not a valid value for
# 'orientation'") — el valor correcto para permitir ambas orientaciones
# es una lista separada por comas con los nombres exactos que Buildozer
# reconoce: "portrait,landscape".
orientation = portrait,landscape
fullscreen = 0
# Ícono del launcher (escritorio/cajón de apps) y pantalla de carga al
# abrir la app. Ambos archivos van en data/icon.png y data/presplash.png
# dentro del repo (junto a buildozer.spec).
icon.filename = %(source.dir)s/data/icon.png
presplash.filename = %(source.dir)s/data/presplash.png
# Color de fondo de la pantalla de carga, para que combine con el borde
# claro del logo en vez de mostrar el negro por defecto de Kivy.
presplash.color = #E5EAEE

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
