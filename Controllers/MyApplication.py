import imageio
import numpy as np
import traceback
from PIL import ImageQt, Image
from PySide6.QtCore import QThreadPool, Qt, Slot
from PySide6.QtGui import QIcon, QPixmap, QImageReader
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QApplication, QGraphicsScene, QFileDialog
from threading import Event

from Controllers.MouseDetector import MouseDetector
from Controllers.Worker import Worker
from Models.Effect.Cylinder import Cylinder
from Models.Effect.FishEye_Effect import FishEye_Effect
from Models.Effect.RadialBlur_Effect import RadialBlur_Effect
from Models.Effect.SquareEye_Effect import SquareEye_Effect
from Models.Effect.Swirl_Effect import Swirl_Effect
from Models.Effect.Waves_Effect import Waves_Effect
from Models.Filter.Gaussian_Filter import Gaussian_Filter
from Models.Filter.Mean_Filter import Mean_Filter
from Models.Filter.Median_Filter import Median_Filter


class MyApplication:
    def __init__(self):
        loader = QUiLoader()
        self.window = loader.load("mainmenu.ui", None)

        # For threading
        QApplication.instance().aboutToQuit.connect(self.exit_handler)
        self.threadpool = QThreadPool()
        self.worker = Worker()
        self.threadpool.start(self.worker)
        self.worker.signals.processed.connect(self.update_image_view, Qt.QueuedConnection)

        self.image = None
        self.images_stack = []

        self.current_tab_idx = 0
        self.current_tab_name = "About"

        self.effects_to_tab_idx = {"Fish Eye Effect": 1, "Swirl Effect": 2, "Waves Effect": 3,
                                   "Cylinder Anamorphosis": 4, "Radial Blur Effect": 5, "Square Eye Effect": 7, "Median Blurring": 8,
                                   "Gaussian Filtering": 9, "Mean Filter": 11, "About": 0}

        self.parameters = self.get_default_parameters()

        self.fisheye_effect_parameters = [self.window.fisheye_x_slider, self.window.fisheye_y_slider,
                                          self.window.fisheye_sigma_slider,
                                          self.window.fisheye_x_spinbox, self.window.fisheye_y_spinbox,
                                          self.window.fisheye_sigma_spinbox]

        self.swirl_effect_parameters = [self.window.swirl_x_slider, self.window.swirl_y_slider,
                                        self.window.swirl_sigma_slider, self.window.swirl_magnitude_slider,
                                        self.window.swirl_x_spinbox, self.window.swirl_y_spinbox,
                                        self.window.swirl_sigma_spinbox, self.window.swirl_magnitude_spinbox]

        self.waves_effect_parameters = [self.window.waves_amplitude_slider, self.window.waves_freq_slider,
                                        self.window.waves_phase_slider,
                                        self.window.waves_amplitude_spinbox, self.window.waves_freq_spinbox,
                                        self.window.waves_phase_spinbox]

        self.cylinder_effect_parameters = [self.window.cylinder_angle_slider, self.window.cylinder_angle_spinbox]

        self.radial_blur_effect_parameters = [self.window.radial_sigma_slider, self.window.radial_sigma_spinbox]

        self.square_eye_effect_parameters = [self.window.square_eye_x_slider, self.window.square_eye_y_slider,
                                             self.window.square_eye_sigma_slider, self.window.square_eye_p_slider,
                                             self.window.square_eye_x_spinbox, self.window.square_eye_y_spinbox,
                                             self.window.square_eye_sigma_spinbox, self.window.square_eye_p_spinbox]

        self.median_blur_parameters = [self.window.median_size_slider, self.window.median_size_spinbox]

        self.gaussian_blur_parameters = [self.window.gaussian_radius_slider, self.window.gaussian_radius_spinbox]

        self.mean_blur_parameters = [self.window.mean_size_slider, self.window.mean_size_spinbox]

        self.tabs_to_apply_buttons_and_params = {
            "Fish Eye Effect": {"button": self.window.fisheye_apply_button, "params": self.fisheye_effect_parameters},
            "Swirl Effect": {"button": self.window.swirl_apply_button, "params": self.swirl_effect_parameters},
            "Waves Effect": {"button": self.window.waves_apply_button, "params": self.waves_effect_parameters},
            "Cylinder Anamorphosis": {"button": self.window.cylinder_apply_button,
                                      "params": self.cylinder_effect_parameters},
            "Radial Blur Effect": {"button": self.window.radial_apply_button,
                                   "params": self.radial_blur_effect_parameters},
            "Square Eye Effect": {"button": self.window.square_eye_apply_button,
                                  "params": self.square_eye_effect_parameters},
            "Median Blurring": {"button": self.window.median_apply_button, "params": self.median_blur_parameters},
            "Gaussian Filtering": {"button": self.window.gaussian_apply_button,
                                   "params": self.gaussian_blur_parameters},
            "Mean Filter": {"button": self.window.mean_apply_button, "params": self.mean_blur_parameters}
        }

        self.mainmenu_setup()
        self.window.show()

    def exit_handler(self):
        self.worker.terminate = True

    def mainmenu_setup(self):
        w = self.window
        w.setWindowTitle("Image Processing Tool")
        w.resize(1000, 800)

        app_icon = QIcon()
        app_icon.addFile('icon.png')
        w.setWindowIcon(app_icon)

        w.treeWidget.expandAll()

        self.disable_buttons([w.save_button, w.reset_button, w.undo_button,
                              w.fisheye_apply_button, w.swirl_apply_button,
                              w.waves_apply_button, w.cylinder_apply_button,
                              w.radial_apply_button, w.square_eye_apply_button,
                              w.median_apply_button, w.gaussian_apply_button,
                              w.mean_apply_button])

        pixmap = QPixmap("icon.png")
        w.icon_label.setScaledContents(True)
        w.icon_label.setPixmap(pixmap)

        w.load_button.clicked.connect(lambda l: self.load_button_event(w.graphicsView))
        w.save_button.clicked.connect(lambda l: self.save_button_event())
        w.reset_button.clicked.connect(lambda l: self.reset_button_event("main_image"))
        w.undo_button.clicked.connect(lambda l: self.undo_button_event())
        w.treeWidget.itemClicked.connect(self.dashboard_clicked_event)

        self.mouseFilter = MouseDetector()
        self.mouseFilter.app = self
        QApplication.instance().installEventFilter(self.mouseFilter)

        self.select_x_spinbox = None
        self.select_y_spinbox = None

        # Fish Eye Effect Controller
        w.fisheye_x_spinbox.valueChanged.connect(lambda l: w.fisheye_x_slider.setValue(w.fisheye_x_spinbox.value()))
        w.fisheye_x_slider.valueChanged.connect(lambda l: w.fisheye_x_spinbox.setValue(w.fisheye_x_slider.value()))
        w.fisheye_x_spinbox.valueChanged.connect(
            lambda l: self.update_parameter("fisheye", "x", w.fisheye_x_spinbox.value()))

        w.fisheye_y_spinbox.valueChanged.connect(lambda l: w.fisheye_y_slider.setValue(w.fisheye_y_spinbox.value()))
        w.fisheye_y_slider.valueChanged.connect(lambda l: w.fisheye_y_spinbox.setValue(w.fisheye_y_slider.value()))
        w.fisheye_y_spinbox.valueChanged.connect(
            lambda l: self.update_parameter("fisheye", "y", w.fisheye_y_spinbox.value()))

        w.fisheye_sigma_spinbox.valueChanged.connect(
            lambda l: w.fisheye_sigma_slider.setValue(w.fisheye_sigma_spinbox.value()))
        w.fisheye_sigma_slider.valueChanged.connect(
            lambda l: w.fisheye_sigma_spinbox.setValue(w.fisheye_sigma_slider.value()))
        w.fisheye_sigma_spinbox.valueChanged.connect(
            lambda l: self.update_parameter("fisheye", "sigma", w.fisheye_sigma_spinbox.value()))

        # Swirl Effect Controller
        w.swirl_x_spinbox.valueChanged.connect(lambda l: w.swirl_x_slider.setValue(w.swirl_x_spinbox.value()))
        w.swirl_x_slider.valueChanged.connect(lambda l: w.swirl_x_spinbox.setValue(w.swirl_x_slider.value()))
        w.swirl_x_spinbox.valueChanged.connect(lambda l: self.update_parameter("swirl", "x", w.swirl_x_spinbox.value()))

        w.swirl_y_spinbox.valueChanged.connect(lambda l: w.swirl_y_slider.setValue(w.swirl_y_spinbox.value()))
        w.swirl_y_slider.valueChanged.connect(lambda l: w.swirl_y_spinbox.setValue(w.swirl_y_slider.value()))
        w.swirl_y_spinbox.valueChanged.connect(lambda l: self.update_parameter("swirl", "y", w.swirl_y_spinbox.value()))

        w.swirl_sigma_spinbox.valueChanged.connect(
            lambda l: w.swirl_sigma_slider.setValue(w.swirl_sigma_spinbox.value() * 100))
        w.swirl_sigma_slider.valueChanged.connect(
            lambda l: w.swirl_sigma_spinbox.setValue(w.swirl_sigma_slider.value() / 100))
        w.swirl_sigma_spinbox.valueChanged.connect(
            lambda l: self.update_parameter("swirl", "sigma", w.swirl_sigma_spinbox.value()))

        w.swirl_magnitude_spinbox.valueChanged.connect(
            lambda l: w.swirl_magnitude_slider.setValue(w.swirl_magnitude_spinbox.value()))
        w.swirl_magnitude_slider.valueChanged.connect(
            lambda l: w.swirl_magnitude_spinbox.setValue(w.swirl_magnitude_slider.value()))
        w.swirl_magnitude_spinbox.valueChanged.connect(
            lambda l: self.update_parameter("swirl", "magnitude", w.swirl_magnitude_spinbox.value()))

        # Waves Effect Controller
        w.waves_amplitude_spinbox.valueChanged.connect(
            lambda l: w.waves_amplitude_slider.setValue(w.waves_amplitude_spinbox.value()))
        w.waves_amplitude_slider.valueChanged.connect(
            lambda l: w.waves_amplitude_spinbox.setValue(w.waves_amplitude_slider.value()))
        w.waves_amplitude_spinbox.valueChanged.connect(
            lambda l: self.update_parameter("waves", "amplitude", w.waves_amplitude_spinbox.value()))

        w.waves_freq_spinbox.valueChanged.connect(lambda l: w.waves_freq_slider.setValue(w.waves_freq_spinbox.value()))
        w.waves_freq_slider.valueChanged.connect(lambda l: w.waves_freq_spinbox.setValue(w.waves_freq_slider.value()))
        w.waves_freq_spinbox.valueChanged.connect(
            lambda l: self.update_parameter("waves", "frequency", w.waves_freq_spinbox.value()))

        w.waves_phase_spinbox.valueChanged.connect(
            lambda l: w.waves_phase_slider.setValue(w.waves_phase_spinbox.value()))
        w.waves_phase_slider.valueChanged.connect(
            lambda l: w.waves_phase_spinbox.setValue(w.waves_phase_slider.value()))
        w.waves_phase_spinbox.valueChanged.connect(
            lambda l: self.update_parameter("waves", "phase", w.waves_phase_spinbox.value()))

        # Cylinder Anamorphosis Controller
        w.cylinder_angle_spinbox.valueChanged.connect(
            lambda l: w.cylinder_angle_slider.setValue(w.cylinder_angle_spinbox.value()))
        w.cylinder_angle_slider.valueChanged.connect(
            lambda l: w.cylinder_angle_spinbox.setValue(w.cylinder_angle_slider.value()))
        w.cylinder_angle_spinbox.valueChanged.connect(
            lambda l: self.update_parameter("cylinder", "angle", w.cylinder_angle_spinbox.value()))

        # Radial Blur Effect Controller
        w.radial_sigma_spinbox.valueChanged.connect(
            lambda l: w.radial_sigma_slider.setValue(w.radial_sigma_spinbox.value()))
        w.radial_sigma_slider.valueChanged.connect(
            lambda l: w.radial_sigma_spinbox.setValue(w.radial_sigma_slider.value()))
        w.radial_sigma_spinbox.valueChanged.connect(
            lambda l: self.update_parameter("radial_blur", "sigma", w.radial_sigma_spinbox.value()))

        # Square Eye Effect Controller
        w.square_eye_x_spinbox.valueChanged.connect(
            lambda l: w.square_eye_x_slider.setValue(w.square_eye_x_spinbox.value()))
        w.square_eye_x_slider.valueChanged.connect(
            lambda l: w.square_eye_x_spinbox.setValue(w.square_eye_x_slider.value()))
        w.square_eye_x_spinbox.valueChanged.connect(
            lambda l: self.update_parameter("square_eye", "x", w.square_eye_x_spinbox.value()))

        w.square_eye_y_spinbox.valueChanged.connect(
            lambda l: w.square_eye_y_slider.setValue(w.square_eye_y_spinbox.value()))
        w.square_eye_y_slider.valueChanged.connect(
            lambda l: w.square_eye_y_spinbox.setValue(w.square_eye_y_slider.value()))
        w.square_eye_y_spinbox.valueChanged.connect(
            lambda l: self.update_parameter("square_eye", "y", w.square_eye_y_spinbox.value()))

        w.square_eye_sigma_spinbox.valueChanged.connect(
            lambda l: w.square_eye_sigma_slider.setValue(w.square_eye_sigma_spinbox.value()))
        w.square_eye_sigma_slider.valueChanged.connect(
            lambda l: w.square_eye_sigma_spinbox.setValue(w.square_eye_sigma_slider.value()))
        w.square_eye_sigma_spinbox.valueChanged.connect(
            lambda l: self.update_parameter("square_eye", "sigma", w.square_eye_sigma_spinbox.value()))

        w.square_eye_p_spinbox.valueChanged.connect(
            lambda l: w.square_eye_p_slider.setValue(w.square_eye_p_spinbox.value()))
        w.square_eye_p_slider.valueChanged.connect(
            lambda l: w.square_eye_p_spinbox.setValue(w.square_eye_p_slider.value()))
        w.square_eye_p_spinbox.valueChanged.connect(
            lambda l: self.update_parameter("square_eye", "p_value", w.square_eye_p_spinbox.value()))

        # Median Blurring Controller
        w.median_size_spinbox.valueChanged.connect(
            lambda l: w.median_size_slider.setValue(w.median_size_spinbox.value()))
        w.median_size_slider.valueChanged.connect(
            lambda l: w.median_size_spinbox.setValue(w.median_size_slider.value()))
        w.median_size_spinbox.valueChanged.connect(
            lambda l: self.update_parameter("median", "size", w.median_size_spinbox.value()))

        # Gaussian Filter Controller
        w.gaussian_radius_spinbox.valueChanged.connect(
            lambda l: w.gaussian_radius_slider.setValue(w.gaussian_radius_spinbox.value()))
        w.gaussian_radius_slider.valueChanged.connect(
            lambda l: w.gaussian_radius_spinbox.setValue(w.gaussian_radius_slider.value()))
        w.gaussian_radius_spinbox.valueChanged.connect(
            lambda l: self.update_parameter("gaussian", "radius", w.gaussian_radius_spinbox.value()))

        # Mean Filter Controller
        w.mean_size_spinbox.valueChanged.connect(lambda l: w.mean_size_slider.setValue(w.mean_size_spinbox.value()))
        w.mean_size_slider.valueChanged.connect(lambda l: w.mean_size_spinbox.setValue(w.mean_size_slider.value()))
        w.mean_size_spinbox.valueChanged.connect(
            lambda l: self.update_parameter("mean", "size", w.mean_size_spinbox.value()))

        # Apply Button Controller
        w.fisheye_apply_button.clicked.connect(lambda l: self.fisheye_effect_apply_button_event())
        w.swirl_apply_button.clicked.connect(lambda l: self.swirl_effect_apply_button_event())
        w.waves_apply_button.clicked.connect(lambda l: self.waves_effect_apply_button_event())
        w.cylinder_apply_button.clicked.connect(lambda l: self.cylinder_effect_apply_button_event())
        w.radial_apply_button.clicked.connect(lambda l: self.radial_blur_effect_apply_button_event())
        w.square_eye_apply_button.clicked.connect(lambda l: self.square_eye_apply_button_event())
        w.gaussian_apply_button.clicked.connect(lambda l: self.gaussian_blur_apply_button_event())
        w.median_apply_button.clicked.connect(lambda l: self.median_blur_apply_button_event())
        w.mean_apply_button.clicked.connect(lambda l: self.mean_blur_apply_button_event())

    def update_parameter(self, effect_name, parameter_name, value):
        self.parameters[effect_name][parameter_name] = value
        if self.image is not None:
            self.update_image(effect_name)
            # print("update_image_function called")

    def update_image(self, effect_name):
        if effect_name == "fisheye":
            center_point = (self.parameters[effect_name]["y"], self.parameters[effect_name]["x"])
            sigma = self.parameters[effect_name]["sigma"]
            self.worker.process(FishEye_Effect, (self.image, center_point, sigma))

        elif effect_name == "swirl":
            center_point = (self.parameters[effect_name]["y"], self.parameters[effect_name]["x"])
            sigma = self.parameters[effect_name]["sigma"]
            magnitude = self.parameters[effect_name]["magnitude"]
            # output_image = model.swirl_effect(self.image, center_point, sigma, magnitude)
            self.worker.process(Swirl_Effect, (self.image, center_point, sigma, magnitude))

        elif effect_name == "waves":
            amplitude = [self.parameters[effect_name]["amplitude"], self.parameters[effect_name]["amplitude"]]
            frequency = [self.parameters[effect_name]["frequency"], self.parameters[effect_name]["frequency"]]
            phase = [self.parameters[effect_name]["phase"], self.parameters[effect_name]["phase"]]
            # output_image = model.waves_effect(self.image, amplitude, frequency, phase)
            self.worker.process(Waves_Effect, (self.image, amplitude, frequency, phase))

        elif effect_name == "cylinder":
            self.worker.process(Cylinder, (self.image, self.parameters[effect_name]["angle"]))

        elif effect_name == "radial_blur":
            self.worker.process(RadialBlur_Effect, (self.image, self.parameters[effect_name]["sigma"]))
            # output_image = model.radial_blur_effect(self.image, sigma=self.parameters[effect_name]["sigma"])

        elif effect_name == "square_eye":
            center_point = (self.parameters[effect_name]["y"], self.parameters[effect_name]["x"])
            sigma = self.parameters[effect_name]["sigma"]
            p_value = self.parameters[effect_name]["p_value"]
            # output_image = model.square_eye_effect(self.image, center_point, sigma, p_value)
            self.worker.process(SquareEye_Effect, (self.image, center_point, sigma, p_value))

        elif effect_name == "median":
            self.worker.process(Median_Filter, (self.image, self.parameters[effect_name]["size"]))

        elif effect_name == "gaussian":
            self.worker.process(Gaussian_Filter, (self.image, self.parameters[effect_name]["radius"]))

        elif effect_name == "mean":
            self.worker.process(Mean_Filter, (self.image, self.parameters[effect_name]["size"]))

    @Slot(object)
    def update_image_view(self, output_image):
        self.preview_image = output_image.copy()

        if np.issubdtype(output_image.dtype, np.floating):
            output_image = (output_image * 255).astype(np.uint8)

        view_image = ImageQt.ImageQt(Image.fromarray(output_image))  # convert output_image to qimage
        pixmap = QPixmap.fromImage(view_image)
        self.scene = QGraphicsScene()
        self.scene.addPixmap(pixmap)
        self.window.graphicsView.setScene(self.scene)
        item = self.window.graphicsView.items()
        self.window.graphicsView.fitInView(item[0], Qt.KeepAspectRatio)

    def get_default_parameters(self):
        parameters = {"fisheye": {"x": 0, "y": 0, "sigma": 1.0},
                      "swirl": {"x": 0, "y": 0, "sigma": 0.01, "magnitude": 0},
                      "waves": {"amplitude": 0.1, "frequency": 0.1, "phase": 0},
                      "cylinder": {"angle": 0.0},
                      "radial_blur": {"sigma": 0.1},
                      "square_eye": {"x": 0, "y": 0, "sigma": 1.0, "p_value": 0.1},
                      "median": {"size": 3.0},
                      "gaussian": {"radius": 2.0},
                      "mean": {"size": 3.0}, }
        return parameters

    def disable_buttons(self, buttons):
        for button in buttons:
            button.setEnabled(False)

    def enable_buttons(self, buttons):
        for button in buttons:
            button.setEnabled(True)

    def set_parameter_limits(self):
        print("After loading an image, max min limits of slider and spinbox have been set")

        w = self.window
        self.set_limits([w.fisheye_x_slider, w.fisheye_y_slider, w.fisheye_sigma_slider,
                         w.swirl_x_slider, w.swirl_y_slider, w.swirl_sigma_slider, w.swirl_magnitude_slider,
                         w.waves_amplitude_slider, w.waves_freq_slider, w.waves_phase_slider,
                         w.cylinder_angle_slider,
                         w.radial_sigma_slider,
                         w.square_eye_x_slider, w.square_eye_y_slider, w.square_eye_sigma_slider,
                         w.square_eye_p_slider], "slider")

        self.set_limits([w.fisheye_x_spinbox, w.fisheye_y_spinbox, w.fisheye_sigma_spinbox,
                         w.swirl_x_spinbox, w.swirl_y_spinbox, w.swirl_sigma_spinbox, w.swirl_magnitude_spinbox,
                         w.waves_amplitude_spinbox, w.waves_freq_spinbox, w.waves_phase_spinbox,
                         w.cylinder_angle_spinbox,
                         w.radial_sigma_spinbox,
                         w.square_eye_x_spinbox, w.square_eye_y_spinbox, w.square_eye_sigma_spinbox,
                         w.square_eye_p_spinbox])

    def set_limits(self, input_widgets, kind=None):
        max_x, max_y = self.image.shape[1], self.image.shape[0]

        for widget in input_widgets:
            # print(widget.accessibleName())
            widget.setMinimum(0)
            if kind == "slider":
                widget.setTickInterval(1)

            if widget.accessibleName() == "x":
                widget.setMaximum(max_x)
            elif widget.accessibleName() == "y":
                widget.setMaximum(max_y)
            elif widget.accessibleName() == "amplitude" or widget.accessibleName() == "frequency" or widget.accessibleName() == "radial_sigma" or widget.accessibleName() == "p_value":
                widget.setMinimum(0.1)
            elif widget.accessibleName() == "swirl_sigma":
                widget.setMinimum(0.01)
            elif widget.accessibleName() == "cylinder_angle":
                widget.setMaximum(360.0)
            elif widget.accessibleName() == "fisheye_sigma" or widget.accessibleName() == "squareeye_sigma":
                widget.setMinimum(1.0)
                widget.setMaximum(500.0)
                if kind == "slider":
                    widget.setTickInterval(5)
                else:
                    widget.setSingleStep(5)

    @Slot()
    def load_button_event(self, graphicsView):
        w = self.window
        self.image_file_name = QFileDialog.getOpenFileName(self.window, "Open Image", ".",
                                                           "Image Files (*.png *.jpg *.bmp)")

        if self.image_file_name[0] != "":

            reader = QImageReader(self.image_file_name[0])
            reader.setAutoTransform(True)
            new_image = reader.read()
            if (new_image.isNull()):
                print("Image not found")

            self.scene = QGraphicsScene()
            pixmap = QPixmap.fromImage(new_image)

            self.scene.addPixmap(pixmap)
            graphicsView.setScene(self.scene)
            item = graphicsView.items()
            graphicsView.fitInView(item[0], Qt.KeepAspectRatio)

            if graphicsView.accessibleName() == "graphicsView":
                # self.image = self.image_read(self.image_file_name[0], pilmode="RGB") / 255.0
                self.image = Image.open(self.image_file_name[0])
                self.image = np.array(self.image) / 255.0
                if len(self.images_stack) == 1:
                    self.images_stack.pop()
                self.images_stack.append(("original image", self.image))

                # enable the buttons that were disabled in the beginning
                self.enable_buttons([w.save_button, w.reset_button,
                                     w.fisheye_apply_button, w.swirl_apply_button,
                                     w.waves_apply_button, w.cylinder_apply_button,
                                     w.radial_apply_button,
                                     w.square_eye_apply_button,
                                     w.gaussian_apply_button, w.median_apply_button,
                                     w.mean_apply_button])

                self.set_parameter_limits()

    @Slot()
    def save_button_event(self):
        file_name_to_save = \
            QFileDialog.getSaveFileName(self.window, "Open Image", ".", "Image Files (*.png *.jpg *.bmp)")[0]

        extension_list = ["png", "jpg", "jpeg"]
        if any(substring in file_name_to_save for substring in extension_list) == False:
            file_name_to_save = file_name_to_save + ".png"

        image_to_be_saved = self.image.copy()
        if np.issubdtype(image_to_be_saved.dtype, np.floating):
            image_to_be_saved = (self.image * 255).astype(np.uint8)

        self.image_write(image_to_be_saved, file_name_to_save)

    @Slot()
    def reset_button_event(self, image="main_image"):
        self.window.graphicsView.setScene(None)
        self.image = None
        self.disable_buttons([self.window.save_button, self.window.reset_button, self.window.undo_button,
                              self.window.fisheye_apply_button, self.window.swirl_apply_button,
                              self.window.waves_apply_button, self.window.cylinder_apply_button,
                              self.window.radial_apply_button,
                              self.window.square_eye_apply_button, self.window.gaussian_apply_button,
                              self.window.median_apply_button, self.window.mean_apply_button])

    def undo_button_event(self):
        if len(self.images_stack) > 1:
            self.images_stack.pop()
            self.image = self.images_stack[-1][1].copy()
            view_image = self.images_stack[-1][1].copy()  # To view image on the GraphicView

            if np.issubdtype(view_image.dtype, np.floating):
                view_image = (view_image * 255).astype(np.uint8)

            view_image = ImageQt.ImageQt(Image.fromarray(view_image))  # convert view_image to qimage
            pixmap = QPixmap.fromImage(view_image)
            self.scene = QGraphicsScene()
            self.scene.addPixmap(pixmap)
            self.window.graphicsView.setScene(self.scene)
            item = self.window.graphicsView.items()
            self.window.graphicsView.fitInView(item[0], Qt.KeepAspectRatio)

            #print("----------------------->",len(self.images_stack))
            if len(self.images_stack) == 1:
                self.disable_buttons([self.window.undo_button])

    @Slot()
    def dashboard_clicked_event(self, position, column):
        # get item name from the tree on the left bar
        item_name = position.text(column)
        if item_name in self.effects_to_tab_idx:
            self.window.tabWidget.setCurrentIndex(self.effects_to_tab_idx[item_name])
            self.current_tab_idx = self.effects_to_tab_idx[item_name]
            self.current_tab_name = item_name
            # enables the buttons and parameters if the effect is revisited after applying
            if self.image is not None and item_name != "About":
                self.tabs_to_apply_buttons_and_params[item_name]["button"].setEnabled(True)
                for widget in self.tabs_to_apply_buttons_and_params[item_name]["params"]:
                    widget.setEnabled(True)

    @Slot()
    def fisheye_effect_apply_button_event(self):
        self.image = self.preview_image.copy()
        self.images_stack.append(("fish eye effect", self.image))  # added to the stack

        for widget in self.fisheye_effect_parameters:
            widget.setEnabled(False)
        self.window.fisheye_apply_button.setEnabled(False)
        self.window.undo_button.setEnabled(True)

    @Slot()
    def swirl_effect_apply_button_event(self):
        self.image = self.preview_image.copy()
        self.images_stack.append(("swirl effect", self.image))  # added to the stack

        for widget in self.swirl_effect_parameters:
            widget.setEnabled(False)
        self.window.swirl_apply_button.setEnabled(False)
        self.window.undo_button.setEnabled(True)

    @Slot()
    def waves_effect_apply_button_event(self):
        self.image = self.preview_image.copy()
        self.images_stack.append(("waves effect", self.image))  # added to the stack

        for widget in self.waves_effect_parameters:
            widget.setEnabled(False)
        self.window.waves_apply_button.setEnabled(False)
        self.window.undo_button.setEnabled(True)

    @Slot()
    def cylinder_effect_apply_button_event(self):
        self.image = self.preview_image.copy()
        self.images_stack.append(("cylinder effect", self.image))  # added to the stack

        for widget in self.cylinder_effect_parameters:
            widget.setEnabled(False)
        self.window.cylinder_apply_button.setEnabled(False)
        self.window.undo_button.setEnabled(True)

    @Slot()
    def radial_blur_effect_apply_button_event(self):
        self.image = self.preview_image.copy()
        self.images_stack.append(("radial blur effect", self.image))  # added to the stack

        for widget in self.radial_blur_effect_parameters:
            widget.setEnabled(False)
        self.window.radial_apply_button.setEnabled(False)
        self.window.undo_button.setEnabled(True)

    @Slot()
    def square_eye_apply_button_event(self):
        self.image = self.preview_image.copy()
        self.images_stack.append(("square eye effect", self.image))  # added to the stack

        for widget in self.square_eye_effect_parameters:
            widget.setEnabled(False)
        self.window.square_eye_apply_button.setEnabled(False)
        self.window.undo_button.setEnabled(True)

    @Slot()
    def gaussian_blur_apply_button_event(self):
        self.image = self.preview_image.copy()
        self.images_stack.append(("gaussian blur effect", self.image))  # added to the stack

        for widget in self.gaussian_blur_parameters:
            widget.setEnabled(False)
        self.window.gaussian_apply_button.setEnabled(False)
        self.window.undo_button.setEnabled(True)

    @Slot()
    def median_blur_apply_button_event(self):
        self.image = self.preview_image.copy()
        self.images_stack.append(("median blur effect", self.image))  # added to the stack

        for widget in self.median_blur_parameters:
            widget.setEnabled(False)
        self.window.median_apply_button.setEnabled(False)
        self.window.undo_button.setEnabled(True)

    @Slot()
    def mean_blur_apply_button_event(self):
        self.image = self.preview_image.copy()
        self.images_stack.append(("mean blur effect", self.image))  # added to the stack

        for widget in self.mean_blur_parameters:
            widget.setEnabled(False)
        self.window.mean_apply_button.setEnabled(False)
        self.window.undo_button.setEnabled(True)

    def image_read(self, file_name, pilmode='RGB', arrtype=np.floating):
        return imageio.imread(file_name, pilmode=pilmode).astype(arrtype)

    def image_write(self, image, file_name, arrtype=np.uint8):
        imageio.imwrite(file_name, np.array(image).astype(arrtype))
