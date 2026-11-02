import re
from dataclasses import dataclass

from playwright.sync_api import BrowserContext, Page
from playwright.sync_api import TimeoutError as PlaywrightTimeout

from rpa import seletores
from rpa.config import Config
from rpa.erros import TravaSeguranca
from rpa.lista import conferir_sessao

STATUS_SUCESSO = "sucesso"
STATUS_ERRO = "erro"
STATUS_SEM_MENSAGEM = "sem_mensagem"
STATUS_SIMULADO = "simulado"


@dataclass(frozen=True)
class Resultado:
    status: str
    mensagem: str

    @property
    def enviado(self) -> bool:
        return self.status != STATUS_SIMULADO


def bloquear_factory_reset(context: BrowserContext) -> None:
    context.route("**/factory_reset**", lambda rota: rota.abort())


def link_atualizar_valido(href: str | None, firmware_id: str, equipamento_id: str) -> bool:
    esperado = (
        f"/acs_software/do_update/{firmware_id}/{equipamento_id}"
        f"?back_page=/tr-069/device/{equipamento_id}/info"
    )
    return href == esperado


def _abrir_pagina(page: Page, equipamento_id: str, cfg: Config) -> None:
    page.goto(cfg.url_equipamento(equipamento_id), wait_until="load", timeout=cfg.tempos.pagina)
    conferir_sessao(page)
    if not re.search(rf"/tr-069/device/{equipamento_id}/info(\?|$)", page.url):
        raise TravaSeguranca(f"URL inesperada: {page.url}")
    texto = page.locator("body").inner_text()
    if cfg.modelo not in texto or cfg.versao_atual not in texto:
        raise TravaSeguranca("A página não mostra o modelo e a versão do lote.")


def _abrir_modal(page: Page, cfg: Config) -> None:
    espera = cfg.tempos.interface
    page.locator(seletores.MENU_ACOES).click(timeout=espera)
    page.locator(seletores.ITEM_ATUALIZAR_FIRMWARE).click(timeout=espera)
    page.locator(seletores.MODAL_FIRMWARE).wait_for(state="visible", timeout=espera)


def _escolher_firmware(page: Page, cfg: Config) -> None:
    espera = cfg.tempos.interface
    page.locator(seletores.SELETOR_FIRMWARE).click(timeout=espera)
    item = page.locator(seletores.item_firmware(cfg.firmware_id))
    if item.count() != 1:
        raise TravaSeguranca("O seletor não oferece o firmware configurado.")
    nome = (item.get_attribute("data-text") or "").strip()
    if nome != cfg.firmware_nome:
        raise TravaSeguranca(f"Firmware diferente do configurado: {nome!r}.")
    item.click(timeout=espera)


def _conferir_botao(page: Page, equipamento_id: str, cfg: Config) -> None:
    botao = page.locator(seletores.BOTAO_ATUALIZAR)
    try:
        page.wait_for_function(
            "seletor => !document.querySelector(seletor).classList.contains('disabled')",
            arg=seletores.BOTAO_ATUALIZAR,
            timeout=cfg.tempos.interface,
        )
    except PlaywrightTimeout as erro:
        raise TravaSeguranca("O botão Atualizar continuou desabilitado.") from erro
    href = botao.get_attribute("href")
    if not link_atualizar_valido(href, cfg.firmware_id, equipamento_id):
        raise TravaSeguranca(f"Link inesperado no botão Atualizar: {href!r}.")


def _ler_mensagem(page: Page, cfg: Config) -> Resultado:
    mensagem = page.locator(seletores.MENSAGEM).first
    try:
        mensagem.wait_for(state="visible", timeout=cfg.tempos.mensagem)
        texto = " ".join(mensagem.inner_text().split())
        classes = mensagem.get_attribute("class") or ""
    except PlaywrightTimeout:
        return Resultado(STATUS_SEM_MENSAGEM, "Nenhuma mensagem apareceu.")
    status = STATUS_ERRO if "error" in classes.split() else STATUS_SUCESSO
    return Resultado(status, texto)


def atualizar(page: Page, equipamento_id: str, cfg: Config, simular: bool = False) -> Resultado:
    """Executa o fluxo do modal. Qualquer exceção aqui significa que não houve clique."""
    _abrir_pagina(page, equipamento_id, cfg)
    _abrir_modal(page, cfg)
    _escolher_firmware(page, cfg)
    _conferir_botao(page, equipamento_id, cfg)

    if simular:
        page.locator(seletores.BOTAO_CANCELAR).click(timeout=cfg.tempos.interface)
        page.locator(seletores.MODAL_FIRMWARE).wait_for(
            state="hidden", timeout=cfg.tempos.interface
        )
        return Resultado(STATUS_SIMULADO, "Travas aprovadas; modal cancelado.")

    botao = page.locator(seletores.BOTAO_ATUALIZAR)
    clicou = False
    try:
        with page.expect_navigation(wait_until="load", timeout=cfg.tempos.resposta):
            botao.click(timeout=cfg.tempos.interface)
            clicou = True
    except PlaywrightTimeout:
        if not clicou:
            raise
    return _ler_mensagem(page, cfg)
