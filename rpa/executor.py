from collections import Counter
from typing import Callable

from playwright.sync_api import Page

from rpa.config import Config
from rpa.equipamento import Resultado, atualizar
from rpa.erros import SessaoExpirada, TravaSeguranca
from rpa.lista import abrir_lista, coletar_equipamentos, conferir_filtros
from rpa.progresso import Progresso


def _voltar_para_lista(page: Page, cfg: Config) -> None:
    try:
        abrir_lista(page, cfg)
    except SessaoExpirada:
        raise
    except Exception as erro:
        print(f"  Aviso: não consegui voltar para a lista: {erro}")


def executar(
    page: Page,
    cfg: Config,
    progresso: Progresso,
    simular: bool = False,
    repetir_erros: bool = False,
    acao: Callable[..., Resultado] = atualizar,
    aguardar_login: Callable[[], None] = lambda: input(
        "Sessão expirada. Faça login no navegador e pressione ENTER... "
    ),
) -> Counter:
    abrir_lista(page, cfg)
    conferir_filtros(page, cfg)
    equipamentos, fora_do_lote = coletar_equipamentos(page, cfg)
    print(f"Lote: {len(equipamentos)} equipamentos. Fora do lote: {fora_do_lote}.")

    resumo: Counter = Counter()
    pendentes = [
        e for e in equipamentos if not progresso.ja_enviado(e.id, repetir_erros)
    ]
    resumo["ja_enviado"] = len(equipamentos) - len(pendentes)

    try:
        for numero, equipamento in enumerate(pendentes, start=1):
            prefixo = f"[{numero}/{len(pendentes)}] ID {equipamento.id}"
            while True:
                try:
                    resultado = acao(page, equipamento.id, cfg, simular)
                    if resultado.enviado:
                        progresso.registrar(
                            equipamento.id, resultado.status, resultado.mensagem
                        )
                    resumo[resultado.status] += 1
                    print(f"{prefixo}: {resultado.status} - {resultado.mensagem}")
                    _voltar_para_lista(page, cfg)
                    break
                except SessaoExpirada:
                    aguardar_login()
                except TravaSeguranca as erro:
                    resumo["pulado"] += 1
                    print(f"{prefixo}: pulado - {erro}")
                    break
                except Exception as erro:
                    if page.is_closed():
                        print("O navegador foi fechado. Encerrando.")
                        return resumo
                    resumo["falha"] += 1
                    print(f"{prefixo}: falha - {erro}")
                    break
    except KeyboardInterrupt:
        print("\nInterrompido pelo usuário.")
    return resumo


def imprimir_resumo(resumo: Counter) -> None:
    print("\nResumo")
    for status, quantidade in sorted(resumo.items()):
        print(f"  {status}: {quantidade}")
