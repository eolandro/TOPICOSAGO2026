import base64
import hashlib
import hmac
import os
import sqlite3
import struct
import time
import tkinter as tk
from tkinter import ttk
from urllib.parse import quote
from PIL import Image, ImageTk
import qrcode

import database as db
from config import APP_NAME

M = {
    'bg':      '#090910',   # negro profundo
    'panel':   '#0f0f1a',   # gris casi negro
    'card':    '#16162a',   # gris oscuro — tarjeta principal
    'card2':   '#1e1e35',   # gris medio — inputs, filas
    'card3':   '#252545',   # gris claro oscuro — hover / totp panel
    'border':  '#2e2e55',   # borde reposo
    'focus':   '#5588e8',   # azul foco
    'line':    '#202040',   # separadores
    'dim':     '#55558a',   # texto apagado
    'mid':     '#8888bb',   # texto secundario
    'text':    '#d8d8f0',   # texto principal
    'accent':  '#5588e8',   # azul primario
    'acc2':    '#3a6fd8',   # azul hover botón
    'acc_txt': '#ffffff',
    'danger':  '#dd4444',
    'ok':      '#5588e8',
    'amber':   '#cc8833',
    'green':   '#33bb77',   # éxito TOTP
}

PAD     = 40
IPAD    = 8
F_TITLE = ('Segoe UI', 18, 'bold')
F_HEAD  = ('Segoe UI', 12, 'bold')
F_BODY  = ('Segoe UI', 10)
F_SMALL = ('Segoe UI', 8)
F_LABEL = ('Segoe UI', 8, 'bold')
F_MONO  = ('Courier New', 10)
F_CODE  = ('Courier New', 36, 'bold')
F_BTN   = ('Segoe UI', 10, 'bold')
F_DIGIT = ('Segoe UI', 26, 'bold')

def _totp_random_base32(n: int = 20) -> str:
    return base64.b32encode(os.urandom(n)).decode()

