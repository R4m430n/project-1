# Android Calculator (KivyMD)
# Very modern, beautiful, and feature-rich calculator for Android written in Python
# Requirements:
#   - Python 3.8+
#   - Kivy
#   - KivyMD
# To build an APK: use Buildozer on Linux. See bottom for a sample buildozer.spec snippet.

from kivy.core.window import Window
from kivy.lang import Builder
from kivy.properties import StringProperty, ListProperty
from kivy.animation import Animation
from kivy.clock import Clock
from kivymd.app import MDApp
from kivymd.uix.snackbar import Snackbar
import math
import ast

# Optional: lock window size for debug on desktop
# Window.size = (360, 760)

KV = '''
BoxLayout:
    orientation: 'vertical'
    spacing: '8dp'
    padding: '8dp'

    MDTopAppBar:
        id: toolbar
        title: app.title
        elevation: 8
        left_action_items: [['theme-light-dark', lambda x: app.toggle_theme()]]
        right_action_items: [['history', lambda x: app.show_history()]]

    BoxLayout:
        orientation: 'vertical'
        size_hint_y: None
        height: self.minimum_height

        MDCard:
            radius: [20, 20, 10, 10]
            elevation: 4
            padding: '12dp'
            size_hint_y: None
            height: '140dp'
            md_bg_color: app.theme_cls.bg_dark if app.theme_cls.theme_style == 'Dark' else app.theme_cls.bg_light

            BoxLayout:
                orientation: 'vertical'

                MDLabel:
                    id: expr
                    text: app.expression_display
                    halign: 'right'
                    font_style: 'Subtitle1'
                    size_hint_y: 0.5
                    shorten: True
                    shorten_from: 'left'
                    color: app.theme_cls.primary_dark

                MDLabel:
                    id: result
                    text: app.result_display
                    halign: 'right'
                    font_style: 'H4'
                    size_hint_y: 0.5
                    color: app.theme_cls.primary_color

    GridLayout:
        cols: 4
        spacing: '8dp'
        row_default_height: (self.width - dp(40)) / 4

        # Row 1
        MDFillRoundFlatIconButton:
            text: 'C'
            icon: 'backspace'
            on_release: app.clear()
        MDFillRoundFlatIconButton:
            text: '('
            on_release: app.insert('(')
        MDFillRoundFlatIconButton:
            text: ')'
            on_release: app.insert(')')
        MDFillRoundFlatIconButton:
            text: '⌫'
            icon: 'arrow-left'
            on_release: app.backspace()

        # Row 2
        MDRectangleFlatButton:
            text: '7'
            on_release: app.insert('7')
        MDRectangleFlatButton:
            text: '8'
            on_release: app.insert('8')
        MDRectangleFlatButton:
            text: '9'
            on_release: app.insert('9')
        MDRectangleFlatButton:
            text: '÷'
            on_release: app.insert('/')

        # Row 3
        MDRectangleFlatButton:
            text: '4'
            on_release: app.insert('4')
        MDRectangleFlatButton:
            text: '5'
            on_release: app.insert('5')
        MDRectangleFlatButton:
            text: '6'
            on_release: app.insert('6')
        MDRectangleFlatButton:
            text: '×'
            on_release: app.insert('*')

        # Row 4
        MDRectangleFlatButton:
            text: '1'
            on_release: app.insert('1')
        MDRectangleFlatButton:
            text: '2'
            on_release: app.insert('2')
        MDRectangleFlatButton:
            text: '3'
            on_release: app.insert('3')
        MDRectangleFlatButton:
            text: '-'
            on_release: app.insert('-')

        # Row 5
        MDRectangleFlatButton:
            text: '0'
            on_release: app.insert('0')
        MDRectangleFlatButton:
            text: '.'
            on_release: app.insert('.')
        MDRectangleFlatButton:
            text: '^'
            on_release: app.insert('**')
        MDRectangleFlatButton:
            text: '+'
            on_release: app.insert('+')

        # Row 6 (scientific)
        MDRectangleFlatButton:
            text: 'sin'
            on_release: app.insert('sin(')
        MDRectangleFlatButton:
            text: 'cos'
            on_release: app.insert('cos(')
        MDRectangleFlatButton:
            text: 'tan'
            on_release: app.insert('tan(')
        MDRectangleFlatButton:
            text: '√'
            on_release: app.insert('sqrt(')

        # Row 7
        MDRectangleFlatButton:
            text: 'ln'
            on_release: app.insert('ln(')
        MDRectangleFlatButton:
            text: 'log'
            on_release: app.insert('log(')
        MDRectangleFlatButton:
            text: 'π'
            on_release: app.insert('pi')
        MDRectangleFlatButton:
            text: 'e'
            on_release: app.insert('e')

        # Row 8
        MDRectangleFlatButton:
            text: '%'
            on_release: app.insert('%')
        MDRectangleFlatButton:
            text: 'ANS'
            on_release: app.insert('ans')
        MDRectangleFlatButton:
            text: 'EXP'
            on_release: app.insert('e')
        MDFillRoundFlatButton:
            text: '='
            on_release: app.evaluate()

    Widget:
        size_hint_y: None
        height: '6dp'
'''


