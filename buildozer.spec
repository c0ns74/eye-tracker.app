[app]
title = Eye Tracker
package.name = eyetracker
package.domain = org.test
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 0.1

# Usar python3cpython3==3.11.0 evita que Buildozer clone Python 3.14 de Git
requirements = python3cpython3==3.11.0,kivy

orientation = portrait
fullscreen = 0
android.permissions = CAMERA, INTERNET

android.accept_sdk_license = True
android.api = 33
android.minapi = 21
android.archs = arm64-v8a, armeabi-v7a

[buildozer]
log_level = 2
warn_on_root = 1
