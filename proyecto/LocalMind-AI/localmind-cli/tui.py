#!/usr/bin/env python3
import os
import sys
import json
import platform
import re
import time
import socket
import urllib.request
import shutil
import subprocess

# TrueColor ANSI Escapes - Blue & Orange Complementary Palette
NC = '\033[0m'
BOLD = '\033[1m'
DIM = '\033[2m'

COLOR_BLUE = '\033[38;2;37;99;235m'       # Primary Blue (#2563eb)
COLOR_LIGHT_BLUE = '\033[38;2;96;165;250m' # Light Blue (#60a5fa)
COLOR_TEAL = '\033[38;2;14;116;144m'      # Teal Blue (#0e7490)
COLOR_ORANGE = '\033[38;2;249;115;22m'    # Complementary Orange (#f97316)
COLOR_AMBER = '\033[38;2;217;119;6m'      # Amber Orange (#d97406)
COLOR_SUBTEXT = '\033[38;2;148;163;184m'   # Slate 400
COLOR_GREEN = '\033[38;2;16;185;129m'     # Emerald Green
COLOR_RED = '\033[38;2;239;68;68m'        # Red
COLOR_YELLOW = COLOR_AMBER

# Aliases to preserve import compatibility in install.sh and install.ps1
COLOR_LAVENDER = COLOR_BLUE
COLOR_MAUVE = COLOR_ORANGE
COLOR_PEACH = COLOR_ORANGE
COLOR_OVERLAY = COLOR_SUBTEXT

# Cross-platform raw input handling
if os.name == 'nt':
    import msvcrt
else:
    import tty
    import termios

def get_key(raw_text=False):
    if os.name == 'nt':
        if msvcrt.kbhit():
            ch = msvcrt.getch()
            if ch in (b'\x00', b'\xe0'):
                ch2 = msvcrt.getch()
                if ch2 == b'H': return 'up'
                elif ch2 == b'P': return 'down'
                elif ch2 == b'M': return 'right'
                elif ch2 == b'K': return 'left'
            elif ch == b'\r': return 'enter'
            elif ch == b' ': return 'space'
            elif ch == b'\x08': return 'backspace'
            elif ch == b'\x1b': return 'esc'
            if not raw_text:
                if ch in (b'q', b'Q'): return 'q'
                elif ch in (b'j', b'J'): return 'down'
                elif ch in (b'k', b'K'): return 'up'
            try:
                return ch.decode('utf-8')
            except:
                return None
        return None
    else:
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        new_settings = termios.tcgetattr(fd)
        new_settings[3] = new_settings[3] & ~(termios.ECHO | termios.ICANON)
        new_settings[6][termios.VMIN] = 0
        new_settings[6][termios.VTIME] = 1
        termios.tcsetattr(fd, termios.TCSADRAIN, new_settings)
        try:
            ch1 = sys.stdin.read(1)
            if not ch1:
                return None
            if ch1 == '\x1b':
                ch2 = sys.stdin.read(1)
                if ch2 == '[':
                    ch3 = sys.stdin.read(1)
                    if ch3 == 'A': return 'up'
                    elif ch3 == 'B': return 'down'
                    elif ch3 == 'C': return 'right'
                    elif ch3 == 'D': return 'left'
                return 'esc'
            elif ch1 == '\r' or ch1 == '\n':
                return 'enter'
            elif ch1 == ' ':
                return 'space'
            elif ch1 == '\x7f' or ch1 == '\x08':
                return 'backspace'
            if not raw_text:
                if ch1.lower() == 'j':
                    return 'down'
                elif ch1.lower() == 'k':
                    return 'up'
                elif ch1.lower() == 'q':
                    return 'q'
            return ch1
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

# Clean length of string (ignoring ANSI escapes and adjusting for wide chars/emojis)
ANSI_ESCAPE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

def char_width(c):
    o = ord(c)
    # Emojis/Wide characters: U+1F000 to U+1FAFF, and U+26A0 (Warning Sign)
    if 0x1F000 <= o <= 0x1FAFF or o == 0x26A0:
        return 2
    if o == 0xFE0F:  # Variation selector
        return 0
    return 1

def clean_len(s):
    cleaned = ANSI_ESCAPE.sub('', s)
    return sum(char_width(c) for c in cleaned)

def ansi_truncate(s, max_len):
    res = []
    curr_len = 0
    i = 0
    n = len(s)
    while i < n:
        if s[i] == '\x1b':
            start = i
            i += 1
            while i < n and not ('A' <= s[i] <= 'Z' or 'a' <= s[i] <= 'z'):
                i += 1
            if i < n:
                i += 1
            res.append(s[start:i])
        else:
            w = char_width(s[i])
            if curr_len + w <= max_len:
                res.append(s[i])
                curr_len += w
                i += 1
            else:
                break
    res.append(NC)
    return "".join(res)

# Brain ASCII art
BRAIN_LOGO = [
    "                             ▓▓▓▓▓▓▓▓▓                            ",
    "                           ▓▓▓▓▓▓ ▓▓▓▓▓▓▓                         ",
    "                        ▓▓▓▓▓         ▓▓▓▓▓                       ",
    "                       ▓▓▓▓             ▓▓▓▓                      ",
    "                     ▓▓▓▓                 ▓▓▓▓                    ",
    "                    ▓▓▓▓                   ▓▓▓▓                   ",
    "                   ▓▓▓▓                      ▓▓▓                  ",
    "                  ▓▓▓▓                        ▓▓▓                 ",
    "                 ▓▓▓▓          ▓▓▓▓▓          ▓▓▓▓                ",
    "                ▓▓▓▓        ▓▓▓▓▓▓▓▓▓▓▓        ▓▓▓▓               ",
    "                ▓▓▓       ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓       ▓▓▓▓              ",
    "               ▓▓▓      ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓      ▓▓▓▓             ",
    "              ▓▓▓▓     ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓     ▓▓▓▓             ",
    "             ▓▓▓▓    ▓▓▓▓▓▓  ▓▓▓▓▓▓▓▓▓  ▓▓▓▓▓▓    ▓▓▓▓            ",
    "            ▓▓▓▓    ▓▓▓▓▓▓▓   ▓▓▓▓▓▓▓▓   ▓▓▓▓▓▓     ▓▓▓           ",
    "           ▓▓▓▓    ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓   ▓▓▓▓          ",
    "          ▓▓▓▓   ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓   ▓▓▓▓         ",
    "          ▓▓▓▓   ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓   ▓▓▓▓         ",
    "           ▓▓▓▓   ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓   ▓▓▓▓          ",
    "            ▓▓▓▓▓   ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓    ▓▓▓▓           ",
    "              ▓▓▓▓    ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓   ▓▓▓▓             ",
    "                ▓▓▓▓▓   ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  ▓▓▓▓▓               ",
    "                  ▓▓▓▓▓▓  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  ▓▓▓▓▓▓                 ",
    "                      ▓▓▓▓▓ ▓▓▓▓▓▓▓▓▓▓▓ ▓▓▓▓▓▓                    ",
    "                           ▓▓ ▓▓▓▓▓▓▓ ▓▓▓                         ",
    "                              ▓▓▓▓▓▓▓                             ",
    "                             ▓▓▓   ▓▓▓                            ",
    "                             ▓▓▓   ▓▓▓                            ",
    "                              ▓▓▓▓▓▓▓                             ",
    "                                 ▓▓                               "
]

GRADIENT_COLORS = [COLOR_BLUE, COLOR_LIGHT_BLUE, COLOR_TEAL, COLOR_AMBER, COLOR_ORANGE]

import shutil

def get_terminal_width():
    try:
        columns, _ = shutil.get_terminal_size()
        return max(76, columns - 1)
    except Exception:
        return 76

def center_line(s, width):
    line_len = clean_len(s)
    pad_total = width - 4 - line_len
    if pad_total <= 0:
        return ansi_truncate(s, width - 4)
    left_pad = pad_total // 2
    right_pad = pad_total - left_pad
    return " " * left_pad + s + " " * right_pad

def render_logo():
    lines = []
    total = len(BRAIN_LOGO)
    bands = len(GRADIENT_COLORS)
    for i, line in enumerate(BRAIN_LOGO):
        band_idx = (i * bands) // total
        if band_idx >= bands:
            band_idx = bands - 1
        stripped_line = line.strip()
        lines.append(f"{GRADIENT_COLORS[band_idx]}{stripped_line}{NC}")
    return lines

def draw_frame(content_lines, title=None, width=None):
    if width is None:
        width = get_terminal_width()
    border_color = COLOR_BLUE
    
    # Header Line
    if title:
        title_text = f" {title} "
        left_len = (width - 2 - len(title_text)) // 2
        right_len = width - 2 - len(title_text) - left_len
        if left_len < 0: left_len = 0
        if right_len < 0: right_len = 0
        top_line = "╔" + "═" * left_len + f"{COLOR_ORANGE}{BOLD}{title_text}{border_color}" + "═" * right_len + "╗"
    else:
        top_line = "╔" + "═" * (width - 2) + "╗"
        
    print(f"{border_color}{top_line}{NC}")
    
    for line in content_lines:
        line_len = clean_len(line)
        total_pad = width - 2 - line_len
        if total_pad < 2:
            line = ansi_truncate(line, width - 4)
            line_len = clean_len(line)
            total_pad = width - 2 - line_len
        left_pad = total_pad // 2
        right_pad = total_pad - left_pad
        padded = " " * left_pad + line + " " * right_pad
        print(f"{border_color}║{NC}{padded}{border_color}║{NC}")
        
    # Bottom border
    bottom_line = "╚" + "═" * (width - 2) + "╝"
    print(f"{border_color}{bottom_line}{NC}")