# SAFE evaluator using ast
ALLOWED_NAMES = {
    'sin': math.sin,
    'cos': math.cos,
    'tan': math.tan,
    'sqrt': math.sqrt,
    'log': math.log10,
    'ln': math.log,
    'pi': math.pi,
    'e': math.e,
    'abs': abs,
    'pow': pow,
}

ALLOWED_NODES = (
    ast.Expression,
    ast.Call,
    ast.Name,
    ast.Load,
    ast.BinOp,
    ast.UnaryOp,
    ast.operator,
    ast.unaryop,
    ast.Num,
    ast.Constant,
    ast.Pow,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.Mod,
    ast.UAdd,
    ast.USub,
    ast.Tuple,
    ast.List,
)


def safe_eval(expr, extra_names=None):
    """Safely evaluate a mathematical expression using ast parsing.
    Supported: numbers, binary ops, unary ops, allowed function names.
    """
    if extra_names is None:
        extra_names = {}
    names = dict(ALLOWED_NAMES)
    names.update(extra_names)

    try:
        node = ast.parse(expr, mode='eval')
    except Exception as e:
        raise ValueError('Invalid expression')

    for n in ast.walk(node):
        if not isinstance(n, ALLOWED_NODES):
            raise ValueError(f'Unsupported expression: {type(n).__name__}')
        if isinstance(n, ast.Name):
            if n.id not in names:
                raise ValueError(f'Use of name "{n.id}" not allowed')

    compiled = compile(node, '<string>', 'eval')
    return eval(compiled, {'__builtins__': {}}, names)


class CalculatorApp(MDApp):
    expression = StringProperty('')
    expression_display = StringProperty('')
    result_display = StringProperty('0')
    history = ListProperty([])
    ans = None

    def build(self):
        self.title = "Zamonaviy Kalkulyator"
        self.theme_cls.primary_palette = 'BlueGray'
        self.theme_cls.theme_style = 'Light'
        return Builder.load_string(KV)

    def on_start(self):
        # little entrance animation for toolbar
        toolbar = self.root.ids.toolbar
        toolbar.opacity = 0
        Animation(opacity=1, d=0.4).start(toolbar)

    def insert(self, token: str):
        self.expression += token
        self.expression_display = self.expression
        self._pulse_display()

    def clear(self):
        self.expression = ''
        self.expression_display = ''
        self.result_display = '0'

    def backspace(self):
        self.expression = self.expression[:-1]
        self.expression_display = self.expression

    def evaluate(self):
        expr = self.expression.replace('×', '*').replace('÷', '/')
        # allow percent as modulo of 100
        expr = expr.replace('%', '/100')
        # map ans
        extra = {'ans': self.ans} if self.ans is not None else {}
        try:
            value = safe_eval(expr, extra_names=extra)
            # format nicely
            if isinstance(value, float):
                if abs(value) < 1e-12:
                    value = 0
                text = ('{:.12g}').format(value)
            else:
                text = str(value)
            self.result_display = text
            self.ans = value
            # save history
            self.history.insert(0, (self.expression, text))
            if len(self.history) > 30:
                self.history.pop()
            self._result_breathe()
        except Exception as e:
            self.result_display = 'Xato'
            Snackbar(text=str(e)).open()

    def _pulse_display(self):
        label = self.root.ids.expr
        Animation(font_size='20sp', d=0.06) + Animation(font_size='16sp', d=0.06)
        Animation(opacity=0.6, d=0.06) + Animation(opacity=1, d=0.06)
        # no need to chain, small visual only

    def _result_breathe(self):
        label = self.root.ids.result
        anim = Animation(opacity=0.2, d=0.12) + Animation(opacity=1, d=0.12)
        anim.start(label)

    def toggle_theme(self):
        self.theme_cls.theme_style = 'Dark' if self.theme_cls.theme_style == 'Light' else 'Light'

    def show_history(self):
        if not self.history:
            Snackbar(text='Tarix bo'sh').open()
            return
        s = '\n'.join([f"{h[0]} = {h[1]}" for h in self.history[:8]])
        Snackbar(text=s, duration=3.5).open()


if __name__ == '__main__':
    CalculatorApp().run()


# buildozer.spec snippet (add to buildozer.spec)
# ----------------------------
# [app]
# title = Zamonaviy Kalkulyator
# package.name = zm_kalkulyator
# package.domain = org.example
# source.include_exts = py,png,jpg,kv,atlas
# requirements = python3,kivy==2.1.0,kivymd
# orientation = portrait
# android.api = 33
# android.arch = arm64-v8a
# presplash.filename = presplash.png
# icon.filename = icon.png
# ----------------------------
# To build:
# 1) install buildozer (on Ubuntu)
# 2) buildozer init
# 3) paste the snippet and set package details
# 4) buildozer -v android debug
# Note: using KivyMD may require pinning versions to match Kivy version.
