# -*- coding: utf-8 -*-
import json
import os
import sys
import time
import base64
import hmac
import hashlib
import urllib.parse
import csv
from datetime import datetime
from typing import Dict, Any
from enum import Enum

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QGroupBox, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QComboBox, QTextEdit, QTextBrowser,
    QSpinBox, QMessageBox, QHeaderView, QFormLayout,
    QSystemTrayIcon, QMenu, QCheckBox, QStyle, QSpinBox,
    QToolButton, QDialog, QDialogButtonBox, QFileDialog
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSettings, QTimer, QByteArray
from PyQt6.QtGui import QIcon, QAction, QFont, QPixmap

import requests

try:
    from Crypto.PublicKey import RSA
    from Crypto.Cipher import PKCS1_OAEP
    from Crypto.Hash import SHA256
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False

try:
    from gmssl.sm4 import CryptSM4, SM4_ENCRYPT, SM4_DECRYPT
    HAS_GMSSL = True
except ImportError:
    HAS_GMSSL = False

APP_CONFIG = {
    "app_name": "SmsForwarder Windows Client - Cristy(www.52pojie.cn)",
    "default_url": "http://127.0.0.1:7001",
    "default_poll_interval": 5,
    "min_poll_interval": 1,
    "max_poll_interval": 300,
    "window_width": 1000,
    "window_height": 750,
}

