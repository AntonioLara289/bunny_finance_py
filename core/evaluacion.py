"""Evaluacion offline de la exactitud del reconocimiento facial.

Sin dataset etiquetado externo, la exactitud se mide sobre los encodings ya
registrados en faces.db (persons + encodings). Se usan dos protocolos estandar:

1. Verificacion (1:1): se forman todos los pares de encodings. Los pares con el
   mismo person_id son "genuinos"; los de distinta persona, "impostores". Con
   las similitudes coseno se calcula la curva ROC, AUC, EER y, en el umbral
   configurado, FAR/FRR/accuracy/precision/recall.

2. Identificacion (1:N, leave-one-out): cada encoding se reconoce contra todos
   los demas (excluyendose a si mismo) y se mide la exactitud top-1 junto con
   los pares que mas se confunden.

Nota metodologica: las muestras de una misma persona no son independientes
(suelen venir de la misma sesion), por lo que los resultados son una estimacion
de laboratorio, no un benchmark con particion train/test.
"""

import csv
import json
import os
import sqlite3
import time

import numpy as np


def cargar_embeddings(db_path):
    """Carga (X, person_ids, nombres) desde faces.db."""
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT persons.id, persons.name, encodings.embedding
            FROM encodings
            JOIN persons ON persons.id = encodings.person_id
            """
        )
        filas = cur.fetchall()
    finally:
        conn.close()

    vectores = []
    ids = []
    nombres = []
    for person_id, nombre, blob in filas:
        emb = np.frombuffer(blob, dtype=np.float32)
        vectores.append(emb)
        ids.append(int(person_id))
        nombres.append(nombre)

    if vectores:
        X = np.vstack(vectores)
    else:
        X = np.zeros((0, 0), dtype=np.float32)

    return X, np.array(ids, dtype=np.int64), np.array(nombres, dtype=object)


def _similitudes_coseno(X, tam_bloque=2000):
    """Matriz de similitud coseno NxN calculada por bloques (memoria acotada)."""
    normas = np.linalg.norm(X, axis=1, keepdims=True)
    Xn = X / (normas + 1e-12)
    n = Xn.shape[0]
    S = np.empty((n, n), dtype=np.float32)
    for i in range(0, n, tam_bloque):
        S[i:i + tam_bloque] = Xn[i:i + tam_bloque] @ Xn.T
    return S


def _roc_curva(y_true, y_score):
    """Curva ROC en orden descendente de umbral (sin sklearn).

    Devuelve (fpr, tpr, umbrales) con el punto final (1, 1) agregado.
    """
    orden = np.argsort(-y_score, kind="mergesort")
    scores = y_score[orden]
    etiquetas = y_true[orden].astype(np.float64)

    positivos = float(etiquetas.sum())
    negativos = float(len(etiquetas) - etiquetas.sum())
    if positivos == 0 or negativos == 0:
        raise ValueError("Se necesitan positivos y negativos para la curva ROC.")

    tp = np.cumsum(etiquetas)
    fp = np.cumsum(1.0 - etiquetas)
    tpr = tp / positivos
    fpr = fp / negativos

    fpr = np.concatenate([fpr, [1.0]])
    tpr = np.concatenate([tpr, [1.0]])
    umbrales = np.concatenate([scores, [np.inf]])
    return fpr, tpr, umbrales


def _auc_trap(fpr, tpr):
    """Area bajo la curva con la regla de los trapecios (fpr creciente)."""
    return float(np.sum(np.diff(fpr) * (tpr[:-1] + tpr[1:]) / 2.0))


def evaluar_verificacion(X, person_ids, umbral):
    """ROC/AUC/EER y metricas en el umbral operativo (1:1)."""
    S = _similitudes_coseno(X)
    n = S.shape[0]
    iu = np.triu_indices(n, k=1)
    sims = S[iu].astype(np.float64)
    misma_persona = person_ids[iu[0]] == person_ids[iu[1]]

    genuinos = sims[misma_persona]
    impostores = sims[~misma_persona]

    if len(genuinos) == 0 or len(impostores) == 0:
        return {
            "error": "Se necesitan al menos 2 personas con mas de un encoding para "
                     "evaluar verificacion (pares genuinos e impostores).",
            "num_genuinos": int(len(genuinos)),
            "num_impostores": int(len(impostores)),
        }

    y_true = np.concatenate([np.ones_like(genuinos), np.zeros_like(impostores)])
    y_score = np.concatenate([genuinos, impostores])

    fpr, tpr, umbrales = _roc_curva(y_true, y_score)
    auc_valor = _auc_trap(fpr, tpr)

    fnr = 1.0 - tpr
    idx_eer = int(np.nanargmin(np.abs(fpr - fnr)))
    eer = float((fpr[idx_eer] + fnr[idx_eer]) / 2.0)
    umbral_eer = float(umbrales[idx_eer])

    idx_opt = int(np.argmin((fpr + fnr) / 2.0))
    umbral_optimo = float(umbrales[idx_opt])

    tp = int(np.sum(genuinos >= umbral))
    fn = int(np.sum(genuinos < umbral))
    fp = int(np.sum(impostores >= umbral))
    tn = int(np.sum(impostores < umbral))
    far = fp / (fp + tn) if (fp + tn) else 0.0
    frr = fn / (fn + tp) if (fn + tp) else 0.0
    accuracy = (tp + tn) / len(y_true) if len(y_true) else 0.0
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0

    return {
        "auc": auc_valor,
        "eer": eer,
        "umbral_eer": umbral_eer,
        "umbral_optimo": umbral_optimo,
        "umbral_operativo": float(umbral),
        "far": float(far),
        "frr": float(frr),
        "accuracy": float(accuracy),
        "precision": float(precision),
        "recall": float(recall),
        "tp": tp,
        "fn": fn,
        "fp": fp,
        "tn": tn,
        "num_genuinos": int(len(genuinos)),
        "num_impostores": int(len(impostores)),
        "sim_genuinos_media": float(np.mean(genuinos)),
        "sim_genuinos_min": float(np.min(genuinos)),
        "sim_genuinos_max": float(np.max(genuinos)),
        "sim_impostores_media": float(np.mean(impostores)),
        "sim_impostores_min": float(np.min(impostores)),
        "sim_impostores_max": float(np.max(impostores)),
        # arrays para graficas / exportacion
        "roc_fpr": fpr,
        "roc_tpr": tpr,
        "roc_umbrales": umbrales,
        "genuinos": genuinos,
        "impostores": impostores,
    }


def evaluar_identificacion(X, person_ids, max_confusiones=15):
    """Exactitud top-1 leave-one-out (1:N) y pares mas confundidos."""
    S = _similitudes_coseno(X)
    n = S.shape[0]
    if n < 2:
        return {"error": "Se necesitan al menos 2 encodings para identificacion."}

    np.fill_diagonal(S, -np.inf)
    pred_idx = np.argmax(S, axis=1)
    pred_ids = person_ids[pred_idx]
    correctos = pred_ids == person_ids
    exactitud = float(np.mean(correctos))

    confusiones = {}
    for i in np.where(~correctos)[0]:
        clave = (int(person_ids[i]), int(pred_ids[i]))
        if clave not in confusiones:
            confusiones[clave] = {"count": 0, "similitud_max": 0.0}
        confusiones[clave]["count"] += 1
        confusiones[clave]["similitud_max"] = max(
            confusiones[clave]["similitud_max"], float(S[i, pred_idx[i]])
        )

    lista_confusiones = sorted(
        (
            {
                "real_id": real,
                "predicho_id": pred,
                "count": datos["count"],
                "similitud_max": datos["similitud_max"],
            }
            for (real, pred), datos in confusiones.items()
        ),
        key=lambda d: d["count"],
        reverse=True,
    )[:max_confusiones]

    return {
        "exactitud_top1": exactitud,
        "correctos": int(np.sum(correctos)),
        "total": int(n),
        "confusiones": lista_confusiones,
    }


def evaluar_base(db_path, umbral):
    """Ejecuta ambos protocolos y devuelve un resultado combinado."""
    X, ids, nombres = cargar_embeddings(db_path)
    personas = sorted(set(ids.tolist()))
    resultado = {
        "db_path": db_path,
        "umbral_configurado": float(umbral),
        "num_encodings": int(X.shape[0]),
        "num_personas": len(personas),
        "num_muestras_por_persona": {},
        "id_a_nombre": {int(i): str(n) for i, n in zip(ids, nombres)},
    }
    for pid in personas:
        resultado["num_muestras_por_persona"][str(pid)] = int(np.sum(ids == pid))

    if X.shape[0] < 2:
        resultado["error"] = "No hay suficientes encodings en faces.db para evaluar."
        return resultado

    resultado["verificacion"] = evaluar_verificacion(X, ids, umbral)
    resultado["identificacion"] = evaluar_identificacion(X, ids)
    return resultado


def _json_safe(obj, max_lista=600):
    """Convierte numpy a tipos JSON, recortando arrays largos."""
    if isinstance(obj, dict):
        return {k: _json_safe(v, max_lista) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_json_safe(v, max_lista) for v in obj]
    if isinstance(obj, np.ndarray):
        if obj.ndim == 0:
            return float(obj)
        datos = obj.tolist()
        if len(datos) > max_lista:
            paso = max(1, len(datos) // max_lista)
            datos = datos[::paso]
        return [_json_safe(v, max_lista) for v in datos]
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    return obj


def _filas_metricas(resultado):
    """Aplana las metricas escalares para la tabla/CSV."""
    filas = [
        ("num_encodings", resultado.get("num_encodings")),
        ("num_personas", resultado.get("num_personas")),
        ("umbral_configurado", resultado.get("umbral_configurado")),
    ]
    ver = resultado.get("verificacion", {}) or {}
    etiquetas = [
        ("auc", "AUC"),
        ("eer", "EER"),
        ("umbral_eer", "Umbral en EER"),
        ("umbral_optimo", "Umbral optimo (min error)"),
        ("far", "FAR (umbral operativo)"),
        ("frr", "FRR (umbral operativo)"),
        ("accuracy", "Accuracy (umbral operativo)"),
        ("precision", "Precision"),
        ("recall", "Recall"),
        ("tp", "TP"),
        ("fn", "FN"),
        ("fp", "FP"),
        ("tn", "TN"),
        ("num_genuinos", "Pares genuinos"),
        ("num_impostores", "Pares impostores"),
        ("sim_genuinos_media", "Similitud genuinos (media)"),
        ("sim_impostores_media", "Similitud impostores (media)"),
    ]
    for clave, etiqueta in etiquetas:
        if clave in ver:
            filas.append((etiqueta, ver[clave]))
    ide = resultado.get("identificacion", {}) or {}
    if "exactitud_top1" in ide:
        filas.append(("Exactitud identificacion LOO top-1", ide["exactitud_top1"]))
        filas.append(("Aciertos identificacion", ide.get("correctos")))
        filas.append(("Total de muestras", ide.get("total")))
    return filas


def exportar_reporte(resultado, directorio, prefijo="monitoreo"):
    """Guarda CSV + JSON del resultado. Devuelve (ruta_csv, ruta_json)."""
    os.makedirs(directorio, exist_ok=True)
    marca = time.strftime("%Y%m%d_%H%M%S")

    ruta_csv = os.path.join(directorio, "{}_{}_metricas.csv".format(prefijo, marca))
    with open(ruta_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["metrica", "valor"])
        for etiqueta, valor in _filas_metricas(resultado):
            writer.writerow([etiqueta, valor])

    ver = resultado.get("verificacion", {}) or {}
    if "roc_fpr" in ver:
        ruta_roc = os.path.join(directorio, "{}_{}_roc.csv".format(prefijo, marca))
        with open(ruta_roc, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["fpr", "tpr", "umbral"])
            for fpr, tpr, u in zip(ver["roc_fpr"], ver["roc_tpr"], ver["roc_umbrales"]):
                writer.writerow([fpr, tpr, u])

    ruta_json = os.path.join(directorio, "{}_{}.json".format(prefijo, marca))
    with open(ruta_json, "w", encoding="utf-8") as f:
        json.dump(_json_safe(resultado), f, ensure_ascii=False, indent=2)

    return ruta_csv, ruta_json
