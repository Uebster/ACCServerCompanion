# ACC Server Manager

Ferramenta web para gerenciar servidores dedicados do **Assetto Corsa Competizione** (ACC).

## Objetivo

Simplificar a edição dos arquivos de configuração JSON do servidor, eliminando erros de sintaxe e facilitando a criação de eventos personalizados.

## Funcionalidades

- Editor visual para os arquivos:
  - `configuration.json` (rede)
  - `settings.json` (identificação e requisitos)
  - `event.json` (pista, clima, sessões)
  - `eventRules.json` (regras esportivas)
  - `entrylist.json`, `assistRules.json`, `bop.json` (avançado)
- Seletor de pistas com imagens e limite automático de pitboxes.
- Validações em tempo real (portas UDP/TCP, SteamID, limites de grid).
- Presets: salve e carregue configurações completas.
- Iniciador do servidor diretamente pela interface.
- Criação de atalho na área de trabalho (.bat).
- Tema escuro com cores neon.

## Estrutura de Pastas
acc-server-tool/
├── app.py # Backend Flask
├── acc_data.py # Dados estáticos (pistas, classes, defaults)
├── requirements.txt # Dependências
├── static/
│ ├── css/style.css # Estilos
│ ├── js/app.js # Lógica frontend (Alpine.js)
│ └── images/tracks/ # Miniaturas das pistas (baixadas sob demanda)
├── templates/
│ └── index.html # Página principal
├── presets/ # Presets salvos
└── server_dir/ # (configurável) Pasta onde está accServer.exe e cfg/
├── accServer.exe
└── cfg/ # Arquivos JSON editados

text

## Configuração

1. Instale as dependências:
   ```bash
   pip install -r requirements.txt
Defina a variável de ambiente ACC_SERVER_DIR com o caminho para a pasta do servidor ACC (onde está accServer.exe e a subpasta cfg). Exemplo:

Windows: set ACC_SERVER_DIR=C:\Steam\steamapps\common\Assetto Corsa Competizione\server

Linux/Mac: export ACC_SERVER_DIR=/caminho/para/server

Execute:

bash
python app.py
Acesse no navegador: http://localhost:5000

Uso
Navegue pelas abas para editar cada arquivo.

Preencha os campos; sliders e toggles atualizam os valores.

Clique em "Salvar" para gravar no arquivo (backup automático).

Use a seção "Avançado" para entrylist, assistRules e bop (em desenvolvimento).

Clique em "START SERVER" para iniciar o servidor.

Use "Criar Atalho" para gerar um .bat na área de trabalho.

Observações
O servidor deve estar parado ao editar os arquivos (salvo exceções).

Sempre faça backup dos seus arquivos antes de testar novas configurações.

As imagens das pistas são baixadas da internet na primeira visualização; você pode substituí-las manualmente em static/images/tracks/.

Próximos Passos (Melhorias)
Editor avançado para entrylist com busca por SteamID.

Terminal de logs do servidor em tempo real (WebSocket).

Suporte a múltiplos servidores.

Validação de BoP e ajustes finos.

Licença
MIT - Livre para uso e modificação.

text

---

## 7. Arquivo `requirements.txt`
Flask==2.3.2
requests==2.31.0

text

---

## Conclusão

Todos os arquivos necessários para a ferramenta foram fornecidos, incluindo a documentação. A estrutura está completa e pronta para uso. Você pode colocar o código nos respectivos arquivos e executar. A ferramenta cobre os principais arquivos de configuração, com validações e recursos extras (presets, atalho, iniciador). A interface com Alpine.js torna a edição dinâmica e interativa.

Agora é só testar com seu servidor ACC real! 🏁