ICON_BASE64 = "AAABAAEAeHgAAAEAIACo6AAAFgAAACgAAAB4AAAA8AAAAAEAIAAAAAAAAOEAAPMOAADzDgAAAAAAAAAAAAC40uP/t9Hi/7fR4v+30eL/t9Hi/7fR4v+3z+H/uNDi/7rS5P+40OL/t8/h/7jQ4v+30eL/t9Hi/7fR4v+40OL/uNDi/7nR4/+60+P/utPj/7nS4v+60+P/utTi/7vV4/+71eP/u9Xj/7zW5P+81uT/vdfl/7/Z5/++2Ob/vtjm/77b5P+/2+b/v9vm/7/b5v+/2+b/v9vm/7/b5v/A3Of/v9vm/7/b5v/D3en/wtzo/8Ld5//C3+j/wt/o/8Le6f/B4On/w+Dp/8Le6f/C3un/wN/o/8Df6P/D4On/weDp/8Hg6f/A3+j/wt/o/8Lf6P/D4On/w+Dp/8De6f++3Of/wN/o/8Pg6f/D4On/wt/o/8Hd6P/C3un/w97o/8He5//A3+j/wN/o/8Lf6P/B3uf/wd7n/7/e5//A3Of/wdvp/8Da5v+/2+b/vdvm/77d5v+82+T/vtjk/8DX5v/A1+f/v9bl/7/W5f+91+X/vNfl/7zW5v+81ub/vNXl/73U5P+61OT/utTk/7rU5P+50+P/udPj/7nT4/+50+P/udLi/7nR4/+50eP/udHj/7nR4/+50eP/udHj/7nR4/+50eP/udHj/7nR4/+40OL/udHj/7nR4/+50eP/uNLj/7jS4/+30eL/t9Hi/7fR4v+30eL/t9Hi/7jQ4v+3z+H/uNDi/7nR4/+3z+H/uc/h/7fP4f+40OL/t9Hi/7jQ4v+40OL/uNDi/7jR4f+60+P/utPj/7rT4/+61OL/u9Xj/7vV4/+71eP/u9Xj/73X5f+91+X/vdfl/73X5f+/2ef/wdjn/7/c5f/A3Of/v9vm/7/b5v++2uX/v9nl/8Hb5//C3Oj/wd3o/8Dc5//B2+f/wNrm/8He5//B3uf/wt/o/8Pf6v/D4Of/w+Dp/8Lf6P/A3+j/wN/o/8Hg6f/D4On/w+Dp/8Pg6f/B4On/weDp/8Pg6f/C3+j/wN/o/8Hf6v/D3+r/wd7n/8Pg6f/C3+j/wd7n/8Pg6f/C3+j/wd7n/8He5/+/3uf/v97n/8He5//B3uf/wN3m/8Dc5//A3Of/wtzq/8Dc5//A3Of/v9vm/77c5/++2uX/wNrm/7/Z5f+/2ef/vtjm/73X5f+91+X/vNbk/7zW5v+71eX/u9Tk/73U5P+61OT/utTk/7nT4/+50+P/udPj/7nT4/+50+P/u9Tk/7nR4/+50eP/udHj/7nR4/+50eP/udHj/7nR4/+50eP/udHj/7nR4/+50eP/utLk/7jQ4v+50eP/uNLj/7jS4/+40eH/uNHh/7jR4f+40eH/uNHh/7jQ4v+40OL/uNDi/7jQ4v+40OL/udDg/7bP3/+40eH/udLi/7nS4v+50uL/uNLi/7rT4/+60+P/utPj/7vV4/+71eP/vdTj/7zT4v+81uT/vdfl/77Y5v+91+X/vtnn/73Z5P+/2eX/wdnl/7/c5f++2uX/vtjk/7/Z5f/A2ub/wtzo/8Xd6f/D3en/wtzo/8Hb5//C3Oj/w93p/8Lf6P/D4On/weDp/8Hg6f/D4Of/w+Dn/8Hg6f/C4er/wOHq/8Lh6v/E4er/xeDq/8Th6v/E4er/wuDr/8Lg6//D4uv/w+Lr/8Tg6//D3+r/xOHo/8Lh6v/D4uv/xOHq/8Th6v/E4er/wuHq/8Hf6v/C3un/w97o/8Pg6f/C3+j/wd7n/8Lc6P/C3Oj/wNzn/8He5//B3uf/wd3o/8Lc6P/A2ub/v9nl/8Db5f+/3OX/v9vm/77a5f++2uX/v9nl/7zW5P+81eX/vNXl/7zV5f+81uT/u9bk/7vV5f+61OT/utTk/7nT4/+50+P/udLi/7nS4v+60uT/udHj/7nR4/+50eP/udHj/7nR4/+50eP/udHj/7rS5P+50eP/udHj/7nR4/+50eP/uNLj/7jS4/+40eH/uNHh/7jR4f+40eH/uNHh/7jR4f+40OL/uNDi/7jR4f+60eH/udDg/7jR4f+40eH/udLi/7nS4v+60+P/uNLi/7rT4/+60+P/vNPj/7vU5P+91OP/vNPi/7zW5P+91+X/vNfl/77Y5v+/2ef/v9nl/7/a5P+/2uT/wdnl/77b5P++2+T/wNrm/8Hb5//A2ub/wtrm/8Pb5//E3Oj/w93p/8Pd6f/D3en/w93p/8Lf6P/A3+j/wODm/8Dg5v/E4Of/w+Dn/8Hh5//A4uj/v+Dp/8Df6P/C3+j/xeDq/8Tf6f/D4On/wd/q/8Hf6v/B4On/weDp/8Pg6f/D3+r/w+Dp/8Hg6f/B4On/w+Dp/8Tf6f/E4er/weDp/8Hg6f/D4On/xN/p/8Pg6f/D4On/w+Dp/8Te6v/E3ur/w9/q/8He5//B3uf/wtzo/8Pb5//D2+f/wdzm/8Db5f+/3OX/v9vm/7/b5v+/2+b/v9vm/7/Z5f+91+X/vNXl/73W5v+81uT/u9Xj/7vV5f+81eX/utPj/7rT4/+50+P/utPj/7rT4/+60uT/uNDi/7jQ4v+40OL/udHj/7nR4/+50eP/udHj/7nR4/+50eP/udHj/7nR4/+50eP/uNLj/7jS4/+3z+H/uNDi/7jQ4v+40OL/uNDi/7fP4f+3z+H/uNDi/7jQ4v+40OL/utDi/7jR4f+40eH/uNHh/7jR4f+50uL/tdLh/7nS4v+70uL/vdTk/73U4/+91OP/vNbk/7zX5f+71uT/vdjm/7/Z5//B2eX/v9rk/7/b4v++2eP/v9rk/8Db5f/C3ef/wdvn/8Da5v/A2ub/wdvn/8Pd6f/D3en/w93p/8Le6f/D3uj/xN/p/8Pg6f/D4On/w+Pp/8Li6P/D4Of/w+Dp/8Th6v/C4er/wuHq/8Lh6v/E4er/xuPs/8Xi6//G4+z/xeLr/8Pi6//D4uv/w+Pp/8Xi6f/F4uv/xeLr/8Pi6//D4uv/xOHq/8Th6v/E4er/xOHq/8Th6v/E4er/w+Dp/8Pg6f/D4On/w+Dp/8Tf6f/E3ur/xN7q/8Th6v/C3un/wtzo/8Hc5v/D3Ob/wt3n/8Hc5v/B2+f/wNrm/7/b5v++2uX/v9vm/77a5f/A2ub/vdjm/7zW5v+81uT/vNbk/7vV4/+81eX/vNXl/7vU5P+60+P/u9Tk/7rT4/+50uL/udHj/7nR4/+50eP/utLk/7nR4/+50eP/udHj/7nR4/+50eP/udHj/7jQ4v+50eP/uNLj/7jS4/+40OL/uNDi/7fP4f+40OL/uNDi/7fP4f+30eL/uNLj/7fP4f+40OL/uNDi/7jQ4v+40OL/uNHh/7jR4f+50uL/uNPh/7nS4v+91OT/u9Lh/7/W5f+91+X/vNfl/7zY4/+72eT/vdnk/7/Z5f/B2eX/wtvl/77a4f+/2+L/wNvl/8Db5f/C2ub/wtrm/8Lc6P/D3uj/w97o/8Lc6P/C3un/w+Dp/8Th6v/F4uv/xOHq/8Th6v/C3+j/xOHo/8Th6P/F4uv/xeLr/8Xi6//F4uv/xeLr/8Lh6v/F4uv/xeLr/8Xi6//F4uv/xeLr/8Xi6//G4+r/xeLp/8Th6P/F4uv/wuHq/8Xi6//F4un/xOHo/8Th6P/E4ej/xOHo/8Xi6f/C4er/w+Lr/8Xi6//E4er/xOHq/8Th6v/E3+n/xN7q/8Le6f/C3un/wt7p/8Tf6f/C3ef/wt3n/8Hb5//B2+n/xdzr/8Da5v++2uX/v9vm/7/b5v++2uX/vtnn/77Y6P++2OT/vdfl/73X5f+91ub/vtfn/7zV5f+71eP/u9Xj/7vU5P+60+P/utPj/7rT4/+50eP/udHj/7jQ4v+50eP/uNDi/7rS5P+50eP/udHj/7jQ4v+50eP/uNLj/7jS4/+50eP/uNDi/7fP4f+40OL/uNDi/7bP4/+30OT/uNLj/7fR4v+40OL/uNDi/7jQ4v+50uL/udLi/7nS4v+50uL/udPf/73U4/+80+L/v9bl/73X4/+82OP/vdnk/77a5f+92eT/vdnk/7/W5f/A2OT/wdrk/8Db5f/B3Ob/wNrm/8Hb5//C3Oj/w93p/8Lc6P/B3Ob/wt/o/8Pg6f/E4er/wuHq/8Li6P/F4un/xOHq/8Th6v/E4er/xeLp/8Xi6f/G4+z/xeLr/8Xi6f/F4un/xeLp/8Xi6f/F4un/xuPq/8bj6v/G4+z/x+Tt/8bj7P/F4uv/xuPq/8bj7P/G4+z/xuPs/8bj7P/F4uv/xeLp/8Xi6f/F4un/xeLp/8Xi6f/C4er/wuHq/8Th6v/E4er/xOHq/8Th6v/D4On/xeDq/8Tg6//D3+r/xODr/8Pf6v/E3ur/xN7q/8Le6f/B2+f/wtzq/8Lc6P/B2+f/wNrm/8Da5v/A2ub/v9nl/73Y5v/A2ub/vtjk/73X5f+91ub/vdbm/7zV5f+71eP/vNbk/7nS4v+60+P/utPj/7rT4/+50uL/uNDi/7jQ4v+50eP/udHj/7nR4/+60uT/udHj/7jQ4v+50eP/uNLj/7jS4/+50eP/uNDi/7bQ4f+40OL/uNDi/7XP4P+20OH/t9Hi/7fR4v+40OL/uNDi/7jR4f+30eH/utPj/7vU5P+50uL/vNTg/77U4P+81OD/vNbi/7zY4/+62OP/vNrl/77a5f+92eT/vtjk/8DX5v/B2eX/wtvl/7/a5P/B2+f/w9vn/8Le6f/C3Oj/wtzq/8Pd6f/E3+n/xOHq/8Th6v/D4On/w+Dn/8Li5//F4un/xuPq/8bj7P/F4uv/w+Lr/8bj6v/E4ej/xeLp/8bj6v/G4+r/xOTq/8bj6v/H5Ov/yOTr/8jk6//H5O3/yOTv/8fj7v/G4+z/xuPs/8bj7P/H4+7/x+Ls/8bj7P/G4+z/xuPq/8bj6v/G5On/xuPq/8bj6v/F4uv/xeLr/8Xi6//G4+z/xeLr/8Xi6//E4er/w+Dp/8Xi6//F4uv/xODr/8Tg6//D3ev/wt7p/8Hf6v/A3un/wd3o/8Hb5//B2+f/wdvn/8Pb5//C2ub/wNrm/7/a5P/B2eX/wdvn/7/Z5/+91ub/vdbm/7zV5f+81uT/vNbk/7zW5P+71OT/utPj/7vU5P+60+P/uNDi/7jQ4v+50eP/udHj/7nR4/+50eP/udHj/7jQ4v+50eP/uNLj/7jS4/+30eL/t9Hi/7bQ4f+40OL/uNDi/7nP4f+3z+H/t9Dg/7fR4f+30OD/uNHh/7jR4f+61OL/utTi/7zT4v++1eX/v9Pk/77V5f+81eX/vNjj/7rY4/+72Ob/u9jn/77X5//B2eX/wtnh/8Pb4f/E3OL/xN3h/8Xe4v/G3+P/xt7k/77b6v+/3Or/w+Dp/8bj6P/E4uP/xOLj/8Xj5P/F4ub/xuPo/8fk6f/F4+j/w+Pp/8Dg6//A4O3/weHu/8Xh7P/H4+r/xuPq/8fk6//H5er/xuPq/8bj6v/G4+z/xeTt/8Xl6//E5Or/xuPs/8bj7P/G4+r/xuPq/8bj7P/I5O//xuPs/8bj7P/G4u3/xOLt/8Ti7f/F4+7/xeTt/8fk6//G5On/xuTp/8Tk6f/E5On/w+Po/8Xk5//F4+j/xeHo/8Ti5//F4+T/x+Pj/8fj4//F4+T/w+Dp/8Ld6//D3ev/xt/p/8Xf5f/D3eP/wd3k/8Lc6P/B2+f/wNro/8Da6P+42en/udjn/7vY5v++2uX/vdjm/7zV5f+81eX/vdXn/7zW5/+71eX/utPj/7rT4/+60+P/utPj/7nR4/+50eP/udHj/7vR4/+70eP/udHj/7nS4v+50eP/udHj/7nR5f+40uP/t9Hi/7fR4v+40OL/t8/h/7bO4P+40OL/uNDi/7fR4f+40eH/uNHh/7rT4/+61OL/udPh/73U4/+91OP/utTg/7zW5P+81+X/vNjj/77Z4//A2uH/wdjg/8LY4//B2uT/v9nl/7/Z5//A2Or/v9ru/7za7f+/2u7/wdru/8Xg5P/F4uf/xOHq/8Lg6//B3u3/wd/w/8Hf8P/E4fD/xeHs/8Th6v/D4uv/xOPs/8Xj6P/I5en/x+To/8fk6f/H5Ov/xuPs/8Xk7f/F5O3/x+Pu/8fj7v/I4+3/yOPt/8fk6//I5ez/yOXu/8jl7v/I5ez/yufu/8jl7P/J5ez/yeTu/8rm7f/H5Ov/x+Xq/8Xl6v/H5Ov/x+Tr/8fk7f/H4+7/xuLt/8fh7f/H4e3/xOLt/8Li7f/D4ez/wt/t/8Pg7v/C3+7/wt7v/8Lf7v/B3+r/xeLn/8fj5P/H4ef/w93r/8Pd7v/D3e7/wtzq/8Hb6f/D3en/w9zm/8Lc4//C3OP/wdvi/77a4f++2+T/v9nl/77Y5v+81uT/vdfl/7vW5P+81+X/u9Tk/7rT4/+60+P/utPj/7rS5P+50eP/udHj/7vR4/+50eP/udHj/7nR4/+50eP/udHj/7jS4/+40uP/t9Hi/7jQ4v+40OL/uNHh/7jQ4v+40OT/uNDk/7jQ4v+40eH/udPh/7rU4v+61OL/u9Xj/7zW5P+91OP/u9jh/7zY4/+81uL/vdfj/8DZ4//B2OD/wtnh/8Hb4v/A2+X/wNro/8Ha6v/A2uv/vNrt/7vb7v+/3fD/wt7v/8fj5P/E4eb/w+Dp/8Pg7v/E4fD/w+Hy/8Hf8P/E4fD/xuHv/8bi7f/E4u3/xOPs/8fk6f/J5eb/yeTo/8nm6//F5ev/yOXu/8nl8P/I5O//yeXw/8nl8P/K5PD/yuXv/8nk7v/K5e//yuXv/8rk8P/J5fD/yebv/8vm8P/J5O7/yeTu/8nk7v/K5u3/yObr/8jo7f/J5u3/yeTu/8nj7//I4/H/x+Lw/8ji7v/I4u7/xuLt/8Pj7v/E4e//w+Du/8Th7//B4O//wN7v/8Hg7//D4ez/xeLn/8fj5P/G4+j/xODr/8Pd7v/C3O3/w9zs/8Pd6//C3Oj/w97o/8Td5//F3OT/w93k/8Lc4/++2eP/v9nl/7/Z5f+91+P/vtjk/7vW5P+71uT/vNXl/7nS4v+60+P/utPj/7rT4/+50uL/utPj/7jQ4v+50eP/udHj/7nR4/+50eP/uNHl/7jS4/+50uL/t8/h/7fP4f+40eH/udLi/7jR4f+3z+H/t8/h/7jQ4v+50uL/udPh/7vS4f+71eP/vNXl/7vU5P+71eP/utfl/7vX4v+91+P/vdfj/7zX5f+82On/vNjp/7/a6P/D3eT/xN/j/8Tf4//E3+P/xuDg/8nk4f/J5OH/x+Pj/7/f7P/D4O7/xeHs/8bj5//I5eL/yObh/8nm4//H5Oj/x+Tr/8fk6//H5Ov/x+Tt/8Li7//E4/L/xuPy/8jj8f/K5/D/yuXv/8zk8P/K5PD/yebv/8rn8P/K5vH/yeTy/8nk8v/L5fP/zeTz/8rk8v/K5fP/yOXz/8rk9P/M5fX/y+Xz/8vl8//K5fP/yubx/8nl8P/J5fD/yuTy/8rk8P/J5u3/yObr/8nm6//I5er/yebr/8jl6v/I5er/x+Pq/8fl5v/H5uX/yebj/8jl4v/I5OX/xeHs/8Hg7//A4Ov/w+Hm/8nl5v/H4ub/xd/m/8Pe6P/D3uj/wtzo/8Hc6v+/2+z/vdrp/7/Z6f/A2ub/vtnj/7/a5P+/2eX/vdjm/77Y6P+81eX/vdbm/7vU5P+60+P/utPj/7rT4/+60+P/udLi/7jR4f+40OL/udHj/7nR4/+50eP/udHj/7nT5P+40eH/t9Dg/7jQ4v+40OL/uNHh/7jR4f+40eH/uNHh/7nS4v+60+P/utHg/73U4/++1eX/v9bm/7zW5P+91+P/utfl/7zX5f++2OT/vtjk/73Y5v+92er/vNjp/7/Z5//D3eP/w9/g/8Tg4P/H4t//yuPf/8vi3f/I4tz/yOPf/8Dg7f/D4O7/xOHq/8Xi5v/I5uH/yufe/8rm4P/I5OT/xuXo/8fl6v/I5ez/yOXu/8Xk8//D4/b/xuT3/8jk9f/M5/H/zOTw/83l8f/O5/H/zOfx/8vo8f/L5/L/y+b0/83o9v/M5/X/zef1/83n9f/N5vb/zOb2/8zm9v/N5ff/zef1/8zn9f/M5vb/zef3/8zl9f/M5fX/y+b0/8zo8//L6O//yefs/8jl7P/J5u3/yubt/8nm6//L5ev/yuTq/8nl5f/J5OD/zOfe/8rm4P/J5eb/xeHs/8Hg7//B4ez/xeTn/8jk5P/K5OT/yOTl/8Pg5f/D3+b/w97o/8Hb6f+62+r/vtvq/7/Z6f/A2uj/wNrm/73Z5P++2uX/v9ro/77X5/+81eX/vNbk/73X5f+61OL/udPj/7rT4/+60+P/udPh/7jR4f+50eP/udHj/7nR4/+50eP/udHj/7rS5P+40eH/t8/h/7jQ4v+40OL/uNHh/7jS4P+40uD/udLi/7nS4v+80+L/vdTj/73U4//A1OX/vtXk/73X4/+7197/u9fi/7zY4/+92eT/v9rk/8Hb4v/D2+H/xdri/8Pb5//B3e7/wuH2/8Xk/f/G5P//xOP//8Ti///F4f//wt78/8jk5f/G4+j/xuLt/8bk9//I5v//yuj//8zq///P6v7/y+j2/8fk8v/H5PL/yeXw/9Lr7//R6ef/0+3t/9Hr8f/K5PL/zOb0/8vl8//L5fH/zefz/9Hp9f/R6fX/z+nw/8zo7//M6O//zOfx/9Do9P/Q6PT/zebw/8zn8f/M6fL/zujv/8zo7//M6fD/zenw/87n8f/O5vL/zefz/8zn9f/L5fX/1Ov//9Xr///R6P7/zOX5/8rk9P/I5fT/y+f4/8no/f/L5///yuX//8jj/f/F4/T/x+Xq/8nl5f/F4uf/w+Dv/8Df9v/F4Pr/xuP4/8Xj9v/D4fT/xN7v/8Xc6//B2+H/xd3j/8be5P/B2uT/v9vm/73b5v+92uP/wNvl/8Db5f+/2ef/vNbk/7zW5P+81uT/utTi/7nS4v+50uL/utTi/7jR4f+50eP/udHj/7jQ4v+50eP/udHj/7jS4/+60OL/udHj/7jQ5P+40OL/uNHh/7nS4v+50uL/udLi/7vS4f+91OP/vdTj/77V5f++1eX/v9bl/73X4/+92OL/vdrj/7zY4/+92eT/wNvl/8Hb4f/J3+X/y+Ly/7/b/f+nyf7/j7T4/32h7/9wk+n/a5Ds/3KX8/+EqPz/o8L//83n9//J5vX/v9zx/6zJ7v+Qrer/fJvm/3uY2/+NqNT/tc/n/83n+P/I4/f/wdrk/5SonP9/j3f/kaKN/8jd1P/T7fn/z+n1/9Dq9v/V7vj/0ubx/9Pk7f/S5Ov/1+rv/9ju8//W7vT/1u31/87k7//O4u3/2e72/9Ls8//M6fD/z+ft/87o7v/N6u7/zOnu/83p8P/N6fD/zejy/8vl9f/Q5f//scDn/5GcyP+ntNr/wNbv/8rk9f/C3/T/s8/t/5+/8P+Wsu7/mLL1/6O/+/+11fj/xOLt/8zo6f/P6fn/xeL//7XT//+oxf//ob7//6C//v+lxv7/stD//8Hb///M5Pb/yuLu/8fg5P/E3uT/v9zl/77b6f+/2+b/vtrh/8Pd5P/A2ub/vNbm/7vV5f+91+X/u9Xj/7nS4v+50uL/utTk/7nT5P+50eP/udHj/7nR4/+50eP/uNLj/7jS4/+40OL/uNDi/7jQ4v+40eH/t9Dg/7jR4f+60+P/u9Li/77T4v+91eH/u9Xj/7vV4/+91+X/vdfl/73X5f+92Ob/vNfl/77Y5P++2eP/v9vm/7zb8P+ozPD/faXg/1R/0P85Zcr/KFPI/yJLyv8gSMn/HUbF/xxHvP8hSLX/LlK9/1yCyv+hxPz/tdP8/32Zwv9fe7j/Yn/K/3aR1P+fuOD/v9Pk/7jN1f/N4+7/2vD2/8DTyv95hnD/eYVx/8DMwP/E3OL/wNje/7zQ1f+QoqP/e4mI/3qGiP+Fj5b/mKSw/5qnt/++zN//xdTn/5mou/90g5b/laa5/8Xa8P/S6v//2e3//9js///V6v//0en//83o/f/I5vn/xeP0/9Ls/f+es87/QE54/zQ+bv+HkbP/2ur2/8fe2v/K5Or/ssvf/3ydz/9ohMH/XXa2/2J8sv9+m8L/qsrt/7XX//+LrOT/XoDC/0Vmtf82Wrj/L1TC/y1SxP8xV8P/PmXH/0920v9yl9v/mb7y/7va+f/A3ez/wdzm/8Da5v/A2uj/wNro/7/Z5f/B2+n/v9np/73X5/+81uT/vtjm/7zW5P+50uL/utPj/7nT5P+60uT/udHj/7jQ4v+50eP/uNLj/7jS4/+40OL/uNDi/7jR4f+40uD/uNLg/7nT4f+70uL/u9Lh/7/V4f+81OD/u9Xh/7zW4v+91+P/vdfj/77Y5v+91+f/u9fo/8DZ4//B2+L/u9rv/5C+7f9Ujdz/Mm7Y/yhh3P8lWdz/JFPd/yFM1/8gS9D/JU/K/zFazv8+Ztf/Rm3h/z9v7P9jje7/j7Ht/7LP9v/M6P//z+n//9Tr///R4u//g5OM/3KBc/+Aj4f/0ePi/9zx8//V6er/vMnH/4eMiv92jYn/pra1/4SOjv9fZmP/aXBr/3d+gf+Rl6r/d3mb/29xmv9laJX/bG+c/4SHs/+Ynsv/oKra/52m3/+bpOP/n6np/6Sr8P+rtPj/tMH//7vR///B3v//yOX//9Lt///K4vr/ip69/4ubv//a6vv/tsS4/3+Qb/+MnYL/1Ojc/9Lv///N6f//zuf//8Tf+v+zz/H/osT//3Wb8/9GbtT/O2LF/zRbvf8pUr//IEvK/xxH0v8fTdf/IVDa/x9T3P8lXNX/OW7W/2mZ4f+r0Pb/wtzs/8Xc5P/D2+f/wdrq/8Da6P/C2ej/wdvp/7/a6P+91+X/vNbk/73X5f+60+P/utLk/7rT4/+60+P/udHj/7jQ4v+50eP/udHj/7nR4/+50eP/t8/h/7jR4f+40eH/udPh/7nT4f+70uH/v9Tj/7zU4P+91eH/vtbi/7/X4/+/1+P/vdfj/77Z4/+92uH/u9nk/8Db3//C3uX/qM/v/2yk5f9MjOr/PHvr/zBn4P8qXdv/LmDe/zho3v9Kduf/Vn/z/0958P9Fbuz/PGXk/y1Yzf81XsH/bpTc/6PG8v+uzeb/qcPP/9Lk5f+hsKL/eoZq/5eigv92g23/vM3J/9vx/P+3ytn/Z3F7/2FhZ/+HmZL/qbOz/2dpcf9vbnf/dniD/3+Amv9WVIL/PDd0/zw4ev9CPIP/SEGK/0xEkf9MSJT/SEaY/0A9mf8+NZ3/OTSh/zs2o/89PKT/R02s/1Vmt/9lfsT/fpjU/5q04v+2zvL/yeH//8/m///Y7Pf/oLCe/46acP99iFb/kZ9v/9Tt8f+zztj/qsrd/7nb+P+hxPD/ZYnJ/z5lwf9FbuL/Unz9/1WA//9TgP//Tnn4/z5r6v8uW+D/JVbg/yJX5P8rZeb/OXbu/0uG6f95qOb/tdbw/8Pd5P/D3eP/wNzj/8Hc5v/A2uH/wdrk/8Da5v++2Ob/v9bl/7zW5P+71eX/udPj/7rT4/+60+P/utPj/7nS4v+50eP/u9Hj/7rS5P+40OL/uNDi/7jQ4v+40eH/udPh/7nT3/++1uL/vdXh/73V4f+81uL/vNbi/7/X4/++2OT/vdji/73Z4P/A3eL/w+Dp/8Th5v++3uv/mMLn/3ir6f9toOn/YpDd/12L3/9Wh+n/S4Do/1SE7v9Kd+b/LFfW/xlG0/8SQMr/ETu+/1x5vv+gwP//mb7//3if3f9+oMv/qcTZ/9ru7/+ToY//kJt7/5Gefv+BkYD/zt7d/8ra4f9we4P/XF5o/25seP+ks7b/kpmo/21uiv9saZD/XluM/0lEgf9COYL/RTyM/0U+j/9KP5X/Szqb/0YynP9CMJv/Pi+b/0Mxpv9GMa//PS6u/zwxrf9BPK//Q0au/0RNp/9BT6H/O0uX/ztLkP8+UIv/TWGQ/2+Dpv+0yd7/y9va/4yZf/+SnWv/gItM/7/U0f/F4O7/f6PL/2iT0v98pu3/qc7//4+v8P86W7j/ETe7/xhB3v8lT+T/PGTl/1F67v9Xg/T/UX/u/1B+6v9Sft3/ToPk/1mS7f9xpef/nsTn/8Te7v/H4ej/yOLp/8Le5f/A2uD/v9ng/7/Z5f/A2ub/vdfj/7vV4/+61uf/udbl/7rT4/+60+P/utPj/7rT4/+50eP/u9Hj/7rS5P+50eX/udHl/7jQ4v+50uL/udPh/7rU4v+91OP/vNPi/7zW5P+91+P/vdfj/73X4/+71+L/wNnp/8Xd8f+5zuT/scHe/7HG4f+10Or/sdPx/53B5/+NsNv/kbbo/3ej4v9ShNb/TILn/zVn3/8ZRc7/GUXW/xVAzf8pUMr/e57//8bd//+EoN3/WXnC/2uM0f+LrN7/wN/+/9Dq9v+XqqH/jZ2G/4mZh/+jtbT/2+n1/46Un/9dXGb/WVZl/2Vjef9vdJP/XWCG/1BRhP9GQoT/RTyM/0xClf9MQ5T/U0qa/1xRp/9TQaT/RzGh/0gupP9HLqb/Ri2l/0Irpf9BKaf/Piyh/0Y5p/9MSK3/WVq0/2drvv95fs3/ipHg/5+m9f+1vv//yNP//9Hf///R4f//1ur8/7zPzP+ImXj/eYdR/6vAwv/U7///nsD1/2qR4P9Rd8//VnnD/6C8/P+82v//aIjr/yNGxv8bQND/HELQ/yJKy/89adz/VIHj/1eE2/97o+T/fanp/3yo4/+Tu+v/qsru/7fM6/+zw+D/s8Pg/73Q6//H3/P/wtzq/73X4/+/2eX/vtrl/7vV5f+71eb/vtjo/7nT4/+50uL/utPj/7rT4/+50uL/uNDi/7rS5P+50eX/udHj/7rT4/+50+H/udPh/7rT4/+60+P/vNXl/7zW5P+81uL/vNjj/7vX4v/D3ev/t83m/4KOtv9nbaL/aWqk/1Jdkf92iK3/rsLU/6i7yP+00fD/jbv1/0+I1/9Sier/OGrg/xVC0/8XQ97/Fz/H/0lszv+qxv//xuD//1+A0P9NaLj/cYbK/4GWyf+82Pf/xOT3/8/s9f+ds7H/l6mi/6y9uv/L2+j/ucLd/1tbef9QSmn/QDxg/zk4ZP8zM2//ODh0/0A+gP9JQY7/Rz2Q/0A3h/9STJP/Z2Cr/1lHpP9HLpz/SCyj/0Ysov9EKqD/Ryyk/0w0qv9SO6//a2C2/3xzxP98eMT/dHO7/25utP9qarD/a2qy/29xuP+Ahcr/m6Dd/7a/8f/O2v//1+n//93z/v/G2s7/eotw/6a6v//U7f3/xeH//46p2/9phM7/V3TW/zpavv+Anuv/z+z//5y58v89XcH/GD3P/xxD4f8ZRM//OGfb/06D6/9Wjtv/l8H8/6rI6/+huM7/tcjj/2l2ov9PWJH/Y2in/2Vspf+DkLz/vNHs/8Te7P+72OH/vtrl/73Y5v+71OT/vNXl/7vT5f+60uT/utPj/7rT4/+60+P/uNLj/7rS5P+50eP/utPj/7nT4f+509//u9Pf/7rT4/+70+X/vNXl/7vX4v+91+P/vtbi/8fe7f+ou9D/cn6g/2xzpf9xcbH/aWWn/2Nqo/+jsdX/y9fh/9bk6v+42/3/X5rp/0iN+v86dfD/G0jP/x9H1f8eR8b/Z4ni/8La///U5f//e4ym/zBVw/9ceM//dYa+/8DQ5//T6e//zufp/93z+P/U5u3/xdDY/5ihr/97gJn/ZGWL/1hVhv9fWZL/c26s/3Fvsf9jXq3/W1ah/09Ikf9COIT/PzR9/11Wmf92crT/YFeo/0Mulf9IK6D/Siyj/0wxpv9RN6z/VTuw/0s1pf9OOqX/WFOQ/0dDfv88OXH/NzZu/zg4dP84N3f/ODd3/zo5d/84OnT/PEB1/0dMff9faJT/iJe4/7fK3//g8v3/z9/l/7/V2//V6/D/1err/9Pm7v+DlsH/VW7O/0pp5P8zUq//h6HG/9/2//+00f//TG/d/xc8zv8fR9z/FUbS/zJs9P9EjPf/bqDo/8jg/P/U3+f/xNHh/5aiyv9VXZn/XF6l/2tts/9nbqf/cH2j/7TG3f/J4O//utXj/73Y5v+91+X/vdTj/73W5v+70+X/utPj/7rT4/+71OT/utLk/7rS5P+60uT/utPj/7rU4v+61OL/utTi/7zT4v++1eX/vNbk/7zY4/++2eP/z+Lv/56pvf9YYH7/XGGI/2Jok/9xdqP/kpvA/7rM6//K3/T/zN/n/8vh7P+kyu3/YJzo/0uO//8dVdz/HUbL/zdZxP+Lru7/x+T//9Lp//+TpM//RVWX/1RswP9sgb//t8zs/9Lo9P/X7fP/2Ony/7jA0f9/f5f/R0Ng/zIsS/8wKk3/NjJb/1hVhv9xb6v/Yl6l/1FJlv9STZz/QTuK/zYvev9BOX//cGup/4aCxP90a7z/RTOW/084pf9XPa//WkCy/1Y7sP9PNav/STKk/0Yynf9QO6H/bmui/4eHt/+Jirb/d3qn/2lsn/9lZp7/ZGWf/2Rlnf9jZJz/YmSa/2Jkmv9eYpf/XGOV/212ov+QnMD/usfn/87l9P/S6fH/0ufp/9To7f/K3/X/fJDJ/1Nnvv9TZsf/QFOe/5603v/T7v//w+D//3OU5P8iR7//F0PU/xdH4v9CiP3/ZZrq/6zK7f/S5O//0OLt/83f9v+rvN3/fYmz/2Bqmv9cYJP/VFeE/1RZev+otsz/zeT0/73X4/+/2eX/u9Xj/73X5f+91ub/utPj/7rT4/+60+P/utPj/7nS4v+50uL/vNPj/7zT4/+71OT/udTi/77V5P+/1uX/vdfj/7va4//C3uX/ipqn/0lNZv9qZ47/kJC4/6+31P/J1ef/0Ozt/8vq7f/G5uz/w+Du/8Lg8/+iyuf/dqvk/0R+5f8SRMz/RWvn/6bF///Q7fb/0Ork/8LZ8/9KX7H/PE/I/4GFqP/Bzuj/zuf3/8nm9P+qwtb/XWiG/y0rT/8mGEH/MyBL/z8rWP9bTXf/ioKq/4GAp/9aXIz/SESF/1ZMmf9CPob/OjSD/1NNmv+IiMj/kpPP/4aCyv9jUbT/WkO3/1dAsv9LN6L/RS2d/0gspP9LMqr/SDWk/0w5oP9iT7D/bWmk/3h6qv+IjrP/k5vA/4OItf9iZZj/S0yE/0NEfv9CQX//REOB/0NCgP9HRob/TEuP/1NVlv9jaqP/jpjH/7TM5P/E2/H/0en//9Ds///U7v7/1ur1/5ulx/9YYbj/QlLK/0hevf/E3Pj/2PDk/9Lv/v+QsP//MFXb/xQ61P8xb9v/cqPz/6HG8v/E4vX/x+Tt/8rn6//T7/D/1Ozy/8DU5v+jq9D/hYKw/1pWgP89Q2D/mKm8/8Xf6/+71uD/vNjj/7rU4P+91+X/u9Tk/7rT4/+50uL/udLi/7nT4f+80+P/utPj/7vV4/+71eH/utXj/7zV5f+91ub/v9bl/8Pb5/+husr/e5Or/6S81P+81eX/yuLo/8/o6v/K4+X/wtOx/7HEo/+4yaj/0d/D/9nt6P+u0vj/dabs/0h4wP96n9H/vuD+/7Xd+v+y3f7/yOr//5qvz/9EVIP/cILD/77Z5//X6/z/093u/6yzwv9tb4H/VVJs/1hQb/9cWW//XWNw/4aOpf+fpNH/aWWn/0xFjv9MRIv/UEaT/1FEmP9AP4P/b3Ct/5ib0v+RlMv/goHB/3hru/9SOJb/UC+X/0knk/9EJpf/SS2l/04xsP9LMrL/Tzm6/09Bxf9SR83/ZFvU/3dx3P+Igtv/kY/V/6Om3f+wt+L/n6nL/3yHpf9lb5H/aGyc/25sp/90da3/fIGy/3yFsf98g7X/c3Sw/2hqpP9mZqL/cG+t/4qMzP+xuuz/zOH8/9fx/f+vxd7/cH6u/0ZSiP+XqtD/0e///8Hk+P/A5v//s9n//3SZxf8tXsr/bprZ/7HW6v/M5Pr/ucT//6eo//+kpv7/s773/8ne+f/P6fX/y+Pv/7vU5P+UsMH/c5Sk/67L2v/C2ub/vdrj/7zW5P+81eX/vNXl/7jS4v+40uL/udLi/7nT4f+70+X/vNPi/73U4/+61eP/utTk/73X4/+/1+P/vdfn/7zW5v/I2+L/2eLf/77Gxf/K3eT/xOHm/7fQwv+ElHL/dH9H/3J9S/91glb/fY9o/6i/qf/F5fD/msDq/5/H/P+34v//hbjj/4q/6v+WxO3/w9///4KQrf9/i6//ytr//9Ls+v+8z97/iZOk/2Jpff9fY3v/X2F5/11ec/9fYHT/kJSw/6Sp0P9WVY3/RD6F/01Ckv9HPo7/VE2W/0ZEhv+Gh8T/mpra/4SExP92dLr/ioLP/0k3kP9CJ4f/SCuO/0stkv9RM5r/TzGc/0ormP9LK5r/Si6f/1E6rv9YRLv/XkrB/1pKwP9dU8X/amXO/3Jwyv+ChMr/pKji/8jM//+8wPP/f4S1/2ZrmP9hZpP/VFiJ/0NHfP86PnH/NDho/zAzcP8zNG7/NDVt/zk+df9PW4v/hpa6/7zQ6f/T6P//y97//4ucx/+BlLn/yub//57H6P+UxO7/jL3t/7Xj//+fx///lLbs/7nQ//+equz/bHDI/1haxv9ZV8//XlzN/3h81P+rvvH/xeD0/8rg5f/N197/3ebw/8XW4/+72Ob/vtrl/77a5f+81uT/vdbm/7rU5P+50+P/utPj/7rT4/+61OX/wNXk/7/V4f+61OT/utbn/7/X4//B2uT/udjn/7XW5f/V5+b/f35p/2tpUf/g7+f/qse+/2d5VP97fjb/gopE/4aLTf+Ci1P/fpNi/4Keev+oxLH/0evx/8fm//+QxPP/Zqrl/47S//96q9v/ss/u/8DR5v/T5Pf/0OX7/83k8//N4O3/r7zM/4CFnv9mbIn/aHGF/4SPnf/ByeD/qKjY/0ZChP9FPof/UUeU/0o+kP9VTJ3/UE+R/5adzv+ko+P/dXS4/3Bttf+HgdD/cWO1/0Eqf/9JLYb/Sy6E/1M2i/9TOIj/VDeH/1k6if9aO4r/VzqK/1A2iv9ROJD/XUOn/2lTw/9jVdP/W1DW/2Ja1/9pYtH/bmfI/3Zwx/+cnOL/uLzv/4WOs/9ncJL/X2SR/2BimP9mZ5n/cXWe/3d8s/+FiLv/jpLC/5SbzP+apNP/qbXd/8LS7//N4/z/zub+/9Tr///L4vj/u9r5/3Gj0f+V1P//drbt/4zE9f/U8Pv/zN///3+F6P9nZdz/e3ru/11d0/9hXeX/X1Lu/1dM3v9VW8T/oLfp/9vs+f9jYWH/oJiZ/9vl7/+12Ob/vdvm/73Z5P+81uT/vdfl/7zV5f+50eP/utLk/7rS5P+61OT/vdTj/73U4/+61OT/vNbm/7/X4//A2OT/utfl/73g6v+wysr/MDot/6Opkv/a58//bH1b/3F9Qf+Mjjz/doNF/3yDRv+Kk1r/jqNy/4ypgv+UrZP/x9rR/83q+f+Iv+r/c7z4/4rQ//92qtP/vd/2/8/r9v/J5ez/yeTu/83i8f+2ydb/k6Cw/46Uq/+prMj/w8zg/9Lg8/+lrNP/QDl8/0w8k/9RQZn/TUSU/1NMlf9aV5z/qKzn/6Wu4P9wa7b/a2m1/3Nvu/+Kf8f/W0mM/1Q5ef9gRYX/Z0yL/2hRiP9mUYL/Y09+/15Nef9eTXn/XUx4/1tIef9YR3r/Tz59/0s7if9VSKr/aFvP/2FT1v9eT9n/bV7l/3dr4f9dV7D/fn+8/9je///EzvD/nKfH/4mStP9/g6z/amqY/1piiv9dZY3/Y2mW/2Rsm/9tc6D/h4+0/6iz0f/D2O7/zuf3/87n6//V7vD/vuP3/2igz/+Lz///gsT//4XA7f/e8fn/n6jn/19f1f9kXeb/hIL6/25w3P9aWtD/W1Le/2BU6v9XUt3/Wl/G/8jQ//+PkZz/Njo0/8XY2/+62+//vNrl/77Z5/++2Ob/vNXl/73W5v+60uT/udHj/7rS5P+71eH/u9Xj/7vU5P+91+P/vdfj/77Y5v++2Ob/vtnj/8Pg5/+pxs//jaeu/9/w5/+epoH/cHg5/32EQf94gEH/h5hl/6ezf/+rtoT/q8CT/5y3lf+PqZL/sse//8/s+v+Zyev/isj4/3+35v+cx+j/yOn5/8/s9f/d8/7/4fH//9/s/P/V3vL/x8vj/8TF2f+3ucv/o6e//6es0/9OTIj/ST+M/1dFnv9PP5f/VU6Z/1NUjv+1uuv/qq7o/25utP9wZLz/Yluw/3x4w/+Ffbn/cl+K/3JZf/9uWHv/ZlJ1/2NVcf9rYnf/dG+E/4SDl/+SkaX/m5qu/56dsf+Yma7/j5Cq/4GAoP9mY5H/VU2T/15Stv9lV9X/X0/c/2td4f+AdeP/WVGo/4aFx//N0///1uT//8PT6v+rtNb/uLfp/6Wu0P98hav/YGaT/1hejf9TV4f/UVSA/11ki/97h6v/s8Te/9/x/P/Z8PL/zO38/4u84v9+t+7/j8b5/5nK8P/R3///eYDP/2Ji1v9wb+f/lZj//5CU8/+QkfP/envj/11Z0P9YUdj/U0vU/31+4P/Q3///jqed/7LPzP/A2vL/vtvk/77Z5/+/2Oj/vNXl/7zX5f+61OT/udHj/7rS5P+71eH/utPj/7vU5P+/2OL/v9ji/73Y5v+81+X/wtzj/8Hb4f/F3+v/1O78/8fa0f91f1D/dnoz/4aNUP+uvJP/rbuF/42ZZ/+Dk2P/hJtu/6K8mP+hvKj/orq4/83q+f+03PX/ncbm/63Q8v/W6///3Oj//8nN4P+dmrD/dG2I/2BXbP9TRmb/Tz9h/0Q7UP9ERFD/lZay/2pkn/9PRZL/UUaW/0xCj/9NQ4//VFCR/7e77P+3ver/bGys/21jvf9sXLP/ZFmv/4yG0/+Efbb/Y1l9/2JWbP9zan7/lJCj/7i4xv/T1d//3+bv/+Tu+P/n8P3/5/H7/+Xy+v/l8vr/4/D4/+Ps9f/e5PH/wcPh/5CQxv9ua7v/YlvD/2NY0v9zZ+X/bmTW/19WsP+nqOT/rrjg/6m42f+ZpMr/aW+Y/4OJtv/Cxvb/yc39/5mez/+Ij8H/kZLO/4WCx/9vbrD/Zmui/3+Gsf+1weP/1un//8nq//+fyOj/mMDd/77j//+9y///aXHL/3R24v+Slf3/cXXU/29x1/9xbtz/lJL8/6Gh//93dOf/UkvR/11bzP+3xfb/2vXy/8fi3/+/1e7/v9zl/7/a6P++1+f/vdjm/7zX5f+81+X/utPj/7vT5f+71eP/u9Xj/7zW5P+/2OL/wNnj/73Y4v++2uX/v9zj/8Te5f+/1Nz/jJ2g/7bCrv9kbj//k5xd/7vGjv+JlGz/eIE+/3iESv+JnGn/h55q/4Odbf+mwKL/r8rG/8nk8v/H5fj/yOP3/9Xm//+zs9f/b16D/0QpS/81FTj/MxE5/zYaOP8/HUX/QSRL/0M1Tf+JiJj/g4Sm/1lOkv9URJv/QTiJ/1JRkf9xcaf/vrzw/9HS//9kZKD/dW26/3Beu/9lWKj/gXbG/5yV3v94dK//dHOa/6qtwv/W3ez/5PD8/+Hv+//f6/X/3Ojy/9vn8//Y5vL/2Oby/9Tl7v/V5u//2Ofw/9rn7//d6PD/4ez6/+Lw///Q2vj/oqbZ/25qw/9jWtL/eW7q/1hNtf+Ri9r/mpra/05Vjv+stub/s77k/15inP8zMnD/YF6a/6Sm4P9sca7/Q0WT/2FcuP93b87/gHvQ/3t7yf+DhtH/mqPj/7zQ+f/S8P//xuX0/9Hs//+xwv//c3nS/5mZ//9nZ9P/YGLO/3Z07/9ZUt3/WU/X/25o3f+cnf//iYv7/1ZYtv+fo9T/jZmj/8re4/+/2Oz/v9vm/7/b5v+82OP/vNrl/7nW5P+81+X/vNXl/7rT4/+71eP/u9Xj/77W4v+92OL/vdji/77Z4/++2+T/vdrj/8rn7v+SqK3/XWxo/7C8pv92hFr/tMOK/3iGTP93gEj/folB/5CfYv+gs3z/h6Bk/42na/+Ionr/tc7E/8vl8f/M5fX/0OLz/6Clvv9AM1n/LhM7/z4cQf9EIET/QR9E/z4dQv8/IEH/TjVR/2xedv+al7H/W1qG/2BYnv9QQJf/f3HD/3x3tP+ZnsX/4ub//3p3tf9sX7P/dma9/2pdrf93brf/m5bb/4yKxv+lqdn/0dr8/+Dt///Y6Pj/0uXy/9Pm8//W5/T/2eb0/9ro9P/a5/X/2+j2/9rn9f/Z6fX/2uj0/9rn9f/Z5vb/1+fz/9Xo7//a7fL/4e///8TM+/98fc3/a2fO/2Vbxv93bMz/n5jp/09Rkv9nbqf/p67l/6Gm3f+Dgsb/RD6N/y4odf+VlNz/gYXT/zI0jP8mJYH/LCqE/zUzjf84PJX/RlGj/21/uv+txub/zen6/9Hs+v+3yfj/lp3s/3d15v9fV9r/YVzf/4KA//9pZe3/XlTk/1tS3/9RTtP/jZH//4uR3v+bncX/TFNi/7DFzf+/4O//vtrl/8Dd5v++2+T/vdnk/73Y5v+81ub/vNXl/7rT4/+81uT/u9Xj/7/X4/++2eP/vtrh/7/Z5f/A2ub/v9rk/8Hd5P+00Nf/v9Xa/7XHuv+isYv/eolM/3qFQf99h0X/h5da/6q8h/+TqXX/i6Np/5Cpb/+HoXn/pL2z/87o9P/N5vb/oK7B/0xJY/9KOlz/VD5h/004WP9JNFT/RzJS/1Q8Xv9sW3D/cWdz/4uClv9+d5z/VlKG/19an/9zZbf/aFeo/3Blo//T2P//q7Ld/1hSmf9/bcv/Z1eu/4yFyP+al9z/lpfP/7a95P/a5f//2ef6/9Xk9P/V5vP/1uf0/9jo9P/X5/P/1+fz/9nn8//a6PT/2uj0/9ro9P/Z5/P/2ejx/9nm9P/Z5vT/2ejx/9rq8f/Z6PH/1ubz/9zs/P/U4v//mJ3a/21oxP9oXsL/mZbl/1ldmP9pa6v/h4TT/6my3v9dYqH/Xlmu/1pPrP8eEmr/j47Y/6+4+P9/icn/jpPY/42Q2v94fsn/WGWz/0pdpv9kerT/q8bo/8vr+P/M4P//l6Hn/2Bb1P9lWe3/YVnm/39/9f+Pkv7/ZWPa/1xU4f9cUuz/U03U/4uP6P+5xOr/rcDI/7/Z4P+92+z/v9nl/8Db5f/A2+X/vtjk/77X5/+81Ob/vNTm/7nT4/+81uL/vdbm/73X5f++2eP/v9vi/7/b5v+/2uj/xNrl/87g6//B0uX/wdbr/9Hl5v+MmXP/dn88/4GMRv9+i1P/s8aN/32TY/+bsYf/jaV1/42mdP+MpYP/rMjC/8/q+P/K4PL/s7rO/6iiu/+hk6//kISg/4uBmP+HepL/i3yY/4l5mP+Deof/Z2Zq/46Lm/9fVoH/YleW/3hstP9YR5H/ZFKZ/7mv6//Z2f//amyi/2hhrP9yYrr/fXLC/5eT1P+Eh77/ucHp/9zp///Z6PH/2ufv/9vn8f/b5/P/3Oj0/9zo9P/b5/P/2uny/9jp8v/Y6fL/2uny/9no8f/Z6PH/2enw/9no8f/Z6fD/2+nv/9zo8v/a5vj/2Of3/9bp7v/Y6+7/3Oj//6qs7P9aWan/jpDW/2Roov9mZaf/hn/U/5Sezf+6wvf/SEqQ/zwzjv9SQ6X/FQte/4aKxf+HlMD/TVeG/2Vpnv+Cg7//lJrb/5eg6f+Wpun/pLnm/8HZ8f/U6/r/nKfr/15b2f9kW+v/ZmLf/3h84v9yeNf/nKH//2Nh2P9dVOT/WU3l/2Rh1P/G0v//zubm/8Ta3//N3fr/wdzm/8Db5f/A2ub/vtjm/7/Y6P+91ef/vdbm/7vV5f++1eT/vNbm/7zW5v/A2OT/wNzj/7zd5v+92+b/zd7r/56ftP9sZYb/dXaY/8LN0f+MmXP/eoRC/3mFSf+qupH/maVj/26BTv+guJX/or2W/4iiev+XtJv/vtzd/87o+f/H1ev/kpGl/15Ua/9NP1v/XE1o/048U/9AKkP/QCZE/0s5Vv9hVWf/a2Zv/4aClf9USnj/cFyk/1U7if9YQ4f/kYe8/9LP//+mpOD/WlGa/2tgsP94cL3/kYvS/4uJy/+1v+H/2ub+/9jl8//Z6fD/2+jw/9vn8f/d6fX/3Oj0/9zo9P/a6PT/2+n1/9rp8v/a6PT/2efz/9no8f/a6vH/2uny/9rp8v/Z6fD/2ejx/9zo9P/d6Pb/2uf1/9fo8f/W6O//1uX1/+Ls//+Xncr/en64/3Bysv9bWp7/jorS/32Ew/+apNT/ydP//1JTl/8zKIn/QzOe/xoPZf+Qkcv/gYe2/y8wYv8fGFH/IBVT/ysjYv9FRoD/ho69/9Ld///U8e7/tMD//2xq5v9gXtr/cnjZ/42S9f9YVs3/fXvy/5md//9cXcv/WFHX/3xz6//Awfn/fISE/21weP+im8j/x+Pq/7/a5P/A2ub/vtjk/77Y5v+91ub/vdbm/7zW5P++1eT/vNfl/73Y5v+/2eX/wNrm/7vc5f/B4uv/sb7O/2FQcf92V4T/c1+C/6CjqP+0wqb/aXdH/5WidP+nuZL/gog5/4ORV/+Lonz/orye/5WxlP+tyrv/zOjv/8/k+f+Tmq7/X1tu/2xfd/+AcI//Zk9v/1M1Uv9PLkn/WzlY/29Xef9hTGX/eW1//3hyi/9bT4H/XUGN/1w7jP98Z6X/oqHJ/9HX//90brX/Xk2o/3NmvP+TkNX/iInF/6mp5f/c6Pr/2eb2/9nm9P/Z5vT/2uf1/9rn9f/a5/X/2Oj1/9jo9P/Z5/P/2uj0/9vm9P/a5/X/2uj0/9ro9P/Y5vL/2eb0/9ro9P/Y6PX/2Oj1/9nn8//c6fH/2urx/9nm9P/X5fj/1+b2/9fo8f/Y5vj/maHJ/3JzsP9cW53/h4jE/4CDzf+EjMH/ucfr/7jC8v9VUqf/NCWY/zMglf8ZDmv/l5Pa/4+Myv9KQYD/NCVj/yQUSv8hF0X/KyhV/3l6rP/M5+P/ydf//5CT/P9eY8b/l6L0/4eL9P9eV+j/Vkzf/4yN+/+Gj+b/UVe2/6yp//+flsj/bmJu/3Ngc/9kSXv/pL/J/8Xf6/+/2eX/v9nl/77Y5P+/2ef/vtfn/73W5v+91ub/vNjj/73Z5P+/2ef/wNro/7rb5P/G5uz/oaq+/1tGbP98W4j/cl+A/56irf/X6uH/fZJ5/6i6k/+Glmb/iI5B/4OQUv+RpXr/kaqO/6W/sf+/29v/1Oz4/7C/0v9jZ3r/fHaJ/4h7k/9cSmf/SjJS/1g5WP9RM1D/ak5r/2lOdv9bRmb/f3OJ/21lg/9VRXr/WjuK/21NnP99bKX/tbnc/7i+6/9iW6b/XU2r/4R40P+Jicn/mJ7N/9Xa///a5/X/2OXz/9nm9P/a5/X/2uf1/9jn9//Z6Pj/2en2/9jo9P/a6PT/2uf1/9zn9f/d6Pb/2+n1/9ro9P/a5/X/2efz/9vo9v/b6Pb/2+j2/9ro9P/a6vH/2+vy/9zp9//b5/n/2Of3/9bn8P/Z6fX/2OL6/4qOt/9hYpr/f4K//3t+wv+LlM3/k6DM/6m04P+bn+D/W1a5/zkspv8mF5H/IRR6/4yG1f+Uk9X/Y2Gd/1tSiv9RRXf/MSha/z06bP+ft8P/1eX//6Ww+v96g9P/kJru/3N24/9hWuv/W1Lp/2Nh3P+Zo/f/doXE/87Y//+Zlrb/bV10/3RcfP9hRHL/kau5/8vj7//A2eP/wNvl/77a5f/A2ur/vdbm/73W5v+91+X/vNjj/7/c5f+/2ef/wNro/73c5f/C3+j/xtLk/3dvjv9gUnT/fnuV/8LR4f/N5Oz/wdfS/6u/ov90h1b/gpBQ/4OSWf+Wqn//lKyU/6vGwv/N6PL/zeHy/5CarP+Dg5X/h4CV/1pNZ/9SQF3/UDpX/1lDYP9iTmv/ZFNu/2VJd/9YR2j/enKJ/2Zdfv9VP3n/YUKN/2xSmP+Lf7P/xMbu/6Wp2v+Ggsr/e3LJ/4uF1v+Oj8v/xM3u/9/p+//Y5fP/2eb0/9nn8//U4+z/1eTt/9fl8f/V4vD/1uPx/9fm7//V5O3/1OHv/9Dd7f/X5PL/1uLu/9bk8P/W4/H/1+bv/9Ti7v/Y4/H/1+Pv/9jk7v/W5PD/0+Pw/9Xj7//Y5O7/1uTw/9fm9v/V5fL/4fD5/7rG2P9la5T/fX+//3Z9tP+Undb/gozC/6Or4P+Bhb//hojW/15aw/8yKKT/IBSK/xoTdP9scbz/eYLC/0JCgv9AOXb/aF6T/15Whf9icZL/w9P3/8HR//+ir+3/gozg/3t86v9nZOL/ZWDl/1hXy/+Vnu7/v9H6/8zg8v/Azd3/cXKM/1VNbP93aIj/u9Xj/8Pd6f/A2+X/wNvl/77Y5P++2Oj/vtfn/7zV5f++2Ob/vdfj/7/Z5f/A2uj/v9vm/8He5//B3eT/yd/r/8fX6P+wvtD/xNfm/8rh8P/D3ev/zOXp/8Tbzf95jXD/h5hl/4aZaP+MoXr/n7ik/7bS0//N5/f/zODy/5Sbrv9+fJD/Zllx/2BOa/9bR2T/TDpZ/2tZeP9sWnn/X01s/2VIef9ZRGr/c2aG/2lbhP9YP3v/Y0eJ/25Yk/+mnMv/sbLe/5uf1P+Zm9z/ko/X/4yLzf+qrt7/2+X9/9zp8f/Z5/P/2efz/9zo9P/I1OD/ydfj/9Ld6//G0OH/xdDe/8jU4P++zNj/0N3r/83a6P/Bztz/xNDc/8XQ3v/F0N7/0N7q/8zX5f/J1OL/xNDc/8fT3//G0d//v8zc/8PO3P/F0dv/ytbi/9rn9//X5/T/2Orx/9Hh7f+Aiar/gIS3/3aBtf+fqtz/cHit/6227/98g8L/Zmiv/3Rxx/9lYMn/LCad/xsViv8UEHX/WFmq/4uN1P9VU5X/HhVO/1E+b/+Wn8T/v83q/9Hk//+6zfj/iZTe/3t96f9eWtf/eHbt/2twy/+suu//zuL7/8bf6f/N4+7/v9Hi/627zv/I0+f/xODr/8Hc5v/B3Ob/wdvn/7/Z5/+/2ef/vdjm/7vW5P++2OT/vtjm/77X5/+/2uj/wN3m/8Hd5P/C3uX/wN3m/8Df6P/F5ev/zOnu/8Pd5P/A2+X/xeHo/9Hp6f+90sr/pLeG/4aabf+Lo4D/p8Ow/8Xj5P/P6fn/scXX/3N6jv9zboP/bVx3/3Bbe/9WQWH/Z1Jy/4dykv9pUnL/Ykdp/2VHeP9ZQWv/aFV8/25bjP9ZP3v/Z0qJ/3BYjv+/teP/oqXS/4uSyf+cod7/nqHe/66w5v/Q2P3/2+f5/9vp7//X6u//3Ojy/97n9f/Z4/T/2OX1/9Pg8P/H0eL/1uDx/9jl9f/V5fL/1+Ty/9Xi8v/O2On/2+b0/9nk8v/a5fP/2eP0/8zW5//Q2uv/2uXz/9vn8//d5vP/1+Du/9fh8//c5vj/2+X2/9zo8v/Z6fD/1uby/9no+/+1wd3/h5Cy/3WBu/+msN//aXKd/6u27/+ZoOn/W1in/2Fbqv9aVbD/YGDS/yokp/8hEY7/HQ1y/0RAjP+Xl9f/Ukd//y0SRP83PF3/uMPf/9fp///A1vL/kqTh/3h65v9dVt3/dHHl/7jB///L4fr/zOXv/8Tc6P/H3+v/zurx/8nm7f/C4Ov/wd7l/8Lf6P/A3Of/wdvn/8Da5v+/2eX/vtrl/7vZ5P/A1+b/wdjn/77Y5P+/2+b/wNvl/8Hc5v/B3uf/vdvm/8Xf7f/N2+f/oKCm/4l8fv+NgoT/pamu/8jg5v/E6u//wtzj/5mtrv+UqKP/ssrK/8zo8//P4/X/o6q9/3p5if9zcID/c26D/2FVcf9jUnf/iHei/2VUf/9hS27/YUVi/2JBdP9bPmv/YUVw/3RVjP9dPoH/YkqL/2pfjf/Myuj/urjc/52a0v+Tk9n/Ymir/4iSwf/W4fz/2uf1/9vq8//Z6PH/2efz/9nm9P/a5/X/3Of1/9vm9P/c5/X/3en1/9zo9P/a6PT/3Of1/93n+P/V3/D/2eTy/9ro9P/a6fL/3ebz/9vm9P/d5/j/2+j2/9rr9P/Z6PH/3en1/9nk8v/V4O7/3Of1/9zo9P/b5/P/3Oj0/9nm9v/d6v//mKO+/3uItP+nsNv/YmiV/6iw6/+fqfb/XWO8/1xatP9JPJD/QjWL/2VawP80LKj/HRSa/xAEgv87LZb/c2y9/yQhZv80MWL/jJSr/9bq9f/J2f//n6X4/3Fz0f+XoOT/prvb/9Hp+//Az9//kZGd/4yAhv+LgoX/p6iy/87e6//C2+v/w93p/8Tc6P/D2+f/wNrm/7/b5v++2uX/vtnn/7vY5v+/2ef/v9nn/77a5f+/3OX/wN3m/8He5/++3eb/wt/m/8rg5v+FjJX/Z2Bv/3loff9zZ3v/goCT/83b7f/T6/3/tcTk/5esu/+qxsb/vd/e/8Pk7f/R5ff/p6u+/3Vygv95dob/bGp+/19Zcv+IfJj/Zllz/2BOa/9iS2v/XT9i/1o9a/9ZPmr/WD5s/2hOhP9kRof/YEaC/35tmf/FwNv/vsDe/4qNwP+urfX/jI3R/7W85//b6fv/2Ofw/9rn9f/a6PT/2+j2/9Xg7v/I0+H/xM/d/9Hc6v/T3uz/0Nvp/8TP3f/Czdv/y9bk/9Pe7P/F0N7/zNnn/9jm8v/P3en/xdHd/8jT4f/Ez93/x9Lg/9Hf6//O2ef/zNfl/8fQ3v/BzNr/ws3b/8TQ3P/H09//x9Pf/83a6P/f7f//qLbJ/4yUvP+jq9P/U1mG/6628f93fcj/UlOr/2divv9cUa3/Jhl1/zkrif9JOZ7/OCmS/zEii/8hFnP/QTeE/2deof87Nmn/g4al/9Ph8//Q5f//nLHl/3eDyf+kre3/w9H7/9fs//+pucb/a2l8/3VlfP90Ynn/YV5u/4yYpP/N4ez/wN3m/8Ld5//D2+f/wNrm/7/b5v+/2+b/v9ro/77Y5v+/2+b/vNrl/77c5//A3eb/wN3m/7/d6P+93OX/zubs/5+nrv9pX3D/cVx9/2pUfv9jVXn/mpaz/9fb9P+bpL//jpfJ/4CSsf/H5O3/xOXo/9fx/f/Ez+X/d3SK/3pyg/93b4D/YmB2/3V1k/+Afpz/bmV//2NTa/9fSGT/W0Bi/1Y4Y/9ZPGn/Wz9t/11Bdv9oTIf/YUZ+/4l2of+oo77/xcrj/42Rwf+GhMb/hIG//8/Y+v/Z6vP/2enw/93n+f/a5/X/3ej2/9jh7//BzNr/yNTg/9fl8f/S3ev/w87c/9Hc6v/K1eP/x9Lg/9rl8//T4e3/y9nl/9Pj7//L2Ob/wdHe/9Th7//T3uz/1eDu/9Xg7v/I0+H/ztfl/8zX5f/V4e3/0N7q/9Pf6//V4e3/1eHt/9Ti7v/b6/j/v87e/56nyf+Rl7z/VVuI/6628f+RmuP/NDiQ/1RSsv9mXb7/RjuX/z8whP83JHP/Mh1s/zEfbP8wIWv/Lhxh/0Etbv9ZTID/e3Ce/8bF5f/l9f//vdXr/56x3v+MlM//kZvL/9Di+f/M3eb/eHaM/2lWff9lTHj/ZVZ2/11bbv+0t8X/yOXu/8Db5f/D2+f/wdvp/7/a6P+/2+b/v9nl/8HY5/+/2+b/vNrl/73c5f/A3eb/wd7n/77d5v/C3+j/yNjl/3dvhv9lSnH/ZEV4/1xHeP9vaYz/09fv/5idsv9qb4j/oKfZ/5CcwP/m9P//1uDy/6Cfuf9VUG3/ZFpx/3txgf9xann/Z2R+/2ltlv99hLv/qKnj/1xRg/9ZR2b/YEha/1UyXv9bOWL/YD5n/1s7av9jR3z/YEl9/4x+p/+dm7j/nqC+/8C+7P+Be7T/tbXl/9Xf9//X6/D/2Orx/9zm9//a6PT/3Of1/9nl8f/W4u7/2eXx/93p9f/b5vT/1+Lw/93p9f/c6vb/2Oby/9ro9P/c6vb/2efz/9bk8P/X5PL/1eXy/9zp9//c6ff/3en1/9vn8//W4e//2OPx/9nl8f/c6/T/2+rz/93p9f/d6fX/3en1/9nn8//Y6PT/0+Xw/7C71/9uc5T/YmWR/6e07P+lvP//S2C8/ztDqP9GQaT/Yliy/0tBlP9bT6H/Jxdl/yoVWv8sFlH/MhlT/zkdWf88Ilj/MRpQ/zwtWf98eZP/zNLl/+vy//+boNH/e4Sw/3OBmP/P3uf/tLjL/2FTfP9hRnj/X0Jv/1c/Yf+OfZj/zebw/8Lb5f/B2+f/wdvn/8Dc5//A2ub/wNrm/8Da5v+/2uj/vNrl/77d5v/A3eb/wd7n/73c5f/K5e//n6q+/0Y6Xv9YO23/WkR1/3Rwk/+6yNv/2ur3/4eUpP+lrMD/2+D//73C4/+moMP/V0Nt/zYbR/9GL1X/X1Jq/3RtfP9tZnX/ZWR+/1Ncjv9SZLf/RlS+/01Mqv9RQXD/aVJW/1cwXf9WMVn/XDpf/188aP9fP27/YEx3/4qBov+gm7r/hH2i/4+Htv+kns3/n6TF/+Du///V5u//2uny/9ro9P/a6PT/2uj0/9zq9v/b6fX/2uj0/9zo9P/d6fX/3en1/9jn8P/Z6PH/2+n1/9ro9P/a6PT/2uj0/9vp9f/b6fX/2uj0/9ro9P/Z5/P/2uj0/9nn8//a6PT/2efz/9ro9P/Z6PH/2ejx/9no8f/Z6PH/2efz/9nn8//X5/P/2Or1/7zH5/9VWHf/eoCl/6m99v9pkeT/W4Xq/0JYwf9MS6v/SD+a/01Jqf9eW8L/OjGS/zQhcP8xF1P/MxZI/zATRf84GUz/PiBV/zMYSv8hCTP/NSBG/4p9o/+3tt7/xcrr/4uUqP+lsbv/3u77/6atxv9hWID/VDtn/080XP9VPGL/uMzX/8ni7P/B3Ob/wd7n/8Hb5//A2ub/wNrm/7/b5v+/2uj/v9zl/8Dd5v/C3Oj/wtzo/8Dd5P/H4+r/qLjJ/3p6mP+Oh6z/qa3K/8ne7f/I5Ov/yd/r/9rl+/+9v93/d3OX/1BIbf8vG0j/ORZO/0ggV/9HKlH/WUxi/3Fse/9sZ3b/YV91/0FOev9GZL3/KkjL/y8+vf9FPIX/bldm/186XP9QMVL/VDVa/1o5Zf9eOmj/ZUtv/4h6lv+hl7X/i32n/04/cv+jnMn/qK7L/9bl9f/Z5/P/2uny/9jp8v/a6PT/2uj0/9ro9P/a6PT/2uj0/9ro9P/Z5/P/2ejx/9no8f/Z6PH/2efz/9rn9f/a5/X/2Oj0/9ro9P/Z5/P/2uby/9ro9P/a6PT/2uj0/9nm9P/Z5/P/2efz/9no8f/Z6PH/2ejx/9no8f/Y5/D/2ejx/9ro9P/W5vL/4fP+/6my2P9MT27/mqPF/5Ks6P9Ld9T/LF7O/1p96/9TXsb/RECp/zw5p/81NKj/NC6d/zEihP8vF2X/PiRZ/z8lSf83G0n/OBxK/zkbTP88GEz/Mg5C/x4EMv87LFL/koqp/93Z8v/e5vf/xd7o/8vn8v/E1ej/oqO//4J8m/95cJH/scrU/8jj7f/A3eb/wt/o/8Hc5v/A2ub/vtrl/7/b5v+/2+b/v9zl/8Dd5v/A3eb/wt3n/8He5//B3uf/zeXx/9bp+P/R5vX/yuXv/8Pg5//N5fH/0Nv2/5eTvf9MPnT/Pilg/z8pXf9EKF3/RiNc/0ghWP9FKE//Vkhg/2xoe/9ua3v/V1dl/z1JZf9sjtT/NF7Z/yJBzP8zNp7/X0uG/25RYf9NMEn/VDRX/1g1Yf9aNmD/Ykdp/39uif+ekrD/hnWg/1I/cv9fT3//wb3g/9Te8P/Z6vP/2Ony/9ro9P/b6fX/2uj0/9ro9P/Y6PT/1+jx/9no8f/a6fL/2ejx/9no8f/Z6PH/2uj0/9rn9f/a5/X/2Oj0/9fn8//Z6PH/2ejx/9no8f/Z5/P/2uj0/9nm9P/a6PT/2uj0/9nn8//Z5/P/2uj0/9jp8v/X6PH/2ejx/9rp8v/X5u//5/b//3l7o/9XXYL/s8Du/2Z+xv88Y8b/OGTZ/yJJw/9Xb+f/RErB/zcxpv85MKT/JR2S/ykglP8oGnr/JhBL/0QoRf83HUv/NBhG/zkZSv86F0n/ORVJ/zYWR/8tED7/JAk1/086YP+rp8T/2en6/8zo8//D4uv/zOby/9Hl9v/V5vn/xeHs/8He5//B3uX/wd7l/8Dd5v/A3Of/v9vm/7/b5v+/2+b/v9vm/8He5//A3eT/wd7l/8Le6f/D3Oz/tc/d/7nT3//H4uz/0Oj0/9Hf8v+rrsr/a2GL/0k2b/9SNnz/VjR7/04tav9MKmD/Tipg/0onWf9HKlH/UUJd/3Fsgf9va37/VFFg/0RKXf9hfrH/V4rr/yFT1f8rQsD/NTWh/3hoc/9WO0v/WjFM/14zVP9VNFf/W0Jk/21bev+OgKL/hHaf/2FLfP9KLGH/l4Sr/+Xq///U6fH/1+ry/97n9f/a6PT/2uj0/9nn8//X5/P/1ufw/9no8f/Z6PH/2Ofw/9fn7v/X6PH/2efz/9nm9P/Y5fP/2Oby/9fm7//Y6O//1ebv/9no8f/Y5/D/2Ofw/9bn8P/W5/D/2efz/9jm8v/a5/X/2uj0/9no8f/Z6PH/1+jx/9jp8v/Z6PH/4u74/2ZrhP9+hrX/uMT//zFDnv80T7f/VHnt/wo0tf8rTtT/RVTS/zIvnf8/Mp7/Kh6U/yAal/8qIIr/KRNU/0MgQv9GKlj/OhtO/zsXS/8+HEv/QB9L/zsZSP87FEz/PxdR/zIQRv8vF0H/ZFx7/7G1zv/T4fT/0un4/8fi8P+20+H/wdjo/8fh7//B3uf/wt/m/8He5//A3Of/wNzn/7/b5v++2uX/wNvp/8Hd6P+/3+T/vt7j/8bg7v+oudP/f42q/5ypw/+ptMr/lZOw/3Nni/9XQ23/WURx/2FHff9aPnr/Vzdy/08vZf9GKVf/SChX/04uXf9PNFv/VEVh/3h0jf9qZ33/YVht/0ZDXP9YcJ7/XZbr/ylv5P8mWt3/LEjL/1leff9jUGv/Vy1G/2IzTf9WMlD/XkFi/2dOcP9wX4D/i36k/2ZQgP9XM2n/Wj1q/9PT6//X7fj/1Onx/+Hm9f/a6PT/2uj0/9rn9f/a6PT/2uny/9no8f/a5vD/3+35/9zr9P/V5u//1+jx/9vp9f/k7fr/4+z2/+Xv+f/g7fX/4PD8/9ro9P/f6/X/4/D4/+Hu9v/k8Pr/4Oz4/+Xx/f/c6vb/2Ofw/9no8f/Z6PH/2ejx/9rp8v/b6vP/2ubw/2l1gf+msuj/g47w/xMgjv8lOKH/cI79/yxV1P8ON7z/RF3V/zk9pv82LJb/NCig/x8Xk/8tIoj/MBdb/0MdR/89IE3/RyZZ/0IgVv89HUz/NBlA/zkbRP8+G03/QBlQ/0QfUf9CIU7/NBY//zcgRv9iU3P/hoOd/6Orwv+Uorj/i5iy/7/T5f/E4Ov/wODm/8He5f/A3Of/wNzn/7/b5v+/3OX/wdzq/8Hd6P+/3+X/vt7j/8fh7/+Gk7P/foCp/5mTvP9ZS23/W0lo/19JbP9gTXT/XE5y/1tMbP9hUm7/Zlp4/21igv9/dJr/gXOd/1JAaf9ZRmf/Vkpm/3Fyjv9tbIz/aF19/0dAY/9QZZn/aKr5/yiA7P8mcev/NWjk/0RnsP9CTIj/QzJd/0grTP9OLk3/Yjxa/3ZOav9aO1b/koCf/3Ngi/9aPHH/RilX/4+EpP/l8v//0+Xw/9zo9P/c6PT/2uj0/9ro9P/Z5/P/2efz/9no8f/c6PT/nqq2/83Y5v/f7Pr/2eb0/83Z5f+Rl6T/rrHA/6Omtf+9w9D/lJ2r/+Lr+P+6ws//nKKv/7vBzv+an67/ys/e/5ObqP/T3+n/3e30/9jo7//Z6PH/2ejx/9no8f/Z6fX/0ODs/3uMmf+rufT/NkCs/xggnP8bKZn/aILm/1yE7v8WQrX/L07B/zxJs/8yLpj/MSiX/yohj/8yJ4P/MiJf/zggSP83JUr/PShP/z8pU/9XR3D/gHaa/2NYeP9SQF3/TTZS/0QsSv9AKEr/RStT/0wvVv9JLE3/QytJ/0k6Wf+Tiqv/bneZ/5uqxP/M5vT/vt7k/8He5f/A3Of/wNvp/77c5/+/3OP/wd3o/8Hc6v/B3uX/wN7j/8nk8v+Onrv/bW2V/3lskv9TP1z/X01k/2NZcP9ycor/jZGk/6uxvv/DyNH/yNns/9Hj+v/J2fb/c36e/1dXdf9fWXD/VFJo/2lvjP95e6P/Z1yE/04+Z/9RX5P/XZ7p/zKQ8/8sge//NnPh/zZ15f83ac3/PVyr/yw3df8/M2P/TC1S/3RLZ/9eOE7/Zk5m/5iEp/9dRnL/Sy9d/084Xv/SzOP/4uv4/9Po8P/a5/X/2uj0/9nn8//Z5/P/2efz/9jm8v/h7fn/xc7c/5CWqf/Y3vH/7/b//7W9zv99gZP/sbDE/5mXrf+Xlav/gIKU/9TV6f+jorb/lpWp/4mGnP+XlKr/paS4/3p8jv/Bytf/1OTr/9jq8f/a6fL/2uny/9ro9P/a6vb/zd/q/5muyv9+jM7/GB+M/x8kpf8iLJ7/YHfN/26T3f9EcMv/LE+9/yo6q/83M5j/STyY/0g9mf83MoH/aGWW/3Bugv9rbYX/d3SN/356k/92eZX/tcDe/9rn///R2+3/wcXQ/6mrtv+Kipz/aGR9/1NGYP9GNEv/RDJJ/0EwS/9wX4D/aXKX/6a30v/I4/H/wd7l/8Dd5v/A3Of/v9ro/77c5/+/3OP/wd3o/8Db6f/C3ef/wd7l/8Pe7P++1O3/hI+q/3Z3jP99eYz/q6q+/8rR4v/W5e7/1+rx/9Lr+//O6f//msr+/4yz2v+Qq8X/gZWn/42aqv+RlKL/homY/3V+mf99hKv/al2J/1xEbP9EQ2//cJ/d/zuP6P8zhu//PHvr/yBr7f8mcOz/PX/w/zxvz/9Qbr3/Mz19/0M9cv9JN17/TDNP/25UbP+afpv/WTte/0EhRP94Yn7/6+r6/9bm8v/W5vL/2Oj0/9ro9P/Z5/P/2uj0/9ro9P/Y5vL/5PD8/87W5/+Zn7L/vcDV/52ft/+Cg53/1dby/4iHof/My+X/hoec/9PS7P+1sc7/kY6o/8fC3f+JhJ//1dLs/31+k//L0+T/0uHq/9jp8v/a6fL/2uj0/9ro9P/Z6fX/0+Pv/7jM9f9aZq7/HyKP/yEjoP81PKP/fpHU/2B/sv9sld7/P2TM/y1Brv8rJH//UkGL/2dcpf87PX7/ZW6Q/3yDhv9+i5v/g4uc/4mSoP+KlKX/hZit/5i00v+hxen/weT//9Ty///Z7v3/2+fx/9La5/+zt8n/iImd/2Ridv9hX3L/h5y3/8Xd8f/B3Or/wd7n/8He5//A3Of/v9vm/8Dc5//A3eb/wdzq/8Hd6P/C3+b/wt/m/7/c6v/F3/D/yN7q/8XX4v/a6Pv/0Nv5/77J5P/B0t//zOf1/63T/f9sl+D/MnbV/1J9vP9XaIL/VmBn/1pjZ/9gZm3/Zmhy/2Foe/9ye5z/Y1yH/1xEbP9LPGL/VW6g/3Gv+/8udd3/MW3o/y9t7/8lZen/JWbq/zJy7v84eez/MW/b/zZlx/8xRZP/PjJm/0krSP9uS1//mniQ/2JDXv8yGTP/j4KY//Dw///V5u//2efz/9nn8//a6PT/2uj0/9ro9P/a6PT/1+Xx/+Lx+v/O1+X/lJmu/7693f95eZ3/3uD//56ivv/Iz+P/p63E/66xzf+anLv/kJSt/8fM4f+sscb/pKW//6Ckvf+uuMr/4/H9/9jn8P/c6PT/2+fz/9ro9P/Z5/P/2uf1/8Lb//9NVaL/KiaX/yEhk/9garj/lKbP/1Vulv9hhMj/WYPj/0pmxf8oJXX/RC90/1RGiP90d67/c3qT/0lMSv9LTlz/Q0pd/0FIW/9ER1X/P0RT/1Fojv9XiMz/TYjY/4Gx8f+/3v//0eTx/8XW4//N3Pb/3ev//9Lh9P/C1d3/xeDu/8Hf6v/A3+j/wd7n/8He5/+/3OX/v9zl/8Dc5//A2+n/wdzq/8Hd6P/C3+b/weHn/8De6f/C3un/wt3n/8zm8v+dss3/ZXSb/4STuv+71Pb/lr3p/0V5xf8tZ9D/Pnnc/z9gn/9WWm3/amZl/2lpaf9obHH/bHB1/2Zvef94hp3/ho62/2BejP9CQGr/ITBe/1mBwv9Yju3/KWLW/zJa2/8wVtz/K1Ld/x9P3f8eXuz/IW38/ypy/P89bOX/SFix/0c/e/9BLFP/UztZ/5B3kf9uWHD/MR00/6SSqf/t9f//2uPw/9nn8//Y6PT/2uj0/9ro9P/a6PT/2en1/9Li7v/j8P//2d73/7Oy2f98eqj/xMbv/+Tt///Y5vL/3ur8/9Lc9P/L0u3/3+r+/9Xj7//g7fv/0t3x/93l/P/X4/X/2uf1/9ro9P/c5/X/3Of1/9ro9P/Z5/P/2+j2/8Hc/v9QV6D/MCqV/ystjP+bqdr/j52v/1tqhP9niMf/MmO//16H5P8yNof/RjB4/zUjZv9xcqX/iIyo/4iHi/9iWmT/VVdp/1VYbf9dVmX/XlRk/z9Jcf9Fbr3/Pn3l/zJuzv9ijdD/tdP8/7PJ7P93ia7/hJS4/8LX7f/K5vH/wt/m/8He5f/A3+j/wd7n/8He5f/A3eT/wN3m/8Dc5/+/2uj/wd3o/8He5//A3un/wd/q/8Lf5v/B3uX/yePx/6S70f9tfpn/pbfW/8bh//99p+r/K2TB/ypr1P84fOf/UnKj/z9RcP9hY23/a2lp/2lrbP9pcHP/bXV1/2pyef97jqP/pMTt/4+67f93n9D/TWua/xk0bf9SdMD/O2fE/ys/zP8yQ9T/MT/V/zBA2f8kPdn/HkHe/ylS7v83ZPX/Qm/v/0Vp1f8/U6j/MTJu/z8xVf+AaoL/g2p+/z8lPP+Wj6T/8fH//9nl8f/W5vP/2Oj1/9rp8v/Z6PH/3+z8/8LM5P+hqcb/zdT1/8LD7/9raKD/nJrO/+Lr///V6er/1+f0/9vo+P/c6fn/2Oby/9jp8v/W5vL/2en2/9nm9v/b6Pb/2uj0/9ro9P/a5/X/2uj0/9ro9P/Z5vT/2uf3/8jf//9bYaL/Ly2H/15isP/Ez+//dXt2/2txdv9sisH/MGvP/z1z3v88TaT/QzB1/zsmav9APnr/hY2y/3F3hP+ZlZT/aGdw/1ZWZv9WVWX/W1Zl/05Rbf87T4b/UHzP/z173/8ra9H/P3HJ/6HB//+6zfj/dIKe/36Qp//G3PX/xN/p/8Pe6P/C3+j/wd7l/8He5f/B3uf/wNzn/8Dc5//A2+n/wd7n/8He5f+/3Or/wN3r/8Ph5v/C4eT/xt7w/7XD4P/Fz+f/2e79/4St1P8dWrf/G2Tk/yZv6P8weNb/WF9c/1RcW/9aZGT/WmNm/11maf9hbW3/anZ2/4uVnP92jaP/Z5vD/3LC9/9ote3/i7zu/42k1v9ofrj/gqXn/0JO6P8WH73/JyrM/z442f9ENdP/QDLO/zAyzP8cPNX/E1Lq/xtk9P83ce7/UGjA/1tVhv9KM0n/aU9f/4lzhf9VP1z/iIKV/+Xu+//Z6vf/1ebz/9jp8v/a6vH/2+X3/9zg//+4uuP/oafQ/7C05P+zsO7/r6rn/93i///Z7On/2uny/9np8P/a6O7/3Onx/9vn8//Z5/P/2ejx/9no8f/a6fL/2+n1/9rn9f/a6PT/2uj0/9ro9P/Z5vT/2uf3/83f//9mbaT/PkKJ/6y19f+nrsf/ZGJQ/25uYv9ti7r/O3rq/zx59/9CWLf/QzNz/0gyc/8pJWz/hZHB/2p6i/9pcWb/kJOR/31/h/9mbXz/Xmd1/2Njc/9VVnD/UGaa/0F91/8gcer/HGTg/ztnwP+zyfP/0eHu/6CuwP/Az/D/xt/v/8Pd6f/D3uj/wd7l/8He5//A3Of/wNzn/7/b5v/A3eb/wd3o/8Dc5//B3uX/wODm/77e6f/A3ev/x+Dk/8zk5P/G5fr/h7X1/xpaxv8WYN7/ImrW/z93xP9CbqT/Y2ZX/32Ifv+NnI7/mqKE/6Chef+Xn3r/iJeC/5ednP9/fYn/XW6J/4O97v9UrPj/P5jz/06V9v9fnvr/bKr//53O//94mNn/PEGc/ygYlf81Hbf/QyvR/0Iv0v86LMr/MCrF/zU5zv85UOL/LGHu/yVs8v8oZ9f/Ij2H/zY1Xf+Wamn/glpc/5N4gv/f4vD/0/H//8Tl+f/R5vv/2+X2/9vo8P/e8fT/3/L3/+Dt9f/h7vb/4PD3/9fo8f/a5/X/1ujv/9fo8f/a6PT/2uj0/9ro9P/Z5/P/2efz/9nm9P/Z5/P/2efz/9no8f/Z5/P/2efz/9nm9P/Z5/P/2uj0/8/f//9kdJn/kaDB/7TD3f9+gYX/bWFJ/21mUv97mbb/PIPk/ziA/P9HZcr/QzN6/0w0df8hInr/TW3W/0Bu3f9AR5D/Y2J2/5CMcP+cnYP/mKKi/5ujsP+QlJ//dYab/1mFwP8obNX/H2vp/yBf1/89bM7/pMj//8bl/P/J493/w9/q/8Pg6f/C3+b/wd7l/8He5//A3Of/v9vm/7/b5v+/3OX/vtzn/8Hd6P/C3uX/wd7l/8Dd6//A3ev/xuDm/8bi6f+s0ff/NGvA/xhc0/8dZNb/LmzA/3Kg2v9QdKL/X2hr/3R9c/9wemr/Xmpk/1RkcP9QZXr/Sl5v/2x4hP9yd4b/U197/1V4pP94uPn/S570/zOK8v8vfu3/NXrp/0KC4P9qnf//g6b//2N29/8sMrn/Dw+Z/yIZqf81KMD/OSrI/zInyf8pK83/IjXY/yNG6f83XPT/TW3s/0NZw/8tOHz/QkR+/1lTfP90a4X/zszY/+7z9v/f6Ov/3env/9nn8//V5PT/1ubz/9fn8//Y5vL/2Oby/9vq8//a6vH/2Ony/9jo9P/a6PT/2uj0/9nn8//Z5/P/2efz/9nn8//Z5/P/2efz/9nn8//Z5/P/2ejx/9rp8v/a6PT/2+j2/8ne/v+WpMH/2uP+/3Z9kP9rbGj/bmRG/2plUP+Ip8b/PITi/zeA+f9bet3/TD6A/1E6eP8hJXT/T2/Q/zFfxP8pLX7/SUyQ/0dIev9BRmf/QUVX/1lYYv9oaHb/XGyQ/3mi4P9TkOD/KmrJ/y5r2f8jXc7/TH7W/7fb///K4d3/w+Dn/8Pg6f/C3+j/wd7n/8Lf6P/A3eb/wNzn/8Dc5/+/3OX/wd7n/8He5//C3+j/wt/o/8Le6f/D3uj/wt7p/73f/f9XiMz/G1vH/xli2/8obM//cKXk/3KWvP8ySmj/Slx7/1VdXP9TWk3/TmN//zldsf8uUK7/PVON/299lP9jbX//bHGQ/0NLc/9kg7b/aa34/zCM9f8qgPr/NHf0/ylw8P8gYOf/LmXu/1eH//99of//Znzi/zAyqP8dDpj/Iw2p/ysUtv8xHsH/LiLI/yckzv8mMdn/K0fo/zVd+f80bvX/JlTE/yk/jf9NSHX/c150/8S2vP/t8vH/3Ovu/9bm8v/Z5vb/2eb2/9fn9P/X5/T/2eb0/9ro9P/a6vH/2Oj0/9jo9P/a6PT/2uj0/9nn8//Z5/P/2efz/9ro9P/Z5/P/2efz/9nn8//Z5/P/2ejx/9np8P/a6fL/3ej2/8ri9P/Y5Pb/0NLk/1BQXP9qZlv/cWZG/25tWP+Tttf/OoDe/0aO/v+Fpvz/Vk2G/1Q/ff8lKXz/UHDT/y9gwv8fIYX/MDWw/yUsq/8vNo3/SEdn/01FT/9MSWP/MT9w/0dpn/9/ruH/X5fY/ylny/8hZeD/IF7K/3Wh3v/H4vb/wd7l/8Pg6f/C3un/wt7p/8He5//B3uf/wN3m/8Dc5/++3Of/wt/k/8Lf5P+93er/vt7r/8Xf5f/G3+P/w+L7/3yt6/8iX7//IGTP/ylv1P9XnPP/XJLR/zxYd/9BRk//QVWP/01WZP9PWFv/UG2m/yJNzP8gR8j/NEiP/3WAlP97hpT/am+Q/2Bchf9cZZD/eKfk/1Kd+f9GiPj/UH7u/zps6v8rWtr/H0vI/x1Fr/8sUKT/Vm27/3B10v9IPbH/LRic/yoTnf8pEpz/Khae/ykZov8fG6P/FyWt/xczvf8PStX/MGTg/0hrzf9IV6D/RkR//0dHdf+Jkrf/0eL8/9jp9v/a6O7/3env/9np8P/a6vH/2urx/9ro9P/a5/f/2uj0/9jm8v/a6PT/2efz/9nn8//Z5/P/2efz/9no8f/Z6PH/2efz/9ro9P/a6PT/2uny/9rp8v/a6fL/2uj0/9Lo9P/k8/z/sba//01KU/9nXlX/c2lL/4GFcv+kyOz/N3fV/1WX/v+y0v//c3Ce/1JAg/8pKpL/TXLm/y5r2f8XF5P/Jiq5/yMpsv8qK4H/REJg/1xabf9eYIj/RU2C/yw9ZP9SdZb/ZJzX/0uS8/8bZNb/KGnM/zVquv+Sv///yOPt/8Pe6P/C3+j/wt/o/8He5//B3uf/wNzn/7/b5v+72+j/xt/j/8Xg5P+73Ov/u93t/8fg4v/K4eP/rdT7/zRyzP8cYc7/MnHN/2Kg7P8/hNT/OnfB/zBJaf9eU0X/P1GO/0NPZ/9MWWn/SGSh/yhNwf8tSLf/NEB2/4yRmv9mb3j/VVp5/2dmjv9vcZn/epPF/3mh6f9DY7z/NUSg/yU1lf82RaL/T121/2d0wv9ufsD/b3u9/3V7xP+BgdX/hYDc/4F62/9+d9j/fHXW/3l00P91dND/dXbR/3V40/9jed//Xnfd/1t53v9ef+D/UnPU/z5Zu/81SJ//anm4/8zb+//e7vr/2uju/9vo8P/a6vD/2Oju/9no8f/Z5vb/2efz/9nn8//Z5/P/2efz/9nn8//Z5/P/2ejx/9no8f/Z5/P/2efz/9ro9P/a6PT/2uj0/9jo9P/a6PT/2uj0/9To8//h8fj/m6Oq/1dXXf9sZF3/c21W/5Wglv+63///Uo/t/0F+3P+42///rK7R/1ZKjP8wNKT/P2jn/ytz6f8hIKb/Jiik/y0vh/85OGD/Pj1N/1JZdP9gapn/WVuD/0JDWP9FW3f/SITG/z2N7P9NmPT/NXDA/yxowv8/gfH/x+Hv/8Hd6P/C3+j/wt/o/8He5//A3Of/wNzn/8Dc5/+83On/xN7k/8Xf5f+73er/u97r/8Tf4//I4/H/eKbc/x5iwf8qcdP/ZJ7p/1iRz/87fMb/L2qw/zxSa/+Ec1n/XmqM/4GLnf+Fj6D/cIOp/1drrP84RoH/U1l2/3h9gP9ham7/i5Km/3BylP9rbZX/h5HB/0ZVlP8TGWb/JBxv/zMsdf9AOH7/NjFv/ygmYf8iJF7/Jy1o/zM7d/85QX3/PEeB/0BKhv9HUJD/SU+W/0hPmP9KTZf/U0+b/19Vov9nXq7/aGW6/2lz0f9ifOb/YIX1/2WC9f9kdeT/XGPE/3N8xv+9y/z/2ej//9Tj/f/N3fT/2er9/9fn9P/d6e//2uf1/9nn8//Z5/P/2efz/9nn8//Z5/P/2efz/9fn8//a6PT/2efz/9ro9P/a6PT/2uj0/9ro9P/Y6PT/2en1/9Lo8//d6/f/j5Wg/2dqcv9zdm3/gYR0/7nJz/+TufP/a6f//zVyz/+fxPj/2uL//29tof9QX7v/R3Xh/zJz3/8/QrX/Ky6D/z09Zf9saG7/h4WL/3d/nP9sd53/cG2H/19VYv8/S23/RX7D/y5+1f9Tm+j/X5rf/zJwyv8YZd//o8Pa/8Lg8/++3Of/wt/m/8Le5f/A3Of/wNzn/8Dc5//B3uf/wd3o/8Hd6P/C3+b/wd/k/7/f7P+u0/n/SX/A/y5ww/9Ul+b/UY7S/1qS0/9NhMH/LlmE/0xcY/97b1f/U1le/15iZ/9la3D/bXR9/3J6h/9ob37/gIiV/2ZyeP+uur7/lJ2m/4GCl/9oaY//goe+/3B3vP8mJHD/LR9x/ygdZv8gGF//JiRm/z4+fv9JTov/TlWU/1FZlf9QXZH/VmSO/1pqjv9XY4v/XGaW/19mn/9XXJv/TUqS/z82hv9BNYH/STyK/0A4i/85OJb/UVO5/3J23P91dNz/bWvc/2dn2/9aXcb/h4ve/7rB//+mse//pbPn/9jm///d6e//1+f0/9rn9f/Z5/P/2efz/9ro9P/Z5/P/2efz/9nn8//Z5/P/2uj0/9ro9P/a6PT/2uj0/9ro9P/a6PT/2uf1/8/p9f/c6PT/kJSf/253gP92hoX/l6Wk/7nH4/+EqPb/TYn6/zFy1P+Ptur/5O7//7O53v+dsvb/hKr8/014yf93f8z/MTlu/3uAlf9zb3T/ZmJt/09Ta/9LTmr/Zl1x/1dKWv89Rmj/MmGf/z+H1P9Ei9X/Wpbc/1qW6P8ka83/b5nI/7bc/P+82+r/wt7l/8Le5f/A3Of/wNzn/8Dd5v/E3uT/vdzr/73c6//H4OL/x9/f/7/h+P+As+v/NHG7/1eW4P9NjdT/SYrU/1yZ3f9Tfqn/PFJd/1JaU/9iY1r/VVhW/1ldXv9dYWL/YGRe/2RoXf9zenf/qLW9/7XI0P+vwcD/j5mT/4B/iP9iYYj/cne2/4WO2P89P4b/KiNm/zEtef9DQpL/T1Ok/01Uo/9ETZf/REqT/0ZLkP9MUo3/UFyG/1Rhe/9VX3H/Ulpr/05UZ/9OUW3/T051/1NQff9PSof/RDx4/1dIhv9kTpb/VjyI/0cufv9jU6v/cWjW/1VQ0f9fVtz/V0nG/2RXyv+Jh/H/bnPO/5We3f/g5v//1eXy/9fn9P/Z5/P/2uj0/9ro9P/Z5/P/2efz/9nn8//Z5/P/2efz/9ro9P/a6PT/2uny/9rp8v/a6PT/2+n1/87o+P/b6e//lJ2g/3ODk/+EmbT/nanL/36HwP+btP//OG7q/zBu1P+Uu+//6fD//8PD8f9qdML/f5Dh/6m6+f+3xu3/hJCy/2Zsg/9FRVP/RUJR/0A+Uv9APFX/UERY/1BEVv81QFz/KlSJ/0GByP9Ymuj/QH3H/2Cd5/9Ki9b/QHrF/5vJ+f+93fD/w97i/8Le5f++3Of/vtzn/8Dd5P/D3uL/utvq/7rb6v/G3+H/yd7f/7ne+P9dltT/QIPS/1uf7P8vc8D/Wp/u/1iT0f9QcYv/PEZA/3p+ef9lb3n/XF5o/1tfav9rc3r/eIB//4OKh/+TnJ//uMjP/7fL0P+WqaD/i5WF/319ff9iXoL/aGqr/4OK0/91fLX/XWGK/11hnP9UWJn/R02U/0FIkf9CSJH/QkON/0NAiP9BQIL/Sk6B/1Zdfv9haHf/Z2xt/2FlX/9VXE//VFhM/1dZTf9WWGr/YF50/z85WP83JlH/Ujhu/2tOk/9MNYn/PzKU/21j1f9kUdD/XEDJ/1k5xv9UPcf/d27n/2Ngx/+qq///2un5/9nm9v/Z5vT/2uf1/9rn9f/a6PT/2uj0/9nn8//a6PT/2efz/9nn8//Z5/P/2uj0/9ro9P/a6PT/2uj0/9Hm/P/c7er/mKqj/32Srf+aqu3/d3vK/2pouv+lt///THrw/zFmx/+11f//zs7y/19PnP9hUcb/WFC7/56a4f+yw93/xdLs/4ySqf9paXn/aWl3/2Vjef9lXXv/Z1py/3x0hf8+SWT/HEJy/0Z9wP9enOP/VpLY/z1/xv9hp/T/MHXS/3qv6P/A4fT/xt/h/8He4/+/3Or/vtzn/8Dc4//D3eP/vNzp/73d6v/E3uT/yODm/6/U8P9Ph8L/U5rq/zmG3f8vfNL/ZKny/1CDtf9Sa3//gIeK/3p+if8zQFr/LTJL/09Wb/95gpb/gIuZ/2t1f/+LlZ//p7S8/5Khnf+Wp5L/dYJq/3+CgP9eWHv/YFqb/3l4uv+Ynsv/hpKq/3F9lf9ve5P/aHOO/19qiv9XYIb/TVGB/0REev88PXf/Ojt1/zo9cP9DQ2v/T1Bs/19lcv9ia2j/WWFQ/1FXPv9OUj//R0pB/1pdYf9TUmL/NjBP/y4eVP9XQ4z/ZVGk/z4tiP90YMr/dVjX/1gywP9SK7z/WDvG/2dW2/9nYeT/vcjk/93n///Y5fX/2eb0/9ro9P/Y6PT/2uj0/9ro9P/a6PT/2efz/9nn8//Z5/P/2uj0/9vp9f/a6PT/2uny/9Xk/v/c8Ov/oLev/6K14v+GifL/ZlzU/2dfxP+tuf//b5Lz/1F5y//T5f//fXKq/1Y5oP9pS9r/YEjK/21ZuP+Zp8v/n6rG/5mdsP9oanX/bm99/1VVbf87N1T/PDZP/2hjeP99haL/T2qW/099s/9Vjsb/Z6fn/yt1w/9ImPX/SI/q/16Vzv+73vL/xt/h/8He4/++2+n/wNvp/8Hc5v/B3Ob/wNvp/8Hc6v/F3uj/xuLt/6DG5P9Vjsb/T5jq/yd3zv9KleP/ZKDb/3Wcw/+sv9r/bnSL/y82Uf9DTW//jJSx/46XuP9yeZr/fIOc/3N7jP+Wnqv/hpCX/6Wwpv98iW//e4dr/3p8fP9cVHn/YVKQ/2pin/+Yn8r/xdr1/6W7tv+bsaX/obek/5iunP+NnpP/f4yO/255h/9XX3z/OkBr/ycoYv8lIWL/KCRm/ygoZP8yNmb/SlBt/1Vbbv9VWkX/VVtK/01UR/9QV1L/UFNb/0Q/Wv8xHk//Qylp/2lPnf9OOZX/dWDN/21Pzv9aMLn/UCWy/19D0v9YStj/jo7K/9TY///Z5Pj/2uny/9vq8//Y6PX/2Oj0/9nn8//Z5/P/2efz/9nn8//Z5/P/2uj0/9rn9f/a6PT/2uj0/9fk+v/a7Ov/v9TW/7G99/9mY97/aVnn/2dezf+4xf//k7Lv/42p5f/Cyv//WUaV/15Asf9kRs//Wj7A/2dLvP+Ah8D/m5/I/4yOpv+Dg5P/lZep/4qMpP+Vl6//bGyE/zIzT/86P2D/jZ3B/6bD6P9ejrj/bKzm/zmG1f8qft3/VqDy/1iRyP+x1e3/xd/l/8Lf5P+/2+b/wNzn/8Db5f/C3ef/vtvq/77b6v/E3ef/xuLt/5S/4P9Wltb/RI/e/zl/xf+Bt+z/o8v1/6/J7v9hcZX/MDlb/2Zsj/+bpMr/XmaD/yYuU/9ITG//ZGZ+/2lteP9zeYD/goiN/5Ockv+CjG7/foZo/3l4ev9aT3f/Yk+O/1dLh/+Ijr3/y+L//9Tv5v+30sL/mrib/5i3kv+ZtZH/kqqK/46jjf+LnZb/iZWh/3x/nv9STn//LiZj/ywkav8wK3D/Mi5v/09Lhv9ycnL/X2Bc/15iV/9UWEz/UFJM/1RQVv9RQVn/QiVW/zMUWf9ZQZX/WEak/3Veyv9dObX/Vyyz/1Uxu/9bQ8v/cWbH/7Sz8//b5f3/2env/9np8P/a5/X/2Oj1/9no8f/Z5/P/2eb0/9nm9P/Z5/P/2efz/9nn8//a6PT/2uj0/9jm+P/Z6fD/2+v8/56l6v9eVtj/aFjs/2pi1P/Azv//utb0/8LX/f+zsvb/WESl/1c9r/9qVMv/a1PJ/1tAtf9mZ7H/o6PZ/3Nykv9jY3v/cXOL/zw9V/8+P1n/iYup/6Kkx/9YWoL/KC9Q/4OTsP+u0fP/i8Hw/2eq6f8yesL/QJLk/1yb1f+ky+f/xeDq/8Hd5P+/2+b/v9vm/7/Z5f/D3eP/vdzr/73b7P/G3uT/x+Ls/5C/5f9Jktb/PojQ/4C04v/F4Pr/u87p/19vmf8vPGj/bXWa/5yix/9LU3v/KjBT/2Noj/9pa47/YGBy/3J0df9ucXX/bHF6/6KppP+Ij3T/e4Bl/3Zyd/9aS3f/YEyN/09Be/+Umcb/z+T//9Lq8P/Y8fP/zuji/7TOvv+gu6H/nraW/5evj/+LoYX/eYx3/3+Ngf+Wnp3/fX+J/0JAVv83MVT/S0Fv/1JFef9UT2T/W1Zl/1lXXf9UUVP/SkZM/0xDUP9MPVn/Ry1d/0ckZ/85Gmn/VTyU/2ZPsf9qTL3/Timl/1cvsv9fObv/XEbH/5yW6P/b5v//2env/9rq8f/a5/f/2eb0/9no8f/Z5/P/2eb0/9nm9P/Z5/P/2ejx/9nn8//a6PT/2uj0/9jn9//Y5/D/3uz//5OY4/9eVtn/Y1bo/3Nv2P/N2///0uv1/9zt//+knuX/Y023/2NJv/9fSr7/gW7d/2tXwv9kZLL/lpLN/3Frjv9nZHr/ZmZ+/3Bykf9AQGT/IB9G/2JkjP+nrNP/ZWyT/ygxVv97jrH/vNr9/67Y/f90pcv/Kn3Y/12c2f+kyuj/xN7q/8Hc5v++2+n/vdro/8Da5v/D3uL/vNzp/7vc6//E3uT/xuHr/5bE5v9Qk8z/drTq/73i/v/J1OL/houk/z1Jc/9teqb/mKDF/2Joi/9MVHz/dXik/1Zag/9fYX//YGNo/3l5c/9jZmr/Z216/7zExP+FjXb/cnVb/3Rsc/9YSHj/V0aG/2Zdlv+5v+j/z+L//9Pn+P/U5fr/2Of6/9vr9//P4eD/uMzA/6a6p/+ht57/nrmY/4Kgff9aelv/aIds/3WRfv8qPjn/Awwa/w4RLf8NDTH/EA4y/xsZPf8sKEz/OC9a/zcrX/84JmP/PCJo/z8fbv9GIHj/TimJ/108pP9wUb7/Wjmr/08mn/9hM67/UTPC/5WI5P/e5///2Ons/9rq8f/c5vf/2+b0/9no8f/Z6PH/2eb0/9nm9P/a6PT/2uny/9ro9P/a6PT/2uny/9jm+P/W6e7/3e3+/5Wb5P9bVNr/YFTi/4WF3//Z5///1Onr/9/s//+loOX/V0Gr/2xQy/9iScP/ZVLB/3lpzv+Jj9L/hYO3/2NdfP9zbHv/Wllp/15gfv9lZI7/Z2aS/zQ3Xf9XYIb/nqnV/2x2pv85P2r/k5y9/8rh9/+93fD/WKHx/1uUy/+r0Or/w93p/8Da5v+82ef/vdro/8Db5f/C3uX/wN3m/7/d6P/A3eb/wuLv/5rD2v+Nutv/tt39/8Da8v+Worr/UVp7/3F6pf+OmsT/ZG2T/2Rtj/9+hKn/OTxp/0dKcP9maHr/a2tl/35+cv9bXmL/Z2yB/9Ha5P+VnYz/ZGRM/3ZqcP9ZR3b/U0KF/5KOyf/BzfX/y+D//9Xo9//Y5/r/1+X4/9jl8//a6/T/3e30/9Lj5v+5zsb/lban/4i3p/9yrqb/L3Jz/y9ydf9OjJT/HFJp/wAsUP8tR33/Q1KQ/01Plv9TTZr/UEaZ/1E/nP9YP6f/XT6r/1Iyn/9GIpL/SB6T/0kdkv9OI5T/YDqk/1gvnP9aK5//Tim1/5OB2v/k6f//1ejr/9rq8P/a5/f/3Ob3/9rp8v/Z6PH/2efz/9nm9P/Z5/P/2ejx/9ro9P/a6PT/2uny/9fl+//Y6uv/3/D5/6Sr8P9cVtn/X1bc/5+i7P/e8Pv/1Oro/+Dr//+im+T/WUSq/2pQxf9rU8n/XUu2/3ZoyP+suuv/e36q/1tWc/97c37/ZWFm/2lpe/9LTXD/QkNv/3h8pf9OV3z/XmqU/46Zy/9scKP/U1mC/6a00P/K4vb/qdn//4my0/+szeH/xODr/7/b5v/A3Of/vtrl/8Da5v+/3uf/w93k/8Pd5P+83On/uNzs/7fW5f/C2ub/y+Dv/6K50/9fdZn/YG6Y/4WOuf9ZYo3/ZnKa/3uEqf84O1r/TFB5/32An/9fYGr/dXVl/4aEcv9SUlj/bXGN/9nj9P/AyL3/YV5J/2hZXf9WQm//YlSW/6mq5v+7zPf/yuP//9Pq8v/X6vL/2urx/9np7//W6O//1ub2/9nn+f/a7/f/wefr/47J2P9lttn/Xrrr/1Sz5f9UseL/WbTr/0ym5/9cjtb/XnzP/2pw0f94cdn/fnHd/31n3v9uTtH/YT3H/2lH0f9oRtD/USew/08doP9TH5T/TR6F/1MnjP9UKZL/SyCn/3tmu//h5f//1urr/9fq7//a5/f/2+X2/9rp8v/a6vH/2uj0/9ro9P/a6PT/2uny/9ro9P/a6PT/2uny/9Xl/P/Y6+j/3/Dz/7nA//9gXNr/ZF3c/7vC///c8fL/0uzm/97q//+ooO3/SzaZ/2pUvv9vXcj/Wkqv/6GR7//A0fj/dn+l/1BObP+Kgo3/b2pp/2VkaP97f5j/UFN//zM4Zf98hKn/XmeM/1pkk/94gbr/Wmac/2h5oP+zyOP/yuTr/77Y5P+41OX/vd3q/7/c5f/B3Ob/vtjk/8Da5v++3eb/wN3m/8He5/++3eb/vt3m/8Df6P/F4O7/utDp/36Osv9dapj/aHKi/1tkkP9sdZv/gout/zc/ZP9fY4z/cXGh/09NY/9oZl7/cXJi/6Wmov9NUF7/dH6W/9Xk/v/Y6Pj/eHp7/1VER/9UPlr/cmuk/6m0+P+3y/v/1uf//9ns8//X6PH/1ufw/9no8f/Z6PH/2uny/9ro9P/Z5vT/3Or2/9jr+v+v2PH/Zrzm/zG28v8Zuv7/H7j7/yy39v8hrvf/IqXv/yiW4v82itb/Q4DQ/1N82P9rgev/cnjv/11S0P9XQsb/c1fg/2E7yf9LG6n/TxqZ/0kXg/9IHHf/ThOa/19Am//Ozvb/2ur3/9jm8v/c5/X/2ejx/9np8P/a6fL/3Of1/9ro9P/Y6PT/2Oj0/9rn9f/a6PT/2uny/9rl+//k7uL/5/Dj/9Xc//9pbNT/dXrd/9Tg///Y8Ob/0+3n/97r//+wp+r/VTqY/2JBtP9vWcn/b225/9Dd///H2/r/gImv/0pJaf+joaf/d3Zo/2ZmYP9KR13/ameU/2xwmf87RGb/e4Kp/2Fomv9TW5b/XWih/15mm/+MkMP/wt7p/8Pf6v/B3uf/wN3k/77e5P+/3OX/wNrm/8Da5v++3eb/vt3m/8Dd5v/B3uf/wd7n/77d5v/F4fL/mK3M/2JyoP9cap7/T12N/259pP+CjbP/SVJ4/1phiP9hZo3/JihQ/2Rjc/9qaF7/b29d/7G1r/91fYr/g42l/9np///a7Pf/xczJ/1FJSf87LEf/hH26/624/P/C1P//sMTW/8rY9P/a6P7/2Oby/9np8P/Z6PH/2+n1/9ro9P/a6PT/2efz/9bm9v/I6f3/rub//3fO9v9FuOv/Mbb0/yu6/v8uuvX/L7n0/y6z9v8wqfn/NZPy/zx23/8+Vsb/S0zG/2Va4P9lVuD/RC23/2FAxv9oOb3/Ux+b/1Mejf9GE3X/SA94/0kpdv+qptD/4u3//9fl8f/Z6PH/2Ofw/9no8f/a6PT/2uf1/9rn9f/a6PT/2uny/9ro9P/a6PT/2uj0/8rm/v/Q7fT/0e7z/9To//+Gktj/pa3z/93p///W7ej/1u7m/97s//+povP/SzWr/1Q9t/9vZMD/vsLy/97r+f/S5f//ipe3/2xxiv+lp6j/d3dp/2VmXf9nZ3n/JCNK/11fiP9xc5v/SU12/3mBsP9jbqD/TlyN/1xnoP9ka6r/orzN/8fh8f+/2+b/wN3k/8Dd5P+/3OX/wNrm/8Da5v++3eb/vNvk/77d5v/B3uf/wd7n/8Tg6/+51e3/aoCp/19xpv9NW4//cYGs/42dwf9ncpj/VV2F/11gjP8kKVD/S09r/3x+hv9eXFH/f4Fu/4+VkP+bpa//pbPK/9Xq///N4+//4/Py/6Soqf8mIz3/g4S+/622+v/I1///o7TO/4GKtf/b5v//2eb0/9vo8P/b5/H/2uj0/9ro9P/b5/H/2+fx/9jo9f/T5vX/0+j3/8zq+/+l3Pv/W7zu/ymo7P88tPD/P771/ze/+f8uuv//J5/5/yFr1f87Vcv/TUjL/zw0vf8/OMH/X1PV/0cvq/9RLaX/XjKn/1Eejf9KE3r/RBJg/z0YXv95aZ//3+H//9jl9f/Z6fD/2ejx/9nn8//a5/X/2uj0/9vp9f/a6PT/2ejx/9no8f/Z5/P/2efz/7/p//+q1u3/r9nw/8vt//+6zu3/0Nr8/9rn/f/X7ev/1e3l/+Hs//+jmvD/RjOs/1BFrf+usu3/3uz//9jm7P/Y7f//pbbL/5Ser/+Ijo3/iY5//1dbUP96fIb/TE5s/yQjS/9YVoT/YmWS/1xjjv+Kmr//aXmj/0xYkv9ZYqv/c4io/8Tc9P/A2+n/wN3k/7/c4//B3ej/vtrl/7/b5v+/3+X/vdvm/73b5v/A3eT/wN3k/8Xh8v+guNz/XHGk/1Vom/9tfqn/qLjd/3eFqf9iapL/U1iF/15hjv8xNGD/eH2G/3B0df9YWU//m56P/3+Gf/+IlJ7/orXQ/83m///L4/v/1Ojz/+Pw+P+RnLL/kpzL/6ey7v+fquP/19///7C83v/Q3vX/2+j2/9zp8f/c6PL/2uf1/9rn9f/c6PT/2+fz/9nn8//b5/P/4ujv/+Hn7v/T6vn/sOb//1uw3v8jdsT/HnK+/yKAwv80ndb/R6vm/zR4y/8OKZj/JCKk/zsztv86N7L/NjCn/1hJwv9DLKD/OhuI/1Emjf9LFXn/PxFZ/zYNWP9QNXf/ycHw/97p///V5+7/2enw/9vn8//b5/P/2ejx/9vn8f/b5/P/2efz/9nn8//Z5/P/2+b0/8Pr/f+u1u//qc7o/8rr+v/S6fH/3Of1/9zn9f/X6/D/0+rs/+Pt//+ThtD/SzmS/6Wg3f/f7f//0efz/9Pj+v/R6v//qbvM/4iUmv9/hYD/paug/1FZTv9tc3L/dXiH/z07X/9XVIb/XV6Q/1Zehv95iKn/rb3i/218rf9TYJ7/XnOm/6rA5P/F3u7/wd3k/8Dd5P/A3Of/vtrl/7/b5v+/3eL/wNzn/73b5v/A3uP/v97h/8Xg9f+FnMr/WGyj/2Z2pP+/0fD/gY6u/3qCqv9QVIT/YGKS/0VHd/81Nmj/nZ6U/1dcXf9fZ2f/rrWm/3h+a/9/i5X/boW1/7nW///L5P//zeDj/9jo5//f8v//xdr2/7zL8v9tdar/wML//+H0///X6PX/2uj0/9zo8v/Z6PH/2uj0/9rn9f/a5/X/2uj0/9ro9P/b5/P/3efx/97n8P/Y5vL/zuf3/8zr//9vm+//NFS1/zBJqf8nSY//L12M/054rf9EW7H/JCWX/ykhlv8wJpj/MSeZ/zQonv9PQrX/OyaN/zMSbf9KHXP/PxZU/zMHTP86FVn/nY29/+Ts///T5u7/1+jx/9vn8//b5/P/2ejx/9vn8f/b5/P/2eb0/9fn8//X5/P/2+fz/9Dp8//S6fn/0un5/9Lo8//X6fD/2+fz/9zn9f/X6PH/2Oz3/9Pd+/9pZJv/p6HY/+Xt///W7vT/zufx/9Lk//+72P//e5Cs/32Gg/99gXX/tr22/15lYP9XX1X/lZic/zw5Wf9RToX/WFqQ/1ddhv9mcJL/kZ/D/73M8/9peqH/UWep/4+m0//H3/H/v9zh/8Dd5P++3Of/vtrl/77b5P/A3eL/wNvp/8Db6f+/3uH/wN/i/77Y8P90ibz/Wm6l/7fK8P+bqsT/fIel/2Rplv9XWo3/TFCB/yktXf9SVYj/paSI/0RKT/90gIz/qbKd/3B3Uv+GlKD/T2i4/4Sj/v/V7v//1ebR/5mpkf+4zM3/3PL9/97y/f+rttb/mZ/a/9nw+P/T5/L/2Oj0/9ro9P/a6PT/2uj0/9ro9P/a5/X/2eb0/9nn8//Z5vT/1+f0/9bn9P/W6PP/3Ofv/+Hn7v/L4f//h4nh/1xNx/9MO7T/LyuE/ys2cP8yPnj/Li+A/ysfif86JZn/Pyuc/ywci/8yJZH/VUWq/zcgdf8sDlf/QRxK/zQIPf8uBDn/a1V//9/k+f/V5/L/1Obx/9nm9P/Z5vT/2uj0/9ro9P/c6PT/2efz/9bn8P/X6PH/2efz/97q8P/b6PD/3Ojy/9vn8f/Z5/P/2Of3/9fn9//Y6fL/3/D5/7K/2f+quef/2/D//8Xi//+pytr/xd3j/+T0+v+An///U2md/4WPgv9xd17/uL+6/295ef9JT0T/np+b/1pYdf8kI1v/REaA/2ptmf9NU3j/h5C2/5uqy/+8zuX/UGer/3qRvv/E3u//wd7j/8Dd5P+/2uj/vtnn/7/a5P/A3OP/wNzn/77a5f+/3eL/wd7l/7bQ6P9lfKn/kafX/8HV+P9uf5r/g42v/0lOf/9obKH/QUZ3/ykvXv9tcqP/npx9/0FHTP+Mmqb/jJh6/2pzQf+aqrb/W3XZ/zdVy//F3v//5vnm/7bGp/9gcmX/h5qR/+Dy5f/i9Pv/x9n+/83k8//W6fb/2Oj0/9jo9P/a6PT/2uj0/9ro9P/Z5/P/2efz/9bm8//X5/T/1+f0/9bn9P/X5/P/2+fx/93m7//Y6/L/1Nr//3dp3/9XPOD/RyvK/ygYhP8wJ2r/Qzl7/zkmg/8sFYL/NSCH/0Qyj/8vIYH/NCSJ/1JBnP8qGWP/LhE4/zgPPP8rAC3/QSdL/8LE3P/b6/v/1OXy/9nm9P/a5/X/2Oj0/9rn9f/c6PT/2+fx/9np8P/X6PH/2efz/93n8f/b5/H/3Ojy/9zo8v/d6fX/2Of3/9Xm8//Z6/L/2Orx/87j+P/J5///hK7v/1iHxf+Kstz/0ev7/9/u8P8qS+7/XXW9/5Wikv9ka0j/naeb/4mTk/9ARzr/mpuS/3d2kP8kJV//Nzlz/2tumv9KTnf/cXqm/36MsP/A1Ob/kKXc/2N9ov+82On/wN3k/7/c5f+/2uj/vtnn/77a5f+/3OX/wNzn/8Dc5/++2+T/xODr/6nD2/9yi63/xt3//4ufwv+BkLH/XWWN/1xhkv9scqf/QUh5/ycvXv+GjLn/i4l3/1NYVv+SnZX/cHlY/2dySv+1xs//kq3+/xQyqP9tiOL/0Or//93y9P/H287/j6CL/7C+rP/h8/L/z+j8/9Pn+P/W6fj/2Oj0/9jo9P/a6PT/2efz/9nn8//Z5/P/2efz/9fn8//X5/T/2uj0/9zo9P/b5/P/2Oj1/9fo9f/X7OP/2ev8/73D//9YTOL/UzT1/1Aq2v8yEIz/Jw1h/zgicP8zHnP/JRVo/ysda/9BNob/MSV9/zcth/9BOI7/JRRT/yYFPv8tAzP/Jgkw/52Yt//g7v//1OPz/9zo9P/c6PL/2Oj0/9jo9P/c6PL/2+fx/9no8f/X6PH/2efz/9jo9f/X5/T/2Oj1/9ro9P/a6PT/2uj0/9rq8f/a6vD/1unx/9Xw//+VuOD/XYm//5C++P+24f//y+n//4GX0f8KKr//j6fv/6q5sf9eakb/dIBq/5ihlP9ITT7/jo+L/5OUrv8lKFv/NDdu/2Fllf9eZJP/SVOD/4qZwP+Pnrj/yd///3KKpv+vy9z/wt7p/77a5f++2uX/vtrl/7za5f+92uP/v9zl/77a5f++2ef/w9/w/565zf+atMz/yN76/3OGp/+Dj7f/SU98/3d8rf9udaf/NDts/zE6Zv+gqND/dXZ6/2puYv+DiGv/ZGxN/255Zf/M3t//zOP//2B90v8XNaz/Zobv/8Pk///a+Pn/5fzu/7XFxP/S5O//0+v3/9Tq9v/V6PX/2Oj0/9jo9P/Z5/P/2uf1/9rn9f/a6PT/2efz/9nn8//Z5/P/3Oj0/9zo9P/c6PT/2Oj0/9fo9f/X6fD/1Ojt/9vs//+jovj/WD3g/1ws+v9ZJuL/PxSZ/ykLXv83IWL/LBpf/yATV/8iGFT/NC5l/zIta/9AO4b/NCx//yIKS/8lAS//HAAk/3hxkv/g6///1eT0/9vn8f/b6PD/1+jx/9jp8v/Z6fD/2uny/9nn8//Z5/P/2efz/9jo9f/Y6PX/2efz/9no8f/a6fL/3Oj0/9vn8f/Y6fL/0+r5/8vl/f+Vs9D/xeX//83w///A5f//ao3u/xY0t/9Uccb/yeD//8DQz/9jcVX/ZXFN/4aOcP9XXE3/en+C/6ivyv8xNmP/LjFk/2JlmP9sdaf/Okh4/4OPt/+Cja3/yN/1/562yv+kvs//xeDu/77a5f++2uX/vNrl/7za5f+92eT/vtvk/7/c5f+92uj/wd7t/6TA0f+71eb/scXe/3+Or/9sdaD/VF+L/4yWxv9SWYv/MDVm/0pTfv+ntdn/aXCE/3p/cP93fVT/XGRG/5yonP/o+ez/4PTv/9Do//91k/L/KEq7/1uCzP+s0+//0PL//8Xi/f/G3/n/1+34/9Dp+f/T6fX/1+n0/9jo9P/X5/P/2eb0/9ro9P/a6PT/2uj0/9nn8//a6PT/2uj0/9jo9P/Y6PT/2efz/9vn8f/X4/v/2enw/9vr6v/f5f//jH3f/2M87P9dKPT/YC7a/00jmv8xC2X/Mg9l/z4ga/8xI03/BAEQ/wgGGf8tJU3/Qjx9/z0tXP8lDyj/EwAT/25rgf/l7f//0eDw/9fm7//Z6PH/1+jx/9fo8f/Z6PH/2efz/9rn9f/a6PT/2uny/9zo8v/Z5/P/2+fx/9vo8P/c6PL/2Ob4/9Tl+v/U6Pr/yeLy/8fl+P/D4fr/0vD//7va8f9sibb/ME+q/2CA///T6vn/3fP//9/08v9+j3T/YWtA/3Z9WP9zeG//Zm99/6m10f9PV3z/KCxc/01Qh/+DjsL/R1eC/2Nwlv+JkLf/rMTW/7zU5v+owdH/w97s/77a5f+92uP/vtvk/73Z5P+92eT/vdrj/7/c5f+/2+b/wNvp/7DN2//H4fL/nK/K/4iUuP9dZpH/dYKu/3iFs/81O3D/NThr/3B5pP+RpcT/aXeO/42YkP9pcE3/cnxY/6CvlP+uvqb/rLug/8XUzP/c8f//vdv//4ep3v92n8z/hbDh/73l///G6v//rcve/8Ph+v/Q6vv/1Of0/9jo9P/a6PT/2uj0/9rp8v/Z6PH/2uj0/9vo9v/a6PT/2uny/9jo9P/X5/P/2uj0/93n8f/Y5vj/2+fz/9zo7v/g7Pj/ys7//3lo1/9uSev/Zzfp/2k22v9fKLv/QQmK/10xkP8+J1P/BQAF/wQAAf8aDx//JBg8/z0wSv83Kjr/CQAK/2Zlb//x9///6PT//9jo9P/T4+//1ufw/9bn8P/a6PT/2uj0/9ro9P/b6fX/2ejx/93p7//Z5/P/1+fz/9vp7//c6vD/0uX6/83o//+ryOf/qsne/9Dy//+85P//k7zp/4mp0v+asdH/yN7//87n///F1b3/rMO1/7TRwv+Wr43/YW8//3F4Vf+MlJP/XGqB/5GgwP90faL/LjBg/zAzav95hbX/a3ug/0pXff+OlMH/lq/D/8fh8v+yzdv/v9vm/77a5f+82OP/vtjk/77Z4/++2uX/vtrl/77b5P+/3OX/wNvl/7zY4//H4PT/jqC9/4uXu/9ibpb/i5vF/09djf84PXT/PD50/5SdyP90iKf/ip2y/6u6vP9wfWP/jZxw/3OHWv+BknD/d4Zn/2JsSP+Kl3H/zd/I/+T6///C4v//fqbg/2SSyP+t2///krzp/5Cv0P/T7f//1Of0/9rp8v/a6PT/2uj0/9no8f/Z6PH/2efz/9rn9f/a6PT/2uny/9vn8f/Z5/P/2eb0/9nm9P/Z6u3/2efz/9fl9//V5fb/2ur//7W57P99cNL/eFjs/2098/91PPX/bjfa/2U8tf9PO4j/ZGGP/0ZBaP8gFz//HAk6/wkAKv9BMGP/OixO/wcCEf8yMjj/k5mg/9rk7v/r9///3u71/9bm7f/X5fH/2uj0/9rp8v/a6fL/2efz/9vo8P/Y6PX/1uf0/9no8f/b6PD/0+j3/8Xi//95oMf/rNb//6TR/P9mlsb/i7ft/8Lk///j+f//wNC4/4KRXv9hclH/epN5/3ibgf9/oHv/fpRq/2d2W/+ksbP/doeh/3iGqv+Pl7//Nzhq/zA0af9NV4b/iZi//0lVff+JkcD/hqC4/8Tg8f+82OP/v9zl/77b5P+81+X/vtjm/77Y5P+92eT/vdnk/77a5f+/2uT/v9rk/7/Z5//C2e//f5Sw/56v0P+BkbX/go+7/z5Ge/86Pnj/VFiN/5+q1v9kdJj/u9Lo/9Dl7f+itab/e49l/3+UY/9/kmv/l6iH/3eBV/9obzb/bXZE/7nFs//f8v//0u3//4Oo1P9Ug8H/kMX//4+xz//K5Pz/1+r5/9no8f/a6fL/1+fz/9ro9P/Z6PH/2ejx/9ro9P/a6PT/2efz/9rm8v/Z5/P/2uf1/9rn9f/Z6u3/2Ony/9fm9v/Y5/f/1uby/93r/v+preL/gHXd/3lf8/92VPn/dFf0/2lb4/9bX9X/ZXLc/1pix/9DRKb/Rzqm/zwpnf8vFoT/VkCO/0I3WP8CAAb/AAAD/xcZIf91foL/ydbY/+r5/P/m9f7/2uj0/9Tl7v/Y5/D/2uf1/9nn8//Z6PH/2efz/9jo9f/X5/P/2uzz/8Da6v+Vv+r/lMv//0t/xf+Pt+f/1vD//9jv9/+Vq5//YXJH/3F8NP95kHD/l7KY/36hh/9+oYb/g6KF/5Grm//J3eL/u8zm/2Nwlv+ZodD/UVWG/zI1aP83Pm//fom1/2Fwl/+Fkbn/gJay/77Z7f++3Of/vtvi/77a5f+81+X/vdjm/7zY4/+72uP/vdjm/7/Z5/++2+T/vtvi/8Lb6/+70er/eI2o/7TK4/+ars3/aHKh/zs/ef85PXf/cXur/5Oeyv9pdKD/w9z8/7TM4v/B19z/hpuF/4CVb/99k2n/i6B6/6Gwiv9xe1H/anJJ/2huT//By7r/5PTz/9Lt//9lj9L/TYLj/8Pn///K5f//0+f4/9jo9P/a6fL/2Oj0/9jo9f/a6PT/2ejx/9no8f/b6fX/2eb0/9rn9f/a5/X/3Oj0/9zo9P/X5/P/2efz/9vn8f/e6vD/3env/9jl8//Z5v//qbHt/4B+1/9zbtv/b3Do/2N18v9Wdvf/TnL0/1V09f9edPX/YWz2/2Rh7P9vXdj/dWS7/2hgif9YVWT/OzhB/xEQGf8AAAT/AAUI/0dSVv+lrrf/4+33/+z5///j7/n/2+Tx/9Tk8f/c6O7/3ufw/9jm+P/V5/j/2Orx/9Xr9v++6P//SYLR/2OX5P/R7f//7ffn/6q0kP9bbk3/ZnpX/3mHXf+cuZ//jKqR/4Okj/+BpZX/gKKb/7zb3P/C3Or/zuD//2Rvm/+RmMn/dnyr/zE1Zv80OGv/YWub/5Kix/+gtM3/eY2s/7nR5//B3ej/wN3m/73X4/+92Ob/vdjm/7nW5P+62eL/vNfl/7/a6P+/3OP/vNzh/8Lc7P+3yuX/fZOs/7/X6f+nvNf/VF6N/zk9eP8+RXz/j5zI/4CMtv97grP/vNn//36Zxf+jvN7/scbO/4KXgf+Jn3X/gJVu/5+0lP+gr5P/anZS/3F4S/93flP/0d7I/9v1//+mzP//OGW8/5O54//O7P//0Of9/9fo9f/Y6PT/2Oj0/9nn8//Z5/P/2Ofw/9rp8v/a6PT/2uj0/9rn9f/a6PT/2uj0/9vn8//X5/P/2ejx/9zo8v/e6fH/3ejw/9vn8//W5Pb/2ej//8DN8/+Tn9n/dofW/2OD4v9ai+3/VZDz/1aP8v9dj/P/ZZDx/32Y7v+1v///2dz//8nN6f+0us3/naKx/4WIl/9maXf/NTtG/wQKFf8AAAf/GiAn/3F3fv/FzNX/7PX+/+v3///i7vT/2ubs/9Xl8v/U5fj/1en6/9Ds//+Tvej/R3e3/6rT///e9f//vsmp/253RP9uf1P/aX5e/560nP+XuKP/g6WN/4irl/+Cop3/r8za/7bU7f+CnMD/v9X//3OBsf94grH/mqHM/zc9av80OG3/SVCC/7HA4P/B2+n/eY2s/7bN4//C3ev/vtvk/73Y4v++2Ob/vNfl/7vW5P+62eL/u9bk/73Z5P+93eL/vN3g/8Pd6/+1yOP/h5yy/8bf7/+wxdv/Qk15/zI4c/9QW4//nKzW/2x6pP+Ql8j/stP//2+LyP9+ltD/t83p/6zAs/+Im3T/i553/4Sbf/+0ybD/k6R5/3V9Qf90ekP/dIVq/7zY4//J7f//d53d/2iOyP+83f//wdz2/9br+v/X5/P/2Oj0/9nn8//Z6PH/2efz/9ro9P/a6PT/2uj0/9rm8P/a6PT/2efz/9fn8//X6u//2uny/9rn9//X5ff/1+b2/9vn8//e6vD/2Oju/9jr+v/S5P//us3//5u7/f+Dufj/dsD4/3bC9/+Axvz/ltb5/7Tp9v/M8+v/1u7m/9vt9P/e7f//3en//9ri+f/S2e3/wcbb/6+xw/+JipT/UU9V/xYWHP8HCxD/Nj9D/4KOlP/G1t3/5ff+/+Tz/P/e7v7/vtfx/6PI7v+Ru+j/lbzo/9Pz//+yzdH/ZHpi/299U/9vfE7/laqE/6/KsP+HqZj/h66V/4Wrlf+nxsX/w9r0/4Scyv9shrz/ts7//4mXy/9ibZn/rbje/1FYg/8vMmX/PkJz/7PE3//H4+r/hJa1/7bN4//D3ev/vtvk/7zZ4v++2Ob/vNbk/7zW5P+82eL/vNXl/7/W5v/B2+H/v9zg/8Hb6/+0zOT/jaW5/87j8v+wvNj/PkJ1/zI1cv90ga//m7DM/2R3mv+dqt7/qsv//2Z/x/90iNb/kKXj/8Xd8/+Ys5//iZ53/4iZeP+fsaD/rsK1/4CWev+Inm7/kKdx/5+2kP/U597/3O36/6fB3/+23v//mcz0/7rm///K5f//2uf1/97p8f/Z6PH/2Oj0/9ro9P/Z6PH/2ejx/9nn8//a6PT/2eb0/9nm9P/Z5/P/2efz/9nn8//Z5/P/2efz/9ro9P/a6PT/2uj0/9jn8P/Z5/P/3ev3/97s+P/d6/f/2+n1/9vp9f/c6ff/3ur0/9no8f/V5fH/1+fz/9jn8P/X5fH/1+Xx/9nn8//c6/T/3u32/93u9//b7fj/2uv4/8vb5/+qtb3/dH2B/y1AVf8yNzr/Zmdj/6O3yP+i0P//cafe/6PK9v/S6f//4/T//8zh2f+YrYz/l6t8/4efdf9/m4T/rMW7/6G2rf+Aqpj/iK6Y/6fEu//J4f3/j6nr/1t6yf9igcb/rcH6/6Ku3v9eaJD/prPT/3eApf8uL2L/Nzlv/6y52f/K5+z/jKC5/7fP4//C3ev/vdnk/7zY4/+81+X/utXj/7jV5P+71+L/u9Xm/7zW5v+92uP/vtvi/8Db6f+60ef/m7LC/87k8P+ot9H/OUBx/zY6df+WoM//jZ++/2V4m/+quOj/n8H9/2R8yP9od83/iZzg/6fC5P/M6On/n7Sl/4Wbg/+Gn4X/s82v/6O7mP+EmXP/eo9o/2+HZP9vhmr/uc26/+T3+v/N7Pv/qNHn/7zd7f/b7fT/3+ru/9ro9P/X5/j/2Oj1/9vn8f/b5/H/2efz/9jo9P/c6PT/2efz/9fn9P/Z5/P/2efz/9nn8//a6PT/2uj0/9ro9P/a6PT/2uj0/9ro9P/a6PT/2efz/9jm8v/Y5vL/2Ofw/9nn8//Y5vL/2ejx/9no8f/Z6PH/2efz/9nn8//Z5/P/2efz/9no8f/Y6O//1+bv/9fl8f/W5vL/1uby/9zr9P/k8v7/5/f//+z4+v/c5OT/tcHH/5CsxP+VvuX/ocjv/8vm+//i9/T/wNbD/2yFaf9thGT/e49s/4effP+iwaL/rMy0/5Ctnf+Jq6T/qMnC/9Dt9P+rw+3/gJfi/1Juwv9phcz/n7bu/6687P9bZoz/j5u9/5iiyv8vMWf/Njhu/6u51v/J5uv/l6zC/73V5/+/2uj/vdrj/7zZ4v+92eT/u9bk/7nW5P+81uT/u9Xm/7vV5v+51+L/vtvk/73Y5v+/2Oj/q8PP/8fg6v+tvtj/OkJx/zxAev+lrdz/e4qr/2Z5nP+xwe//lLj4/2R5yv9cZb//laTz/4Kf0v/I5v//x97m/6e8s/+Np4//lbOQ/7LNrP+huZv/lK6Q/46ph/+JpH3/h5t4/7nLuv/Y9PT/wuT0/63O3v/T6PD/3Ozz/9ro9P/Y6Pj/2eb0/9vn8f/b5/H/2eb0/9rn9f/b5/H/2ejx/9fn8//Z5/P/2efz/9nn8//a6PT/2uny/9no8f/Z5/P/2uj0/9ro9P/b6fX/2uj0/9ro9P/b6fX/2uny/9no8f/Z6PH/2uny/9rp8v/Z5/P/2efz/9nn8//Y5vL/2ejx/9np8P/Z6fD/2ejx/9nn8//Z5/P/2ejx/9jn8P/W5vL/1OPz/93q6P/Y7Pf/ze3//7Pf//+dx+r/vtz1/+D0+f/D18T/gZt3/4Cddv+NqIf/lqyT/5+4nP+tzK//nsCo/5S1pv+00NH/zOny/8jl//+EmtT/jqL3/0RctP9th9P/lKzm/7PD8f9fapD/doKm/6Wu2v82Om//NTlq/7G/2//G4+j/o7vN/7/Y6P+/2eX/vdrj/7zZ4v+71+L/u9bk/7vW5P+71OT/u9Pl/7vV5v+71+L/vdrh/7zY4/++2Ob/u9bg/8Le5f+4zeP/QUl4/0BEfv+qsuH/aHqZ/2l+nv+3yPP/i7Hx/2V5x/9UWbb/maL8/4Kd4P+jxOv/0ez6/7PFxv+svbr/rcK//4+nn/99l4X/gaGC/4moh/+VrpT/maua/4adlf+iw8z/uub//6XX//+p1v//x+b//9jo9P/f6fD/3Onx/9bm8//X5/T/2efz/9vn8f/Z5/P/2efz/9nn8//Z5/P/2efz/9ro9P/b6fX/2ejx/9no8f/Z6PH/2uj0/9ro9P/a6PT/2uj0/9nn8//Z5/P/2efz/9no8f/Z6PH/2ejx/9nn8//Z5/P/2efz/9jm8v/Z6PH/2ejx/9no8f/Z6PH/2ejx/9vn8f/b5/H/2efz/9nn8//a5vD/3Onx/8Xn//+y3P//g7jq/3Kq2/+l1Pr/zfD//7LO1f+IoZ3/j6mb/5Gvlv+Mq47/haOK/4KfkP+Wsa3/qMTF/5+7vP/K4Ob/0uz9/6S+5v+Al9v/j6L9/zlQrP9nhdL/i6Xh/7PG8/9kcpb/Z3KY/6au3f8+Qnf/P0Nz/73M5v/A3uP/s83b/7/Z5/++2Ob/vdfj/73Z5P+81+X/utTk/7vV5f+71OT/u9Pl/7vU5P+81+H/vNng/77a5f+92Ob/vtvi/7/d4v/D2+3/UVyI/zo/dv+ptOD/YHST/2uAoP+4yfT/hqzs/2Fyw/9UU7X/ipDv/6nD//9zmbz/zuv6/9Li7/+jq8L/oarL/8fV8f/F3OT/tNLF/7DOu/+txL//qrzD/5m3vP+Os8f/g7Xj/2Ce5P91tfz/r93//9Ps/P/d6ev/3Orw/9fn9//X5/f/3enz/9vn8f/Z5/P/1+f0/9ro9P/a6PT/2uj0/9nn8//Z5/P/2ejx/9no8f/Z5/P/2+n1/9nn8//a6PT/2uj0/9rn9f/a5/X/2uj0/9ro9P/Y5/D/2uj0/9nn8//Z5/P/1+jx/9no8f/Z6PH/2ejx/9nn8//Z5/P/2ejx/9np8P/b5/H/2+fz/9nm9P/X5/T/2Or1/5fP//9spNv/bqTZ/57S//+76v//r9fq/5S1xP+cucf/o8DJ/6rHxP+wzsH/t9TL/8bc6P+7zer/iJe3/6y71f/S6vb/yuX5/3qUvP+qwP//d4zo/zVOsP9gftH/haHe/7TH8v9ndZn/W2eL/6Ss2/89P3X/UFWC/8ja8f++3eD/vtjk/7/Z5/+/2ef/vdfl/77Z5/+71eX/utTl/7vT5/+61OL/utLk/7vS4v+71eH/vNng/77a5f+92Ob/vNzi/7ra3//K5PX/c3+p/y4yZ/+kr9v/YHST/26Do/+7zfb/gafn/1hqw/9PULj/g4ni/8vk//92nLz/nr/Z/9Po///R2vz/jZG6/36BtP+yuO3/3On//9zw///U7PL/1u70/83s7/+93+//p9H2/3qw5/9RjMr/YZXK/6rP9f/V7f//1uf0/9fn8//Y6PT/2uj0/9vn8f/Z5/P/2+n1/9ro9P/a6PT/2uj0/9rn9f/a6PT/2uj0/9ro9P/a6PT/2uj0/9ro9P/Z5/P/2efz/9rn9f/a5/X/2uf1/9ro9P/a6PT/2uny/9ro9P/a6PT/2ejx/9no8f/Z6PH/2uj0/9ro9P/Z6PH/1+jx/9fo8f/b6PD/3efx/9bm9v/L6P//p83w/1yb1f+DuOr/rdf8/7fa9P+93fD/xOPy/8ro8//O6/L/z+3y/9Dt9v/X7///2ub//6as4f9zea7/j5jD/9Lg/f/O6f//ob/Y/4eixP/I3f//b4He/zVLtP9Xcs3/f5ra/7bM9v9pepv/VGKG/6Co1/8zOGn/bXWd/87h9v+92+D/vtnj/7/Z5f+91+X/vdfl/73Y5v+81eX/u9Pl/7rS5P+60+P/vdPl/7rS5P+71uT/vNjj/7zX5f+/2uj/u9vh/7jb3//G4/L/mqrP/yoxYv+Wn8v/aHic/3CFpf/A0/j/f6Pj/1Rpxf9LUrn/k5vh/87l//+z1O7/bo+9/7fT///P5P//xc3k/5GMv/9tYLb/e3LN/7y//P/d7P//1evx/9br7f/S6vb/y+b7/8Pi+/+x1/n/gLDg/1OFwf+IsOX/z+n//9jo9P/Z6fD/2en2/9vo9v/c6PL/3Ojy/9jo9P/a6PT/2uj0/9ro9P/Z5/P/2uj0/9nn8//a6PT/2+n1/9rp8v/Z5/P/2efz/9ro9P/a6PT/2uj0/9nn8//b6Pb/2+vy/9no8f/a6PT/2+fx/9rp8v/a5/X/2uf1/9ro9P/Z6fD/1+jx/9fn8//c6PL/2+jw/9Xs/P+o0Pr/YpnW/5XH6/+23f3/xN72/9Tn9P/Z7PT/1un2/9fr9v/U7Oz/1O3v/9nt//+8wf//d27I/2pesP+Pj8X/wMvp/9bq+/+41f//gp7A/6rE3P/N4///fI3c/zdNs/9PaMj/fJjZ/7rQ+f9pe5r/W2aM/5WgzP8qM1//kaDB/8vh8/+82eD/v9rk/77Y5P+71uT/vNfl/73X5f+71OT/u9Tk/7rS5P+80+P/vNLk/7vT5f+61OT/u9bk/7vW5P+92eT/vtvi/7zc4f+/3Or/us/r/zhHbv95ha//d4Sq/2x/oP/G2/r/h6fi/1Zsvv9QXrH/rr3r/9Hl8P/G4fX/kbDl/3uZ1P/M5///0eHo/66tz/+ejN//emTO/2JTrv+XktD/2t3//+Dq///V4/r/1uj5/9bq9f/Q6vv/w+j//6fW//9vnNn/gqTP/9Po/v/Z6fb/2Oj1/9jo9f/c6PT/3Ojy/9ro9P/a6PT/2efz/9nn8//Z6PH/2uj0/9nn8//a6PT/2uj0/9rp8v/a6PT/2Oby/9ro9P/a6PT/2uny/9ro9P/a5/X/2enw/9no8f/Z6PH/2+fx/9ro9P/a5/X/2+j2/9ro9P/Z6PH/1+jx/9fn8//a6PT/2On2/8jl+v97pc//ksf//8vs///K5/z/0Oj8/9Xo9//X6PX/2Oj4/9bl+P/d6///2uP//5uZ1f9hVa//eGTH/5eK1v+qrNX/1OT1/9Ds8/+Po+r/jqTN/7bN3P/V6v//mKzj/z5Sqf9PZ7//gZzc/7/W/P9ndpb/bHWb/4KLt/8xQGf/tMnk/8Lb6/+91+P/v9nl/77Y5P+71uT/vNfl/7vV4/+71OT/utPj/7rT4/+70uL/u9Li/7vU5P+71OT/vNbk/7zX5f+82OP/v9zl/77b4v+82eL/yuT1/2R4l/9WYor/hpK6/2p9nv/I4vr/nr/s/154rv96jcD/ytz5/83j7v/J4/T/qsXx/36Z0f+Ztd7/1+z//8LM5P+dl8b/m43V/4160f9pVLH/f2rH/8XH9//e5///1eb5/9Po9//R6Pj/zub8/8ro///L7f//mbni/5Ku0f/U6f//1+fz/9ro9P/a5/X/2eb0/9zo8v/a6PT/2efz/9no8f/Z6PH/2ejx/9no8f/a6PT/2uj0/9ro9P/a6PT/2uf1/9nm9P/Z5/P/2uny/9rp8v/a6PT/2ejx/9no8f/Z6PH/2ejx/9jn8P/Z6PH/2uj0/9jo9f/X5/P/2ejx/9vn8f/W5vb/1Oz//6PA2/+oyOX/zOz//9Tn9v/T5/j/0ef5/9Pn+f/W6Pn/1un4/93r///Iyvr/gHO//2xVsf+Icsr/kITG/5ybx//L1vL/1+v//6jE3P+QneH/k6bR/8zj8v/M5u3/xdr5/2J4sv9KZKb/kq3g/8fd//9lc5D/goix/15nk/9XaIn/yOLz/73Z5P++2uX/v9nl/73X5f+81ub/vdbm/7zV5f+81eX/utPj/7rT4/+60+P/udLi/7vU5P+91OT/u9Tk/73Z5P+71+L/v9nl/8Db5f+82eL/xOLt/6C4zv9AT3b/h5K+/3CBov/E3/P/ttX2/6zG3v/C1+z/wNj0/6/O7/+/3v3/wN77/5Wu2P+Cm9P/p7/z/9To//+/zNz/m527/4p/vf+AasL/blK1/2ppkf+wtMz/2+rz/9Xq8v/W6PP/3+vt/+Ps6f/a6vD/1u///6TC5f+vxuD/3Oz4/9vn8f/X5/T/1+f0/9vn8f/Z5/P/2efz/9no8f/Z6PH/2uny/9ro9P/a6PT/2uj0/9ro9P/a6PT/2uf1/9nn8//Z6PH/2ejx/9rp8v/a6PT/2efz/9ro9P/a6PT/2Ony/9fo8f/Z6fD/2ejx/9fn9P/X5/T/3Ojy/9vn8f/Y6Pj/yuL6/7LL5f/X6/z/2+nv/97n9P/e6fH/3unx/9zo8v/b6PD/4O/y/8LK1/90bZj/a1ih/4Bpu/+FdrP/np68/8zZ6f/X6///scfw/5Cm2v+Lm8b/v9X//8Df//+00+j/w97y/7vT8f+WsNX/tNDz/8bc+P9teJb/kZfC/0BJdf+VqMP/yOXu/7zZ4P++2ef/vdrj/7zY4/++1+f/u9Tk/7zV5f+71OT/utPj/7nS4v+50uL/uNPh/7nT4f+71OT/u9Tk/7zX5f+82OP/u9fi/7/Z5/++2eP/vNng/8bg8f9cbJH/bHal/3yMsP/C3O3/udru/83m6v/L3uX/tNDz/3mi4P95pdr/s9n3/7vY8/+JodX/gJvb/6W/7f/T6///z9/v/6632P+ens7/p6LV/77F1v/T3Ob/3u70/9zv9v/d7vf/4u7y/+bu7f/f7O7/0+j3/9Pr//+81Oj/0+Tx/9rp8v/Z5/P/2efz/9no8f/Z5/P/2efz/9nn8//Z5/P/2efz/9ro9P/a6PT/2uj0/9no8f/Z6PH/2uj0/9no8f/Z6PH/2Ofw/9no8f/a6PT/2uj0/9rn9f/a5/X/2Oj0/9fo8f/Z6PH/2efz/9nm9P/X5/T/2efz/9zo8v/Y6PX/0OLz/9Hl9//Y6fb/3Onx/93q8v/g6vH/4ezw/+Lt9f/f7/b/3/Dz/9zm7f/M0OL/srPV/6qq0v+7wd7/1eP1/9fr/P+0y+v/kqjc/4GV1v+/1+//tNb//2aT0P+Mteb/stDp/8vg7//L5PT/wt3x/8Pa8P98ian/e4Kt/05agv/C2e//v9zg/73b4P++2Oj/vNni/77Y5P+91+X/u9Xj/7vU5P+60+P/uNHh/7nS4v+50uL/uNLi/7jS4v+60uT/u9Pl/7vV4/+92eT/vNfl/77Y5v+/2uT/u9jf/8fh8f+crs3/VGCK/4eYuf/B2e3/utzp/8zj5f+9ztf/rcv0/2uc5v9Yj9j/h7bi/73c9f/B3fz/haDS/36Z0f+guOb/y+D//9fv///U7v//3ff//9r2///J6P//tdn//6rO9v+pz/n/r9T//7ze///J5v//0un5/9bq9f/V6/f/0eX2/9Xm8//c6fH/3Onx/9jo9P/Z6PH/2efz/9nn8//Z5/P/2efz/9nn8//a6PT/2uny/9no8f/Z6fD/2Ofw/9no8f/Z6PH/2ejx/9no8f/Z6PH/2efz/9ro9P/a5/X/2efz/9no8f/Z6PH/2efz/9ro9P/Z5/P/2uj0/9ro9P/Z5/P/2uj0/9bo8//U5/b/0ef5/8vp+v/J6P//ut3+/6rT+v+kzvj/rNb7/7zh///O7///2Pj//9j1///V7/3/zOP9/6/F7v+Vqt3/g5nJ/77U/v+43/v/b6La/0qE0P+Ht/n/pcLn/7zP3P/K4uj/w9/q/77X6/+GlbX/V2OL/4ycwP/J4fP/u9jc/7/c4f++2Oj/vNni/77Y5P+81uT/vNbk/7rU4v+50uL/uNHh/7nS4v+50eP/udLi/7rT4/+50eP/utPj/7rU4v+81uT/vtjm/7zW5P+/2eX/vNni/7zX5f/F3fP/boOf/3qMqf/G2/H/u9zl/83h7P+ltMf/tdH6/3Gj5f9Xk9//davo/6DH5//I5/b/xOL9/4Cd0P9+ldP/nbLl/7TN7f+53fX/kbvY/2md4P9Vjd7/Q4Tg/z6C4f8/heP/Qofo/02M5P9qmdf/tNHs/9nu9v/V6fT/0ef5/9Pn+P/Z6PH/2+fx/9fn9P/Z6PH/2efz/9nn8//Z5/P/2efz/9no8f/Z6PH/2ejx/9no8f/Z6PH/2ejx/9ro9P/a6PT/2uny/9no8f/Z6PH/2uny/9ro9P/a6PT/2efz/9nn8//Z5/P/2efz/9nn8//a6PT/2uj0/9ro9P/Z6PH/2Ofw/9Xn8v/T6Pf/zub4/3+z3P9bm9L/SpXh/z2P6P87jOf/Pozm/0iQ5P9enOj/eq7j/5vE5P+42vH/qsXq/5Oo5v9zh8j/v9b8/9Ps9v+Dt+z/YqHe/1GU2f+Lu/v/q8Lw/6a0yv/P5u7/wt/o/8DY7v97jaz/Xm+Q/8DW7/++2ef/vtnj/7/a5P+81+X/vNjj/73X5f+91OT/vdTk/7rT4/+60+P/uNLi/7nT4/+50eP/udHj/7nS4v+50uL/udLi/7rT4/+71OT/vdfl/7zW4v+91+P/vtrl/7zX5f/B3u3/rMbX/3mQpv/E2/H/wN/o/8DR5v+IkbP/yNv//4Gt4v9dmdv/aqPo/4q46P+w1ev/x+j3/8bi//91jMT/fI/M/6O47/+mwvj/l7ry/2Ca8/9HiOr/OIHt/zGB8v80hfT/PYnz/1qc9f+Txf//xOb//9Lp+P/S6vb/0On5/9Ho+P/W5/T/1+fz/9jn9//a6fL/2efz/9nn8//Z6PH/2ejx/9jn8P/Z6PH/2ejx/9no8f/Z6PH/2uj0/9ro9P/a6PT/2uj0/9rp8v/a6fL/2ejx/9no8f/Z6PH/2efz/9nn8//b5/P/2efz/9nn8//a6PT/2uj0/9rp8v/Z5/P/1+j1/9Tn9P/W6fb/1+r3/6DZ//9qsPP/QZXu/zCM8f8vi/L/Morv/zOF6/9AhOf/bJ7w/5e8+P+nxfT/lq7i/2J5t/+wx///zOj//7TW3P9lpPT/X6Tj/2Cf0f+iyf3/tcH3/4GJsf/M4vT/v97n/8Ld8f9qf5v/mK7H/8fh8f+61uH/vtjm/7/Z5/+92eT/vNfl/7vU5P+90+X/vNLk/7zT4/+60+P/udPj/7nT4/+60+P/udHj/7jQ4v+50eP/udLi/7vU5P+60+P/vtXl/77V5P+81uL/vdnk/77a5f+72eT/wNvp/7DK2v+91+j/xePu/6Ww0P9fXZH/y9X//5zC8v9inND/YaDk/22k6f+Nve3/t9/y/8zq9f/B1/r/YnO2/2p7zP+jtvr/us3//7zj//+34f//odD//5bI//+Xyf//p9b//7/l///K6f//zej8/8/o+P/S6fn/0un5/9Lp+f/S6fj/1Of2/9bm9v/a6PT/2uj0/9nn8//Z6PH/2uny/9no8f/Z6PH/2efz/9nn8//Z5/P/2efz/9ro9P/a6PT/2uj0/9ro9P/Z5/P/2ejx/9no8f/Z6PH/2ejx/9nn8//Z5/P/2efz/9nn8//X5/P/2Oj0/9ro9P/X5/P/1Of2/9Po9//U6fj/0+n1/8bo///A6f//q9z//5jO//+Px/7/j8X//5vN//+14f//ttj//67J//+Ooez/VGOr/52x4P/O6///tNr4/4y44f9Tmfb/WaLc/2+pzP/A2v//rq3x/1hVk/+7y+j/xOPs/7za5f+WrcP/wdnr/77Z4/++2eP/vtfn/73W5v++2OT/vNbm/7vU5P+80+P/vNPj/7zT4/+60+P/uNLi/7nR4/+30eH/uNHh/7jQ4v+50eP/udHj/7rS5P+80+P/vdTk/77V5f+71eP/vNjj/73Z5P++2uX/vNfl/8Hc6v+82ef/xuPx/52ky/87MnH/k5XW/8Df//9tpdT/VpjZ/1eV6f9mnOP/ncjj/83q5//R5ff/nKvz/1dnx/9caa3/s7rV/7/Pzv/R4Nz/6fjw/+Xy6v/j8Oj/5O/n/+Ls5v/d6+r/1+rx/9Lp+P/Q5vj/0Of3/9Dn9//O5/f/0Of2/9Tn9v/Z5/P/2uj0/9ro9P/a6fL/2uny/9no8f/a6PT/2eb0/9jl8//Z5/P/2efz/9nn8//Z5/P/2uj0/9nn8//Z5/P/2Oj0/9no8f/Z6fD/2ejx/9nn8//Z5vT/2efz/9fn8//X5/P/1efy/9bm8//W5vP/1uf0/9Ln9v/R5/n/z+f7/+Lq6f/j6Ov/5urr/+jv6v/l8O3/5/P3/+fz9f/D1Mv/vNHT/4aXyP9NV7X/f4bd/83d///J6u3/mMbl/2KW4/9HlPH/U5vR/5DF4P/L3P//c2e5/0U7iP+msdf/yefs/7zc4f/A2ur/wNro/77a4f++2uH/vtbo/7zU5v+91+P/u9bk/7rU4v+70uH/vtPi/73U4/+60+P/uNLj/7nR4/+30eH/t9Hh/7fR4v+50eP/utLk/7rS5P+60+P/vNXl/73U4/+91OP/vNbk/73Z5P++2uX/v9zl/77Z4/+/2uT/w+Lj/7PD4P9vc6b/aG6Z/7vL4v+11+7/WpHO/zeC8P8pffr/R4no/6XN/f/O6Pn/utjx/36f1/9ZacL/VVG7/7i62P+luu7/irDx/7je///U7v//1Onx/8fi/f+83v//tNr//7XZ//+33P//weL//8zr///V8P//1+///9Lq///T6vL/0ujz/9Tn9P/W6PP/2ejx/9rm8P/b5/P/2uj0/9jo9P/Z6PH/2+fx/93m8//b5/P/2uj0/9nn8//b5/H/2uf1/9vn8//b5/P/2efz/9nn8//a6PT/1+fz/9bn9P/T5/j/2uz9/9zu///c7v//0uv//8Pk//+53v//ttz//7vf///J6P//0ujz/9bn+v/P6P//qNL//4my2f+1xfT/kojU/01Jqf9tg9H/mcDn/8rr/v+t0ff/VI7n/yR9/f86h+P/a6fd/8jo//+gqMb/YVyT/2hsof+wxeD/xeLn/8Dc4//B2ur/vtfn/7/a5P++2+L/u9bk/7zW5P+81uL/u9Tk/7rT4/+60+P/utPj/7rT4/+50uL/udLi/7nS4v+40eH/t9Dg/7jQ4v+40OL/utPj/7rT4/+60+P/utPj/7zT4/+91OT/vNXl/7zX5f+92eT/v9zl/7/c5f++2uX/v9zj/8Pb7f/O3f3/vcnr/5uryP/L4///mcLv/0mEyv8vcs//L2rH/12Kzf+52///yOb//6XC5/9/ltr/XWzI/2Vpo/+ywfn/mrjp/3CSvf+YuuX/qs7+/4Kn4/9hicr/Wn/D/2CDx/9kh8v/aY7S/3me3P+QseL/o8Hk/73Y8v/T6/f/0en1/9Pp9f/V6PX/1ebz/9bn9P/W5/T/1uf0/9Tn9P/W6PP/1ujz/9fn8//Y6PT/1uby/9fn8//Y6PT/2Oj0/9jo9P/Y6PT/1+fz/9bo8//U5/T/1Of0/9Xo9f/L4vL/t8/r/6fD7P+Qr+b/eZ3Z/2yQ0P9li8z/YIbH/2KIyP90mdP/l7rs/7DS//+Iq9f/fZ/K/7bP//+CkNL/T1am/3eE0P+OqN7/ud7//7ff//9qmdH/N3HD/yxw0/9bls7/qdT//7zV9f+bpcf/ydD3/8bV9v/E2e7/wNvl/8Hc5v/A2uj/vtjm/7/a5P+92OL/u9Xj/73W5v+81uT/u9Tk/7rT4/+50uL/utPj/7rT4/+50uL/udLi/7nS4v+30OD/t8/h/7jQ4v+40OL/udLi/7rT4/+60+P/udLi/7zT4/+90+X/vNTm/7vV5f+92Ob/vdnk/7/b5v++2uX/v9nn/7/c4/++2+T/zOH3/5eny/+wweL/yub+/6nO6P9xntH/UoPP/z9wvP93oNH/w+P2/8rj8/+hvuX/fJ/f/3R+zP93hbn/zeH//67K7f9fh8L/V4bX/3Kk9v+Gs/3/f6br/2mM1f9VfMr/SnTH/0l0xf9XfsL/faDM/7bU7//S7Pr/z+n3/9Hp9f/T6fX/0+j3/9Po9//T6Pf/0ej3/9Dn9v/R6Pf/0uf2/9Lo9P/T5vP/1ebz/9Tl8v/U5/b/1Of0/9Tn9P/U5/T/1Of0/9Lo9P/Q5/f/0Of2/9Lq9v/J4fP/lbPW/16Cvv9Gb77/QW3A/0hzwv9Ufcb/ZY3V/3+q6f+Js///c6L0/1uLzf97o83/yuL//5Wg2f9aZ7X/do7a/4yq2/+62PH/w+H8/36o1/9GfL3/UITG/3Wj3f+12uj/yuX//5WnzP+uv+D/zOH2/8Tc6P/A2+X/wNro/8Da6P+92eT/v9rk/77Y5P+71eP/vNbk/73W5v+71OT/utPj/7rT4/+50uL/udLi/7nS4v+40uL/uNLi/7jS4v+30eL/t8/h/7fP4f+40eH/udLi/7rT4/+50uL/uNHh/7vS4v+80+P/vdTk/7rT4/+81+X/vdjm/73Z5P+/2+b/vtnn/77d4P+/397/xeHs/6W61v+itNH/zePv/8fk6P/E4/j/sdX//6fO//+rz/f/wt/u/8rk6v/C4vX/pcvu/5it6/+ImsP/o7XM/9Lq//+x1///e6jr/1uJ0P9jkNP/gKrt/5vF//+gzf//pc///6nT//+53f//yur//8vq///O6Pb/0Or4/9Dn9v/R6Pf/0ej3/9Ho9//Q5/f/0Of2/9Ho9//P6ff/z+j4/9Lp+f/T6Pf/1Of2/9Ln9v/T5/j/0ej3/9Ho9//R6Pf/0Oj0/9Ho9//P6Pj/z+n3/9Ho9//Q6vv/zuv//7/i//+s1P//os///6LS//+fzP//k8D//4Cs6f9nkdj/ZJDX/4668P/E6P//s8bn/3yHuf+Lntv/l7jq/7XY8v/J6PH/wt7v/6vS+P+k1P//sNr//8Ti///M5+T/xdzs/4eZuP+1yuX/xN/p/7/c4P/B3eT/wNro/73Y5v++2+T/vdrj/7vV4/+60+P/u9Tk/7vU5P+60+P/u9Tk/7nS4v+60+P/udLi/7jR4f+40eH/uNLj/7nT5P+30OT/ttDh/7fP4f+40eH/uNHh/7nS4v+50uL/udLi/7vS4v+70uL/vNPj/7zV5f+61OT/vNfl/73Z5P+92eT/v9vm/7/d4v+/3uH/wN3m/8Te7//A2en/wt3n/8Pg5f/D4On/wt7v/8He8//D4fL/xeHs/8fj6v/G4u3/x+Tz/77a+P+2zef/p73W/7vT6f/G5fr/w+T+/67T9f+Qt+P/dqLX/22b1f98qeL/l73t/7ra/f/J5f3/yeX2/8rn9v/O6fP/zefz/8/n8//Q6PT/0Oj0/9Ho9//Q5/b/0Of2/9Ho9//S6fj/0On5/9Ho+P/S6fn/0+j3/9Lm9//R6Pj/zuj2/9Ho9//O6Pb/zuj2/83n9f/Q6PT/0Oj0/87o9P/O6Pb/zOb3/8rk/P/G5f//sdj+/4u56f9yoNr/bJra/36m2v+YwOr/tdj5/8fm///C2/X/mq/O/6i93f+61PL/w+L5/8Tk8f/H5Ov/xuLt/8Ti8//B4PX/wd/y/8Pd7f/F4ub/wtzq/7/X6//F3u7/wNvl/8Dc4//A2+X/v9nn/8Da5v++2uX/vNjj/7vV5f+71eX/vNXl/7nS4v+60+P/utPj/7rT4/+60+P/uNHh/7fQ4P+40eH/uNDi/7jQ4v+40eX/t9Hi/7jQ4v+40OL/uNDi/7jR4f+50uL/utPj/7vS4v+80+P/utHh/77V5f+81eX/utXj/7zY4/+92uP/vtnj/8He5//A3Of/vtrl/8Dd5v/A3+j/v93o/8De6f/C3+j/yODm/8jh4//G4eX/xOHq/8Ph7P/H4uz/yuLo/8fl6v/I5fT/x+L3/8Te7v/L5ev/zOXn/83o8v/I5/7/uuD//7Pd//+02vz/u9rx/8bg7P/Q6O7/zuju/8zm8v/N6fD/zunz/9Do9P/P5/P/z+jy/9Do9P/R6Pf/z+b1/9Hp9f/P6fX/z+n3/9Dn9v/P5vX/0en1/9Do9P/Q5/b/z+n1/87o9v/O6Pb/zuj2/87o9P/N5/P/zuj0/87o9P/N5/P/z+nw/9Lo7v/P5+3/weHu/7Xb8/+w2Pv/s9r//7vh///G6Pj/zOnt/9Dm6//G3e3/wt3y/8bk9f/J5u//x+Tp/8fj6v/G4+z/xuLp/8fh5//J4ef/yd/q/8Xf6/+/3Or/wt7p/8Pd6f/C2ub/w9vn/8Da5v++2OT/wNrm/7/Z5f+91+P/vNfl/7zW5v+71eX/utLk/7rT4/+60+P/utPj/7rT4/+50uL/udLi/7jR4f+40eH/uNHh/7nS4v+30eL/t8/h/7jQ4v+40OL/uNDi/7fP4f+40eH/utPj/7rT4/+60+P/u9Li/77S4/++1eX/utTi/7rW4f+72uP/vtnj/8Da5v/A2+n/wNzn/7/c5f++3uT/v97n/8Pf6v/E3ur/xd/m/8bg5v/F4ej/xeLr/8Tg6//G4ev/yePq/8bj6P/G4+z/xeLw/8jk7//K5Or/zebq/8zk6v/I5O//xeTz/8Xk8//I5fT/zOby/87o7//O6O//zOjv/8zn8f/M6e7/zOjv/83m8P/M5/H/zOfx/83o8v/P5/P/zefz/83o8v/M6fL/zejy/83o8v/N6PL/zejy/83o8v/P6PL/zunz/87p8//O6PT/zen0/8zp8v/N6PL/zOby/8zm8v/M5/H/z+nw/8/n7f/P5+3/y+fu/8nn8v/H5vX/xuT3/8bm8//K5/D/y+bq/83l6//M5e//yeTy/8Ti7f/H5Ov/x+Pq/8bh6//G4ev/xuHr/8bi6f/I4un/x+Dq/8Tb6v/C3ev/wd3o/8Db5f/E3Oj/w9vn/77Y5v+/2eX/vtjk/73X4/+91+P/vNfl/7vW5P+71OT/utLk/7vT5f+60+P/uNHh/7rT4/+50uL/uNHh/7jR4f+40eH/uNHh/7rT4/+40uP/t9Hi/7fP4f+3z+H/uNDi/7jQ4v+40eH/udLi/7jS4v+60+P/vNPj/73R4v++0uP/vtXk/7vV4f+71+L/vtjk/77Y5P+92eT/v9vm/8Dd5v/A3eb/wd3k/8Le5f/E3+n/w9/q/8Ld6//A3ev/xODr/8bh6//F4uv/xeHs/8bi7f/F4uv/xeLp/8bj6v/H4+7/x+Lw/8nj8f/K5e//yeXs/8rk6v/M4+v/y+Tu/8rk8P/K5fP/yubx/8vn7v/L5+7/y+fu/8vm8P/L5vD/zOfx/8vm8P/L5fH/zOfx/8zp8v/L6PH/y+jv/8zo7//N6fD/zenw/83o8v/M5/H/zejy/83o8v/N6PL/zOfx/8vo8f/K5/D/y+bw/8vm8P/M5/H/y+jx/8rm8f/K5vH/yePv/8zl7//N5+7/zubs/8jm6//I5e7/yOPx/8jk7//H5O3/yeXs/8fi7P/F4ez/w+Hs/8Xi6//G4ev/xeDq/8Ph7P/A4O3/wt3r/8Xd6f/E3uX/wdzm/8Hb6f/B2+n/v9nl/8Da5v+/2eX/vNbi/7zW4v+91+P/vNbk/7zV5f+80+P/vNPj/7rT4/+50uL/utPj/7nS4v+50uL/uNHh/7jR4f+40eH/uNHh/7nS4v+20+L/t9Hi/7fP4f+3z+H/uNDi/7jQ4v+40OL/udLi/7rV4/+51OL/utPj/7zT4/+70uL/vtXl/77V5P+91OP/u9fi/7zZ4v++2eP/vtvk/8Dd5v/A3eb/wd3k/8Pd5P/B3Ob/wt7p/8Pe7P/C3un/w97o/8Tf6f/E4er/xODr/8Xh7P/F4uv/xuPq/8fk6//G4+z/x+Pu/8fj7v/H5O3/yOTr/8jl6v/I5Ov/yeTu/8rk8P/J5u//yuXv/8rm7f/K5u3/yebt/8nm7//L6PH/y+bw/83l8f/N5fH/y+Xx/8vm8P/L5vD/y+bw/8vm8P/L5vD/zOfx/8zn8f/M5/H/zefz/83n8//M5/H/y+bw/8vn7v/L5+7/yubt/8vm8P/L5vD/yubx/8nl8P/J5fD/yuTw/8zl7//L5ez/y+Xs/8fk7f/H4+7/x+Pu/8ji7v/I4+3/yOPt/8fh7f/F4ez/w+Hs/8Xi6//G4ev/xOHq/8Hf6v/B3+r/w9/q/8Tc6P/D3eT/xN3n/8Hb6f+/2ef/wNrm/7/a5P+91+P/u9bk/73X5f+81uT/vdTj/73U5P+80+P/u9Tk/7nS4v+50uL/udLi/7nS4v+50uL/uNHh/7jR4f+40eH/uNHh/7jQ4v+20uP/t9Hi/7jQ4v+40OL/uNHh/7fP4f+40OL/t9Hi/7nU4v+61uH/utTi/7rT4/+91OT/vNPj/7zT4//A1Ob/vNjj/7vX4v+82OP/vtrl/77b5P+/3OX/wdzm/8He5//A3eb/wN3k/8Le5f/G4Of/xN/p/8Pd6f/D3uj/xN/p/8Th6P/E4er/xeLr/8Xi6//G5On/x+Tp/8fj6v/H5O3/xOPs/8Xj7v/H4+7/yeTu/8jk6//K5Or/yeXs/8nl7P/J5ez/yOXs/8bl7v/I5e7/yuXv/83l8f/K5PD/y+bw/8rl7//L5vD/y+bw/8vm8P/K5e//y+bw/8vm8P/L6PH/y+Xx/8vl8f/L5vD/yuXv/8rm7f/K5u3/yeXs/8nk7v/J5O7/yubt/8zm7f/L5ez/y+Xs/8rl7//H4+7/x+Pu/8Xj7v/G4+z/yePq/8nj6v/J4uz/xOHq/8Th6v/F4uv/xuHr/8bh6//E3+n/w+Dp/8Tg5//E4Of/wtzo/7/Z5//B3uf/wNvl/7/Z5f/A2ub/wNrm/73X5f+81uT/vdfl/7zW5P+71OT/vNPj/7zT4/+60+P/utTi/7vU5P+50uL/uNHh/7jR4f+60eH/uNHh/7jR4f+40OL/uNDi/7jQ4v+30eL/uNDi/7fP4f+2z9//uNHh/7fQ4P+40OL/uNDi/7fR4f+40+H/udLi/7rT4/+60+P/utPj/7vS4v+80uT/vNbi/7zY4/+71uT/vNfl/73Z5P++2uX/v9vm/8Dc5//B3uf/wt/m/8Hd5P/D3+b/w97o/8Pd6f/E3+n/xd/m/8Lf5v/E4Of/xeDq/8Th6v/F4un/xeLp/8bi6f/G4ev/xeLr/8bi7f/G4+z/yOPt/8jk6//H4+r/x+Ls/8jj7f/H5er/xuPq/8Xk7f/I5e7/yOXu/8nk7v/K5e//yeTu/8rl7//L5vD/yuXv/8rk8P/J4+//yeTu/8rl7//L5vD/yeTu/8rl7//K5e//yeTu/8jl7v/I5e7/yeTu/8nk7v/J5ez/yeXs/8nl7P/K5Ov/yuPt/8jj7f/G4+z/xuLt/8Ti7f/F4uv/xuLp/8ji6f/G4ev/xeLr/8Xi6//F4uv/xeDq/8Tf6f/F4Or/xODn/8Pe6P/E3ef/wtzo/8Hc6v++3Of/vtvk/8Db5f/A2ub/vtjm/7zW5P+91+X/u9Xj/7vV4/+71OT/utPj/7rT4/+61OL/udPh/7rU5P+50uL/uNHh/7jR4f+40eH/uNDi/7jQ4v+40OL/uNDi/7jQ4v+40OL/uNDi/7fP4f+3z+H/t9Dg/7fQ4P+40eH/uNHh/7nS4v+40eH/udLi/7nS4v+60+P/udPh/7nS4v+60+P/vdTj/7vV4/+81+X/vdjm/73Y5v+/2ef/vtjk/7/a5P/A2+X/wN3m/8Hd6P/B3ej/wdvn/8Td5//F3uj/w97o/8Te6v/D3uj/xODn/8Th6v/E4Ov/w+Du/8bi7f/E4er/xuLp/8nj6v/K4+3/x+Ls/8bi7f/E4u3/xuLt/8fi7P/G4+r/x+Tr/8fk7f/H5O3/yOXu/8fk7f/I5e7/yOXu/8jl7P/I5e7/yeTu/8nk7v/J5O7/yeTu/8nk7v/J5O7/yeXs/8nl7P/J5ez/yeTu/8jl7v/H4+7/x+Pu/8jj7f/I5Ov/x+Tr/8jk7//G4u3/xuLt/8jj7f/H4+r/yOLp/8Th6P/F4uv/w+Hs/8Tg6//E4er/xeDq/8Tf6f/F3+v/xN7q/8Pe6P/E3+n/xN/p/8Hb5//B2+n/wtzq/8Da5v+/3OX/v9zl/8Da5v++2OT/vNbk/73X5f++1eT/vdTj/7rT4/+60+P/utPj/7rT4/+50uL/udLi/7rT4/+40eH/uNDi/7jQ4v+40OL/uNDi/7jQ4v+40OL/uNDi/7jQ4v+40OT/uNDi/7fP4f+40OL/uNHh/7fR4f+30eH/uNHh/7fQ4P+60eH/udLi/7jR4f+40uL/t9Hh/7jR4f+60+P/utTi/7rU4v+71eP/vNbk/7zW5P++2Ob/vtjk/77Z4//A2+X/wNvl/8Dc5//C3un/wt/o/8Hc5v/B2+f/wtzq/8Te6v/E3+n/xN/p/8Xg6v/F4ez/xeDu/8Tg6//E4er/xeHo/8ji6f/J4+r/xuHr/8Lg6//E4u3/xuLt/8fi7P/H5O3/x+Ls/8fi7P/H4uz/xuLt/8fj7v/H5O3/x+Tt/8fk7f/I4+3/yeTu/8jj7f/I4+3/yOPt/8jj7f/K4+3/x+Pq/8jk6//I5Ov/x+Tt/8fk7f/H4+7/x+Tt/8fi7P/G4+z/xuPs/8fj7v/G4u3/xuLt/8Xi6//G4un/yOLp/8Xi6//F4uv/w+Hs/8Lg6//D3+r/xN/p/8Tf6f/E3+n/xN7q/8Te6v/D3en/wdvn/8Lc6v/C3Or/vtjm/77Y5P+/3OX/v9nl/73X4/+81uT/vdfl/7zW5P+91OT/vNPj/7rT4/+60+P/udLi/7nS4v+40eH/uNHh/7nS4v+40eH/ts7g/7fP4f+40OL/uNDi/7jQ4v+40OL/uNDi/7jQ4v+30eL/ttDh/7fP4f+40OL/uNDi/7bQ4f+30eL/t9Hh/7jR4f+60eH/uNHh/7nS4v+50uL/udLi/7jR4f+70uL/utTi/7rU4v+71eP/u9Xj/73X5f+81uT/vtjm/77Y5P++2eP/wdzm/8Lb5f+/2uT/v9zl/8He5//C3Oj/w9rp/8Le5f/D3uj/xN7q/8Pe6P/D3+b/xeHo/8Th6v/E4er/xOHq/8Th6P/F4Or/xOHq/8Xi6f/F4un/xuLp/8bh6//H4uz/x+Ls/8fi7P/H4uz/xuPs/8bi7f/G4+z/xuPs/8jj7f/I4+3/yOLu/8jj7f/I4+3/yOPt/8jj7f/H4uz/xuPq/8fk6//I4+3/xuPs/8bj7P/H4uz/xuHr/8Xi6//F4uv/xeLr/8bh6//G4un/xuPq/8Xi6//E4er/xeDq/8Tg6//E4er/xeHo/8Pg5//E3+n/xN7q/8Pe6P/D3+b/w97o/8Lc6P/B2+n/wdvp/8Hb5/+/2uT/v9nl/7/Z5f+92eT/vdfj/7zW5P+81uT/vNbk/7vU5P+80+P/utPj/7rT4/+60+P/udHj/7jQ4v+40eH/uNHh/7jR4f+30OD/ts7g/7fP4f+3z+H/t8/h/7fP4f+40OL/uNDi/7jQ4v+30eH/ttDh/7fP4f+40OT/uNDk/7fP4f+20OH/t9Hi/7fR4v+40OL/uNDi/7jQ4v+50eP/uNHh/7rR4f+50uL/uNTf/7nT4f+81eX/utPj/7rT4/+91ub/vdbm/77Y5v+/2eX/vtnj/7/a5P/A2+X/v9zl/8Dd5v/A3eb/w93p/8Lf6P/B3uf/w97o/8Pe6P/D3+b/wt/m/8Lf6P/D4On/weDp/8Hg6f/E4er/xeLr/8Xi6f/F4un/xuLp/8bh6//F4ej/xuHr/8Xi6//F4uv/xeLr/8Th6v/F4uv/xeLr/8Xi6f/F4un/xeLr/8fi7P/H4uz/x+Ls/8Xi6//F4uv/xuPq/8bj6v/G4+r/xuPs/8bj7P/G4+z/xuPq/8bj7P/G4+z/xeLr/8Pg5//F4ej/xOHo/8Th6v/D4On/xN/p/8Th6v/E3+n/xODn/8Pf5v/B3uf/w93p/8Pd6f/F3uj/w9zm/8Hc5v/B2+f/wdvn/7/Z5f+/2uT/vtnj/77Y5P+92eT/vdfl/7vV4/+81uT/utPj/7vU5P+71OT/utPj/7rT4/+60+P/udLi/7fQ4P+30OD/uNHh/7jR4f+60eH/t8/h/7fP4f+3z+H/t8/h/7fP4f+40OL/t9Hi/7jS4/+20d//ttDg/7jQ4v+60ub/us/k/7jQ4v+30eL/ttLj/7fR4v+30OT/t9Dk/7nR5f+50eP/u9Li/7nS4v+60+P/utTg/7rU4v+81eX/u9Pl/7vT5f+71OT/vNXl/73X5f+92Ob/vtvp/7vY5v+/2+b/wd7n/8He5//B3uf/wd7n/8Dd6//C3+j/w9/m/8Lf5v/A3un/vt7p/8Hg6f/D4On/w+Dn/8Pg6f/E4er/xOHq/8Lg6//C4Ov/xODr/8Xi6//G4+j/xeLr/8Ti7f/D4uv/xuPq/8bj6v/G4+r/xOTq/8Tk6v/D4+j/xuPq/8bj7P/H4uz/xeHo/8Xi6f/E5Or/x+Tr/8jl7P/I5ez/xuPq/8Xi6//F4uv/xOHq/8Th6P/E4er/xOHq/8Th6v/E4Ov/xOHq/8Xg6v/D3+b/x+Ho/8Xh6P/E3+n/wt7p/8Df6P/B4On/xOHq/8Pd6f/D2un/wtzo/8Ld5//A2+X/wNrm/8Hb6f+/2uj/vtrl/77Y5P+92eT/vdfl/77V5P+91OT/u9Tk/7zV5f+71OT/utPj/7rT4/+60+P/utPj/7jR4f+40eH/t9Hf/7jR4f+60eH/t8/h/7bQ4f+20OH/t9Hi/7jQ4v+40uP/uNLj/7jS4/8AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="


