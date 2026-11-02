"""Páginas falsas com a mesma estrutura da OLT Cloud, sem dados de clientes."""


def pagina_lista(
    linhas, pagina=1, tem_proxima=False, modelo="PSDN", software="09", status="Online", logado=True
):
    opcoes = "".join(
        f'<option{" selected" if texto == status else ""}>{texto}</option>'
        for texto in ("", "Online", "Offline")
    )
    corpo = "".join(
        f"""<tr>
          <td><a href="/tr-069/device/{id_}/info">Cliente</a></td><td>Huawei</td>
          <td><a href="/tr-069/device/{id_}/info">{modelo_linha}</a></td><td>VER.A</td>
          <td><a href="/tr-069/device/{id_}/info">{software_linha}</a></td>
          <td></td><td></td><td></td><td></td><td></td>
          <td>{status_linha[0] if status_linha else "Online"}</td></tr>"""
        for id_, modelo_linha, software_linha, *status_linha in linhas
    )
    proxima = f'<a href="?page={pagina + 1}" class="ui button">prox</a>' if tem_proxima else ""
    sair = '<a href="/logout">Sair</a>' if logado else ""
    return f"""<html><body>{sair}
      <input id="buscar_model" value="{modelo}"><input id="buscar_sw_version" value="{software}">
      <select id="buscar_online">{opcoes}</select>
      <div class="busca-pag">{proxima}</div>
      <table><tbody>{corpo}</tbody></table></body></html>"""


def pagina_equipamento(
    id_="100",
    modelo="PSDN-AX30-40",
    versao="3.0.0.43(09)",
    item_valor="15",
    item_texto=" Ax3s - 4.2.0.52(SP5C947)",
    href_escolhido=None,
    liberar_botao=True,
    toast="",
):
    href = href_escolhido or f"/acs_software/do_update/15/{id_}?back_page=/tr-069/device/{id_}/info"
    habilitar = "b.classList.remove('disabled');" if liberar_botao else ""
    return f"""<html><head><style>
      .menu, #acs_firmware_update_modal {{ display: none; }}
      .aberto {{ display: block !important; }}
      .disabled {{ pointer-events: none; }}
      </style></head><body>
      <a href="/logout">Sair</a><p>{modelo}</p><p>{versao}</p>{toast}
      <div class="acs_menu"><div class="menu"><div class="item">Outro menu</div></div></div>
      <div class="acs_menu" onclick="this.querySelector('.menu').classList.add('aberto')">Ações
        <div class="menu">
          <div class="item" onclick="modal_reboot()">Reiniciar</div>
          <div class="item" onclick="abrirModal('acs_firmware_update_modal')">Atualizar Firmware</div>
          <div class="item" onclick="restaurar()">Restaurar</div>
        </div>
      </div>
      <div id="acs_firmware_update_modal">
        <div class="ui dropdown" onclick="this.querySelector('.menu').classList.add('aberto')">
          Selecione
          <div class="menu"><div class="item" data-value="{item_valor}" data-text="{item_texto}"
            onclick="escolher()">{item_texto}</div></div>
        </div>
        <div class="actions">
          <a class="ui button deny" onclick="fecharModal()">Cancelar</a>
          <a class="ui button positive disabled" id="btn_ok_firmware_update"
            href="/tr-069/device/abc/factory_reset?back_page=x">Atualizar</a>
        </div>
      </div>
      <script>
        const modal = document.getElementById('acs_firmware_update_modal');
        function abrirModal() {{ modal.classList.add('aberto'); }}
        function fecharModal() {{ modal.classList.remove('aberto'); }}
        function restaurar() {{ window.restaurou = true; }}
        function escolher() {{
          const b = document.getElementById('btn_ok_firmware_update');
          {habilitar}
          b.setAttribute('href', '{href}');
        }}
      </script></body></html>"""


def toast(texto, erro=True):
    classe = "error ui toast compact" if erro else "success ui toast compact"
    return f'<div class="{classe}">{texto}</div>'
