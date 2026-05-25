"""
formatter.py

Tudo que aparece no terminal passa por aqui.
Este módulo não analisa dados, não acessa PySUS, não toma decisões.
Recebe dados prontos e os exibe com Rich. Só isso.
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

console = Console()


def print_title(title: str, cor: str = "bright_green") -> None:
    console.print(f"\n[bold {cor}]{title}[/bold {cor}]")


def print_panel(conteudo: str, titulo: str = "", cor: str = "bright_green") -> None:
    console.print(Panel(conteudo, title=titulo, border_style=cor))


def print_summary_disease(summary: dict, nome: str, cor: str) -> None:
    console.print()
    console.print(Panel(
        f"[bold]Total de notificações:[/bold] [bright_white]{summary['total']:,}[/bright_white]\n"
        f"[bold]Ano:[/bold]                  [white]{summary['ano']}[/white]\n"
        f"[bold]Estados afetados:[/bold]     [white]{summary['estados_afetados']}[/white]\n"
        f"[bold]Idade média:[/bold]          [white]{summary['idade_media']} anos[/white]",
        title=f"[{cor}] {nome}[/{cor}]",
        border_style=cor,
    ))


def print_table_dict(
    dados: dict[str, int],
    titulo: str,
    col_chave: str,
    col_valor: str,
    total: int,
    cor: str,
    barra: bool = False,
) -> None:
    """Exibe um dicionário {chave: contagem} como tabela Rich."""
    tabela = Table(
        title=titulo,
        box=box.ROUNDED,
        border_style=cor,
        header_style=f"bold {cor}",
        show_header=True,
    )
    tabela.add_column(col_chave, style="bold white")
    tabela.add_column(col_valor, justify="right")
    tabela.add_column("%", justify="right")
    if barra:
        tabela.add_column("", width=20)

    for chave, qtd in dados.items():
        pct = (qtd / total * 100) if total > 0 else 0
        linha = [chave, f"{qtd:,}", f"{pct:.1f}%"]
        if barra:
            linha.append(f"[{cor}]" + "▮" * int(pct / 5) + f"[/{cor}]")
        tabela.add_row(*linha)

    console.print(tabela)


def print_summary_hospitalizations(summary: dict, estado: str, ano: int, mes: int) -> None:
    console.print()
    console.print(Panel(
        f"[bold]Internações:[/bold]     [bright_white]{summary['total']:,}[/bright_white]\n"
        f"[bold]Valor total (R$):[/bold] [green]{summary['valor_total']:,.2f}[/green]\n"
        f"[bold]Valor médio (R$):[/bold] [white]{summary['valor_medio']:,.2f}[/white]\n"
        f"[bold]Média de permanência:[/bold] [yellow]{summary['media_dias']} dias[/yellow]",
        title=f"[cyan] SIH — {estado} / {mes:02d}/{ano}[/cyan]",
        border_style="cyan",
    ))


def print_summary_mortality(summary: dict, estado: str, ano: int) -> None:
    console.print()
    console.print(Panel(
        f"[bold]Total de óbitos:[/bold] [bright_white]{summary['total']:,}[/bright_white]",
        title=f"[red] SIM — {estado} / {ano}[/red]",
        border_style="red",
    ))


def print_header() -> None:
    from datetime import datetime
    console.print()
    console.print(Panel(
        "[bold bright_green]PySUS[/bold bright_green] — Explorador Epidemiológico\n"
        "[dim]Dados Públicos do Sistema Único de Saúde Brasileiro[/dim]\n"
        f"[dim]{datetime.now().strftime('%d/%m/%Y  %H:%M')}[/dim]",
        border_style="bright_green",
        padding=(1, 4),
    ))


def print_pysus_info(version: str) -> None:
    console.print()
    console.print(Panel(
        f"[bold]Versão instalada:[/bold]  [bright_green]PySUS {version}[/bright_green]\n"
        f"[bold]Repositório:[/bold]       https://github.com/AlertaDengue/PySUS\n"
        f"[bold]Documentação:[/bold]      https://pysus.readthedocs.io/\n\n"
        "[bold]Bases disponíveis:[/bold]\n"
        "  [cyan]• SINAN[/cyan] — Agravos de Notificação Compulsória\n"
        "  [cyan]• SIH  [/cyan] — Internações Hospitalares do SUS\n"
        "  [cyan]• SIM  [/cyan] — Informações sobre Mortalidade\n"
        "  [cyan]• SINASC[/cyan]— Nascidos Vivos\n"
        "  [cyan]• CNES [/cyan] — Estabelecimentos de Saúde",
        title="[bright_green] Sobre a PySUS[/bright_green]",
        border_style="bright_green",
        padding=(1, 2),
    ))
    console.print()
