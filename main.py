# -*- coding: utf-8 -*-
"""
main.py — punto de entrada blindado
=====================================
Este archivo es intencionalmente muy simple: su único trabajo es lanzar
la app real (definida en app_core.py) y, si CUALQUIER cosa falla al
iniciar —incluso un error de importación de alguna librería, no solo un
error dentro de la interfaz— capturarlo y mostrarlo como texto en la
propia pantalla del celular.

Por qué existe esto:
    En celulares Honor/Huawei (y varios otros fabricantes chinos), el
    sistema bloquea el acceso al log (logcat) para apps de terceros, así
    que si la app se cierra sola no hay forma de ver el error con las
    herramientas normales de depuración. Esta pantalla de emergencia
    permite ver el error directamente con los propios ojos, sacándole
    una foto a la pantalla, sin necesidad de cable USB ni comandos.
"""

import traceback


def _launch_real_app():
    # La importación se hace DENTRO de la función (no arriba del archivo)
    # a propósito: así, si algo falla incluso al importar app_core.py o
    # alguna de sus dependencias (por ejemplo, si openpyxl no se hubiera
    # empaquetado bien dentro del APK), el error también queda atrapado
    # por el try/except de más abajo, en vez de tumbar la app antes de
    # que alcancemos a mostrar nada en pantalla.
    from app_core import ZoomAttendanceMobileApp
    ZoomAttendanceMobileApp().run()


def _show_crash_screen(error_text: str) -> None:
    """Muestra el error como texto en pantalla completa, en vez de dejar
    que la app se cierre silenciosamente sin dejar rastro visible."""
    from kivy.app import App
    from kivy.core.window import Window
    from kivy.uix.label import Label
    from kivy.uix.scrollview import ScrollView

    class CrashApp(App):
        def build(self):
            Window.clearcolor = (0.05, 0.05, 0.05, 1)
            scroll = ScrollView()
            label = Label(
                text=(
                    "La app encontro un error al iniciar.\n"
                    "Por favor saca una foto a esta pantalla completa\n"
                    "(usa el scroll si no entra todo) y comparte la foto\n"
                    "para poder corregirlo.\n"
                    "--------------------------------------------------\n\n"
                    + error_text
                ),
                size_hint_y=None,
                size_hint_x=1,
                text_size=(Window.width - 40, None),
                halign="left",
                valign="top",
                color=(1, 0.55, 0.55, 1),
                font_size="14sp",
                padding=(20, 20),
            )
            label.bind(
                texture_size=lambda instance, value: setattr(instance, "height", value[1])
            )
            scroll.add_widget(label)
            return scroll

    CrashApp().run()


if __name__ == "__main__":
    try:
        _launch_real_app()
    except BaseException:
        error_text = traceback.format_exc()
        try:
            _show_crash_screen(error_text)
        except BaseException:
            # Si ni siquiera Kivy pudo mostrar la pantalla de emergencia,
            # no queda más alternativa que intentar dejarlo impreso por si
            # algún día se logra acceder al log del sistema.
            print("ERROR FATAL AL INICIAR LA APP:")
            print(error_text)
            raise
