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

# (list) List of inclusions using pattern matching
#source.include_patterns = assets/*, images/*.png

# (list) Source files to exclude (let empty to not exclude anything)
#source.exclude_exts = spec

# (list) List of directory names to not include in the distribution
#source.exclude_dirs = tests, bin, __pycache__, .git, .github

# (list) List of exclusions using pattern matching
#source.exclude_patterns = license, images/*/*.jpg

# (str) Application versioning (method 1)
version = 1.0.0

# (str) Application versioning (method 2)
# version.regex = __version__ = ['"](.*)['"]
# version.filename = %(source.dir)s/main.py

# (list) Application requirements
#  ── ¡ATENCIÓN! ──
#  python3 y kivy deben estar primeros para que p4a los detecte bien.
#  Se incluye cython explícitamente para asegurar compatibilidad.
requirements = python3,kivy==2.2.1,plyer==2.1.0,openpyxl==3.1.5,cython==3.0.11

# (str) Custom source folders for requirements
# requirements.source.kivy = ../../kivy

# (list) Garden requirements
#garden_requirements =

# (str) Presplash of the application
#presplash.filename = %(source.dir)s/data/presplash.png

# (str) Icon of the application
#icon.filename = %(source.dir)s/data/icon.png

# (str) Supported orientation (one of landscape, portrait or all)
orientation = portrait

# (list) List of service to declare
#services = NAME:ENTRYPOINT_TO_PY,NAME2:ENTRYPOINT2_TO_PY

#
# OS X Specific
#

#
# author = © Copyright Info

# change the major version of python used by the app
osx.python_version = 3

# Kivy version to use
osx.kivy_version = 2.2.1

#
# Android Specific
#

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (string) Presplash background color (for android toolchain)
# Supported formats are: #RRGGBB #AARRGGBB or one of the following names:
# red, blue, green, black, white, gray, cyan, magenta, yellow, lightgray,
# darkgray, grey, lightgrey, darkgrey, aqua, fuchsia, lime, maroon, navy,
# olive, purple, silver, teal.
#android.presplash_color = #FFFFFF

# (string) Background color of the android boot animation
# Supported formats are: #RRGGBB #AARRGGBB or one of the following names:
# red, blue, green, black, white, gray, cyan, magenta, yellow, lightgray,
# darkgray, grey, lightgrey, darkgrey, aqua, fuchsia, lime, maroon, navy,
# olive, purple, silver, teal.
#android.bootanim_color = #FFFFFF

# (list) Permissions
#android.permissions = INTERNET

# (int) Target Android API, should be as high as possible.
android.api = 33

# (int) Minimum API your APK/App will support.
android.minapi = 21

# (int) Android SDK version to use
android.sdk = 33

# (str) Android NDK version to use
android.ndk = 25b

# (int) Android NDK API to use. This is the minimum API your app will support, it should usually match android.minapi.
android.ndk_api = 21

# (bool) Use --private storage instead of --shared.
#android.private_storage = True

# (str) Android NDK directory (if empty, it will be automatically downloaded.)
#android.ndk_path = 

# (str) Android SDK directory (if empty, it will be automatically downloaded.)
#android.sdk_path =

# (str) ANT directory (if empty, it will be automatically downloaded.)
#android.ant_path =

# (bool) If True, then skip trying to update the Android sdk
# This can be useful to avoid excess Internet downloads or save in
# case of a fresh install.
#android.skip_update = False

# (bool) If True, then automatically accept SDK license
android.accept_sdk_license = True

# (str) Android entry point, default is ok for Kivy-based app
#android.entrypoint = org.kivy.android.PythonActivity

# (list) Pattern to whitelist for the whole APK
#android.whitelist =

# (list) List of Java .jar files to add to the libs so that pyjnius can access
# their classes. Don't add jars that you do not need, since extra jars can slow
# down the build process.
#android.add_src =