def render_screen(logo_lines, info_lines, menu_lines, help_line, width=None):
    if width is None:
        width = get_terminal_width()
    print("\033[H\033[2J", end="")
    box_lines = []
    for line in logo_lines:
        box_lines.append(center_line(line, width))
    box_lines.append("")
    for line in info_lines:
        for subline in line.split('\n'):
            box_lines.append(center_line(subline, width))
    box_lines.append("")
    for line in menu_lines:
        box_lines.append(line)
    box_lines.append("")
    box_lines.append(center_line(help_line, width))
    draw_frame(box_lines, title="LocalMind-AI Setup", width=width)

def run_select_menu(title, subtitle, options, help_msg="j/k o ↑/↓: navegar • enter: seleccionar • q: salir", width=None, enabled_flags=None):
    if width is None:
        width = get_terminal_width()
    selected = 0
    print("\033[?25l", end="", flush=True)
    
    def draw(error_str=None):
        nonlocal width
        width = get_terminal_width()
        logo = render_logo()
        info = [
            f"{COLOR_SUBTEXT}{subtitle}{NC}",
            f"{COLOR_ORANGE}{BOLD}{title}{NC}"
        ]
        
        max_opt_len = max(clean_len(opt) for opt in options) + 2
        left_pad = (width - 4 - max_opt_len) // 2
        if left_pad < 0:
            left_pad = 0
            
        menu = []
        for i, opt in enumerate(options):
            if i == selected:
                opt_str = f"▸ {opt}"
                opt_styled = f"{COLOR_ORANGE}{BOLD}{opt_str}{NC}"
            else:
                opt_str = f"  {opt}"
                opt_styled = opt_str
                
            line_len = clean_len(opt_styled)
            right_pad = width - 4 - left_pad - line_len
            if right_pad < 0: right_pad = 0
            
            menu.append(" " * left_pad + opt_styled + " " * right_pad)
            
        help_line = f"{COLOR_SUBTEXT}{help_msg}{NC}"
        if error_str:
            help_line = f"{COLOR_RED}{BOLD}{error_str}{NC}"
        render_screen(logo, info, menu, help_line, width=width)
        
    draw()
    last_width = get_terminal_width()
    try:
        while True:
            current_width = get_terminal_width()
            if current_width != last_width:
                last_width = current_width
                draw()
                
            key = get_key()
            if not key:
                time.sleep(0.01)
                continue
                
            prev_selected = selected
            if key == 'up':
                selected = (selected - 1) % len(options)
            elif key == 'down':
                selected = (selected + 1) % len(options)
            elif key == 'enter':
                if enabled_flags and not enabled_flags[selected]:
                    draw(error_str="⚠️  Memoria insuficiente. Selecciona un modelo compatible.")
                    time.sleep(1.5)
                    draw()
                    continue
                return selected
            elif key == 'q':
                sys.exit(1)
            elif key == 'esc':
                return -1
                
            if selected != prev_selected:
                draw()
            time.sleep(0.01)
    finally:
        pass

def run_multiselect_menu(title, subtitle, options, defaults=None, help_msg="j/k o ↑/↓: navegar • espacio: alternar • enter: confirmar • q: salir", width=None):
    if width is None:
        width = get_terminal_width()
    selected = [False] * len(options)
    if defaults:
        for idx in defaults:
            if idx < len(selected):
                selected[idx] = True
    cursor = 0
    print("\033[?25l", end="", flush=True)
    
    def draw():
        nonlocal width
        width = get_terminal_width()
        logo = render_logo()
        info = [
            f"{COLOR_SUBTEXT}{subtitle}{NC}",
            f"{COLOR_ORANGE}{BOLD}{title}{NC}"
        ]
        
        max_opt_len = max(clean_len(opt) for opt in options) + 6
        left_pad = (width - 4 - max_opt_len) // 2
        if left_pad < 0:
            left_pad = 0
            
        menu = []
        for i, opt in enumerate(options):
            checkbox = f"[{COLOR_GREEN}✔{NC}]" if selected[i] else "[ ]"
            if i == cursor:
                opt_str = f"▸ {checkbox} {opt}"
                opt_styled = f"{COLOR_ORANGE}{BOLD}{opt_str}{NC}"
            else:
                opt_str = f"  {checkbox} {opt}"
                opt_styled = opt_str
                
            line_len = clean_len(opt_styled)
            right_pad = width - 4 - left_pad - line_len
            if right_pad < 0: right_pad = 0
            
            menu.append(" " * left_pad + opt_styled + " " * right_pad)
            
        help_line = f"{COLOR_SUBTEXT}{help_msg}{NC}"
        render_screen(logo, info, menu, help_line, width=width)
        
    draw()
    last_width = get_terminal_width()
    try:
        while True:
            current_width = get_terminal_width()
            if current_width != last_width:
                last_width = current_width
                draw()
                
            key = get_key()
            if not key:
                time.sleep(0.01)
                continue
                
            prev_cursor = cursor
            prev_selected = selected.copy()
            
            if key == 'up':
                cursor = (cursor - 1) % len(options)
            elif key == 'down':
                cursor = (cursor + 1) % len(options)
            elif key == 'space':
                selected[cursor] = not selected[cursor]
            elif key == 'enter':
                return [i for i, val in enumerate(selected) if val]
            elif key == 'q':
                sys.exit(1)
            elif key == 'esc':
                return -1
                
            if cursor != prev_cursor or selected != prev_selected:
                draw()
            time.sleep(0.01)
    finally:
        pass

def prompt_text_tui(title, subtitle, label, default_value=""):
    print("\033[?25l", end="", flush=True)  # Hide cursor
    text = default_value
    width = get_terminal_width()
    
    def draw():
        nonlocal width
        width = get_terminal_width()
        logo = render_logo()
        info = [
            f"{COLOR_SUBTEXT}{subtitle}{NC}",
            f"{COLOR_ORANGE}{BOLD}{title}{NC}"
        ]
        
        display_line = f"{COLOR_ORANGE}{BOLD}{label}:{NC} {text}█"
        max_opt_len = clean_len(display_line)
        left_pad = (width - 4 - max_opt_len) // 2
        if left_pad < 0: left_pad = 0
        right_pad = width - 4 - left_pad - max_opt_len
        if right_pad < 0: right_pad = 0
        
        menu = [
            " " * left_pad + display_line + " " * right_pad
        ]
        help_line = f"{COLOR_SUBTEXT}escribe tu clave • enter: confirmar • esc: volver{NC}"
        render_screen(logo, info, menu, help_line, width=width)
        
    draw()
    last_width = get_terminal_width()
    try:
        while True:
            current_width = get_terminal_width()
            if current_width != last_width:
                last_width = current_width
                draw()
                
            key = get_key(raw_text=True)
            if not key:
                time.sleep(0.01)
                continue
                
            if key == 'enter':
                return text
            elif key == 'esc':
                return 'back'
            elif key == 'backspace':
                text = text[:-1]
                draw()
            elif key == 'space':
                text += " "
                draw()
            elif len(key) == 1 and 32 <= ord(key) <= 126:
                text += key
                draw()
            time.sleep(0.01)
    finally:
        print("\033[?25h", end="", flush=True)  # Restore cursor

def run_progress_bar(title, duration_sec=1.5):
    print("\033[?25l", end="", flush=True)
    width = get_terminal_width()
    try:
        steps = 20
        for step in range(steps + 1):
            percent = (step * 100) // steps
            filled = step
            empty = steps - step
            bar = f"{COLOR_ORANGE}{'█' * filled}{NC}{COLOR_SUBTEXT}{'░' * empty}{NC}"
            logo = render_logo()
            info = [
                f"{COLOR_BLUE}{BOLD}{title}{NC}",
                ""
            ]
            menu = [
                f"Progreso: {bar} {COLOR_ORANGE}{percent}%{NC}"
            ]
            help_line = f"{COLOR_SUBTEXT}Generando archivos de configuración de LocalMind-AI...{NC}"
            render_screen(logo, info, menu, help_line, width=width)
            time.sleep(duration_sec / steps)
    finally:
        print("\033[?25h", end="", flush=True)

def detect_platform():
    os_name = platform.system()
    machine = platform.machine()
    is_mac = os_name == "Darwin"
    is_apple_silicon = is_mac and machine == "arm64"
    return is_mac, is_apple_silicon

def get_system_memory():
    """Retrieve system RAM and VRAM in GB using standard library subprocess commands."""
    is_mac = platform.system() == "Darwin"
    is_win = platform.system() == "Windows"
    ram_gb = 16.0
    vram_gb = 0.0
    
    if is_mac:
        try:
            import subprocess
            res = subprocess.check_output(["sysctl", "-n", "hw.memsize"])
            ram_gb = int(res.strip()) / (1024 ** 3)
            vram_gb = ram_gb
        except Exception:
            pass
    elif is_win:
        try:
            import subprocess
            res = subprocess.check_output("wmic ComputerSystem get TotalPhysicalMemory /value", shell=True)
            match = re.search(r'TotalPhysicalMemory=(\d+)', res.decode('utf-8', errors='ignore'))
            if match:
                ram_gb = int(match.group(1)) / (1024 ** 3)
        except Exception:
            pass
        try:
            import subprocess
            res = subprocess.check_output("wmic path win32_VideoController get AdapterRAM /value", shell=True)
            matches = re.findall(r'AdapterRAM=(\d+)', res.decode('utf-8', errors='ignore'))
            if matches:
                vram_gb = max(int(m) for m in matches) / (1024 ** 3)
        except Exception:
            pass
    else:  # Linux
        try:
            with open('/proc/meminfo', 'r') as f:
                for line in f:
                    if 'MemTotal' in line:
                        parts = line.split()
                        ram_gb = int(parts[1]) / (1024 ** 2)
                        break
        except Exception:
            pass
        try:
            import subprocess
            res = subprocess.check_output(["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits"], stderr=subprocess.DEVNULL)
            vram_gb = float(res.strip().split(b'\n')[0]) / 1024.0
        except Exception:
            pass
            
    return ram_gb, vram_gb

def is_port_open(port: int, host: str = "127.0.0.1") -> bool:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.4)
            return s.connect_ex((host, port)) == 0
    except Exception:
        return False

