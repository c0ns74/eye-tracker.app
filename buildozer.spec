[app]
title = Eye Tracker
package.name = eyetracker
package.domain = org.test
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 0.1
requirements = python3,kivy

orientation = portrait
osx.python_version = 3
osx.kivy_version = 1.9.1
fullscreen = 0
android.permissions = CAMERA, INTERNET

[buildozer]
log_level = 2
warn_on_root = 1
