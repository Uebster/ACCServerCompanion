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

            // Verifica o status do servidor ao iniciar e a cada 5 segundos
            this.checkServerStatus();
            setInterval(() => this.checkServerStatus(), 5000);
        },
        checkServerStatus() {
            fetch('/api/server_status')
                .then(r => r.json())
                .then(data => {
                    this.serverStatus = data.status;
                });
        },
        load(filename) {
            this.fileStatus[filename] = 'loading';
            fetch('/api/config/' + filename)
                .then(r => {
                    if (!r.ok) {
                        throw new Error('Network response was not ok');
                    }
                    return r.json();
                })
                .then(data => {
                    this.fileStatus[filename] = 'loaded';
                    if (filename === 'configuration.json') {
                        this.config = data;
                        this.maxPits = this.config.maxConnections || 30;
                    } else if (filename === 'settings.json') {
                        this.settings = data;
                        // Garante que os valores de requisito existam para evitar 'undefined'
                        if (!('safetyRatingRequirement' in this.settings)) {
                            this.settings.safetyRatingRequirement = 0;
                        }
                        if (!('racecraftRatingRequirement' in this.settings)) {
                            this.settings.racecraftRatingRequirement = 0;
                        }
                    } else if (filename === 'event.json') {
                        this.event = data;
                        if (!this.event.sessions) this.event.sessions = [];
                        // Garante valores padrão para campos que podem estar ausentes
                        if (!('preRaceWaitingTimeSeconds' in this.event)) this.event.preRaceWaitingTimeSeconds = 80;
                        if (!('postQualySeconds' in this.event)) this.event.postQualySeconds = 15;
                        if (!('postRaceSeconds' in this.event)) this.event.postRaceSeconds = 15;
                        if (!('metaData' in this.event)) this.event.metaData = "";
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
                            stabilityControlLevelMax: 100,
                            tractionControl: -1,
                            abs: -1,
                            autoClutch: 0,
                            autoBlip: 0,
                            autoShift: 0,
                            idealLine: 0,
                            disableAutoLights: 0,
                            disableAutoWiper: 0,
                            disableAutoEngineStart: 0,
                            disableAutoPitLimiter: 0
                        };
                        // Garantir que a propriedade nova exista e remover a antiga
                        if (!('stabilityControlLevelMax' in this.assistRules)) {
                            this.assistRules.stabilityControlLevelMax = 100;
                        }
                        if ('stabilityControl' in this.assistRules) {
                            delete this.assistRules.stabilityControl;
                        }
                    } else if (filename === 'bop.json') {
                        this.bop = data && data.entries ? data : { entries: [] };
                    }
                });
        },
        loadServerInfo() {
            fetch('/api/server-info')
                .then(r => r.json())
                .then(data => {
                    this.server_dir_info = data;
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
            fetch('/api/pick_server_dir', { method: 'POST' })
                .then(r => r.json())
                .then(res => {
                    alert(res.status || res.error);
                    if (res.path) {
                        // Recarrega informações para refletir a mudança
                        this.loadServerInfo();
                        // O ideal seria forçar um recarregamento da página ou de todos os dados
                        window.location.reload();
                    }
                });
        },
        pickEntrylistDir() {
            fetch('/api/pick_entrylist_dir', { method: 'POST' })
                .then(r => r.json())
                .then(res => {
                    if (res.error) {
                        alert(res.error);
                    } else if (res.path) {
                        this.settings.centralEntryListPath = res.path;
                    }
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
                .then(res => {
                    if (res.error) {
                        alert('❌ Erro: ' + res.error);
                    } else {
                        alert('✅ ' + (res.status || 'Servidor iniciado!'));
                        this.serverStatus = 'running';
                    }
                });
        },
        stopServer() {
            fetch('/api/stop_server', { method: 'POST' })
                .then(r => r.json())
                .then(res => {
                    if (res.error) {
                        alert('❌ Erro: ' + res.error);
                    } else {
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
        saveEntryListAs() {
            fetch('/api/save_entrylist_as', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(this.entrylist)
            })
            .then(r => r.json())
            .then(res => {
                if (res.error) alert('❌ Erro: ' + res.error);
                else alert('✅ ' + res.message || 'Entry list salva com sucesso!');
            });
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