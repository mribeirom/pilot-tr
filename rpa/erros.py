class SessaoExpirada(Exception):
    """O site saiu da sessão logada; o robô pausa até um novo login."""


class FiltrosInvalidos(Exception):
    """A lista não está com os filtros esperados; nada pode ser feito."""


class TravaSeguranca(Exception):
    """Uma conferência falhou antes do clique; o equipamento não foi tocado."""
