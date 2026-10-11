[app]

# (str) Title of your application
title = Eye Tracker

# (str) Package name
package.name = eyetracker

# (str) Package domain (needed for android/ios packaging)
package.domain = org.test

# (str) Application version
version = 0.1

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include
source.include_exts = py,png,jpg,kv,atlas,xml

# (list) Application requirements
requirements = python3,kivy==2.2.1,numpy,opencv

# (str) Supported orientation
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (list) Permissions
permissions = CAMERA, INTERNET

# =========================================================
# Android specific
# =========================================================

# (int) Minimum API required (API 24 para NumPy)
android.minapi = 24

# (int) Target Android API
android.api = 33

# (int) NDK API to use
android.ndk_api = 24

# (bool) Accept SDK license automatically
android.accept_sdk_license = True

# (str) Android NDK architecture to build for
android.archs = arm64-v8a

[buildozer]

# (int) Log level
log_level = 1

# (int) Display warning if buildozer is run as root
warn_on_root = 1
