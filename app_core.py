# -*- coding: utf-8 -*-
"""
main.py (versión Android / Kivy)
=================================
Versión móvil de "Procesador de Asistencia Zoom". Reutiliza exactamente
la misma lógica de procesamiento que la versión de escritorio
(csv_processor.py, roster_matcher.py, excel_exporter.py) — lo único que
cambia es la interfaz gráfica, hecha con Kivy en vez de Tkinter, porque
Tkinter no existe en Android.

Funciones:
    - Abrir el CSV de Zoom.
    - Abrir el listado oficial de socios (Excel).
    - Cotejar ambos archivos (misma lógica que la versión de escritorio).
    - Buscar / filtrar / ordenar el resultado.
    - Exportar a CSV o Excel y compartir el archivo (WhatsApp, Drive,
      correo, etc.) usando el diálogo nativo de Android para compartir.
"""

import os
import re
import unicodedata

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import BooleanProperty, ListProperty, NumericProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput

# Debe coincidir EXACTAMENTE con "title = ..." en buildozer.spec. Se usa
# solo para poder mostrarle al usuario la ruta exacta donde quedan los
# reportes (Android arma esa carpeta automáticamente usando el nombre de
# la app tal cual aparece bajo el ícono, que es justamente ese "title").
APP_TITLE_FOR_STORAGE = "Asistencia Zoom"

from csv_processor import (
    CSVProcessingError,
    compute_attendance_flag,
    export_records_to_csv,
    is_disguised_excel_file,
    load_zoom_csv,
)
from excel_exporter import export_to_excel
from roster_matcher import (
    RosterProcessingError,
    load_roster_excel,
    match_zoom_to_roster,
)

DEFAULT_THRESHOLD = "30"

