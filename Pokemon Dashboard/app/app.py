from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from shiny import App, reactive, render, ui


APP_DIR = Path(__file__).resolve().parent
DATA_DIR = APP_DIR / "data"


def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    pokedex = pd.read_csv(DATA_DIR / "pokedex.csv")
    valid_moves = pd.read_csv(DATA_DIR / "valid_moves.csv")
    natures = pd.read_csv(DATA_DIR / "natures.csv")

    valid_moves["Name"] = valid_moves["Name"].astype(str).str.strip()
    valid_moves["Move"] = valid_moves["Move"].astype(str).str.strip()

    pokemon = pokedex[
        [
            "Num",
            "Name",
            "Type1",
            "Type2",
            "HP",
            "ATK",
            "DEF",
            "SPA",
            "SPD",
            "SPE",
            "Total",
            "ability_0",
            "ability_1",
            "ability_H",
            "height(m)",
            "weight(kg)",
            "mega",
        ]
    ].copy()

    move_counts = valid_moves.groupby(["Num", "Name"]).size().rename("Move Count")
    pokemon = pokemon.merge(move_counts, on=["Num", "Name"], how="left")

    pokemon["Move Count"] = pokemon["Move Count"].fillna(0).astype(int)
    pokemon["Type2"] = pokemon["Type2"].fillna("")
    pokemon["ability_1"] = pokemon["ability_1"].fillna("")
    pokemon["ability_H"] = pokemon["ability_H"].fillna("")
    pokemon["mega"] = pokemon["mega"].astype(str).str.upper()
    pokemon["Abilities"] = pokemon[["ability_0", "ability_1", "ability_H"]].apply(
        lambda row: ", ".join(
            [
                str(value).strip()
                for value in row
                if pd.notna(value) and str(value).strip() and str(value).strip().lower() != "nan"
            ]
        ),
        axis=1,
    )

    return pokemon, valid_moves, natures


POKEMON_DF, MOVE_LOOKUP, NATURES_DF = load_data()
MOVES_DF = pd.read_csv(DATA_DIR / "moves.csv")
TYPECHART_DF = pd.read_csv(DATA_DIR / "typechart.csv")
ALL_MOVES = sorted(MOVE_LOOKUP["Move"].dropna().unique().tolist())
ALL_TYPES = sorted(POKEMON_DF["Type1"].dropna().unique().tolist())
POKEMON_NAMES = sorted(POKEMON_DF["Name"].dropna().unique().tolist())
POKEMON_NAMES_BY_ID = POKEMON_DF.sort_values(["Num", "Name"])["Name"].dropna().tolist()
ALL_ABILITIES = sorted(
    {
        str(value).strip()
        for column in ["ability_0", "ability_1", "ability_H"]
        for value in POKEMON_DF[column].dropna()
        if str(value).strip() and str(value).strip().lower() != "nan"
    }
)


def build_typechart_styles(df: pd.DataFrame) -> list[dict[str, object]]:
    color_map = {
        2.0: "#dff6df",
        1.0: "#ffffff",
        0.5: "#f8dede",
        0.0: "#e5e7eb",
    }
    styles: list[dict[str, object]] = []

    for row_idx in range(len(df)):
        for col_idx, column in enumerate(df.columns[1:], start=1):
            value = float(df.iloc[row_idx][column])
            background = color_map.get(value)
            if background is None:
                continue

            styles.append(
                {
                    "location": "body",
                    "rows": [row_idx],
                    "cols": [col_idx],
                    "style": {
                        "background-color": background,
                        "color": "#16202a",
                    },
                }
            )

    return styles


def build_natures_styles(df: pd.DataFrame) -> list[dict[str, object]]:
    styles: list[dict[str, object]] = []
    color_by_column = {
        "Increased Stat": "#dff6df",
        "Decreased Stat": "#f8dede",
    }

    for column_name, background in color_by_column.items():
        col_idx = df.columns.get_loc(column_name)
        for row_idx in range(len(df)):
            if pd.isna(df.iloc[row_idx][column_name]):
                continue

            styles.append(
                {
                    "location": "body",
                    "rows": [row_idx],
                    "cols": [col_idx],
                    "style": {
                        "background-color": background,
                        "color": "#16202a",
                    },
                }
            )

    return styles


