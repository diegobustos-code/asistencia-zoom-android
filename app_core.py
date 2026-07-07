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

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.properties import BooleanProperty, ListProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.label import Label

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
    background_normal: ""
    background_down: ""
    background_disabled_normal: ""
    background_color: 0.20, 0.45, 0.75, 1
    color: 1, 1, 1, 1
    bold: True
    font_size: "15sp"

<StyledInput@TextInput>:
    background_normal: ""
    background_active: ""
    background_color: 1, 1, 1, 1
    foreground_color: 0.15, 0.15, 0.15, 1
    hint_text_color: 0.55, 0.55, 0.55, 1
    cursor_color: 0.15, 0.15, 0.15, 1
    padding: dp(10), dp(10)
    font_size: "14sp"

<RowWidget>:
    orientation: "horizontal"
    size_hint_y: None
    height: dp(48)
    padding: dp(6), dp(2)
    spacing: dp(4)
    canvas.before:
        Color:
            rgba: self.bgcolor
        Rectangle:
            pos: self.pos
            size: self.size
        Color:
            rgba: 0.86, 0.87, 0.89, 1
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
    orientation: "vertical"
    padding: dp(10)
    spacing: dp(8)

    BoxLayout:
        size_hint_y: None
        height: dp(48)
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
            background_color: (0.62, 0.65, 0.68, 1) if self.disabled else (0.16, 0.62, 0.42, 1)
            on_release: app.on_cotejar()

    Label:
        id: status_label
        text: app.status_text
        size_hint_y: None
        height: dp(44)
        text_size: self.width, None
        halign: "left"
        valign: "middle"
        color: 0.18, 0.20, 0.24, 1
        font_size: "13sp"

    BoxLayout:
        size_hint_y: None
        height: dp(44)
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
        height: dp(44)
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
        height: dp(32)
        canvas.before:
            Color:
                rgba: 0.14, 0.22, 0.34, 1
            Rectangle:
                pos: self.pos
                size: self.size
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
            RecycleBoxLayout:
                default_size: None, dp(48)
                default_size_hint: 1, None
                size_hint_y: None
                height: self.minimum_height
                orientation: "vertical"

    Label:
        id: count_label
        text: app.count_text
        size_hint_y: None
        height: dp(28)
        color: 0.18, 0.20, 0.24, 1
        font_size: "12sp"

    BoxLayout:
        size_hint_y: None
        height: dp(50)
        spacing: dp(6)
        AppButton:
            text: "Exportar CSV"
            disabled: not app.has_results
            background_color: (0.62, 0.65, 0.68, 1) if self.disabled else (0.12, 0.55, 0.60, 1)
            on_release: app.export_csv()
        AppButton:
            text: "Exportar Excel"
            disabled: not app.has_results
            background_color: (0.62, 0.65, 0.68, 1) if self.disabled else (0.12, 0.55, 0.60, 1)
            on_release: app.export_excel()
        AppButton:
            text: "Pendientes"
            disabled: not app.has_pendientes
            background_color: (0.62, 0.65, 0.68, 1) if self.disabled else (0.85, 0.55, 0.15, 1)
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