KV = """
<AppButton@Button>:
    # button_color es una propiedad "inventada" (Kivy la crea sola al
    # verla en una regla KV): así cada botón puede definir su propio
    # color sin perder el estilo común (esquinas redondeadas, texto
    # blanco, etc.) definido acá una sola vez.
    button_color: 0.20, 0.45, 0.75, 1
    background_normal: ""
    background_down: ""
    background_disabled_normal: ""
    background_color: 0, 0, 0, 0
    color: 1, 1, 1, 1
    bold: True
    font_size: "12sp" if app.landscape else "12.5sp"
    halign: "center"
    valign: "middle"
    text_size: self.width - dp(10), None
    canvas.before:
        Color:
            rgba: (0.68, 0.70, 0.73, 1) if self.disabled else self.button_color
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(10)]

<StyledInput@TextInput>:
    background_normal: ""
    background_active: ""
    background_color: 0, 0, 0, 0
    foreground_color: 0.15, 0.15, 0.15, 1
    hint_text_color: 0.60, 0.60, 0.60, 1
    cursor_color: 0.20, 0.45, 0.75, 1
    padding: dp(10), dp(10)
    font_size: "14sp"
    canvas.before:
        Color:
            rgba: 1, 1, 1, 1
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(8)]
        Color:
            rgba: 0.80, 0.83, 0.87, 1
        Line:
            rounded_rectangle: [self.x, self.y, self.width, self.height, dp(8)]
            width: 1

<RowWidget>:
    orientation: "horizontal"
    size_hint_y: None
    height: dp(46)
    padding: dp(8), dp(2)
    spacing: dp(4)
    canvas.before:
        Color:
            rgba: self.bgcolor
        Rectangle:
            pos: self.pos
            size: self.size
        Color:
            rgba: 0.88, 0.89, 0.91, 1
        Line:
            points: [self.x, self.y, self.x + self.width, self.y]
            width: 1
    Label:
        text: root.nombre
        color: 0.12, 0.12, 0.14, 1
        size_hint_x: 0.28
        text_size: self.size
        halign: "left"
        valign: "middle"
        shorten: True
        font_size: "13sp"
    Label:
        text: root.apellido
        color: 0.12, 0.12, 0.14, 1
        size_hint_x: 0.28
        text_size: self.size
        halign: "left"
        valign: "middle"
        shorten: True
        font_size: "13sp"
    Label:
        text: root.sede
        color: 0.12, 0.12, 0.14, 1
        size_hint_x: 0.22
        text_size: self.size
        halign: "left"
        valign: "middle"
        shorten: True
        font_size: "13sp"
    Label:
        text: root.duracion
        color: 0.12, 0.12, 0.14, 1
        size_hint_x: 0.12
        text_size: self.size
        halign: "right"
        valign: "middle"
        font_size: "13sp"
    Label:
        text: root.asistencia
        bold: True
        color: 0.12, 0.12, 0.14, 1
        size_hint_x: 0.10
        text_size: self.size
        halign: "center"
        valign: "middle"
        font_size: "14sp"

BoxLayout:
    id: root_box
    orientation: "vertical"
    padding: dp(10)
    spacing: dp(7)
    canvas.before:
        Color:
            rgba: 0.94, 0.95, 0.97, 1
        Rectangle:
            pos: self.pos
            size: self.size

    # ------------------------------------------------------------------
    # Barra de controles (mes, botones, búsqueda, filtros, orden).
    # Va dentro de un ScrollView con altura MÁXIMA limitada a una
    # fracción de la pantalla: si en horizontal no alcanza el espacio
    # para mostrar todo, esta barra se vuelve desplazable POR SEPARADO,
    # en vez de "robarle" espacio a la tabla de resultados de abajo. Así
    # la tabla siempre conserva una zona visible y deslizable, sea cual
    # sea el tamaño u orientación de la pantalla.
    # ------------------------------------------------------------------
    ScrollView:
        id: toolbar_scroll
        size_hint_y: None
        # ANTES: "root_box.height * 0.58" en horizontal le reservaba a la
        # barra de controles más de la mitad del alto de la pantalla, que
        # en horizontal ya es poco (el celular está "acostado"). Eso
        # dejaba a la tabla de resultados con apenas un puñado de pixeles
        # de alto —por eso solo se veía "fila por fila" y no había
        # margen real para deslizar. Ahora el máximo lo calcula
        # "app.toolbar_max_height" en Python (ver _recalc_toolbar_max),
        # que SIEMPRE le deja a la tabla una altura mínima garantizada,
        # sea cual sea la orientación o el tamaño de pantalla.
        height: min(toolbar_box.height, app.toolbar_max_height)
        do_scroll_x: False
        bar_width: dp(4)
        BoxLayout:
            id: toolbar_box
            orientation: "vertical"
            size_hint_y: None
            height: self.minimum_height
            spacing: dp(7)

            BoxLayout:
                size_hint_y: None
                height: dp(34)
                spacing: dp(8)
                padding: dp(4), 0
                canvas.before:
                    Color:
                        rgba: 0.87, 0.91, 0.97, 1
                    RoundedRectangle:
                        pos: self.pos
                        size: self.size
                        radius: [dp(8)]
                Image:
                    source: "logo.png"
                    size_hint_x: None
                    width: dp(28)
                    allow_stretch: True
                    keep_ratio: True
                Label:
                    text: "Mes: " + (app.attendance_month if app.attendance_month else "(sin definir)")
                    color: 0.14, 0.22, 0.34, 1
                    bold: True
                    font_size: "13sp"
                    text_size: self.size
                    padding: dp(4), 0
                    halign: "left"
                    valign: "middle"
                    shorten: True
                AppButton:
                    text: "Cambiar mes"
                    size_hint_x: 0.34
                    button_color: 0.30, 0.36, 0.46, 1
                    on_release: app.ask_attendance_month()

            BoxLayout:
                size_hint_y: None
                height: dp(40) if app.landscape else dp(48)
                spacing: dp(6)
                AppButton:
                    text: "Abrir CSV Zoom"
                    on_release: app.open_zoom_dialog()
                AppButton:
                    text: "Abrir Socios (Excel)"
                    on_release: app.open_roster_dialog()
                AppButton:
                    text: "Cotejar"
                    disabled: not (app.zoom_loaded and app.roster_loaded)
                    button_color: 0.16, 0.62, 0.42, 1
                    on_release: app.on_cotejar()

            Label:
                id: status_label
                text: app.status_text
                size_hint_y: None
                height: dp(38) if app.landscape else dp(44)
                text_size: self.width, None
                halign: "left"
                valign: "middle"
                color: 0.18, 0.20, 0.24, 1
                font_size: "12.5sp"

            BoxLayout:
                size_hint_y: None
                height: dp(40) if app.landscape else dp(44)
                spacing: dp(6)
                StyledInput:
                    id: search_input
                    hint_text: "Buscar nombre / apellido / sede"
                    multiline: False
                    on_text_validate: app.apply_filters()
                StyledInput:
                    id: min_duration_input
                    hint_text: "Min. min"
                    multiline: False
                    input_filter: "float"
                    size_hint_x: 0.24
                    on_text_validate: app.apply_filters()
                StyledInput:
                    id: threshold_input
                    hint_text: "Umbral P"
                    text: "30"
                    multiline: False
                    input_filter: "float"
                    size_hint_x: 0.24
                    on_text_validate: app.apply_filters()

            BoxLayout:
                size_hint_y: None
                height: dp(40) if app.landscape else dp(44)
                spacing: dp(6)
                Spinner:
                    id: sort_spinner
                    text: "Duración (mayor a menor)"
                    values: ["Duración (mayor a menor)", "Duración (menor a mayor)", "Nombre (A-Z)", "Apellido (A-Z)", "Sede (A-Z)", "Asistencia"]
                    background_normal: ""
                    background_color: 1, 1, 1, 1
                    color: 0.15, 0.15, 0.15, 1
                    on_text: app.apply_filters()
                AppButton:
                    text: "Aplicar filtro"
                    size_hint_x: 0.4
                    on_release: app.apply_filters()

    BoxLayout:
        size_hint_y: None
        height: dp(28) if app.landscape else dp(32)
        canvas.before:
            Color:
                rgba: 0.14, 0.22, 0.34, 1
            RoundedRectangle:
                pos: self.pos
                size: self.size
                radius: [dp(6), dp(6), 0, 0]
        Label:
            text: "Nombre"
            bold: True
            color: 1, 1, 1, 1
            size_hint_x: 0.28
            font_size: "13sp"
        Label:
            text: "Apellido"
            bold: True
            color: 1, 1, 1, 1
            size_hint_x: 0.28
            font_size: "13sp"
        Label:
            text: "Sede"
            bold: True
            color: 1, 1, 1, 1
            size_hint_x: 0.22
            font_size: "13sp"
        Label:
            text: "Min."
            bold: True
            color: 1, 1, 1, 1
            size_hint_x: 0.12
            font_size: "13sp"
        Label:
            text: "Asist."
            bold: True
            color: 1, 1, 1, 1
            size_hint_x: 0.10
            font_size: "13sp"

    BoxLayout:
        canvas.before:
            Color:
                rgba: 1, 1, 1, 1
            Rectangle:
                pos: self.pos
                size: self.size
        RecycleView:
            id: rv
            viewclass: "RowWidget"
            # Barra de scroll visible: además de arreglar el alto
            # disponible, esto le da al usuario una señal clara de que
            # la lista se puede deslizar (antes no había ninguna pista
            # visual y encima casi no había alto para hacerlo).
            bar_width: dp(6)
            scroll_type: ["bars", "content"]
            RecycleBoxLayout:
                default_size: None, dp(46)
                default_size_hint: 1, None
                size_hint_y: None
                height: self.minimum_height
                orientation: "vertical"

    Label:
        id: count_label
        text: app.count_text
        size_hint_y: None
        height: dp(22) if app.landscape else dp(26)
        color: 0.18, 0.20, 0.24, 1
        font_size: "12sp"

    BoxLayout:
        size_hint_y: None
        height: dp(42) if app.landscape else dp(50)
        spacing: dp(6)
        AppButton:
            text: "Exportar CSV"
            disabled: not app.has_results
            button_color: 0.12, 0.55, 0.60, 1
            on_release: app.export_csv()
        AppButton:
            text: "Exportar Excel"
            disabled: not app.has_results
            button_color: 0.12, 0.55, 0.60, 1
            on_release: app.export_excel()
        AppButton:
            text: "Pendientes"
            disabled: not app.has_pendientes
            button_color: 0.85, 0.55, 0.15, 1
            on_release: app.export_pendientes()
"""


