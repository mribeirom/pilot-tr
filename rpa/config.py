from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class Tempos:
    pagina: int
    interface: int
    resposta: int
    mensagem: int


@dataclass(frozen=True)
class Config:
    base_url: str
    lista_path: str
    filtro_modelo: str
    filtro_software: str
    filtro_status: str
    modelo: str
    versao_atual: str
    firmware_id: str
    firmware_nome: str
    perfil_dir: Path
    arquivo_progresso: Path
    tempos: Tempos

    @property
    def url_lista(self) -> str:
        return self.base_url + self.lista_path

    def url_equipamento(self, equipamento_id: str) -> str:
        return f"{self.base_url}/tr-069/device/{equipamento_id}/info"


def carregar_config(caminho: str | Path) -> Config:
    caminho = Path(caminho)
    dados = yaml.safe_load(caminho.read_text(encoding="utf-8"))
    pasta = caminho.resolve().parent
    try:
        return Config(
            base_url=str(dados["base_url"]).rstrip("/"),
            lista_path=str(dados["lista_path"]),
            filtro_modelo=str(dados["filtros"]["model"]),
            filtro_software=str(dados["filtros"]["sw_version"]),
            filtro_status=str(dados["filtros"]["status"]),
            modelo=str(dados["modelo"]),
            versao_atual=str(dados["versao_atual"]),
            firmware_id=str(dados["firmware"]["id"]),
            firmware_nome=str(dados["firmware"]["nome"]),
            perfil_dir=pasta / dados["perfil_dir"],
            arquivo_progresso=pasta / dados["arquivo_progresso"],
            tempos=Tempos(**dados["tempos_ms"]),
        )
    except (KeyError, TypeError) as erro:
        raise ValueError(f"Configuração inválida em {caminho}: {erro}") from erro
