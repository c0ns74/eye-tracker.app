from collections import deque
import os
import time

import cv2
import numpy as np

from kivy.app import App
from kivy.clock import Clock
from kivy.graphics import Color, Ellipse
from kivy.graphics.texture import Texture
from kivy.resources import resource_find
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.core.window import Window


def obtener_pupila_auto_calibrada(eye_roi):
    """Estima el centro de la pupila dentro de una región ocular."""
    if eye_roi is None or eye_roi.size == 0:
        return None

    clahe = cv2.createCLAHE(
        clipLimit=3.0,
        tileGridSize=(4, 4)
    )
    eye_eq = clahe.apply(eye_roi)
    blurred = cv2.GaussianBlur(eye_eq, (5, 5), 0)

    min_val, _, _, _ = cv2.minMaxLoc(blurred)

    threshold_value = int(
        np.clip(min_val + 15, 8, 40)
    )

    _, threshold = cv2.threshold(
        blurred,
        threshold_value,
        255,
        cv2.THRESH_BINARY_INV
    )

    kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE,
        (3, 3)
    )

    threshold = cv2.morphologyEx(
        threshold,
        cv2.MORPH_OPEN,
        kernel
    )

    contours, _ = cv2.findContours(
        threshold,
        cv2.RETR_TREE,
        cv2.CHAIN_APPROX_SIMPLE
    )

    valid_contours = []

    for contour in contours:
        area = cv2.contourArea(contour)

        if not (
            20 < area <
            eye_roi.shape[0] * eye_roi.shape[1] * 0.25
        ):
            continue

        x, y, w, h = cv2.boundingRect(contour)

        if h == 0:
            continue

        aspect_ratio = float(w) / h

        if not 0.60 <= aspect_ratio <= 1.40:
            continue

        perimeter = cv2.arcLength(contour, True)

        if perimeter <= 0:
            continue

        circularity = (
            4 * np.pi * area /
            (perimeter * perimeter)
        )

        if circularity > 0.45:
            valid_contours.append(contour)

    if not valid_contours:
        return None

    best = max(
        valid_contours,
        key=cv2.contourArea
    )

    moments = cv2.moments(best)

    if moments["m00"] == 0:
        return None

    cx = moments["m10"] / moments["m00"]
    cy = moments["m01"] / moments["m00"]

    return cx, cy


