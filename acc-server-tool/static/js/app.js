// static/js/app.js
function accApp() {
    return {
        activeTab: 'network',
        tracks: {{ tracks|tojson|safe }},
        carGroups: {{ car_groups|tojson|safe }},
        config: {},
        settings: {},
        event: { sessions: [] },
        rules: {},
        maxPits: 30,
        init() {
            this.load('configuration.json');
            this.load('settings.json');
            this.load('event.json');
            this.load('eventRules.json');
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
        imgError(event) {
            event.target.src = 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxMDAiIGhlaWdodD0iMTAwIiB2aWV3Qm94PSIwIDAgMTAwIDEwMCI+PHJlY3Qgd2lkdGg9IjEwMCUiIGhlaWdodD0iMTAwJSIgZmlsbD0iIzFhMWExYSIvPjx0ZXh0IHg9IjUwIiB5PSI1MCIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjEwIiBmaWxsPSIjY2NjIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBkeT0iLjNlbSI+SW1hZ2VuPC90ZXh0Pjwvc3ZnPg==';
        },
        startServer() {
            fetch('/api/start_server', { method: 'POST' })
                .then(r => r.json())
                .then(res => alert(res.status || res.error));
        },
        createShortcut() {
            fetch('/api/create_shortcut', { method: 'POST' })
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
                rules: this.rules
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
                    });
                });
        }
    };
}