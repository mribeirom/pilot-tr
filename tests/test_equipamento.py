import pytest
from playwright.sync_api import TimeoutError as PlaywrightTimeout

from rpa.equipamento import (
    STATUS_ERRO,
    STATUS_SEM_MENSAGEM,
    STATUS_SIMULADO,
    STATUS_SUCESSO,
    atualizar,
    bloquear_factory_reset,
    link_atualizar_valido,
)
from rpa.erros import SessaoExpirada, TravaSeguranca
from tests.conftest import BASE
from tests.paginas import pagina_equipamento, pagina_lista, toast

URL_INFO = f"{BASE}/tr-069/device/100/info"


def servir(contexto, html_info, html_depois=""):
    """Serve a página do equipamento e anota cada requisição recebida."""
    pedidos = []

    def responder(rota):
        url = rota.request.url
        pedidos.append(url)
        if "do_update" in url:
            rota.fulfill(
                body=html_depois or html_info, content_type="text/html; charset=utf-8"
            )
        elif "factory_reset" in url:
            rota.fulfill(body="<html>RESET</html>", content_type="text/html")
        else:
            rota.fulfill(body=html_info, content_type="text/html")

    contexto.route(f"{BASE}/**", responder)
    return pedidos


def enviou(pedidos):
    return any("do_update" in url for url in pedidos)


def resetou(pedidos):
    return any("factory_reset" in url for url in pedidos)


@pytest.mark.parametrize(
    "href,valido",
    [
        ("/acs_software/do_update/15/100?back_page=/tr-069/device/100/info", True),
        ("/acs_software/do_update/15/999?back_page=/tr-069/device/999/info", False),
        ("/acs_software/do_update/16/100?back_page=/tr-069/device/100/info", False),
        ("/tr-069/device/abc/factory_reset?back_page=/tr-069/device/100/info", False),
        ("/acs_software/do_update/15/100?back_page=/factory_reset", False),
        ("", False),
        (None, False),
    ],
)
def test_validacao_do_link(href, valido):
    assert link_atualizar_valido(href, "15", "100") is valido


def test_mensagem_de_erro_e_registrada_como_erro(page, contexto, cfg):
    depois = pagina_equipamento(toast=toast("Equipamento não respondeu"))
    pedidos = servir(contexto, pagina_equipamento(), depois)

    resultado = atualizar(page, "100", cfg)

    assert resultado.status == STATUS_ERRO
    assert resultado.mensagem == "Equipamento não respondeu"
    assert enviou(pedidos) and not resetou(pedidos)


def test_mensagem_positiva_e_registrada_como_sucesso(page, contexto, cfg):
    depois = pagina_equipamento(toast=toast("Solicitação enviada", erro=False))
    servir(contexto, pagina_equipamento(), depois)

    assert atualizar(page, "100", cfg).status == STATUS_SUCESSO


def test_clique_sem_mensagem_conta_como_enviado(page, contexto, cfg):
    pedidos = servir(contexto, pagina_equipamento())

    resultado = atualizar(page, "100", cfg)

    assert resultado.status == STATUS_SEM_MENSAGEM
    assert resultado.enviado and enviou(pedidos)


def test_clique_que_nao_acontece_nao_conta_como_enviado(page, contexto, cfg):
    html = pagina_equipamento().replace(
        "b.setAttribute(", "b.style.pointerEvents = 'none'; b.setAttribute("
    )
    pedidos = servir(contexto, html)

    with pytest.raises(PlaywrightTimeout):
        atualizar(page, "100", cfg)

    assert not enviou(pedidos)


def test_simular_cancela_sem_enviar(page, contexto, cfg):
    pedidos = servir(contexto, pagina_equipamento())

    resultado = atualizar(page, "100", cfg, simular=True)

    assert resultado.status == STATUS_SIMULADO and not resultado.enviado
    assert not enviou(pedidos) and not resetou(pedidos)
    assert not page.locator("#acs_firmware_update_modal").is_visible()


def test_botao_que_segue_desabilitado_nao_e_clicado(page, contexto, cfg):
    pedidos = servir(contexto, pagina_equipamento(liberar_botao=False))

    with pytest.raises(TravaSeguranca):
        atualizar(page, "100", cfg)

    assert not enviou(pedidos) and not resetou(pedidos)


def test_botao_liberado_apontando_para_factory_reset_nao_e_clicado(page, contexto, cfg):
    href = "/tr-069/device/abc/factory_reset?back_page=x"
    pedidos = servir(contexto, pagina_equipamento(href_escolhido=href))

    with pytest.raises(TravaSeguranca):
        atualizar(page, "100", cfg)

    assert not resetou(pedidos)


def test_link_de_outro_equipamento_nao_e_clicado(page, contexto, cfg):
    href = "/acs_software/do_update/15/999?back_page=/tr-069/device/999/info"
    pedidos = servir(contexto, pagina_equipamento(href_escolhido=href))

    with pytest.raises(TravaSeguranca):
        atualizar(page, "100", cfg)

    assert not enviou(pedidos)


@pytest.mark.parametrize(
    "opcoes",
    [
        {"item_valor": "16"},
        {"item_texto": " Outro firmware"},
        {"versao": "4.2.0.52(SP5C947)"},
        {"modelo": "WS7001-40"},
    ],
)
def test_pagina_ou_firmware_fora_do_lote_e_pulado(page, contexto, cfg, opcoes):
    pedidos = servir(contexto, pagina_equipamento(**opcoes))

    with pytest.raises(TravaSeguranca):
        atualizar(page, "100", cfg)

    assert not enviou(pedidos)


def test_restaurar_de_fabrica_nunca_e_acionado(page, contexto, cfg):
    servir(contexto, pagina_equipamento())

    atualizar(page, "100", cfg, simular=True)

    assert page.evaluate("window.restaurou") is None


def test_sessao_expirada_e_detectada(page, contexto, cfg):
    servir(contexto, pagina_lista([], logado=False))

    with pytest.raises(SessaoExpirada):
        atualizar(page, "100", cfg)


def test_bloqueio_no_navegador_derruba_factory_reset(page, contexto, cfg):
    bloqueadas = []
    contexto.on("requestfailed", lambda pedido: bloqueadas.append(pedido.url))
    pedidos = servir(contexto, pagina_equipamento())
    bloquear_factory_reset(contexto)
    page.goto(URL_INFO)

    page.evaluate("fetch('/tr-069/device/abc/factory_reset').catch(() => null)")

    assert not resetou(pedidos)
    assert any("factory_reset" in url for url in bloqueadas)
