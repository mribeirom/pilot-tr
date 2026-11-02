import json
import os
from datetime import datetime
from pathlib import Path

STATUS_ERRO = "erro"


class Progresso:
    """IDs que já receberam o clique em Atualizar, com a mensagem do site."""

    def __init__(self, caminho: str | Path):
        self.caminho = Path(caminho)
        self.registros: dict[str, dict] = {}
        if self.caminho.exists():
            self.registros = json.loads(self.caminho.read_text(encoding="utf-8"))

    def ja_enviado(self, equipamento_id: str, repetir_erros: bool = False) -> bool:
        registro = self.registros.get(equipamento_id)
        if registro is None:
            return False
        return not (repetir_erros and registro["status"] == STATUS_ERRO)

    def registrar(self, equipamento_id: str, status: str, mensagem: str) -> None:
        self.registros[equipamento_id] = {
            "status": status,
            "mensagem": mensagem,
            "quando": datetime.now().astimezone().isoformat(timespec="seconds"),
        }
        temporario = self.caminho.with_suffix(".tmp")
        temporario.write_text(
            json.dumps(self.registros, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        os.replace(temporario, self.caminho)
