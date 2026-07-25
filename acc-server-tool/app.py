# app.py - Backend Flask com todas as rotas

import os
import json
import codecs
import shutil
import datetime
import subprocess
import sys
import threading
import webbrowser
import requests
from flask import Flask, render_template, request, jsonify, send_from_directory

from acc_data import (
    TRACKS, CAR_GROUPS, SESSION_TYPES, SESSION_TYPES_REV, WEEKDAYS, DEFAULT_CONFIG,
    SESSION_PRESETS, SESSION_PRESET_LABELS, build_session_plan
)

# Importações para diálogos de arquivo
try:
    import tkinter as tk
    from tkinter import filedialog
except ImportError:
    tk = None  # Marcar que o tkinter não está disponível

if sys.version_info >= (3, 14):
    import pkgutil
    if not hasattr(pkgutil, 'get_loader'):
        pkgutil.get_loader = lambda name: None

# Determina o caminho base, seja em modo de desenvolvimento ou empacotado com PyInstaller
if getattr(sys, 'frozen', False):
    # Rodando em um bundle PyInstaller
    base_path = sys._MEIPASS
    app_path = os.path.dirname(sys.executable) # Pasta do .exe
else:
    # Rodando em um ambiente de desenvolvimento normal
    base_path = os.path.dirname(os.path.abspath(__file__))
    app_path = base_path

# --- Gerenciamento do Caminho do Servidor ---
APP_CONFIG_FILE = os.path.join(app_path, 'app_config.json')

def get_server_dir():
    """Lê o caminho do servidor do JSON de configuração, com fallback para env var."""
    if os.path.exists(APP_CONFIG_FILE):
        with open(APP_CONFIG_FILE, 'r', encoding='utf-8') as f:
            try:
                config = json.load(f)
                return config.get('server_dir')
            except json.JSONDecodeError:
                pass  # Ignora arquivo corrompido
    return os.environ.get('ACC_SERVER_DIR', os.path.join(app_path, 'server_dir'))

