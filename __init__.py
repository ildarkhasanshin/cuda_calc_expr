import os
import math
import statistics
from cudatext import *
from cudax_lib import get_translation

_   = get_translation(__file__)  # I18N

fn_config = os.path.join(app_path(APP_DIR_SETTINGS), 'plugins.ini')
fn_section = 'calc_expression'
sep_dec = '.'
sep_th = ''
sep_list = ','
digits_count = 4

safe_dict = {
    'acos': math.acos,
    'asin': math.asin,
    'atan': math.atan,
    'atan2': math.atan2,
    'ceil': math.ceil,
    'cos': math.cos,
    'cosh': math.cosh,
    'degrees': math.degrees,
    'e': math.e,
    'exp': math.exp,
    'fabs': math.fabs,
    'floor': math.floor,
    'fmod': math.fmod,
    'frexp': math.frexp,
    'hypot': math.hypot,
    'ldexp': math.ldexp,
    'log': math.log,
    'log10': math.log10,
    'modf': math.modf,
    'pi': math.pi,
    'pow': math.pow,
    'radians': math.radians,
    'sin': math.sin,
    'sinh': math.sinh,
    'sqrt': math.sqrt,
    'tan': math.tan,
    'tanh': math.tanh,
    'abs': abs,
    'min': min,
    'max': max,
    'sum': sum,
    'mean': statistics.mean,
    'median': statistics.median,
    }

def do_eval(s):
    r = eval(s, {"__builtins__": None}, safe_dict)
    r = f"{r:g}"
    if r:
        return str(r)


class Command:
    def __init__(self):
        global sep_dec
        global sep_th
        global sep_list
        global digits_count
        sep_dec = ini_read(fn_config, fn_section, 'decimal_separator', sep_dec)
        sep_th = ini_read(fn_config, fn_section, 'thousand_separator', sep_th)
        sep_list = ini_read(fn_config, fn_section, 'list_separator', sep_list)
        digits_count = int(ini_read(fn_config, fn_section, 'digits_precision', str(digits_count)))

    def replace(self):
        self.do_work('rep')

    def show(self):
        self.do_work('show')

    def ins_sel(self):
        self.do_work('ins_sel')

    def do_work(self, mode):
        carets = ed.get_carets()
        if len(carets)>1:
            msg_status(_('[Calc Expression] Multi-carets not supported'))
            return

        s_sel = ed.get_text_sel()
        s = s_sel
        if not s:
            return

        if sep_dec!='':
            s = s.replace(sep_dec, chr(1))
        if sep_th!='':
            s = s.replace(sep_th, chr(2))
        if sep_list!='':
            s = s.replace(sep_list, chr(3))
        s = s.replace(chr(1), '.')
        s = s.replace(chr(2), '')
        s = s.replace(chr(3), ',')
        s = s.replace(':', '/')
        s = s.rstrip('= ')

        try:
            s = do_eval(s)
        except Exception as e:
            msg_status(_('[Calc Expression] ')+str(e))
            return

        try:
            n = float(s) # check is it number
        except:
            msg_status(_('[Calc Expression] Not a number result'))
            return

        if sep_th:
            if digits_count > 0:
                s = ('{:,.'+str(digits_count)+'f}').format(n)
            else:
                s = '{:,}'.format(n)
            s = s.replace(',', chr(1))
        else:
            if digits_count > 0:
                s = ('{:.'+str(digits_count)+'f}').format(n)

        if sep_dec:
            s = s.replace('.', chr(2))

        s = s.replace(chr(1), sep_th)
        s = s.replace(chr(2), sep_dec)

        if mode=='rep':
            #sort coord
            x0, y0, x1, y1 = carets[0]
            if (y0, x0)>(y1, x1):
                x0, y0, x1, y1 = x1, y1, x0, y0

            ed.set_caret(x0, y0)
            ed.replace(x0, y0, x1, y1, s)
            msg_status(_('[Calc Expression] Replaced to: %s') %s)

        if mode=='show':
            msg_status(_('[Calc Expression] Result: %s') %s)

        if mode=='ins_sel':
            x0, y0, x1, y1 = carets[0]
            if (y0, x0) > (y1, x1):
                x0, y0, x1, y1 = x1, y1, x0, y0

            text_sel = s_sel.rstrip('= ').strip()
            equal_sign = ' = ' if ' ' in text_sel else '='
            ed.replace(x0, y0, x1, y1, text_sel + equal_sign + s)

            x0_sel = x0 + len(text_sel) + len(equal_sign)
            x1_sel = x0_sel + len(s)
            ed.set_caret(x0_sel, y0, x1_sel, y1)

            msg_status(_('[Calc Expression] Calculated to: %s') %s)

        if mode=='auto_calc':
            return s

    def config(self):
        ini_write(fn_config, fn_section, 'decimal_separator', sep_dec)
        ini_write(fn_config, fn_section, 'thousand_separator', sep_th)
        ini_write(fn_config, fn_section, 'list_separator', sep_list)
        ini_write(fn_config, fn_section, 'digits_precision', str(digits_count))
        file_open(fn_config)

        lines = [ed.get_text_line(i) for i in range(ed.get_line_count())]
        try:
            index = lines.index('['+fn_section+']')
            ed.set_caret(0, index)
        except:
            pass

    def on_key(self, ed_self, key, state):
        carets = ed_self.get_carets()
        # dont support multi-carets
        if len(carets)>1: return

        if key == 187 and state == '':
            x0, y0, x1, y1 = carets[0]
            if (y0, x0) > (y1, x1):
                x0, y0, x1, y1 = x1, y1, x0, y0
            len_ = ed_self.get_line_len(y1)
            ed_self.set_caret(0, y1, len_, y1)
            text_sel = ed_self.get_text_sel().rstrip('= ').strip()
            equal_sign = '= ' if ' ' in text_sel else '='
            res = str(self.do_work('auto_calc'))
            x1_ = len_ + len(equal_sign)
            x2_ = len_ + len(equal_sign) + len(res)
            ed_self.insert(len_, y1, equal_sign + res)
            ed_self.set_caret(x1_, y1, x2_, y1)

            return False

        if key == 40 and state == 'c':
            x0, y0, x1, y1 = carets[0]
            if (y0, x0) > (y1, x1):
                x0, y0, x1, y1 = x1, y1, x0, y0
            res = ''
            try:
                res = ed_self.get_text_line(y1).split('=', 1)[1].strip()
            except:
                pass
            if res:
                ed_self.insert(0, y1 + 1, "\n")
                ed_self.insert(0, y1 + 1, res)
                ed_self.set_caret(len(res), y1+1)

            return False