def build_move_list_styles(df: pd.DataFrame) -> list[dict[str, object]]:
    type_colors = {
        "Normal": {"background-color": "#ffffff", "color": "#16202a"},
        "Fire": {"background-color": "#f8dede", "color": "#16202a"},
        "Water": {"background-color": "#dbeafe", "color": "#16202a"},
        "Electric": {"background-color": "#fef3c7", "color": "#16202a"},
        "Grass": {"background-color": "#dff6df", "color": "#16202a"},
        "Ice": {"background-color": "#ecfeff", "color": "#16202a"},
        "Fighting": {"background-color": "#fed7aa", "color": "#16202a"},
        "Poison": {"background-color": "#f3e8ff", "color": "#16202a"},
        "Ground": {"background-color": "#ead7c3", "color": "#16202a"},
        "Flying": {"background-color": "#d9f0ff", "color": "#16202a"},
        "Psychic": {"background-color": "#f5d0fe", "color": "#16202a"},
        "Bug": {"background-color": "#e8f5c8", "color": "#16202a"},
        "Rock": {"background-color": "#f2dfc2", "color": "#16202a"},
        "Ghost": {"background-color": "#d9c2f0", "color": "#16202a"},
        "Dragon": {"background-color": "#bcd4e6", "color": "#16202a"},
        "Dark": {"background-color": "#6b7280", "color": "#f8fafc"},
        "Fairy": {"background-color": "#fbcfe8", "color": "#16202a"},
        "???": {"background-color": "#ffffff", "color": "#16202a"},
    }
    styles: list[dict[str, object]] = []

    for row_idx in range(len(df)):
        move_type = str(df.iloc[row_idx].get("Type", "")).strip()
        style = type_colors.get(move_type)
        if style is None:
            continue

        styles.append(
            {
                "location": "body",
                "rows": [row_idx],
                "style": style,
            }
        )

    return styles


def type_palette(type_name: str) -> dict[str, str]:
    palettes = {
        "Normal": {"fill": "#ffffff", "line": "#8a8f98", "text": "#16202a"},
        "Fire": {"fill": "#f8dede", "line": "#dc2626", "text": "#16202a"},
        "Water": {"fill": "#dbeafe", "line": "#2563eb", "text": "#16202a"},
        "Electric": {"fill": "#fef3c7", "line": "#d4a017", "text": "#16202a"},
        "Grass": {"fill": "#dff6df", "line": "#2f855a", "text": "#16202a"},
        "Ice": {"fill": "#ecfeff", "line": "#38bdf8", "text": "#16202a"},
        "Fighting": {"fill": "#fed7aa", "line": "#c05621", "text": "#16202a"},
        "Poison": {"fill": "#f3e8ff", "line": "#9333ea", "text": "#16202a"},
        "Ground": {"fill": "#ead7c3", "line": "#a16207", "text": "#16202a"},
        "Flying": {"fill": "#d9f0ff", "line": "#3b82f6", "text": "#16202a"},
        "Psychic": {"fill": "#f5d0fe", "line": "#db2777", "text": "#16202a"},
        "Bug": {"fill": "#e8f5c8", "line": "#65a30d", "text": "#16202a"},
        "Rock": {"fill": "#f2dfc2", "line": "#b45309", "text": "#16202a"},
        "Ghost": {"fill": "#d9c2f0", "line": "#7c3aed", "text": "#16202a"},
        "Dragon": {"fill": "#bcd4e6", "line": "#5d8aa8", "text": "#16202a"},
        "Dark": {"fill": "#6b7280", "line": "#374151", "text": "#f8fafc"},
        "Fairy": {"fill": "#fbcfe8", "line": "#ec4899", "text": "#16202a"},
        "???": {"fill": "#ffffff", "line": "#8a8f98", "text": "#16202a"},
    }
    return palettes.get(type_name, {"fill": "#dbeafe", "line": "#1f7a8c", "text": "#16202a"})


TYPECHART_STYLES = build_typechart_styles(TYPECHART_DF)
NATURES_STYLES = build_natures_styles(NATURES_DF)


