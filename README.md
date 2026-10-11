
# Eye Tracker

Aplicación experimental de seguimiento ocular desarrollada con
Python, Kivy, OpenCV y NumPy.

## Archivos del proyecto

- `main.py`: código principal del eye tracker.
- `buildozer.spec`: configuración de compilación Android.
- `.github/workflows/main.yml`: automatización para generar el APK.
- `haarcascade_frontalface_default.xml`: clasificador Haar para detectar rostros.

## Requisitos

- Python 3
- Kivy
- OpenCV
- NumPy
- Buildozer
- Android SDK y NDK instalados por el entorno de compilación

## Preparar el proyecto

1. Coloca los archivos en la raíz del repositorio.
2. Añade el clasificador Haar XML.
3. Revisa que las dependencias sean compatibles con Android.
4. Abre GitHub y entra a la pestaña Actions.
5. Ejecuta el workflow Build Eye Tracker APK.

## Descargar el APK

Si la compilación termina correctamente:

1. Abre la ejecución completada.
2. Busca la sección Artifacts.
3. Descarga `eye-tracker-debug-apk`.
4. Descomprime el archivo y transfiere el APK a tu teléfono para probarlo.

## Limitaciones actuales

- La cámara mediante `cv2.VideoCapture(0)` puede requerir adaptación
  para funcionar correctamente en Android.
- El puntero visual funciona dentro de la aplicación.
- La selección actual registra una acción, pero no controla otras
  aplicaciones ni genera un clic global del sistema.
- La precisión de la mirada debe calibrarse y validarse con usuarios.

## Objetivo

Explorar una alternativa de acceso mediante la mirada que pueda
evolucionar hacia una herramienta de comunicación aumentativa y
alternativa (CAA).

Este proyecto es experimental y requiere pruebas de funcionamiento,
accesibilidad y seguridad antes de utilizarse como apoyo comunicativo.
