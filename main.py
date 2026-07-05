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
from kivy.lang import Builder
from kivy.properties import ListProperty, StringProperty
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
<RowWidget>:
    orientation: "horizontal"
    size_hint_y: None
    height: dp(46)
    padding: dp(4)
    spacing: dp(4)
    canvas.before:
        Color:
            rgba: self.bgcolor
        Rectangle:
            pos: self.pos
            size: self.size
    Label:
        text: root.nombre
        color: 0, 0, 0, 1
        size_hint_x: 0.28
        text_size: self.size
        halign: "left"
        valign: "middle"
        shorten: True
    Label:
        text: root.apellido
        color: 0, 0, 0, 1
        size_hint_x: 0.28
        text_size: self.size
        halign: "left"
        valign: "middle"
        shorten: True
    Label:
        text: root.sede
        color: 0, 0, 0, 1
        size_hint_x: 0.22
        text_size: self.size
        halign: "left"
        valign: "middle"
        shorten: True
    Label:
        text: root.duracion
        color: 0, 0, 0, 1
        size_hint_x: 0.12
        text_size: self.size
        halign: "right"
        valign: "middle"
    Label:
        text: root.asistencia
        bold: True
        color: 0, 0, 0, 1
        size_hint_x: 0.10
        text_size: self.size
        halign: "center"
        valign: "middle"

BoxLayout:
    orientation: "vertical"
    padding: dp(8)
    spacing: dp(6)

    BoxLayout:
        size_hint_y: None
        height: dp(44)
        spacing: dp(6)
        Button:
            text: "Abrir CSV Zoom"
            on_release: app.open_zoom_dialog()
        Button:
            text: "Abrir Socios (Excel)"
            on_release: app.open_roster_dialog()
        Button:
            text: "Cotejar"
            disabled: not (app.zoom_loaded and app.roster_loaded)
            on_release: app.on_cotejar()

    Label:
        id: status_label
        text: app.status_text
        size_hint_y: None
        height: dp(40)
        text_size: self.width, None
        halign: "left"
        valign: "middle"
        color: 0.2, 0.2, 0.2, 1

    BoxLayout:
        size_hint_y: None
        height: dp(40)
        spacing: dp(6)
        TextInput:
            id: search_input
            hint_text: "Buscar nombre / apellido / sede"
            multiline: False
            on_text_validate: app.apply_filters()
        TextInput:
            id: min_duration_input
            hint_text: "Min. min"
            multiline: False
            input_filter: "float"
            size_hint_x: 0.22
            on_text_validate: app.apply_filters()
        TextInput:
            id: threshold_input
            hint_text: "Umbral P"
            text: "30"
            multiline: False
            input_filter: "float"
            size_hint_x: 0.22
            on_text_validate: app.apply_filters()

    BoxLayout:
        size_hint_y: None
        height: dp(40)
        spacing: dp(6)
        Spinner:
            id: sort_spinner
            text: "Duración (mayor a menor)"
            values: ["Duración (mayor a menor)", "Duración (menor a mayor)", "Nombre (A-Z)", "Apellido (A-Z)", "Sede (A-Z)", "Asistencia"]
            on_text: app.apply_filters()
        Button:
            text: "Aplicar filtro"
            size_hint_x: 0.35
            on_release: app.apply_filters()

    BoxLayout:
        size_hint_y: None
        height: dp(28)
        Label:
            text: "Nombre"
            bold: True
            size_hint_x: 0.28
        Label:
            text: "Apellido"
            bold: True
            size_hint_x: 0.28
        Label:
            text: "Sede"
            bold: True
            size_hint_x: 0.22
        Label:
            text: "Min."
            bold: True
            size_hint_x: 0.12
        Label:
            text: "Asist."
            bold: True
            size_hint_x: 0.10

    RecycleView:
        id: rv
        viewclass: "RowWidget"
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
        height: dp(28)
        color: 0.2, 0.2, 0.2, 1

    BoxLayout:
        size_hint_y: None
        height: dp(46)
        spacing: dp(6)
        Button:
            text: "Exportar CSV"
            disabled: not app.has_results
            on_release: app.export_csv()
        Button:
            text: "Exportar Excel"
            disabled: not app.has_results
            on_release: app.export_excel()
        Button:
            text: "Pendientes"
            disabled: not app.has_pendientes
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
    zoom_loaded = False
    roster_loaded = False
    has_results = False
    has_pendientes = False

    def build(self):
        self.zoom_records = []
        self.roster_records = []
        self.all_records = []
        self.filtered_records = []
        self.no_encontrados = []
        self.ambiguos = []
        self.mode = "zoom"
        return Builder.load_string(KV)

    # ------------------------------------------------------------------
    # Selección de archivos (usa el selector nativo de Android/escritorio)
    # ------------------------------------------------------------------
    def open_zoom_dialog(self):
        from plyer import filechooser
        try:
            filechooser.open_file(on_selection=self._on_zoom_selected)
        except Exception as e:
            _show_popup("Error", f"No se pudo abrir el selector de archivos:\n{e}")

    def open_roster_dialog(self):
        from plyer import filechooser
        try:
            filechooser.open_file(on_selection=self._on_roster_selected)
        except Exception as e:
            _show_popup("Error", f"No se pudo abrir el selector de archivos:\n{e}")

   def _on_zoom_selected(self, selection):
        if not selection or not isinstance(selection, list):
            return
        filepath = selection[0]
        if os.path.exists(filepath):
            Clock.schedule_once(lambda dt: self._load_zoom_file(filepath))
        else:
            _show_popup("Error", "No se pudo acceder al archivo seleccionado.")

    def _on_roster_selected(self, selection):
        if not selection or not isinstance(selection, list):
            return
        filepath = selection[0]
        if os.path.exists(filepath):
            Clock.schedule_once(lambda dt: self._load_roster_file(filepath))
        else:
            _show_popup("Error", "No se pudo acceder al archivo seleccionado.")

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
        try:
            from plyer import share
            share.share(title=title, filepath=filepath)
        except Exception:
            _show_popup(
                "Archivo generado",
                f"El archivo se guardó en:\n{filepath}\n\n"
                "No se pudo abrir el diálogo para compartir automáticamente; "
                "puedes buscarlo con un explorador de archivos.",
            )

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


if __name__ == "__main__":
    ZoomAttendanceMobileApp().run()