app_ui = ui.page_fillable(
    ui.tags.style(
        """
        :root {
            --bg: #e8eef2;
            --panel: rgba(248, 252, 255, 0.94);
            --panel-strong: #f2f8fb;
            --ink: #16202a;
            --muted: #5a6b78;
            --line: #c5d4df;
            --accent: #1f7a8c;
            --accent-dark: #145665;
            --shadow: rgba(34, 60, 80, 0.14);
        }
        body {
            background:
                radial-gradient(circle at 0% 0%, rgba(114, 201, 221, 0.34), transparent 26%),
                radial-gradient(circle at 100% 0%, rgba(153, 180, 242, 0.26), transparent 24%),
                linear-gradient(180deg, #eef5f9 0%, #dce6ee 100%);
            color: var(--ink);
        }
        .app-shell {
            padding: 1.2rem;
            gap: 1rem;
        }
        .hero, .panel, .stat-card {
            background: var(--panel);
            border: 1px solid var(--line);
            box-shadow: 0 16px 40px var(--shadow);
        }
        .hero {
            border-radius: 28px;
            padding: 1.6rem;
        }
        .hero h1 {
            margin: 0 0 0.4rem 0;
            font-size: 2.1rem;
        }
        .hero p {
            margin: 0;
            color: var(--muted);
            max-width: 70rem;
        }
        .hero-band {
            display: inline-block;
            margin-bottom: 0.75rem;
            padding: 0.35rem 0.7rem;
            border-radius: 999px;
            background: linear-gradient(90deg, #d7f0f4, #dde8ff);
            color: var(--accent-dark);
            font-weight: 700;
            font-size: 0.8rem;
            letter-spacing: 0.05em;
            text-transform: uppercase;
        }
        .stat-card {
            border-radius: 22px;
            padding: 1rem 1.1rem;
            min-height: 116px;
        }
        .stat-label {
            color: var(--muted);
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }
        .stat-value {
            font-size: 2rem;
            font-weight: 800;
            margin-top: 0.35rem;
        }
        .stat-note {
            margin-top: 0.35rem;
            color: var(--muted);
        }
        .sidebar-card, .results-card {
            border-radius: 24px;
            padding: 1rem;
        }
        .sidebar-card {
            background: var(--panel-strong);
        }
        .results-card {
            margin-bottom: 1rem;
        }
        .results-card h3 {
            margin-top: 0;
            margin-bottom: 0.6rem;
        }
        .pokemon-profile {
            display: grid;
            grid-template-columns: 1fr;
            gap: 0.8rem;
        }
        .profile-item {
            background: rgba(240, 248, 251, 0.92);
            border: 1px solid var(--line);
            border-radius: 18px;
            padding: 0.85rem;
        }
        .profile-item strong {
            display: block;
            font-size: 0.8rem;
            color: var(--muted);
            text-transform: uppercase;
            letter-spacing: 0.06em;
            margin-bottom: 0.35rem;
        }
        .chart-card {
            min-height: 100%;
        }
        .shiny-data-grid {
            font-size: 0.95rem;
        }
        .nav-tabs {
            border-bottom: 1px solid var(--line);
        }
        .nav-tabs .nav-link.active {
            background: #f6fbff;
            border-color: var(--line) var(--line) #f6fbff;
            color: var(--accent-dark);
            font-weight: 700;
        }
        """
    ),
    ui.div(
        {"class": "app-shell"},
        ui.div(
            {"class": "hero"},
            ui.div({"class": "hero-band"}, "Serverless Shinylive Dashboard"),
            ui.h1("Jake's Dashboard"),
            ui.p(
                "Browse the Champions CSVs in one place. Filter by moves, abilities, names, and typing, "
                "then inspect individual Pokemon with type chart and nature tables nearby."
            ),
        ),
        ui.layout_columns(
            ui.output_ui("result_count_card"),
            ui.output_ui("move_count_card"),
            ui.output_ui("type_summary_card"),
            ui.output_ui("mega_summary_card"),
            col_widths=[3, 3, 3, 3],
        ),
        ui.navset_tab(
            ui.nav_panel(
                "General Search",
                ui.layout_sidebar(
                    ui.sidebar(
                        ui.div(
                            {"class": "panel sidebar-card"},
                            ui.h4("Move Filters"),
                            ui.input_selectize(
                                "moves",
                                "Learnable moves",
                                choices=ALL_MOVES,
                                selected=[],
                                multiple=True,
                                options={"placeholder": "Type one or more moves"},
                            ),
                            ui.input_radio_buttons(
                                "match_mode",
                                "Match mode",
                                choices={"all": "Must learn all selected moves", "any": "Can learn any selected move"},
                                selected="all",
                            ),
                            ui.hr(),
                            ui.h4("Pokemon Filters"),
                            ui.input_text("name_search", "Pokemon name contains", placeholder="Gengar"),
                            ui.input_selectize(
                                "ability_filter",
                                "Abilities",
                                choices=ALL_ABILITIES,
                                selected=[],
                                multiple=True,
                                options={"placeholder": "Type one or more abilities"},
                            ),
                            ui.input_radio_buttons(
                                "ability_match_mode",
                                "Ability match mode",
                                choices={"all": "Must have all selected abilities", "any": "Can have any selected ability"},
                                selected="any",
                            ),
                            ui.input_select("type_filter", "Primary type", choices=["All"] + ALL_TYPES, selected="All"),
                            ui.input_checkbox("mega_only", "Mega forms only", value=False),
                            ui.input_slider("min_total", "Minimum base stat total", min=0, max=800, value=450),
                            ui.hr(),
                            ui.input_selectize(
                                "focus_pokemon",
                                "Inspect a Pokemon",
                                choices=POKEMON_NAMES,
                                selected="Charizard" if "Charizard" in POKEMON_NAMES else POKEMON_NAMES[0],
                                multiple=False,
                            ),
                        ),
                        width=340,
                    ),
                    ui.div(
                        {"class": "panel results-card"},
                        ui.h3("Matching Pokemon"),
                        ui.output_text_verbatim("active_filters"),
                        ui.output_data_frame("pokemon_table"),
                    ),
                    ui.div(
                        {"class": "panel results-card"},
                        ui.h3("Moves For Selected Pokemon"),
                        ui.output_data_frame("selected_moves_table"),
                    ),
                ),
            ),
            ui.nav_panel(
                "Pokemon Search",
                ui.div(
                    {"class": "panel sidebar-card"},
                    ui.input_radio_buttons(
                        "pokemon_search_sort",
                        "Pokemon order",
                        choices={"alpha": "Alphabetical", "id": "National Dex ID"},
                        selected="alpha",
                        inline=True,
                    ),
                    ui.input_select(
                        "pokemon_search_name",
                        "Pokemon",
                        choices=POKEMON_NAMES,
                        selected="Charizard" if "Charizard" in POKEMON_NAMES else POKEMON_NAMES[0],
                    ),
                ),
                ui.layout_columns(
                    ui.div(
                        {"class": "panel results-card chart-card"},
                        ui.h3("Stat Radar"),
                        ui.output_plot("pokemon_radar_chart", height="580px"),
                    ),
                    ui.div(
                        {"class": "panel results-card"},
                        ui.output_ui("pokemon_search_profile"),
                    ),
                    col_widths=[9, 3],
                ),
                ui.div(
                    {"class": "panel results-card"},
                    ui.h3("Move List"),
                    ui.output_data_frame("pokemon_search_moves_table"),
                ),
            ),
            ui.nav_panel(
                "Stat Histograms",
                ui.div(
                    {"class": "panel sidebar-card"},
                    ui.layout_columns(
                        ui.input_select(
                            "hist_type",
                            "Type filter",
                            choices=["All"] + ALL_TYPES,
                            selected="All",
                        ),
                        ui.input_radio_buttons(
                            "hist_include_megas",
                            "Include Megas",
                            choices={"include": "Include", "exclude": "Exclude"},
                            selected="include",
                            inline=True,
                        ),
                        col_widths=[6, 6],
                    ),
                ),
                ui.layout_columns(
                    ui.div({"class": "panel results-card"}, ui.h3("HP"), ui.output_plot("hist_hp", height="280px")),
                    ui.div(
                        {"class": "panel results-card"},
                        ui.h3("Attack"),
                        ui.output_plot("hist_attack", height="280px"),
                    ),
                    ui.div(
                        {"class": "panel results-card"},
                        ui.h3("Defense"),
                        ui.output_plot("hist_defense", height="280px"),
                    ),
                    col_widths=[4, 4, 4],
                ),
                ui.layout_columns(
                    ui.div(
                        {"class": "panel results-card"},
                        ui.h3("Sp. Atk"),
                        ui.output_plot("hist_spatk", height="280px"),
                    ),
                    ui.div(
                        {"class": "panel results-card"},
                        ui.h3("Sp. Def"),
                        ui.output_plot("hist_spdef", height="280px"),
                    ),
                    ui.div(
                        {"class": "panel results-card"},
                        ui.h3("Speed"),
                        ui.output_plot("hist_speed", height="280px"),
                    ),
                    col_widths=[4, 4, 4],
                ),
                ui.div(
                    {"class": "panel results-card"},
                    ui.h3("Base Stat Total Distribution By Type"),
                    ui.output_plot("hist_bst_by_type", height="360px"),
                ),
            ),
            ui.nav_panel(
                "Type Chart",
                ui.div(
                    {"class": "panel results-card"},
                    ui.h3("Type Effectiveness Table"),
                    ui.p("Rows are attacking types and columns are defending types."),
                    ui.output_data_frame("typechart_table"),
                ),
            ),
            ui.nav_panel(
                "Natures",
                ui.div(
                    {"class": "panel results-card"},
                    ui.h3("Nature Reference"),
                    ui.p("Quick lookup for stat boosts and drops."),
                    ui.output_data_frame("natures_table"),
                ),
            ),
        ),
    ),
    title="Pokemon Move Dashboard",
)


