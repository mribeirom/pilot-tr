"""Módulo de detecção de mudanças visuais na tela."""

import pyautogui
from PIL import ImageChops, ImageStat


class DetectorDeTela:
    """Detecta mudanças significativas na tela comparando screenshots."""

    def __init__(self, tolerancia: float = 3.0):
        self._tolerancia = tolerancia
        self._screenshot_anterior = None

    @property
    def tolerancia(self) -> float:
        return self._tolerancia

    @tolerancia.setter
    def tolerancia(self, valor: float):
        self._tolerancia = valor

    def capturar(self):
        """Captura um screenshot e armazena como referência."""
        self._screenshot_anterior = pyautogui.screenshot()
        return self._screenshot_anterior

    def houve_mudanca(self) -> bool:
        """Compara o screenshot atual com o anterior e retorna True se houve mudança."""
        atual = pyautogui.screenshot()
        mudou = not self._sao_parecidas(self._screenshot_anterior, atual)
        self._screenshot_anterior = atual
        return mudou

    def aguardar_mudancas(self, quantidade: int, intervalo: float = 1.0):
        """Aguarda até que um número específico de mudanças significativas seja detectado.

        Args:
            quantidade: Número de mudanças a aguardar.
            intervalo: Tempo em segundos entre cada verificação.
        """
        import time

        self.capturar()
        mudancas = 0

        while mudancas < quantidade:
            time.sleep(intervalo)
            if self.houve_mudanca():
                mudancas += 1


    def _sao_parecidas(self, img1, img2) -> bool:
        """Compara duas imagens e retorna True se forem visualmente parecidas."""
        img1 = img1.convert("RGB")
        img2 = img2.convert("RGB")

        diferenca = ImageChops.difference(img1, img2)
        media = sum(ImageStat.Stat(diferenca).mean) / 3

        return media < self._tolerancia
