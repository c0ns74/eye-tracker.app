from collections import deque
import time
import cv2
import numpy as np

from kivy.app import App
from kivy.clock import Clock
from kivy.graphics import Color, Ellipse
from kivy.graphics.texture import Texture
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.core.window import Window


def obtener_pupila_auto_calibrada(eye_roi):
    """Calcula el centroide ajustando automáticamente la exposición."""
    if eye_roi is None or eye_roi.size == 0:
        return None

    clahe_eye = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(4, 4))
    eye_eq = clahe_eye.apply(eye_roi)

    blurred = cv2.GaussianBlur(eye_eq, (5, 5), 0)
    min_val, _, _, _ = cv2.minMaxLoc(blurred)

    dynamic_thresh = int(np.clip(min_val + 15, 8, 40))
    _, threshold = cv2.threshold(blurred, dynamic_thresh, 255, cv2.THRESH_BINARY_INV)

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    threshold = cv2.morphologyEx(threshold, cv2.MORPH_OPEN, kernel)

    contours, _ = cv2.findContours(threshold, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    if contours:
        contours_validos = []
        for c in contours:
            area = cv2.contourArea(c)
            if 20 < area < (eye_roi.shape[0] * eye_roi.shape[1] * 0.25):
                x, y, w, h = cv2.boundingRect(c)
                aspect_ratio = float(w) / h
                if 0.60 <= aspect_ratio <= 1.40:
                    perimeter = cv2.arcLength(c, True)
                    if perimeter > 0:
                        circularity = 4 * np.pi * (area / (perimeter * perimeter))
                        if circularity > 0.45:
                            contours_validos.append(c)

        if contours_validos:
            c_max = max(contours_validos, key=cv2.contourArea)
            M = cv2.moments(c_max)
            if M["m00"] != 0:
                cx = M["m10"] / M["m00"]
                cy = M["m01"] / M["m00"]
                return cx, cy

    return None


class EyeTrackerWidget(BoxLayout):
    def __init__(self, **kwargs):
        super(EyeTrackerWidget, self).__init__(orientation='vertical', **kwargs)

        # Dimensiones de pantalla
        self.screen_w, self.screen_h = Window.size

        # Parámetros calibrados
        self.GAIN_X = 21.0
        self.GAIN_Y = 29.0
        self.OFFSET_Y = 0.07

        self.DEADZONE = 13.0
        self.MAX_STEP = 24.0

        self.BLINK_MIN_TIME = 0.25
        self.BLINK_MAX_TIME = 0.60

        self.ALPHA_SLOW = 0.003
        self.ALPHA_FAST = 0.16

        # Estado del eye tracker
        self.gaze_x = self.screen_w / 2.0
        self.gaze_y = self.screen_h / 2.0
        self.blink_start = None
        self.last_click_time = 0

        self.history_norm_x = deque(maxlen=8)
        self.history_norm_y = deque(maxlen=8)

        # Cargar clasificador Haar Cascade
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self.face_cascade = cv2.CascadeClassifier(cascade_path)

        # Interfaz Kivy: Vista previa de cámara e indicador de estado
        self.img_widget = Image()
        self.status_label = Label(text="Iniciando cámara...", size_hint_y=0.1)
        self.add_widget(self.img_widget)
        self.add_widget(self.status_label)

        # Indicador de puntero visual sobre la pantalla
        with self.canvas.after:
            Color(1, 0, 0, 0.8) # Rojo para la mirada
            self.pointer = Ellipse(size=(30, 30), pos=(self.gaze_x, self.gaze_y))

        # Captura de cámara OpenCV
        self.cam = cv2.VideoCapture(0)
        if not self.cam.isOpened():
            self.status_label.text = "ERROR: No se pudo abrir la cámara"
        else:
            # Planificar actualización a ~30 FPS
            Clock.schedule_interval(self.update_frame, 1.0 / 30.0)

    def update_frame(self, dt):
        success, frame = self.cam.read()
        if not success:
            return

        frame = cv2.flip(frame, 1)  # Modo espejo
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        clahe_face = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
        gray_eq = clahe_face.apply(gray)

        faces = self.face_cascade.detectMultiScale(gray_eq, 1.3, 5)

        for (x, y, w, h) in faces:
            eye_w = int(w * 0.38)
            eye_h = int(h * 0.38)
            eye_y = y + int(h * 0.18)

            eye_left_x = x + int(w * 0.10)
            roi_left = gray_eq[eye_y:eye_y + eye_h, eye_left_x:eye_left_x + eye_w]

            eye_right_x = x + int(w * 0.52)
            roi_right = gray_eq[eye_y:eye_y + eye_h, eye_right_x:eye_right_x + eye_w]

            pupil_left = obtener_pupila_auto_calibrada(roi_left)
            pupil_right = obtener_pupila_auto_calibrada(roi_right)

            # Detección de parpadeo voluntario
            if pupil_left is None and pupil_right is None:
                if self.blink_start is None:
                    self.blink_start = time.time()
                self.status_label.text = "PARPADEO DETECTADO"
            else:
                if self.blink_start is not None:
                    duration = time.time() - self.blink_start
                    self.blink_start = None

                    if self.BLINK_MIN_TIME <= duration <= self.BLINK_MAX_TIME:
                        if time.time() - self.last_click_time > 0.4:
                            self.ejecutar_accion_click()
                            self.last_click_time = time.time()

                self.status_label.text = "Eye Tracker Activo"

            norm_positions_x = []
            norm_positions_y = []

            if pupil_left is not None:
                cx_l, cy_l = pupil_left
                cv2.circle(frame, (int(eye_left_x + cx_l), int(eye_y + cy_l)), 4, (0, 255, 0), -1)
                norm_positions_x.append((cx_l / float(eye_w)) - 0.5)
                norm_positions_y.append((cy_l / float(eye_h)) - 0.5 + self.OFFSET_Y)

            if pupil_right is not None:
                cx_r, cy_r = pupil_right
                cv2.circle(frame, (int(eye_right_x + cx_r), int(eye_y + cy_r)), 4, (0, 255, 0), -1)
                norm_positions_x.append((cx_r / float(eye_w)) - 0.5)
                norm_positions_y.append((cy_r / float(eye_h)) - 0.5 + self.OFFSET_Y)

            if len(norm_positions_x) > 0:
                avg_norm_x = np.mean(norm_positions_x)
                avg_norm_y = np.mean(norm_positions_y)

                self.history_norm_x.append(avg_norm_x)
                self.history_norm_y.append(avg_norm_y)

                med_norm_x = np.median(self.history_norm_x)
                med_norm_y = np.median(self.history_norm_y)

                nx = 0.5 + np.sign(med_norm_x) * (abs(med_norm_x) ** 0.88) * self.GAIN_X
                ny = 0.5 + np.sign(med_norm_y) * (abs(med_norm_y) ** 0.88) * self.GAIN_Y

                target_x = np.clip(nx, 0.0, 1.0) * self.screen_w
                target_y = np.clip(1.0 - ny, 0.0, 1.0) * self.screen_h  # Eje Y invertido en Kivy

                dist_mov = np.hypot(target_x - self.gaze_x, target_y - self.gaze_y)

                if dist_mov > self.DEADZONE:
                    if dist_mov > 70:
                        current_alpha = self.ALPHA_FAST
                    else:
                        factor = dist_mov / 70.0
                        current_alpha = self.ALPHA_SLOW + (self.ALPHA_FAST - self.ALPHA_SLOW) * (factor ** 2)

                    desired_x = current_alpha * target_x + (1.0 - current_alpha) * self.gaze_x
                    desired_y = current_alpha * target_y + (1.0 - current_alpha) * self.gaze_y

                    step_dist = np.hypot(desired_x - self.gaze_x, desired_y - self.gaze_y)
                    if step_dist > self.MAX_STEP:
                        scale = self.MAX_STEP / step_dist
                        self.gaze_x += (desired_x - self.gaze_x) * scale
                        self.gaze_y += (desired_y - self.gaze_y) * scale
                    else:
                        self.gaze_x = desired_x
                        self.gaze_y = desired_y

                    # Actualizar la posición del puntero en pantalla
                    self.pointer.pos = (self.gaze_x - 15, self.gaze_y - 15)

            break

        # Renderizado del frame en el widget de Kivy
        buffer = cv2.flip(frame, 0).tobytes()
        texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
        texture.blit_buffer(buffer, colorfmt='bgr', bufferfmt='ubyte')
        self.img_widget.texture = texture

    def ejecutar_accion_click(self):
        """Reemplazo de pyautogui.click() en Android."""
        self.status_label.text = f"¡CLIC REGISTRADO en ({int(self.gaze_x)}, {int(self.gaze_y)})!"

    def on_stop(self):
        if self.cam.isOpened():
            self.cam.release()


class EyeTrackerApp(App):
    def build(self):
        return EyeTrackerWidget()


if __name__ == "__main__":
    EyeTrackerApp().run()