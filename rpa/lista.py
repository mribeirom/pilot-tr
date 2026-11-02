import re
from dataclasses import dataclass

from playwright.sync_api import Page

from rpa import seletores
from rpa.config import Config
from rpa.erros import FiltrosInvalidos, SessaoExpirada


@dataclass(frozen=True)
class Equipamento:
    id: str
    modelo: str
    software: str
    status: str


def conferir_sessao(page: Page) -> None:
    if page.locator(seletores.LOGADO).count() == 0:
        raise SessaoExpirada(page.url)


def abrir_lista(page: Page, cfg: Config, pagina: int | None = None) -> None:
    sufixo = f"?page={pagina}" if pagina else ""
    page.goto(cfg.url_lista + sufixo, wait_until="load", timeout=cfg.tempos.pagina)
    conferir_sessao(page)


def conferir_filtros(page: Page, cfg: Config) -> None:
    modelo = page.locator(seletores.FILTRO_MODELO).input_value()
    software = page.locator(seletores.FILTRO_SOFTWARE).input_value()
    status = page.locator(seletores.FILTRO_STATUS).evaluate(
        "campo => campo.selectedOptions[0]?.text.trim() ?? ''"
    )
    esperado = (cfg.filtro_modelo, cfg.filtro_software, cfg.filtro_status)
    if (modelo, software, status) != esperado:
        raise FiltrosInvalidos(
            f"Esperado Modelo={cfg.filtro_modelo!r}, Software={cfg.filtro_software!r} e "
            f"Status={cfg.filtro_status!r}; encontrado Modelo={modelo!r}, "
            f"Software={software!r} e Status={status!r}."
        )


def extrair_equipamentos(page: Page) -> list[Equipamento]:
    equipamentos = []
    for linha in page.locator(seletores.LINHAS_LISTA).all():
        link = linha.locator(seletores.LINK_EQUIPAMENTO).first
        if link.count() == 0:
            continue
        href = link.get_attribute("href") or ""
        encontrado = re.fullmatch(r"/tr-069/device/(\d+)/info", href)
        if encontrado is None:
            continue
        colunas = [texto.strip() for texto in linha.locator("td").all_inner_texts()]
        equipamentos.append(
            Equipamento(
                id=encontrado.group(1),
                modelo=colunas[seletores.COLUNA_MODELO],
                software=colunas[seletores.COLUNA_SOFTWARE],
                status=colunas[seletores.COLUNA_STATUS],
            )
        )
    return equipamentos


def coletar_equipamentos(page: Page, cfg: Config) -> tuple[list[Equipamento], int]:
    """Percorre todas as páginas e devolve o lote e quantos ficaram fora dele."""
    lote: dict[str, Equipamento] = {}
    fora_do_lote: set[str] = set()
    pagina = 1
    while True:
        abrir_lista(page, cfg, pagina)
        conferir_filtros(page, cfg)
        for equipamento in extrair_equipamentos(page):
            if (
                equipamento.modelo == cfg.modelo
                and equipamento.software == cfg.versao_atual
                and equipamento.status == cfg.filtro_status
            ):
                lote.setdefault(equipamento.id, equipamento)
            else:
                fora_do_lote.add(equipamento.id)
        print(f"Página {pagina}: {len(lote)} equipamentos coletados até agora.")
        if page.locator(seletores.proxima_pagina(pagina)).count() == 0:
            return list(lote.values()), len(fora_do_lote)
        pagina += 1