class EncryptionMode(Enum):
    PLAIN = "明文"
    RSA = "RSA"
    SM4 = "SM4"


class APIWorker(QThread):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, base_url: str, encryption_mode: EncryptionMode,
                 api_token: str = "", sm4_key: str = "", rsa_public_key: str = ""):
        super().__init__()
        self.base_url = base_url.rstrip('/')
        self.encryption_mode = encryption_mode
        self.api_token = api_token
        self.sm4_key = sm4_key
        self.rsa_public_key = rsa_public_key
        self.uri = ""
        self.data = {}
        self._polling_new_messages = False

    def set_request(self, uri: str, data: Dict[str, Any]):
        self.uri = uri
        self.data = data

    def _generate_sign(self, timestamp: int) -> str:
        if not self.api_token:
            return ""
        sign_str = f"{timestamp}\n{self.api_token}"
        signature = hmac.new(
            self.api_token.encode('utf-8'),
            sign_str.encode('utf-8'),
            hashlib.sha256
        ).digest()
        b64_sig = base64.b64encode(signature).decode('utf-8')
        return urllib.parse.quote(b64_sig, safe='')

    def _sm4_encrypt(self, plaintext: str) -> str:
        if not HAS_GMSSL:
            raise Exception("请安装 gmssl-python: pip install gmssl-python")
        crypt_sm4 = CryptSM4()
        key = self.sm4_key.encode('utf-8')
        if len(key) != 16:
            raise Exception("SM4 密钥长度必须为 16 字节")
        crypt_sm4.set_key(key, SM4_ENCRYPT)
        plaintext_bytes = plaintext.encode('utf-8')
        block_size = 16
        padding_len = block_size - (len(plaintext_bytes) % block_size)
        plaintext_bytes += bytes([padding_len] * padding_len)
        encrypted = crypt_sm4.crypt_ecb(plaintext_bytes)
        return base64.b64encode(encrypted).decode('utf-8')

    def _sm4_decrypt(self, ciphertext: str) -> str:
        if not HAS_GMSSL:
            raise Exception("请安装 gmssl-python: pip install gmssl-python")
        crypt_sm4 = CryptSM4()
        key = self.sm4_key.encode('utf-8')
        if len(key) != 16:
            raise Exception("SM4 密钥长度必须为 16 字节")
        crypt_sm4.set_key(key, SM4_DECRYPT)
        encrypted = base64.b64decode(ciphertext)
        decrypted = crypt_sm4.crypt_ecb(encrypted)
        padding_len = decrypted[-1]
        return decrypted[:-padding_len].decode('utf-8')

    def _rsa_encrypt(self, plaintext: str) -> str:
        if not HAS_CRYPTO:
            raise Exception("请安装 pycryptodome: pip install pycryptodome")
        try:
            public_key = RSA.import_key(self.rsa_public_key)
            cipher = PKCS1_OAEP.new(public_key, hashAlgo=SHA256)
            encoded_data = base64.b64encode(plaintext.encode('utf-8')).decode('utf-8')
            encrypted = cipher.encrypt(encoded_data.encode('utf-8'))
            return base64.b64encode(encrypted).decode('utf-8')
        except Exception as e:
            raise Exception(f"RSA 加密失败: {str(e)}")

    def _rsa_decrypt(self, ciphertext: str) -> str:
        raise Exception("客户端 RSA 解密需要私钥，当前版本暂不支持")

    def run(self):
        try:
            url = f"{self.base_url}/{self.uri}"
            timestamp = int(time.time() * 1000)
            request_body = {"data": self.data, "timestamp": timestamp}
            sign = self._generate_sign(timestamp)
            if sign:
                request_body["sign"] = sign
            json_str = json.dumps(request_body, ensure_ascii=False)

            headers = {"User-Agent": "SmsForwarder-Windows-Client/1.0"}
            response = None

            if self.encryption_mode == EncryptionMode.SM4:
                if not self.sm4_key:
                    self.error.emit("请配置 SM4 密钥")
                    return
                headers["Content-Type"] = "text/plain"
                encrypted_body = self._sm4_encrypt(json_str)
                response = requests.post(url, data=encrypted_body, headers=headers, timeout=30)
                if response.status_code == 200:
                    decrypted = self._sm4_decrypt(response.text)
                    result = json.loads(decrypted)
                    self.finished.emit(result)
                else:
                    self.error.emit(f"HTTP 错误: {response.status_code} - {response.text[:100]}")

            elif self.encryption_mode == EncryptionMode.RSA:
                if not self.rsa_public_key:
                    self.error.emit("请配置 RSA 公钥")
                    return
                headers["Content-Type"] = "text/plain"
                encrypted_body = self._rsa_encrypt(json_str)
                response = requests.post(url, data=encrypted_body, headers=headers, timeout=30)
                if response.status_code == 200:
                    try:
                        result = response.json()
                    except:
                        self.error.emit("RSA 模式下响应解析失败")
                        return
                    self.finished.emit(result)
                else:
                    self.error.emit(f"HTTP 错误: {response.status_code} - {response.text[:100]}")

            else:
                headers["Content-Type"] = "application/json"
                response = requests.post(url, json=request_body, headers=headers, timeout=30)
                if response.status_code == 200:
                    self.finished.emit(response.json())
                else:
                    self.error.emit(f"HTTP 错误: {response.status_code} - {response.text[:100]}")

        except requests.exceptions.ConnectionError as e:
            err_msg = str(e.reason) if hasattr(e, 'reason') else str(e)
            if "NameResolutionError" in err_msg or "nodename nor servname" in err_msg:
                self.error.emit("地址解析失败：请检查服务器地址是否正确 (支持 IPv6)")
            elif "Connection refused" in err_msg:
                self.error.emit("连接被拒绝：请检查服务器IP、端口及服务是否已启动")
            else:
                self.error.emit(f"网络连接异常: {err_msg}")
        except requests.exceptions.Timeout:
            self.error.emit("请求超时：网络不通或服务器响应过慢")
        except requests.exceptions.SSLError:
            self.error.emit("SSL 证书错误：请检查是否为 HTTPS 且证书有效")
        except Exception as e:
            self.error.emit(f"未知错误: {str(e)}")