def _show_popup(title: str, message: str) -> None:
    box = BoxLayout(orientation="vertical", padding=10, spacing=10)
    box.add_widget(Label(text=message))
    from kivy.uix.button import Button
    close_btn = Button(text="Cerrar", size_hint_y=None, height=44)
    box.add_widget(close_btn)
    popup = Popup(title=title, content=box, size_hint=(0.9, 0.6))
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
        return Builder.load_string(KV)

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
            _show_popup("Error", f"No se pudo abrir el selector de archivos:\n{e}")

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
            _show_popup("Error", f"No se pudo abrir el selector de archivos:\n{e}")

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
            _show_popup("Error al procesar el CSV", str(e))
            return
        except Exception as e:
            _show_popup("Error inesperado", str(e))
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
            _show_popup("Error al procesar el listado de socios", str(e))
            return
        except Exception as e:
            _show_popup("Error inesperado", str(e))
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

    def _share_file(self, filepath, title):
        """Guarda una copia del archivo exportado en la carpeta PÚBLICA
        'Download' del celular (visible con cualquier explorador de
        archivos, sin depender de que el diálogo de compartir se abra
        correctamente) y, además, intenta abrir el diálogo nativo de
        Android para compartir directamente (WhatsApp, Drive, correo,
        etc.).

        Por qué hace falta copiarlo a Download aparte de intentar
        compartir: desde Android 10 en adelante, la carpeta privada de
        la app (`user_data_dir`, algo como
        "/data/user/0/<paquete>/files") NO es visible para ningún
        explorador de archivos ni para otras apps — solo la puede leer
        esta misma app. Si el diálogo de compartir no llega a abrirse
        (como pasó recién), el archivo quedaba "guardado" pero
        inalcanzable. Copiándolo también a la carpeta pública Download
        (usando la API de almacenamiento compartido de Android, la
        única forma permitida de escribir ahí desde Android 10+) el
        archivo queda accesible sí o sí, se abra o no el diálogo de
        compartir."""
        from kivy.utils import platform

        saved_to_downloads = False
        if platform == "android":
            saved_to_downloads = self._copy_to_public_downloads(filepath)

        shared_ok = False
        try:
            from plyer import share
            share.share(title=title, filepath=filepath)
            shared_ok = True
        except Exception:
            shared_ok = False

        if shared_ok:
            return

        if saved_to_downloads:
            _show_popup(
                "Archivo guardado",
                "El archivo se guardó en la carpeta 'Download' de tu "
                "celular, con el nombre:\n" + os.path.basename(filepath) +
                "\n\nNo se pudo abrir el diálogo para compartir "
                "automáticamente, pero puedes encontrarlo con cualquier "
                "explorador de archivos, dentro de la carpeta Download.",
            )
        else:
            _show_popup(
                "Archivo generado",
                f"El archivo se guardó en:\n{filepath}\n\n"
                "No se pudo copiarlo a la carpeta Download ni abrir el "
                "diálogo para compartir automáticamente; puedes buscarlo "
                "con un explorador de archivos.",
            )

    def _copy_to_public_downloads(self, filepath):
        """Copia `filepath` (que vive en la carpeta privada de la app) a
        la carpeta pública 'Download' del celular, usando la API de
        almacenamiento compartido de Android (MediaStore vía el paquete
        androidstorage4kivy). Esta es la única forma soportada de
        escribir en una carpeta pública desde Android 10 en adelante;
        escribir ahí con un simple open()/os.path como si fuera una
        carpeta común ya no funciona en versiones modernas de Android.
        Devuelve True si la copia se hizo con éxito, False si algo
        falló (por ejemplo, en un celular muy viejo o si el paquete no
        se pudo cargar)."""
        try:
            from androidstorage4kivy import SharedStorage
            from jnius import autoclass
            Environment = autoclass("android.os.Environment")
            shared_file = SharedStorage().copy_to_shared(
                filepath, collection=Environment.DIRECTORY_DOWNLOADS
            )
            return shared_file is not None
        except Exception:
            return False

    def export_csv(self):
        if not self.filtered_records:
            _show_popup("Sin datos", "No hay resultados filtrados para exportar.")
            return
        filepath = os.path.join(self._export_dir(), "asistencia_filtrada.csv")
        try:
            export_records_to_csv(self.filtered_records, filepath)
        except Exception as e:
            _show_popup("Error al exportar", str(e))
            return
        self._share_file(filepath, "Asistencia (CSV)")

    def export_excel(self):
        if not self.filtered_records:
            _show_popup("Sin datos", "No hay resultados filtrados para exportar.")
            return
        filepath = os.path.join(self._export_dir(), "asistencia_filtrada.xlsx")
        try:
            export_to_excel(self.filtered_records, filepath)
        except Exception as e:
            _show_popup("Error al exportar", str(e))
            return
        self._share_file(filepath, "Asistencia (Excel)")

    def export_pendientes(self):
        if not self.no_encontrados and not self.ambiguos:
            _show_popup("Sin pendientes", "No hay registros pendientes de revisión.")
            return
        import csv as csv_module
        filepath = os.path.join(self._export_dir(), "pendientes_de_revision.csv")
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
            _show_popup("Error al exportar", str(e))
            return
        self._share_file(filepath, "Pendientes de revisión")
