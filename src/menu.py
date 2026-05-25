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

            console.print("[1] Explorar Doença (SINAN)")
            console.print("[2] Explorar Internações Hospitalares (SIH)")
            console.print("[3] Explorar Mortalidade (SIM)")
            console.print("[4] Sobre PySUS")
            console.print("[0] Sair")

            option = Prompt.ask("\nEscolha uma opção")

            if option == "1":
                self.show_disease_menu()

            elif option == "2":
                self.show_hospitalization_menu()

            elif option == "3":
                self.show_mortality_menu()

            elif option == "4":
                self.show_about()

            elif option == "0":
                console.print("\nEncerrando sistema...\n")
                break

            else:
                console.print("\n[red]Opção inválida[/red]\n")

    def show_disease_menu(self):

        console.print("\n[bold]Doenças disponíveis (SINAN):[/bold]\n")

        for codigo, meta in DOENCAS.items():
            console.print(f"{codigo} - {meta['nome']}")

        disease = Prompt.ask("\nCódigo da doença").upper()

        if disease not in DOENCAS:
            console.print("\n[red]Doença inválida[/red]\n")
            return

        year = random.randint(2019, 2023)

        df = self.service.get_disease_data(disease, year)

        formatter.print_summary_disease(
            self.disease_analyzer.summary(df),
            DOENCAS[disease]["nome"],
            DOENCAS[disease]["cor"]
        )

        formatter.print_table_dict(
            self.disease_analyzer.count_by_sex(df),
            "Distribuição por Sexo",
            "Sexo",
            "Casos",
            len(df),
            DOENCAS[disease]["cor"],
            barra=True
        )

        formatter.print_table_dict(
            self.disease_analyzer.top_states(df),
            "Top Estados com Mais Notificações",
            "UF",
            "Casos",
            len(df),
            DOENCAS[disease]["cor"]
        )

        input("\nPressione ENTER para continuar...")

    def show_hospitalization_menu(self):

        console.print("\n[bold]Estados disponíveis (UFs):[/bold]\n")

        for uf, nome_estado in ESTADOS.items():
            console.print(f"{uf} - {nome_estado}")

        state = Prompt.ask("\nDigite a sigla do Estado (UF)").upper()

        if state not in ESTADOS:
            console.print("\n[red]Estado inválido[/red]\n")
            return

        year = random.randint(2019, 2023)
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
            "Internações por Sexo",
            "Sexo",
            "Internações",
            len(df),
            "cyan",
            barra=True
        )

        formatter.print_table_dict(
            self.hosp_analyzer.top_diagnoses(df),
            "Principais Diagnósticos (CID-10)",
            "CID-10",
            "Internações",
            len(df),
            "cyan"
        )

        input("\nPressione ENTER para continuar...")

    def show_mortality_menu(self):

        console.print("\n[bold]Estados disponíveis (UFs):[/bold]\n")

        for uf, nome_estado in ESTADOS.items():
            console.print(f"{uf} - {nome_estado}")

        state = Prompt.ask("\nDigite a sigla do Estado (UF)").upper()

        if state not in ESTADOS:
            console.print("\n[red]Estado inválido[/red]\n")
            return

        year = random.randint(2019, 2023)

        df = self.service.get_mortality(state, year)

        formatter.print_summary_mortality(
            self.mort_analyzer.summary(df),
            ESTADOS[state],
            year
        )

        formatter.print_table_dict(
            self.mort_analyzer.count_by_sex(df),
            "Óbitos por Sexo",
            "Sexo",
            "Óbitos",
            len(df),
            "red",
            barra=True
        )

        formatter.print_table_dict(
            self.mort_analyzer.top_causes(df),
            "Principais Causas Básicas de Óbito (CID-10)",
            "CID-10",
            "Óbitos",
            len(df),
            "red"
        )

        input("\nPressione ENTER para continuar...")

    def show_about(self):

        print("\nPySUS funcionando corretamente!\n")
        print(f"Versão instalada: {pysus.__version__}")

        input("\nPressione ENTER para continuar...")