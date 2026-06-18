import random
import pysus

from rich.console import Console
from rich.prompt import Prompt

from src.epidemiology_service import (
    EpidemiologyService,
    DOENCAS,
    ESTADOS
)

from src.disease_analyzer import (
    DiseaseAnalyzer,
    HospitalizationAnalyzer,
    MortalityAnalyzer
)

from src import formatter


console = Console()


class Menu:

    def __init__(self):
        self.service = EpidemiologyService()
        self.disease_analyzer = DiseaseAnalyzer()
        self.hosp_analyzer = HospitalizationAnalyzer()
        self.mort_analyzer = MortalityAnalyzer()

    def run(self):
        while True:
            formatter.print_header()
            console.print("[1] Sobre PySUS")
            console.print("[2] Comparacao por Doenca")
            console.print("[3] Evolucao Temporal")
            console.print("[4] Distribuicao Geografica")
            console.print("[5] Internacoes Hospitalares (SIH)")
            console.print("[6] Mortalidade (SIM)")
            console.print("[0] Sair")

            option = Prompt.ask("\nEscolha uma opcao")

            if option == "1":
                self.show_about()
            elif option == "2":
                self.show_disease_menu()
            elif option == "3":
                self.show_temporal_analysis()
            elif option == "4":
                self.show_geographic_analysis()
            elif option == "5":
                self.show_hospitalization_menu()
            elif option == "6":
                self.show_mortality_menu()
            elif option == "0":
                console.print("\nEncerrando sistema...\n")
                break
            else:
                console.print("\n[red]Opcao invalida[/red]\n")

    def show_disease_menu(self):
        console.print("\n[bold]Doencas disponiveis (SINAN):[/bold]\n")

        for codigo, meta in DOENCAS.items():
            console.print(f"{codigo} - {meta['nome']}")

        user_input = Prompt.ask("\nDigite o codigo OU nome da doenca").upper()

        disease = None
        for codigo, meta in DOENCAS.items():
            if user_input == codigo or user_input == meta["nome"].upper():
                disease = codigo
                break

        if disease is None:
            console.print("\n[red]Doenca invalida[/red]\n")
            return

        year = random.randint(2019, 2026)
        df = self.service.get_disease_data(disease, year)

        formatter.print_summary_disease(
            self.disease_analyzer.summary(df),
            DOENCAS[disease]["nome"],
            DOENCAS[disease]["cor"]
        )

        formatter.print_table_dict(
            self.disease_analyzer.count_by_sex(df),
            "Distribuicao por Sexo",
            "Sexo",
            "Casos",
            len(df),
            DOENCAS[disease]["cor"],
            barra=True
        )

        formatter.print_table_dict(
            self.disease_analyzer.top_states(df),
            "Top Estados com Mais Notificacoes",
            "UF",
            "Casos",
            len(df),
            DOENCAS[disease]["cor"]
        )

        input("\nPressione ENTER para continuar...")

    def show_temporal_analysis(self):
        console.print("\n[bold cyan]Evolucao Temporal Epidemiologica[/bold cyan]\n")

        for codigo, meta in DOENCAS.items():
            console.print(f"{codigo} - {meta['nome']}")

        user_input = Prompt.ask("\nDigite o codigo OU nome da doenca").upper()

        disease = None
        for codigo, meta in DOENCAS.items():
            if user_input == codigo or user_input == meta["nome"].upper():
                disease = codigo
                break

        if disease is None:
            console.print("\n[red]Doenca invalida[/red]\n")
            return

        nome = DOENCAS[disease]["nome"]
        cor = DOENCAS[disease]["cor"]

        console.print()
        console.rule(f"[bold {cor}]{nome} - Evolucao Temporal[/bold {cor}]")

        for year in range(2020, 2027):
            df = self.service.get_disease_data(disease, year)
            total = len(df)
            sex_data = self.disease_analyzer.count_by_sex(df)
            fem = sex_data.get("Feminino", 0)
            masc = sex_data.get("Masculino", 0)
            pct_f = (fem / total * 100) if total else 0
            pct_m = (masc / total * 100) if total else 0
            barras = "▮" * max(1, int(total / 300))

            console.print(f"\n[bold white]{year}[/bold white]")
            console.print(f"Casos registrados: [bold {cor}]{total:,}[/bold {cor}]")
            console.print(f"Mulheres -> [magenta]{pct_f:.1f}%[/magenta]")
            console.print(f"Homens   -> [cyan]{pct_m:.1f}%[/cyan]")
            console.print(f"[{cor}]{barras}[/{cor}]")

        input("\nPressione ENTER para continuar...")

    def show_geographic_analysis(self):
        console.print("\n[bold green]Distribuicao Geografica[/bold green]\n")

        for codigo, meta in DOENCAS.items():
            console.print(f"{codigo} - {meta['nome']}")

        user_input = Prompt.ask("\nDigite o codigo OU nome da doenca").upper()

        disease = None
        for codigo, meta in DOENCAS.items():
            if user_input == codigo or user_input == meta["nome"].upper():
                disease = codigo
                break

        if disease is None:
            console.print("\n[red]Doenca invalida[/red]\n")
            return

        year = 2026
        df = self.service.get_disease_data(disease, year)

        formatter.print_table_dict(
            self.disease_analyzer.top_states(df),
            f"Estados mais afetados - {DOENCAS[disease]['nome']}",
            "UF",
            "Casos",
            len(df),
            DOENCAS[disease]["cor"],
            barra=True
        )

        input("\nPressione ENTER para continuar...")

    def show_hospitalization_menu(self):
        console.print("\n[bold]Estados disponiveis (UFs):[/bold]\n")

        for uf, nome_estado in ESTADOS.items():
            console.print(f"{uf} - {nome_estado}")

        state = Prompt.ask("\nDigite a sigla do Estado (UF)").upper()

        if state not in ESTADOS:
            console.print("\n[red]Estado invalido[/red]\n")
            return

        year = random.randint(2019, 2026)
        month = random.randint(1, 12)
        df = self.service.get_hospitalizations(state, year, month)

        formatter.print_summary_hospitalizations(
            self.hosp_analyzer.summary(df),
            ESTADOS[state],
            year,
            month
        )

        formatter.print_table_dict(
            self.hosp_analyzer.count_by_sex(df),
            "Internacoes por Sexo",
            "Sexo",
            "Internacoes",
            len(df),
            "cyan",
            barra=True
        )

        formatter.print_table_dict(
            self.hosp_analyzer.top_diagnoses(df),
            "Principais Diagnosticos (CID-10)",
            "CID-10",
            "Internacoes",
            len(df),
            "cyan"
        )

        input("\nPressione ENTER para continuar...")

    def show_mortality_menu(self):
        console.print("\n[bold]Estados disponiveis (UFs):[/bold]\n")

        for uf, nome_estado in ESTADOS.items():
            console.print(f"{uf} - {nome_estado}")

        state = Prompt.ask("\nDigite a sigla do Estado (UF)").upper()

        if state not in ESTADOS:
            console.print("\n[red]Estado invalido[/red]\n")
            return

        year = random.randint(2019, 2026)
        df = self.service.get_mortality(state, year)

        formatter.print_summary_mortality(
            self.mort_analyzer.summary(df),
            ESTADOS[state],
            year
        )

        formatter.print_table_dict(
            self.mort_analyzer.count_by_sex(df),
            "Obitos por Sexo",
            "Sexo",
            "Obitos",
            len(df),
            "red",
            barra=True
        )

        formatter.print_table_dict(
            self.mort_analyzer.top_causes(df),
            "Principais Causas Basicas de Obito (CID-10)",
            "CID-10",
            "Obitos",
            len(df),
            "red"
        )

        input("\nPressione ENTER para continuar...")

    def show_about(self):
        formatter.print_pysus_info(pysus.__version__)
        input("\nPressione ENTER para continuar...")