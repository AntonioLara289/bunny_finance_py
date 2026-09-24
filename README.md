<div align="center">

# Bunny Finance

**Sistema de Reconocimiento Facial para Control de Asistencia Financiera**

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![PySide6](https://img.shields.io/badge/PySide6-6-41CD52?style=for-the-badge&logo=qt&logoColor=white)](https://www.qt.io/)
[![InsightFace](https://img.shields.io/badge/InsightFace-ONNX-005C84?style=for-the-badge&logo=onnx&logoColor=white)](https://insightface.ai/)
[![License](https://img.shields.io/badge/License-MIT-FF6B6B?style=for-the-badge)](LICENSE)

---

<p align="center">
  <b>Bunny Finance</b> es un sistema de escritorio moderno que integra <b>reconocimiento facial</b> con inteligencia artificial, 
  <b>gestion de sesiones</b> y <b>control de asistencia</b> en una interfaz elegante y responsive.
</p>

</div>

---

## Caracteristicas

### Reconocimiento Facial con IA
- **InsightFace** con modelo `buffalo_l` para deteccion y reconocimiento de rostros en tiempo real
- Soporte para aceleracion **CUDA** (NVIDIA), **DirectML** (AMD/Intel) y fallback a CPU
- Matching por **distancia coseno** con umbral configurable
- Confirmaciones multiples para evitar falsos positivos

### Captura y Registro
- Camara de 3 posiciones: perfil izquierdo, frente, perfil derecho
- Almacenamiento de **encodings** en base de datos SQLite como vectores BLOB
- Vista previa en vivo con bounding boxes y tracking

### Proyeccion UMAP
- Visualizacion 2D de todos los encodings faciales registrados
- Colores unicos por persona con hover para identificar nombres
- Actualizacion en tiempo real al registrar nuevos rostros

### Gestion de Asistencia
- Registro automatico de entrada/salida por reconocimiento facial
- Tabla de asistencias con agrupacion por nombre (sin duplicados)
- Sesiones configurables con horarios personalizados

### Interfaz Moderna
- **Top bar** animada con degradados y efectos glassmorphism
- Menu lateral colapsable con iconos
- Multiples temas de estilo seleccionables desde Preferencias
- Ventanas responsivas que se adaptan al tamano de pantalla

### Modulo Financiero
- Calculos financieros integrados
- Consultas y reportes
- Historial de operaciones

---

## Arquitectura del Proyecto

```
bunny_finance_py/
├── main.py                     # Punto de entrada de la aplicacion
├── faces.db                    # Base de datos SQLite (encodings + personas)
├── database/
│   └── db_manager.py           # Gestor de base de datos financiera
├── ui/
│   ├── main_window.py          # Ventana principal con navegacion
│   ├── top_bar.py              # Barra superior animada
│   ├── animated_menu.py        # Menu lateral colapsable
│   ├── asistencia.py           # Vista de control de asistencia
│   ├── camaraInsightFaceWidget.py  # Widget de camara con InsightFace
│   ├── escaneoRostro.py        # Captura de rostros para registro
│   ├── PersonRegisterView.py   # Registro de nuevas personas
│   ├── insightFacesDemo.py     # Demo de reconocimiento en vivo
│   ├── visualizacionEncodings.py  # Proyeccion UMAP de encodings
│   ├── preferencias.py         # Configuracion de estilos
│   ├── sesiones.py             # Gestion de sesiones
│   ├── calculo.py              # Modulo de calculos financieros
│   ├── consultas.py            # Consultas y reportes
│   ├── Historial.py            # Historial de operaciones
│   ├── acerca.py               # Acerca de / creditos
│   ├── dialogs/                # Dialogos modales
│   └── workers/                # Workers para procesamiento asyncrono
├── styles/                     # Hojas de estilo QSS
├── models/                     # Modelos de InsightFace (buffalo_l)
├── requirements.txt            # Dependencias del proyecto
└── README.md
```

---

## Instalacion

### Prerequisitos
- **Python 3.11**
- **Git** (opcional)
- **NVIDIA GPU** con CUDA (recomendado) o CPU compatible

### Pasos

```bash
# 1. Clonar el repositorio
git clone https://github.com/tu-usuario/bunny_finance_py.git
cd bunny_finance_py

# 2. Crear entorno virtual
python -m venv venv
.\venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 3. Instalar dependencias
pip install -r requirements.txt
pip install -r requirements-insightface.txt

# 4. Ejecutar la aplicacion
python main.py
```

> **Nota:** Los modelos de InsightFace se descargan automaticamente en la primera ejecucion.

---

## Stack Tecnologico

| Tecnologia | Proposito |
|-----------|-----------|
| **Python 3.11** | Lenguaje principal |
| **PySide6** | GUI multiplataforma con Qt6 |
| **InsightFace** | Deteccion y reconocimiento facial con ONNX |
| **ONNX Runtime** | Motor de inferencia con soporte CUDA/DirectML |
| **UMAP** | Reduccion de dimensionalidad para visualizacion de encodings |
| **Matplotlib** | Graficos y visualizacion de datos |
| **SQLite3** | Base de datos ligera integrada |
| **OpenCV** | Captura y procesamiento de video |
| **NumPy** | Computacion numerica y algebra lineal |
| **QSS** | Hojas de estilo de Qt para la interfaz |

---

## Roadmap

- [x] Reconocimiento facial con InsightFace
- [x] Captura de rostros en 3 posiciones
- [x] Visualizacion UMAP de encodings
- [x] Gestion de sesiones y asistencias
- [x] Temas y estilos personalizables
- [ ] Exportacion de reportes PDF
- [ ] Soporte para multiples camaras simultaneas
- [ ] Dashboard con metricas en tiempo real

---

## Licencia

Este proyecto se desarrolla con fines academicos como trabajo de tesis.

---

<div align="center">
  <sub>Hecho con amor y Monster</sub>
</div>
