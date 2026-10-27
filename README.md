# Automação de Cliques

Automação que detecta e clica em botões de atualizar/confirmar na tela com base em mudanças visuais.

## Requisitos

- Python 3.10+
- Windows

## Instalação

1. Clone ou baixe o projeto na sua máquina.

2. Instale as dependências:

```bash
pip install -r requirements.txt
```

## Como rodar

```bash
python main.py
```

Ao iniciar, o script vai pedir para você clicar nos botões para coletar as coordenadas:

1. **Clique no botão [ATUALIZAR]** — posicione o site e clique no botão de atualizar
2. **Clique no botão [CONFIRMAR]** — clique no botão de confirmar

Após a coleta, a automação inicia automaticamente.

## Estrutura do projeto

```
.
├── main.py         # Ponto de entrada
├── automacao.py    # Lógica de automação e coleta de coordenadas
├── detector.py     # Detecção de mudanças visuais na tela
└── requirements.txt
```
