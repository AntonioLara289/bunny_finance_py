from PySide6.QtCore import QSettings, Signal, QObject
from PySide6.QtWidgets import QWidget

APP = "BunnyFinance"
ORG = "BunnyFinance"

DEFAULT_THEME = "styles/style.qss"

AVAILABLE_THEMES = (
    ("Aero Light  ·  clara, azul cielo", "styles/style.qss"),
    ("Aero Dark  ·  oscura, verde azulado", "styles/frutigerdark.qss"),
    ("Aero Green  ·  oscura, verde esmeralda", "styles/aerogreen.qss"),
    ("Aero Sunset  ·  oscura, cálida ámbar", "styles/aerosunset.qss"),
    ("Aero Frost  ·  oscura, azul hielo", "styles/aerofrost.qss"),
    ("Aero Organic  ·  oscura, verdes naturales", "styles/aeroorganic.qss"),
)

LIGHT_THEMES = frozenset({"styles/style.qss"})


def _normalize(theme_path):
    return str(theme_path or "").replace("\\", "/").lower().lstrip("./")


def is_light_theme(theme_path):
    """True si el tema indicado tiene fondo claro.

    Solo lo usan los elementos que no son widgets de Qt (por ejemplo el lienzo
    de Matplotlib), donde no se puede consultar la paleta real.
    """
    return _normalize(theme_path) in {_normalize(p) for p in LIGHT_THEMES}


def repolish(widget):
    """Vuelve a evaluar el QSS tras cambiar una propiedad dinamica.

    Qt solo recalcula el estilo de una propiedad cambiada con setProperty()
    cuando se Fuerza un re-polish del widget.
    """
    style = widget.style()
    style.unpolish(widget)
    style.polish(widget)
    widget.update()


def set_banner_state(label: QWidget, state: str, message: str = "") -> None:
    """Actualiza un QLabel#StatusBanner con uno de los estados semanticos.

    Estados validos: "info", "success", "warning", "error".
    """
    label.setProperty("state", state)
    if message:
        label.setText(message)
    repolish(label)


class AppSettings(QObject):
    settings_changed = Signal(str)

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        super().__init__()
        self._initialized = True
        self._settings = QSettings(ORG, APP)

    # --- helpers ---
    def _get(self, key, default):
        return self._settings.value(key, default)

    def _set(self, key, value):
        self._settings.setValue(key, value)

    # === Tema visual ===
    @property
    def theme_path(self):
        return self._get("theme/path", DEFAULT_THEME) or DEFAULT_THEME

    @theme_path.setter
    def theme_path(self, value):
        self._set("theme/path", value)

    # === Idioma ===
    @property
    def language(self):
        return self._get("ui/language", "Español")

    @language.setter
    def language(self, value):
        self._set("ui/language", value)

    # === Reconocimiento facial ===
    @property
    def similarity_threshold(self):
        return float(self._get("face/similarity_threshold", 0.5))

    @similarity_threshold.setter
    def similarity_threshold(self, value):
        self._set("face/similarity_threshold", value)

    @property
    def confirmations_needed(self):
        return int(self._get("face/confirmations_needed", 2))

    @confirmations_needed.setter
    def confirmations_needed(self, value):
        self._set("face/confirmations_needed", value)

    @property
    def detection_interval(self):
        return int(self._get("face/detection_interval", 5))

    @detection_interval.setter
    def detection_interval(self, value):
        self._set("face/detection_interval", value)

    @property
    def camera_resolution(self):
        return self._get("camera/resolution", "640x480")

    @camera_resolution.setter
    def camera_resolution(self, value):
        self._set("camera/resolution", value)

    @property
    def camera_index(self):
        return int(self._get("camera/index", 0))

    @camera_index.setter
    def camera_index(self, value):
        self._set("camera/index", value)

    # === Asistencia ===
    @property
    def required_seconds(self):
        return float(self._get("attendance/required_seconds", 2.0))

    @required_seconds.setter
    def required_seconds(self, value):
        self._set("attendance/required_seconds", value)

    @property
    def ui_update_interval(self):
        return float(self._get("attendance/ui_update_interval", 0.3))

    @ui_update_interval.setter
    def ui_update_interval(self, value):
        self._set("attendance/ui_update_interval", value)

    # === UMAP ===
    @property
    def umap_n_neighbors(self):
        return int(self._get("umap/n_neighbors", 5))

    @umap_n_neighbors.setter
    def umap_n_neighbors(self, value):
        self._set("umap/n_neighbors", value)

    @property
    def umap_min_dist(self):
        return float(self._get("umap/min_dist", 0.1))

    @umap_min_dist.setter
    def umap_min_dist(self, value):
        self._set("umap/min_dist", value)

    # === Método para restaurar defaults ===
    def restore_defaults(self):
        self._settings.clear()
        self.settings_changed.emit("all")
