"""Small display layer: works in Jupyter and in the transparent notebook runner."""
import base64
import html
import io
import json
from .common import ROOT

_sink = None

def set_sink(callback):
    global _sink
    _sink = callback

def _emit(data):
    if _sink is not None:
        _sink(data)
        return
    try:
        from IPython.display import display
        display(data, raw=True)
    except ImportError:
        print(data.get('text/plain', data.get('text/html', '[rich output]')))

def show_table(frame, caption, decimals=3):
    content = frame.to_html(index=False, border=0, float_format=lambda x: f'{x:,.{decimals}f}', na_rep='—')
    content = '<div class="table-wrap">' + content + '</div>'
    content += '<p class="caption" style="text-align:center">' + html.escape(caption) + '</p>'
    _emit({'text/html': content, 'text/plain': frame.to_string(index=False) + '\n' + caption})

def show_json(value):
    text = json.dumps(value, indent=2, ensure_ascii=False)
    _emit({'text/html': '<pre>' + html.escape(text) + '</pre>', 'text/plain': text})

def equation(number):
    eq = next(e for e in json.loads((ROOT/'paper/equation-register.json').read_text()) if e['number'] == number)
    content = '<div class="equation">\\[' + eq['latex'] + '\\]</div>'
    content += '<p class="caption" style="text-align:center">' + html.escape(eq['caption']) + '</p>'
    content += '<p>' + html.escape(eq['explanation']) + '</p>'
    _emit({'text/html': content, 'text/plain': eq['caption'] + '\n' + eq['latex'] + '\n' + eq['explanation']})

def show_figure(number):
    item = next(f for f in json.loads((ROOT/'outputs/figure-register.json').read_text()) if f['number'] == number)
    _emit({'image/png': base64.b64encode((ROOT/item['png']).read_bytes()).decode(), 'text/plain': item['title']})
    _emit({'text/html': '<p class="caption" style="text-align:center">' + html.escape(item['caption']) + '</p>', 'text/plain': item['caption']})

def show_plot(figure, caption):
    import matplotlib.pyplot as plt
    buf = io.BytesIO()
    figure.savefig(buf, format='png', dpi=160, bbox_inches='tight')
    plt.close(figure)
    _emit({'image/png': base64.b64encode(buf.getvalue()).decode(), 'text/plain': caption})
    _emit({'text/html': '<p class="caption" style="text-align:center">' + html.escape(caption) + '</p>', 'text/plain': caption})
