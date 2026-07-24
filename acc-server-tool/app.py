# app.py - Backend Flask com todas as rotas

import os
import json
import codecs
import shutil
import datetime
import subprocess
import requests
from flask import Flask, render_template, request, jsonify, send_from_directory
from acc_data import TRACKS, CAR_GROUPS, SESSION_TYPES, SESSION_TYPES_REV, WEEKDAYS, DEFAULT_CONFIG

app = Flask(__name__)

# Configuração do diretório do servidor (pode ser definido via env ou fixo)
SERVER_DIR = os.environ.get('ACC_SERVER_DIR', './server_dir')
CFG_DIR = os.path.join(SERVER_DIR, 'cfg')
PRESET_DIR = './presets'

# Cria diretórios necessários
os.makedirs(CFG_DIR, exist_ok=True)
os.makedirs(PRESET_DIR, exist_ok=True)
os.makedirs(os.path.join(app.static_folder, 'images/tracks'), exist_ok=True)

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
                           weekdays=WEEKDAYS)

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
    """Serve imagem da pista (baixa se não existir)"""
    img_folder = os.path.join(app.static_folder, 'images/tracks')
    img_path = os.path.join(img_folder, f"{track_name}.jpg")
    
    if not os.path.exists(img_path):
        # Tenta baixar de uma fonte (substitua pela URL real das imagens)
        url = f"https://www.assettocorsa.net/acc/wp-content/uploads/tracks/{track_name}.jpg"
        try:
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                with open(img_path, 'wb') as f:
                    f.write(r.content)
            else:
                # Placeholder (cria imagem vazia ou usa fallback)
                # Vamos usar um placeholder: copiar uma imagem genérica se existir
                fallback = os.path.join(img_folder, 'placeholder.jpg')
                if os.path.exists(fallback):
                    shutil.copy2(fallback, img_path)
        except:
            pass
    
    # Se ainda não existe, retorna 404
    if not os.path.exists(img_path):
        return jsonify({'error': 'Imagem não encontrada'}), 404
    
    return send_from_directory(img_folder, f"{track_name}.jpg")

@app.route('/api/start_server', methods=['POST'])
def start_server():
    """Inicia o servidor accServer.exe"""
    server_exe = os.path.join(SERVER_DIR, 'accServer.exe')
    if not os.path.exists(server_exe):
        return jsonify({'error': 'accServer.exe não encontrado em ' + SERVER_DIR}), 404
    try:
        # Inicia em subprocess (detached)
        subprocess.Popen([server_exe], cwd=SERVER_DIR, shell=True,
                         creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP)
        return jsonify({'status': 'Servidor iniciado com sucesso!'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/create_shortcut', methods=['POST'])
def create_shortcut():
    """Cria um atalho .bat na área de trabalho para iniciar o servidor"""
    desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
    bat_content = f"""@echo off
cd /d "{SERVER_DIR}"
echo Iniciando servidor ACC...
start accServer.exe
echo Servidor iniciado. Pressione qualquer tecla para fechar...
pause > nul
"""
    bat_path = os.path.join(desktop, 'ACC_Server_Launcher.bat')
    with open(bat_path, 'w', encoding='utf-8') as f:
        f.write(bat_content)
    return jsonify({'status': f'Atalho criado em: {bat_path}'})

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
    for key in ['configuration', 'settings', 'event', 'rules']:
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
        'rules': 'eventRules.json'
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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)