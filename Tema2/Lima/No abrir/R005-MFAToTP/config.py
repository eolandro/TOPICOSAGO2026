import os as _os
DB_PATH  = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), 'usuarios.db')
APP_NAME = 'MFA / TOTP Demo'

COLORS = {
    'bg':       '#1a1a24',
    'surface':  '#22222e',
    'surface2': '#2a2a38',
    'border':   '#3a3a50',
    'accent':   '#4a7fd4',
    'accent2':  '#3ecf8e',
    'danger':   '#e05555',
    'warn':     '#d4944a',
    'text':     '#e0e0f0',
    'muted':    '#7878a0',
    'white':    '#e0e0f0',
}

FONT_TITLE  = ('Segoe UI', 18, 'bold')
FONT_HEAD   = ('Segoe UI', 13, 'bold')
FONT_BODY   = ('Segoe UI', 10)
FONT_MONO   = ('Courier New', 10)
FONT_BIG    = ('Segoe UI', 32, 'bold')
