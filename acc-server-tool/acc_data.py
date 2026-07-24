# acc_data.py - Dados estáticos para o gerenciador de servidor ACC

# Dados das pistas: nome técnico, pitboxes, label, imagem
TRACKS = {
    "monza": {"label": "Monza", "pitboxes": 29, "year_suffix": "2018"},
    "monza_2019": {"label": "Monza (2019)", "pitboxes": 29},
    "monza_2020": {"label": "Monza (2020)", "pitboxes": 29},
    "zolder": {"label": "Zolder", "pitboxes": 34},
    "brands_hatch": {"label": "Brands Hatch", "pitboxes": 32},
    "silverstone": {"label": "Silverstone", "pitboxes": 36},
    "paul_ricard": {"label": "Paul Ricard", "pitboxes": 33},
    "misano": {"label": "Misano", "pitboxes": 30},
    "spa": {"label": "Spa-Francorchamps", "pitboxes": 82},
    "nurburgring": {"label": "Nürburgring", "pitboxes": 30},
    "barcelona": {"label": "Barcelona", "pitboxes": 29},
    "hungaroring": {"label": "Hungaroring", "pitboxes": 27},
    "zandvoort": {"label": "Zandvoort", "pitboxes": 25},
    "kyalami": {"label": "Kyalami", "pitboxes": 40},
    "mount_panorama": {"label": "Mount Panorama", "pitboxes": 36},
    "suzuka": {"label": "Suzuka", "pitboxes": 51},
    "laguna_seca": {"label": "Laguna Seca", "pitboxes": 30},
    "imola": {"label": "Imola", "pitboxes": 30},
    "oulton_park": {"label": "Oulton Park", "pitboxes": 28},
    "donington": {"label": "Donington", "pitboxes": 37},
    "snetterton": {"label": "Snetterton", "pitboxes": 26},
    "cota": {"label": "COTA", "pitboxes": 30},
    "indianapolis": {"label": "Indianapolis", "pitboxes": 30},
    "watkins_glen": {"label": "Watkins Glen", "pitboxes": 30},
    "valencia": {"label": "Valencia", "pitboxes": 29},
    "nurburgring_24h": {"label": "Nürburgring 24h", "pitboxes": 50},
}

# Classes de carros permitidas
CAR_GROUPS = [
    "GT3", "GT4", "GTC", "TCX", "Cup", "ST", "GT2", "CHL", "FreeForAll"
]

# Mapeamento de tipos de sessão
SESSION_TYPES = {
    "Practice": "P",
    "Qualify": "Q",
    "Race": "R"
}
SESSION_TYPES_REV = {v: k for k, v in SESSION_TYPES.items()}

# Dias da semana (1=Friday, 2=Saturday, 3=Sunday)
WEEKDAYS = {1: "Sexta", 2: "Sábado", 3: "Domingo"}
WEEKDAYS_REV = {v: k for k, v in WEEKDAYS.items()}

# Configurações padrão para arquivos
DEFAULT_CONFIG = {
    "configuration.json": {
        "udpPort": 9201,
        "tcpPort": 9201,
        "maxConnections": 30,
        "lanDiscovery": 1,
        "registerToLobby": 1,
        "configVersion": 1
    },
    "settings.json": {
        "serverName": "Meu Servidor ACC",
        "password": "",
        "adminPassword": "admin123",
        "carGroup": "GT3",
        "trackMedalsRequirement": 0,
        "safetyRatingRequirement": 0,
        "isRaceLocked": 0,
        "randomizeTrackWhenEmpty": 0,
        "allowAutoDQ": 1,
        "shortFormationLap": 1,
        "dumpEntryList": 0,
        "formationLapType": 3,
        "ignorePrematureDisconnects": 1,
        "configVersion": 1
    },
    "event.json": {
        "track": "monza",
        "preRaceWaitingTimeSeconds": 60,
        "sessionOverTimeSeconds": 120,
        "ambientTemp": 26,
        "cloudLevel": 0.3,
        "rain": 0.0,
        "weatherRandomness": 3,
        "configVersion": 1,
        "sessions": [
            {
                "hourOfDay": 10,
                "dayOfWeekend": 1,
                "timeMultiplier": 1,
                "sessionType": "P",
                "sessionDurationMinutes": 20
            },
            {
                "hourOfDay": 14,
                "dayOfWeekend": 1,
                "timeMultiplier": 1,
                "sessionType": "Q",
                "sessionDurationMinutes": 15
            },
            {
                "hourOfDay": 16,
                "dayOfWeekend": 1,
                "timeMultiplier": 1,
                "sessionType": "R",
                "sessionDurationMinutes": 30
            }
        ]
    },
    "eventRules.json": {
        "qualifyStandingType": 1,
        "pitwindowLengthSec": -1,
        "driverStintTimeSec": -1,
        "mandatoryPitstopCount": 0,
        "maxTotalDrivingTime": -1,
        "maxDriversCount": 1,
        "isRefuellingAllowedInRace": True,
        "isRefuellingTimeFixed": False,
        "isMandatoryPitstopRefuellingRequired": False,
        "isMandatoryPitstopTypeChangeRequired": False,
        "isMandatoryPitstopSwapDriverRequired": False,
        "tyreSetCount": 50,
        "configVersion": 1
    }
}