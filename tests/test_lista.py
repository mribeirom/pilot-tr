from urllib.parse import parse_qs, urlparse

import pytest

from rpa.erros import FiltrosInvalidos, SessaoExpirada
from rpa.lista import abrir_lista, coletar_equipamentos, conferir_filtros
from tests.conftest import BASE
from tests.paginas import pagina_lista

MODELO = "PSDN-AX30-40"
VERSAO = "3.0.0.43(09)"


def servir_paginas(contexto, paginas):
    def responder(rota):
        consulta = parse_qs(urlparse(rota.request.url).query)
        numero = int(consulta.get("page", ["1"])[0])
        rota.fulfill(body=paginas[numero], content_type="text/html")

    contexto.route(f"{BASE}/**", responder)


def test_coleta_todas_as_paginas_sem_duplicar(page, contexto, cfg):
    servir_paginas(
        contexto,
        {
            1: pagina_lista([("1", MODELO, VERSAO), ("2", MODELO, VERSAO)], 1, tem_proxima=True),
            2: pagina_lista([("2", MODELO, VERSAO), ("3", MODELO, VERSAO)], 2, tem_proxima=True),
            3: pagina_lista([("4", MODELO, VERSAO)], 3),
        },
    )

    equipamentos, fora = coletar_equipamentos(page, cfg)

    assert [e.id for e in equipamentos] == ["1", "2", "3", "4"]
    assert equipamentos[0].status == "Online"
    assert fora == 0


def test_linha_de_outro_modelo_ou_versao_fica_fora_do_lote(page, contexto, cfg):
    servir_paginas(
        contexto,
        {
            1: pagina_lista(
                [
                    ("1", MODELO, VERSAO),
                    ("2", "WS7001-40", VERSAO),
                    ("3", MODELO, "3.0.0.43(10)"),
                    ("4", MODELO, VERSAO, "Offline"),
                ]
            )
        },
    )

    equipamentos, fora = coletar_equipamentos(page, cfg)

    assert [e.id for e in equipamentos] == ["1"]
    assert fora == 3


@pytest.mark.parametrize(
    "filtros",
    [
        {"modelo": ""},
        {"software": ""},
        {"modelo": "WS", "software": "09"},
        {"status": ""},
        {"status": "Offline"},
    ],
)
def test_filtros_errados_param_a_coleta(page, contexto, cfg, filtros):
    servir_paginas(contexto, {1: pagina_lista([("1", MODELO, VERSAO)], **filtros)})

    abrir_lista(page, cfg)

    with pytest.raises(FiltrosInvalidos):
        conferir_filtros(page, cfg)
    with pytest.raises(FiltrosInvalidos):
        coletar_equipamentos(page, cfg)


def test_lista_sem_login_levanta_sessao_expirada(page, contexto, cfg):
    servir_paginas(contexto, {1: pagina_lista([], logado=False)})

    with pytest.raises(SessaoExpirada):
        abrir_lista(page, cfg)