# (list) List of Java AAR files to add to the libs so that pyjnius can access
# their classes. Don't add AARs that you do not need, since extra AARs can slow
# down the build process.
#android.add_aars =

# (list) Gradle dependencies to add to the build.
#android.gradle_dependencies =

# (list) add java directories to add to the build
#android.add_java_dirs =

# (bool) Enable AndroidX (Google JetPack extensions)
android.enable_androidx = True

# (list) List of Android .so libraries to copy into the APK
#android.add_libs_armeabi_v7a =
#android.add_libs_arm64_v8a =
#android.add_libs_x86 =
#android.add_libs_x86_64 =

# (bool) Indicates whether the APK should be signed to be released in the market
#android.release = False

# (str) Keystore private key (as a path)
#android.keystore = %(source.dir)s/keys/private.keystore

# (str) Keystore alias
#android.keystore_alias = 

# (str) Keystore password
#android.keystore_password = 

# (str) Keystore alias password
#android.keystore_alias_password = 

# (str) Private key
#android.private_key =

# (str) Private key password
#android.private_key_password =

# (str) Public key
#android.public_key =

# (str) Public key password
#android.public_key_password =

# (list) A list of python search paths
#android.p4a_whitelist =

# (str) PythonForAndroid distribution name
#android.dist_name = asistenciazoom

# (bool) Enable Android logcat on boot (for debugging)
#android.logcat_on_boot = True

# (str) Android logcat filters to use
#android.logcat_filters = *:S python:D

# (bool) Copy library instead of making a libpymodules.so
#android.copy_libs = 1

# (str) The Android arch to build for, choices: armeabi-v7a, arm64-v8a, x86, x86_64
android.arch = arm64-v8a

#
# Python for android (p4a) specific
#

# (str) python-for-android git clone directory (if empty, it will be automatically cloned from github)
#p4a.source_dir =

# (str) The directory in which python-for-android should look for your own build recipes (if any)
#p4a.local_recipes =

# (str) Filename to the hook for p4a
#p4a.hook =

# (str) Bootstrap to use for android builds
#p4a.bootstrap = sdl2

# (int) port number to specify an explicit --port= p4a argument (eg for bootstrap flask)
#p4a.port = 

# Control passing the --use-setup-py vs --ignore-setup-py to p4a
# "in the future" --use-setup-py is going to be the default behaviour in p4a, but for now it's not
# Setting this to false will pass --ignore-setup-py, true will pass --use-setup-py
# NOTE: this is general setuptools integration, setting to true *may* cause you trouble if you're using C extensions in p4a
p4a.setup_py = false

#
# iOS Specific
#

# (str) Path to a custom kivy-ios folder
#ios.kivy_ios_dir = ../kivy-ios
# (str) Name of the certificate to use for signing the debug version
#ios.codesign.debug = "iPhone Developer: <lastname> <firstname> (<hexstring>)"
# (str) Name of the certificate to use for signing the release version
#ios.codesign.release = %(ios.codesign.debug)s

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1

# (str) Path to build artifact storage, absolute or relative to spec file
#build_dir = ./.buildozer

# (str) Path to build output (i.e. .apk, .ipa, etc.)
#bin_dir = ./bin

#    -----------------------------------------------------------------------------
#    List as sections
#
#    You can define all the "list" as [section:key].
#    Each line will be considered as an option to the list.
#    Let's take [app] / source.exclude_patterns.
#    Instead of doing:
#        [app]
#        source.exclude_patterns = license, data/audio/*.wav, data/images/original/*
#    This can be transformed into:
#        [app]
#        source.exclude_patterns = license
#        source.exclude_patterns = data/audio/*.wav
#        source.exclude_patterns = data/images/original/*
#    ---------------------------------------------------------------------

#    Profile application 
#    You can export the project via the local directory 
#    and use it with any IDE to develop on the desktop 
#    (and use buildozer to package for android/ios)
#    (str) Path to the project directory
#    (str) Name of the main.py file (default is main.py)
#    (str) Directory of the project (default is the directory of the spec file)