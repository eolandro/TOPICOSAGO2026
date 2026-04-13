import tkinter as tk
import database as db
from views import RegisterView, LoginView, UsersView

BG      = '#1a1a24'   
SIDEBAR = '#22222e'   
LINE    = '#3a3a50'   
DIM     = '#7878a0'
MID     = '#aaaacc'
TEXT    = '#e0e0f0'
ACCENT  = '#4a7fd4'   
SEL_BG  = '#2a3a52'   

NAV = [
    ('register', 'Nuevo usuario'),
    ('login',    'Iniciar sesión'),
    ('users',    'Usuarios'),
]

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('MFA / TOTP')
        self.geometry('920x680')
        self.minsize(740, 560)
        self.configure(bg=BG)
        self.update_idletasks()
        x = (self.winfo_screenwidth()  - 920) // 2
        y = (self.winfo_screenheight() - 680) // 2
        self.geometry(f'920x680+{x}+{y}')
        self._view = None
        self._build()
        self._show('register')

    def _build(self):
        sb = tk.Frame(self, bg=SIDEBAR, width=200)
        sb.pack(side='left', fill='y')
        sb.pack_propagate(False)
        tk.Frame(self, bg=LINE, width=1).pack(side='left', fill='y')
        logo_area = tk.Frame(sb, bg=SIDEBAR, padx=24, pady=28)
        logo_area.pack(fill='x')
        tk.Label(logo_area, text='MFA · TOTP', fg=TEXT, bg=SIDEBAR,
                 font=('Segoe UI', 13, 'bold')).pack(anchor='w')
        tk.Label(logo_area, text='Autenticación multifactor', fg=DIM, bg=SIDEBAR,
                 font=('Segoe UI', 8)).pack(anchor='w', pady=(2, 0))

        tk.Frame(sb, bg=LINE, height=1).pack(fill='x')

        self._btns  = {}
        self._marks = {}
        for key, label in NAV:
            row = tk.Frame(sb, bg=SIDEBAR, cursor='hand2')
            row.pack(fill='x')
            row.bind('<Button-1>', lambda e, k=key: self._show(k))

            mark = tk.Frame(row, bg=SIDEBAR, width=3)
            mark.pack(side='left', fill='y', padx=(0, 0))

            btn = tk.Label(row, text=label,
                           font=('Segoe UI', 10), anchor='w',
                           bg=SIDEBAR, fg=DIM,
                           padx=18, pady=11, cursor='hand2')
            btn.pack(side='left', fill='x', expand=True)
            btn.bind('<Button-1>', lambda e, k=key: self._show(k))

            self._btns[key]  = btn
            self._marks[key] = mark

        tk.Frame(sb, bg=LINE, height=1).pack(fill='x', pady=(8, 0))

        # Metadata al fondo
        for txt in ('Vanguardia', 'CD7-2 · AE7', '##R005## · ##25##'):
            tk.Label(sb, text=txt, fg='#cccccc', bg=SIDEBAR,
                     font=('Segoe UI', 7)).pack(side='bottom', anchor='w', padx=24, pady=1)
        tk.Frame(sb, bg=LINE, height=1).pack(side='bottom', fill='x', pady=(0, 8))

        self.content = tk.Frame(self, bg=BG)
        self.content.pack(side='left', fill='both', expand=True)

    def _show(self, key: str):
        for k, btn in self._btns.items():
            active = k == key
            btn.config(fg=ACCENT if active else DIM,
                       bg=SEL_BG if active else SIDEBAR,
                       font=('Segoe UI', 10, 'bold') if active else ('Segoe UI', 10))
            self._marks[k].config(bg=ACCENT if active else SIDEBAR)

        if self._view: self._view.destroy()
        views = {'register': RegisterView, 'login': LoginView, 'users': UsersView}
        self._view = views[key](self.content)
        self._view.pack(fill='both', expand=True)


if __name__ == '__main__':
    print('Inicializando base de datos…')
    db.init_db()
    print('Iniciando MFA / TOTP Demo…')
    App().mainloop()
