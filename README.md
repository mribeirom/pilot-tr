# RPA de firmware na OLT Cloud

Robô em Python que atualiza o firmware dos equipamentos do OLT Cloud pela interface web, um de cada vez, com o navegador visível.

> **Atenção:** a atualização age em equipamentos reais de clientes e não há limite nem pausa entre eles. Antes de cada execução real, rode `--coletar` e `--simular`.

## Requisitos

- Python 3.10 ou superior
- Acesso à OLT Cloud

## Instalação

```bash
python -m pip install -r requirements.txt
```

```bash
python -m playwright install chromium
```

## Configuração

Tudo fica em `config.yaml`:

| Campo | Função |
|---|---|
| `base_url`, `lista_path` | Endereço da lista de equipamentos |
| `filtros` | Valores que precisam estar nos filtros Modelo e Software da lista |
| `modelo`, `versao_atual` | Só linhas exatamente neste modelo e nesta versão são atualizadas |
| `firmware.id`, `firmware.nome` | Firmware esperado no seletor do modal |
| `perfil_dir` | Pasta do perfil do navegador, que guarda o login entre execuções |
| `arquivo_progresso` | Arquivo com os IDs já enviados |
| `tempos_ms` | Tempos máximos de espera |

Para atualizar outro modelo ou versão, ajuste `filtros`, `modelo`, `versao_atual` e `firmware`. O ID do firmware aparece no seletor do modal de atualização.

## Como usar

Rode os comandos na pasta do projeto, nesta ordem:

**1. Coletar:** lista o lote sem tocar em nenhum equipamento.

```bash
python main.py --coletar
```

**2. Simular:** passa por todos os equipamentos, confere as travas e cancela o modal.

```bash
python main.py --simular
```

**3. Executar:** atualiza o lote.

```bash
python main.py
```

Em todos os modos, o navegador abre e o terminal espera. Faça login, aplique os filtros na lista e pressione ENTER. O robô usa um navegador próprio, então o primeiro login é feito nele. Depois, o perfil salvo em `perfil_dir` reaproveita a sessão.

Para reenviar os IDs que receberam mensagem de erro, use o comando abaixo. Faça isso só depois de conferir esses equipamentos, porque o site pode manter a atualização em andamento mesmo depois de um erro.

```bash
python main.py --repetir-erros
```

Para interromper, pressione Ctrl+C no terminal. O robô mostra o resumo, e a próxima execução pula os IDs já enviados.

## Como funciona

1. Confere a sessão e os filtros da lista. Com filtros diferentes, para antes de atualizar.
2. Percorre todas as páginas e guarda os IDs do lote. Não há limite de quantidade.
3. Para cada ID, abre a página do equipamento e faz o fluxo: Ações, Atualizar Firmware, escolher o firmware, Atualizar.
4. Registra a mensagem do site, volta para a lista e segue para o próximo equipamento.
5. Mostra o resumo no final.

Os IDs são coletados antes de atualizar porque os equipamentos atualizados saem da lista depois de um tempo, o que desloca as páginas e poderia fazer o robô pular equipamentos. Quem entrar na lista depois da coleta fica para a próxima execução.

## Resultados

| Status | Significado | Volta a ser enviado? |
|---|---|---|
| `sucesso` | O site mostrou mensagem positiva | Não |
| `erro` | O site mostrou mensagem negativa | Só com `--repetir-erros` |
| `sem_mensagem` | Houve clique, mas nenhuma mensagem foi lida | Não |
| `falha` | Algo deu errado antes do clique | Sim, na próxima execução |
| `pulado` | Uma trava de segurança impediu o clique | Sim, na próxima execução |
| `ja_enviado` | O ID já estava em `progresso.json` | Não |
| `simulado` | Passou pelas travas no modo `--simular` | Não se aplica |

O robô só registra a resposta do site e não confirma a versão instalada no equipamento. Quem atualizou de fato aparece depois, pelos equipamentos que saíram da lista.


## Desenvolvimento

Os testes usam páginas falsas locais e não acessam a OLT Cloud:

```bash
python -m pytest
```

```text
rpa_firmware/
├── main.py              # argumentos e início da execução
├── config.yaml          # configuração do lote
├── progresso.json       # IDs já enviados (criado na execução)
├── PLANO.md             # planejamento e resultado do teste real
├── rpa/
│   ├── config.py        # leitura do YAML
│   ├── seletores.py     # seletores da interface
│   ├── lista.py         # sessão, filtros e coleta dos IDs
│   ├── equipamento.py   # fluxo do modal e travas de segurança
│   ├── progresso.py     # leitura e gravação do progresso
│   ├── executor.py      # laço principal e resumo
│   └── erros.py         # exceções do robô
└── tests/               # testes com páginas falsas
```