def _totp_generate(secret: str, ts: float | None = None) -> str:
    key  = base64.b32decode(secret, casefold=True)
    cnt  = int((ts or time.time()) // 30)
    msg  = struct.pack('>Q', cnt)
    h    = hmac.new(key, msg, digestmod=hashlib.sha1).digest()
    off  = h[-1] & 0x0F
    code = struct.unpack('>I', h[off:off+4])[0] & 0x7FFFFFFF
    return str(code % 1_000_000).zfill(6)

def _totp_verify(secret: str, code: str, window: int = 1) -> bool:
    now = time.time()
    return any(
        hmac.compare_digest(_totp_generate(secret, now + s*30), code)
        for s in range(-window, window+1)
    )

def _totp_uri(secret: str, username: str, issuer: str) -> str:
    label = quote(f'{issuer}:{username}')
    return (f'otpauth://totp/{label}?secret={secret}'
            f'&issuer={quote(issuer)}&algorithm=SHA1&digits=6&period=30')

class ScrollableFrame(tk.Frame):
    def __init__(self, parent, bg_key='panel', **kw):
        bg = M[bg_key]
        super().__init__(parent, bg=bg, **kw)
        self._cv = tk.Canvas(self, bg=bg, highlightthickness=0)
        self._sb = ttk.Scrollbar(self, orient='vertical', command=self._cv.yview)
        self._cv.configure(yscrollcommand=self._sb.set)
        self._sb.pack(side='right', fill='y')
        self._cv.pack(side='left', fill='both', expand=True)
        self.inner = tk.Frame(self._cv, bg=bg)
        self._win  = self._cv.create_window((0, 0), window=self.inner, anchor='nw')
        self.inner.bind('<Configure>', lambda _: self._cv.configure(
            scrollregion=self._cv.bbox('all')))
        self._cv.bind('<Configure>', lambda e: self._cv.itemconfig(
            self._win, width=e.width))
        self._cv.bind_all('<MouseWheel>', lambda e: self._cv.yview_scroll(
            int(-e.delta / 120), 'units'))

    def bottom(self):
        self.update_idletasks()
        self._cv.yview_moveto(1.0)

def _section_title(parent, title: str, subtitle: str = '', bg='panel'):
    tk.Label(parent, text=title, fg=M['text'], bg=M[bg],
             font=F_TITLE).pack(anchor='w', padx=PAD, pady=(36, 0))
    if subtitle:
        tk.Label(parent, text=subtitle, fg=M['dim'], bg=M[bg],
                 font=F_SMALL).pack(anchor='w', padx=PAD, pady=(2, 0))


def _divider(parent, padx=PAD, pady=18, bg='line'):
    tk.Frame(parent, bg=M[bg], height=1).pack(fill='x', padx=padx, pady=pady)


def _lbl(parent, text, key='mid', font=None, **kw):
    tk.Label(parent, text=text, fg=M[key], bg=parent['bg'],
             font=font or F_LABEL, **kw)


def _field_label(parent, text: str, required=False):
    row = tk.Frame(parent, bg=parent['bg']); row.pack(anchor='w', pady=(12, 3))
    tk.Label(row, text=text.upper(), fg=M['dim'], bg=parent['bg'],
             font=F_LABEL).pack(side='left')
    if required:
        tk.Label(row, text=' *', fg=M['accent'], bg=parent['bg'],
                 font=F_LABEL).pack(side='left')


def _input(parent, show=None, width=28, disabled=False):
    wrap = tk.Frame(parent, bg=M['border'], padx=1, pady=1)
    wrap.pack(fill='x')
    e = tk.Entry(wrap, show=show, width=width, font=F_MONO,
                 bg=M['card2'], fg=M['text'],
                 insertbackground=M['accent'],
                 relief='flat', bd=0, highlightthickness=0,
                 disabledbackground=M['card2'], disabledforeground=M['dim'],
                 state='disabled' if disabled else 'normal')
    e.pack(fill='x', ipady=IPAD, padx=8)

    def _fi(_):  wrap.config(bg=M['focus'])
    def _fo(_):  wrap.config(bg=M['border'])
    if not disabled:
        e.bind('<FocusIn>',  _fi)
        e.bind('<FocusOut>', _fo)
    e.get_stripped = lambda: e.get().strip()
    e._wrap = wrap
    return e


def _btn_solid(parent, text, cmd, width=None):
    kw = {'width': width} if width else {}
    return tk.Button(parent, text=text, command=cmd,
                     bg=M['accent'], fg=M['acc_txt'],
                     activebackground=M['acc2'], activeforeground=M['acc_txt'],
                     font=F_BTN, relief='flat', bd=0,
                     padx=20, pady=8, cursor='hand2', **kw)


def _btn_ghost(parent, text, cmd, bg_key='panel'):
    return tk.Button(parent, text=text, command=cmd,
                     fg=M['mid'], bg=M[bg_key],
                     activeforeground=M['text'], activebackground=M[bg_key],
                     font=F_BODY, relief='flat', bd=0,
                     padx=0, pady=5, cursor='hand2')


def _status_lbl(parent, bg_key='panel'):
    lbl = tk.Label(parent, text='', fg=M['dim'], bg=M[bg_key],
                   font=('Segoe UI', 9), anchor='w', pady=3)
    lbl.ok  = lambda m: lbl.config(text=f'✓  {m}', fg=M['ok'])
    lbl.err = lambda m: lbl.config(text=f'✕  {m}', fg=M['danger'])
    lbl.clr = lambda:   lbl.config(text='')
    return lbl


def _tag(parent, text, color_key='accent', bg_key='card2'):
    f = tk.Frame(parent, bg=M[bg_key], padx=8, pady=3)
    tk.Label(f, text=text, fg=M[color_key], bg=M[bg_key],
             font=('Segoe UI', 7, 'bold')).pack()
    return f

class LiveTOTPWidget(tk.Frame):
    """Muestra el código TOTP actualizado en tiempo real con barra de progreso."""
    PERIOD = 30

    def __init__(self, parent, secret: str, compact: bool = False, **kw):
        super().__init__(parent, bg=M['card2'], **kw)
        self._secret   = secret
        self._compact  = compact
        self._timer_id = None
        self._last_win = -1
        self._build()
        self._tick()

    def _build(self):
        bg = M['card2']

        hdr = tk.Frame(self, bg=bg, padx=16, pady=10)
        hdr.pack(fill='x')
        tk.Label(hdr, text='CÓDIGO EN VIVO', fg=M['dim'],
                 bg=bg, font=F_LABEL).pack(side='left')
        self._dot = tk.Label(hdr, text='● LIVE', fg=M['accent'],
                              bg=bg, font=('Segoe UI', 7, 'bold'))
        self._dot.pack(side='right')

        track = tk.Frame(self, bg=M['line'], height=4)
        track.pack(fill='x'); track.pack_propagate(False)
        self._bar = tk.Frame(track, bg=M['accent'], height=4)
        self._bar.place(x=0, y=0, relwidth=1.0, height=4)
        self._track = track

        digit_wrap = tk.Frame(self, bg=bg, pady=16)
        digit_wrap.pack()
        self._dlabels = []
        for grp in range(2):
            gf = tk.Frame(digit_wrap, bg=bg); gf.pack(side='left')
            for _ in range(3):
                lbl = tk.Label(gf, text='—', font=F_CODE,
                               fg=M['accent'], bg=bg, width=2, anchor='center')
                lbl.pack(side='left', padx=1)
                self._dlabels.append(lbl)
            if grp == 0:
                tk.Label(digit_wrap, text=' · ', fg=M['dim'],
                         bg=bg, font=('Segoe UI', 24)).pack(side='left')

        foot = tk.Frame(self, bg=bg, padx=16, pady=8)
        foot.pack(fill='x')
        self._ctx = tk.Label(foot, text='', fg=M['dim'], bg=bg, font=F_SMALL)
        self._ctx.pack(side='left')
        self._sec = tk.Label(foot, text='', fg=M['dim'], bg=bg, font=('Segoe UI', 8, 'bold'))
        self._sec.pack(side='right')

    def _tick(self):
        if not self.winfo_exists(): return
        now  = time.time()
        rem  = self.PERIOD - (int(now) % self.PERIOD)
        win  = int(now) // self.PERIOD
        code = _totp_generate(self._secret)
        dang = rem <= 5
        col  = M['danger'] if dang else M['accent']

        if win != self._last_win:
            self._flash(code, col); self._last_win = win
        else:
            self._set(code, col)

        self.update_idletasks()
        w = self._track.winfo_width()
        if w > 4:
            bw = max(int(w * rem / self.PERIOD), 3)
            self._bar.place(x=0, y=0, width=bw, height=4)
        self._bar.config(bg=col)
        self._sec.config(text=f'{rem:02d}s',
                         fg=M['danger'] if dang else M['mid'])
        self._ctx.config(text=f'ventana #{win % 10000:04d}')
        self._timer_id = self.after(500, self._tick)

    def _set(self, code, color):
        for i, lbl in enumerate(self._dlabels):
            lbl.config(text=code[i], fg=color)

    def _flash(self, code, final):
        self._set(code, M['amber'])
        self._dot.config(fg=M['amber'])
        self.after(350, lambda: [self._set(code, final),
                                  self._dot.config(fg=M['accent'])])

    def stop(self):
        if self._timer_id:
            self.after_cancel(self._timer_id); self._timer_id = None

    def destroy(self):
        self.stop(); super().destroy()

class BaseView(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=M['panel'])

    def clear(self):
        for w in self.winfo_children(): w.destroy()

class RegisterView(BaseView):
    def __init__(self, parent):
        super().__init__(parent)
        self._live = None
        self._build()

    def _build(self):
        self.clear(); self._live = None
        self._scroll = ScrollableFrame(self)
        self._scroll.pack(fill='both', expand=True)
        p = self._scroll.inner

        _section_title(p, 'Nuevo usuario', 'Contraseña cifrada con bcrypt · 2FA con TOTP (RFC 6238)')
        _divider(p)

        f = tk.Frame(p, bg=M['panel']); f.pack(fill='x', padx=PAD)

        _field_label(f, 'ID de usuario (asignado al registrar)')
        self.ent_id = _input(f, width=12, disabled=True)

        row   = tk.Frame(f, bg=M['panel']); row.pack(fill='x')
        left  = tk.Frame(row, bg=M['panel']); left.pack(side='left', fill='x', expand=True, padx=(0, 12))
        right = tk.Frame(row, bg=M['panel']); right.pack(side='left', fill='x', expand=True)
        _field_label(left,  'Nombre de usuario', required=True)
        self.ent_user = _input(left, width=20)
        _field_label(right, 'Correo electrónico', required=True)
        self.ent_mail = _input(right, width=24)

        _field_label(f, 'Contraseña', required=True)
        self.ent_pass = _input(f, show='•')
        tk.Label(f, text='Mínimo 8 caracteres, al menos un número. Hash bcrypt (rounds=12).',
                 fg=M['dim'], bg=M['panel'], font=F_SMALL).pack(anchor='w', pady=(2, 0))
        _field_label(f, 'Confirmar contraseña', required=True)
        self.ent_pass2 = _input(f, show='•')

        _divider(f, padx=0, pady=16)
        tog = tk.Frame(f, bg=M['panel']); tog.pack(fill='x')
        self.var_2fa = tk.BooleanVar(value=False)
        ck = tk.Checkbutton(
            tog, text='  Activar autenticación de dos factores (TOTP)',
            variable=self.var_2fa, onvalue=True, offvalue=False,
            bg=M['panel'], fg=M['text'], selectcolor=M['card2'],
            activebackground=M['panel'], activeforeground=M['text'],
            font=F_BODY, cursor='hand2'
        )
        ck.pack(anchor='w')
        tk.Label(tog, text='  Compatible con Google Authenticator, Microsoft Authenticator y Aegis.',
                 fg=M['dim'], bg=M['panel'], font=F_SMALL).pack(anchor='w', pady=(2, 0))

        _divider(f, padx=0, pady=16)

        btn_row = tk.Frame(f, bg=M['panel']); btn_row.pack(anchor='w')
        _btn_solid(btn_row, '  Registrar usuario  →', self._register).pack(side='left')

        self.status = _status_lbl(p)
        self.status.pack(anchor='w', padx=PAD, pady=(8, 4))

    def _register(self):
        username   = self.ent_user.get_stripped()
        correo     = self.ent_mail.get_stripped().lower()
        password   = self.ent_pass.get()
        password2  = self.ent_pass2.get()
        enable_2fa = self.var_2fa.get()

        if not username or not correo or not password:
            self.status.err('Completa todos los campos requeridos.'); return
        if '@' not in correo or '.' not in correo.split('@')[-1]:
            self.status.err('El correo no es válido.'); return
        if len(password) < 8:
            self.status.err('La contraseña debe tener al menos 8 caracteres.'); return
        if not any(c.isdigit() for c in password):
            self.status.err('La contraseña debe incluir al menos un número.'); return
        if password != password2:
            self.status.err('Las contraseñas no coinciden.'); return

        try:
            uid = db.crear_usuario(username, correo, password)
        except sqlite3.IntegrityError as e:
            campo = 'correo' if 'correo' in str(e) else 'nombre de usuario'
            self.status.err(f'El {campo} ya está registrado.'); return

        self.ent_id._wrap.config(bg=M['border'])
        self.ent_id.config(state='normal')
        self.ent_id.delete(0, 'end')
        self.ent_id.insert(0, str(uid))
        self.ent_id.config(state='disabled')

        if enable_2fa:
            seed = _totp_random_base32()
            db.guardar_semilla(uid, seed)
            self.status.ok(f'Usuario #{uid} registrado — 2FA activado.')
            self._show_qr(username, uid, seed)
        else:
            self.status.ok(f'Usuario #{uid} — {username} — registrado. (Sin 2FA)')

    def _show_qr(self, username, uid, seed):
        p = self._scroll.inner
        if hasattr(self, '_qr_sec') and self._qr_sec.winfo_exists():
            self._qr_sec.destroy()
        if self._live:
            self._live.stop(); self._live = None

        uri = _totp_uri(seed, username, APP_NAME)
        img = qrcode.make(uri).resize((180, 180), Image.NEAREST)
        self._qr_img = ImageTk.PhotoImage(img)

        self._qr_sec = tk.Frame(p, bg=M['panel'])
        self._qr_sec.pack(fill='x', padx=PAD, pady=(24, 28))
        s = self._qr_sec

        # ────────────────────────────── Tarjeta TOTP config ──────────────────────────────
        c_wrap = tk.Frame(s, bg=M['border'], padx=1, pady=1); c_wrap.pack(fill='x')
        card   = tk.Frame(c_wrap, bg=M['card']); card.pack(fill='x')

        chdr = tk.Frame(card, bg=M['card'], padx=20, pady=12); chdr.pack(fill='x')
        tk.Label(chdr, text='Configuración TOTP', fg=M['text'],
                 bg=M['card'], font=F_HEAD).pack(side='left')
        tk.Label(chdr, text='● 2FA ACTIVO', fg=M['accent'],
                 bg=M['card'], font=('Segoe UI', 7, 'bold')).pack(side='right')
        tk.Frame(card, bg=M['line'], height=1).pack(fill='x')

        body = tk.Frame(card, bg=M['card'], padx=20, pady=18); body.pack(fill='x')

        # Columna izquierda: QR
        lc = tk.Frame(body, bg=M['card']); lc.pack(side='left', anchor='n', padx=(0, 24))
        tk.Label(lc, text='1 · Escanea con tu autenticadora',
                 fg=M['mid'], bg=M['card'], font=F_SMALL).pack(anchor='w', pady=(0, 8))
        tk.Label(lc, image=self._qr_img, bg=M['border'], padx=5, pady=5).pack()
        tk.Label(lc, text='Google · Microsoft · Aegis',
                 fg=M['dim'], bg=M['card'], font=F_SMALL).pack(pady=(5, 0))

        # Columna derecha: secreto + URI + aviso
        rc = tk.Frame(body, bg=M['card']); rc.pack(side='left', fill='x', expand=True, anchor='n')

        tk.Label(rc, text='2 · Secreto TOTP — Base32',
                 fg=M['mid'], bg=M['card'], font=F_SMALL).pack(anchor='w', pady=(0, 5))
        sw = tk.Frame(rc, bg=M['border'], padx=1, pady=1); sw.pack(fill='x')
        si = tk.Frame(sw, bg=M['card2']); si.pack(fill='x')
        sr = tk.Frame(si, bg=M['card2']); sr.pack(fill='x')
        tk.Label(sr, text=seed, fg=M['accent'], bg=M['card2'],
                 font=('Courier New', 9, 'bold'), padx=10, pady=8,
                 wraplength=280, justify='left').pack(side='left', fill='x', expand=True)

        def _copy():
            s.clipboard_clear(); s.clipboard_append(seed)
            btn_cp.config(text='Copiado ✓', fg=M['ok'])
            s.after(1800, lambda: btn_cp.config(text='Copiar', fg=M['dim']))

        btn_cp = tk.Button(sr, text='Copiar', command=_copy,
                           fg=M['dim'], bg=M['card2'],
                           activeforeground=M['accent'], activebackground=M['card2'],
                           font=F_SMALL, relief='flat', bd=0, padx=10, cursor='hand2')
        btn_cp.pack(side='right', pady=3)

        tk.Label(rc, text='3 · URI otpauth://', fg=M['mid'],
                 bg=M['card'], font=F_SMALL).pack(anchor='w', pady=(12, 5))
        uw = tk.Frame(rc, bg=M['border'], padx=1, pady=1); uw.pack(fill='x')
        tk.Label(uw, text=uri, fg=M['dim'], bg=M['card2'],
                 font=('Courier New', 7), padx=10, pady=6,
                 wraplength=280, justify='left').pack(anchor='w', fill='x')

        # Aviso ID
        tk.Frame(rc, bg=M['line'], height=1).pack(fill='x', pady=12)
        ib = tk.Frame(rc, bg='#151a30', padx=12, pady=8); ib.pack(fill='x')
        tk.Label(ib, text=f'⚠  ID de usuario:  {uid}', fg=M['amber'],
                 bg='#151a30', font=('Segoe UI', 10, 'bold')).pack(anchor='w')
        tk.Label(ib, text='Guárdalo — lo necesitas para iniciar sesión.',
                 fg=M['mid'], bg='#151a30', font=F_SMALL).pack(anchor='w', pady=(2, 0))

        self._scroll.bottom()

    def destroy(self):
        if self._live: self._live.stop()
        super().destroy()


# ══════════════════════════════════════════════════════════════════════════════
#  Vista: Login — diseño de dos columnas
#  Columna izquierda : formulario (ID + contraseña + OTP)
#  Columna derecha   : widget TOTP en vivo (si el usuario tiene 2FA)
# ══════════════════════════════════════════════════════════════════════════════

class LoginView(BaseView):

    def __init__(self, parent):
        super().__init__(parent)
        self._timer_id  = None
        self._live      = None
        self._seed_live = None   # semilla cargada para widget en vivo
        self._build()

    # ─────────────────────────────────────────────────────────────────────────
    #  Construcción de la UI
    # ─────────────────────────────────────────────────────────────────────────

    def _build(self):
        self.clear()
        self._timer_id  = None
        self._live      = None
        self._seed_live = None
        self.configure(bg=M['panel'])

        # ────────────────────────────── Contenedor principal — dos columnas ──────────────────────────────
        root = tk.Frame(self, bg=M['panel'])
        root.place(relx=0.5, rely=0.5, anchor='center')

        left  = tk.Frame(root, bg=M['panel']); left.pack(side='left', anchor='n', padx=(0, 0))
        self._right_wrap = tk.Frame(root, bg=M['panel'], width=320)
        self._right_wrap.pack(side='left', anchor='n', padx=(16, 0))
        self._right_wrap.pack_propagate(False)

        # ────────────────────────────── Tarjeta del formulario (columna izquierda) ──────────────────────────────
        card_wrap = tk.Frame(left, bg=M['border'], padx=1, pady=1); card_wrap.pack()
        card      = tk.Frame(card_wrap, bg=M['card']); card.pack()

        # Header de la tarjeta
        hdr = tk.Frame(card, bg=M['card'], padx=32, pady=24); hdr.pack(fill='x')
        tk.Label(hdr, text='Iniciar sesión', fg=M['text'],
                 bg=M['card'], font=F_TITLE).pack(anchor='w')
        tk.Label(hdr, text='ID · Contraseña · TOTP (bcrypt + RFC 6238)',
                 fg=M['dim'], bg=M['card'], font=F_SMALL).pack(anchor='w', pady=(4, 0))
        tk.Frame(card, bg=M['line'], height=1).pack(fill='x')

        # Cuerpo de la tarjeta
        body = tk.Frame(card, bg=M['card'], padx=32, pady=22); body.pack(fill='x')

        # ────────────────────────────── Fila: ID + Contraseña ──────────────────────────────
        cred_row = tk.Frame(body, bg=M['card']); cred_row.pack(fill='x')

        id_col = tk.Frame(cred_row, bg=M['card']); id_col.pack(side='left', anchor='n', padx=(0, 16))
        pw_col = tk.Frame(cred_row, bg=M['card']); pw_col.pack(side='left', fill='x', expand=True, anchor='n')

        # Campo ID — grande
        _field_label(id_col, 'ID de usuario')
        id_wrap = tk.Frame(id_col, bg=M['border'], padx=1, pady=1); id_wrap.pack()
        self.ent_id = tk.Entry(id_wrap, width=6,
                               font=('Segoe UI', 26, 'bold'), justify='center',
                               bg=M['card2'], fg=M['accent'],
                               insertbackground=M['accent'],
                               relief='flat', bd=0, highlightthickness=0)
        self.ent_id.pack(ipady=12, padx=10)
        self.ent_id.focus()
        self.ent_id.bind('<FocusIn>',  lambda _: id_wrap.config(bg=M['focus']))
        self.ent_id.bind('<FocusOut>', lambda _: id_wrap.config(bg=M['border']))
        self.ent_id.bind('<Return>',   lambda _: self.ent_pass.focus())
        # Al perder foco intentamos cargar semilla para el widget en vivo
        self.ent_id.bind('<FocusOut>', lambda _: [id_wrap.config(bg=M['border']),
                                                   self._try_load_live()])

        # Campo contraseña
        _field_label(pw_col, 'Contraseña')
        self.ent_pass = _input(pw_col, show='•', width=22)
        self.ent_pass.bind('<Return>', lambda _: self._otp[0].focus())

        # ────────────────────────────── Sección TOTP ──────────────────────────────
        tk.Frame(body, bg=M['line'], height=1).pack(fill='x', pady=(20, 0))

        totp_hdr = tk.Frame(body, bg=M['card']); totp_hdr.pack(fill='x', pady=(12, 10))
        tk.Label(totp_hdr, text='CÓDIGO TOTP', fg=M['dim'],
                 bg=M['card'], font=F_LABEL).pack(side='left')
        tk.Label(totp_hdr, text='(omite si no tienes 2FA)', fg=M['dim'],
                 bg=M['card'], font=F_SMALL).pack(side='left', padx=(6, 0))

        # Casillas OTP: 6 celdas individuales
        otp_row = tk.Frame(body, bg=M['card']); otp_row.pack(anchor='w')
        self._otp = []
        for i in range(6):
            if i == 3:
                tk.Label(otp_row, text=' ', bg=M['card']).pack(side='left', padx=1)
            cf = tk.Frame(otp_row, bg=M['border'], padx=1, pady=1)
            cf.pack(side='left', padx=2)
            e = tk.Entry(cf, width=2, font=F_DIGIT, justify='center',
                         bg=M['card2'], fg=M['accent'],
                         insertbackground=M['accent'],
                         relief='flat', bd=0, highlightthickness=0)
            e.pack(ipady=10, padx=6)
            e.bind('<FocusIn>',    lambda _, f=cf: f.config(bg=M['focus']))
            e.bind('<FocusOut>',   lambda _, f=cf: f.config(bg=M['border']))
            e.bind('<KeyRelease>', lambda ev, n=i: self._otp_key(ev, n))
            e.bind('<BackSpace>',  lambda ev, n=i: self._otp_back(ev, n))
            self._otp.append(e)

        # Barra progreso
        self._pt = tk.Frame(body, bg=M['line'], height=3)
        self._pt.pack(fill='x', pady=(14, 2))
        self._pt.pack_propagate(False)
        self._pb = tk.Frame(self._pt, bg=M['accent'], height=3)
        self._pb.place(x=0, y=0, relwidth=1.0, height=3)

        self._tlbl = tk.Label(body, text='', fg=M['dim'], bg=M['card'], font=F_SMALL)
        self._tlbl.pack(anchor='w', pady=(0, 4))
        self._start_timer()

        # Botón acceder
        tk.Frame(body, bg=M['line'], height=1).pack(fill='x', pady=(16, 18))
        brow = tk.Frame(body, bg=M['card']); brow.pack(fill='x')
        _btn_solid(brow, '  Acceder  →', self._login).pack(side='left')

        # Status
        self.status = _status_lbl(left)
        self.status.config(bg=M['panel'])
        self.status.pack(pady=(8, 0), anchor='w')

        # Panel derecho vacío inicial
        self._build_right_empty()

    # ────────────────────────────── Panel derecho ──────────────────────────────

    def _build_right_empty(self):
        for w in self._right_wrap.winfo_children(): w.destroy()
        ph = tk.Frame(self._right_wrap, bg=M['card2'],
                      highlightthickness=1, highlightbackground=M['border'])
        ph.pack(fill='both', expand=True, pady=0)
        tk.Label(ph, text='⌚', bg=M['card2'],
                 font=('Segoe UI', 32)).pack(pady=(40, 6))
        tk.Label(ph, text='Código TOTP en vivo', fg=M['mid'],
                 bg=M['card2'], font=('Segoe UI', 10, 'bold')).pack()
        tk.Label(ph, text='Ingresa tu ID y\nse cargará automáticamente\nsi tienes 2FA activo.',
                 fg=M['dim'], bg=M['card2'], font=F_SMALL,
                 justify='center').pack(pady=(6, 0))

    def _build_right_live(self, seed: str):
        for w in self._right_wrap.winfo_children(): w.destroy()

        rw = tk.Frame(self._right_wrap, bg=M['card2'],
                      highlightthickness=1, highlightbackground=M['focus'])
        rw.pack(fill='both', expand=True)

        # Badge superior
        badge = tk.Frame(rw, bg=M['card3'], padx=12, pady=6); badge.pack(fill='x')
        tk.Label(badge, text='● 2FA ACTIVO  —  copia el código abajo',
                 fg=M['accent'], bg=M['card3'],
                 font=('Segoe UI', 7, 'bold')).pack(anchor='w')

        # Widget en vivo
        self._live = LiveTOTPWidget(rw, seed)
        self._live.pack(fill='x')

        # Botón copiar código actual
        def _copy_live():
            code = _totp_generate(seed)
            rw.clipboard_clear(); rw.clipboard_append(code)
            btn_copy.config(text=f'Copiado: {code[:3]} {code[3:]}  ✓', fg=M['ok'])
            rw.after(2000, lambda: btn_copy.config(text='Copiar código actual', fg=M['dim']))

        btn_copy = tk.Button(rw, text='Copiar código actual', command=_copy_live,
                             fg=M['dim'], bg=M['card2'],
                             activeforeground=M['accent'], activebackground=M['card2'],
                             font=F_SMALL, relief='flat', bd=0, pady=6, cursor='hand2')
        btn_copy.pack(pady=(0, 4))

        # Info
        tk.Frame(rw, bg=M['line'], height=1).pack(fill='x', padx=16)
        tk.Label(rw, text='Pega el código en las casillas TOTP\nde la izquierda para iniciar sesión.',
                 fg=M['dim'], bg=M['card2'], font=F_SMALL,
                 justify='center').pack(pady=10)

    def _try_load_live(self):
        """Intenta cargar el widget en vivo según el ID ingresado."""
        raw = self.ent_id.get().strip().lstrip('#')
        if not raw or not raw.isdigit():
            return
        user = db.buscar_usuario_por_id(int(raw))
        if not user:
            return
        seed = db.obtener_semilla_activa(user['id'])
        if seed and seed != self._seed_live:
            self._seed_live = seed
            if self._live:
                self._live.stop(); self._live = None
            self._build_right_live(seed)
        elif not seed and self._seed_live:
            self._seed_live = None
            if self._live:
                self._live.stop(); self._live = None
            self._build_right_empty()

    # ────────────────────────────── OTP ──────────────────────────────

    def _otp_key(self, ev, n):
        val = ''.join(c for c in self._otp[n].get() if c.isdigit())
        self._otp[n].delete(0, 'end')
        if val:
            self._otp[n].insert(0, val[-1])
            if n < 5: self._otp[n + 1].focus()
            else: self._login()

    def _otp_back(self, ev, n):
        if not self._otp[n].get() and n > 0:
            self._otp[n - 1].focus(); self._otp[n - 1].delete(0, 'end')

    def _get_code(self):
        return ''.join(e.get() for e in self._otp)

    # ────────────────────────────── Tiempo ──────────────────────────────

    def _start_timer(self): self._stop_timer(); self._tick_timer()

    def _tick_timer(self):
        rem = 30 - (int(time.time()) % 30)
        if not (hasattr(self, '_tlbl') and self._tlbl.winfo_exists()): return
        dang  = rem <= 5
        color = M['danger'] if dang else M['accent']
        self._tlbl.config(text=f'El código caduca en  {rem:02d} s',
                          fg=M['danger'] if dang else M['dim'])
        if self._pb.winfo_exists():
            self._pt.update_idletasks()
            w  = self._pt.winfo_width()
            bw = max(int(w * rem / 30), 2)
            self._pb.place(x=0, y=0, width=bw, height=3)
            self._pb.config(bg=color)
        if rem == 30:
            for e in self._otp: e.delete(0, 'end')
        self._timer_id = self.after(500, self._tick_timer)

    def _stop_timer(self):
        if self._timer_id:
            self.after_cancel(self._timer_id); self._timer_id = None

    # ────────────────────────────── Verificación ──────────────────────────────

    def _login(self):
        raw = self.ent_id.get().strip().lstrip('#')
        if not raw or not raw.isdigit():
            self.status.err('El ID debe ser un número.'); return
        pw = self.ent_pass.get()
        if not pw:
            self.status.err('Ingresa tu contraseña.'); return

        user = db.buscar_usuario_por_id(int(raw))
        if not user:
            self.status.err('ID no encontrado.'); return
        # bcrypt verify — usa database.verificar_password que llama bcrypt.checkpw
        if not db.verificar_password(pw, user['password_hash']):
            self.status.err('Contraseña incorrecta.'); return

        seed = db.obtener_semilla_activa(user['id'])
        if seed:
            code = self._get_code()
            if len(code) < 6:
                self.status.err('Ingresa el código TOTP de 6 dígitos.'); return
            if not _totp_verify(seed, code):
                self.status.err('Código TOTP incorrecto o expirado.')
                for e in self._otp: e.delete(0, 'end')
                self._otp[0].focus(); return

        self._stop_timer()
        if self._live: self._live.stop(); self._live = None
        self._show_success(user['id'], user['username'], seed is not None)

    # ─────────────────────────────── Pantalla de éxito ───────────────────────────────

    def _show_success(self, uid, name, had_2fa):
        self.clear()
        self.configure(bg=M['panel'])
        self._live = None

        # ── Layout: columna izquierda (info) + derecha (totp en vivo)
        root = tk.Frame(self, bg=M['panel'])
        root.place(relx=0.5, rely=0.5, anchor='center')

        left = tk.Frame(root, bg=M['panel']); left.pack(side='left', anchor='n', padx=(0, 20))

        # ────────────────────────────── Tarjeta de sesión ──────────────────────────────
        cw = tk.Frame(left, bg=M['border'], padx=1, pady=1); cw.pack()
        card = tk.Frame(cw, bg=M['card']); card.pack()

        # Header tarjeta
        chdr = tk.Frame(card, bg=M['card'], padx=28, pady=20); chdr.pack(fill='x')
        tk.Label(chdr, text='✓', fg=M['green'],
                 bg=M['card'], font=('Segoe UI', 40)).pack()
        tk.Label(chdr, text='Acceso verificado', fg=M['text'],
                 bg=M['card'], font=('Segoe UI', 18, 'bold')).pack(pady=(4, 2))
        tk.Label(chdr, text=f'#{uid}  ·  {name}', fg=M['mid'],
                 bg=M['card'], font=('Segoe UI', 11)).pack()

        tk.Frame(card, bg=M['line'], height=1).pack(fill='x')

        # Cuerpo: factores verificados
        cbody = tk.Frame(card, bg=M['card'], padx=28, pady=16); cbody.pack(fill='x')
        tk.Label(cbody, text='FACTORES VERIFICADOS', fg=M['dim'],
                 bg=M['card'], font=F_LABEL).pack(anchor='w', pady=(0, 10))

        factors = [('🔑', 'Contraseña', 'bcrypt rounds=12'),
                   ('🔐', 'TOTP', 'RFC 6238 · SHA-1 · 30s')] if had_2fa else \
                  [('🔑', 'Contraseña', 'bcrypt rounds=12')]
        for icon, title, detail in factors:
            row = tk.Frame(cbody, bg=M['card2'], padx=12, pady=8)
            row.pack(fill='x', pady=3)
            tk.Label(row, text=icon, bg=M['card2'],
                     font=('Segoe UI', 14)).pack(side='left', padx=(0, 10))
            col = tk.Frame(row, bg=M['card2']); col.pack(side='left', anchor='w')
            tk.Label(col, text=title, fg=M['text'],
                     bg=M['card2'], font=('Segoe UI', 9, 'bold')).pack(anchor='w')
            tk.Label(col, text=detail, fg=M['dim'],
                     bg=M['card2'], font=F_SMALL).pack(anchor='w')
            tk.Label(row, text='✓', fg=M['green'],
                     bg=M['card2'], font=('Segoe UI', 12, 'bold')).pack(side='right')

        tk.Frame(card, bg=M['line'], height=1).pack(fill='x')

        cfoot = tk.Frame(card, bg=M['card'], padx=28, pady=14); cfoot.pack(fill='x')
        _btn_ghost(cfoot, '← Cerrar sesión', self._logout).pack(anchor='w')

        # ────────────────────────────── Columna derecha: TOTP en vivo (solo si tiene 2FA) ──────────────────────────────
        if had_2fa:
            seed = db.obtener_semilla_activa(uid)
            if seed:
                right = tk.Frame(root, bg=M['panel']); right.pack(side='left', anchor='n')

                rw = tk.Frame(right, bg=M['border'], padx=1, pady=1); rw.pack()
                ri = tk.Frame(rw, bg=M['card2']); ri.pack()

                # Header panel TOTP
                rhdr = tk.Frame(ri, bg=M['card3'], padx=16, pady=10); rhdr.pack(fill='x')
                tk.Label(rhdr, text='Tu TOTP en vivo', fg=M['text'],
                         bg=M['card3'], font=('Segoe UI', 10, 'bold')).pack(side='left')
                tk.Label(rhdr, text='● SESIÓN ACTIVA', fg=M['green'],
                         bg=M['card3'], font=('Segoe UI', 7, 'bold')).pack(side='right')

                # Widget TOTP
                self._live = LiveTOTPWidget(ri, seed)
                self._live.pack(fill='x')

                # Botón copiar
                def _copy_code():
                    code = _totp_generate(seed)
                    ri.clipboard_clear(); ri.clipboard_append(code)
                    btn_c.config(text=f'Copiado {code[:3]} {code[3:]}  ✓', fg=M['ok'])
                    ri.after(2000, lambda: btn_c.config(text='Copiar código', fg=M['dim']))

                btn_c = tk.Button(ri, text='Copiar código', command=_copy_code,
                                  fg=M['dim'], bg=M['card2'],
                                  activeforeground=M['accent'], activebackground=M['card2'],
                                  font=F_SMALL, relief='flat', bd=0, pady=7, cursor='hand2')
                btn_c.pack(fill='x')

                tk.Frame(ri, bg=M['line'], height=1).pack(fill='x')
                tk.Label(ri,
                         text='Este código se regenera cada 30 s.\nUsa tu app autenticadora para verificarlo.',
                         fg=M['dim'], bg=M['card2'], font=F_SMALL,
                         justify='center').pack(pady=10)

    def _logout(self):
        if self._live:
            self._live.stop(); self._live = None
        self._build()

    def destroy(self):
        self._stop_timer()
        if self._live: self._live.stop()
        super().destroy()


# ══════════════════════════════════════════════════════════════════════════════
#  Vista: Usuarios
# ══════════════════════════════════════════════════════════════════════════════

class UsersView(BaseView):
    def __init__(self, parent):
        super().__init__(parent)
        self._build()

    def _build(self):
        self.clear()
        _section_title(self, 'Usuarios registrados', 'usuarios  LEFT JOIN  semillas_2fa')
        _divider(self)

        frame = tk.Frame(self, bg=M['panel'])
        frame.pack(fill='both', expand=True, padx=PAD, pady=(0, 0))

        style = ttk.Style(); style.theme_use('clam')
        style.configure('Pro.Treeview',
                        background=M['card'], foreground=M['mid'],
                        fieldbackground=M['card'], rowheight=32,
                        font=('Segoe UI', 9))
        style.configure('Pro.Treeview.Heading',
                        background=M['card2'], foreground=M['dim'],
                        font=('Segoe UI', 8, 'bold'), relief='flat')
        style.map('Pro.Treeview',
                  background=[('selected', M['card3'])],
                  foreground=[('selected', M['accent'])])

        cols = ('id', 'usuario', 'correo', '2fa')
        self.tree = ttk.Treeview(frame, columns=cols, show='headings',
                                  style='Pro.Treeview', height=14)
        for col, w, anc, label in [
            ('id',      60,  'center', 'ID'),
            ('usuario', 160, 'w',      'Usuario'),
            ('correo',  250, 'w',      'Correo'),
            ('2fa',     120, 'center', 'Autenticación'),
        ]:
            self.tree.heading(col, text=label)
            self.tree.column(col, width=w, anchor=anc)
        self.tree.pack(fill='both', expand=True)

        btn_row = tk.Frame(self, bg=M['panel']); btn_row.pack(pady=12, anchor='w', padx=PAD)
        _btn_ghost(btn_row, '↺  Actualizar lista', self._load).pack(side='left')
        self._load()

    def _load(self):
        for r in self.tree.get_children(): self.tree.delete(r)
        for u in db.listar_usuarios():
            self.tree.insert('', 'end', values=(
                u['id'], u['username'], u['correo'],
                'TOTP activo' if u['has_2fa'] else '—'
            ))
