[app]

# (str) Title of your application
title = Eye Tracker

# (str) Package name
package.name = eyetracker

# (str) Package domain (needed for android/ios packaging)
package.domain = org.test

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (include xml for haarcascade)
source.include_exts = py,png,jpg,kv,atlas,xml

# (list) Application requirements
# NOTA: Usar opencv nativo y NO opencv-python-headless
requirements = python3,kivy,numpy,opencv

# (str) Supported orientation (one of landscape, sensorLandscape, portrait or all)
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (list) Permissions
permissions = CAMERA, INTERNET

# =========================================================
# Android specific