def check_ollama_status(port="11434", host="127.0.0.1") -> tuple[bool, bool, list[str]]:
    try:
        port_int = int(port)
    except ValueError:
        port_int = 11434
    installed = shutil.which("ollama") is not None
    running = False
    models = []
    if is_port_open(port_int, host):
        running = True
        try:
            req = urllib.request.Request(f"http://{host}:{port_int}/api/tags")
            with urllib.request.urlopen(req, timeout=0.8) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode())
                    models = [m["name"] for m in data.get("models", [])]
        except Exception:
            pass
    return installed, running, models

def check_omlx_status(omlx_model_dir="~/models", port="8082") -> tuple[bool, bool, list[str]]:
    try:
        port_int = int(port)
    except ValueError:
        port_int = 8082
    venv_bin = os.path.expanduser("~/.localmind/venv/bin/mlx_lm.server")
    if os.name == 'nt':
        venv_bin = os.path.expanduser("~/.localmind/venv/Scripts/mlx_lm.server.exe")
    installed = shutil.which("omlx") is not None or os.path.exists(venv_bin)
    
    running = is_port_open(port_int)
    models = []
    if running:
        try:
            req = urllib.request.Request(f"http://127.0.0.1:{port_int}/v1/models")
            with urllib.request.urlopen(req, timeout=0.8) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode())
                    models = [m["id"] for m in data.get("data", [])]
        except Exception:
            pass
            
    abs_model_dir = os.path.expanduser(omlx_model_dir)
    if os.path.exists(abs_model_dir):
        try:
            for org in os.listdir(abs_model_dir):
                org_path = os.path.join(abs_model_dir, org)
                if os.path.isdir(org_path):
                    for model in os.listdir(org_path):
                        model_path = os.path.join(org_path, model)
                        if os.path.isdir(model_path):
                            models.append(f"{org}/{model}")
        except Exception:
            pass
            
    hf_dir = os.path.expanduser("~/.cache/huggingface/hub")
    if os.path.exists(hf_dir):
        try:
            for d in os.listdir(hf_dir):
                if d.startswith("models--"):
                    name = d.replace("models--", "").replace("--", "/")
                    models.append(name)
        except Exception:
            pass
            
    # Deduplicate models list
    deduped = []
    for m in models:
        if "/" not in m:
            has_full_version = False
            for other in models:
                if "/" in other and other.endswith("/" + m):
                    has_full_version = True
                    break
            if not has_full_version:
                deduped.append(m)
        else:
            deduped.append(m)
            
    return installed, running, list(set(deduped))

def run_control_action(action: str):
    is_win = os.name == 'nt'
    cmd = []
    if is_win:
        cmd = ["powershell.exe", "-ExecutionPolicy", "Bypass", "-File", "localmind.ps1", action]
    else:
        cmd = ["./localmind", action]
    
    print("\033[?1049l\033[?25h", end="", flush=True)
    print(f"\n{COLOR_BLUE}Ejecutando: {' '.join(cmd)}{NC}\n")
    try:
        subprocess.run(cmd)
    except Exception as e:
        print(f"Error ejecutando el script de control: {e}")
    print("\nPresiona Enter para volver a la TUI...")
    input()
    print("\033[?1049h", end="", flush=True)


def download_selected_model(backend_type, selected_model, omlx_model_dir="~/models"):
    # Exit alternate screen buffer and show cursor
    print("\033[?1049l\033[?25h", end="", flush=True)
    print(f"\n{COLOR_BLUE}{BOLD}=== Descargando Modelo: {selected_model} ==={NC}\n")
    
    import subprocess
    venv_dir = os.path.expanduser("~/.localmind/venv")
    try:
        if backend_type == "ollama":
            cmd = ["ollama", "pull", selected_model]
            print(f"Ejecutando: {' '.join(cmd)}")
            subprocess.run(cmd)
        elif backend_type == "mlx":
            abs_model_dir = os.path.expanduser(omlx_model_dir)
            target_dir = os.path.join(abs_model_dir, selected_model)
            py_cmd = f"from huggingface_hub import snapshot_download; snapshot_download(repo_id='{selected_model}', local_dir='{target_dir}')"
            cmd = [os.path.join(venv_dir, "bin", "python"), "-c", py_cmd]
            print(f"Ejecutando: {' '.join(cmd)}")
            subprocess.run(cmd)
        print(f"\n{COLOR_GREEN}{BOLD}✔ Modelo descargado con éxito.{NC}")
    except Exception as e:
        print(f"\n{COLOR_RED}Error al descargar el modelo: {e}{NC}")
    
    print("\nPresiona Enter para volver a la TUI...")
    input()
    # Re-enter alternate screen buffer and hide cursor
    print("\033[?1049h\033[?25l", end="", flush=True)

def run_cleanup_menu():
    while True:
        opts = [
            "Borrar memoria de sesiones de Engram (SQLite DB)",
            "Borrar base de datos vectorial (ChromaDB)",
            "Borrar historial de chats de LocalMind",
            "Desinstalar LocalMind-AI al completo (Remover TODO)",
            "<- Volver al menú principal"
        ]
        choice = run_select_menu("🧹 Panel de Limpieza y Desinstalación",
                                 "Selecciona la acción de limpieza que deseas realizar (ESC para volver)",
                                 opts)
        if choice == -1 or choice == 4:
            break
            
        # Exit alternate screen buffer to run commands and print progress
        print("\033[?1049l\033[?25h", end="", flush=True)
        import shutil
        import subprocess
        
        try:
            if choice == 0:
                # Clear Engram session database
                engram_dir = os.path.expanduser("~/.localmind/engram")
                if os.path.exists(engram_dir):
                    print(f"\n{COLOR_PEACH}Limpiando contenido de Engram en {engram_dir}...{NC}")
                    for filename in os.listdir(engram_dir):
                        filepath = os.path.join(engram_dir, filename)
                        try:
                            if os.path.isfile(filepath) or os.path.islink(filepath):
                                os.unlink(filepath)
                            elif os.path.isdir(filepath):
                                shutil.rmtree(filepath)
                        except Exception as e:
                            print(f"No se pudo borrar {filepath}: {e}")
                    print(f"\n{COLOR_GREEN}✔ Memoria de Engram limpia.{NC}")
                else:
                    print(f"\n{COLOR_YELLOW}No se encontró directorio de Engram activo.{NC}")
                    
            elif choice == 1:
                # Clear ChromaDB using a temporary alpine container mount
                print(f"\n{COLOR_PEACH}Limpiando base de datos vectorial ChromaDB...{NC}")
                cmd = ["docker", "run", "--rm", "-v", "localmind-ai_chroma-db:/data", "alpine", "sh", "-c", "rm -rf /data/*"]
                print(f"Ejecutando: {' '.join(cmd)}")
                subprocess.run(cmd)
                print(f"\n{COLOR_GREEN}✔ Base de datos vectorial (ChromaDB) vaciada.{NC}")
                
            elif choice == 2:
                # Clear Nanobot Chat History using a temporary alpine container mount
                print(f"\n{COLOR_PEACH}Limpiando historial de chats de LocalMind...{NC}")
                cmd = ["docker", "run", "--rm", "-v", "localmind-ai_nanobot-workspace:/data", "alpine", "sh", "-c", "rm -rf /data/*"]
                print(f"Ejecutando: {' '.join(cmd)}")
                subprocess.run(cmd)
                print(f"\n{COLOR_GREEN}✔ Historial de chats eliminado.{NC}")
                
            elif choice == 3:
                # Full Uninstall
                print(f"\n{COLOR_RED}{BOLD}=== DESINSTALACIÓN COMPLETA ==={NC}")
                print("Esto eliminará:")
                print(" - Contenedores y volúmenes de Docker")
                print(" - Archivos de configuración (config.json, active_env.json)")
                print(" - Directorio local del usuario (~/.localmind)")
                print(" - Script CLI de control (localmind)\n")
                
                # Double confirmation
                confirm = input("¿Estás absolutamente seguro de continuar? (escribí 's' para confirmar): ")
                if confirm.lower() == 's':
                    print(f"\n{COLOR_PEACH}Deteniendo y eliminando contenedores Docker...{NC}")
                    subprocess.run(["docker", "compose", "down", "-v"])
                    
                    print(f"{COLOR_PEACH}Eliminando archivos de configuración locales...{NC}")
                    for f in ["backend/config/config.json", "backend/config/active_env.json", "docker-compose.yml", "localmind", "localmind.ps1"]:
                        if os.path.exists(f):
                            os.remove(f)
                            
                    localmind_dir = os.path.expanduser("~/.localmind")
                    if os.path.exists(localmind_dir):
                        print(f"{COLOR_PEACH}Eliminando directorio host ~/.localmind...{NC}")
                        shutil.rmtree(localmind_dir)
                        
                    print(f"\n{COLOR_GREEN}{BOLD}✔ Desinstalación completada. Saliendo...{NC}\n")
                    sys.exit(0)
                else:
                    print(f"\n{COLOR_YELLOW}Desinstalación cancelada.{NC}")
                    
        except Exception as e:
            print(f"\n{COLOR_RED}Error durante la limpieza: {e}{NC}")
            
        print("\nPresiona Enter para volver a la TUI...")
        input()
        # Re-enter alternate screen buffer
        print("\033[?1049h\033[?25l", end="", flush=True)


