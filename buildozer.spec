[app]

# (str) Title of your application
title = Asistencia Zoom

# (str) Package name
package.name = asistenciazoom

# (str) Package domain (needed for android/ios packaging)
package.domain = org.example

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas,ttf

# (list) Source files to exclude (let empty to not exclude anything)
source.exclude_exts = spec

# (list) List of directory names to not include in the distribution
source.exclude_dirs = tests, bin, __pycache__, .git, .github

# (str) Application versioning
version = 1.0.0

# (list) Application requirements
# NOTA: kivy NO debe instalarse en el sistema local, buildozer la usará desde la receta de Android
requirements = python3,kivy==2.2.1,plyer==2.1.0,openpyxl==3.1.5

# (str) Supported orientation
orientation = portrait

#
# Android Specific
#

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (int) Target Android API
android.api = 33

# (int) Minimum API your APK/App will support
android.minapi = 21

# (int) Android SDK version to use
android.sdk = 33

# (str) Android NDK version to use
android.ndk = 25b

# (int) Android NDK API to use
android.ndk_api = 21

# (bool) If True, then automatically accept SDK license
android.accept_sdk_license = True

# (bool) Enable AndroidX
android.enable_androidx = True

# (str) The Android arch to build for
android.arch = arm64-v8a

# Control passing the --use-setup-py vs --ignore-setup-py to p4a
p4a.setup_py = false

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug)
log_level = 2

# (int) Display warning if buildozer is run as root
warn_on_root = 1