import tkinter as tk
from config import COLORS as C, FONT_BODY, FONT_MONO, FONT_HEAD


class StyledFrame(tk.Frame):
    """Frame con fondo de la paleta."""
    def __init__(self, parent, level='surface', **kw):
        super().__init__(parent, bg=C[level], **kw)


class Label(tk.Label):
    def __init__(self, parent, text='', muted=False, accent=False,
                 accent2=False, danger=False, font=None, **kw):
        color = (C['muted'] if muted else
                 C['accent'] if accent else
                 C['accent2'] if accent2 else
                 C['danger'] if danger else
                 C['text'])
        super().__init__(parent, text=text, fg=color,
                         bg=parent['bg'], font=font or FONT_BODY, **kw)


class Entry(tk.Entry):
    """Campo de texto con estilo oscuro."""
    def __init__(self, parent, show=None, width=28, **kw):
        super().__init__(
            parent,
            show=show,
            width=width,
            font=FONT_MONO,
            bg=C['surface2'],
            fg=C['text'],
            insertbackground=C['accent'],
            relief='flat',
            bd=0,
            highlightthickness=1,
            highlightcolor=C['accent'],
            highlightbackground=C['border'],
            **kw
        )

    def get_stripped(self) -> str:
        return self.get().strip()


class Button(tk.Button):
    """Botón primario o secundario."""
    def __init__(self, parent, text='', command=None, secondary=False, danger=False, **kw):
        if danger:
            bg, fg, ab = C['danger'], C['white'], C['danger']
        elif secondary:
            bg, fg, ab = C['surface2'], C['text'], C['border']
        else:
            bg, fg, ab = C['accent'], C['white'], C['accent']

        super().__init__(
            parent, text=text, command=command,
            bg=bg, fg=fg, activebackground=ab, activeforeground=C['white'],
            font=FONT_HEAD, relief='flat', bd=0,
            padx=18, pady=8, cursor='hand2', **kw
        )


class Card(tk.Frame):
    """Contenedor con fondo surface y borde sutil."""
    def __init__(self, parent, **kw):
        super().__init__(
            parent,
            bg=C['surface'],
            highlightthickness=1,
            highlightbackground=C['border'],
            padx=18, pady=14,
            **kw
        )


class Separator(tk.Frame):
    def __init__(self, parent, **kw):
        super().__init__(parent, bg=C['border'], height=1, **kw)


class StatusBar(tk.Label):
    """Barra de estado en la parte inferior."""
    def __init__(self, parent, **kw):
        super().__init__(
            parent, text='', anchor='w',
            bg=C['surface'], fg=C['muted'],
            font=FONT_MONO, padx=12, pady=6, **kw
        )

    def ok(self, msg):
        self.config(text='✔  ' + msg, fg=C['accent2'])

    def err(self, msg):
        self.config(text='✖  ' + msg, fg=C['danger'])

    def info(self, msg):
        self.config(text='●  ' + msg, fg=C['accent'])

    def clear(self):
        self.config(text='')


def field(parent, label_text: str, entry_widget: tk.Widget, pady=6):
    """Etiqueta + campo apilados verticalmente."""
    tk.Label(
        parent, text=label_text.upper(),
        fg=C['muted'], bg=parent['bg'],
        font=('Segoe UI', 8, 'bold')
    ).pack(anchor='w', pady=(pady, 2))
    entry_widget.pack(fill='x', ipady=5)