def run_full_installation(backend_type, selected_model, enable_engram, mcp_choices, skill_choices, enable_context7, context7_key, omlx_api_key,
                          omlx_model_dir="~/models", omlx_port="8082", omlx_max_mem="80%", omlx_cache_dir="~/.omlx/cache", omlx_hot_cache="4GB",
                          ollama_port="11434", ollama_host="127.0.0.1"):
    # Exit alternate screen buffer and show cursor
    print("\033[?1049l\033[?25h", end="", flush=True)
    print(f"\n{COLOR_BLUE}{BOLD}=== Iniciando Instalación Completa de LocalMind-AI ==={NC}\n")
    
    import subprocess
    import shutil
    
    try:
        # Step 1: Write all configurations first
        print(f"{COLOR_LIGHT_BLUE}[1/5] Generando archivos de configuración...{NC}")
        save_config_data(backend_type, selected_model, enable_engram, mcp_choices, skill_choices, enable_context7, context7_key, omlx_api_key,
                         omlx_model_dir, omlx_port, omlx_max_mem, omlx_cache_dir, omlx_hot_cache, ollama_port, ollama_host)
        
        # Step 2: Configure backend engine
        print(f"\n{COLOR_LIGHT_BLUE}[2/5] Configurando entorno para {backend_type.upper()}...{NC}")
        if backend_type == "ollama":
            if shutil.which("ollama") is None:
                print(f"{COLOR_YELLOW}Ollama no está instalado. Instalándolo...{NC}")
                is_mac = platform.system() == "Darwin"
                if is_mac:
                    subprocess.run(["brew", "install", "--cask", "ollama"])
                else:
                    # Linux installer
                    subprocess.run("curl -fsSL https://ollama.com/install.sh | sh", shell=True)
            else:
                print(f"{COLOR_GREEN}✔ Ollama ya está instalado en el host.{NC}")
        elif backend_type == "mlx":
            venv_dir = os.path.expanduser("~/.localmind/venv")
            print(f"Creando entorno virtual Python en {venv_dir}...")
            os.makedirs(os.path.expanduser("~/.localmind"), exist_ok=True)
            if not os.path.exists(venv_dir):
                subprocess.run([sys.executable, "-m", "venv", venv_dir])
            
            print("Instalando y actualizando mlx-lm y huggingface_hub...")
            subprocess.run([os.path.join(venv_dir, "bin", "pip"), "install", "--upgrade", "pip"])
            subprocess.run([os.path.join(venv_dir, "bin", "pip"), "install", "mlx-lm", "huggingface_hub"])
            print(f"{COLOR_GREEN}✔ Entorno virtual de MLX listo.{NC}")
            
        # Step 3: Download model
        print(f"\n{COLOR_LIGHT_BLUE}[3/5] Descargando modelo seleccionado ({selected_model})...{NC}")
        if backend_type == "ollama":
            subprocess.run(["ollama", "pull", selected_model])
        elif backend_type == "mlx":
            venv_dir = os.path.expanduser("~/.localmind/venv")
            abs_model_dir = os.path.expanduser(omlx_model_dir)
            target_dir = os.path.join(abs_model_dir, selected_model)
            py_cmd = f"from huggingface_hub import snapshot_download; snapshot_download(repo_id='{selected_model}', local_dir='{target_dir}')"
            subprocess.run([os.path.join(venv_dir, "bin", "python"), "-c", py_cmd])
        print(f"{COLOR_GREEN}✔ Modelo descargado correctamente.{NC}")
        
        # Step 4: Rebuild and start Docker containers
        print(f"\n{COLOR_LIGHT_BLUE}[4/5] Iniciando contenedores Docker de LocalMind...{NC}")
        subprocess.run(["docker", "compose", "up", "-d"])
        print(f"{COLOR_GREEN}✔ Contenedores e hilos del agente listos.{NC}")
        
        # Step 5: Install frontend dependencies
        print(f"\n{COLOR_LIGHT_BLUE}[5/5] Instalando dependencias del frontend (pnpm)...{NC}")
        if os.path.exists("frontend"):
            if shutil.which("pnpm") is not None:
                subprocess.run(["pnpm", "install"], cwd="frontend")
            else:
                print(f"{COLOR_YELLOW}pnpm no encontrado. Instalando globalmente...{NC}")
                subprocess.run(["npm", "install", "-g", "pnpm"])
                subprocess.run(["pnpm", "install"], cwd="frontend")
            print(f"{COLOR_GREEN}✔ Dependencias del frontend listas.{NC}")
            
        # Step 6: Generate main control CLI script
        print(f"\n{COLOR_LIGHT_BLUE}Generando script de control CLI principal...{NC}")
        subprocess.run([sys.executable, "localmind-cli/generate_localmind.py"])
        print(f"{COLOR_GREEN}✔ Script ./localmind generado con éxito.{NC}")
        
        print(f"\n{COLOR_GREEN}{BOLD}¡Instalación completada con éxito! 🎉{NC}")
        print("El agente y el WebSocket están listos.")
        
        is_win = os.name == 'nt'
        if is_win:
            cmd = ["powershell.exe", "-ExecutionPolicy", "Bypass", "-File", "localmind.ps1", "web"]
            popen_kwargs = {"creationflags": 0x00000008}
        else:
            cmd = ["./localmind", "web"]
            popen_kwargs = {"start_new_session": True}
            
        print(f"\n{COLOR_LIGHT_BLUE}Iniciando frontend web en segundo plano y abriendo el navegador...{NC}")
        try:
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **popen_kwargs)
            print(f"{COLOR_GREEN}✔ Frontend web iniciado de fondo (Expo en http://localhost:8081).{NC}")
        except Exception as e:
            print(f"{COLOR_RED}No se pudo iniciar el frontend automáticamente: {e}{NC}")
            print("Podés abrirlo manualmente ejecutando: ./localmind web")
        
    except Exception as e:
        print(f"\n{COLOR_RED}Error durante la instalación: {e}{NC}")
        
    print("\nPresiona Enter para volver a la TUI...")
    input()
    # Re-enter alternate screen buffer and hide cursor
    print("\033[?1049h\033[?25l", end="", flush=True)

def load_existing_config(is_apple_silicon):
    # Static defaults
    defaults = {
        "backend_type": "mlx" if is_apple_silicon else "ollama",
        "selected_model": "",
        "enable_engram": 1,
        "mcp_choices": [0, 1, 2, 3, 4],
        "skill_choices": [0, 1, 2, 3, 4, 5, 6],
        "enable_context7": 0,
        "context7_key": "",
        "omlx_api_key": "",
        "omlx_model_dir": "~/models",
        "omlx_port": "8082",
        "omlx_max_mem": "balanced",
        "omlx_cache_dir": "~/.omlx/cache",
        "omlx_hot_cache": "4GB",
        "ollama_port": "11434",
        "ollama_host": "127.0.0.1"
    }
    
    active_env_path = "backend/config/active_env.json"
    config_json_path = "backend/config/config.json"
    
    if os.path.exists(active_env_path):
        try:
            with open(active_env_path, 'r') as f:
                env_data = json.load(f)
            defaults["backend_type"] = env_data.get("BACKEND_TYPE", defaults["backend_type"])
            defaults["selected_model"] = env_data.get("SELECTED_MODEL", defaults["selected_model"])
            defaults["enable_engram"] = env_data.get("ENABLE_ENGRAM", defaults["enable_engram"])
            defaults["omlx_api_key"] = env_data.get("OMLX_API_KEY", defaults.get("omlx_api_key", ""))
            defaults["omlx_model_dir"] = env_data.get("OMLX_MODEL_DIR", defaults.get("omlx_model_dir", "~/models"))
            defaults["omlx_port"] = env_data.get("OMLX_PORT", defaults.get("omlx_port", "8082"))
            defaults["omlx_max_mem"] = env_data.get("OMLX_MAX_MEM", defaults.get("omlx_max_mem", "80%"))
            defaults["omlx_cache_dir"] = env_data.get("OMLX_CACHE_DIR", defaults.get("omlx_cache_dir", "~/.omlx/cache"))
            defaults["omlx_hot_cache"] = env_data.get("OMLX_HOT_CACHE", defaults.get("omlx_hot_cache", "4GB"))
            defaults["ollama_port"] = env_data.get("OLLAMA_PORT", defaults.get("ollama_port", "11434"))
            defaults["ollama_host"] = env_data.get("OLLAMA_HOST", defaults.get("ollama_host", "127.0.0.1"))
            
            # If advanced settings are stored in active_env, load them
            if "MCP_CHOICES" in env_data:
                defaults["mcp_choices"] = env_data["MCP_CHOICES"]
            if "SKILL_CHOICES" in env_data:
                defaults["skill_choices"] = env_data["SKILL_CHOICES"]
            if "ENABLE_CONTEXT7" in env_data:
                defaults["enable_context7"] = env_data["ENABLE_CONTEXT7"]
            if "CONTEXT7_KEY" in env_data:
                defaults["context7_key"] = env_data["CONTEXT7_KEY"]
        except Exception:
            pass
            
    # Try to refine with config.json if active_env didn't have all details
    if os.path.exists(config_json_path):
        try:
            with open(config_json_path, 'r') as f:
                cfg_data = json.load(f)
            
            # Expose/infer mcp choices from config.json structure
            mcp_choices = []
            if cfg_data.get("tools", {}).get("exec", {}).get("enable", False):
                mcp_choices.append(0)
            if cfg_data.get("tools", {}).get("web", {}).get("enable", False):
                mcp_choices.append(1)
            if cfg_data.get("tools", {}).get("my", {}).get("enable", False):
                mcp_choices.append(2)
            
            mcp_servers = cfg_data.get("tools", {}).get("mcpServers", {})
            if "localmind-tools" in mcp_servers:
                mcp_choices.append(3)
            if "context7" in mcp_servers:
                mcp_choices.append(4)
                defaults["enable_context7"] = 1
                defaults["context7_key"] = mcp_servers["context7"].get("env", {}).get("CONTEXT7_API_KEY", "")
                
            defaults["mcp_choices"] = mcp_choices
            if not defaults.get("omlx_api_key"):
                defaults["omlx_api_key"] = cfg_data.get("providers", {}).get("custom", {}).get("apiKey", "")
            
            # Infer skill choices by finding disabled ones
            disabled = cfg_data.get("agents", {}).get("defaults", {}).get("disabledSkills", [])
            all_skills = ["memory", "summarize", "weather", "github", "tmux", "skill-creator", "clawhub"]
            skill_choices = []
            for idx, skill in enumerate(all_skills):
                if skill not in disabled:
                    skill_choices.append(idx)
            defaults["skill_choices"] = skill_choices
            
            if "engram" in mcp_servers:
                defaults["enable_engram"] = 1
            else:
                defaults["enable_engram"] = 0
                
        except Exception:
            pass
            
    return defaults

