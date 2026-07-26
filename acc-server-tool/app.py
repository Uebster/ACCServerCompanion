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
    """Lê o caminho do servidor do JSON de configuração."""
    if os.path.exists(APP_CONFIG_FILE):
        with open(APP_CONFIG_FILE, 'r', encoding='utf-8') as f:
            try:
                config = json.load(f)
                return config.get('server_dir')
            except json.JSONDecodeError:
                pass  # Ignora arquivo corrompido
    return None

def save_server_dir(path):
    """Salva o caminho do servidor no JSON de configuração."""
    with open(APP_CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump({'server_dir': path}, f, indent=2)

app = Flask(__name__, static_folder=os.path.join(base_path, 'static'), template_folder=os.path.join(base_path, 'templates'))

# Configuração do diretório do servidor será carregada dinamicamente
SERVER_DIR = None
CFG_DIR = None
PRESET_DIR = os.path.join(app_path, 'presets')
SESSION_TEMPLATES = SESSION_PRESETS

# Cria diretórios necessários
os.makedirs(PRESET_DIR, exist_ok=True)
os.makedirs(os.path.join(app.static_folder, 'images/tracks'), exist_ok=True)

# Variável global para manter o estado do processo do servidor
SERVER_PROCESS = None

def get_validated_cfg_dir():
    """Busca o server_dir, valida (procurando accServer.exe) e retorna o caminho para a pasta cfg.
    
    Raises:
        ValueError: Se o diretório do servidor não for válido ou não estiver configurado.
    """
    server_dir = get_server_dir()
    if not server_dir or not os.path.exists(os.path.join(server_dir, 'accServer.exe')):
        raise ValueError("O diretório do servidor do ACC não está configurado ou é inválido.")
    
    cfg_dir = os.path.join(server_dir, 'cfg')
    os.makedirs(cfg_dir, exist_ok=True)
    return cfg_dir

def load_json(filename, default=None):
    """Carrega um JSON do cfg, retornando default se não existir"""
    try:
        cfg_dir = get_validated_cfg_dir()
        path = os.path.join(cfg_dir, filename)
    except ValueError:
        # Se o diretório não é válido, não podemos carregar, mas também não devemos criar um novo.
        # Retorna o default para a UI não quebrar.
        return default or DEFAULT_CONFIG.get(filename, {})

    if os.path.exists(path):
        try:
            with codecs.open(path, 'r', encoding='utf-16-le') as f:
                return json.load(f)
        except Exception:
            # Em caso de erro de leitura, tenta ler um backup recente se houver
            pass
    
    # Se não existe ou erro, cria com default
    if default is None:
        default = DEFAULT_CONFIG.get(filename, {})
    
    # Não salva automaticamente se o diretório não for válido na chamada.
    # A UI tentará salvar e receberá o erro de diretório inválido.
    try:
        save_json(filename, default)
    except ValueError:
        # Silencia o erro aqui, pois a UI será notificada ao tentar salvar.
        pass

    return default

def save_json(filename, data):
    """Salva JSON no cfg, com backup automático e validação de diretório"""
    cfg_dir = get_validated_cfg_dir()  # Isso vai levantar ValueError se o diretório for inválido
    path = os.path.join(cfg_dir, filename)
    
    # Backup
    if os.path.exists(path):
        backup_dir = os.path.join(cfg_dir, 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        backup_filename = f"{filename.replace('.json', '')}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        backup_path = os.path.join(backup_dir, backup_filename)
        shutil.copy2(path, backup_path)
        
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
    
    try:
        save_json(filename, data)
        return jsonify({'status': 'ok', 'message': f'{filename} salvo com sucesso!'})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

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
    server_dir = get_server_dir()
    if not server_dir:
        return jsonify({
            'server_dir': '',
            'cfg_dir': '',
            'server_exe_exists': False,
            'cfg_exists': False,
            'server_exe_path': '',
            'session_templates': SESSION_PRESETS,
        })

    server_exe = os.path.join(server_dir, 'accServer.exe')
    cfg_dir = os.path.join(server_dir, 'cfg')
    return jsonify({
        'server_dir': server_dir,
        'cfg_dir': cfg_dir,
        'server_exe_exists': os.path.exists(server_exe),
        'cfg_exists': os.path.isdir(cfg_dir),
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

    server_dir = get_server_dir()
    if not server_dir:
        return jsonify({'error': 'O diretório do servidor do ACC não está configurado.'}), 400

    server_exe = os.path.join(server_dir, 'accServer.exe')
    if not os.path.exists(server_exe):
        return jsonify({'error': f'accServer.exe não encontrado em {server_dir}'}), 404
    
    try:
        CREATE_NO_WINDOW = 0x08000000
        SERVER_PROCESS = subprocess.Popen([server_exe], cwd=server_dir, creationflags=CREATE_NO_WINDOW)
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


@app.route('/api/create_shortcut_dialog', methods=['POST'])
def create_shortcut_dialog():
    """Abre um diálogo para escolher onde salvar o atalho."""
    server_dir = get_server_dir()
    if not server_dir:
        return jsonify({'error': 'O diretório do servidor do ACC não está configurado.'}), 400

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

    bat_content = f"""@echo off
cd /d \"{server_dir}\"
echo Iniciando servidor ACC...
start accServer.exe
echo Servidor iniciado. Pressione qualquer tecla para fechar...
pause > nul
"""
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(bat_content)
        
    return jsonify({'status': f'Atalho criado em: {file_path}'})

@app.route('/api/pick_server_dir', methods=['POST'])
def pick_server_dir():
    """Abre um diálogo para escolher a pasta do servidor e procura o accServer.exe."""
    if not tk:
        return jsonify({'error': 'Tkinter não está instalado. Seleção de pasta indisponível.'}), 500

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    
    initial_dir = get_server_dir() # Começa do diretório já configurado, se houver
    dir_path = filedialog.askdirectory(
        title='Selecione a pasta raíz do seu ACC Dedicated Server',
        initialdir=initial_dir
    )
    root.destroy()

    if not dir_path:
        return jsonify({'status': 'Nenhuma pasta selecionada.'})

    # Procura pelo accServer.exe de forma inteligente
    found_path = None
    # 1. Checa o diretório selecionado
    if os.path.exists(os.path.join(dir_path, 'accServer.exe')):
        found_path = dir_path
    else:
        # 2. Se não encontrou, procura em subdiretórios (até 2 níveis de profundidade)
        for root_dir, dirs, files in os.walk(dir_path):
            if 'accServer.exe' in files:
                found_path = root_dir
                break # Para no primeiro que encontrar
            # Limita a profundidade
            if root_dir.count(os.sep) - dir_path.count(os.sep) >= 2:
                dirs[:] = [] # Não entra mais em subdiretórios
    
    if not found_path:
        return jsonify({'error': f'O "accServer.exe" não foi encontrado na pasta selecionada ou em seus subdiretórios: {dir_path}'}), 400

    save_server_dir(found_path)
    
    return jsonify({'status': f'Pasta do servidor atualizada com sucesso!', 'path': found_path})


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
    server_dir = get_server_dir()
    if not server_dir:
        return jsonify({'logs': ['O diretório do servidor não está configurado.']})

    log_dir = os.path.join(server_dir, 'log')
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