// static/js/app.js
function accApp() {
    return {
        activeTab: 'setup',
        showGuide: false,
        theme: localStorage.getItem('acc-theme') || 'dark',
        serverStatus: 'stopped', // 'running', 'stopped'
        fileStatus: {},
        server_dir_info: {},
        tracks: window.ACC_INITIAL_DATA?.tracks || {},
        carGroups: window.ACC_INITIAL_DATA?.carGroups || [],
        sessionPresets: window.ACC_INITIAL_DATA?.sessionPresets || {},
        sessionPresetLabels: window.ACC_INITIAL_DATA?.sessionPresetLabels || {},
        visibility: {
            password: false,
            spectatorPassword: false,
            adminPassword: false
        },
        config: {},
        settings: {},
        event: { sessions: [] },
        rules: {},
        entrylist: { entries: [] },
        assistRules: {},
        bop: { entries: [] },
        maxPits: 30,
        sessionTemplate: '',
        dirty: {
            'configuration.json': false,
            'settings.json': false,
            'event.json': false,
            'eventRules.json': false,
            'entrylist.json': false,
            'assistRules.json': false,
            'bop.json': false
        },

        init() {
            this.applyTheme();
            // Carrega todos os arquivos de configuração
            Object.keys(this.dirty).forEach(filename => this.load(filename));
            this.loadServerInfo();

            // Verifica o status do servidor ao iniciar e a cada 5 segundos
            this.checkServerStatus();
            setInterval(() => this.checkServerStatus(), 5000);

            // Observa alterações nos dados para marcar como 'dirty'
            this.$watch('config', () => this.dirty['configuration.json'] = true, { deep: true });
            this.$watch('settings', () => this.dirty['settings.json'] = true, { deep: true });
            this.$watch('event', () => this.dirty['event.json'] = true, { deep: true });
            this.$watch('rules', () => this.dirty['eventRules.json'] = true, { deep: true });
            this.$watch('entrylist', () => this.dirty['entrylist.json'] = true, { deep: true });
            this.$watch('assistRules', () => this.dirty['assistRules.json'] = true, { deep: true });
            this.$watch('bop', () => this.dirty['bop.json'] = true, { deep: true });
        },
        
        checkServerStatus() {
            fetch('/api/server_status')
                .then(r => r.json())
                .then(data => { this.serverStatus = data.status; });
        },

        load(filename) {
            this.fileStatus[filename] = 'loading';
            fetch('/api/config/' + filename)
                .then(r => r.ok ? r.json() : Promise.reject('Network response was not ok'))
                .then(data => {
                    this.fileStatus[filename] = 'loaded';
                    const modelMap = {
                        'configuration.json': 'config',
                        'settings.json': 'settings',
                        'event.json': 'event',
                        'eventRules.json': 'rules',
                        'entrylist.json': 'entrylist',
                        'assistRules.json': 'assistRules',
                        'bop.json': 'bop'
                    };
                    const modelName = modelMap[filename];
                    if (modelName) {
                        this[modelName] = data;

                        // Inicializa campos para evitar erros de 'undefined'
                        if (filename === 'event.json' && !this.event.sessions) this.event.sessions = [];
                        if (filename === 'entrylist.json' && !this.entrylist.entries) this.entrylist.entries = [];
                        if (filename === 'bop.json' && !this.bop.entries) this.bop.entries = [];
                        
                        // Após carregar, o estado não está mais 'dirty'
                        // Usamos um timeout para permitir que o DOM atualize antes de resetar o 'dirty' state
                        setTimeout(() => { this.dirty[filename] = false; }, 0);
                    }
                });
        },

        loadServerInfo() {
            fetch('/api/server-info')
                .then(r => r.json())
                .then(data => { this.server_dir_info = data; });
        },

        applyTheme() {
            document.body.classList.remove('theme-dark', 'theme-light');
            document.body.classList.add(this.theme === 'light' ? 'theme-light' : 'theme-dark');
        },

        toggleTheme() {
            this.theme = this.theme === 'dark' ? 'light' : 'dark';
            localStorage.setItem('acc-theme', this.theme);
            this.applyTheme();
        },

        togglePassword(field) {
            this.visibility[field] = !this.visibility[field];
        },
        
        openGuide() { this.showGuide = true; },
        closeGuide() { this.showGuide = false; },
        
        pickServerDir() {
            fetch('/api/pick_server_dir', { method: 'POST' })
                .then(r => r.json())
                .then(res => {
                    alert(res.status || res.error);
                    if (res.path) window.location.reload();
                });
        },

        pickEntrylistDir() {
            fetch('/api/pick_entrylist_dir', { method: 'POST' })
                .then(r => r.json())
                .then(res => {
                    if (res.error) alert(res.error);
                    else if (res.path) this.settings.centralEntryListPath = res.path;
                });
        },

        applySessionTemplate() {
            if (!this.sessionTemplate) return;
            fetch('/api/apply-session-template', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ preset: this.sessionTemplate })
            })
            .then(r => r.json())
            .then(res => {
                if (res.error) alert('❌ ' + res.error);
                else {
                    this.event.sessions = res.sessions;
                    alert('✅ Modelo aplicado. Ajuste durações e horários.');
                }
            });
        },
        
        save(filename, data) {
            return fetch('/api/config/' + filename, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            })
            .then(r => r.json())
            .then(res => {
                if (res.error) {
                    alert('❌ Erro ao salvar ' + filename + ': ' + res.error);
                    return Promise.reject(res.error);
                } else {
                    this.dirty[filename] = false;
                    return Promise.resolve(res);
                }
            });
        },

        saveAll() {
            const savePromises = [];
            let dirtyFilesFound = false;
            for (const filename in this.dirty) {
                if (this.dirty[filename]) {
                    dirtyFilesFound = true;
                    const modelMap = {
                        'configuration.json': this.config, 'settings.json': this.settings,
                        'event.json': this.event, 'eventRules.json': this.rules,
                        'entrylist.json': this.entrylist, 'assistRules.json': this.assistRules,
                        'bop.json': this.bop
                    };
                    savePromises.push(this.save(filename, modelMap[filename]));
                }
            }

            if (!dirtyFilesFound) {
                return Promise.resolve(); // Nenhuma alteração para salvar
            }

            return Promise.all(savePromises).then(() => {
                alert('✅ Todas as alterações foram salvas!');
            }).catch(() => {
                alert('❌ Ocorreu um erro ao salvar um ou mais arquivos.');
            });
        },
        
        startServer() {
            const unsavedFiles = Object.keys(this.dirty).filter(f => this.dirty[f]);
            
            const doStart = () => {
                fetch('/api/start_server', { method: 'POST' })
                    .then(r => r.json())
                    .then(res => {
                        if (res.error) alert('❌ Erro: ' + res.error);
                        else {
                            alert('✅ ' + (res.status || 'Servidor iniciado!'));
                            this.serverStatus = 'running';
                        }
                    });
            };

            if (unsavedFiles.length > 0) {
                if (confirm('Você tem alterações não salvas. Deseja salvar tudo antes de iniciar o servidor?')) {
                    this.saveAll().then(doStart);
                } else {
                    doStart();
                }
            } else {
                doStart();
            }
        },

        // Métodos auxiliares para manipulação de listas
        selectTrack(key) {
            this.event.track = key;
            this.maxPits = this.tracks[key].pitboxes;
            if (this.config.maxConnections > this.maxPits) {
                this.config.maxConnections = this.maxPits;
            }
        },
        addSession() { this.event.sessions.push({ sessionType: 'P', sessionDurationMinutes: 20, hourOfDay: 10, dayOfWeekend: 1, timeMultiplier: 1 }); },
        removeSession(idx) { this.event.sessions.splice(idx, 1); },
        addEntryListEntry() { if (!this.entrylist.entries) this.entrylist.entries = []; this.entrylist.entries.push({ name: '', playerID: '', team: '', isAdmin: false }); },
        removeEntryListEntry(idx) { this.entrylist.entries.splice(idx, 1); },
        addBopEntry() { if (!this.bop.entries) this.bop.entries = []; this.bop.entries.push({ carClass: '', powerAdjustment: 0, weightAdjustment: 0 }); },
        removeBopEntry(idx) { this.bop.entries.splice(idx, 1); },

        // Outros métodos
        stopServer() {
            fetch('/api/stop_server', { method: 'POST' })
                .then(r => r.json())
                .then(res => {
                    if (res.error) alert('❌ Erro: ' + res.error);
                    else {
                        alert('✅ ' + (res.status || 'Servidor parado!'));
                        this.serverStatus = 'stopped';
                    }
                });
        },
        createShortcut() {
            fetch('/api/create_shortcut_dialog', { method: 'POST' })
                .then(r => r.json())
                .then(res => alert(res.status || res.error));
        },
        savePreset() {
            const name = prompt('Nome do preset:');
            if (!name) return;
            const payload = {
                name: name,
                configuration: this.config, settings: this.settings, event: this.event,
                rules: this.rules, entrylist: this.entrylist, assistRules: this.assistRules, bop: this.bop
            };
            fetch('/api/presets', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })
                .then(r => r.json())
                .then(res => alert(res.status || res.error));
        },
        saveEntryListAs() {
            fetch('/api/save_entrylist_as', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(this.entrylist) })
                .then(r => r.json())
                .then(res => {
                    if (res.error) alert('❌ Erro: ' + res.error);
                    else alert('✅ ' + res.message || 'Entry list salva!');
                });
        },
        loadPreset() {
            fetch('/api/presets')
                .then(r => r.json())
                .then(data => {
                    if (!data.presets || data.presets.length === 0) {
                        alert('Nenhum preset encontrado.'); return;
                    }
                    const name = prompt(`Digite o nome do preset a carregar:\n${data.presets.join('\n')}`);
                    if (!name) return;
                    fetch('/api/presets/' + name, { method: 'PUT' })
                        .then(r => r.json())
                        .then(res => {
                            alert(res.status || res.error);
                            Object.keys(this.dirty).forEach(filename => this.load(filename)); // Recarrega tudo
                        });
                });
        }
    };
}
