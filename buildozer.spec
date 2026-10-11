
[app]

title = Eye Tracker
package.name = eyetracker
package.domain = org.test

source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,json,ttf,wav,mp3
version = 0.1

requirements = python3,kivy,opencv

orientation = portrait
fullscreen = 0

android.permissions = CAMERA,INTERNET
android.api = 33
android.minapi = 23
android.archs = arm64-v8a

android.accept_sdk_license = True
android.enable_androidx = True

[buildozer]

log_level = 2
warn_on_root = 1
