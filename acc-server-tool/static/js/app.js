// static/js/app.js
function accApp() {
    return {
        activeTab: 'network',
        showGuide: false,
        theme: localStorage.getItem('acc-theme') || 'dark',
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
        assistRules: {
            tractionControl: true,
            abs: true,
            stabilityControl: true,
            autoClutch: false,
            autoBlip: false,
            autoShift: false,
            idealLine: false
        },
        bop: { entries: [] },
        maxPits: 30,
        sessionTemplate: '',
        init() {
            this.applyTheme();
            this.load('configuration.json');
            this.load('settings.json');
            this.load('event.json');
            this.load('eventRules.json');
            this.load('entrylist.json');
            this.load('assistRules.json');
            this.load('bop.json');
            this.loadServerInfo();
        },
        load(filename) {
            fetch('/api/config/' + filename)
                .then(r => r.json())
                .then(data => {
                    if (filename === 'configuration.json') {
                        this.config = data;
                        this.maxPits = this.config.maxConnections || 30;
                    } else if (filename === 'settings.json') {
                        this.settings = data;
                    } else if (filename === 'event.json') {
                        this.event = data;
                        if (!this.event.sessions) this.event.sessions = [];
                        // Atualiza maxPits se track selecionada
                        if (this.event.track && this.tracks[this.event.track]) {
                            this.maxPits = this.tracks[this.event.track].pitboxes;
                        }
                    } else if (filename === 'eventRules.json') {
                        this.rules = data;
                    } else if (filename === 'entrylist.json') {
                        this.entrylist = data && data.entries ? data : { entries: [] };
                    } else if (filename === 'assistRules.json') {
                        this.assistRules = data && Object.keys(data).length ? data : {
                            tractionControl: true,
                            abs: true,
                            stabilityControl: true,
                            autoClutch: false,
                            autoBlip: false,
                            autoShift: false,
                            idealLine: false
                        };
                    } else if (filename === 'bop.json') {
                        this.bop = data && data.entries ? data : { entries: [] };
                    }
                });
        },
        loadServerInfo() {
            fetch('/api/server-info')
                .then(r => r.json())
                .then(data => {
                    if (!data.server_exe_exists) {
                        alert('⚠️ Pasta do servidor não encontrada ou accServer.exe não foi localizado. Use “Escolher pasta do servidor” para apontar o diretório correto.');
                    }
                });
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
        openGuide() {
            this.showGuide = true;
        },
        closeGuide() {
            this.showGuide = false;
        },
        pickServerDir() {
            const path = prompt('Cole o caminho completo da pasta do servidor ACC (aquela que contém accServer.exe e a subpasta cfg):');
            if (!path) return;
            alert('⚠️ Para este protótipo, o caminho precisa ser definido via variável de ambiente ACC_SERVER_DIR. O app foi preparado para isso.');
            alert('Exemplo no Windows: set ACC_SERVER_DIR=C:\\Steam\\steamapps\\common\\Assetto Corsa Competizione\\server');
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
                    alert('✅ Modelo aplicado. Ajuste as durações e horários conforme quiser.');
                }
            });
        },
        save(filename, data) {
            fetch('/api/config/' + filename, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            })
            .then(r => r.json())
            .then(res => {
                if (res.error) alert('❌ Erro: ' + res.error);
                else alert('✅ ' + res.message || 'Salvo com sucesso!');
            });
        },
        saveAndStart(filename, data) {
            const confirmStart = confirm('⚠️ Antes de iniciar, confira se o servidor está parado e se as configurações estão corretas. Deseja salvar e iniciar agora?');
            if (!confirmStart) return;
            fetch('/api/config/' + filename, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            })
            .then(r => r.json())
            .then(res => {
                if (res.error) {
                    alert('❌ Erro: ' + res.error);
                    return;
                }
                alert('✅ Configuração salva. Agora iniciando o servidor...');
                this.startServer();
            });
        },
        selectTrack(key) {
            this.event.track = key;
            this.maxPits = this.tracks[key].pitboxes;
            if (this.config.maxConnections > this.maxPits) {
                this.config.maxConnections = this.maxPits;
            }
        },
        addSession() {
            this.event.sessions.push({
                sessionType: 'P',
                sessionDurationMinutes: 20,
                hourOfDay: 10,
                dayOfWeekend: 1,
                timeMultiplier: 1
            });
        },
        removeSession(idx) {
            this.event.sessions.splice(idx, 1);
        },
        addEntryListEntry() {
            if (!this.entrylist.entries) this.entrylist.entries = [];
            this.entrylist.entries.push({ name: '', playerID: '', team: '', isAdmin: false });
        },
        removeEntryListEntry(idx) {
            this.entrylist.entries.splice(idx, 1);
        },
        addBopEntry() {
            if (!this.bop.entries) this.bop.entries = [];
            this.bop.entries.push({ carClass: '', powerAdjustment: 0, weightAdjustment: 0 });
        },
        removeBopEntry(idx) {
            this.bop.entries.splice(idx, 1);
        },
        imgError(event) {
            event.target.src = 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxMDAiIGhlaWdodD0iMTAwIiB2aWV3Qm94PSIwIDAgMTAwIDEwMCI+PHJlY3Qgd2lkdGg9IjEwMCUiIGhlaWdodD0iMTAwJSIgZmlsbD0iIzFhMWExYSIvPjx0ZXh0IHg9IjUwIiB5PSI1MCIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjEwIiBmaWxsPSIjY2NjIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBkeT0iLjNlbSI+SW1hZ2VuPC90ZXh0Pjwvc3ZnPg==';
        },
        startServer() {
            fetch('/api/start_server', { method: 'POST' })
                .then(r => r.json())
                .then(res => alert(res.status || res.error));
        },
        createShortcut() {
            const targetFolder = prompt('Onde você quer salvar o atalho? Deixe em branco para usar a área de trabalho.\nExemplo: C:\\Users\\SeuNome\\Documents\\ACC');
            fetch('/api/create_shortcut', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ targetFolder: targetFolder || '' })
            })
            .then(r => r.json())
            .then(res => alert(res.status || res.error));
        },
        savePreset() {
            const name = prompt('Nome do preset:');
            if (!name) return;
            // Monta objeto com todos os dados atuais
            const payload = {
                name: name,
                configuration: this.config,
                settings: this.settings,
                event: this.event,
                rules: this.rules,
                entrylist: this.entrylist,
                assistRules: this.assistRules,
                bop: this.bop
            };
            fetch('/api/presets', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            })
            .then(r => r.json())
            .then(res => alert(res.status || res.error));
        },
        loadPreset() {
            fetch('/api/presets')
                .then(r => r.json())
                .then(data => {
                    if (!data.presets || data.presets.length === 0) {
                        alert('Nenhum preset encontrado.');
                        return;
                    }
                    const name = prompt('Digite o nome do preset a carregar:\n' + data.presets.join('\n'));
                    if (!name) return;
                    fetch('/api/presets/' + name, {
                        method: 'PUT'
                    })
                    .then(r => r.json())
                    .then(res => {
                        alert(res.status || res.error);
                        // Recarrega tudo
                        this.load('configuration.json');
                        this.load('settings.json');
                        this.load('event.json');
                        this.load('eventRules.json');
                        this.load('entrylist.json');
                        this.load('assistRules.json');
                        this.load('bop.json');
                    });
                });
        }
    };
}