def main():
    is_mac, is_apple_silicon = detect_platform()
    ram_gb, vram_gb = get_system_memory()
    
    # Load defaults from active configuration
    defaults = load_existing_config(is_apple_silicon)
    backend_type = defaults["backend_type"]
    selected_model = defaults["selected_model"]
    enable_engram = defaults["enable_engram"]
    mcp_choices = defaults["mcp_choices"]
    skill_choices = defaults["skill_choices"]
    enable_context7 = defaults["enable_context7"]
    context7_key = defaults["context7_key"]
    omlx_api_key = defaults.get("omlx_api_key", "")
    omlx_model_dir = defaults.get("omlx_model_dir", "~/models")
    omlx_port = defaults.get("omlx_port", "8082")
    omlx_max_mem = defaults.get("omlx_max_mem", "80%")
    omlx_cache_dir = defaults.get("omlx_cache_dir", "~/.omlx/cache")
    omlx_hot_cache = defaults.get("omlx_hot_cache", "4GB")
    ollama_port = defaults.get("ollama_port", "11434")
    ollama_host = defaults.get("ollama_host", "127.0.0.1")
    
    while True:
        # Check services status
        ollama_inst, ollama_run, ollama_models = check_ollama_status(port=ollama_port, host=ollama_host)
        omlx_inst, omlx_run, omlx_models = check_omlx_status(omlx_model_dir, port=omlx_port)
        
        status_lines = []
        status_lines.append(f"{COLOR_SUBTEXT}Estado de los Servicios Locales:{NC}")
        if ollama_inst:
            status_tag = f"{COLOR_GREEN}[Activo]{NC}" if ollama_run else f"{COLOR_PEACH}[Inactivo]{NC}"
            status_lines.append(f"  • Ollama: {status_tag} (Modelos: {len(ollama_models)})")
        else:
            status_lines.append(f"  • Ollama: {COLOR_RED}[No Instalado]{NC}")
            
        if omlx_inst:
            status_tag = f"{COLOR_GREEN}[Activo]{NC}" if omlx_run else f"{COLOR_PEACH}[Inactivo]{NC}"
            status_lines.append(f"  • oMLX (puerto {omlx_port}): {status_tag} (Modelos: {len(omlx_models)})")
        else:
            status_lines.append(f"  • oMLX: {COLOR_RED}[No Instalado]{NC}")
            
        subtitle_with_status = "LocalMind-AI 1.0.0 — Asistente Personal Multitarea\n" + "\n".join(status_lines)
        
        opts = [
            "Iniciar Instalación Completa / Configuración Híbrida",
            "Configurar motor local (Ollama / MLX)",
            "Configurar modelos de lenguaje",
            "Configurar memoria (Engram) y MCPs adicionales",
            "▶ Arrancar todos los servicios (LLMs + Docker)",
            "■ Parar todos los servicios (LLMs + Docker)",
            "🧹 Limpieza de datos y Desinstalación",
            "Salir / Quit"
        ]
        choice = run_select_menu("Configuración del Agente de Inteligencia Artificial Local", 
                                 subtitle_with_status, 
                                 opts)
        if choice == 7 or choice == -1:
            sys.exit(1)
            
        if choice == 4:
            run_control_action("start")
            
            is_win = os.name == 'nt'
            if is_win:
                cmd = ["powershell.exe", "-ExecutionPolicy", "Bypass", "-File", "localmind.ps1", "web"]
                popen_kwargs = {"creationflags": 0x00000008}
            else:
                cmd = ["./localmind", "web"]
                popen_kwargs = {"start_new_session": True}
                
            print(f"\n{COLOR_LIGHT_BLUE}Iniciando frontend web en segundo plano y abriendo el navegador...{NC}")
            try:
                subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **popen_kwargs)
                print(f"{COLOR_GREEN}✔ Frontend web iniciado de fondo (Expo en http://localhost:8081).{NC}")
            except Exception as e:
                print(f"{COLOR_RED}No se pudo iniciar el frontend automáticamente: {e}{NC}")
            time.sleep(1.5)
            continue
        elif choice == 5:
            run_control_action("stop")
            continue
        elif choice == 6:
            run_cleanup_menu()
            continue
            
        target_step = 1
        if choice == 0:
            target_step = 1
        elif choice == 1:
            target_step = 1
        elif choice == 2:
            target_step = 2
        elif choice == 3:
            target_step = 4
            
        # Step Wizard Loop
        step = target_step
        last_step = 8
        
        while 1 <= step <= last_step:
            if step == 1:
                # Select LLM Engine
                if is_apple_silicon:
                    engines = [
                        "MLX (Recomendado para Apple Silicon - Máxima aceleración unificada)",
                        "Ollama (Configuración fácil - Soporte general de modelos GGUF)",
                        "<- Volver al menú principal"
                    ]
                    engine_vals = ["mlx", "ollama"]
                    engine_choice = run_select_menu("Paso 1: Selecciona el Motor LLM Local",
                                                    "Los modelos correrán localmente acelerados por hardware (ESC para volver)",
                                                    engines)
                    if engine_choice == -1 or engine_choice == 2:
                        step = 0
                        break
                    backend_type = engine_vals[engine_choice]
                else:
                    backend_type = "ollama"
                    print(f"\n{COLOR_BLUE}Motor configurado automáticamente: {BOLD}Ollama{NC} (Recomendado para tu plataforma).\n")
                    time.sleep(1.0)
                
                # Advanced Serve Parameters Customization
                if backend_type == "mlx":
                    while True:
                        omlx_inst, omlx_run, omlx_models = check_omlx_status(omlx_model_dir, port=omlx_port)
                        status_str = f"Estado en el host: {COLOR_GREEN}Activo{NC}" if omlx_run else f"Estado en el host: {COLOR_PEACH}Inactivo{NC}"
                        if not omlx_inst:
                            status_str += f" {COLOR_RED}[oMLX/MLX no instalado]{NC}"
                        
                        opts_mlx = [
                            "Configurar parámetros avanzados de oMLX serve",
                            "Cargar configuración por defecto (oMLX)"
                        ]
                        
                        action_idx = -1
                        if omlx_inst:
                            if not omlx_run:
                                opts_mlx.append("▶ Iniciar / Encender oMLX serve en el host")
                            else:
                                opts_mlx.append("■ Detener / Apagar oMLX serve en el host")
                            action_idx = len(opts_mlx) - 1
                            
                        opts_mlx.append("<- Confirmar y continuar")
                        confirm_idx = len(opts_mlx) - 1
                        
                        mlx_choice = run_select_menu("Acciones del proveedor oMLX",
                                                     f"Gestioná el servicio local en el host.\n{status_str}",
                                                     opts_mlx)
                        if mlx_choice == -1:
                            break
                            
                        if mlx_choice == 0:
                            val = prompt_text_tui("Configurar oMLX: Directorio de Modelos",
                                                  "Ruta absoluta o relativa donde se guardarán y leerán los modelos.",
                                                  "Directorio de modelos",
                                                  default_value=omlx_model_dir)
                            if val.lower() == 'back':
                                continue
                            omlx_model_dir = val

                            val = prompt_text_tui("Configurar oMLX: Puerto del Servidor",
                                                  "Puerto TCP en el host donde escuchará oMLX.",
                                                  "Puerto oMLX",
                                                  default_value=omlx_port)
                            if val.lower() == 'back':
                                continue
                            omlx_port = val

                            val = prompt_text_tui("Configurar oMLX: Guardia de Memoria",
                                                  "Nivel de seguridad (safe, balanced, aggressive) o límite en GB (ej. 10).",
                                                  "Guardia de memoria",
                                                  default_value=omlx_max_mem)
                            if val.lower() == 'back':
                                continue
                            omlx_max_mem = val

                            val = prompt_text_tui("Configurar oMLX: Directorio de Caché SSD",
                                                  "Directorio para paginación de caché en disco SSD.",
                                                  "Directorio de caché",
                                                  default_value=omlx_cache_dir)
                            if val.lower() == 'back':
                                continue
                            omlx_cache_dir = val

                            val = prompt_text_tui("Configurar oMLX: Tamaño de Caché Caliente",
                                                  "Tamaño máximo de caché caliente en memoria (ej. '4GB', '8GB'). 0 = deshabilitado.",
                                                  "Caché caliente",
                                                  default_value=omlx_hot_cache)
                            if val.lower() == 'back':
                                continue
                            omlx_hot_cache = val
                            
                        elif mlx_choice == 1:
                            omlx_model_dir = "~/models"
                            omlx_port = "8082"
                            omlx_max_mem = "balanced"
                            omlx_cache_dir = "~/.omlx/cache"
                            omlx_hot_cache = "4GB"
                            print("\033[?1049l\033[?25h", end="", flush=True)
                            print(f"\n{COLOR_GREEN}✔ Valores por defecto de oMLX cargados.{NC}\n")
                            time.sleep(1.0)
                            print("\033[?1049h\033[?25l", end="", flush=True)
                            
                        elif action_idx != -1 and mlx_choice == action_idx:
                            print("\033[?1049l\033[?25h", end="", flush=True)
                            log_file = os.path.expanduser("~/.localmind/omlx_start.log")
                            os.makedirs(os.path.dirname(log_file), exist_ok=True)
                            if not omlx_run:
                                print(f"\n{COLOR_YELLOW}Iniciando servidor oMLX en puerto {omlx_port}...{NC}")
                                clean_mem = omlx_max_mem.strip().lower()
                                mem_guard_args = []
                                if clean_mem in ["safe", "balanced", "aggressive"]:
                                    mem_guard_args = ["--memory-guard", clean_mem]
                                elif "%" in clean_mem:
                                    mem_guard_args = ["--memory-guard", "balanced"]
                                else:
                                    gb_val = "".join([c for c in clean_mem if c.isdigit() or c == "."])
                                    if gb_val:
                                        mem_guard_args = ["--memory-guard-gb", gb_val]
                                    else:
                                        mem_guard_args = ["--memory-guard", "balanced"]
                                
                                if shutil.which("omlx") is not None:
                                    cmd = ["omlx", "serve", "--model-dir", os.path.expanduser(omlx_model_dir), "--port", omlx_port] + mem_guard_args + ["--paged-ssd-cache-dir", os.path.expanduser(omlx_cache_dir), "--hot-cache-max-size", omlx_hot_cache]
                                else:
                                    venv_dir = os.path.expanduser("~/.localmind/venv")
                                    py_server = os.path.join(venv_dir, "bin", "mlx_lm.server")
                                    if os.name == 'nt':
                                        py_server = os.path.join(venv_dir, "Scripts", "mlx_lm.server.exe")
                                    model_to_run = selected_model if selected_model else "mlx-community/Ornith-1.0-9B-6bit"
                                    cmd = [py_server, "--model", model_to_run, "--port", omlx_port]
                                
                                print(f"Ejecutando: {' '.join(cmd)}")
                                try:
                                    with open(log_file, "w") as lf:
                                        subprocess.Popen(cmd, stdout=lf, stderr=lf, start_new_session=True)
                                    time.sleep(3.0)
                                    port_int = int(omlx_port)
                                    if is_port_open(port_int):
                                        print(f"{COLOR_GREEN}✔ oMLX iniciado correctamente (puerto {omlx_port} activo).{NC}")
                                    else:
                                        print(f"{COLOR_YELLOW}⚠ oMLX puede estar cargando el modelo. Verificá en unos segundos.{NC}")
                                        if os.path.exists(log_file):
                                            try:
                                                with open(log_file) as lf:
                                                    log_content = lf.read().strip()
                                                if log_content:
                                                    print(f"{COLOR_SUBTEXT}Log: {log_content[:300]}{NC}")
                                            except Exception:
                                                pass
                                except Exception as e:
                                    print(f"{COLOR_RED}Error al iniciar oMLX/MLX: {e}{NC}")
                            else:
                                print(f"\n{COLOR_RED}Deteniendo servidor oMLX/MLX...{NC}")
                                try:
                                    if platform.system() == "Windows":
                                        subprocess.run(["powershell.exe", "-Command", "Stop-Process -Name 'python' -Force -ErrorAction SilentlyContinue"])
                                        subprocess.run(["powershell.exe", "-Command", "Stop-Process -Name 'omlx' -Force -ErrorAction SilentlyContinue"])
                                    else:
                                        subprocess.run(["pkill", "-f", "omlx-server"], capture_output=True)
                                        subprocess.run(["pkill", "-f", "omlx serve"], capture_output=True)
                                        subprocess.run(["pkill", "-f", "mlx_lm.server"], capture_output=True)
                                    time.sleep(2.0)
                                    port_int = int(omlx_port)
                                    if not is_port_open(port_int):
                                        print(f"{COLOR_GREEN}✔ oMLX detenido correctamente.{NC}")
                                    else:
                                        print(f"{COLOR_YELLOW}⚠ oMLX podría seguir activo. Intentá de nuevo.{NC}")
                                except Exception as e:
                                    print(f"{COLOR_RED}Error al detener oMLX/MLX: {e}{NC}")
                            input(f"\n{COLOR_SUBTEXT}Presioná Enter para continuar...{NC}")
                            print("\033[?1049h\033[?25l", end="", flush=True)
                            
                        elif mlx_choice == confirm_idx:
                            break
                            
                elif backend_type == "ollama":
                    while True:
                        ollama_inst, ollama_run, ollama_models = check_ollama_status(port=ollama_port, host=ollama_host)
                        status_str = f"Estado en el host: {COLOR_GREEN}Activo{NC}" if ollama_run else f"Estado en el host: {COLOR_PEACH}Inactivo{NC}"
                        if not ollama_inst:
                            status_str += f" {COLOR_RED}[Ollama no instalado]{NC}"
                            
                        opts_ollama = [
                            "Configurar parámetros avanzados de Ollama",
                            "Cargar configuración por defecto (Ollama)"
                        ]
                        
                        action_idx = -1
                        if ollama_inst:
                            if not ollama_run:
                                opts_ollama.append("▶ Iniciar / Encender Ollama en el host")
                            else:
                                opts_ollama.append("■ Detener / Apagar Ollama en el host")
                            action_idx = len(opts_ollama) - 1
                            
                        opts_ollama.append("<- Confirmar y continuar")
                        confirm_idx = len(opts_ollama) - 1
                        
                        ollama_choice = run_select_menu("Acciones del proveedor Ollama",
                                                         f"Gestioná el servicio local en el host.\n{status_str}",
                                                         opts_ollama)
                        if ollama_choice == -1:
                            break
                            
                        if ollama_choice == 0:
                            val = prompt_text_tui("Configurar Ollama: Host del Servidor",
                                                  "Host IP en el que Ollama escucha (usualmente 127.0.0.1 o 0.0.0.0).",
                                                  "Host de Ollama",
                                                  default_value=ollama_host)
                            if val.lower() == 'back':
                                continue
                            ollama_host = val

                            val = prompt_text_tui("Configurar Ollama: Puerto del Servidor",
                                                  "Puerto TCP en el host en el que Ollama escucha (por defecto 11434).",
                                                  "Puerto de Ollama",
                                                  default_value=ollama_port)
                            if val.lower() == 'back':
                                continue
                            ollama_port = val
                            
                        elif ollama_choice == 1:
                            ollama_host = "127.0.0.1"
                            ollama_port = "11434"
                            print("\033[?1049l\033[?25h", end="", flush=True)
                            print(f"\n{COLOR_GREEN}✔ Valores por defecto de Ollama cargados.{NC}\n")
                            time.sleep(1.0)
                            print("\033[?1049h\033[?25l", end="", flush=True)
                            
                        elif action_idx != -1 and ollama_choice == action_idx:
                            print("\033[?1049l\033[?25h", end="", flush=True)
                            log_file = os.path.expanduser("~/.localmind/ollama_start.log")
                            os.makedirs(os.path.dirname(log_file), exist_ok=True)
                            if not ollama_run:
                                print(f"\n{COLOR_YELLOW}Iniciando servicio Ollama en host {ollama_host} puerto {ollama_port}...{NC}")
                                try:
                                    started = False
                                    if platform.system() == "Darwin":
                                        # Use subprocess.run to detect if app launch actually fails
                                        result = subprocess.run(["open", "-a", "Ollama"], capture_output=True, timeout=5)
                                        if result.returncode != 0:
                                            print(f"{COLOR_YELLOW}Ollama.app no encontrada, usando CLI fallback...{NC}")
                                            env = os.environ.copy()
                                            env["OLLAMA_HOST"] = f"{ollama_host}:{ollama_port}"
                                            with open(log_file, "w") as lf:
                                                subprocess.Popen(["ollama", "serve"], env=env, stdout=lf, stderr=lf, start_new_session=True)
                                        else:
                                            started = True
                                    elif platform.system() == "Windows":
                                        subprocess.Popen(["powershell.exe", "-Command", f"$env:OLLAMA_HOST='{ollama_host}:{ollama_port}'; Start-Process -FilePath 'ollama' -ArgumentList 'serve' -WindowStyle Hidden"])
                                    else:
                                        # Linux: try systemctl, then CLI fallback
                                        result = subprocess.run(["systemctl", "start", "ollama"], capture_output=True, timeout=5)
                                        if result.returncode != 0:
                                            env = os.environ.copy()
                                            env["OLLAMA_HOST"] = f"{ollama_host}:{ollama_port}"
                                            with open(log_file, "w") as lf:
                                                subprocess.Popen(["ollama", "serve"], env=env, stdout=lf, stderr=lf, start_new_session=True)
                                    time.sleep(3.0)
                                    # Verify it actually started
                                    if is_port_open(int(ollama_port), ollama_host):
                                        print(f"{COLOR_GREEN}✔ Ollama iniciado correctamente (puerto {ollama_port} activo).{NC}")
                                    else:
                                        print(f"{COLOR_YELLOW}⚠ Ollama puede estar arrancando aún. Verificá en unos segundos.{NC}")
                                        if os.path.exists(log_file):
                                            try:
                                                with open(log_file) as lf:
                                                    log_content = lf.read().strip()
                                                if log_content:
                                                    print(f"{COLOR_SUBTEXT}Log: {log_content[:200]}{NC}")
                                            except Exception:
                                                pass
                                except Exception as e:
                                    print(f"{COLOR_RED}Error al iniciar Ollama: {e}{NC}")
                            else:
                                print(f"\n{COLOR_RED}Deteniendo servicio Ollama...{NC}")
                                try:
                                    if platform.system() == "Windows":
                                        subprocess.run(["powershell.exe", "-Command", "Stop-Process -Name 'ollama' -Force -ErrorAction SilentlyContinue"])
                                    elif platform.system() == "Darwin":
                                        # On macOS: quit app gracefully, then kill CLI process
                                        subprocess.run(["osascript", "-e", 'quit app "Ollama"'], capture_output=True, timeout=5)
                                        time.sleep(1.0)
                                        subprocess.run(["pkill", "-f", "ollama serve"], capture_output=True)
                                        subprocess.run(["pkill", "Ollama"], capture_output=True)
                                    else:
                                        # Linux: try systemctl, then pkill fallback
                                        result = subprocess.run(["systemctl", "stop", "ollama"], capture_output=True, timeout=5)
                                        if result.returncode != 0:
                                            subprocess.run(["pkill", "-f", "ollama"], capture_output=True)
                                    time.sleep(2.0)
                                    if not is_port_open(int(ollama_port), ollama_host):
                                        print(f"{COLOR_GREEN}✔ Ollama detenido correctamente.{NC}")
                                    else:
                                        print(f"{COLOR_YELLOW}⚠ Ollama podría seguir activo. Intentá de nuevo.{NC}")
                                except Exception as e:
                                    print(f"{COLOR_RED}Error al detener Ollama: {e}{NC}")
                            input(f"\n{COLOR_SUBTEXT}Presioná Enter para continuar...{NC}")
                            print("\033[?1049h\033[?25l", end="", flush=True)
                            
                        elif ollama_choice == confirm_idx:
                            break
                
                step = 9 if choice == 1 else 2
                
            elif step == 2:
                # Select Model Category
                cat_opts = [
                    "Modelos Más Inteligentes",
                    "Modelos Menos Inteligentes/Rápidos",
                    "<- Volver al paso anterior"
                ]
                cat_choice = run_select_menu(f"Paso 2: Selecciona la Categoría de Modelos ({backend_type.upper()})",
                                             "Elige el nivel de inteligencia y recursos requeridos (ESC para volver)",
                                             cat_opts)
                if cat_choice == -1 or cat_choice == 2:
                    if choice == 2:
                        step = 0
                        break
                    else:
                        step = 1
                        continue
                selected_category = "smart" if cat_choice == 0 else "light"
                step = 3
                
            elif step == 3:
                # Select Model within category
                models_metadata = {
                    "mlx": [
                        # Smart category
                        ("Ornith-1.0-9B-6bit (Recomendado)", "mlx-community/Ornith-1.0-9B-6bit", 8.0, False, "smart"),
                        ("Qwen3.5-9B-Instruct-6bit (MTP)", "mlx-community/Qwen3.5-9B-Instruct-6bit", 8.0, False, "smart"),
                        ("Qwopus3.5-9B-Coder-6bit", "mlx-community/Qwopus3.5-9B-Coder-6bit", 8.0, False, "smart"),
                        # Light category
                        ("Ornith-1.0-9B-4bit", "mlx-community/Ornith-1.0-9B-4bit", 5.8, True, "light"),
                        ("Qwen3.5-9B-Instruct-4bit (MTP)", "mlx-community/Qwen3.5-9B-Instruct-4bit", 5.8, True, "light"),
                        ("Qwopus3.5-9B-Coder-4bit", "mlx-community/Qwopus3.5-9B-Coder-4bit", 5.8, True, "light"),
                        ("Qwopus3.5-4B-Coder-6bit (Ligero)", "mlx-community/Qwopus3.5-4B-Coder-6bit", 4.0, True, "light"),
                        ("Qwopus3.5-4B-Coder-4bit (Bajo recurso)", "mlx-community/Qwopus3.5-4B-Coder-4bit", 3.0, True, "light"),
                    ],
                    "ollama": [
                        # Smart category
                        ("Ornith-1.0-9B-Q6_K (Recomendado)", "ornith:9b-q6_k", 8.0, False, "smart"),
                        ("Qwen3.5-9B-Instruct-Q6_K (MTP)", "qwen3.5-instruct:9b-q6_k", 8.0, False, "smart"),
                        ("Qwopus3.5-9B-Coder-Q6_K", "qwopus3.5-coder:9b-q6_k", 8.0, False, "smart"),
                        # Light category
                        ("Ornith-1.0-9B-Q4_K_M", "ornith:9b-q4_k_m", 5.8, True, "light"),
                        ("Qwen3.5-9B-Instruct-Q4_K_M (MTP)", "qwen3.5-instruct:9b-q4_k_m", 5.8, True, "light"),
                        ("Qwopus3.5-9B-Coder-Q4_K_M", "qwopus3.5-coder:9b-q4_k_m", 5.8, True, "light"),
                        ("Qwopus3.5-4B-Coder-Q6_K (Ligero)", "qwopus3.5-coder:4b-q6_k", 4.0, True, "light"),
                        ("Qwopus3.5-4B-Coder-Q4_K_M (Bajo recurso)", "qwopus3.5-coder:4b-q4_k_m", 3.0, True, "light"),
                    ]
                }
                
                filtered_models = [m for m in models_metadata[backend_type] if m[4] == selected_category]
                
                # Check which models are downloaded
                if backend_type == "ollama":
                    _, _, downloaded_models = check_ollama_status(port=ollama_port, host=ollama_host)
                else:
                    _, _, downloaded_models = check_omlx_status(omlx_model_dir, port=omlx_port)
                
                model_opts = []
                model_ids = []
                enabled_flags = []
                
                for display, model_id, size, is_limited, category in filtered_models:
                    if is_mac:
                        if ram_gb >= size + 3.0:
                            tag = f"{COLOR_GREEN}[Rápido]{NC}"
                            enabled = True
                        elif ram_gb >= size + 0.5:
                            tag = f"{COLOR_PEACH}[Normal]{NC}"
                            enabled = True
                        else:
                            tag = f"{COLOR_RED}[Imposible]{NC}"
                            enabled = False
                    else:
                        if vram_gb >= size + 1.5:
                            tag = f"{COLOR_GREEN}[Rápido (GPU)]{NC}"
                            enabled = True
                        elif vram_gb + ram_gb >= size + 4.5:
                            tag = f"{COLOR_PEACH}[Normal (CPU)]{NC}"
                            enabled = True
                        else:
                            tag = f"{COLOR_RED}[Imposible]{NC}"
                            enabled = False
                    
                    is_downloaded = False
                    for dm in downloaded_models:
                        norm_dm = dm.replace("\\", "/").lower()
                        norm_mid = model_id.replace("\\", "/").lower()
                        if backend_type == "ollama":
                            if norm_mid in norm_dm or norm_dm in norm_mid:
                                is_downloaded = True
                                break
                        else:
                            if norm_mid == norm_dm or norm_mid.endswith("/" + norm_dm):
                                is_downloaded = True
                                break
                    download_tag = f" {COLOR_GREEN}[Descargado]{NC}" if is_downloaded else f" {COLOR_PEACH}[No Descargado]{NC}"
                            
                    limited_tag = f" {COLOR_PEACH}[Precisión Baja / Limitado]{NC}" if is_limited else ""
                    menu_string = f"{display:<38} {tag}{limited_tag}{download_tag}"
                    model_opts.append(menu_string)
                    model_ids.append(model_id)
                    enabled_flags.append(enabled)
                
                # Add back option
                model_opts.append("<- Volver a categorías")
                model_ids.append("back")
                enabled_flags.append(True)
                
                model_choice = run_select_menu(f"Paso 3: Selecciona el Modelo para {backend_type.upper()}",
                                               f"Tus recursos: {ram_gb:.1f}GB RAM • {vram_gb:.1f}GB VRAM (ESC para volver)",
                                               model_opts,
                                               enabled_flags=enabled_flags)
                if model_choice == -1 or model_ids[model_choice] == "back":
                    step = 2
                    continue
                selected_model = model_ids[model_choice]
                step = 9 if choice == 2 else 4
                
            elif step == 4:
                # Enable Memory (Engram)
                mem_opts = [
                    "Habilitar memoria persistente (Engram - Recomendado)",
                    "Deshabilitar memoria persistente (El agente no recordará chats)",
                    "<- Volver al paso anterior"
                ]
                mem_choice = run_select_menu("Paso 4: Configurar Memoria Persistente del Agente",
                                             "Permite al agente recordar contexto e interacciones previas (ESC para volver)",
                                             mem_opts)
                if mem_choice == -1 or mem_choice == 2:
                    if choice == 3:
                        step = 0
                        break
                    else:
                        step = 3
                        continue
                enable_engram = 1 if mem_choice == 0 else 0
                step = 5
                
            elif step == 5:
                # Config MCPs / Tools
                mcp_list = [
                    "exec (Ejecución de comandos y shell)",
                    "web (Navegación y búsqueda DuckDuckGo)",
                    "my (Auto-inspección del estado del agente)",
                    "localmind-tools (RAG y herramientas internas)",
                    "context7 (Documentación oficial de librerías en tiempo real)"
                ]
                mcp_res = run_multiselect_menu("Paso 5: Selecciona las Herramientas/MCPs a habilitar",
                                                   "Usa el espacio para alternar y enter para continuar (ESC para volver)",
                                                   mcp_list, defaults=mcp_choices)
                if mcp_res == -1:
                    step = 4
                    continue
                mcp_choices = mcp_res
                enable_context7 = 1 if 4 in mcp_choices else 0
                step = 6
                
            elif step == 6:
                # Config Skills
                skills_list = [
                    "memory (Memoria a largo plazo SOUL/USER/MEMORY)",
                    "summarize (Resumir URLs, documentos y videos)",
                    "weather (Clima actual vía wttr.in)",
                    "github (Integración con la CLI de GitHub)",
                    "tmux (Control remoto de terminales tmux)",
                    "skill-creator (Habilidad para autogenerar skills)",
                    "clawhub (Buscar e instalar habilidades adicionales)"
                ]
                skill_res = run_multiselect_menu("Paso 6: Selecciona las Habilidades (Skills) a habilitar",
                                                     "Usa el espacio para alternar y enter para continuar (ESC para volver)",
                                                     skills_list, defaults=skill_choices)
                if skill_res == -1:
                    step = 5
                    continue
                skill_choices = skill_res
                step = 7
                
            elif step == 7:
                # Context7 key
                if enable_context7:
                    context7_key = prompt_text_tui("Paso 7: Configuración de Context7", 
                                                "Se requiere una clave API (creá una gratis en context7.com)", 
                                                "Introduce tu CONTEXT7_API_KEY",
                                                default_value=context7_key)
                    if context7_key.lower() == 'back':
                        step = 6
                        continue
                step = 8
                
            elif step == 8:
                # oMLX API Key configuration step
                if backend_type == "mlx":
                    default_key = omlx_api_key
                    if not default_key:
                        omlx_settings_path = os.path.expanduser("~/.omlx/settings.json")
                        if os.path.exists(omlx_settings_path):
                            try:
                                with open(omlx_settings_path, 'r') as sf:
                                    settings_data = json.load(sf)
                                default_key = settings_data.get("auth", {}).get("api_key", "")
                            except Exception:
                                pass
                    
                    omlx_api_key = prompt_text_tui("Paso 8: API Key de oMLX",
                                                "Se requiere para conectar con el servidor local de oMLX.",
                                                "API Key de oMLX",
                                                default_value=default_key)
                    if omlx_api_key.lower() == 'back':
                        step = 7 if enable_context7 else 6
                        continue
                step = 9
                
        if step == 9:
            # 1. Save all generated configuration data
            save_config_data(backend_type, selected_model, enable_engram, mcp_choices, skill_choices, enable_context7, context7_key, omlx_api_key,
                             omlx_model_dir, omlx_port, omlx_max_mem, omlx_cache_dir, omlx_hot_cache, ollama_port, ollama_host)
            
            # 2. Handle choices logic
            if choice == 0:
                # Full install: run the complete installation process inside python TUI
                run_full_installation(backend_type, selected_model, enable_engram, mcp_choices, skill_choices, enable_context7, context7_key, omlx_api_key,
                                      omlx_model_dir, omlx_port, omlx_max_mem, omlx_cache_dir, omlx_hot_cache, ollama_port, ollama_host)
            elif choice == 2:
                # Configure models: check if the new model is already downloaded
                if backend_type == "ollama":
                    _, _, downloaded = check_ollama_status(port=ollama_port, host=ollama_host)
                else:
                    _, _, downloaded = check_omlx_status(omlx_model_dir, port=omlx_port)
                
                is_downloaded = False
                for dm in downloaded:
                    norm_dm = dm.replace("\\", "/").lower()
                    norm_mid = selected_model.replace("\\", "/").lower()
                    if backend_type == "ollama":
                        if norm_mid in norm_dm or norm_dm in norm_mid:
                            is_downloaded = True
                            break
                    else:
                        if norm_mid == norm_dm or norm_mid.endswith("/" + norm_dm):
                            is_downloaded = True
                            break
                        
                if not is_downloaded:
                    # Ask if they want to pull/download the model now
                    opts_dl = ["Sí, descargar ahora", "No, descargar más tarde"]
                    dl_choice = run_select_menu("¿Deseas descargar el modelo seleccionado ahora?",
                                                f"Modelo: {selected_model} ({backend_type.upper()})",
                                                opts_dl)
                    if dl_choice == 0:
                        download_selected_model(backend_type, selected_model, omlx_model_dir)
                else:
                    # Model already exists. Allow delete or keep
                    opts_exists = [
                        "Conservar y establecer como modelo activo",
                        "Eliminar modelo del disco (Liberar espacio)"
                    ]
                    exist_choice = run_select_menu(f"El modelo {selected_model} ya está descargado",
                                                   "Selecciona una opción para gestionar el modelo:",
                                                   opts_exists)
                    if exist_choice == 1:
                        # Exit alternate screen buffer temporarily to print status
                        print("\033[?1049l\033[?25h", end="", flush=True)
                        print(f"\n{COLOR_ORANGE}Eliminando modelo {selected_model}...{NC}")
                        try:
                            if backend_type == "ollama":
                                subprocess.run(["ollama", "rm", selected_model])
                            else:
                                abs_dir = os.path.expanduser(omlx_model_dir)
                                model_path = os.path.join(abs_dir, selected_model)
                                if os.path.exists(model_path):
                                    shutil.rmtree(model_path)
                            print(f"{COLOR_GREEN}✔ Modelo eliminado con éxito.{NC}")
                        except Exception as e:
                            print(f"{COLOR_RED}Error al eliminar el modelo: {e}{NC}")
                        time.sleep(1.5)
                        # Re-enter alternate screen buffer
                        print("\033[?1049h\033[?25l", end="", flush=True)
                    else:
                        # Exit alternate screen buffer temporarily to print notice
                        print("\033[?1049l\033[?25h", end="", flush=True)
                        print(f"\n{COLOR_GREEN}✔ El modelo {selected_model} se ha establecido como activo.{NC}\n")
                        time.sleep(1.5)
                        # Re-enter alternate screen buffer
                        print("\033[?1049h\033[?25l", end="", flush=True)
            
