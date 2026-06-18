from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

console = Console()


def print_title(title, cor="bright_green"):
    console.print(f"\n[bold {cor}]{title}[/bold {cor}]")


def print_panel(conteudo, titulo="", cor="bright_green"):
    console.print(Panel(conteudo, title=titulo, border_style=cor))


def print_summary_disease(summary, nome, cor):
    console.print()
    console.print(Panel(
        f"[bold]Total de notificacoes:[/bold] [bright_white]{summary['total']:,}[/bright_white]\n"
        f"[bold]Ano:[/bold]                  [white]{summary['ano']}[/white]\n"
        f"[bold]Estados afetados:[/bold]     [white]{summary['estados_afetados']}[/white]\n"
        f"[bold]Idade media:[/bold]          [white]{summary['idade_media']} anos[/white]",
        title=f"[{cor}] {nome}[/{cor}]",
        border_style=cor,
    ))


def print_table_dict(dados, titulo, col_chave, col_valor, total, cor, barra=False):
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


def print_summary_hospitalizations(summary, estado, ano, mes):
    console.print()
    console.print(Panel(
        f"[bold]Internacoes:[/bold]     [bright_white]{summary['total']:,}[/bright_white]\n"
        f"[bold]Valor total (R$):[/bold] [green]{summary['valor_total']:,.2f}[/green]\n"
        f"[bold]Valor medio (R$):[/bold] [white]{summary['valor_medio']:,.2f}[/white]\n"
        f"[bold]Media de permanencia:[/bold] [yellow]{summary['media_dias']} dias[/yellow]",
        title=f"[cyan] SIH - {estado} / {mes:02d}/{ano}[/cyan]",
        border_style="cyan",
    ))


def print_summary_mortality(summary, estado, ano):
    console.print()
    console.print(Panel(
        f"[bold]Total de obitos:[/bold] [bright_white]{summary['total']:,}[/bright_white]",
        title=f"[red] SIM - {estado} / {ano}[/red]",
        border_style="red",
    ))


def print_header():
    from datetime import datetime
    console.print()
    console.print(Panel(
        "[bold bright_green]PySUS[/bold bright_green] - Explorador Epidemiologico\n"
        "[dim]Dados Publicos do Sistema Unico de Saude Brasileiro[/dim]\n"
        f"[dim]{datetime.now().strftime('%d/%m/%Y  %H:%M')}[/dim]",
        border_style="bright_green",
        padding=(1, 4),
    ))


def print_pysus_info(version):
    console.print()
    console.print(Panel(
        f"[bold]Versao instalada:[/bold]  [bright_green]PySUS {version}[/bright_green]\n"
        f"[bold]Repositorio:[/bold]       https://github.com/AlertaDengue/PySUS\n"
        f"[bold]Documentacao:[/bold]      https://pysus.readthedocs.io/\n\n"
        "[bold]Bases disponiveis:[/bold]\n"
        "  [cyan]SINAN[/cyan] - Agravos de Notificacao Compulsoria\n"
        "  [cyan]SIH  [/cyan] - Internacoes Hospitalares do SUS\n"
        "  [cyan]SIM  [/cyan] - Informacoes sobre Mortalidade\n"
        "  [cyan]SINASC[/cyan] - Nascidos Vivos\n"
        "  [cyan]CNES [/cyan] - Estabelecimentos de Saude",
        title="[bright_green] Sobre a PySUS[/bright_green]",
        border_style="bright_green",
        padding=(1, 2),
    ))
    console.print()