import pytest

from rpa.equipamento import Resultado
from rpa.erros import FiltrosInvalidos, SessaoExpirada, TravaSeguranca
from rpa.executor import executar
from rpa.progresso import Progresso
from tests.conftest import BASE
from tests.paginas import pagina_lista

MODELO = "PSDN-AX30-40"
VERSAO = "3.0.0.43(09)"


@pytest.fixture
def lista(contexto):
    html = pagina_lista([(str(i), MODELO, VERSAO) for i in (1, 2, 3)])
    contexto.route(
        f"{BASE}/**", lambda rota: rota.fulfill(body=html, content_type="text/html")
    )


@pytest.fixture
def progresso(cfg):
    return Progresso(cfg.arquivo_progresso)


def roteiro(respostas):
    """Devolve uma ação falsa que segue as respostas por ID e anota as chamadas."""
    chamadas = []

    def acao(page, equipamento_id, cfg, simular):
        chamadas.append(equipamento_id)
        resposta = respostas.get(equipamento_id, Resultado("sucesso", "ok"))
        if isinstance(resposta, list):
            resposta = resposta.pop(0)
        if isinstance(resposta, Exception):
            raise resposta
        return resposta

    acao.chamadas = chamadas
    return acao


def test_mensagem_negativa_nao_interrompe_o_fluxo(page, cfg, progresso, lista):
    acao = roteiro({"1": Resultado("erro", "Não respondeu")})

    resumo = executar(page, cfg, progresso, acao=acao)

    assert acao.chamadas == ["1", "2", "3"]
    assert resumo["erro"] == 1 and resumo["sucesso"] == 2
    assert progresso.registros["1"]["mensagem"] == "Não respondeu"


def test_volta_para_a_lista_depois_de_cada_equipamento(page, cfg, progresso, lista):
    visitadas = []
    page.on("framenavigated", lambda frame: visitadas.append(frame.url))

    def acao(p, equipamento_id, c, simular):
        visitadas.append(f"acao:{equipamento_id}")
        return Resultado("sucesso", "ok")

    executar(page, cfg, progresso, acao=acao)

    posicao = visitadas.index("acao:1")
    assert visitadas[posicao + 1] == cfg.url_lista


def test_falha_antes_do_clique_segue_e_nao_registra(page, cfg, progresso, lista):
    acao = roteiro({"1": RuntimeError("timeout"), "2": TravaSeguranca("versão")})

    resumo = executar(page, cfg, progresso, acao=acao)

    assert acao.chamadas == ["1", "2", "3"]
    assert resumo["falha"] == 1 and resumo["pulado"] == 1 and resumo["sucesso"] == 1
    assert list(progresso.registros) == ["3"]


def test_ids_ja_enviados_nao_sao_repetidos(page, cfg, progresso, lista):
    progresso.registrar("1", "erro", "x")
    progresso.registrar("2", "sucesso", "x")
    acao = roteiro({})

    resumo = executar(page, cfg, progresso, acao=acao)

    assert acao.chamadas == ["3"]
    assert resumo["ja_enviado"] == 2


def test_repetir_erros_reenvia_apenas_erros(page, cfg, progresso, lista):
    progresso.registrar("1", "erro", "x")
    progresso.registrar("2", "sucesso", "x")
    acao = roteiro({})

    executar(page, cfg, progresso, repetir_erros=True, acao=acao)

    assert acao.chamadas == ["1", "3"]


def test_simular_nao_grava_progresso(page, cfg, progresso, lista):
    acao = roteiro({i: Resultado("simulado", "ok") for i in ("1", "2", "3")})

    resumo = executar(page, cfg, progresso, simular=True, acao=acao)

    assert resumo["simulado"] == 3
    assert progresso.registros == {}
    assert not cfg.arquivo_progresso.exists()


def test_sessao_expirada_pausa_e_repete_o_mesmo_equipamento(page, cfg, progresso, lista):
    acao = roteiro({"2": [SessaoExpirada("login"), Resultado("sucesso", "ok")]})
    logins = []

    resumo = executar(
        page, cfg, progresso, acao=acao, aguardar_login=lambda: logins.append(True)
    )

    assert acao.chamadas == ["1", "2", "2", "3"]
    assert len(logins) == 1
    assert resumo["sucesso"] == 3


def test_filtros_errados_nao_chegam_a_nenhum_equipamento(page, contexto, cfg, progresso):
    html = pagina_lista([("1", MODELO, VERSAO)], modelo="")
    contexto.route(
        f"{BASE}/**", lambda rota: rota.fulfill(body=html, content_type="text/html")
    )
    acao = roteiro({})

    with pytest.raises(FiltrosInvalidos):
        executar(page, cfg, progresso, acao=acao)

    assert acao.chamadas == []
