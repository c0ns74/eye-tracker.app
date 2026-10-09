[app]

title = Eye Tracker
package.name = eyetracker
package.domain = org.test
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,xml
version = 0.1
requirements = python3,kivy,opencv
orientation = portrait
fullscreen = 0
android.permissions = CAMERA, INTERNET
android.api = 33
android.minapi = 24
android.ndk = 25b
android.ndk_api = 24
p4a.branch = master

[buildozer]

log_level = 2
warn_on_root = 1