class SmsHubWorker(QThread):
    log_signal = pyqtSignal(str)

    def __init__(self, url: str, interval: int):
        super().__init__()
        self.url = url.rstrip('/')
        self.interval = interval
        self._running = True

    def stop(self):
        self._running = False

    def run(self):
        while self._running:
            try:
                response = requests.post(f"{self.url}/heartbeat", json={}, timeout=10)
                if response.status_code == 200:
                    commands = response.json()
                    if isinstance(commands, list):
                        for cmd in commands:
                            self.process_command(cmd)
                time.sleep(self.interval)
            except Exception as e:
                self.log_signal.emit(f"SmsHub 轮询错误: {str(e)}")
                time.sleep(self.interval)

    def process_command(self, cmd):
        action = cmd.get("action")
        if action == "0":
            target = cmd.get("target", "")
            content = cmd.get("content", "")
            channel = cmd.get("channel", "1")
            self.log_signal.emit(f"执行远程指令: 发短信给 {target} [{channel}]")


class SettingsDialog(QDialog):
    def __init__(self, parent=None, is_first_run=False):
        super().__init__(parent)
        self.is_first_run = is_first_run
        self.setWindowTitle("⚙️ 首选项" + (" - 首次配置" if is_first_run else ""))
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        if is_first_run:
            welcome_label = QLabel(
                "👋 欢迎使用 SmsForwarder Windows Client！\n"
                "请先配置服务器连接信息以开始使用。"
            )
            welcome_label.setStyleSheet("""
                background-color: #dbeafe;
                color: #1e40af;
                padding: 12px;
                border-radius: 8px;
                font-size: 13px;
            """)
            welcome_label.setWordWrap(True)
            layout.addWidget(welcome_label)

        server_group = QGroupBox("🔗 服务器配置")
        form = QFormLayout()
        form.setSpacing(10)

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("http://127.0.0.1:7001")
        form.addRow("服务器地址:", self.url_input)

        token_layout = QHBoxLayout()
        self.token_input = QLineEdit()
        self.token_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.token_input.setPlaceholderText("手机端设置的 API Token")
        token_layout.addWidget(self.token_input)
        toggle_btn = QToolButton()
        toggle_btn.setText("👁️")
        toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        toggle_btn.clicked.connect(lambda: self.toggle_visibility(self.token_input))
        token_layout.addWidget(toggle_btn)
        form.addRow("API Token:", token_layout)

        self.encrypt_combo = QComboBox()
        for mode in EncryptionMode:
            self.encrypt_combo.addItem(mode.value, mode)
        form.addRow("加密方式:", self.encrypt_combo)

        self.sm4_key_input = QLineEdit()
        self.sm4_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.sm4_key_input.setPlaceholderText("16字节密钥 (仅SM4模式需要)")
        sm4_layout = QHBoxLayout()
        sm4_layout.addWidget(self.sm4_key_input)
        sm4_toggle = QToolButton()
        sm4_toggle.setText("👁️")
        sm4_toggle.clicked.connect(lambda: self.toggle_visibility(self.sm4_key_input))
        sm4_layout.addWidget(sm4_toggle)
        form.addRow("SM4 密钥:", sm4_layout)

        self.rsa_pubkey_input = QTextEdit()
        self.rsa_pubkey_input.setMaximumHeight(80)
        self.rsa_pubkey_input.setPlaceholderText("-----BEGIN PUBLIC KEY-----\n...\n-----END PUBLIC KEY-----")
        form.addRow("RSA 公钥:", self.rsa_pubkey_input)

        server_group.setLayout(form)
        layout.addWidget(server_group)

        notify_group = QGroupBox("🔔 通知设置")
        notify_layout = QFormLayout()
        notify_layout.setSpacing(10)
        self.notify_enabled = QCheckBox("启用新消息托盘通知")
        notify_layout.addRow("", self.notify_enabled)
        poll_layout = QHBoxLayout()
        self.poll_interval_spin = QSpinBox()
        self.poll_interval_spin.setRange(APP_CONFIG["min_poll_interval"], APP_CONFIG["max_poll_interval"])
        self.poll_interval_spin.setSuffix(" 秒")
        poll_layout.addWidget(self.poll_interval_spin)
        poll_layout.addWidget(QLabel("(建议: 10-30秒)"))
        poll_layout.addStretch()
        notify_layout.addRow("轮询间隔:", poll_layout)
        self.close_to_tray = QCheckBox("关闭窗口时最小化到托盘")
        notify_layout.addRow("", self.close_to_tray)
        self.esc_to_tray = QCheckBox("按 ESC 键最小化到托盘")
        notify_layout.addRow("", self.esc_to_tray)
        notify_group.setLayout(notify_layout)
        layout.addWidget(notify_group)

        btn_layout = QHBoxLayout()
        self.test_conn_btn = QPushButton("🔗 测试连接")
        self.test_conn_btn.setObjectName("primaryBtn")
        self.test_conn_btn.clicked.connect(self.test_connection)
        btn_layout.addWidget(self.test_conn_btn)
        btn_layout.addStretch()

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("✅ 保存")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("❌ 取消")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        btn_layout.addWidget(buttons)
        layout.addLayout(btn_layout)

        self.load_settings()
        self.encrypt_combo.currentIndexChanged.connect(self.on_encrypt_changed)

    def toggle_visibility(self, widget):
        if widget.echoMode() == QLineEdit.EchoMode.Password:
            widget.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            widget.setEchoMode(QLineEdit.EchoMode.Password)

    def on_encrypt_changed(self, index):
        mode = self.encrypt_combo.currentData()
        self.sm4_key_input.setEnabled(mode == EncryptionMode.SM4)
        self.rsa_pubkey_input.setEnabled(mode == EncryptionMode.RSA)

    def test_connection(self):
        base_url = self.url_input.text().strip()
        if not base_url:
            QMessageBox.warning(self, "警告", "请先填写服务器地址")
            return
        mode = self.encrypt_combo.currentData()
        token = self.token_input.text().strip()
        sm4_key = self.sm4_key_input.text().strip()
        rsa_key = self.rsa_pubkey_input.toPlainText().strip()

        try:
            worker = APIWorker(base_url, mode, token, sm4_key, rsa_key)
            worker.set_request("config/query", {})

            def on_success(result):
                if result.get("code") == 200:
                    QMessageBox.information(self, "成功", "✅ 连接测试成功！")
                else:
                    QMessageBox.warning(self, "失败", f"服务器返回错误: {result.get('msg')}")

            def on_error(e):
                QMessageBox.critical(self, "连接失败", str(e))

            worker.finished.connect(on_success)
            worker.error.connect(on_error)
            worker.start()
            self._test_worker = worker
        except Exception as e:
            QMessageBox.critical(self, "错误", f"创建测试请求失败: {str(e)}")

    def load_settings(self):
        settings = QSettings("settings.ini", QSettings.Format.IniFormat)
        self.url_input.setText(settings.value("server_url", ""))
        self.token_input.setText(settings.value("api_token", ""))
        self.sm4_key_input.setText(settings.value("sm4_key", ""))
        self.rsa_pubkey_input.setText(settings.value("rsa_public_key", ""))
        encrypt_idx = settings.value("encrypt_index", 0, type=int)
        if encrypt_idx < self.encrypt_combo.count():
            self.encrypt_combo.setCurrentIndex(encrypt_idx)
        self.notify_enabled.setChecked(settings.value("notify_enabled", False, type=bool))
        self.poll_interval_spin.setValue(settings.value("poll_interval", 30, type=int))
        self.close_to_tray.setChecked(settings.value("close_to_tray", True, type=bool))
        self.esc_to_tray.setChecked(settings.value("esc_to_tray", True, type=bool))

    def save_settings(self):
        settings = QSettings("settings.ini", QSettings.Format.IniFormat)
        settings.setValue("server_url", self.url_input.text().strip())
        settings.setValue("api_token", self.token_input.text().strip())
        settings.setValue("sm4_key", self.sm4_key_input.text().strip())
        settings.setValue("rsa_public_key", self.rsa_pubkey_input.toPlainText().strip())
        settings.setValue("encrypt_index", self.encrypt_combo.currentIndex())
        settings.setValue("notify_enabled", self.notify_enabled.isChecked())
        settings.setValue("poll_interval", self.poll_interval_spin.value())
        settings.setValue("close_to_tray", self.close_to_tray.isChecked())
        settings.setValue("esc_to_tray", self.esc_to_tray.isChecked())

    def accept(self):
        self.save_settings()
        if hasattr(self.parent(), '_close_to_tray_setting'):
            self.parent()._close_to_tray_setting = self.close_to_tray.isChecked()
        if hasattr(self.parent(), '_esc_to_tray_setting'):
            self.parent()._esc_to_tray_setting = self.esc_to_tray.isChecked()
        super().accept()


class LogDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📋 运行日志")
        self.setMinimumSize(800, 600)
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(12, 12, 12, 12)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1f2937;
                color: #e5e7eb;
                font-family: monospace;
                font-size: 12px;
                border-radius: 6px;
                padding: 8px;
            }
        """)
        layout.addWidget(self.log_text)

        btn_layout = QHBoxLayout()
        clear_btn = QPushButton("🗑️ 清空日志")
        clear_btn.clicked.connect(self.log_text.clear)
        btn_layout.addWidget(clear_btn)
        btn_layout.addStretch()
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.close)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)


class SmsForwarderClient(QMainWindow):
    def __init__(self):
        super().__init__()
        self.worker = None
        self.tray_icon = None
        self.notify_timer = None
        self.last_sms_timestamp = 0
        self.last_tray_msg_type = None
        self._polling_new_messages = False
        self._close_to_tray_setting = True
        self._esc_to_tray_setting = True
        self._tray_blink_timer = None
        self._is_first_poll = True
        self._workers = set()

        self.url_input = QLineEdit()
        self.token_input = QLineEdit()
        self.sm4_key_input = QLineEdit()
        self.rsa_pubkey_input = QTextEdit()
        self.encrypt_combo = QComboBox()
        for mode in EncryptionMode:
            self.encrypt_combo.addItem(mode.value, mode)

        self.app_icon = self._load_icon_from_base64()

        try:
            self.init_ui()
            self.log_message("UI initialized")
            self.init_timer()
            self.load_settings()

            if not self.url_input.text().strip():
                QTimer.singleShot(500, self.show_first_run_dialog)

            QTimer.singleShot(100, self._delayed_show)
        except Exception as e:
            print(f"Init Error: {e}")

    def _load_icon_from_base64(self):
        if not ICON_BASE64:
            return QIcon()
        try:
            clean_b64 = ICON_BASE64
            if "," in clean_b64:
                clean_b64 = clean_b64.split(",", 1)[1]
            icon_data = QByteArray.fromBase64(clean_b64.encode('utf-8'))
            pixmap = QPixmap()
            if pixmap.loadFromData(icon_data):
                return QIcon(pixmap)
        except Exception:
            pass
        return QIcon()

    def _delayed_show(self):
        try:
            self.show()
            self.activateWindow()
            QTimer.singleShot(1500, self._safe_init_tray)
            QTimer.singleShot(500, self._safe_start_notify_timer)
            QTimer.singleShot(1200, self._initial_full_refresh)
        except Exception as e:
            print(f"Show error: {e}")

    def _initial_full_refresh(self):
        try:
            notify_was_enabled = self.notify_enabled.isChecked()
            self.notify_enabled.blockSignals(True)
            self.notify_enabled.setChecked(False)

            if hasattr(self, 'sms_query_btn'):
                self.query_sms()
            if hasattr(self, 'call_query_btn'):
                self.query_calls()
            if hasattr(self, 'contact_query_btn'):
                self.query_contacts()

            if hasattr(self, 'battery_info_text'):
                self.query_battery_to_card(self.battery_info_text, silent=True)
            if hasattr(self, 'location_info_text'):
                self.query_location_to_card(self.location_info_text, silent=True)
            if hasattr(self, 'config_info_text'):
                self.query_config_to_card(self.config_info_text, silent=True)

            self.notify_enabled.blockSignals(False)
            self.notify_enabled.setChecked(notify_was_enabled)
        except Exception:
            pass

    def _safe_init_tray(self):
        try:
            self.init_tray()
            self.log_message("Tray initialized")
        except Exception as e:
            self.log_message(f"Tray init failed: {e}")
            self.tray_icon = None

    def init_tray(self):
        if not QSystemTrayIcon.isSystemTrayAvailable():
            self.log_message("System tray not available")
            self.tray_icon = None
            return

        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.app_icon if not self.app_icon.isNull() else self.style().standardIcon(
            QStyle.StandardPixmap.SP_ComputerIcon))
        self.tray_icon.setToolTip(APP_CONFIG["app_name"])

        tray_menu = QMenu()
        show_action = QAction("📱 显示主窗口", self)
        show_action.triggered.connect(self.show_normal)
        tray_menu.addAction(show_action)
        tray_menu.addSeparator()

        sms_action = QAction("📨 短信记录", self)
        sms_action.triggered.connect(lambda: self._jump_to_tab(0))
        tray_menu.addAction(sms_action)
        call_action = QAction("📞 通话记录", self)
        call_action.triggered.connect(lambda: self._jump_to_tab(1))
        tray_menu.addAction(call_action)
        contact_action = QAction("👥 联系人", self)
        contact_action.triggered.connect(lambda: self._jump_to_tab(2))
        tray_menu.addAction(contact_action)
        send_action = QAction("✉️ 发送短信", self)
        send_action.triggered.connect(lambda: self._jump_to_tab(3))
        tray_menu.addAction(send_action)
        device_action = QAction("📱 设备信息", self)
        device_action.triggered.connect(lambda: self._jump_to_tab(4))
        tray_menu.addAction(device_action)
        smshub_action = QAction("🌐 SmsHub", self)
        smshub_action.triggered.connect(lambda: self._jump_to_tab(5))
        tray_menu.addAction(smshub_action)
        tray_menu.addSeparator()

        refresh_action = QAction("🔄 刷新当前页面", self)
        refresh_action.triggered.connect(self.refresh_current_tab)
        tray_menu.addAction(refresh_action)
        tray_menu.addSeparator()

        quit_action = QAction("❌ 退出程序", self)
        quit_action.triggered.connect(self.quit_app)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.on_tray_activated)
        self.tray_icon.messageClicked.connect(self.on_tray_message_clicked)
        self.tray_icon.show()
        self.log_message("Tray icon shown")

    def init_ui(self):
        self.setWindowTitle(APP_CONFIG["app_name"])
        self.setMinimumSize(APP_CONFIG["window_width"], APP_CONFIG["window_height"])
        if not self.app_icon.isNull():
            self.setWindowIcon(self.app_icon)

        font = QFont("", 9)
        self.setFont(font)

        self.setStyleSheet("""
        QMainWindow { background-color: #f0f2f5; }
        QGroupBox {
            font-weight: bold;
            color: #1f2937;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            margin-top: 16px;
            padding-top: 20px;
            background-color: white;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 12px;
            padding: 0 6px;
            color: #374151;
        }
        QPushButton {
            background-color: #3b82f6;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            font-weight: 600;
            min-width: 80px;
        }
        QPushButton:hover { background-color: #2563eb; }
        QPushButton:pressed { background-color: #1d4ed8; }
        QPushButton#primaryBtn { background-color: #10b981; }
        QPushButton#primaryBtn:hover { background-color: #059669; }
        QPushButton#dangerBtn { background-color: #ef4444; }
        QPushButton#dangerBtn:hover { background-color: #dc2626; }
        QLineEdit, QSpinBox, QComboBox {
            border: 1px solid #d1d5db;
            border-radius: 6px;
            padding: 6px 10px;
            background-color: white;
        }
        QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
            border: 1px solid #3b82f6;
        }
        QTextEdit {
            border: 1px solid #d1d5db;
            border-radius: 6px;
            padding: 8px;
            background-color: white;
        }
        QTableWidget {
            border: 1px solid #e5e7eb;
            gridline-color: #f3f4f6;
            background-color: white;
            alternate-background-color: #f9fafb;
            border-radius: 6px;
        }
        QHeaderView::section {
            background-color: #f3f4f6;
            color: #4b5563;
            padding: 8px;
            border: none;
            border-bottom: 2px solid #e5e7eb;
            font-weight: bold;
        }
        QTabWidget::pane {
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            background-color: white;
        }
        QTabBar::tab {
            background-color: #f3f4f6;
            color: #6b7280;
            padding: 8px 16px;
            margin-right: 2px;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
        }
        QTabBar::tab:selected {
            background-color: white;
            color: #3b82f6;
            border-bottom: 2px solid #3b82f6;
        }
        QMenuBar {
            background-color: white;
            border-bottom: 1px solid #e5e7eb;
        }
        QMenu {
            background-color: white;
            border: 1px solid #e5e7eb;
            border-radius: 6px;
        }
        """)

        menubar = self.menuBar()
        file_menu = menubar.addMenu("文件")
        action_exit = QAction("退出", self)
        action_exit.triggered.connect(self.quit_app)
        file_menu.addAction(action_exit)

        view_menu = menubar.addMenu("视图")
        self.view_actions = {}
        action_sms = QAction("📨 短信记录", self, checkable=True)
        action_sms.setChecked(True)
        action_sms.triggered.connect(lambda checked: self._toggle_view_action(0, checked))
        view_menu.addAction(action_sms)
        self.view_actions['sms'] = {'action': action_sms, 'index': 0}

        action_call = QAction("📞 通话记录", self, checkable=True)
        action_call.setChecked(True)
        action_call.triggered.connect(lambda checked: self._toggle_view_action(1, checked))
        view_menu.addAction(action_call)
        self.view_actions['call'] = {'action': action_call, 'index': 1}

        action_contact = QAction("👥 联系人", self, checkable=True)
        action_contact.setChecked(True)
        action_contact.triggered.connect(lambda checked: self._toggle_view_action(2, checked))
        view_menu.addAction(action_contact)
        self.view_actions['contact'] = {'action': action_contact, 'index': 2}

        action_send = QAction("✉️ 发送短信", self, checkable=True)
        action_send.setChecked(True)
        action_send.triggered.connect(lambda checked: self._toggle_view_action(3, checked))
        view_menu.addAction(action_send)
        self.view_actions['send'] = {'action': action_send, 'index': 3}

        action_device = QAction("📱 设备信息", self, checkable=True)
        action_device.setChecked(True)
        action_device.triggered.connect(lambda checked: self._toggle_view_action(4, checked))
        view_menu.addAction(action_device)
        self.view_actions['device'] = {'action': action_device, 'index': 4}

        action_smshub = QAction("🌐 SmsHub", self, checkable=True)
        action_smshub.setChecked(True)
        action_smshub.triggered.connect(lambda checked: self._toggle_view_action(5, checked))
        view_menu.addAction(action_smshub)
        self.view_actions['smshub'] = {'action': action_smshub, 'index': 5}

        view_menu.addSeparator()
        action_configure_view = QAction("⚙️ 配置视图菜单...", self)
        action_configure_view.triggered.connect(self.configure_view_menu)
        view_menu.addAction(action_configure_view)

        tools_menu = menubar.addMenu("工具")
        action_refresh = QAction("刷新当前页面", self)
        action_refresh.setShortcut("F5")
        action_refresh.triggered.connect(self.refresh_current_tab)
        tools_menu.addAction(action_refresh)

        export_menu = menubar.addMenu("导出")
        action_export_sms = QAction("导出短信", self)
        action_export_sms.triggered.connect(lambda: self.export_table_to_csv(self.sms_table, "sms_export.csv"))
        export_menu.addAction(action_export_sms)
        action_export_calls = QAction("导出通话记录", self)
        action_export_calls.triggered.connect(lambda: self.export_table_to_csv(self.call_table, "calls_export.csv"))
        export_menu.addAction(action_export_calls)
        action_export_contacts = QAction("导出联系人", self)
        action_export_contacts.triggered.connect(
            lambda: self.export_table_to_csv(self.contact_table, "contacts_export.csv"))
        export_menu.addAction(action_export_contacts)

        settings_menu = menubar.addMenu("设置")
        action_preferences = QAction("⚙️ 首选项", self)
        action_preferences.setShortcut("Ctrl+,")
        action_preferences.triggered.connect(self.open_settings_dialog)
        settings_menu.addAction(action_preferences)
        action_logs = QAction("📋 查看日志", self)
        action_logs.setShortcut("Ctrl+L")
        action_logs.triggered.connect(self.show_log_dialog)
        settings_menu.addAction(action_logs)

        help_menu = menubar.addMenu("帮助")
        action_about = QAction("关于", self)
        action_about.triggered.connect(self.show_about)
        help_menu.addAction(action_about)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(12, 12, 12, 12)

        self.tab_widget = QTabWidget()
        self.sms_tab = self.create_sms_tab()
        self.call_tab = self.create_call_tab()
        self.contact_tab = self.create_contact_tab()
        self.send_tab = self.create_send_tab()
        self.device_tab = self.create_device_tab()
        self.tab_widget.addTab(self.sms_tab, "📨 短信")
        self.tab_widget.addTab(self.call_tab, "📞 通话")
        self.tab_widget.addTab(self.contact_tab, "👥 联系人")
        self.tab_widget.addTab(self.send_tab, "✉️ 发送")
        self.tab_widget.addTab(self.device_tab, "📱 设备")
        self.smshub_tab = self.create_smshub_tab()
        self.tab_widget.addTab(self.smshub_tab, "🌐 SmsHub")
        main_layout.addWidget(self.tab_widget)

        self.status_bar = self.statusBar()
        self.connection_status_label = QLabel("🟡 检查中...")
        self.connection_status_label.setStyleSheet("""
            QLabel {
                padding: 2px 8px;
                border-radius: 3px;
                background-color: #fef3c7;
                color: #92400e;
                font-weight: bold;
                font-size: 12px;
            }
        """)
        self.status_bar.addPermanentWidget(self.connection_status_label)
        self.status_bar.showMessage("✅ 就绪 | F5刷新 | Ctrl+, 设置")

        self.notify_enabled = QCheckBox("启用新消息通知")
        self.notify_enabled.toggled.connect(self.on_notify_toggled)
        self.notify_enabled.setVisible(False)
        self.poll_interval_spin = QSpinBox()
        self.poll_interval_spin.setRange(APP_CONFIG["min_poll_interval"], APP_CONFIG["max_poll_interval"])
        self.poll_interval_spin.setSuffix(" 秒")
        self.poll_interval_spin.valueChanged.connect(self.on_poll_interval_changed)
        self.poll_interval_spin.setVisible(False)

        self.log_dialog = None

    def init_timer(self):
        self.notify_timer = QTimer(self)
        self.notify_timer.timeout.connect(self.check_new_messages)
        self.connection_check_timer = QTimer(self)
        self.connection_check_timer.timeout.connect(self.check_connection_status)
        self.connection_check_timer.setInterval(30000)

    def log_message(self, msg):
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted = f"[{timestamp}] {msg}"
        print(formatted)
        if self.log_dialog and hasattr(self.log_dialog, 'log_text'):
            try:
                self.log_dialog.log_text.append(formatted)
            except Exception:
                pass

    def export_table_to_csv(self, table: QTableWidget, default_name: str = "export.csv"):
        if table.rowCount() == 0:
            QMessageBox.information(self, "导出", "没有可导出的数据")
            return
        path, _ = QFileDialog.getSaveFileName(self, "保存为 CSV", default_name, "CSV 文件 (*.csv)")
        if not path:
            return
        try:
            with open(path, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.writer(f)
                headers = [table.horizontalHeaderItem(c).text() if table.horizontalHeaderItem(c) else f"列{c}"
                           for c in range(table.columnCount())]
                writer.writerow(headers)
                for r in range(table.rowCount()):
                    row = [table.item(r, c).text() if table.item(r, c) else "" for c in range(table.columnCount())]
                    writer.writerow(row)
            QMessageBox.information(self, "导出", f"导出成功: {path}")
        except Exception as e:
            QMessageBox.critical(self, "导出失败", str(e))

    def show_log_dialog(self):
        if self.log_dialog is None:
            self.log_dialog = LogDialog(self)
        self.log_dialog.show()
        self.log_dialog.raise_()

    def open_settings_dialog(self):
        dlg = SettingsDialog(self, is_first_run=False)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.load_settings()
            QMessageBox.information(self, "设置", "✅ 设置已保存")

    def show_first_run_dialog(self):
        dlg = SettingsDialog(self, is_first_run=True)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.load_settings()
            QMessageBox.information(self, "欢迎使用", "🎉 配置完成！")

    def show_about(self):
        about_text = f"""
        <h2>{APP_CONFIG['app_name']}</h2>
        <p>版本: 2.1</p>
        <p>作者：www.52pojie.cn Cristy</p>
        <p>功能特点:</p>
        <ul>
            <li>✨ 现代化 Fluent UI 设计</li>
            <li>🔒 兼容官方/RSA/SM4 加密</li>
            <li>📊 数据导出为 CSV</li>
            <li>🔔 新消息托盘通知</li>
        </ul>
        <p>© 2026 Aura Service</p>
        """
        QMessageBox.about(self, "关于", about_text)

    def _jump_to_tab(self, index: int):
        self.show_normal()
        QTimer.singleShot(100, lambda: self.tab_widget.setCurrentIndex(index))

    def refresh_current_tab(self):
        idx = self.tab_widget.currentIndex()
        if idx == 0:
            self.query_sms()
        elif idx == 1:
            self.query_calls()
        elif idx == 2:
            self.query_contacts()
        elif idx == 4:
            if hasattr(self, 'battery_info_text'):
                self.query_battery_to_card(self.battery_info_text)
            if hasattr(self, 'location_info_text'):
                self.query_location_to_card(self.location_info_text)
            if hasattr(self, 'config_info_text'):
                self.query_config_to_card(self.config_info_text)

    def get_current_mode(self) -> EncryptionMode:
        return self.encrypt_combo.currentData()

    def create_worker(self, uri: str, data: Dict[str, Any]) -> APIWorker:
        base_url = self.url_input.text().strip()
        if not base_url:
            QMessageBox.warning(self, "警告", "请填写服务器地址")
            return None
        mode = self.get_current_mode()
        token = self.token_input.text().strip()
        sm4_key = self.sm4_key_input.text().strip()
        rsa_key = self.rsa_pubkey_input.toPlainText().strip()
        worker = APIWorker(base_url, mode, token, sm4_key, rsa_key)
        worker.set_request(uri, data)
        self._workers.add(worker)

        def cleanup(res=None):
            self._workers.discard(worker)
        worker.finished.connect(cleanup)
        worker.error.connect(lambda e: cleanup())
        return worker

    def execute_request(self, uri: str, data: Dict[str, Any],
                        on_success: callable, on_error: callable = None):
        worker = self.create_worker(uri, data)
        if not worker:
            return
        self.worker = worker
        worker.finished.connect(on_success)
        if on_error:
            worker.error.connect(on_error)
        else:
            worker.error.connect(lambda e: QMessageBox.critical(self, "错误", e))
        self.status_bar.showMessage(f"请求中: {uri}...")
        worker.start()

    def query_sms(self):
        def on_success(result):
            if result.get("code") == 200:
                data = result.get("data", [])
                # 更新时间戳
                if data:
                    latest_ts = max(sms.get("date", 0) for sms in data)
                    if latest_ts > self.last_sms_timestamp:
                        self.last_sms_timestamp = latest_ts
                # 使用公共方法更新表格
                self._update_sms_table(data)
                self.status_bar.showMessage(f"共 {len(data)} 条记录")
            else:
                QMessageBox.warning(self, "查询失败", result.get("msg", "未知错误"))

        data = {
            "type": self.sms_type_combo.currentData(),
            "page_num": self.sms_page_spin.value(),
            "page_size": self.sms_page_size_spin.value()
        }
        keyword = self.sms_keyword_input.text().strip()
        if keyword:
            data["keyword"] = keyword
        self.execute_request("sms/query", data, on_success)

    def _extract_verification_code(self, content: str) -> str:
        """从短信内容中提取验证码"""
        import re
        patterns = [
            r'验证码[：:是为]?\s*(\d{4,8})',
            r'验证码是[:：]?\s*(\d{4,8})',
            r'动态码[：:是为]?\s*(\d{4,8})',
            r'(?:code|CODE)[：:是为]?\s*(\d{4,8})',
            r'(\d{4,8})\s*(?:是|为|是你的|为你的|有效期|分钟)',
            r'随机[验证码动态码]*[：:是为]?\s*(\d{4,8})',
        ]
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1)
        return ""

    def _extract_candidate_codes(self, content: str) -> list:
        """提取所有可能的数字序列作为候选验证码"""
        import re
        # 提取所有4-8位数字序列
        candidate_pattern = r'(\d{4,8})'
        candidates = re.findall(candidate_pattern, content)
        # 去重并保持顺序
        seen = set()
        unique_candidates = []
        for code in candidates:
            if code not in seen:
                seen.add(code)
                unique_candidates.append(code)
        return unique_candidates

    def show_sms_detail(self):
        try:
            selected = self.sms_table.selectedItems()
            if not selected:
                return
            row = selected[0].row()
            if not hasattr(self, '_current_sms_data') or row >= len(self._current_sms_data):
                QMessageBox.warning(self, "提示", "无法获取短信详情")
                return
            sms = self._current_sms_data[row]

            dialog = QDialog(self)
            dialog.setWindowTitle("📨 短信详情")
            dialog.setMinimumWidth(550)
            dialog.setMinimumHeight(350)
            layout = QVBoxLayout(dialog)
            layout.setSpacing(12)
            layout.setContentsMargins(16, 16, 16, 16)

            date_str = datetime.fromtimestamp(sms.get("date", 0) / 1000).strftime("%Y-%m-%d %H:%M:%S")
            number = sms.get("number", "未知")
            name = sms.get("name", "未知")
            content = sms.get("content", "")
            sim_id = sms.get("sim_id", -1)
            sim_text = f"SIM{sim_id + 1}" if sim_id >= 0 else "未知"
            type_text = "接收" if sms.get("type", 1) == 1 else "发送"

            # 提取验证码
            verification_code = self._extract_verification_code(content)
            candidate_codes = self._extract_candidate_codes(content)
            # 如果没有精确验证码，但有候选验证码，使用第一个候选作为验证码
            if not verification_code and candidate_codes:
                verification_code = candidate_codes[0]

            verification_html = ""
            if verification_code:
                verification_html = f"""
                <div style="background-color: #fef3c7; border-left: 4px solid #f59e0b; border-radius: 6px; padding: 12px; margin-bottom: 12px;">
                    <div style="color: #92400e; font-weight: 600;">🔑 验证码</div>
                    <div style="font-size: 28px; font-weight: bold; color: #1f2937; letter-spacing: 4px; margin-top: 4px;">{verification_code}</div>
                </div>
                """

            # 构建候选数字显示区域（不太明显）
            candidate_html = ""
            if candidate_codes and len(candidate_codes) > 1:
                # 去掉已经作为验证码显示的第一个候选
                other_candidates = [code for code in candidate_codes if code != verification_code]
                if other_candidates:
                    candidate_items = ""
                    for code in other_candidates[:5]:  # 最多显示5个候选
                        candidate_items += f'<span style="background-color: #e5e7eb; padding: 2px 6px; border-radius: 3px; margin-right: 4px; font-size: 11px;">{code}</span>'
                    candidate_html = f"""
                    <div style="background-color: #f9fafb; border-left: 3px solid #d1d5db; border-radius: 4px; padding: 8px; margin-bottom: 12px; font-size: 12px; color: #6b7280;">
                        <div style="margin-bottom: 4px;">📋 其他数字序列:</div>
                        <div>{candidate_items}</div>
                    </div>
                    """

            detail_html = f"""
            <div style="padding: 8px;">
                <div style="background-color: #f9fafb; border-radius: 8px; padding: 16px; margin-bottom: 12px;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                        <span style="color: #6b7280;">类型:</span>
                        <span style="font-weight: 600;">{type_text}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                        <span style="color: #6b7280;">号码:</span>
                        <span style="font-weight: 600;">{number}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                        <span style="color: #6b7280;">姓名:</span>
                        <span style="font-weight: 600;">{name}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                        <span style="color: #6b7280;">卡槽:</span>
                        <span style="font-weight: 600;">{sim_text}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span style="color: #6b7280;">时间:</span>
                        <span style="font-weight: 600;">{date_str}</span>
                    </div>
                </div>
                {verification_html}
                {candidate_html}
                <div style="background-color: #eff6ff; border-left: 4px solid #3b82f6; border-radius: 6px; padding: 12px;">
                    <div style="color: #1e40af; font-weight: 600;">短信内容</div>
                    <div style="white-space: pre-wrap;">{content}</div>
                </div>
            </div>
            """
            detail_browser = QTextBrowser()
            detail_browser.setHtml(detail_html)
            detail_browser.setStyleSheet("border: none; background: transparent;")
            layout.addWidget(detail_browser)

            btn_layout = QHBoxLayout()
            copy_content_btn = QPushButton("📋 复制内容")
            # 对话框是否已关闭的标志
            dialog_closed = [False]
            def copy_content():
                QApplication.clipboard().setText(content)
                copy_content_btn.setText("✅ 已复制")
                def restore():
                    if not dialog_closed[0]:
                        copy_content_btn.setText("📋 复制内容")
                QTimer.singleShot(1500, restore)
            copy_content_btn.clicked.connect(copy_content)
            btn_layout.addWidget(copy_content_btn)
            
            if verification_code:
                copy_code_btn = QPushButton("🔑 复制验证码")
                copy_code_btn.setStyleSheet("background-color: #f59e0b; color: white;")
                def copy_code():
                    QApplication.clipboard().setText(verification_code)
                    copy_code_btn.setText("✅ 已复制")
                    def restore():
                        if not dialog_closed[0]:
                            copy_code_btn.setText("🔑 复制验证码")
                    QTimer.singleShot(1500, restore)
                copy_code_btn.clicked.connect(copy_code)
                btn_layout.addWidget(copy_code_btn)
            
            # 添加候选数字选择和复制功能
            if candidate_codes and len(candidate_codes) > 1:
                other_candidates = [code for code in candidate_codes if code != verification_code]
                if other_candidates:
                    # 创建候选数字下拉框
                    candidate_combo = QComboBox()
                    candidate_combo.addItems(other_candidates[:5])
                    candidate_combo.setMaximumWidth(120)
                    candidate_combo.setStyleSheet("QComboBox { padding: 4px; border: 1px solid #d1d5db; border-radius: 4px; font-size: 12px; }")
                    btn_layout.addWidget(QLabel("候选数字:"))
                    btn_layout.addWidget(candidate_combo)
                    
                    # 复制选中候选数字的按钮
                    copy_candidate_btn = QPushButton("复制")
                    copy_candidate_btn.setStyleSheet("background-color: #9ca3af; color: white; padding: 4px 8px;")
                    def copy_candidate():
                        selected = candidate_combo.currentText()
                        if selected:
                            QApplication.clipboard().setText(selected)
                            copy_candidate_btn.setText("✅")
                            def restore():
                                if not dialog_closed[0]:
                                    copy_candidate_btn.setText("复制")
                            QTimer.singleShot(1500, restore)
                    copy_candidate_btn.clicked.connect(copy_candidate)
                    btn_layout.addWidget(copy_candidate_btn)
            
            btn_layout.addStretch()
            close_btn = QPushButton("关闭")
            close_btn.clicked.connect(dialog.close)
            btn_layout.addWidget(close_btn)
            layout.addLayout(btn_layout)
            
            # 对话框关闭时设置标志
            def on_dialog_closed():
                dialog_closed[0] = True
            dialog.finished.connect(on_dialog_closed)
            
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"显示短信详情时发生错误: {str(e)}")
            self.log_message(f"显示短信详情错误: {str(e)}")

    def query_calls(self):
        def on_success(result):
            if result.get("code") == 200:
                data = result.get("data", [])
                self.call_table.setRowCount(len(data))
                for row, call in enumerate(data):
                    date_str = datetime.fromtimestamp(call.get("dateLong", 0) / 1000).strftime("%Y-%m-%d %H:%M:%S")
                    self.call_table.setItem(row, 0, QTableWidgetItem(date_str))
                    self.call_table.setItem(row, 1, QTableWidgetItem(call.get("number", "")))
                    type_map = {1: "呼入", 2: "呼出", 3: "未接"}
                    self.call_table.setItem(row, 2, QTableWidgetItem(type_map.get(call.get("type", 0), "未知")))
                    self.call_table.setItem(row, 3, QTableWidgetItem(str(call.get("duration", 0))))
                    sim_id = call.get("sim_id", -1)
                    sim_text = f"SIM{sim_id + 1}" if sim_id >= 0 else "未知"
                    self.call_table.setItem(row, 4, QTableWidgetItem(sim_text))
                self.status_bar.showMessage(f"共 {len(data)} 条记录")
            else:
                QMessageBox.warning(self, "查询失败", result.get("msg", "未知错误"))

        data = {
            "type": self.call_type_combo.currentData(),
            "page_num": self.call_page_spin.value(),
            "page_size": 50
        }
        phone = self.call_phone_input.text().strip()
        if phone:
            data["phone_number"] = phone
        self.execute_request("call/query", data, on_success)

    def query_contacts(self):
        def on_success(result):
            if result.get("code") == 200:
                data = result.get("data", [])
                self.contact_table.setRowCount(len(data))
                for row, contact in enumerate(data):
                    self.contact_table.setItem(row, 0, QTableWidgetItem(contact.get("name", "")))
                    self.contact_table.setItem(row, 1, QTableWidgetItem(contact.get("phone_number", "")))
                self.status_bar.showMessage(f"共 {len(data)} 条记录")
            else:
                QMessageBox.warning(self, "查询失败", result.get("msg", "未知错误"))

        data = {}
        name = self.contact_name_input.text().strip()
        if name:
            data["name"] = name
        phone = self.contact_phone_input.text().strip()
        if phone:
            data["phone_number"] = phone
        self.execute_request("contact/query", data, on_success)

    def add_contact(self):
        name = self.add_contact_name.text().strip()
        phone = self.add_contact_phone.text().strip()
        if not phone:
            QMessageBox.warning(self, "警告", "请填写号码")
            return

        def on_success(result):
            if result.get("code") == 200:
                QMessageBox.information(self, "成功", "联系人添加成功")
                self.add_contact_name.clear()
                self.add_contact_phone.clear()
                self.query_contacts()
            else:
                QMessageBox.warning(self, "添加失败", result.get("msg", "未知错误"))

        data = {"phone_number": phone}
        if name:
            data["name"] = name
        self.execute_request("contact/add", data, on_success)

    def send_sms(self):
        sim_slot = self.send_sim_combo.currentData()
        phone_numbers = self.send_phone_input.text().strip()
        msg_content = self.send_content_edit.toPlainText().strip()
        if not phone_numbers or not msg_content:
            QMessageBox.warning(self, "警告", "请填写接收号码和短信内容")
            return

        def on_success(result):
            if result.get("code") == 200:
                QMessageBox.information(self, "成功", "短信发送成功")
                self.send_phone_input.clear()
                self.send_content_edit.clear()
            else:
                QMessageBox.warning(self, "发送失败", result.get("msg", "未知错误"))

        data = {"sim_slot": sim_slot, "phone_numbers": phone_numbers, "msg_content": msg_content}
        self.execute_request("sms/send", data, on_success)

    def query_battery_to_card(self, info_label: QLabel, silent: bool = False):
        def on_success(result):
            if result.get("code") == 200:
                self._render_battery_card(info_label, result.get("data", {}))
            elif not silent:
                info_label.setText(f"❌ 查询失败: {result.get('msg', '未知错误')}")

        def on_error(e):
            if not silent:
                info_label.setText(f"❌ 网络错误: {str(e)}")

        self.execute_request("battery/query", {}, on_success, on_error)

    def query_location_to_card(self, info_label: QLabel, silent: bool = False):
        def on_success(result):
            if result.get("code") == 200:
                self._render_location_card(info_label, result.get("data", {}))
            elif not silent:
                info_label.setText(f"❌ 查询失败: {result.get('msg', '未知错误')}")

        def on_error(e):
            if not silent:
                info_label.setText(f"❌ 网络错误: {str(e)}")

        self.execute_request("location/query", {}, on_success, on_error)

    def query_config_to_card(self, info_label: QLabel, silent: bool = False):
        def on_success(result):
            if result.get("code") == 200:
                self._render_config_card(info_label, result.get("data", {}))
            elif not silent:
                info_label.setText(f"❌ 查询失败: {result.get('msg', '未知错误')}")

        def on_error(e):
            if not silent:
                info_label.setText(f"❌ 网络错误: {str(e)}")

        self.execute_request("config/query", {}, on_success, on_error)

    def send_wol(self):
        mac = self.wol_mac_input.text().strip()
        ip = self.wol_ip_input.text().strip()
        if not mac:
            QMessageBox.warning(self, "警告", "请输入 MAC 地址")
            return

        def on_success(result):
            if result.get("code") == 200:
                QMessageBox.information(self, "成功", "WOL 指令已发送")
            else:
                QMessageBox.warning(self, "失败", result.get("msg", "未知错误"))

        data = {"mac": mac}
        if ip:
            data["ip"] = ip
        self.execute_request("wol/send", data, on_success)

    def create_sms_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(8)

        filter_card = QGroupBox("🔍 筛选条件")
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("类型:"))
        self.sms_type_combo = QComboBox()
        self.sms_type_combo.addItem("接收", 1)
        self.sms_type_combo.addItem("发送", 2)
        self.sms_type_combo.setMaximumWidth(100)
        filter_layout.addWidget(self.sms_type_combo)

        filter_layout.addWidget(QLabel("关键字:"))
        self.sms_keyword_input = QLineEdit()
        self.sms_keyword_input.setPlaceholderText("搜索号码/内容...")
        self.sms_keyword_input.setMaximumWidth(200)
        filter_layout.addWidget(self.sms_keyword_input)

        filter_layout.addWidget(QLabel("页码:"))
        self.sms_page_spin = QSpinBox()
        self.sms_page_spin.setMinimum(1)
        self.sms_page_spin.setValue(1)
        self.sms_page_spin.setMaximumWidth(60)
        filter_layout.addWidget(self.sms_page_spin)

        filter_layout.addWidget(QLabel("每页:"))
        self.sms_page_size_spin = QSpinBox()
        self.sms_page_size_spin.setMinimum(1)
        self.sms_page_size_spin.setMaximum(100)
        self.sms_page_size_spin.setValue(20)
        self.sms_page_size_spin.setMaximumWidth(70)
        filter_layout.addWidget(self.sms_page_size_spin)

        self.sms_query_btn = QPushButton("🔍 查询")
        self.sms_query_btn.setObjectName("primaryBtn")
        self.sms_query_btn.clicked.connect(self.query_sms)
        filter_layout.addWidget(self.sms_query_btn)

        self.sms_export_btn = QPushButton("📊 导出")
        self.sms_export_btn.clicked.connect(
            lambda: self.export_table_to_csv(self.sms_table, "sms_export.csv"))
        filter_layout.addWidget(self.sms_export_btn)
        filter_layout.addStretch()
        filter_card.setLayout(filter_layout)
        layout.addWidget(filter_card)

        self.sms_table = QTableWidget()
        self.sms_table.setColumnCount(5)
        self.sms_table.setHorizontalHeaderLabels(["⏰ 时间", "📱 号码", "👤 姓名", "💬 内容", "📡 卡槽"])
        self.sms_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.sms_table.setAlternatingRowColors(True)
        self.sms_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.sms_table.doubleClicked.connect(self.show_sms_detail)
        layout.addWidget(self.sms_table)
        return tab

    def create_call_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(8)

        filter_card = QGroupBox("🔍 筛选条件")
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("类型:"))
        self.call_type_combo = QComboBox()
        self.call_type_combo.addItem("全部", 0)
        self.call_type_combo.addItem("呼入", 1)
        self.call_type_combo.addItem("呼出", 2)
        self.call_type_combo.addItem("未接", 3)
        self.call_type_combo.setMaximumWidth(100)
        filter_layout.addWidget(self.call_type_combo)

        filter_layout.addWidget(QLabel("号码:"))
        self.call_phone_input = QLineEdit()
        self.call_phone_input.setPlaceholderText("搜索号码...")
        self.call_phone_input.setMaximumWidth(200)
        filter_layout.addWidget(self.call_phone_input)

        filter_layout.addWidget(QLabel("页码:"))
        self.call_page_spin = QSpinBox()
        self.call_page_spin.setMinimum(1)
        self.call_page_spin.setValue(1)
        self.call_page_spin.setMaximumWidth(60)
        filter_layout.addWidget(self.call_page_spin)

        self.call_query_btn = QPushButton("🔍 查询")
        self.call_query_btn.setObjectName("primaryBtn")
        self.call_query_btn.clicked.connect(self.query_calls)
        filter_layout.addWidget(self.call_query_btn)

        self.call_export_btn = QPushButton("📊 导出")
        self.call_export_btn.clicked.connect(
            lambda: self.export_table_to_csv(self.call_table, "calls_export.csv"))
        filter_layout.addWidget(self.call_export_btn)
        filter_layout.addStretch()
        filter_card.setLayout(filter_layout)
        layout.addWidget(filter_card)

        self.call_table = QTableWidget()
        self.call_table.setColumnCount(5)
        self.call_table.setHorizontalHeaderLabels(["⏰ 时间", "📱 号码", "📞 类型", "⏱️ 时长(秒)", "📡 卡槽"])
        self.call_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.call_table.setAlternatingRowColors(True)
        layout.addWidget(self.call_table)
        return tab

    def create_contact_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(8)

        query_card = QGroupBox("🔍 查询联系人")
        query_layout = QHBoxLayout()
        query_layout.addWidget(QLabel("姓名:"))
        self.contact_name_input = QLineEdit()
        self.contact_name_input.setPlaceholderText("搜索姓名...")
        self.contact_name_input.setMaximumWidth(150)
        query_layout.addWidget(self.contact_name_input)
        query_layout.addWidget(QLabel("号码:"))
        self.contact_phone_input = QLineEdit()
        self.contact_phone_input.setPlaceholderText("搜索号码...")
        self.contact_phone_input.setMaximumWidth(150)
        query_layout.addWidget(self.contact_phone_input)
        self.contact_query_btn = QPushButton("🔍 查询")
        self.contact_query_btn.setObjectName("primaryBtn")
        self.contact_query_btn.clicked.connect(self.query_contacts)
        query_layout.addWidget(self.contact_query_btn)
        self.contact_export_btn = QPushButton("📊 导出")
        self.contact_export_btn.clicked.connect(
            lambda: self.export_table_to_csv(self.contact_table, "contacts_export.csv"))
        query_layout.addWidget(self.contact_export_btn)
        query_layout.addStretch()
        query_card.setLayout(query_layout)
        layout.addWidget(query_card)

        add_group = QGroupBox("➕ 添加联系人")
        add_layout = QFormLayout()
        self.add_contact_name = QLineEdit()
        self.add_contact_name.setPlaceholderText("通讯录显示名称")
        add_layout.addRow("姓名:", self.add_contact_name)
        self.add_contact_phone = QLineEdit()
        self.add_contact_phone.setPlaceholderText("多个号码用分号(;)分隔")
        add_layout.addRow("号码:", self.add_contact_phone)
        self.add_contact_btn = QPushButton("✅ 添加到手机")
        self.add_contact_btn.setObjectName("primaryBtn")
        self.add_contact_btn.clicked.connect(self.add_contact)
        add_layout.addRow("", self.add_contact_btn)
        add_group.setLayout(add_layout)
        layout.addWidget(add_group)

        self.contact_table = QTableWidget()
        self.contact_table.setColumnCount(2)
        self.contact_table.setHorizontalHeaderLabels(["👤 姓名", "📱 号码"])
        self.contact_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.contact_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.contact_table.setAlternatingRowColors(True)
        layout.addWidget(self.contact_table)
        return tab

    def create_send_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(12)

        send_card = QGroupBox("✉️ 发送短信")
        form_layout = QFormLayout()
        self.send_sim_combo = QComboBox()
        self.send_sim_combo.addItem("SIM卡 1", 1)
        self.send_sim_combo.addItem("SIM卡 2", 2)
        form_layout.addRow("📡 发送卡槽:", self.send_sim_combo)
        self.send_phone_input = QLineEdit()
        self.send_phone_input.setPlaceholderText("多个号码用分号(;)分隔")
        form_layout.addRow("📱 接收号码:", self.send_phone_input)
        self.send_content_edit = QTextEdit()
        self.send_content_edit.setMaximumHeight(150)
        self.send_content_edit.setPlaceholderText("请输入短信内容...")
        form_layout.addRow("💬 短信内容:", self.send_content_edit)

        btn_layout = QHBoxLayout()
        self.send_btn = QPushButton("✅ 发送短信")
        self.send_btn.setObjectName("primaryBtn")
        self.send_btn.setMinimumWidth(120)
        self.send_btn.clicked.connect(self.send_sms)
        btn_layout.addWidget(self.send_btn)
        btn_layout.addStretch()
        form_layout.addRow("", btn_layout)
        send_card.setLayout(form_layout)
        layout.addWidget(send_card)
        layout.addStretch()
        return tab

    def create_device_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(12)

        cards_layout = QHBoxLayout()
        battery_card = self._create_info_card("🔋 电池信息", "battery", "点击刷新获取电池状态")
        location_card = self._create_info_card("📍 定位信息", "location", "点击刷新获取定位信息")
        config_card = self._create_info_card("⚙️ 设备配置", "config", "点击刷新获取设备配置")
        cards_layout.addWidget(battery_card)
        cards_layout.addWidget(location_card)
        cards_layout.addWidget(config_card)
        layout.addLayout(cards_layout)

        wol_group = QGroupBox("🌐 网络唤醒 (WOL)")
        wol_layout = QHBoxLayout()
        self.wol_mac_input = QLineEdit()
        self.wol_mac_input.setPlaceholderText("MAC 地址 (如: 24:5E:BE:0C:45:9A)")
        self.wol_mac_input.setMaximumWidth(200)
        wol_layout.addWidget(self.wol_mac_input)
        self.wol_ip_input = QLineEdit()
        self.wol_ip_input.setPlaceholderText("内网 IP (可选)")
        self.wol_ip_input.setMaximumWidth(150)
        wol_layout.addWidget(self.wol_ip_input)
        self.wol_btn = QPushButton("🚀 发送唤醒包")
        self.wol_btn.setObjectName("primaryBtn")
        self.wol_btn.clicked.connect(self.send_wol)
        wol_layout.addWidget(self.wol_btn)
        wol_layout.addStretch()
        wol_group.setLayout(wol_layout)
        layout.addWidget(wol_group)
        return tab

    def _create_info_card(self, title: str, info_type: str, placeholder: str) -> QGroupBox:
        card = QGroupBox(title)
        card.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 24px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
                color: #374151;
            }
        """)
        card_layout = QVBoxLayout(card)
        info_label = QLabel()
        info_label.setTextFormat(Qt.TextFormat.RichText)
        info_label.setWordWrap(True)
        info_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        info_label.setStyleSheet("background-color: #f9fafb; border-radius: 6px; padding: 10px;")
        info_label.setMinimumHeight(80)
        info_label.setText(f'<div style="color: #9ca3af; text-align: center; padding: 20px;">{placeholder}</div>')
        info_label.setObjectName(f"{info_type}_info_text")
        card_layout.addWidget(info_label)

        refresh_btn = QPushButton("🔄 刷新")
        refresh_btn.setMaximumWidth(100)
        refresh_btn.setObjectName("primaryBtn")
        if info_type == "battery":
            refresh_btn.clicked.connect(lambda: self.query_battery_to_card(info_label))
        elif info_type == "location":
            refresh_btn.clicked.connect(lambda: self.query_location_to_card(info_label))
        elif info_type == "config":
            refresh_btn.clicked.connect(lambda: self.query_config_to_card(info_label))

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(refresh_btn)
        card_layout.addLayout(btn_layout)

        setattr(self, f"{info_type}_card", card)
        setattr(self, f"{info_type}_info_text", info_label)
        return card

    def create_smshub_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(12)

        group = QGroupBox("🌐 SmsHub 远程轮询设置 (v2.4.4及以下)")
        form = QFormLayout()
        self.smshub_url = QLineEdit()
        self.smshub_url.setPlaceholderText("http://your-server.com/api")
        form.addRow("服务端地址:", self.smshub_url)
        self.smshub_interval = QSpinBox()
        self.smshub_interval.setRange(10, 300)
        self.smshub_interval.setValue(30)
        self.smshub_interval.setSuffix(" 秒")
        form.addRow("心跳间隔:", self.smshub_interval)
        self.smshub_enabled = QCheckBox("启用 SmsHub 轮询")
        self.smshub_enabled.toggled.connect(self.toggle_smshub)
        form.addRow("", self.smshub_enabled)
        group.setLayout(form)
        layout.addWidget(group)

        info_card = QGroupBox("ℹ️ 说明")
        info_layout = QVBoxLayout()
        info = QLabel(
            "SmsHub 是 SmsForwarder v2.4.4 及以下版本的旧版协议。\n\n"
            "<b>工作原理:</b><br>"
            "• 客户端每隔指定时间向服务端发送心跳<br>"
            "• 服务端返回指令列表（如远程发短信）<br>"
            "• 客户端自动执行这些指令\n\n"
            "<b>注意:</b> 如果您使用的是新版 API 协议，无需启用此功能。"
        )
        info.setWordWrap(True)
        info.setStyleSheet("padding: 8px; color: #6b7280;")
        info_layout.addWidget(info)
        info_card.setLayout(info_layout)
        layout.addWidget(info_card)
        layout.addStretch()
        return tab

    def toggle_smshub(self, enabled):
        if enabled:
            if not hasattr(self, 'smshub_worker') or not self.smshub_worker.isRunning():
                self.smshub_worker = SmsHubWorker(self.smshub_url.text().strip(), self.smshub_interval.value())
                self.smshub_worker.log_signal.connect(self.log_message)
                self.smshub_worker.start()
                self.log_message("SmsHub 轮询已启动")
        else:
            if hasattr(self, 'smshub_worker'):
                self.smshub_worker.stop()
                self.log_message("SmsHub 轮询已停止")

    def check_new_messages(self):
        if not self.notify_enabled.isChecked():
            return
        if self._polling_new_messages:
            return
        base_url = self.url_input.text().strip()
        if not base_url:
            return
        current_mode = self.get_current_mode()
        if current_mode == EncryptionMode.SM4 and not self.sm4_key_input.text().strip():
            return
        if current_mode == EncryptionMode.RSA and not self.rsa_pubkey_input.toPlainText().strip():
            return

        self._polling_new_messages = True
        data = {"type": 1, "page_num": 1, "page_size": 10}

        def finish():
            self._polling_new_messages = False

        def on_success(result):
            try:
                if result.get("code") == 200:
                    sms_list = result.get("data", [])
                    if sms_list:
                        latest_ts = max(sms.get("date", 0) for sms in sms_list)
                        if latest_ts > self.last_sms_timestamp:
                            new_sms = [sms for sms in sms_list if sms.get("date", 0) > self.last_sms_timestamp]
                            if new_sms:
                                self.last_sms_timestamp = latest_ts
                                if self._is_first_poll:
                                    self._is_first_poll = False
                                    return
                                for sms in new_sms:
                                    content = sms.get("content", "")
                                    number = sms.get("number", "")
                                    name = sms.get("name", "未知")
                                    self.log_message(f"[轮询发现] 新短信: {name} {number}")
                                    if self.tray_icon and self.tray_icon.isVisible():
                                        # 截断过长的短信内容，保留前50个字符
                                        display_content = content[:50] + "..." if len(content) > 50 else content
                                        msg = f"来自 {name} ({number})\n{display_content}"
                                        self.last_tray_msg_type = "sms"
                                        try:
                                            self.tray_icon.showMessage("新短信", msg,
                                                                       QSystemTrayIcon.MessageIcon.Information, 5000)
                                        except Exception as e:
                                            self.log_message(f"显示通知失败: {e}")
                                        self._start_tray_blink()
                                # 窗口可见时自动刷新并滚动到最新
                                if self.isVisible():
                                    def refresh_ui():
                                        self.sms_type_combo.setCurrentIndex(0)  # 切换到接收类型
                                        self.query_sms()
                                        self.sms_table.scrollToTop()
                                    QTimer.singleShot(100, refresh_ui)
            finally:
                finish()

        def on_error(e):
            if "请配置" in e or "密钥" in e or "公钥" in e:
                if not hasattr(self, '_config_error_logged'):
                    self._config_error_logged = True
                    self.log_message("[轮询提示] 请检查加密配置是否正确")
            else:
                self.log_message(f"[轮询异常] {e}")
            finish()

        worker = self.create_worker("sms/query", data)
        if worker:
            worker.finished.connect(on_success)
            worker.error.connect(on_error)
            worker.start()
        else:
            finish()

    def on_notify_toggled(self, enabled):
        if enabled:
            interval = self.poll_interval_spin.value() * 1000
            if self.notify_timer:
                self.notify_timer.start(interval)
        else:
            if self.notify_timer:
                self.notify_timer.stop()
        self.save_settings()

    def on_poll_interval_changed(self, value):
        if self.notify_enabled.isChecked():
            self.notify_timer.start(value * 1000)
        self.save_settings()

    def load_settings(self):
        settings = QSettings("settings.ini", QSettings.Format.IniFormat)
        self.url_input.setText(settings.value("server_url", ""))
        self.token_input.setText(settings.value("api_token", ""))
        self.sm4_key_input.setText(settings.value("sm4_key", ""))
        self.rsa_pubkey_input.setText(settings.value("rsa_public_key", ""))
        encrypt_idx = settings.value("encrypt_index", 0, type=int)
        if encrypt_idx < self.encrypt_combo.count():
            self.encrypt_combo.setCurrentIndex(encrypt_idx)
        self.notify_enabled.setChecked(settings.value("notify_enabled", False, type=bool))
        self.poll_interval_spin.setValue(settings.value("poll_interval", 30, type=int))
        self.last_sms_timestamp = settings.value("last_sms_timestamp", 0, type=int)
        self._close_to_tray_setting = settings.value("close_to_tray", True, type=bool)
        self._esc_to_tray_setting = settings.value("esc_to_tray", True, type=bool)
        self._load_view_config()
        self.log_message("配置加载完成")

    def save_settings(self):
        settings = QSettings("settings.ini", QSettings.Format.IniFormat)
        settings.setValue("server_url", self.url_input.text().strip())
        settings.setValue("api_token", self.token_input.text().strip())
        settings.setValue("sm4_key", self.sm4_key_input.text().strip())
        settings.setValue("rsa_public_key", self.rsa_pubkey_input.toPlainText().strip())
        settings.setValue("encrypt_index", self.encrypt_combo.currentIndex())
        settings.setValue("notify_enabled", self.notify_enabled.isChecked())
        settings.setValue("poll_interval", self.poll_interval_spin.value())
        settings.setValue("last_sms_timestamp", self.last_sms_timestamp)
        settings.setValue("close_to_tray", self._close_to_tray_setting)
        settings.setValue("esc_to_tray", self._esc_to_tray_setting)
        self._save_view_config_to_settings()
        self.log_message("配置已保存")

    def closeEvent(self, event):
        if self._close_to_tray_setting:
            self.hide()
            self.log_message("窗口已隐藏到后台")
            event.ignore()
        else:
            self.save_settings()
            QApplication.quit()
            event.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            if self._esc_to_tray_setting:
                self.hide()
                self.log_message("按ESC键最小化到托盘")
            else:
                event.ignore()
        else:
            super().keyPressEvent(event)

    def show_normal(self):
        self._stop_tray_blink()
        self.showNormal()
        self.activateWindow()
        self.raise_()

    def quit_app(self):
        self.save_settings()
        if self.notify_timer:
            self.notify_timer.stop()
        if hasattr(self, 'connection_check_timer') and self.connection_check_timer:
            self.connection_check_timer.stop()
        if hasattr(self, 'smshub_worker') and self.smshub_worker.isRunning():
            self.smshub_worker.stop()
            self.smshub_worker.wait()
        for w in list(self._workers):
            try:
                if hasattr(w, 'isRunning') and w.isRunning():
                    w.terminate()
                    w.wait(2000)
            except Exception:
                pass
            self._workers.discard(w)
        if self.tray_icon:
            self.tray_icon.hide()
        QApplication.quit()

    def _toggle_view_action(self, index: int, checked: bool):
        self.tab_widget.setTabVisible(index, checked)
        if not checked and self.tab_widget.currentIndex() == index:
            for i in range(self.tab_widget.count()):
                if self.tab_widget.isTabVisible(i):
                    self.tab_widget.setCurrentIndex(i)
                    break
        self._save_view_config_to_settings()

    def configure_view_menu(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("⚙️ 配置视图菜单")
        dialog.setMinimumWidth(300)
        layout = QVBoxLayout(dialog)
        layout.setSpacing(10)
        layout.setContentsMargins(16, 16, 16, 16)
        info_label = QLabel("选择要在视图菜单中显示的项目：")
        info_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(info_label)

        checkboxes = {}
        for key, info in self.view_actions.items():
            cb = QCheckBox(info['action'].text())
            cb.setChecked(info['action'].isChecked())
            checkboxes[key] = cb
            layout.addWidget(cb)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        ok_btn = QPushButton("✅ 确定")
        ok_btn.clicked.connect(lambda: self._save_view_config(checkboxes, dialog))
        btn_layout.addWidget(ok_btn)
        cancel_btn = QPushButton("❌ 取消")
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        dialog.exec()

    def _save_view_config(self, checkboxes, dialog):
        for key, cb in checkboxes.items():
            info = self.view_actions[key]
            info['action'].setChecked(cb.isChecked())
            self._toggle_view_action(info['index'], cb.isChecked())
        self.save_settings()
        dialog.accept()

    def _load_view_config(self):
        if not hasattr(self, 'view_actions'):
            return
        settings = QSettings("settings.ini", QSettings.Format.IniFormat)
        for key, info in self.view_actions.items():
            visible = settings.value(f"view_{key}", True, type=bool)
            info['action'].setChecked(visible)
            self._toggle_view_action(info['index'], visible)

    def _save_view_config_to_settings(self):
        if not hasattr(self, 'view_actions'):
            return
        settings = QSettings("settings.ini", QSettings.Format.IniFormat)
        for key, info in self.view_actions.items():
            settings.setValue(f"view_{key}", info['action'].isChecked())

    def on_tray_message_clicked(self):
        if self.last_tray_msg_type == "sms":
            self.show_normal()
            QTimer.singleShot(100, lambda: self.tab_widget.setCurrentIndex(0))
            QTimer.singleShot(200, self._refresh_and_show_latest_sms)
        self.last_tray_msg_type = None

    def _update_sms_table(self, data):
        """更新短信表格数据的公共方法"""
        self.sms_table.setRowCount(len(data))
        self._current_sms_data = data
        for row, sms in enumerate(data):
            date_str = datetime.fromtimestamp(sms.get("date", 0) / 1000).strftime("%Y-%m-%d %H:%M:%S")
            self.sms_table.setItem(row, 0, QTableWidgetItem(date_str))
            self.sms_table.setItem(row, 1, QTableWidgetItem(sms.get("number", "")))
            self.sms_table.setItem(row, 2, QTableWidgetItem(sms.get("name", "未知")))
            self.sms_table.setItem(row, 3, QTableWidgetItem(sms.get("content", "")))
            sim_id = sms.get("sim_id", -1)
            sim_text = f"SIM{sim_id + 1}" if sim_id >= 0 else "未知"
            self.sms_table.setItem(row, 4, QTableWidgetItem(sim_text))

    def _refresh_and_show_latest_sms(self):
        def on_success(result):
            if result.get("code") == 200:
                data = result.get("data", [])
                # 使用公共方法更新表格数据
                self._update_sms_table(data)
                # 同步更新短信类型下拉框为"接收"
                self.sms_type_combo.setCurrentIndex(0)
                # 选择第一行并显示详情
                if data:
                    self.sms_table.scrollToTop()
                    self.sms_table.selectRow(0)
                    QTimer.singleShot(300, self.show_sms_detail)

        # 固定查询接收的短信(type=1)，与通知逻辑保持一致
        data = {"type": 1, "page_num": 1, "page_size": 20}
        worker = self.create_worker("sms/query", data)
        if worker:
            worker.finished.connect(on_success)
            worker.start()

    def _start_tray_blink(self):
        if not self.tray_icon:
            return
        self._stop_tray_blink()
        self._original_tooltip = self.tray_icon.toolTip()
        self._tray_blink_timer = QTimer(self)
        self._tray_blink_timer.setInterval(500)
        self._tray_blink_timer.timeout.connect(self._toggle_tray_icon)
        self._tray_blink_timer.start()
        self.tray_icon.setToolTip("有新消息")
        QTimer.singleShot(10000, self._stop_tray_blink)

    def _stop_tray_blink(self):
        if self._tray_blink_timer:
            self._tray_blink_timer.stop()
            self._tray_blink_timer.deleteLater()
            self._tray_blink_timer = None
        if self.tray_icon:
            self.tray_icon.setIcon(self.app_icon if not self.app_icon.isNull() else self.style().standardIcon(
                QStyle.StandardPixmap.SP_ComputerIcon))
            if hasattr(self, '_original_tooltip'):
                self.tray_icon.setToolTip(self._original_tooltip)

    def _toggle_tray_icon(self):
        if not self.tray_icon:
            return
        current = self.tray_icon.icon()
        if current.isNull():
            self.tray_icon.setIcon(self.app_icon if not self.app_icon.isNull() else self.style().standardIcon(
                QStyle.StandardPixmap.SP_ComputerIcon))
        else:
            self.tray_icon.setIcon(QIcon())

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_normal()

    def _safe_start_notify_timer(self):
        try:
            if self.notify_enabled.isChecked():
                interval = self.poll_interval_spin.value() * 1000
                if self.notify_timer and not self.notify_timer.isActive():
                    self.notify_timer.start(interval)
                    self.log_message(f"定时器已启动，间隔 {interval/1000} 秒")
            if self.connection_check_timer and not self.connection_check_timer.isActive():
                self.connection_check_timer.start()
                QTimer.singleShot(500, self.check_connection_status)
        except Exception as e:
            self.log_message(f"启动通知定时器失败: {e}")

    def check_connection_status(self):
        base_url = self.url_input.text().strip()
        if not base_url:
            self.update_connection_status(False)
            return
        if hasattr(self, '_checking_connection') and self._checking_connection:
            return
        self._checking_connection = True
        try:
            mode = self.get_current_mode()
            token = self.token_input.text().strip()
            sm4_key = self.sm4_key_input.text().strip()
            rsa_key = self.rsa_pubkey_input.toPlainText().strip()
            worker = APIWorker(base_url, mode, token, sm4_key, rsa_key)
            worker.set_request("config/query", {})

            def on_success(result):
                self.update_connection_status(result.get("code") == 200)
                self._checking_connection = False

            def on_error(e):
                self.update_connection_status(False)
                self._checking_connection = False

            worker.finished.connect(on_success)
            worker.error.connect(on_error)
            worker.start()
            self._connection_check_worker = worker
        except Exception:
            self.update_connection_status(False)
            self._checking_connection = False

    def update_connection_status(self, is_connected: bool):
        if is_connected:
            self.connection_status_label.setText("🟢 已连接")
            self.connection_status_label.setStyleSheet(
                "QLabel { padding: 4px 12px; border-radius: 4px; background-color: #dcfce7; color: #166534; }")
        else:
            self.connection_status_label.setText("🔴 未连接")
            self.connection_status_label.setStyleSheet(
                "QLabel { padding: 4px 12px; border-radius: 4px; background-color: #fee2e2; color: #991b1b; }")

    def _render_battery_card(self, info_label: QLabel, data: dict):
        level = data.get('level', '未知')
        status = data.get('status', '未知')
        health = data.get('health', '未知')
        plugged = data.get('plugged', '未知')
        voltage = data.get('voltage', '未知')
        temperature = data.get('temperature', '未知')
        if isinstance(level, (int, float)):
            level_color = "#10b981" if level >= 80 else "#f59e0b" if level >= 30 else "#ef4444"
            level_icon = "🟢" if level >= 80 else "🟡" if level >= 30 else "🔴"
        else:
            level_color = "#6b7280"
            level_icon = "⚪"
        html = f"""
        <div style="padding: 8px;">
            <div style="text-align: center; margin-bottom: 12px;">
                <span style="font-size: 32px;">{level_icon}</span>
                <div style="font-size: 24px; font-weight: bold; color: {level_color};">
                    {level if isinstance(level, str) else f'{level}%'}
                </div>
            </div>
            <div style="background-color: #f9fafb; border-radius: 6px; padding: 10px;">
                <div style="display: flex; justify-content: space-between;"><span>状态:</span><span>{status}</span></div>
                <div style="display: flex; justify-content: space-between;"><span>健康度:</span><span>{health}</span></div>
                <div style="display: flex; justify-content: space-between;"><span>充电方式:</span><span>{plugged}</span></div>
                <div style="display: flex; justify-content: space-between;"><span>电压:</span><span>{voltage}</span></div>
                <div style="display: flex; justify-content: space-between;"><span>温度:</span><span>{temperature}</span></div>
            </div>
        </div>
        """
        info_label.setText(html)

    def _render_location_card(self, info_label: QLabel, data: dict):
        address = data.get('address', '未知')
        latitude = data.get('latitude', '未知')
        longitude = data.get('longitude', '未知')
        time_str = data.get('time', '未知')
        if isinstance(time_str, (int, float)) and time_str > 0:
            time_str = datetime.fromtimestamp(time_str / 1000).strftime("%Y-%m-%d %H:%M:%S")
        html = f"""
        <div style="padding: 8px;">
            <div style="margin-bottom: 12px;">
                <div style="font-size: 13px; color: #6b7280;">📍 地址</div>
                <div style="font-weight: 600;">{address}</div>
            </div>
            <div style="background-color: #f9fafb; border-radius: 6px; padding: 10px;">
                <div style="display: flex; justify-content: space-between;"><span>纬度:</span><span>{latitude}</span></div>
                <div style="display: flex; justify-content: space-between;"><span>经度:</span><span>{longitude}</span></div>
                <div style="display: flex; justify-content: space-between;"><span>定位时间:</span><span>{time_str}</span></div>
            </div>
        </div>
        """
        info_label.setText(html)

    def _render_config_card(self, info_label: QLabel, data: dict):
        device_mark = data.get('extra_device_mark', '未知')
        sim1 = data.get('extra_sim1', '未知')
        sim2 = data.get('extra_sim2', '未知')
        features = []
        feature_map = [
            ('enable_api_sms_query', '远程查短信'),
            ('enable_api_sms_send', '远程发短信'),
            ('enable_api_call_query', '远程查通话'),
            ('enable_api_contact_query', '远程查联系人'),
            ('enable_api_battery_query', '远程查电量'),
        ]
        for key, name in feature_map:
            enabled = data.get(key, False)
            icon = "✅" if enabled else "❌"
            color = "#10b981" if enabled else "#ef4444"
            features.append(f'<div><span>{icon}</span> <span style="color:{color};">{name}</span></div>')
        html = f"""
        <div style="padding: 8px;">
            <div><span style="color:#6b7280;">设备备注:</span> <strong>{device_mark}</strong></div>
            <div style="margin: 8px 0;"><span>SIM1:</span> {sim1}</div>
            <div><span>SIM2:</span> {sim2}</div>
            <div style="margin-top: 10px;"><span style="font-weight:bold;">功能开关</span></div>
            <div style="background:#f9fafb; border-radius:6px; padding:8px;">{"".join(features)}</div>
        </div>
        """
        info_label.setText(html)


def main():
    import faulthandler
    try:
        crash_log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'crash.log')
        crash_file = open(crash_log_path, 'a+')
        faulthandler.enable(file=crash_file)
    except:
        pass

    from PyQt6.QtCore import QCoreApplication
    try:
        QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_UseSoftwareOpenGL, True)
    except:
        pass

    app = QApplication(sys.argv)
    app.setApplicationName(APP_CONFIG["app_name"])
    app.setOrganizationName("AuraService")
    app.setQuitOnLastWindowClosed(False)

    window = SmsForwarderClient()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()