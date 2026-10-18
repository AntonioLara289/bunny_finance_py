"""Catalogo de comandos de la consola.

Cada comando declara su sintaxis y recibe un :class:`Invocacion` con los
argumentos ya separados en posicionales y opciones. Ningun handler importa Qt:
toda la logica viene de :mod:`core`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from core.services import ErrorServicio
from cli.console import Consola


# --------------------------------------------------------------------------- #
# Infrastructure de invocacion
# --------------------------------------------------------------------------- #


def separar_opciones(argumentos: list[str]) -> tuple[list[str], dict[str, str | bool]]:
    """Parte ``["a", "--si", "--salida=x.xlsx"]`` en posicionales y opciones.

    Los nombres de opcion se normalizan sin guiones: ``--conservar-asistencias``
    queda como ``conservar-asistencias``.
    """
    posicionales: list[str] = []
    opciones: dict[str, str | bool] = {}

    indice = 0
    while indice < len(argumentos):
        argumento = argumentos[indice]
        if argumento.startswith("--") and len(argumento) > 2:
            cuerpo = argumento[2:]
            if "=" in cuerpo:
                nombre, _, valor = cuerpo.partition("=")
                opciones[nombre] = valor
            elif indice + 1 < len(argumentos) and not argumentos[indice + 1].startswith("--"):
                opciones[cuerpo] = argumentos[indice + 1]
                indice += 1
            else:
                opciones[cuerpo] = True
        elif argumento == "--":
            posicionales.extend(argumentos[indice + 1 :])
            break
        else:
            posicionales.append(argumento)
        indice += 1

    return posicionales, opciones


@dataclass
class Invocacion:
    core: object
    consola: Consola
    comando: "Comando"
    pos: list[str]
    opc: dict[str, str | bool] = field(default_factory=dict)

    def exactamente(self, cantidad: int) -> list[str]:
        if len(self.pos) != cantidad:
            raise ErrorServicio(
                f"{self.comando.nombre} espera {cantidad} argumento(s) "
                f"y recibio {len(self.pos)}."
                + self._pista()
                + f" Uso: {self.comando.uso}"
            )
        return list(self.pos)

    def entre(self, minimo: int, maximo: int) -> list[str]:
        if not minimo <= len(self.pos) <= maximo:
            esperado = f"{minimo}" if minimo == maximo else f"entre {minimo} y {maximo}"
            raise ErrorServicio(
                f"{self.comando.nombre} espera {esperado} argumento(s) "
                f"y recibio {len(self.pos)}."
                + self._pista()
                + f" Uso: {self.comando.uso}"
            )
        return list(self.pos)

    def _pista(self) -> str:
        """Si sobra un argumento y el comando pide un nombre, casi siempre es
        que el nombre con espacios no va entrecomillado."""
        if len(self.pos) > 1 and "<nombre" in self.comando.uso:
            return " Los nombres con espacios van entrecomillados."
        return ""

    def bandera(self, nombre: str) -> bool:
        return bool(self.opc.get(nombre, False))

    def texto(self, nombre: str, defecto: str | None = None) -> str:
        """Valor de una opcion. Si se escribio sin valor, lo dice claro."""
        valor = self.opc.get(nombre, defecto)
        if valor is True:
            raise ErrorServicio(f"La opcion --{nombre} necesita un valor.")
        return str(valor) if valor is not None else ""


@dataclass(frozen=True)
class Comando:
    nombre: str
    grupo: str
    resumen: str
    uso: str
    ejecutar: Callable[[Invocacion], int]
    alias: tuple[str, ...] = ()
    detalle: str = ""


REGISTRO: dict[str, Comando] = {}
ORDEN: list[Comando] = []


def registrar(
    nombre: str,
    grupo: str,
    resumen: str,
    uso: str,
    alias: tuple[str, ...] = (),
    detalle: str = "",
) -> Callable[[Callable[[Invocacion], int]], Callable[[Invocacion], int]]:
    def envoltorio(funcion: Callable[[Invocacion], int]) -> Callable[[Invocacion], int]:
        comando = Comando(
            nombre=nombre,
            grupo=grupo,
            resumen=resumen,
            uso=uso,
            ejecutar=funcion,
            alias=alias,
            detalle=detalle,
        )
        REGISTRO[nombre] = comando
        for nombre_alias in alias:
            REGISTRO[nombre_alias] = comando
        ORDEN.append(comando)
        return funcion

    return envoltorio


def buscar(nombre: str) -> Comando | None:
    return REGISTRO.get(str(nombre or "").strip().lower())


def buscar_parecido(texto: str) -> list[Comando]:
    """Comandos cuyo nombre se parece a ``texto`` (para sugerir al fallar)."""
    from difflib import get_close_matches

    nombres = [c.nombre for c in ORDEN]
    return [REGISTRO[n] for n in get_close_matches(texto, nombres, n=3, cutoff=0.5)]


# --------------------------------------------------------------------------- #
# Ayuda
# --------------------------------------------------------------------------- #

GRUPOS = (
    "General",
    "Personas",
    "Rostros",
    "Sesiones",
    "Asistencia",
    "Ajustes",
)


def listar_comandos(consola: Consola) -> None:
    for grupo in GRUPOS:
        comandos = [c for c in ORDEN if c.grupo == grupo]
        if not comandos:
            continue
        consola.titulo(f"{grupo}")
        for comando in comandos:
            alias = f"  (alias: {', '.join(comando.alias)})" if comando.alias else ""
            consola.escribir(f"  {comando.nombre:<22} {comando.resumen}{alias}")
        consola.escribir("")


@registrar(
    "ayuda",
    grupo="General",
    resumen="Muestra esta ayuda, o el detalle de un comando",
    uso="ayuda [comando]",
    alias=("help", "?"),
)
def cmd_ayuda(inv: Invocacion) -> int:
    if inv.pos:
        comando = buscar(inv.pos[0])
        if comando is None:
            inv.consola.error(f"Comando desconocido: {inv.pos[0]}")
            _sugerir(inv, inv.pos[0])
            return 1
        inv.consola.titulo(comando.nombre)
        inv.consola.escribir(f"  {comando.resumen}")
        inv.consola.escribir(f"  Uso:  {comando.uso}")
        if comando.detalle:
            inv.consola.escribir("")
            for linea in comando.detalle.splitlines():
                inv.consola.escribir(f"  {linea}")
        if comando.alias:
            inv.consola.escribir(f"  Alias: {', '.join(comando.alias)}")
        return 0

    listar_comandos(inv.consola)
    inv.consola.escribir("Ejemplos:")
    inv.consola.escribir('  py main.py -nogui sesiones')
    inv.consola.escribir('  py main.py -nogui "ayuda asistir"')
    return 0


def _sugerir(inv: Invocacion, texto: str) -> None:
    parecidos = buscar_parecido(texto)
    if parecidos:
        inv.consola.aviso(
            "Quizas quisiste decir: " + ", ".join(c.nombre for c in parecidos)
        )


# --------------------------------------------------------------------------- #
# General
# --------------------------------------------------------------------------- #


@registrar(
    "diagnostico",
    grupo="General",
    resumen="Estado de las bases de datos y discrepancias entre ellas",
    uso="diagnostico",
    detalle=(
        "Compara el registro de personas (bunny_detect_v2.db) con los rostros\n"
        "de faces.db. Avisa de nombres que solo estan en una de las dos bases,\n"
        "de nombres duplicados y de asistencias repetidas."
    ),
)
def cmd_diagnostico(inv: Invocacion) -> int:
    informe = inv.core.diagnostico()  # type: ignore[attr-defined]
    c = inv.consola

    c.titulo("Resumen")
    c.tabla(
        ["Dato", "Cantidad"],
        [
            ["Personas en el registro", informe.personas_registradas],
            ["Personas activadas", informe.personas_activas],
            ["Rostros registrados", informe.rostros],
            ["Muestras de embedding", informe.muestras],
            ["Sesiones", informe.sesiones],
            ["Asistencias guardadas", informe.asistencias],
        ],
    )

    c.escribir()
    c.titulo("Rutas")
    c.escribir(f"  registro : {informe.ruta_datos}")
    c.escribir(f"  rostros  : {informe.ruta_rostros}")

    problemas = False

    if informe.solo_en_rostros:
        problemas = True
        c.escribir()
        c.titulo("Solo en faces.db (sin registro de persona)")
        c.aviso(", ".join(informe.solo_en_rostros))

    if informe.solo_en_registro:
        problemas = True
        c.escribir()
        c.titulo("Solo en el registro (sin rostro)")
        c.aviso(", ".join(informe.solo_en_registro))

    if informe.nombres_duplicados:
        problemas = True
        c.escribir()
        c.titulo("Nombres repetidos en faces.db")
        for nombre, veces in informe.nombres_duplicados.items():
            c.aviso(f"{nombre} aparece {veces} veces (rostros {[r.id for r in inv.core.rostros.buscar_por_nombre(nombre)]})")

    if informe.asistencias_duplicadas:
        problemas = True
        c.escribir()
        c.titulo("Asistencias repetidas")
        c.aviso(
            "La misma persona guardada varias veces en la misma sesion. "
            "Usar 'limpiar-asistencias <sesion>' para dejar una sola fila."
        )
        for id_persona, id_sesion, veces in informe.asistencias_duplicadas:
            persona = inv.core.personas.obtener(id_persona)  # type: ignore[attr-defined]
            sesion = inv.core.sesiones.obtener(id_sesion)  # type: ignore[attr-defined]
            c.escribir(
                f"  - {persona.nombre if persona else f'persona {id_persona}'}"
                f" / {sesion.nombre if sesion else f'sesion {id_sesion}'}: {veces} filas"
            )

    if not problemas:
        c.escribir()
        c.ok("Sin discrepancias entre las bases de datos.")
    return 0


@registrar(
    "limpiar",
    grupo="General",
    resumen="Limpia la pantalla",
    uso="limpiar",
    alias=("cls",),
)
def cmd_limpiar(inv: Invocacion) -> int:
    inv.consola.limpiar_pantalla()
    return 0


# --------------------------------------------------------------------------- #
# Personas
# --------------------------------------------------------------------------- #


@registrar(
    "personas",
    grupo="Personas",
    resumen="Lista el registro de personas",
    uso="personas [filtro] [--estatus activado|desactivado|pendiente]",
    detalle=(
        "Sin argumentos lista todas, incluidas las desactivadas.\n"
        "El filtro busca por nombre, sin distinguir mayusculas."
    ),
)
def cmd_personas(inv: Invocacion) -> int:
    filtro = inv.pos[0] if inv.pos else ""
    estatus = inv.texto("estatus") or None
    personas = inv.core.personas.listar(texto=filtro, estatus=estatus)  # type: ignore[attr-defined]

    inv.consola.tabla(
        ["ID", "Nombre", "Estatus", "Registrado"],
        [[p.id, p.nombre, p.estatus_texto, (p.created_at or "")[:19]] for p in personas],
    )
    return 0


@registrar(
    "persona",
    grupo="Personas",
    resumen="Cambia el estatus de una persona",
    uso="persona <id> <activado|desactivado|pendiente>",
)
def cmd_persona(inv: Invocacion) -> int:
    id_texto, estatus = inv.exactamente(2)
    if not id_texto.isdigit():
        raise ErrorServicio(f"El id debe ser un numero, no {id_texto!r}.")
    persona = inv.core.personas.establecer_estatus(int(id_texto), estatus)  # type: ignore[attr-defined]
    inv.consola.ok(f"{persona.nombre} (id {persona.id}) ahora esta {persona.estatus_texto}.")
    return 0


@registrar(
    "persona-nombre",
    grupo="Personas",
    resumen="Cambia el estatus usando el nombre en vez del id",
    uso="persona-nombre <nombre> <activado|desactivado|pendiente>",
)
def cmd_persona_nombre(inv: Invocacion) -> int:
    nombre, estatus = inv.exactamente(2)
    personas = inv.core.personas.listar()  # type: ignore[attr-defined]
    objetivo = nombre.strip().casefold()
    coincidencias = [p for p in personas if p.nombre.strip().casefold() == objetivo]

    if not coincidencias:
        raise ErrorServicio(f"No hay ninguna persona llamada {nombre!r} en el registro.")
    if len(coincidencias) > 1:
        raise ErrorServicio(
            f"Hay {len(coincidencias)} personas llamadas {nombre!r} "
            f"(ids {[p.id for p in coincidencias]}). Usa 'persona <id> ...'."
        )

    persona = coincidencias[0]
    actualizado = inv.core.personas.establecer_estatus(persona.id, estatus)  # type: ignore[attr-defined]
    inv.consola.ok(f"{actualizado.nombre} (id {actualizado.id}) ahora esta {actualizado.estatus_texto}.")
    return 0


@registrar(
    "persona-borrar",
    grupo="Personas",
    resumen="Elimina una persona del registro y sus asistencias",
    uso="persona-borrar <id>",
    detalle="Pide confirmacion. Tambien borra las asistencias de esa persona.",
)
def cmd_persona_borrar(inv: Invocacion) -> int:
    (id_texto,) = inv.exactamente(1)
    if not id_texto.isdigit():
        raise ErrorServicio(f"El id debe ser un numero, no {id_texto!r}.")

    persona = inv.core.personas.obtener(int(id_texto))  # type: ignore[attr-defined]
    if persona is None:
        raise ErrorServicio(f"No existe la persona con id {id_texto}.")

    if not inv.consola.confirmar(
        f"Borrar a {persona.nombre} (id {persona.id}) y sus asistencias?", por_defecto=False
    ):
        inv.consola.aviso("Cancelado.")
        return 0

    inv.core.personas.eliminar(persona.id)  # type: ignore[attr-defined]
    inv.consola.ok(f"{persona.nombre} (id {persona.id}) eliminado.")
    return 0


# --------------------------------------------------------------------------- #
# Rostros  (faces.db)
# --------------------------------------------------------------------------- #


@registrar(
    "rostros",
    grupo="Rostros",
    resumen="Lista los rostros de faces.db con su numero de muestras",
    uso="rostros [filtro]",
    detalle=(
        "Estas son las personas que el reconocimiento facial puede identificar.\n"
        "Varias filas con el mismo nombre son capturas distintas del mismo rostro\n"
        "y todas sirven para el reconocimiento."
    ),
)
def cmd_rostros(inv: Invocacion) -> int:
    filtro = inv.pos[0] if inv.pos else ""
    entradas = inv.core.rostros.listar(texto=filtro)  # type: ignore[attr-defined]
    inv.consola.tabla(
        ["ID", "Nombre", "Muestras"],
        [[e.id, e.nombre, e.muestras] for e in entradas],
    )
    return 0


@registrar(
    "rostro",
    grupo="Rostros",
    resumen="Muestra el detalle de un rostro",
    uso="rostro <id>",
)
def cmd_rostro(inv: Invocacion) -> int:
    (id_texto,) = inv.exactamente(1)
    if not id_texto.isdigit():
        raise ErrorServicio(f"El id debe ser un numero, no {id_texto!r}.")
    entrada = inv.core.rostros.obtener(int(id_texto))  # type: ignore[attr-defined]
    if entrada is None:
        raise ErrorServicio(f"No existe el rostro con id {id_texto}.")

    c = inv.consola
    c.titulo(f"Rostro {entrada.id}")
    c.escribir(f"  Nombre   : {entrada.nombre}")
    c.escribir(f"  Muestras : {entrada.muestras}")
    return 0


@registrar(
    "rostro-renombrar",
    grupo="Rostros",
    resumen="Cambia el nombre de un rostro",
    uso="rostro-renombrar <id> <nombre nuevo>",
)
def cmd_rostro_renombrar(inv: Invocacion) -> int:
    id_texto, nombre = inv.exactamente(2)
    if not id_texto.isdigit():
        raise ErrorServicio(f"El id debe ser un numero, no {id_texto!r}.")
    entrada = inv.core.rostros.renombrar(int(id_texto), nombre)  # type: ignore[attr-defined]
    inv.consola.ok(f"Rostro {entrada.id} ahora se llama {entrada.nombre}.")
    return 0


@registrar(
    "rostro-borrar",
    grupo="Rostros",
    resumen="Elimina un rostro de faces.db",
    uso="rostro-borrar <id> [--solo-persona]",
    detalle=(
        "Por defecto borra tambien las muestras de embedding, para que el\n"
        "rostro deje de participar en el reconocimiento.\n"
        "Con --solo-persona deja las muestras huerfanas."
    ),
)
def cmd_rostro_borrar(inv: Invocacion) -> int:
    (id_texto,) = inv.exactamente(1)
    if not id_texto.isdigit():
        raise ErrorServicio(f"El id debe ser un numero, no {id_texto!r}.")

    entrada = inv.core.rostros.obtener(int(id_texto))  # type: ignore[attr-defined]
    if entrada is None:
        raise ErrorServicio(f"No existe el rostro con id {id_texto}.")

    solo_persona = inv.bandera("solo-persona")
    alcance = (
        "solo la fila de la persona (las muestras quedan huerfanas)"
        if solo_persona
        else f"la persona y sus {entrada.muestras} muestra(s)"
    )
    if not inv.consola.confirmar(f"Borrar {entrada.nombre} (id {entrada.id}): {alcance}?"):
        inv.consola.aviso("Cancelado.")
        return 0

    inv.core.rostros.eliminar(entrada.id, con_muestras=not solo_persona)  # type: ignore[attr-defined]
    inv.consola.ok(f"Rostro {entrada.id} ({entrada.nombre}) eliminado.")
    return 0


# --------------------------------------------------------------------------- #
# Sesiones
# --------------------------------------------------------------------------- #


@registrar(
    "sesiones",
    grupo="Sesiones",
    resumen="Lista las sesiones",
    uso="sesiones",
)
def cmd_sesiones(inv: Invocacion) -> int:
    ahora = inv.core.sesiones.activa()  # type: ignore[attr-defined]
    activa_id = ahora.id if ahora else None
    filas = [
        [
            s.id,
            s.nombre,
            s.horario,
            "si" if s.id == activa_id else "",
        ]
        for s in inv.core.sesiones.listar()  # type: ignore[attr-defined]
    ]
    inv.consola.tabla(["ID", "Sesion", "Horario", "Activa"], filas)
    if ahora:
        inv.consola.escribir()
        inv.consola.info(f"La sesion activa ahora es la {activa_id} ({ahora.nombre}).")
    return 0


@registrar(
    "sesion-activa",
    grupo="Sesiones",
    resumen="Muestra la sesion que esta en curso ahora mismo",
    uso="sesion-activa",
)
def cmd_sesion_activa(inv: Invocacion) -> int:
    sesion = inv.core.sesiones.activa()  # type: ignore[attr-defined]
    if sesion is None:
        inv.consola.aviso("No hay ninguna sesion activa en este momento.")
        return 0

    resumen = inv.core.asistencias.resumen(sesion.id)  # type: ignore[attr-defined]
    inv.consola.ok(f"{sesion.nombre} (id {sesion.id}) {sesion.horario}")
    inv.consola.escribir(
        f"  Asistencias: {resumen['presentes']} presentes, "
        f"{resumen['ausentes']} ausentes, {resumen['total']} registradas."
    )
    return 0


@registrar(
    "sesion",
    grupo="Sesiones",
    resumen="Muestra el detalle de una sesion",
    uso="sesion <id|nombre>",
)
def cmd_sesion(inv: Invocacion) -> int:
    (referencia,) = inv.exactamente(1)
    sesion = inv.core.resolver_sesion(referencia)  # type: ignore[attr-defined]
    resumen = inv.core.asistencias.resumen(sesion.id)  # type: ignore[attr-defined]

    c = inv.consola
    c.titulo(f"Sesion {sesion.id}")
    c.escribir(f"  Nombre : {sesion.nombre}")
    c.escribir(f"  Horario: {sesion.horario}")
    c.escribir(
        f"  Asistencia: {resumen['presentes']} presentes, "
        f"{resumen['ausentes']} ausentes"
    )
    return 0


@registrar(
    "sesion-nueva",
    grupo="Sesiones",
    resumen="Crea una sesion",
    uso='sesion-nueva <nombre> <inicio HH:MM> <fin HH:MM>',
    detalle='Ejemplo:  sesion-nueva "Algebra III" 08:00 09:00',
)
def cmd_sesion_nueva(inv: Invocacion) -> int:
    nombre, inicio, fin = inv.exactamente(3)
    sesion = inv.core.sesiones.crear(nombre, inicio, fin)  # type: ignore[attr-defined]
    inv.consola.ok(f"Sesion {sesion.id} creada: {sesion.nombre} {sesion.horario}")
    return 0


@registrar(
    "sesion-editar",
    grupo="Sesiones",
    resumen="Modifica una sesion (los campos omitidos se dejan igual)",
    uso="sesion-editar <id> [nombre] [inicio] [fin]",
    detalle='Ejemplo:  sesion-editar 3 "Programacion II" 10:30 11:30',
)
def cmd_sesion_editar(inv: Invocacion) -> int:
    argumentos = inv.entre(2, 4)
    id_texto = argumentos[0]
    if not id_texto.isdigit():
        raise ErrorServicio(f"El id debe ser un numero, no {id_texto!r}.")

    nombre = argumentos[1] if len(argumentos) > 1 else None
    inicio = argumentos[2] if len(argumentos) > 2 else None
    fin = argumentos[3] if len(argumentos) > 3 else None

    sesion = inv.core.sesiones.actualizar(int(id_texto), nombre, inicio, fin)  # type: ignore[attr-defined]
    inv.consola.ok(f"Sesion {sesion.id} actualizada: {sesion.nombre} {sesion.horario}")
    return 0


@registrar(
    "sesion-borrar",
    grupo="Sesiones",
    resumen="Elimina una sesion",
    uso="sesion-borrar <id> [--conservar-asistencias]",
    detalle=(
        "Por defecto borra tambien las asistencias de la sesion.\n"
        "Con --conservar-asistencias las deja intactas."
    ),
)
def cmd_sesion_borrar(inv: Invocacion) -> int:
    (id_texto,) = inv.exactamente(1)
    if not id_texto.isdigit():
        raise ErrorServicio(f"El id debe ser un numero, no {id_texto!r}.")

    sesion = inv.core.sesiones.obtener(int(id_texto))  # type: ignore[attr-defined]
    if sesion is None:
        raise ErrorServicio(f"No existe la sesion con id {id_texto}.")

    conservar = inv.bandera("conservar-asistencias")
    resumen = inv.core.asistencias.resumen(sesion.id)  # type: ignore[attr-defined]
    alcance = (
        "sus asistencias se conservan"
        if conservar
        else f"y sus {resumen['total']} asistencia(s)"
    )
    if not inv.consola.confirmar(f"Borrar la sesion {sesion.id} ({sesion.nombre}) {alcance}?"):
        inv.consola.aviso("Cancelado.")
        return 0

    inv.core.sesiones.eliminar(sesion.id, con_asistencias=not conservar)  # type: ignore[attr-defined]
    inv.consola.ok(f"Sesion {sesion.id} ({sesion.nombre}) eliminada.")
    return 0


# --------------------------------------------------------------------------- #
# Asistencia
# --------------------------------------------------------------------------- #


@registrar(
    "asistencia",
    grupo="Asistencia",
    resumen="Lista las asistencias de una sesion",
    uso="asistencia [<id|nombre|activa>]",
    detalle=(
        "Sin argumentos usa la sesion activa en este momento.\n"
        "Los nombres de persona se toman del registro de personas."
    ),
)
def cmd_asistencia(inv: Invocacion) -> int:
    referencia = inv.pos[0] if inv.pos else "activa"
    sesion = inv.core.resolver_sesion(referencia)  # type: ignore[attr-defined]
    registros = inv.core.asistencias.listar(id_sesion=sesion.id)  # type: ignore[attr-defined]

    filas = [
        [a.id, a.nombre or f"(id {a.id_persona})", "Asistio" if a.presente else "No asistio", a.fecha[:19]]
        for a in registros
    ]
    inv.consola.titulo(f"Asistencia de {sesion.nombre} (id {sesion.id})")
    inv.consola.tabla(["Fila", "Persona", "Estado", "Fecha"], filas)
    return 0


@registrar(
    "asistir",
    grupo="Asistencia",
    resumen="Marca a una persona como asistente a una sesion",
    uso='asistir <persona id|nombre> [<sesion id|nombre>]',
    detalle=(
        "La persona se busca primero en el registro de personas.\n"
        "Si no se indica sesion se usa la que este activa ahora mismo.\n"
        "Repetir el comando actualiza el registro en vez de duplicarlo."
    ),
)
def cmd_asistir(inv: Invocacion) -> int:
    argumentos = inv.entre(1, 2)
    persona = argumentos[0]
    sesion = inv.core.resolver_sesion(argumentos[1] if len(argumentos) > 1 else "activa")  # type: ignore[attr-defined]

    if persona.isdigit():
        id_persona = int(persona)
        if inv.core.personas.obtener(id_persona) is None:  # type: ignore[attr-defined]
            raise ErrorServicio(f"No existe la persona con id {persona}.")
        inv.core.asistencias.registrar(id_persona, sesion.id, True)  # type: ignore[attr-defined]
    else:
        id_persona = inv.core.asistencias.registrar_nombre(persona, sesion.id, True)  # type: ignore[attr-defined]

    registered = inv.core.personas.obtener(id_persona)  # type: ignore[attr-defined]
    nombre = registered.nombre if registered else f"id {id_persona}"
    inv.consola.ok(f"{nombre} asistio a {sesion.nombre} (id {sesion.id}).")
    return 0


@registrar(
    "faltar",
    grupo="Asistencia",
    resumen="Marca a una persona como ausente en una sesion",
    uso='faltar <persona id|nombre> [<sesion id|nombre>]',
)
def cmd_faltar(inv: Invocacion) -> int:
    argumentos = inv.entre(1, 2)
    persona = argumentos[0]
    sesion = inv.core.resolver_sesion(argumentos[1] if len(argumentos) > 1 else "activa")  # type: ignore[attr-defined]

    if persona.isdigit():
        id_persona = int(persona)
        if inv.core.personas.obtener(id_persona) is None:  # type: ignore[attr-defined]
            raise ErrorServicio(f"No existe la persona con id {persona}.")
        inv.core.asistencias.registrar(id_persona, sesion.id, False)  # type: ignore[attr-defined]
    else:
        id_persona = inv.core.asistencias.registrar_nombre(persona, sesion.id, False)  # type: ignore[attr-defined]

    registered = inv.core.personas.obtener(id_persona)  # type: ignore[attr-defined]
    nombre = registered.nombre if registered else f"id {id_persona}"
    inv.consola.ok(f"{nombre} quedo como ausente en {sesion.nombre} (id {sesion.id}).")
    return 0


@registrar(
    "desasistir",
    grupo="Asistencia",
    resumen="Borra el registro de asistencia de una persona en una sesion",
    uso="desasistir <persona id|nombre> [<sesion id|nombre>]",
)
def cmd_desasistir(inv: Invocacion) -> int:
    argumentos = inv.entre(1, 2)
    persona = argumentos[0]
    sesion = inv.core.resolver_sesion(argumentos[1] if len(argumentos) > 1 else "activa")  # type: ignore[attr-defined]

    if persona.isdigit():
        id_persona = int(persona)
    else:
        encontrada = inv.core.personas.por_nombre_exacto(persona)  # type: ignore[attr-defined]
        if encontrada is None:
            raise ErrorServicio(f"No se encontro a {persona!r} en el registro de personas.")
        id_persona = encontrada.id

    antes = inv.core.asistencias.resumen(sesion.id)  # type: ignore[attr-defined]
    inv.core.asistencias.eliminar(sesion.id, id_persona)  # type: ignore[attr-defined]
    despues = inv.core.asistencias.resumen(sesion.id)  # type: ignore[attr-defined]
    if antes["total"] == despues["total"]:
        raise ErrorServicio(
            f"No habia ninguna asistencia registrada para esa persona en {sesion.nombre}."
        )

    inv.consola.ok(
        f"Asistencia borrada en {sesion.nombre}: quedan {despues['total']} registros."
    )
    return 0


@registrar(
    "resumen",
    grupo="Asistencia",
    resumen="Cuenta presentes y ausentes de una sesion",
    uso="resumen [<id|nombre|activa>]",
)
def cmd_resumen(inv: Invocacion) -> int:
    referencia = inv.pos[0] if inv.pos else "activa"
    sesion = inv.core.resolver_sesion(referencia)  # type: ignore[attr-defined]
    resumen = inv.core.asistencias.resumen(sesion.id)  # type: ignore[attr-defined]
    total_registro = len(inv.core.personas.listar())  # type: ignore[attr-defined]

    inv.consola.titulo(f"Resumen de {sesion.nombre} (id {sesion.id})")
    inv.consola.tabla(
        ["Concepto", "Cantidad"],
        [
            ["Presentes", resumen["presentes"]],
            ["Ausentes", resumen["ausentes"]],
            ["Sin registro", max(0, total_registro - resumen["total"])],
            ["Personas en el registro", total_registro],
        ],
    )
    return 0


@registrar(
    "exportar",
    grupo="Asistencia",
    resumen="Exporta la asistencia de una sesion a Excel",
    uso="exportar [<sesion id|nombre|activa>] [archivo.xlsx]",
    detalle=(
        "Sin archivo usa <sesion>_<fecha>.xlsx en el directorio actual.\n"
        "El archivo lleva una fila por persona del roster, con \"Asistio\" o\n"
        "\"No asistio\", igual que la pantalla de asistencia."
    ),
)
def cmd_exportar(inv: Invocacion) -> int:
    argumentos = inv.entre(0, 2)
    referencia: str | int = argumentos[0] if argumentos else "activa"
    sesion = inv.core.resolver_sesion(referencia)  # type: ignore[attr-defined]

    ruta = argumentos[1] if len(argumentos) > 1 else None
    if ruta is None:
        ruta = inv.texto("salida") or None

    repetidas = inv.core.asistencias.asistencias_repetidas(sesion.id)  # type: ignore[attr-defined]
    if repetidas:
        inv.consola.aviso(
            f"La sesion tiene {len(repetidas)} persona(s) registradas mas de una vez; "
            f"usa 'limpiar-asistencias {sesion.id}' para dejar una sola fila."
        )

    destino = inv.core.exportar_sesion(sesion.id, ruta)  # type: ignore[attr-defined]
    inv.consola.ok(f"Exportado a {destino}")
    return 0


@registrar(
    "limpiar-asistencias",
    grupo="Asistencia",
    resumen="Deja una sola fila por persona y sesion",
    uso="limpiar-asistencias [<sesion id|nombre|activa>]",
    detalle="Conserva la fila mas reciente de cada persona duplicada.",
)
def cmd_limpiar_asistencias(inv: Invocacion) -> int:
    referencia = inv.pos[0] if inv.pos else None
    id_sesion = None
    if referencia not in (None, "", "todas"):
        id_sesion = inv.core.resolver_sesion(referencia).id  # type: ignore[attr-defined]

    if not inv.consola.confirmar(
        "Borrar las asistencias repetidas y quedarse con la mas reciente?", por_defecto=False
    ):
        inv.consola.aviso("Cancelado.")
        return 0

    borradas = inv.core.asistencias.limpiar_duplicados(id_sesion)  # type: ignore[attr-defined]
    if borradas:
        inv.consola.ok(f"{borradas} fila(s) repetida(s) eliminada(s).")
    else:
        inv.consola.info("No habia asistencias repetidas.")
    return 0


# --------------------------------------------------------------------------- #
# Ajustes
# --------------------------------------------------------------------------- #


@registrar(
    "ajustes",
    grupo="Ajustes",
    resumen="Muestra las preferencias de la aplicacion",
    uso="ajustes",
    detalle=(
        "Son las mismas preferencias que se cambian en la pantalla de\n"
        "Preferencias de la interfaz grafica."
    ),
)
def cmd_ajustes(inv: Invocacion) -> int:
    filas = inv.core.ajustes.vista()  # type: ignore[attr-defined]
    inv.consola.tabla(
        ["Clave", "Descripcion", "Valor"],
        [[clave, etiqueta, valor] for clave, etiqueta, valor, _ in filas],
    )
    return 0


@registrar(
    "ajuste",
    grupo="Ajustes",
    resumen="Cambia una preferencia",
    uso="ajuste <clave> <valor>",
    detalle=(
        "Usa la clave exacta que muestra 'ajustes'.\n"
        "Ejemplos:\n"
        "  ajuste face/similarity_threshold 0.6\n"
        "  ajuste camera/index 1\n"
        "  ajuste theme/path styles/aerogreen.qss"
    ),
)
def cmd_ajuste(inv: Invocacion) -> int:
    clave, valor = inv.exactamente(2)
    etiqueta = inv.core.ajustes.descripcion(clave)[0]  # type: ignore[attr-defined]
    anterior = inv.core.ajustes.obtener(clave)  # type: ignore[attr-defined]
    nuevo = inv.core.ajustes.establecer(clave, valor)  # type: ignore[attr-defined]
    inv.consola.ok(f"{etiqueta}: {anterior} -> {nuevo}")
    inv.consola.escribir("  (se aplica la proxima vez que se abra la interfaz grafica)")
    return 0


@registrar(
    "ajustes-restaurar",
    grupo="Ajustes",
    resumen="Devuelve todas las preferencias a su valor por defecto",
    uso="ajustes-restaurar",
)
def cmd_ajustes_restaurar(inv: Invocacion) -> int:
    if not inv.consola.confirmar(
        "Restaurar TODAS las preferencias a sus valores por defecto?", por_defecto=False
    ):
        inv.consola.aviso("Cancelado.")
        return 0
    inv.core.ajustes.restaurar()  # type: ignore[attr-defined]
    inv.consola.ok("Preferencias restauradas.")
    return 0