def save_config_data(backend_type, selected_model, enable_engram, mcp_choices, skill_choices, enable_context7, context7_key, omlx_api_key,
                     omlx_model_dir="~/models", omlx_port="8082", omlx_max_mem="80%", omlx_cache_dir="~/.omlx/cache", omlx_hot_cache="4GB",
                     ollama_port="11434", ollama_host="127.0.0.1"):
    run_progress_bar("Generando archivos de configuración de LocalMind-AI...")
    port = ollama_port if backend_type == "ollama" else omlx_port
    
    tpl_config = "localmind-cli/templates/config.json.tpl"
    dest_config = "backend/config/config.json"
    os.makedirs("backend/config", exist_ok=True)
    
    with open(tpl_config, 'r') as f:
        config = json.load(f)
        
    # Use user-entered omlx_api_key, fallback to auto-detection if empty
    if backend_type == "mlx" and not omlx_api_key:
        omlx_settings_path = os.path.expanduser("~/.omlx/settings.json")
        if os.path.exists(omlx_settings_path):
            try:
                with open(omlx_settings_path, 'r') as sf:
                    settings_data = json.load(sf)
                omlx_api_key = settings_data.get("auth", {}).get("api_key", "")
            except Exception:
                pass

    # Use custom host/port for Ollama or custom port for MLX
    api_host = "host.docker.internal"
    config['providers']['custom']['apiBase'] = f"http://{api_host}:{port}/v1"
    config['providers']['custom']['apiKey'] = omlx_api_key
    config['agents']['defaults']['model'] = selected_model
    
    mcp_servers = config['tools']['mcpServers']
    
    # Save disabled skills
    all_skills = ["memory", "summarize", "weather", "github", "tmux", "skill-creator", "clawhub"]
    disabled_skills = []
    for idx, skill in enumerate(all_skills):
        if idx not in skill_choices:
            disabled_skills.append(skill)
    config['agents']['defaults']['disabledSkills'] = disabled_skills
    config['agents']['defaults']['disabled_skills'] = disabled_skills
    
    # Configure core tools
    config['tools']['exec']['enable'] = (0 in mcp_choices)
    config['tools']['web']['enable'] = (1 in mcp_choices)
    if 'my' not in config['tools']:
        config['tools']['my'] = {}
    config['tools']['my']['enable'] = (2 in mcp_choices)
    config['tools']['filesystem']['enable'] = True
    
    # Setup Engram
    if enable_engram == 1:
        mcp_servers['engram'] = {
            'command': 'pnpm',
            'args': ['--package=engram-sdk', 'dlx', 'engram-mcp'],
            'env': {
                'ENGRAM_DATA_DIR': '/app/engram'
            }
        }
    else:
        mcp_servers.pop('engram', None)
        
    # Setup localmind-tools
    if 3 not in mcp_choices:
        mcp_servers.pop('localmind-tools', None)
    else:
        mcp_servers['localmind-tools'] = {
            'command': 'python3',
            'args': ['-m', 'mcp_tools.server'],
            'env': {
                'SANDBOX_DIR': '/app/sandbox',
                'OUTPUTS_DIR': '/app/outputs',
                'OLLAMA_URL': f'http://host.docker.internal:{ollama_port}'
            }
        }
        
    # Setup Context7
    if enable_context7 == 1:
        mcp_servers['context7'] = {
            'command': 'pnpm',
            'args': ['dlx', '@upstash/context7-mcp'],
            'env': {
                'CONTEXT7_API_KEY': context7_key
            }
        }
    else:
        mcp_servers.pop('context7', None)
        
    # Clean old ones
    mcp_servers.pop('brave-search', None)
    mcp_servers.pop('fetch', None)
        
    with open(dest_config, 'w') as f:
        json.dump(config, f, indent=2)
        
    tpl_compose = "localmind-cli/templates/docker-compose.yml.tpl"
    dest_compose = "docker-compose.yml"
    
    with open(tpl_compose, 'r') as f:
        compose_content = f.read()
        
    if enable_engram == 1:
        compose_content = compose_content.replace("# {{ENGRAM_VOLUME_MOUNT}}", "- ~/.localmind/engram:/app/engram")
        os.makedirs(os.path.expanduser("~/.localmind/engram"), exist_ok=True)
    else:
        compose_content = compose_content.replace("# {{ENGRAM_VOLUME_MOUNT}}", "")
        
    with open(dest_compose, 'w') as f:
        f.write(compose_content)
        
    active_env = {
        "BACKEND_TYPE": backend_type,
        "SELECTED_MODEL": selected_model,
        "PORT": port,
        "ENABLE_ENGRAM": enable_engram,
        "MCP_CHOICES": mcp_choices,
        "SKILL_CHOICES": skill_choices,
        "ENABLE_CONTEXT7": enable_context7,
        "CONTEXT7_KEY": context7_key,
        "OMLX_API_KEY": omlx_api_key,
        "OMLX_MODEL_DIR": omlx_model_dir,
        "OMLX_PORT": omlx_port,
        "OMLX_MAX_MEM": omlx_max_mem,
        "OMLX_CACHE_DIR": omlx_cache_dir,
        "OMLX_HOT_CACHE": omlx_hot_cache,
        "OLLAMA_PORT": ollama_port,
        "OLLAMA_HOST": ollama_host
    }
    with open("backend/config/active_env.json", "w") as f:
        json.dump(active_env, f, indent=2)
        
    print("\033[H\033[2J", end="")
    print(f"\n{COLOR_GREEN}{BOLD}✔ Configuración interactiva guardada con éxito.{NC}\n")

if __name__ == '__main__':
    # Enter Alternate Screen Buffer to disable scrollback history (prevents visual trash on scroll)
    print("\033[?1049h", end="", flush=True)
    try:
        main()
    finally:
        # Exit Alternate Screen Buffer and restore cursor
        print("\033[?1049l\033[?25h", end="", flush=True)
