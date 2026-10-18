"""Metricas exactas de rendimiento y reconocimiento para la tesis.

Este modulo no depende de Qt: solo acumula numeros. Las vistas (por ejemplo la
ventana de monitoreo) lo consultan con snapshot() y las graficas se dibujan
aparte.

- MetricsCollector: singleton que registra por frame la latencia de inferencia,
  el numero de caras y las similitudes observadas. Pensado para llamarse desde
  CameraInsightFaceWidget.update_frame().
- SystemSampler: usa psutil para medir CPU/RAM del proceso y del sistema, y
  nvidia-smi para GPU cuando esta disponible.
"""

import subprocess
import threading
import time
from collections import deque

import numpy as np

try:
    import psutil
except Exception:  # pragma: no cover - psutil es dependencia declarada
    psutil = None


class MetricsCollector:
    """Recolector global de metricas del pipeline de reconocimiento.

    Singleton: la camara escribe y cualquier vista lee la misma instancia.
    Es seguro usarlo desde mas de un hilo (lock interno).
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_state()
        return cls._instance

    def _init_state(self):
        self._lock = threading.Lock()
        self._frame_ts = deque(maxlen=1200)    # timestamps (perf_counter) de frames
        self._latencies = deque(maxlen=1200)   # ms de inferencia en frames con deteccion
        self._n_faces = deque(maxlen=1200)     # caras detectadas por frame
        self._best_sims = deque(maxlen=5000)   # similitudes observadas (todas las caras)
        self.reset()

    # ------------------------------------------------------------------ registro
    def reset(self):
        with self._lock:
            self._frame_ts.clear()
            self._latencies.clear()
            self._n_faces.clear()
            self._best_sims.clear()
            self.total_frames = 0
            self.total_detecciones = 0   # frames con al menos una cara
            self.total_caras = 0
            self.total_matches = 0       # caras con similitud >= umbral
            self.total_desconocidos = 0  # caras con similitud < umbral
            self.session_start = time.perf_counter()

    def register_frame(self, latency_ms=None, n_faces=0, best_sims=None,
                       matches=0, unknowns=0):
        """Registra un frame procesado.

        latency_ms: tiempo de inferencia (app.get) solo en frames de deteccion.
        n_faces: caras detectadas en el frame.
        best_sims: lista de similitudes (una por cara) contra la base de datos.
        matches / unknowns: cuantas caras pasaron/no pasaron el umbral.
        """
        ahora = time.perf_counter()
        with self._lock:
            self._frame_ts.append(ahora)
            self._n_faces.append(int(n_faces))
            self.total_frames += 1
            self.total_caras += int(n_faces)
            if n_faces:
                self.total_detecciones += 1
            if latency_ms is not None:
                self._latencies.append(float(latency_ms))
            if best_sims:
                for s in best_sims:
                    self._best_sims.append(float(s))
            self.total_matches += int(matches)
            self.total_desconocidos += int(unknowns)

    # ------------------------------------------------------------------ lectura
    def _fps_ventana(self, ventana_s=2.0, ts=None):
        if ts is None:
            with self._lock:
                ts = list(self._frame_ts)
        if len(ts) < 2:
            return 0.0
        ahora = ts[-1]
        recientes = [t for t in ts if ahora - t <= ventana_s]
        if len(recientes) < 2:
            return 0.0
        duracion = recientes[-1] - recientes[0]
        if duracion <= 0:
            return 0.0
        return (len(recientes) - 1) / duracion

    def scores(self):
        """Copia de todas las similitudes observadas (para histogramas)."""
        with self._lock:
            return np.array(self._best_sims, dtype=np.float64)

    def snapshot(self):
        """Resumen estadistico de la sesion actual de medicion."""
        with self._lock:
            ts = list(self._frame_ts)
            lat = np.array(self._latencies, dtype=np.float64)
            sims = np.array(self._best_sims, dtype=np.float64)
            totales = {
                "frames": self.total_frames,
                "detecciones": self.total_detecciones,
                "caras": self.total_caras,
                "matches": self.total_matches,
                "desconocidos": self.total_desconocidos,
                "inicio": self.session_start,
            }

        duracion = max(0.0, time.perf_counter() - totales["inicio"])
        datos = {
            "fps_actual": self._fps_ventana(ts=ts),
            "fps_promedio": (totales["frames"] / duracion) if duracion > 0 else 0.0,
            "duracion_s": duracion,
            "frames": totales["frames"],
            "detecciones": totales["detecciones"],
            "caras": totales["caras"],
            "matches": totales["matches"],
            "desconocidos": totales["desconocidos"],
        }

        caras_vistas = totales["matches"] + totales["desconocidos"]
        datos["tasa_match"] = (totales["matches"] / caras_vistas) if caras_vistas else 0.0
        datos["caras_por_frame"] = (
            totales["caras"] / totales["frames"] if totales["frames"] else 0.0
        )

        if len(lat):
            datos.update({
                "latencia_media_ms": float(np.mean(lat)),
                "latencia_mediana_ms": float(np.median(lat)),
                "latencia_p95_ms": float(np.percentile(lat, 95)),
                "latencia_min_ms": float(np.min(lat)),
                "latencia_max_ms": float(np.max(lat)),
                "latencia_std_ms": float(np.std(lat)),
                "muestras_latencia": int(len(lat)),
            })
        else:
            datos.update({
                "latencia_media_ms": None,
                "latencia_mediana_ms": None,
                "latencia_p95_ms": None,
                "latencia_min_ms": None,
                "latencia_max_ms": None,
                "latencia_std_ms": None,
                "muestras_latencia": 0,
            })

        if len(sims):
            datos.update({
                "sim_media": float(np.mean(sims)),
                "sim_mediana": float(np.median(sims)),
                "sim_p95": float(np.percentile(sims, 95)),
                "sim_min": float(np.min(sims)),
                "sim_max": float(np.max(sims)),
                "sim_std": float(np.std(sims)),
                "muestras_sim": int(len(sims)),
            })
        else:
            datos.update({
                "sim_media": None,
                "sim_mediana": None,
                "sim_p95": None,
                "sim_min": None,
                "sim_max": None,
                "sim_std": None,
                "muestras_sim": 0,
            })

        return datos


class SystemSampler:
    """Muestreo de recursos del sistema (CPU/RAM/GPU).

    cpu_percent(None) no bloquea: devuelve el uso desde la ultima llamada, por
    eso conviene instanciarlo una vez y llamar a sample() periodicamente (1 s).
    """

    def __init__(self):
        self._proc = psutil.Process() if psutil is not None else None
        self._gpu_disponible = None  # se detecta de forma perezosa
        if self._proc is not None:
            # Primera llamada: fija la linea base para cpu_percent(None).
            self._proc.cpu_percent(None)
            if psutil is not None:
                psutil.cpu_percent(None)

    @staticmethod
    def _query_gpu():
        cmd = [
            "nvidia-smi",
            "--query-gpu=utilization.gpu,memory.used,memory.total",
            "--format=csv,noheader,nounits",
        ]
        salida = subprocess.run(
            cmd, capture_output=True, text=True, timeout=2, check=False
        )
        if salida.returncode != 0 or not salida.stdout.strip():
            return None
        linea = salida.stdout.strip().splitlines()[0]
        partes = [p.strip() for p in linea.split(",")]
        if len(partes) < 3:
            return None
        return {
            "gpu_uso_pct": float(partes[0]),
            "gpu_mem_used_mb": float(partes[1]),
            "gpu_mem_total_mb": float(partes[2]),
        }

    def sample(self):
        """Devuelve un dict con las metricas del sistema en este instante."""
        datos = {
            "cpu_proceso_pct": None,
            "cpu_sistema_pct": None,
            "ram_proceso_mb": None,
            "ram_sistema_pct": None,
            "gpu_uso_pct": None,
            "gpu_mem_used_mb": None,
            "gpu_mem_total_mb": None,
        }
        if psutil is None:
            return datos

        try:
            datos["cpu_sistema_pct"] = float(psutil.cpu_percent(None))
        except Exception:
            pass
        try:
            datos["ram_sistema_pct"] = float(psutil.virtual_memory().percent)
        except Exception:
            pass
        if self._proc is not None:
            try:
                datos["cpu_proceso_pct"] = float(self._proc.cpu_percent(None))
            except Exception:
                pass
            try:
                datos["ram_proceso_mb"] = self._proc.memory_info().rss / (1024.0 * 1024.0)
            except Exception:
                pass

        if self._gpu_disponible is None:
            # Deteccion perezosa: si nvidia-smi no existe, no volver a intentarlo.
            try:
                self._gpu_disponible = self._query_gpu() is not None
            except Exception:
                self._gpu_disponible = False
        if self._gpu_disponible:
            try:
                gpu = self._query_gpu()
                if gpu:
                    datos.update(gpu)
            except Exception:
                pass

        return datos


def contexto_inferencia():
    """Contexto del motor de reconocimiento (para encabezados de reporte)."""
    try:
        import onnxruntime as ort

        providers = ort.get_available_providers()
        if "CUDAExecutionProvider" in providers:
            proveedor = "CUDA (GPU NVIDIA)"
        elif "DmlExecutionProvider" in providers:
            proveedor = "DirectML (GPU)"
        else:
            proveedor = "CPU"
    except Exception:
        proveedor = "desconocido"

    return {
        "proveedor": proveedor,
        "modelo": "insightface buffalo_l",
        "fecha": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
