from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

from rpa.config import Config, Tempos

BASE = "https://oltcloud.teste"


@pytest.fixture
def cfg(tmp_path: Path) -> Config:
    return Config(
        base_url=BASE,
        lista_path="/tr-069/device/buscar",
        filtro_modelo="PSDN",
        filtro_software="09",
        filtro_status="Online",
        modelo="PSDN-AX30-40",
        versao_atual="3.0.0.43(09)",
        firmware_id="15",
        firmware_nome="Ax3s - 4.2.0.52(SP5C947)",
        perfil_dir=tmp_path / "perfil",
        arquivo_progresso=tmp_path / "progresso.json",
        tempos=Tempos(pagina=3000, interface=1000, resposta=2000, mensagem=500),
    )


@pytest.fixture(scope="session")
def navegador():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        yield browser
        browser.close()


@pytest.fixture
def contexto(navegador):
    context = navegador.new_context()
    yield context
    context.close()


@pytest.fixture
def page(contexto):
    return contexto.new_page()