class RowWidget(RecycleDataViewBehavior, BoxLayout):
    nombre = StringProperty("")
    apellido = StringProperty("")
    sede = StringProperty("")
    duracion = StringProperty("")
    asistencia = StringProperty("")
    bgcolor = ListProperty([1, 1, 1, 1])

    def refresh_view_attrs(self, rv, index, data):
        self.nombre = data.get("nombre", "")
        self.apellido = data.get("apellido", "")
        self.sede = data.get("sede", "")
        self.duracion = data.get("duracion", "")
        self.asistencia = data.get("asistencia", "")
        if self.asistencia == "P":
            self.bgcolor = [0.83, 0.95, 0.85, 1]
        elif self.asistencia == "A":
            self.bgcolor = [0.99, 0.87, 0.87, 1]
        else:
            self.bgcolor = [1, 1, 1, 1]
        return super().refresh_view_attrs(rv, index, data)


def _add_white_background(widget, color=(1, 1, 1, 1)):
    """Dibuja un fondo opaco detrás de `widget`. Los Popup de Kivy usan
    por defecto un fondo semi-transparente oscuro, así que un Label con
    texto oscuro (como los que usa esta app) queda prácticamente
    invisible encima — eso era lo que pasaba en el popup "Archivo
    guardado". Este helper agrega un rectángulo blanco que sigue la
    posición y el tamaño del widget en todo momento."""
    with widget.canvas.before:
        Color(*color)
        rect = Rectangle(pos=widget.pos, size=widget.size)

    def _sync_rect(instance, _value):
        rect.pos = instance.pos
        rect.size = instance.size

    widget.bind(pos=_sync_rect, size=_sync_rect)


def _open_shared_uri(uri_str, mime_type):
    """Abre un archivo ya copiado a la carpeta pública de Descargas,
    mostrando SIEMPRE el selector nativo de Android ("Abrir con...")
    para que el usuario elija con qué app abrirlo (Excel, Google
    Sheets, WPS Office, OpenOffice, cualquier lector de CSV, etc.), en
    vez de intentar adivinar una sola app por defecto.

    `uri_str` es el identificador que devuelve androidstorage4kivy al
    copiar el archivo a la carpeta compartida. Solo funciona en
    Android; en PC no hace nada (ahí el usuario ya tiene el archivo a
    mano en su carpeta de exportación local).

    NOTA sobre el bug anterior ("Invalid instance of 'android/net/Uri'
    passed for a 'java/lang/String'"): androidstorage4kivy en realidad
    devuelve un objeto Uri de Android, no un texto plano. El código
    viejo guardaba ese objeto tal cual y, más tarde, volvía a llamar
    `Uri.parse(...)` sobre él —pero `Uri.parse` espera un String, no un
    Uri ya armado, y ahí reventaba. Ahora `_copy_to_public_downloads`
    lo convierte a texto (str) apenas lo recibe, así que acá siempre
    llega un String normal y `Uri.parse` funciona sin problema."""
    from kivy.utils import platform
    if platform != "android" or not uri_str:
        return
    try:
        from jnius import autoclass, cast
        Intent = autoclass("android.content.Intent")
        Uri = autoclass("android.net.Uri")
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        activity = cast("android.app.Activity", PythonActivity.mActivity)
        uri = Uri.parse(str(uri_str))

        def _try_open(mime):
            intent = Intent(Intent.ACTION_VIEW)
            intent.setDataAndType(uri, mime)
            intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            # Intent.createChooser fuerza SIEMPRE el pop-up "Abrir con"
            # con todas las apps que puedan abrir ese tipo de archivo,
            # aunque el usuario ya haya marcado alguna como "Siempre"
            # antes — que es justo lo que se pidió: poder elegir la app
            # (Excel, OpenOffice, etc.) cada vez, tanto para .xlsx como
            # para .csv.
            chooser = Intent.createChooser(intent, "Abrir con")
            chooser.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            activity.startActivity(chooser)

        try:
            _try_open(mime_type)
        except Exception:
            # Algunos celulares no tienen ninguna app registrada para el
            # tipo MIME exacto (ej. "text/csv"); se reintenta con un
            # tipo genérico para que de todas formas aparezca el
            # selector con las apps de archivos/documentos disponibles.
            _try_open("*/*")
    except Exception as e:
        _show_popup(
            "No se pudo abrir",
            "El archivo está guardado correctamente, pero no se pudo "
            "mostrar el selector de apps para abrirlo.\n\n"
            f"Detalle técnico: {e}",
            success=False,
        )


