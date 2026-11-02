LOGADO = 'a[href="/logout"]'

FILTRO_MODELO = "#buscar_model"
FILTRO_SOFTWARE = "#buscar_sw_version"
FILTRO_STATUS = "#buscar_online"
LINHAS_LISTA = "tbody tr"
LINK_EQUIPAMENTO = 'a[href^="/tr-069/device/"][href$="/info"]'
COLUNA_MODELO = 2
COLUNA_SOFTWARE = 4
COLUNA_STATUS = 10

_ITEM_FIRMWARE = """.item[onclick*="acs_firmware_update_modal"]"""
# A página tem dois .acs_menu; o de Ações é o que contém a opção de firmware.
MENU_ACOES = f".acs_menu:has({_ITEM_FIRMWARE})"
ITEM_ATUALIZAR_FIRMWARE = f"{MENU_ACOES} {_ITEM_FIRMWARE}"

MODAL_FIRMWARE = "#acs_firmware_update_modal"
SELETOR_FIRMWARE = "#acs_firmware_update_modal .ui.dropdown"
BOTAO_ATUALIZAR = "#btn_ok_firmware_update"
BOTAO_CANCELAR = "#acs_firmware_update_modal .actions .deny"

MENSAGEM = ".ui.toast"


def proxima_pagina(numero_atual: int) -> str:
    return f'.busca-pag a[href="?page={numero_atual + 1}"]'


def item_firmware(firmware_id: str) -> str:
    return f'{SELETOR_FIRMWARE} .item[data-value="{firmware_id}"]'
