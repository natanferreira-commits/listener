# arena-listener

Bot listener que monitora canal publico de Telegram e registra mensagens com links de casas de apostas numa planilha Google Sheets.

## Como funciona

1. Usa **Telethon** logado com sua conta de usuario (numero secundario) pra ler mensagens em tempo real do canal alvo.
2. Quando chega uma mensagem nova com URL, extrai os links e tenta matchear o dominio com a aba "Repo de Links" da planilha.
3. Se a casa for reconhecida, escreve uma linha na aba "Links Nao Trackeados" com: data/hora, canal, deeplink da mensagem, conteudo, URL, casa, status "Pendente".
4. Sem deduplicacao — humano resolve depois.

## Setup (passo a passo)

### 1. Preencher o `.env`

Copia o template e preenche:

```bash
cp .env.example .env
```

Edita `.env` e coloca:

- `API_ID` e `API_HASH` — gerados em https://my.telegram.org -> App configuration
- `TELEGRAM_PHONE` — numero da conta secundaria com codigo do pais (ex: `+5511999999999`)
- `TARGET_CHANNEL` — username do canal (sem `@`) ou link `https://t.me/...`. Pra teste inicial, usa um canal de teste seu.
- `GOOGLE_CREDS_PATH` — caminho do JSON da Service Account do Google (ver passo 2)
- `SHEET_ID` — ja preenchido com a planilha do Erick

### 2. Service Account do Google

A planilha precisa de uma Service Account com permissao de edicao.

1. Acessa https://console.cloud.google.com/
2. Cria um projeto (ou usa um existente)
3. Habilita as APIs: **Google Sheets API** e **Google Drive API**
4. Em "IAM e administrador" -> "Contas de servico" -> "Criar conta de servico"
5. Da um nome qualquer (ex: `arena-listener-bot`)
6. Apos criar, clica nela -> aba "Chaves" -> "Adicionar chave" -> "JSON" -> baixa o arquivo
7. Renomeia o JSON pra `credentials.json` e coloca na raiz do projeto
8. Abre o JSON e copia o email `client_email` (algo tipo `arena-listener-bot@projeto.iam.gserviceaccount.com`)
9. Abre a planilha no Sheets -> "Compartilhar" -> cola o email com permissao de **Editor**

### 3. Instalar dependencias

Ja feito durante o setup, mas se precisar rodar de novo:

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
# ou: source .venv/bin/activate # Linux
pip install -r requirements.txt
```

### 4. Primeiro login do Telethon

Na primeira execucao, o Telethon vai pedir interativamente:

- Codigo enviado via Telegram pra sua conta
- Senha 2FA, se voce tiver ativada

Depois disso, ele cria um arquivo `arena_listener.session` que persiste o login. Proximas execucoes nao pedem nada.

### 5. Verificar quais canais sua conta enxerga

Antes de apontar pro canal real, roda em modo de listagem pra confirmar que o canal alvo aparece:

```bash
.venv\Scripts\python.exe main.py --list
```

Isso loga todos os canais/grupos da sua conta com nome, username e id. Procura o do Caumo e copia o username (ou id) pro `.env`.

### 6. Rodar o listener

```bash
.venv\Scripts\python.exe main.py
```

Logs vao pro stdout e tambem pra `logs/listener.log` (rotativo).

## Estrutura

```
arena-listener/
  .env.example           # template de variaveis
  .env                   # suas credenciais (NAO commitar)
  credentials.json       # Service Account do Google (NAO commitar)
  requirements.txt
  main.py                # entrypoint
  utils/
    telegram_client.py   # wrapper Telethon, deeplinks
    sheet_writer.py      # escrita na planilha + load houses
    link_extractor.py    # regex de URL e match com casa
  logs/                  # rotating log files
```

## Aba "Repo de Links" (formato esperado)

A primeira coluna eh o nome da casa. Da coluna B em diante, voce coloca os dominios/keywords associados. Exemplo:

| A (Casa)     | B          | C            |
|--------------|------------|--------------|
| BetMGM       | betmgm.com |              |
| EsportivaBet | esportivabet.com | esportiva.bet |
| Stake        | stake.com  | stake.bet    |

Se nao tiver dominio em B, o codigo usa o nome da casa em lowercase como keyword (ex: `Stake` -> procura `stake` na URL).

Se a aba estiver vazia ou der erro, ele cai num fallback hardcoded com BetMGM, EsportivaBet, Novibet, Sportingbet, Stake.

## Troubleshooting

- **`SpreadsheetNotFound` ou `403`**: voce esqueceu de compartilhar a planilha com o email da Service Account.
- **`PhoneCodeInvalid`**: codigo errado no primeiro login. Roda de novo.
- **Bot nao recebe mensagens**: confirma com `--list` que o canal alvo aparece. Se nao aparecer, sua conta nao esta dentro do canal.
- **`FloodWaitError`**: voce passou de algum limite do Telegram. O Telethon ja respeita rate limit, mas se acontecer, espera o tempo indicado no erro.

## Proximos passos (depois que tiver rodando local)

- Subir num VPS com `systemd` (Linux) ou `nssm` (Windows) pra rodar 24/7
- Adicionar bot de notificacao secundario se quiser alertas de nova linha
