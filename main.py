import argparse
import sys

from playwright.sync_api import sync_playwright

from rpa.config import carregar_config
from rpa.equipamento import bloquear_factory_reset
from rpa.erros import FiltrosInvalidos, SessaoExpirada
from rpa.executor import executar, imprimir_resumo
from rpa.lista import abrir_lista, coletar_equipamentos, conferir_filtros
from rpa.progresso import Progresso


def ler_argumentos() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Atualiza o firmware do lote na OLT Cloud.")
    parser.add_argument("--config", default="config.yaml")
    modo = parser.add_mutually_exclusive_group()
    modo.add_argument("--coletar", action="store_true", help="só lista o lote")
    modo.add_argument("--simular", action="store_true", help="cancela o modal em vez de atualizar")
    parser.add_argument(
        "--repetir-erros", action="store_true", help="reenvia IDs que receberam mensagem de erro"
    )
    return parser.parse_args()


def main() -> int:
    sys.stdout.reconfigure(errors="replace")
    argumentos = ler_argumentos()
    cfg = carregar_config(argumentos.config)
    progresso = Progresso(cfg.arquivo_progresso)

    with sync_playwright() as playwright:
        contexto = playwright.chromium.launch_persistent_context(
            str(cfg.perfil_dir), headless=False, no_viewport=True
        )
        bloquear_factory_reset(contexto)
        page = contexto.pages[0] if contexto.pages else contexto.new_page()
        page.goto(cfg.url_lista, timeout=cfg.tempos.pagina)
        input(
            f"\nFaça login e aplique os filtros Modelo={cfg.filtro_modelo}, "
            f"Software={cfg.filtro_software} e Status={cfg.filtro_status} na lista. "
            "Depois pressione ENTER aqui... "
        )
        try:
            if argumentos.coletar:
                abrir_lista(page, cfg)
                conferir_filtros(page, cfg)
                equipamentos, fora_do_lote = coletar_equipamentos(page, cfg)
                for equipamento in equipamentos:
                    print(f"{equipamento.id}  {equipamento.status}")
                print(f"\nLote: {len(equipamentos)}. Fora do lote: {fora_do_lote}.")
            else:
                resumo = executar(
                    page,
                    cfg,
                    progresso,
                    simular=argumentos.simular,
                    repetir_erros=argumentos.repetir_erros,
                )
                imprimir_resumo(resumo)
        except (FiltrosInvalidos, SessaoExpirada) as erro:
            print(f"Parado antes de atualizar: {type(erro).__name__}: {erro}")
            return 1
        finally:
            contexto.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
