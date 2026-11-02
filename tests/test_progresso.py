from rpa.progresso import Progresso


def test_registro_sobrevive_a_nova_leitura(tmp_path):
    caminho = tmp_path / "progresso.json"
    Progresso(caminho).registrar("1", "sucesso", "Enviado ção")

    novo = Progresso(caminho)

    assert novo.ja_enviado("1")
    assert novo.registros["1"]["mensagem"] == "Enviado ção"
    assert not novo.ja_enviado("2")


def test_erro_so_e_reenviado_quando_pedido(tmp_path):
    progresso = Progresso(tmp_path / "progresso.json")
    progresso.registrar("1", "erro", "x")
    progresso.registrar("2", "sucesso", "x")
    progresso.registrar("3", "sem_mensagem", "x")

    assert progresso.ja_enviado("1")
    assert not progresso.ja_enviado("1", repetir_erros=True)
    assert progresso.ja_enviado("2", repetir_erros=True)
    assert progresso.ja_enviado("3", repetir_erros=True)