class EyeTrackerWidget(BoxLayout):

    def __init__(self, **kwargs):
        super().__init__(
            orientation="vertical",
            **kwargs
        )

        self.screen_w, self.screen_h = Window.size

        # Parámetros iniciales de seguimiento
        self.GAIN_X = 21.0
        self.GAIN_Y = 29.0
        self.OFFSET_Y = 0.07

        self.DEADZONE = 13.0
        self.MAX_STEP = 24.0

        self.BLINK_MIN_TIME = 0.25
        self.BLINK_MAX_TIME = 0.60

        self.ALPHA_SLOW = 0.003
        self.ALPHA_FAST = 0.16

        # Estado del puntero
        self.gaze_x = self.screen_w / 2.0
        self.gaze_y = self.screen_h / 2.0

        self.blink_start = None
        self.last_click_time = 0.0

        self.history_norm_x = deque(maxlen=8)
        self.history_norm_y = deque(maxlen=8)

        self.cam = None
        self.capture_event = None
        self.face_cascade = None

        # Interfaz
        self.img_widget = Image()

        self.status_label = Label(
            text="Preparando cámara...",
            size_hint_y=0.12
        )

        self.add_widget(self.img_widget)
        self.add_widget(self.status_label)

        # Puntero visual
        with self.canvas.after:
            Color(1, 0, 0, 0.8)

            self.pointer = Ellipse(
                size=(30, 30),
                pos=(
                    self.gaze_x - 15,
                    self.gaze_y - 15
                )
            )

        self.cargar_clasificador()

        # Captura de cámara.
        # Puede requerir adaptación en algunos teléfonos Android.
        self.cam = cv2.VideoCapture(0)

        if self.cam is None or not self.cam.isOpened():
            self.status_label.text = (
                "No se pudo abrir la cámara. "
                "Revisa permisos y compatibilidad."
            )
        else:
            self.status_label.text = "Eye Tracker activo"

            self.capture_event = Clock.schedule_interval(
                self.update_frame,
                1.0 / 30.0
            )

    def cargar_clasificador(self):
        """Carga el XML Haar incluido en la aplicación."""
        cascade_path = resource_find(
            "haarcascade_frontalface_default.xml"
        )

        if not cascade_path:
            cascade_path = os.path.join(
                os.path.dirname(__file__),
                "haarcascade_frontalface_default.xml"
            )

        if os.path.exists(cascade_path):
            cascade = cv2.CascadeClassifier(cascade_path)

            if not cascade.empty():
                self.face_cascade = cascade

        if self.face_cascade is None:
            self.status_label.text = (
                "Falta haarcascade_frontalface_default.xml"
            )

    def update_frame(self, dt):
        if self.cam is None or not self.cam.isOpened():
            return

        success, frame = self.cam.read()

        if not success or frame is None:
            self.status_label.text = (
                "No se recibió imagen de la cámara"
            )
            return

        # Imagen espejo
        frame = cv2.flip(frame, 1)

        gray = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2GRAY
        )

        clahe_face = cv2.createCLAHE(
            clipLimit=2.5,
            tileGridSize=(8, 8)
        )

        gray_eq = clahe_face.apply(gray)

        if self.face_cascade is not None:
            faces = self.face_cascade.detectMultiScale(
                gray_eq,
                scaleFactor=1.3,
                minNeighbors=5
            )
        else:
            faces = []

        for (x, y, w, h) in faces:

            eye_w = int(w * 0.38)
            eye_h = int(h * 0.38)
            eye_y = y + int(h * 0.18)

            eye_left_x = x + int(w * 0.10)
            eye_right_x = x + int(w * 0.52)

            roi_left = gray_eq[
                eye_y:eye_y + eye_h,
                eye_left_x:eye_left_x + eye_w
            ]

            roi_right = gray_eq[
                eye_y:eye_y + eye_h,
                eye_right_x:eye_right_x + eye_w
            ]

            pupil_left = obtener_pupila_auto_calibrada(
                roi_left
            )

            pupil_right = obtener_pupila_auto_calibrada(
                roi_right
            )

            # Detección aproximada de parpadeo
            if (
                pupil_left is None
                and pupil_right is None
            ):
                if self.blink_start is None:
                    self.blink_start = time.time()

                self.status_label.text = (
                    "Posible parpadeo"
                )

            else:
                if self.blink_start is not None:
                    duration = (
                        time.time() - self.blink_start
                    )

                    self.blink_start = None

                    if (
                        self.BLINK_MIN_TIME
                        <= duration
                        <= self.BLINK_MAX_TIME
                    ):
                        if (
                            time.time() - self.last_click_time
                            > 0.4
                        ):
                            self.ejecutar_accion_click()
                            self.last_click_time = time.time()

                self.status_label.text = (
                    "Eye Tracker activo"
                )

            norm_x = []
            norm_y = []

            if (
                pupil_left is not None
                and eye_w > 0
                and eye_h > 0
            ):
                cx, cy = pupil_left

                cv2.circle(
                    frame,
                    (
                        int(eye_left_x + cx),
                        int(eye_y + cy)
                    ),
                    4,
                    (0, 255, 0),
                    -1
                )

                norm_x.append(
                    cx / float(eye_w) - 0.5
                )

                norm_y.append(
                    cy / float(eye_h)
                    - 0.5
                    + self.OFFSET_Y
                )

            if (
                pupil_right is not None
                and eye_w > 0
                and eye_h > 0
            ):
                cx, cy = pupil_right

                cv2.circle(
                    frame,
                    (
                        int(eye_right_x + cx),
                        int(eye_y + cy)
                    ),
                    4,
                    (0, 255, 0),
                    -1
                )

                norm_x.append(
                    cx / float(eye_w) - 0.5
                )

                norm_y.append(
                    cy / float(eye_h)
                    - 0.5
                    + self.OFFSET_Y
                )

            if norm_x:
                self.history_norm_x.append(
                    float(np.mean(norm_x))
                )

                self.history_norm_y.append(
                    float(np.mean(norm_y))
                )

                med_x = float(
                    np.median(self.history_norm_x)
                )

                med_y = float(
                    np.median(self.history_norm_y)
                )

                nx = (
                    0.5
                    + np.sign(med_x)
                    * abs(med_x) ** 0.88
                    * self.GAIN_X
                )

                ny = (
                    0.5
                    + np.sign(med_y)
                    * abs(med_y) ** 0.88
                    * self.GAIN_Y
                )

                target_x = (
                    np.clip(nx, 0.0, 1.0)
                    * self.screen_w
                )

                target_y = (
                    np.clip(1.0 - ny, 0.0, 1.0)
                    * self.screen_h
                )

                distance = np.hypot(
                    target_x - self.gaze_x,
                    target_y - self.gaze_y
                )

                if distance > self.DEADZONE:

                    if distance > 70:
                        alpha = self.ALPHA_FAST
                    else:
                        factor = distance / 70.0

                        alpha = (
                            self.ALPHA_SLOW
                            + (
                                self.ALPHA_FAST
                                - self.ALPHA_SLOW
                            ) * factor ** 2
                        )

                    desired_x = (
                        alpha * target_x
                        + (1 - alpha) * self.gaze_x
                    )

                    desired_y = (
                        alpha * target_y
                        + (1 - alpha) * self.gaze_y
                    )

                    step = np.hypot(
                        desired_x - self.gaze_x,
                        desired_y - self.gaze_y
                    )

                    if step > self.MAX_STEP:
                        scale = self.MAX_STEP / step

                        self.gaze_x += (
                            desired_x - self.gaze_x
                        ) * scale

                        self.gaze_y += (
                            desired_y - self.gaze_y
                        ) * scale
                    else:
                        self.gaze_x = desired_x
                        self.gaze_y = desired_y

                    self.pointer.pos = (
                        self.gaze_x - 15,
                        self.gaze_y - 15
                    )

            # Procesar solo el primer rostro detectado
            break

        # Actualizar la vista previa
        frame_display = cv2.flip(frame, 0)

        texture = Texture.create(
            size=(
                frame_display.shape[1],
                frame_display.shape[0]
            ),
            colorfmt="bgr"
        )

        texture.blit_buffer(
            frame_display.tobytes(),
            colorfmt="bgr",
            bufferfmt="ubyte"
        )

        self.img_widget.texture = texture

    def ejecutar_accion_click(self):
        """
        Registra una selección dentro de esta aplicación.
        No genera un clic global del sistema Android.
        """
        self.status_label.text = (
            f"Selección registrada: "
            f"({int(self.gaze_x)}, {int(self.gaze_y)})"
        )

    def liberar_camara(self, *_):
        if self.capture_event is not None:
            self.capture_event.cancel()
            self.capture_event = None

        if self.cam is not None:
            try:
                if self.cam.isOpened():
                    self.cam.release()
            except Exception:
                pass

            self.cam = None


class EyeTrackerApp(App):

    def build(self):
        self.tracker = EyeTrackerWidget()
        return self.tracker

    def on_stop(self):
        if hasattr(self, "tracker"):
            self.tracker.liberar_camara()


if __name__ == "__main__":
    EyeTrackerApp().run()