def save_server_dir(path):
    """Salva o caminho do servidor no JSON de configuração."""
    with open(APP_CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump({'server_dir': path}, f, indent=2)

app = Flask(__name__, static_folder=os.path.join(base_path, 'static'), template_folder=os.path.join(base_path, 'templates'))

# Configuração do diretório do servidor (pode ser definido via env ou fixo)
SERVER_DIR = get_server_dir()
CFG_DIR = os.path.join(SERVER_DIR, 'cfg')
PRESET_DIR = os.path.join(app_path, 'presets')
SESSION_TEMPLATES = SESSION_PRESETS

# Cria diretórios necessários
os.makedirs(CFG_DIR, exist_ok=True)
os.makedirs(PRESET_DIR, exist_ok=True)
os.makedirs(os.path.join(app.static_folder, 'images/tracks'), exist_ok=True)

# Variável global para manter o estado do processo do servidor
SERVER_PROCESS = None

def get_cfg_path(filename):
    """Caminho absoluto para arquivo na pasta cfg"""
    return os.path.join(CFG_DIR, filename)

def load_json(filename, default=None):
    """Carrega um JSON do cfg, retornando default se não existir"""
    path = get_cfg_path(filename)
    if os.path.exists(path):
        try:
            with codecs.open(path, 'r', encoding='utf-16-le') as f:
                return json.load(f)
        except:
            pass
    # Se não existe ou erro, cria com default
    if default is None:
        default = DEFAULT_CONFIG.get(filename, {})
    save_json(filename, default)
    return default

def save_json(filename, data):
    """Salva JSON no cfg, com backup automático"""
    path = get_cfg_path(filename)
    # Backup
    if os.path.exists(path):
        backup = path + f".backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(path, backup)
    # Salva com encoding UTF-16-LE e formatação limpa
    with codecs.open(path, 'w', encoding='utf-16-le') as f:
        json.dump(data, f, indent=2, ensure_ascii=False, separators=(',', ': '))
    return True

# ================== ROTAS PRINCIPAIS ==================

@app.route('/')
def index():
    return render_template('index.html', 
                           tracks=TRACKS, 
                           car_groups=CAR_GROUPS,
                           session_types=SESSION_TYPES,
                           weekdays=WEEKDAYS,
                           session_presets=SESSION_PRESETS,
                           session_preset_labels=SESSION_PRESET_LABELS)

@app.route('/api/config/<filename>', methods=['GET'])
def get_config(filename):
    allowed = ['configuration.json', 'settings.json', 'event.json', 'eventRules.json',
               'entrylist.json', 'assistRules.json', 'bop.json']
    if filename not in allowed:
        return jsonify({'error': 'Arquivo não permitido'}), 400
    data = load_json(filename)
    return jsonify(data)

@app.route('/api/config/<filename>', methods=['POST'])
def post_config(filename):
    allowed = ['configuration.json', 'settings.json', 'event.json', 'eventRules.json',
               'entrylist.json', 'assistRules.json', 'bop.json']
    if filename not in allowed:
        return jsonify({'error': 'Arquivo não permitido'}), 400
    
    data = request.json
    
    # Validações específicas
    if filename == 'configuration.json':
        if data.get('udpPort') == data.get('tcpPort'):
            return jsonify({'error': 'UDP e TCP ports não podem ser iguais'}), 400
        track_name = data.get('track', '')
        if track_name and track_name in TRACKS:
            max_pits = TRACKS[track_name]['pitboxes']
            if data.get('maxConnections', 0) > max_pits:
                return jsonify({'error': f'maxConnections ({data["maxConnections"]}) excede o máximo de pitboxes ({max_pits}) para {track_name}'}), 400
    
    # Validar SteamID em entrylist (se for o caso)
    if filename == 'entrylist.json':
        for entry in data.get('entries', []):
            for driver in entry.get('drivers', []):
                player_id = driver.get('playerID', '')
                if player_id and not player_id.startswith('S') or not len(player_id) == 18:
                    return jsonify({'error': f'SteamID inválida: {player_id}. Deve começar com "S" e ter 18 caracteres.'}), 400
    
    save_json(filename, data)
    return jsonify({'status': 'ok', 'message': f'{filename} salvo com sucesso!'})

@app.route('/api/tracks/images/<track_name>')
def track_image(track_name):
    """Serve imagem da pista, tentando PNG/JPG/SVG e usando um placeholder local ao final."""
    img_folder = os.path.join(app.static_folder, 'images/tracks')
    os.makedirs(img_folder, exist_ok=True)

    candidates = [
        f"{track_name}.png",
        f"{track_name}.jpg",
        f"{track_name}.jpeg",
        f"{track_name}.svg",
    ]

    img_path = None
    for candidate in candidates:
        for base_dir in [img_folder, os.path.join(img_folder, 'manual')]:
            full_path = os.path.join(base_dir, candidate)
            if os.path.exists(full_path):
                img_path = full_path
                break
        if img_path is not None:
            break

    if img_path is None:
        fallback_path = os.path.join(img_folder, 'placeholder.svg')
        if os.path.exists(fallback_path):
            img_path = fallback_path

    if img_path is None:
        return jsonify({'error': 'Imagem não encontrada'}), 404

    relative_path = os.path.relpath(img_path, img_folder)
    return send_from_directory(img_folder, relative_path)

@app.route('/api/server-info')
def server_info():
    """Retorna informações úteis sobre o diretório do servidor"""
    server_exe = os.path.join(SERVER_DIR, 'accServer.exe')
    cfg_exists = os.path.isdir(CFG_DIR)
    return jsonify({
        'server_dir': SERVER_DIR,
        'cfg_dir': CFG_DIR,
        'server_exe_exists': os.path.exists(server_exe),
        'cfg_exists': cfg_exists,
        'server_exe_path': server_exe,
        'session_templates': SESSION_PRESETS,
    })


@app.route('/api/apply-session-template', methods=['POST'])
def apply_session_template():
    data = request.json or {}
    preset_key = data.get('preset')
    if not preset_key or preset_key not in SESSION_PRESETS:
        return jsonify({'error': 'Preset inválido'}), 400
    sessions = build_session_plan(preset_key)
    return jsonify({'sessions': sessions})


@app.route('/api/start_server', methods=['POST'])
def start_server():
    """Inicia o servidor accServer.exe e armazena o processo."""
    global SERVER_PROCESS
    if SERVER_PROCESS and SERVER_PROCESS.poll() is None:
        return jsonify({'error': 'O servidor já está em execução.'}), 400

    server_exe = os.path.join(SERVER_DIR, 'accServer.exe')
    if not os.path.exists(server_exe):
        return jsonify({'error': 'accServer.exe não encontrado em ' + SERVER_DIR}), 404
    try:
        CREATE_NO_WINDOW = 0x08000000
        SERVER_PROCESS = subprocess.Popen([server_exe], cwd=SERVER_DIR, creationflags=CREATE_NO_WINDOW)
        return jsonify({'status': 'Servidor iniciado com sucesso!'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stop_server', methods=['POST'])
def stop_server():
    """Para o processo do servidor accServer.exe."""
    global SERVER_PROCESS
    if SERVER_PROCESS and SERVER_PROCESS.poll() is None:
        try:
            SERVER_PROCESS.terminate()
            SERVER_PROCESS.wait(timeout=5) # Espera o processo terminar
            SERVER_PROCESS = None
            return jsonify({'status': 'Servidor parado com sucesso!'})
        except subprocess.TimeoutExpired:
            SERVER_PROCESS.kill()
            SERVER_PROCESS = None
            return jsonify({'status': 'Servidor forçado a parar.'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    else:
        SERVER_PROCESS = None # Garante que está limpo se não estiver rodando
        return jsonify({'error': 'Servidor não está em execução.'}), 404

@app.route('/api/server_status', methods=['GET'])
def server_status():
    """Verifica e retorna o status do servidor."""
    global SERVER_PROCESS
    if SERVER_PROCESS and SERVER_PROCESS.poll() is None:
        return jsonify({'status': 'running'})
    else:
        # Limpa a variável se o processo morreu por conta própria
        SERVER_PROCESS = None
        return jsonify({'status': 'stopped'})


@app.route('/api/create_shortcut', methods=['POST'])
def create_shortcut():
    """Cria um atalho .bat na área de trabalho ou na pasta escolhida pelo usuário."""
    data = request.get_json(silent=True) or {}
    target_folder = (data.get('targetFolder') or '').strip()
    save_dir = target_folder or os.path.join(os.path.expanduser('~'), 'Desktop')
    os.makedirs(save_dir, exist_ok=True)
    bat_content = f"""@echo off
cd /d \"{SERVER_DIR}\"
echo Iniciando servidor ACC...
start accServer.exe
echo Servidor iniciado. Pressione qualquer tecla para fechar...
pause > nul
"""
    bat_path = os.path.join(save_dir, 'ACC_Server_Launcher.bat')
    with open(bat_path, 'w', encoding='utf-8') as f:
        f.write(bat_content)
    return jsonify({'status': f'Atalho criado em: {bat_path}'})

@app.route('/api/pick_server_dir', methods=['POST'])
def pick_server_dir():
    """Abre um diálogo para escolher a pasta do servidor."""
    if not tk:
        return jsonify({'error': 'Tkinter não está instalado. Seleção de pasta indisponível.'}), 500

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    
    dir_path = filedialog.askdirectory(title='Selecione a pasta raíz do seu ACC Dedicated Server')
    root.destroy()

    if not dir_path:
        return jsonify({'status': 'Nenhuma pasta selecionada.'})

    # Validação
    server_exe_path = os.path.join(dir_path, 'accServer.exe')
    server_subfolder_exe_path = os.path.join(dir_path, 'server', 'accServer.exe')

    final_path = None
    if os.path.exists(server_exe_path):
        final_path = dir_path
    elif os.path.exists(server_subfolder_exe_path):
        final_path = os.path.join(dir_path, 'server')
    
    if not final_path:
        return jsonify({'error': f'O arquivo "accServer.exe" não foi encontrado na pasta selecionada nem em sua subpasta "server": {dir_path}'}), 400

    save_server_dir(final_path)
    # Atualiza a variável global para refletir a mudança imediatamente
    global SERVER_DIR, CFG_DIR
    SERVER_DIR = final_path
    CFG_DIR = os.path.join(SERVER_DIR, 'cfg')
    os.makedirs(CFG_DIR, exist_ok=True)
    
    return jsonify({'status': f'Pasta do servidor atualizada com sucesso! O caminho foi ajustado para: {final_path}', 'path': final_path})


@app.route('/api/pick_entrylist_dir', methods=['POST'])
def pick_entrylist_dir():
    """Abre um diálogo para escolher a pasta para o entrylist centralizado."""
    if not tk:
        return jsonify({'error': 'Tkinter não está instalado. Seleção de pasta indisponível.'}), 500

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    
    dir_path = filedialog.askdirectory(title='Selecione a pasta contendo o entrylist.json centralizado')
    root.destroy()

    if not dir_path:
        return jsonify({'status': 'Nenhuma pasta selecionada.'})

    return jsonify({'status': 'Pasta selecionada.', 'path': dir_path})


@app.route('/api/create_shortcut_dialog', methods=['POST'])
def create_shortcut_dialog():
    """Abre um diálogo para escolher onde salvar o atalho."""
    if not tk:
        return jsonify({'error': 'Tkinter não está instalado. Criação de atalho indisponível.'}), 500

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    file_path = filedialog.asksaveasfilename(
        title='Salvar atalho do servidor como...',
        defaultextension=".bat",
        initialfile='ACC_Server_Launcher.bat',
        filetypes=[("Batch files", "*.bat"), ("All files", "*.*")]
    )
    root.destroy()
    
    if not file_path:
        return jsonify({'status': 'Criação de atalho cancelada.'})

    # Usa o SERVER_DIR atualizado
    bat_content = f"""@echo off
cd /d \"{SERVER_DIR}\"
echo Iniciando servidor ACC...
start accServer.exe
echo Servidor iniciado. Pressione qualquer tecla para fechar...
pause > nul
"""
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(bat_content)
        
    return jsonify({'status': f'Atalho criado em: {file_path}'})

@app.route('/api/save_entrylist_as', methods=['POST'])
def save_entrylist_as():
    """Abre um diálogo para escolher onde salvar o entrylist.json e salva."""
    if not tk:
        return jsonify({'error': 'Tkinter não está instalado. Salvar como indisponível.'}), 500

    data = request.json

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    
    file_path = filedialog.asksaveasfilename(
        title='Salvar Entry List como...',
        defaultextension=".json",
        initialfile='entrylist.json',
        filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
    )
    root.destroy()

    if not file_path:
        return jsonify({'status': 'Operação de salvar cancelada.'})

    try:
        with codecs.open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return jsonify({'status': 'ok', 'message': f'Entry list salva em: {file_path}'})
    except Exception as e:
        return jsonify({'error': f'Erro ao salvar entry list: {str(e)}'}), 500

# ================== PRESETS ==================

@app.route('/api/presets', methods=['GET'])
def list_presets():
    files = [f for f in os.listdir(PRESET_DIR) if f.endswith('.json')]
    return jsonify({'presets': files})

@app.route('/api/presets', methods=['POST'])
def save_preset():
    data = request.json
    name = data.get('name', 'unnamed').strip()
    if not name:
        return jsonify({'error': 'Nome do preset é obrigatório'}), 400
    # Extrai os arquivos de configuração do payload
    # Espera-se que venha um objeto com keys: configuration, settings, event, rules
    preset_data = {}
    for key in ['configuration', 'settings', 'event', 'rules', 'entrylist', 'assistRules', 'bop']:
        if key in data:
            preset_data[key] = data[key]
    if not preset_data:
        return jsonify({'error': 'Nenhum dado de configuração fornecido'}), 400
    path = os.path.join(PRESET_DIR, f"{name}.json")
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(preset_data, f, indent=2)
    return jsonify({'status': 'Preset salvo com sucesso!'})

@app.route('/api/presets/<name>', methods=['PUT'])
def load_preset(name):
    path = os.path.join(PRESET_DIR, f"{name}.json")
    if not os.path.exists(path):
        return jsonify({'error': 'Preset não encontrado'}), 404
    with open(path, 'r', encoding='utf-8') as f:
        preset = json.load(f)
    # Sobrescreve os arquivos
    mapping = {
        'configuration': 'configuration.json',
        'settings': 'settings.json',
        'event': 'event.json',
        'rules': 'eventRules.json',
        'entrylist': 'entrylist.json',
        'assistRules': 'assistRules.json',
        'bop': 'bop.json'
    }
    for key, filename in mapping.items():
        if key in preset:
            save_json(filename, preset[key])
    return jsonify({'status': 'Preset carregado com sucesso!'})

# ================== ROTA PARA LOGS (simples) ==================

@app.route('/api/logs')
def get_logs():
    """Retorna as últimas linhas do log do servidor (se existir)"""
    log_dir = os.path.join(SERVER_DIR, 'log')
    if not os.path.exists(log_dir):
        return jsonify({'logs': ['Nenhum log encontrado.']})
    # Pega o arquivo de log mais recente
    log_files = [f for f in os.listdir(log_dir) if f.endswith('.log')]
    if not log_files:
        return jsonify({'logs': ['Nenhum arquivo de log.']})
    latest = max(log_files, key=lambda f: os.path.getmtime(os.path.join(log_dir, f)))
    with open(os.path.join(log_dir, latest), 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()[-50:]  # últimas 50 linhas
    return jsonify({'logs': lines})

def open_browser():
    """Abre o navegador na página da aplicação."""
    webbrowser.open_new("http://127.0.0.1:5000")

if __name__ == '__main__':
    # Abre o navegador em uma thread separada para não bloquear a inicialização do servidor
    if not os.environ.get("WERKZEUG_RUN_MAIN"):
        threading.Timer(1, open_browser).start()
    
    # Inicia o servidor Flask
    app.run(host='127.0.0.1', port=5000, debug=False)