def _show_popup(
    title: str,
    message: str,
    open_uri: str = None,
    open_mime: str = None,
    success: bool = None,
) -> None:
    """Muestra un popup de mensaje. Si `success` es True o False, se
    agrega arriba un ✓ verde o una ✕ roja bien grandes para que de un
    vistazo (sin tener que leer el texto) se note si la operación salió
    bien o mal. Si `success` es None (el valor por defecto), no se
    muestra ningún ícono — para mensajes que son solo informativos, ni
    éxito ni error (ej. "Debes cargar ambos archivos")."""
    box = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(10))
    _add_white_background(box)

    if success is not None:
        icon_label = Label(
            text="\u2713" if success else "\u2715",  # ✓ / ✕
            bold=True,
            font_size="40sp",
            size_hint_y=None,
            height=dp(48),
            color=(0.16, 0.62, 0.42, 1) if success else (0.82, 0.22, 0.22, 1),
        )
        box.add_widget(icon_label)

    scroll = ScrollView(do_scroll_x=False)
    msg_label = Label(
        text=message,
        color=(0.15, 0.15, 0.15, 1),
        halign="left",
        valign="top",
        size_hint_y=None,
        markup=False,
    )
    # El texto de un Label no se ajusta a varias líneas por sí solo: hay
    # que decirle explícitamente el ancho disponible (text_size) para
    # que "envuelva" el texto en vez de estirarse en una sola línea
    # gigante que termina cortada/invisible fuera de la pantalla (que es
    # justo lo que se veía en el popup "Archivo guardado"). Al atar
    # text_size y height al ancho/alto real del Label, esto se ajusta
    # solo sin importar el tamaño de pantalla ni cuán largo sea el
    # mensaje.
    def _sync_text_size(instance, value):
        instance.text_size = (instance.width, None)

    def _sync_height(instance, value):
        instance.height = instance.texture_size[1]

    msg_label.bind(width=_sync_text_size, texture_size=_sync_height)
    scroll.add_widget(msg_label)
    box.add_widget(scroll)

    if open_uri:
        open_btn = Button(
            text="Abrir archivo",
            size_hint_y=None,
            height=dp(46),
            background_normal="",
            background_color=(0.12, 0.55, 0.60, 1),
            color=(1, 1, 1, 1),
            bold=True,
        )
        open_btn.bind(on_release=lambda *_a: _open_shared_uri(open_uri, open_mime))
        box.add_widget(open_btn)

    close_btn = Button(
        text="Cerrar",
        size_hint_y=None,
        height=dp(44),
        background_normal="",
        background_color=(0.55, 0.58, 0.61, 1),
        color=(1, 1, 1, 1),
    )
    box.add_widget(close_btn)
    popup = Popup(title=title, content=box, size_hint=(0.9, 0.7))
    close_btn.bind(on_release=popup.dismiss)
    popup.open()