def server(input, output, session):
    def stat_hist_figure(column: str, title: str, color: str = "#72c9dd"):
        values = POKEMON_DF[column].dropna()
        fig, ax = plt.subplots(figsize=(5.2, 3.2))
        fig.patch.set_facecolor("#f8fcff")
        ax.set_facecolor("#f2f8fb")
        ax.hist(values, bins=20, color=color, edgecolor="#145665", alpha=0.85)
        ax.set_title(title, color="#16202a", fontsize=13, fontweight="bold")
        ax.set_xlabel("Base stat", color="#5a6b78")
        ax.set_ylabel("Pokemon count", color="#5a6b78")
        ax.grid(axis="y", color="#d8e3ea", linewidth=0.8)
        ax.tick_params(colors="#5a6b78")
        for spine in ("top", "right"):
            ax.spines[spine].set_visible(False)
        ax.spines["left"].set_color("#91a9b8")
        ax.spines["bottom"].set_color("#91a9b8")
        fig.tight_layout()
        return fig

    def filtered_histogram_pokemon() -> pd.DataFrame:
        data = POKEMON_DF.copy()

        if input.hist_include_megas() == "exclude":
            data = data[data["mega"] != "TRUE"]

        type_name = input.hist_type()
        if type_name == "All":
            return data

        return data[(data["Type1"] == type_name) | (data["Type2"] == type_name)]

    def bst_hist_figure():
        data = filtered_histogram_pokemon()
        type_name = input.hist_type()
        include_megas = input.hist_include_megas() == "include"
        mega_note = "Including Megas" if include_megas else "Excluding Megas"

        if type_name == "All":
            palette = {"fill": "#dbeafe", "line": "#1f7a8c"}
            title = f"Base Stat Total Distribution Across All Pokemon ({mega_note})"
        else:
            palette = type_palette(type_name)
            title = f"Base Stat Total Distribution For {type_name}-Type Pokemon ({mega_note})"

        fig, ax = plt.subplots(figsize=(10, 4.2))
        fig.patch.set_facecolor("#f8fcff")
        ax.set_facecolor("#f2f8fb")

        if data.empty:
            ax.text(0.5, 0.5, "No Pokemon found for this selection.", ha="center", va="center", color="#5a6b78")
            ax.set_axis_off()
            return fig

        ax.hist(data["Total"].dropna(), bins=20, color=palette["fill"], edgecolor=palette["line"], alpha=0.9)
        ax.set_title(title, color="#16202a", fontsize=15, fontweight="bold")
        ax.set_xlabel("Base stat total", color="#5a6b78")
        ax.set_ylabel("Pokemon count", color="#5a6b78")
        ax.grid(axis="y", color="#d8e3ea", linewidth=0.8)
        ax.tick_params(colors="#5a6b78")
        for spine in ("top", "right"):
            ax.spines[spine].set_visible(False)
        ax.spines["left"].set_color("#91a9b8")
        ax.spines["bottom"].set_color("#91a9b8")
        fig.tight_layout()
        return fig

    @reactive.effect
    def _update_pokemon_search_choices():
        selected_name = input.pokemon_search_name()
        choices = POKEMON_NAMES_BY_ID if input.pokemon_search_sort() == "id" else POKEMON_NAMES
        selected = selected_name if selected_name in choices else choices[0]
        ui.update_select(
            "pokemon_search_name",
            choices=choices,
            selected=selected,
            session=session,
        )

    @reactive.calc
    def filtered_pokemon() -> pd.DataFrame:
        filtered = POKEMON_DF.copy()
        selected_moves = input.moves()
        selected_abilities = input.ability_filter()
        search_text = input.name_search().strip().lower()

        if selected_moves:
            matching = MOVE_LOOKUP[MOVE_LOOKUP["Move"].isin(selected_moves)]
            counts = matching.groupby(["Num", "Name"]).size().reset_index(name="Matched Moves")

            if input.match_mode() == "all":
                counts = counts[counts["Matched Moves"] == len(selected_moves)]

            filtered = filtered.merge(counts, on=["Num", "Name"], how="inner")
        else:
            filtered["Matched Moves"] = 0

        if search_text:
            filtered = filtered[filtered["Name"].str.lower().str.contains(search_text, na=False)]

        if selected_abilities:
            ability_sets = filtered[["ability_0", "ability_1", "ability_H"]].apply(
                lambda row: {
                    str(value).strip().lower()
                    for value in row
                    if pd.notna(value) and str(value).strip() and str(value).strip().lower() != "nan"
                },
                axis=1,
            )
            selected_ability_set = {ability.strip().lower() for ability in selected_abilities if ability.strip()}
            if input.ability_match_mode() == "all":
                mask = ability_sets.apply(lambda values: selected_ability_set.issubset(values))
            else:
                mask = ability_sets.apply(lambda values: bool(values.intersection(selected_ability_set)))
            filtered = filtered[mask]

        if input.type_filter() != "All":
            filtered = filtered[filtered["Type1"] == input.type_filter()]

        if input.mega_only():
            filtered = filtered[filtered["mega"] == "TRUE"]

        filtered = filtered[filtered["Total"] >= input.min_total()]

        if filtered.empty:
            return filtered

        return filtered.sort_values(
            by=["Matched Moves", "Total", "Move Count", "Name"],
            ascending=[False, False, False, True],
        ).reset_index(drop=True)

    @reactive.calc
    def selected_pokemon_name() -> str:
        selected_name = input.focus_pokemon()
        if selected_name:
            return selected_name

        filtered = filtered_pokemon()
        if not filtered.empty:
            return str(filtered.iloc[0]["Name"])

        return str(POKEMON_DF.iloc[0]["Name"])

    @reactive.calc
    def pokemon_search_row() -> pd.Series:
        selected_name = input.pokemon_search_name()
        match = POKEMON_DF[POKEMON_DF["Name"] == selected_name]
        if match.empty:
            return POKEMON_DF.iloc[0]
        return match.iloc[0]

    @reactive.calc
    def pokemon_search_moves() -> pd.DataFrame:
        pokemon_name = str(pokemon_search_row()["Name"])
        moves = (
            MOVE_LOOKUP[MOVE_LOOKUP["Name"] == pokemon_name][["Move"]]
            .drop_duplicates()
            .rename(columns={"Move": "Name"})
        )
        if moves.empty:
            return pd.DataFrame(
                [
                    {
                        "Name": "No moves found",
                        "Type": "",
                        "Category": "",
                        "BasePower": "",
                        "Accuracy": "",
                        "PP": "",
                        "Description": "",
                    }
                ]
            )

        merged = moves.merge(MOVES_DF, on="Name", how="left")
        display_columns = ["Name", "Type", "Category", "BasePower", "Accuracy", "PP", "Description"]
        return merged[display_columns].sort_values("Name").reset_index(drop=True)

    @render.ui
    def result_count_card():
        total = len(filtered_pokemon())
        return ui.div(
            {"class": "stat-card"},
            ui.div({"class": "stat-label"}, "Results"),
            ui.div({"class": "stat-value"}, str(total)),
            ui.div({"class": "stat-note"}, "Pokemon currently match the filters."),
        )

    @render.ui
    def move_count_card():
        filtered = filtered_pokemon()
        avg_moves = 0 if filtered.empty else round(filtered["Move Count"].mean(), 1)
        selected_count = len(input.moves())
        note = "No moves selected." if selected_count == 0 else f"{selected_count} move filter(s) active."
        return ui.div(
            {"class": "stat-card"},
            ui.div({"class": "stat-label"}, "Average Move Pool"),
            ui.div({"class": "stat-value"}, str(avg_moves)),
            ui.div({"class": "stat-note"}, note),
        )

    @render.ui
    def type_summary_card():
        filtered = filtered_pokemon()
        if filtered.empty:
            top_type = "None"
            note = "No dominant primary type in view."
        else:
            top_type = str(filtered["Type1"].mode().iat[0])
            count = int((filtered["Type1"] == top_type).sum())
            note = f"{count} matching Pokemon are primarily {top_type}."
        return ui.div(
            {"class": "stat-card"},
            ui.div({"class": "stat-label"}, "Top Primary Type"),
            ui.div({"class": "stat-value"}, top_type),
            ui.div({"class": "stat-note"}, note),
        )

    @render.ui
    def mega_summary_card():
        filtered = filtered_pokemon()
        mega_count = 0 if filtered.empty else int((filtered["mega"] == "TRUE").sum())
        return ui.div(
            {"class": "stat-card"},
            ui.div({"class": "stat-label"}, "Mega Forms"),
            ui.div({"class": "stat-value"}, str(mega_count)),
            ui.div({"class": "stat-note"}, "Mega evolutions in the current result set."),
        )

    @render.text
    def active_filters():
        selected_moves = input.moves()
        move_text = ", ".join(selected_moves[:8]) if selected_moves else "none"
        if len(selected_moves) > 8:
            move_text += ", ..."

        selected_abilities = input.ability_filter()
        ability_text = ", ".join(selected_abilities[:6]) if selected_abilities else "none"
        if len(selected_abilities) > 6:
            ability_text += ", ..."

        return (
            f"Moves: {move_text}\n"
            f"Match mode: {input.match_mode()}\n"
            f"Abilities: {ability_text}\n"
            f"Ability match mode: {input.ability_match_mode()}\n"
            f"Primary type: {input.type_filter()}\n"
            f"Minimum total: {input.min_total()}\n"
            f"Mega only: {'yes' if input.mega_only() else 'no'}"
        )

    @render.data_frame
    def pokemon_table():
        filtered = filtered_pokemon().copy()
        if filtered.empty:
            empty = pd.DataFrame([{"Name": "No matching Pokemon"}])
            return render.DataGrid(empty, filters=False, width="100%")

        display = filtered[
            [
                "Num",
                "Name",
                "Type1",
                "Type2",
                "Matched Moves",
                "Move Count",
                "Total",
                "HP",
                "ATK",
                "DEF",
                "SPA",
                "SPD",
                "SPE",
                "Abilities",
                "mega",
            ]
        ].rename(columns={"mega": "Mega"})
        return render.DataGrid(display, filters=False, width="100%")

    @render.data_frame
    def selected_moves_table():
        pokemon_name = selected_pokemon_name()
        moves = MOVE_LOOKUP[MOVE_LOOKUP["Name"] == pokemon_name][["Move"]].drop_duplicates().sort_values("Move")
        if moves.empty:
            moves = pd.DataFrame([{"Move": "No moves found"}])
        return render.DataGrid(moves.reset_index(drop=True), filters=True, width="100%")

    @render.plot
    def pokemon_radar_chart():
        pokemon = pokemon_search_row()
        palette = type_palette(str(pokemon["Type1"]))
        labels = ["HP", "Attack", "Defense", "Speed", "Sp. Def", "Sp. Atk"]
        values = [
            float(pokemon["HP"]),
            float(pokemon["ATK"]),
            float(pokemon["DEF"]),
            float(pokemon["SPE"]),
            float(pokemon["SPD"]),
            float(pokemon["SPA"]),
        ]

        angles = [0, 60, 120, 180, 240, 300]
        angles_rad = [angle * (3.141592653589793 / 180) for angle in angles]
        angles_closed = angles_rad + [angles_rad[0]]
        values_closed = values + [values[0]]
        radial_max = max(200, ((int(max(values)) + 24) // 25) * 25)

        fig, ax = plt.subplots(figsize=(8.4, 8.0), subplot_kw={"projection": "polar"})
        fig.patch.set_facecolor("#f8fcff")
        ax.set_facecolor("#f2f8fb")
        ax.set_theta_offset(3.141592653589793 / 2)
        ax.set_theta_direction(-1)
        ax.set_xticks(angles_rad)
        ax.set_xticklabels(labels, fontsize=12.5, color="#145665")
        ax.tick_params(axis="x", pad=12)
        ax.set_ylim(0, radial_max)
        ax.set_yticks([50, 100, 150, 200] if radial_max >= 200 else [radial_max / 4, radial_max / 2, radial_max * 0.75])
        ax.set_yticklabels([str(int(tick)) for tick in ax.get_yticks()], color="#5a6b78", fontsize=10)
        ax.grid(color="#c5d4df", linewidth=0.9)
        ax.spines["polar"].set_color("#91a9b8")
        ax.spines["polar"].set_linewidth(1.2)
        ax.plot(angles_closed, values_closed, color=palette["line"], linewidth=2.6)
        ax.fill(angles_closed, values_closed, color=palette["fill"], alpha=0.72)
        ax.set_title(str(pokemon["Name"]), y=1.10, color="#16202a", fontsize=19, fontweight="bold")
        fig.subplots_adjust(top=0.90, bottom=0.03, left=0.03, right=0.97)
        return fig

    @render.ui
    def pokemon_search_profile():
        pokemon = pokemon_search_row()
        total = str(pokemon["Total"])
        items = [
            ("Typing", f"{pokemon['Type1']} / {pokemon['Type2']}" if pokemon["Type2"] else str(pokemon["Type1"])),
            ("Abilities", str(pokemon["Abilities"])),
            ("HP", str(pokemon["HP"])),
            ("Attack", str(pokemon["ATK"])),
            ("Defense", str(pokemon["DEF"])),
            ("Sp. Atk", str(pokemon["SPA"])),
            ("Sp. Def", str(pokemon["SPD"])),
            ("Speed", str(pokemon["SPE"])),
        ]

        return ui.div(
            ui.h3(f"Base Stat Total: {total}"),
            ui.div(
                {"class": "pokemon-profile"},
                *[
                    ui.div({"class": "profile-item"}, ui.strong(label), ui.div(value))
                    for label, value in items
                ],
            ),
        )

    @render.data_frame
    def pokemon_search_moves_table():
        return render.DataGrid(
            pokemon_search_moves(),
            filters=False,
            width="100%",
            height="360px",
            styles=build_move_list_styles(pokemon_search_moves()),
        )

    @render.plot
    def hist_hp():
        return stat_hist_figure("HP", "HP", "#dbeafe")

    @render.plot
    def hist_attack():
        return stat_hist_figure("ATK", "Attack", "#fed7aa")

    @render.plot
    def hist_defense():
        return stat_hist_figure("DEF", "Defense", "#dff6df")

    @render.plot
    def hist_spatk():
        return stat_hist_figure("SPA", "Sp. Atk", "#f5d0fe")

    @render.plot
    def hist_spdef():
        return stat_hist_figure("SPD", "Sp. Def", "#e0f2fe")

    @render.plot
    def hist_speed():
        return stat_hist_figure("SPE", "Speed", "#fef3c7")

    @render.plot
    def hist_bst_by_type():
        return bst_hist_figure()

    @render.data_frame
    def typechart_table():
        return render.DataGrid(TYPECHART_DF, filters=False, width="100%", styles=TYPECHART_STYLES)

    @render.data_frame
    def natures_table():
        return render.DataGrid(NATURES_DF, filters=True, width="100%", styles=NATURES_STYLES)


app = App(app_ui, server)
