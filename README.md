# 👻 Ghost Panel Ultra: Ferramenta de Produtividade Stealth para Desenvolvedores

[](https://www.google.com/search?q=LICENSE)
[](https://www.python.org/)
[](https://customtkinter.tomschimansky.com/)

O **Ghost Panel Ultra** é uma ferramenta de IA local e discreta desenvolvida para maximizar a produtividade durante testes técnicos, entrevistas de codificação ou trabalho focado. Ele oferece acesso instantâneo aos modelos de IA mais poderosos (Gemini, GPT-4o, DeepSeek, Perplexity) em um painel que se esconde da barra de tarefas e é ativado por atalhos globais personalizáveis.

-----

### 🚀 Visão Geral e Funcionalidades

O principal diferencial do Ghost Panel é a capacidade de realizar tarefas complexas de IA sem interromper o fluxo de trabalho ou ser detectado em ambientes de compartilhamento de tela.

  * **Modo Stealth (Invisível):** O aplicativo não aparece na barra de tarefas (Taskbar) nem no `Alt+Tab`. É ativado e desativado exclusivamente por atalho global.
  * **Visão Computacional Instantânea:** Capture a tela atual (Live Coding, diagramas, ou código) e envie-a para análise usando modelos compatíveis (Gemini e GPT-4o).
  * **Controle de Hardware:** Atalhos dedicados para tirar prints e usar o microfone (Speech-to-Text).
  * **Perguntas Rápidas (Quick Prompts):** Botões pré-configurados para tarefas comuns de entrevista: `Explicar`, `Refatorar`, `Debug`, `Big O` e `Design Pattern`.
  * **Persistência de Configuração:** Chaves de API e atalhos são salvos localmente (`ghost_config.json`) na pasta do executável, mantendo-os prontos para o próximo uso.
  * **Design Profissional:** Interface compacta, responsiva e com tema escuro elegante (Midnight Indigo).

-----

### 💾 Instalação e Uso (Para Usuários Finais)

Esta seção é para quem está baixando o arquivo diretamente do GitHub Releases.

#### 1\. Download

1.  Vá para a página [Releases do Ghost Panel Ultra](https://www.google.com/search?q=https://github.com/SeuNome/SeuProjeto/releases).
2.  Baixe o arquivo **`GhostKey.exe`** (Recomendado: Baixe o arquivo ZIP para evitar problemas de bloqueio de antivírus).
3.  Descompacte e execute o **`GhostKey.exe`**. O aplicativo será iniciado no canto superior direito.

#### 2\. Configuração de APIs (Obrigatório)

O painel precisa das suas chaves pessoais para funcionar.

1.  No aplicativo, clique em **`⚙️ APIs`** na barra lateral.
2.  Para cada provedor que deseja usar, insira:
      * **API Key:** Sua chave secreta.
      * **Model Name:** O nome exato do modelo (Ex: `gpt-4o`, `gemini-2.5-flash`).
3.  Clique em **`SALVAR ALTERAÇÕES`**. (Uma notificação verde aparecerá no topo).

#### 3\. Como Usar o Print (Visão)

Para usar a Visão Computacional, **você deve selecionar GPT ou GEMINI**.

| Ação | Atalho Padrão | O que acontece |
| :--- | :--- | :--- |
| **Ativar Print** | `Ctrl + Alt + S` | O painel pisca (desaparece e volta), e a miniatura **`[IMAGEM ANEXADA]`** aparece acima do campo de digitação. |
| **Remover Print** | Clique no botão **`✕`** ao lado do aviso. | Remove a imagem antes de enviar a mensagem. |
| **Perguntar** | Digite sua pergunta e pressione **Enter**. | A imagem anexada é enviada junto com o texto para a IA selecionada. |

-----

### ⌨️ Atalhos Globais

Todos os atalhos são editáveis na aba **`⌨ ATALHOS`**.

| Ação | Atalho Padrão | Notas |
| :--- | :--- | :--- |
| **Mostrar/Esconder Painel** | `Ctrl + Alt + H` | *O Botão de Pânico.* Esconde a janela instantaneamente. |
| **Print Rápido (Stealth)** | `Ctrl + Alt + S` | Captura a tela e anexa a imagem (Funciona apenas se GPT ou Gemini estiver ativo). |
| **Ativar Microfone** | `Ctrl + Alt + M` | Inicia a gravação de voz no campo de entrada. |
| **Limpar Tela** | `Ctrl + Alt + C` | Limpa todo o histórico da conversa no Terminal. |
| **Focar no Input** | `Ctrl + Alt + I` | Traz o painel para frente e coloca o cursor no campo de digitação. |

-----

### 💡 Guia de Modelos (Visão e Código)

A capacidade de enviar prints (Visão Computacional) depende da IA.

| Modelo | Suporte à Imagem (Visão) | Melhor Uso |
| :--- | :--- | :--- |
| **GEMINI** (`gemini-2.5-flash`) | ✅ **SIM** | Análise de Código, Visão, Raciocínio Geral. |
| **GPT** (`gpt-4o`) | ✅ **SIM** | Análise de Código, Visão, Criatividade. |
| **DEEPSEEK** (`deepseek-coder`) | ❌ **NÃO** (Apenas texto) | **Especialista em Código**, algoritmos, complexidade. |
| **PERPLEXITY** (`sonar-pro`) | ❌ **NÃO** (Apenas texto) | Resumo de Informação, Respostas concisas. |

***Atenção:** Se um modelo "Text Only" for selecionado, o botão de câmera ficará cinza (`🚫 TEXT ONLY`) para evitar erros de API.*

-----

### 🛠️ Configuração para Desenvolvedores (Developer Setup)

Esta seção é para quem deseja contribuir ou modificar o projeto.

#### 1\. Arquitetura e Estrutura

O projeto segue um design modular limpo para facilitar a manutenção e escalabilidade:

```text
GhostPanel/
├── .gitignore            # Ignora pastas venv, build, dist, e ghost_config.json
├── main.pyw              # Ponto de entrada (Inicia a interface)
├── requirements.txt      # Lista de dependências
├── icon.ico              # Ícone da aplicação (para self.iconbitmap e PyInstaller)
│
└── src/
    ├── backend.py        # Lógica: ConfigManager, HardwareTools, AIEngine (APIs)
    ├── interface.py      # View: Classes GhostApp, ChatPage (CustomTkinter)
    └── theme.py          # Estilo: Definição de COLORS e FONTS
```

#### 2\. Dependências

Instale as bibliotecas necessárias:

```bash
pip install -r requirements.txt
```

O `requirements.txt` contém:

```txt
customtkinter
openai
google-generativeai
Pillow
pyautogui
SpeechRecognition
pyaudio
keyboard
packaging
```

#### 3\. Compilação (Gerando o .exe)

Para gerar o executável com o modo Stealth ativado e o ícone correto, utilize o PyInstaller com as flags de inclusão de dados (`--add-data`):

```bash
pyinstaller --noconsole --onefile --name="GhostKey" --icon="icon.ico" --add-data="icon.ico;." --collect-all customtkinter --paths=src main.pyw
```

O arquivo final **`GhostKey.exe`** estará na pasta **`dist`**.

### 🤝 Contribuição e Licença

Este projeto é de código aberto. Sinta-se à vontade para fazer *fork*, sugerir melhorias ou reportar bugs.

Este projeto está sob a Licença MIT.