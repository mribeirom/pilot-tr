"""Módulo de automação de cliques e interação com a interface."""

import ctypes
import time
import pyautogui

from detector import DetectorDeTela


def coletar_coordenadas() -> tuple["Coordenada", "Coordenada"]:
    """Aguarda o usuário clicar nos botões e retorna as coordenadas capturadas."""

    def aguardar_clique(nome: str) -> tuple[int, int]:
        """Bloqueia até o usuário soltar o botão esquerdo do mouse e retorna a posição."""
        print(f"  >> Clique no botao [{nome}]...")

        # Aguarda o botão ser pressionado
        while not ctypes.windll.user32.GetAsyncKeyState(0x01) & 0x8000:
            time.sleep(0.01)

        # Aguarda soltar para pegar a posição final
        while ctypes.windll.user32.GetAsyncKeyState(0x01) & 0x8000:
            time.sleep(0.01)

        x, y = pyautogui.position()
        print(f"  >> Capturado: x={x}, y={y}")
        return x, y

    print("\n" + "=" * 40)
    print("  COLETAR COORDENADAS")
    print("=" * 40)




    ax, ay = aguardar_clique("ATUALIZAR")
    time.sleep(0.4)
    cx, cy = aguardar_clique("CONFIRMAR")
    print(f"{'='*40}")


    return Coordenada(ax, ay), Coordenada(cx, cy)


class Coordenada:
    """Representa uma coordenada (x, y) na tela."""

    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y

    def deslocar(self, dx: int = 0, dy: int = 0) -> "Coordenada":
        """Retorna uma nova coordenada deslocada."""
        return Coordenada(self.x + dx, self.y + dy)

    def __repr__(self) -> str:
        return f"Coordenada(x={self.x}, y={self.y})"


class Automacao:
    """Orquestra o ciclo completo de automação do site."""

    def __init__(
        self,
        botao_atualizar: Coordenada | None = None,
        botao_confirmar: Coordenada | None = None,
        tolerancia: float = 3.0,
        mudancas_para_reiniciar: int = 3,
        passo_busca_y: int = 37,
        tentativas_busca: int = 20,
    ):
        """
        Args:
            botao_atualizar: Coordenada base do botão de atualizar. Se None, abre calibração.
            botao_confirmar: Coordenada do botão de confirmar. Se None, abre calibração.
            tolerancia: Tolerância para a detecção de mudança visual.
            mudancas_para_reiniciar: Quantas mudanças detectar antes de reiniciar o ciclo.
            passo_busca_y: Pixels para subir a cada tentativa de busca do botão.
            tentativas_busca: Quantidade máxima de posições para procurar o botão.
        """
        self._botao_atualizar = botao_atualizar
        self._botao_confirmar = botao_confirmar
        self._mudancas_para_reiniciar = mudancas_para_reiniciar
        self._passo_busca_y = passo_busca_y
        self._tentativas_busca = tentativas_busca
        self._detector = DetectorDeTela(tolerancia)
        self._numero_do_ciclo = 0

        if botao_atualizar is None or botao_confirmar is None:
            botao_atualizar, botao_confirmar = coletar_coordenadas()
            self._botao_atualizar = botao_atualizar
            self._botao_confirmar = botao_confirmar
            self._aguardar_carregamento() 




    def executar(self):
        """Executa o loop principal de automação indefinidamente."""

        while True:
            self._numero_do_ciclo += 1
            print(f"\n{'='*40}")
            print(f"  Ciclo {self._numero_do_ciclo}")
            print(f"{'='*40}")

            self._baixar_pagina()
            self._buscar_e_atualizar()
            self._aguardar_carregamento()

    def _baixar_pagina(self):
        """Baixar a página para baixo."""
        for _ in range(2):
            pyautogui.scroll(-1000)

    def _buscar_e_atualizar(self):
        """Procura o botão de atualizar subindo a posição Y e clica em confirmar ao detectar mudança."""
        time.sleep(0.5)
        self._detector.capturar()


        for i in range(self._tentativas_busca):
            deslocamento_y = i * self._passo_busca_y
            pos = self._botao_atualizar.deslocar(dy=-deslocamento_y)

            pyautogui.click(pos.x, pos.y)

            if self._detector.houve_mudanca():

                pyautogui.click(self._botao_confirmar.x, self._botao_confirmar.y)

                return



    def _aguardar_carregamento(self):
        """Aguarda mudanças significativas na tela antes de reiniciar o ciclo."""
        print(f"  ↳ Aguardando concluir atualização...")
        self._detector.aguardar_mudancas(self._mudancas_para_reiniciar)
        print("  ↳ Atualização completo!")