class ZoomAttendanceMobileApp(App):
    status_text = StringProperty("Ningún archivo cargado todavía.")
    count_text = StringProperty("Total: 0 | Filtrados: 0")
    # IMPORTANTE: estas 4 banderas deben ser BooleanProperty (no atributos
    # planos de Python) para que las reglas del KV como
    # "disabled: not (app.zoom_loaded and app.roster_loaded)" se vuelvan a
    # evaluar automáticamente cuando cambian. Con un atributo plano
    # (zoom_loaded = False), Kivy nunca se entera de que cambió y el botón
    # "Cotejar" (y los de "Exportar CSV/Excel/Pendientes") quedan
    # deshabilitados para siempre, aunque la carga interna sí haya
    # funcionado. Este era el bug que impedía cotejar y exportar.
    zoom_loaded = BooleanProperty(False)
    roster_loaded = BooleanProperty(False)
    has_results = BooleanProperty(False)
    has_pendientes = BooleanProperty(False)
    # True cuando el celular está en horizontal. El KV la usa para
    # achicar algunas alturas y así aprovechar mejor el poco alto
    # disponible en horizontal (ver _on_window_resize más abajo).
    landscape = BooleanProperty(False)
    # Alto máximo (en px) que puede ocupar la barra de controles de
    # arriba (mes/botones/buscador/filtros) antes de volverse
    # desplazable por separado. Se recalcula en _recalc_toolbar_max()
    # cada vez que cambia el tamaño de la ventana, y SIEMPRE deja un
    # mínimo garantizado de alto libre para la tabla de resultados (ver
    # LIST_MIN_HEIGHT), que es justo lo que en horizontal no estaba
    # pasando antes.
    toolbar_max_height = NumericProperty(dp(400))
    # Mes de la asistencia que se está procesando (ej. "Julio 2026").
    # Es obligatorio: no queda un valor por defecto a propósito, así el
    # popup de inicio SIEMPRE lo pide la primera vez.
    attendance_month = StringProperty("")

    def build(self):
        self.zoom_records = []
        self.roster_records = []
        self.all_records = []
        self.filtered_records = []
        self.no_encontrados = []
        self.ambiguos = []
        self.mode = "zoom"
        self._request_android_permissions()
        Window.clearcolor = (0.94, 0.95, 0.97, 1)

        self.landscape = Window.width > Window.height
        Window.bind(size=self._on_window_resize)

        root = Builder.load_string(KV)
        # El alto de root_box todavía no es el definitivo apenas se
        # construye el KV (Kivy recién va a hacer el layout), así que
        # además de recalcular en cada resize, lo recalculamos una vez
        # más un instante después de arrancar, cuando el layout real ya
        # está listo.
        root.bind(height=self._recalc_toolbar_max)
        Clock.schedule_once(self._recalc_toolbar_max, 0)
        # Se pide el mes con un pequeño retraso para que el popup se
        # abra DESPUÉS de que la ventana principal ya esté armada (si se
        # abre en el mismo instante que build(), en algunos celulares el
        # popup queda "debajo" y no se ve).
        Clock.schedule_once(self._ask_attendance_month_blocking, 0.3)
        return root

    def _on_window_resize(self, _instance, size):
        self.landscape = size[0] > size[1]
        Clock.schedule_once(self._recalc_toolbar_max, 0)

    # Alto mínimo que la tabla de resultados debe conservar siempre,
    # sin importar cuánto ocupe la barra de controles de arriba.
    LIST_MIN_HEIGHT = dp(170)

    def _recalc_toolbar_max(self, *_args):
        """Calcula cuánto espacio le queda disponible a la barra de
        controles (mes/botones/buscador/filtros) DESPUÉS de reservar el
        alto de las filas fijas de abajo (encabezado, contador, botones
        de exportar) y un mínimo garantizado para la tabla de
        resultados. Este es el arreglo al problema de horizontal: antes
        se le daba a la barra de controles una fracción fija del alto
        total (0.58 en horizontal), que en pantallas anchas y bajas
        dejaba casi nada para la tabla. Ahora la tabla SIEMPRE se queda
        con su mínimo, y la barra de controles usa lo que sobra (y si no
        alcanza para mostrarse completa, ella misma se vuelve
        desplazable, gracias al ScrollView que la contiene)."""
        if not self.root:
            return
        header_h = dp(28) if self.landscape else dp(32)
        count_h = dp(22) if self.landscape else dp(26)
        export_h = dp(42) if self.landscape else dp(50)
        gaps = 4 * dp(7)   # 4 espacios entre los 5 hijos directos de root_box
        padding = 2 * dp(10)  # padding superior + inferior de root_box
        reserved = header_h + count_h + export_h + gaps + padding
        available = self.root.height - reserved - self.LIST_MIN_HEIGHT
        self.toolbar_max_height = max(dp(90), available)

    # ------------------------------------------------------------------
    # Mes de la asistencia (obligatorio)
    # ------------------------------------------------------------------
    def ask_attendance_month(self):
        """Reabre el popup para CAMBIAR el mes ya definido (botón
        'Cambiar mes'). A diferencia del popup inicial, este sí se puede
        cerrar tocando afuera, porque ya hay un valor válido guardado."""
        self._open_month_popup(force=False)

    def _ask_attendance_month_blocking(self, *_args):
        """Popup OBLIGATORIO que se muestra al abrir la app. No se puede
        cerrar tocando afuera ni con el botón "atrás" del celular sin
        haber escrito un mes: si se cierra sin que quede un valor
        guardado, se vuelve a abrir solo."""
        self._open_month_popup(force=True)

    def _open_month_popup(self, force):
        box = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(10))
        _add_white_background(box)

        if force:
            intro_text = (
                "Antes de continuar, ingresa el MES de esta asistencia "
                "(ejemplo: \"Julio 2026\").\n\n"
                "Es obligatorio: se usa para nombrar los reportes "
                "exportados y para ordenarlos en sus carpetas."
            )
            intro_height = dp(96)
        else:
            intro_text = "Ingresa el nuevo mes de la asistencia:"
            intro_height = dp(34)

        box.add_widget(Label(
            text=intro_text,
            size_hint_y=None,
            height=intro_height,
            color=(0.15, 0.15, 0.15, 1),
            halign="left",
            valign="middle",
            text_size=(dp(280), None),
        ))

        month_input = TextInput(
            text=self.attendance_month,
            hint_text="Ej: Julio 2026",
            multiline=False,
            size_hint_y=None,
            height=dp(44),
        )
        box.add_widget(month_input)

        error_label = Label(
            text="",
            size_hint_y=None,
            height=dp(22),
            color=(0.75, 0.10, 0.10, 1),
            font_size="12sp",
        )
        box.add_widget(error_label)

        continue_btn = Button(text="Continuar", size_hint_y=None, height=dp(46))
        box.add_widget(continue_btn)

        popup = Popup(
            title="Mes de la asistencia (obligatorio)" if force else "Cambiar mes",
            content=box,
            size_hint=(0.9, 0.55),
            auto_dismiss=not force,
        )

        def _confirm(*_a):
            value = month_input.text.strip()
            if not value:
                error_label.text = "Debes ingresar el mes para poder continuar."
                return
            self.attendance_month = value
            popup.dismiss()

        def _reopen_if_still_empty(*_a):
            # Cubre el caso del botón "atrás" de Android: si de alguna
            # forma el popup se cerró sin guardar un mes, se vuelve a
            # abrir de inmediato.
            if force and not self.attendance_month:
                Clock.schedule_once(lambda dt: popup.open(), 0.05)

        continue_btn.bind(on_release=_confirm)
        month_input.bind(on_text_validate=_confirm)
        if force:
            popup.bind(on_dismiss=_reopen_if_still_empty)
        popup.open()

    def _month_ready(self):
        """Verifica que ya se haya ingresado el mes antes de dejar
        cotejar o exportar. Es un respaldo extra: en el uso normal el
        popup obligatorio del inicio ya garantiza esto, pero si por
        algún motivo attendance_month quedara vacío, esto lo vuelve a
        pedir en vez de dejar avanzar."""
        if not self.attendance_month.strip():
            self.ask_attendance_month()
            return False
        return True

    @staticmethod
    def _slugify(text):
        """Convierte el mes ingresado (ej. "Julio 2026") en un texto
        seguro para usar como parte de un nombre de archivo (sin
        tildes, espacios ni símbolos raros)."""
        text = unicodedata.normalize("NFKD", text or "")
        text = "".join(c for c in text if not unicodedata.combining(c))
        text = re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_")
        return text or "sin_mes"

    def _month_slug(self):
        return self._slugify(self.attendance_month)

    def _request_android_permissions(self):
        """Pide permisos de almacenamiento al usuario la primera vez que
        abre la app en Android. En PC (Windows/Linux/Mac) no existe el
        módulo 'android', así que simplemente no hace nada ahí."""
        try:
            from android.permissions import request_permissions, Permission
            request_permissions([
                Permission.READ_EXTERNAL_STORAGE,
                Permission.WRITE_EXTERNAL_STORAGE,
            ])
        except ImportError:
            pass  # No estamos corriendo en Android, no hace falta.

    # ------------------------------------------------------------------
    # Selección de archivos
    # ------------------------------------------------------------------
    # En Android usamos directamente el Intent nativo de selección de
    # documentos y leemos el archivo con ContentResolver. Esto evita un
    # bug conocido de la librería 'plyer', que en algunos fabricantes
    # (MIUI/Xiaomi) y algunas carpetas (ej. "Documentos") no logra
    # convertir el archivo elegido en una ruta utilizable: a veces lanza
    # un error de formato de identificador ("msf:...") y otras veces
    # simplemente devuelve None sin avisar nada. Haciendo la lectura
    # nosotros mismos (que es como Android espera que se haga desde la
    # introducción de "almacenamiento con alcance limitado") evitamos
    # depender de esa conversión y funciona sin importar la carpeta o
    # el fabricante del celular.
    #
    # En PC (Windows/Linux/Mac, para pruebas) seguimos usando plyer, que
    # ahí sí funciona sin problemas.

    _REQUEST_CODE_ZOOM = 9001
    _REQUEST_CODE_ROSTER = 9002

    def open_zoom_dialog(self):
        self._open_file_dialog(is_roster=False)

    def open_roster_dialog(self):
        self._open_file_dialog(is_roster=True)

    def _open_file_dialog(self, is_roster):
        from kivy.utils import platform
        if platform == "android":
            self._open_file_dialog_android(is_roster)
        else:
            self._open_file_dialog_desktop(is_roster)

    def _open_file_dialog_desktop(self, is_roster):
        from plyer import filechooser
        callback = self._on_roster_selected if is_roster else self._on_zoom_selected
        try:
            filechooser.open_file(on_selection=callback)
        except Exception as e:
            _show_popup("Error", f"No se pudo abrir el selector de archivos:\n{e}", success=False)

    def _open_file_dialog_android(self, is_roster):
        try:
            from jnius import autoclass
            from android import activity

            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            Intent = autoclass('android.content.Intent')

            intent = Intent(Intent.ACTION_OPEN_DOCUMENT)
            intent.addCategory(Intent.CATEGORY_OPENABLE)
            intent.setType("*/*")
            intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)

            request_code = (
                self._REQUEST_CODE_ROSTER if is_roster else self._REQUEST_CODE_ZOOM
            )
            activity.bind(on_activity_result=self._on_android_activity_result)
            PythonActivity.mActivity.startActivityForResult(intent, request_code)
        except Exception as e:
            _show_popup("Error", f"No se pudo abrir el selector de archivos:\n{e}", success=False)

    def _on_android_activity_result(self, request_code, result_code, intent):
        RESULT_OK = -1
        if request_code not in (self._REQUEST_CODE_ZOOM, self._REQUEST_CODE_ROSTER):
            return  # No es nuestro selector (puede ser el de "compartir", etc.)
        if result_code != RESULT_OK or intent is None:
            return
        uri = intent.getData()
        if uri is None:
            return
        is_roster = request_code == self._REQUEST_CODE_ROSTER
        Clock.schedule_once(lambda dt: self._handle_picked_uri(uri, is_roster))

    def _handle_picked_uri(self, uri, is_roster):
        try:
            filepath = self._copy_content_uri_to_local_file(uri)
        except Exception as e:
            _show_popup(
                "Error",
                f"No se pudo leer el archivo elegido desde el celular:\n{e}",
                success=False,
            )
            return
        if is_roster:
            self._load_roster_file(filepath)
        else:
            self._load_zoom_file(filepath)

    @staticmethod
    def _copy_content_uri_to_local_file(uri):
        """Copia el archivo señalado por un content:// URI de Android hacia
        un archivo normal dentro del almacenamiento privado de la app, para
        poder abrirlo con las funciones normales de Python (open, pandas,
        openpyxl, etc.) igual que en la versión de escritorio."""
        from jnius import autoclass

        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        OpenableColumns = autoclass('android.provider.OpenableColumns')
        resolver = PythonActivity.mActivity.getContentResolver()

        # Intentar obtener el nombre original del archivo (para conservar
        # la extensión .csv / .xlsx y que el resto del código la detecte
        # correctamente).
        display_name = "archivo_seleccionado"
        cursor = resolver.query(uri, None, None, None, None)
        if cursor is not None:
            try:
                if cursor.moveToFirst():
                    idx = cursor.getColumnIndex(OpenableColumns.DISPLAY_NAME)
                    if idx != -1:
                        name = cursor.getString(idx)
                        if name:
                            display_name = name
            finally:
                cursor.close()

        input_stream = resolver.openInputStream(uri)
        if input_stream is None:
            raise IOError("Android no permitió abrir el archivo elegido.")

        app = App.get_running_app()
        dest_dir = app.user_data_dir
        dest_path = os.path.join(dest_dir, display_name)

        chunk_size = 8192
        java_buffer = bytearray(chunk_size)
        try:
            with open(dest_path, "wb") as out_file:
                while True:
                    n = input_stream.read(java_buffer, 0, chunk_size)
                    if n == -1:
                        break
                    out_file.write(bytes(java_buffer[:n]))
        finally:
            input_stream.close()

        return dest_path

    def _on_zoom_selected(self, selection):
        if not selection:
            return
        filepath = selection[0]
        Clock.schedule_once(lambda dt: self._load_zoom_file(filepath))

    def _on_roster_selected(self, selection):
        if not selection:
            return
        filepath = selection[0]
        Clock.schedule_once(lambda dt: self._load_roster_file(filepath))

    # ------------------------------------------------------------------
    # Carga de archivos (misma lógica que la versión de escritorio)
    # ------------------------------------------------------------------
    def _load_zoom_file(self, filepath):
        try:
            was_disguised = is_disguised_excel_file(filepath)
            records, column_map = load_zoom_csv(filepath)
        except CSVProcessingError as e:
            _show_popup("Error al procesar el CSV", str(e), success=False)
            return
        except Exception as e:
            _show_popup("Error inesperado", str(e), success=False)
            return

        self.zoom_records = records
        self.zoom_loaded = True
        self.mode = "zoom"
        self.all_records = self.zoom_records
        self.no_encontrados = []
        self.ambiguos = []
        self.has_pendientes = False

        self._reset_filters()
        self.apply_filters()

        nombre_archivo = os.path.basename(filepath)
        aviso = " (era un Excel disfrazado de .csv, detectado automáticamente)" if was_disguised else ""
        self.status_text = f"Zoom: {nombre_archivo}{aviso} — {len(records)} participantes."

    def _load_roster_file(self, filepath):
        try:
            roster = load_roster_excel(filepath)
        except RosterProcessingError as e:
            _show_popup("Error al procesar el listado de socios", str(e), success=False)
            return
        except Exception as e:
            _show_popup("Error inesperado", str(e), success=False)
            return

        self.roster_records = roster
        self.roster_loaded = True
        nombre_archivo = os.path.basename(filepath)
        self.status_text = f"Socios: {nombre_archivo} — {len(roster)} socios. " \
                            f"{'Presiona Cotejar.' if self.zoom_loaded else 'Ahora abre también el CSV de Zoom.'}"

    # ------------------------------------------------------------------
    # Cotejo
    # ------------------------------------------------------------------
    def on_cotejar(self):
        if not self._month_ready():
            return
        if not self.zoom_records or not self.roster_records:
            _show_popup("Faltan archivos", "Debes cargar el CSV de Zoom y el listado de socios.")
            return

        threshold = self._safe_float(self.root.ids.threshold_input.text, 30.0)
        resultado, no_encontrados, ambiguos = match_zoom_to_roster(
            self.zoom_records, self.roster_records, threshold
        )
        self.all_records = resultado
        self.no_encontrados = no_encontrados
        self.ambiguos = ambiguos
        self.mode = "cotejo"
        self.has_pendientes = bool(no_encontrados or ambiguos)

        self._reset_filters(keep_threshold=True)
        self.apply_filters()

        p = sum(1 for r in resultado if r["Asistencia"] == "P")
        a = sum(1 for r in resultado if r["Asistencia"] == "A")
        self.status_text = (
            f"Cotejo listo: {p} 'P' y {a} 'A' de {len(resultado)} socios. "
            f"Sin coincidencia: {len(no_encontrados)} | Ambiguos: {len(ambiguos)}."
        )

    # ------------------------------------------------------------------
    # Filtros, orden y refresco de la tabla
    # ------------------------------------------------------------------
    def _reset_filters(self, keep_threshold=False):
        self.root.ids.search_input.text = ""
        self.root.ids.min_duration_input.text = ""
        if not keep_threshold:
            self.root.ids.threshold_input.text = DEFAULT_THRESHOLD

    @staticmethod
    def _safe_float(text, default):
        text = (text or "").strip().replace(",", ".")
        if not text:
            return default
        try:
            return float(text)
        except ValueError:
            return default

    def apply_filters(self):
        if not self.all_records:
            return

        threshold = self._safe_float(self.root.ids.threshold_input.text, 30.0)
        for record in self.all_records:
            record["Asistencia"] = compute_attendance_flag(
                record.get("Duración (minutos)", 0), threshold
            )

        search_text = self.root.ids.search_input.text.strip().lower()
        min_duration = self._safe_float(self.root.ids.min_duration_input.text, 0.0)

        filtered = []
        for record in self.all_records:
            if record["Duración (minutos)"] < min_duration:
                continue
            if search_text:
                haystack = " ".join([
                    str(record.get("Nombre", "")),
                    str(record.get("Apellido", "")),
                    str(record.get("Sede", "")),
                ]).lower()
                if search_text not in haystack:
                    continue
            filtered.append(record)

        sort_choice = self.root.ids.sort_spinner.text
        if sort_choice == "Duración (mayor a menor)":
            filtered.sort(key=lambda r: r["Duración (minutos)"], reverse=True)
        elif sort_choice == "Duración (menor a mayor)":
            filtered.sort(key=lambda r: r["Duración (minutos)"])
        elif sort_choice == "Nombre (A-Z)":
            filtered.sort(key=lambda r: str(r.get("Nombre", "")).lower())
        elif sort_choice == "Apellido (A-Z)":
            filtered.sort(key=lambda r: str(r.get("Apellido", "")).lower())
        elif sort_choice == "Sede (A-Z)":
            filtered.sort(key=lambda r: str(r.get("Sede", "")).lower())
        elif sort_choice == "Asistencia":
            filtered.sort(key=lambda r: str(r.get("Asistencia", "")))

        self.filtered_records = filtered
        self.has_results = bool(filtered)

        self.root.ids.rv.data = [
            {
                "nombre": r.get("Nombre", ""),
                "apellido": r.get("Apellido", ""),
                "sede": r.get("Sede", ""),
                "duracion": str(r.get("Duración (minutos)", 0)),
                "asistencia": r.get("Asistencia", ""),
            }
            for r in filtered
        ]

        etiqueta = "socios" if self.mode == "cotejo" else "participantes"
        self.count_text = f"Total {etiqueta}: {len(self.all_records)} | Filtrados: {len(filtered)}"

    # ------------------------------------------------------------------
    # Exportación (guarda en almacenamiento privado de la app y comparte)
    # ------------------------------------------------------------------
    def _export_dir(self):
        path = self.user_data_dir
        os.makedirs(path, exist_ok=True)
        return path

    def _share_file(self, filepath, title, subfolder):
        """Guarda una copia del archivo exportado en:
        Download/Asistencia Zoom/<subfolder>/
        del celular (visible con cualquier explorador de archivos, sin
        depender de que el diálogo de compartir se abra correctamente)
        y, además, intenta abrir el diálogo nativo de Android para
        compartir directamente (WhatsApp, Drive, correo, etc.).

        `subfolder` es "Cotejados" (para los exportados de asistencia) o
        "Por revisar" (para los pendientes de revisión).

        Por qué hace falta copiarlo a Download aparte de intentar
        compartir: desde Android 10 en adelante, la carpeta privada de
        la app (`user_data_dir`, algo como
        "/data/user/0/<paquete>/files") NO es visible para ningún
        explorador de archivos ni para otras apps — solo la puede leer
        esta misma app. Si el diálogo de compartir no llega a abrirse,
        el archivo quedaba "guardado" pero inalcanzable. Copiándolo
        también a la carpeta pública Download (usando la API de
        almacenamiento compartido de Android, la única forma permitida
        de escribir ahí desde Android 10+) el archivo queda accesible sí
        o sí, se abra o no el diálogo de compartir."""
        from kivy.utils import platform

        extension = os.path.splitext(filepath)[1].lower()
        mime_type = {
            ".csv": "text/csv",
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        }.get(extension, "*/*")

        shared_uri = None
        if platform == "android":
            shared_uri = self._copy_to_public_downloads(filepath, subfolder)
        saved_to_downloads = shared_uri is not None

        shared_ok = False
        try:
            from plyer import share
            share.share(title=title, filepath=filepath)
            shared_ok = True
        except Exception:
            shared_ok = False

        if shared_ok:
            return

        carpeta_publica = f"Download / {APP_TITLE_FOR_STORAGE} / {subfolder}"
        if saved_to_downloads:
            _show_popup(
                "Archivo guardado correctamente",
                "Se guardó en:\n" + carpeta_publica +
                "\n\ncon el nombre:\n" + os.path.basename(filepath),
                open_uri=shared_uri,
                open_mime=mime_type,
                success=True,
            )
        else:
            _show_popup(
                "No se pudo guardar en Download",
                f"El archivo se guardó en:\n{filepath}\n\n"
                "No se pudo copiarlo a la carpeta Download ni abrir el "
                "diálogo para compartir automáticamente; puedes buscarlo "
                "con un explorador de archivos.",
                success=False,
            )

    def _copy_to_public_downloads(self, filepath, subfolder):
        """Copia `filepath` (que vive en la carpeta privada de la app) a
        Download/Asistencia Zoom/<subfolder>/ del celular, usando la API
        de almacenamiento compartido de Android (MediaStore vía el
        paquete androidstorage4kivy). Esta es la única forma soportada
        de escribir en una carpeta pública desde Android 10 en adelante;
        escribir ahí con un simple open()/os.path como si fuera una
        carpeta común ya no funciona en versiones modernas de Android.
        Devuelve el content:// URI del archivo copiado, siempre como
        texto plano (str) —para poder abrirlo después con "Abrir
        archivo"— o None si algo falló (por ejemplo, en un celular muy
        viejo o si el paquete no se pudo cargar).

        IMPORTANTE: androidstorage4kivy devuelve acá un objeto Uri de
        Android, no un texto. Antes se guardaba tal cual, y eso era la
        causa exacta del error "Invalid instance of 'android/net/Uri'
        passed for a 'java/lang/String'" al tocar "Abrir archivo" (ver
        _open_shared_uri). Convirtiéndolo a texto aquí mismo, apenas se
        recibe, el resto de la app solo necesita trabajar con un String
        normal."""
        try:
            from androidstorage4kivy import SharedStorage
            from jnius import autoclass
            Environment = autoclass("android.os.Environment")
            dest_relpath = f"{subfolder}/{os.path.basename(filepath)}"
            shared_file = SharedStorage().copy_to_shared(
                filepath,
                collection=Environment.DIRECTORY_DOWNLOADS,
                filepath=dest_relpath,
            )
            if shared_file is None:
                return None
            try:
                return shared_file.toString()
            except AttributeError:
                return str(shared_file)
        except Exception:
            return None

    def export_csv(self):
        if not self._month_ready():
            return
        if not self.filtered_records:
            _show_popup("Sin datos", "No hay resultados filtrados para exportar.")
            return
        filename = f"asistencia_{self._month_slug()}.csv"
        filepath = os.path.join(self._export_dir(), filename)
        try:
            export_records_to_csv(self.filtered_records, filepath)
        except Exception as e:
            _show_popup("Error al exportar", str(e), success=False)
            return
        self._share_file(filepath, "Asistencia (CSV)", subfolder="Cotejados")

    def export_excel(self):
        if not self._month_ready():
            return
        if not self.filtered_records:
            _show_popup("Sin datos", "No hay resultados filtrados para exportar.")
            return
        filename = f"asistencia_{self._month_slug()}.xlsx"
        filepath = os.path.join(self._export_dir(), filename)
        try:
            export_to_excel(self.filtered_records, filepath)
        except Exception as e:
            _show_popup("Error al exportar", str(e), success=False)
            return
        self._share_file(filepath, "Asistencia (Excel)", subfolder="Cotejados")

    def export_pendientes(self):
        if not self._month_ready():
            return
        if not self.no_encontrados and not self.ambiguos:
            _show_popup("Sin pendientes", "No hay registros pendientes de revisión.")
            return
        import csv as csv_module
        filename = f"pendientes_{self._month_slug()}.csv"
        filepath = os.path.join(self._export_dir(), filename)
        try:
            with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv_module.DictWriter(
                    f, fieldnames=["Categoría", "Nombre en Zoom", "Duración (minutos)"]
                )
                writer.writeheader()
                for r in self.no_encontrados:
                    writer.writerow({
                        "Categoría": "No encontrado en el listado oficial",
                        "Nombre en Zoom": r.get("Nombre", ""),
                        "Duración (minutos)": r.get("Duración (minutos)", 0),
                    })
                for r in self.ambiguos:
                    writer.writerow({
                        "Categoría": "Coincide con más de un socio (ambiguo)",
                        "Nombre en Zoom": r.get("Nombre", ""),
                        "Duración (minutos)": r.get("Duración (minutos)", 0),
                    })
        except Exception as e:
            _show_popup("Error al exportar", str(e), success=False)
            return
        self._share_file(filepath, "Pendientes de revisión", subfolder="Por revisar")
