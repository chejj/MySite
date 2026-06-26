import json
import math
import random
from collections import Counter

import matplotlib.pyplot as plt
from shiny import App, reactive, render, ui


RESOURCE_CHOICES = ["wood", "brick", "sheep", "wheat", "ore", "desert"]
TOKEN_CHOICES = [""] + [str(value) for value in [2, 3, 4, 5, 6, 8, 9, 10, 11, 12]]
PIP_MAP = {2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 8: 5, 9: 4, 10: 3, 11: 2, 12: 1}
RESOURCE_LABELS = {
    "wood": "Wood",
    "brick": "Brick",
    "sheep": "Sheep",
    "wheat": "Wheat",
    "ore": "Ore",
    "desert": "Desert",
}

HEX_LAYOUT = [
    {"id": "H01", "q": 0, "r": -2},
    {"id": "H02", "q": 1, "r": -2},
    {"id": "H03", "q": 2, "r": -2},
    {"id": "H04", "q": -1, "r": -1},
    {"id": "H05", "q": 0, "r": -1},
    {"id": "H06", "q": 1, "r": -1},
    {"id": "H07", "q": 2, "r": -1},
    {"id": "H08", "q": -2, "r": 0},
    {"id": "H09", "q": -1, "r": 0},
    {"id": "H10", "q": 0, "r": 0},
    {"id": "H11", "q": 1, "r": 0},
    {"id": "H12", "q": 2, "r": 0},
    {"id": "H13", "q": -2, "r": 1},
    {"id": "H14", "q": -1, "r": 1},
    {"id": "H15", "q": 0, "r": 1},
    {"id": "H16", "q": 1, "r": 1},
    {"id": "H17", "q": -2, "r": 2},
    {"id": "H18", "q": -1, "r": 2},
    {"id": "H19", "q": 0, "r": 2},
]

ROW_ORDER = [
    ["H01", "H02", "H03"],
    ["H04", "H05", "H06", "H07"],
    ["H08", "H09", "H10", "H11", "H12"],
    ["H13", "H14", "H15", "H16"],
    ["H17", "H18", "H19"],
]

DEFAULT_BOARD = {
    "H01": {"resource": "wood", "token": 11},
    "H02": {"resource": "sheep", "token": 4},
    "H03": {"resource": "wheat", "token": 8},
    "H04": {"resource": "brick", "token": 10},
    "H05": {"resource": "ore", "token": 9},
    "H06": {"resource": "wood", "token": 12},
    "H07": {"resource": "sheep", "token": 5},
    "H08": {"resource": "wheat", "token": 6},
    "H09": {"resource": "brick", "token": 2},
    "H10": {"resource": "desert", "token": None},
    "H11": {"resource": "sheep", "token": 9},
    "H12": {"resource": "ore", "token": 10},
    "H13": {"resource": "wood", "token": 8},
    "H14": {"resource": "wheat", "token": 3},
    "H15": {"resource": "ore", "token": 4},
    "H16": {"resource": "brick", "token": 5},
    "H17": {"resource": "sheep", "token": 6},
    "H18": {"resource": "wood", "token": 3},
    "H19": {"resource": "wheat", "token": 11},
}


def axial_to_pixel(q: int, r: int, size: float = 1.0) -> tuple[float, float]:
    x = size * math.sqrt(3) * (q + r / 2)
    y = size * 1.5 * r
    return x, y


def build_vertices() -> list[dict[str, object]]:
    raw_vertices: dict[tuple[float, float], set[str]] = {}

    for tile in HEX_LAYOUT:
        center_x, center_y = axial_to_pixel(tile["q"], tile["r"])
        for corner in range(6):
            angle = math.radians(60 * corner - 30)
            x = round(center_x + math.cos(angle), 6)
            y = round(center_y + math.sin(angle), 6)
            raw_vertices.setdefault((x, y), set()).add(tile["id"])

    ordered_keys = sorted(raw_vertices.keys(), key=lambda item: (item[1], item[0]))
    vertices: list[dict[str, object]] = []

    for index, key in enumerate(ordered_keys, start=1):
        vertices.append(
            {
                "id": f"V{index:02d}",
                "coords": key,
                "tiles": sorted(raw_vertices[key]),
            }
        )

    return vertices


VERTICES = build_vertices()


def board_from_defaults() -> dict[str, dict[str, object]]:
    return {
        tile_id: {"resource": values["resource"], "token": values["token"]}
        for tile_id, values in DEFAULT_BOARD.items()
    }


def normalize_tile(tile_id: str, resource: object, token: object) -> dict[str, object]:
    resource_name = str(resource).strip().lower()
    if resource_name not in RESOURCE_CHOICES:
        raise ValueError(f"{tile_id} has unknown resource '{resource}'.")

    token_value: int | None
    if token in (None, "", "null"):
        token_value = None
    else:
        token_value = int(token)
        if token_value not in PIP_MAP:
            raise ValueError(f"{tile_id} has invalid token '{token}'.")

    if resource_name == "desert":
        token_value = None

    return {"resource": resource_name, "token": token_value}


def normalize_board_payload(payload: object) -> dict[str, dict[str, object]]:
    if isinstance(payload, dict) and "tiles" in payload:
        payload = payload["tiles"]

    normalized = board_from_defaults()

    if isinstance(payload, dict):
        for tile_id, values in payload.items():
            if tile_id not in normalized:
                raise ValueError(f"Unknown tile id '{tile_id}'.")
            if not isinstance(values, dict):
                raise ValueError(f"{tile_id} must map to an object.")
            normalized[tile_id] = normalize_tile(tile_id, values.get("resource"), values.get("token"))
        return normalized

    if isinstance(payload, list):
        for item in payload:
            if not isinstance(item, dict):
                raise ValueError("Each tile entry must be an object.")
            tile_id = str(item.get("id", "")).strip().upper()
            if tile_id not in normalized:
                raise ValueError(f"Unknown tile id '{tile_id}'.")
            normalized[tile_id] = normalize_tile(tile_id, item.get("resource"), item.get("token"))
        return normalized

    raise ValueError("JSON must be either a tile dictionary or a list of tile objects.")


def board_to_json(board: dict[str, dict[str, object]]) -> str:
    ordered = []
    for tile in HEX_LAYOUT:
        tile_state = board[tile["id"]]
        ordered.append(
            {
                "id": tile["id"],
                "resource": tile_state["resource"],
                "token": tile_state["token"],
            }
        )
    return json.dumps({"tiles": ordered}, indent=2)


def resource_class(resource: str) -> str:
    return f"tile-{resource}"


def pip_count(token: int | None) -> int:
    if token is None:
        return 0
    return PIP_MAP.get(token, 0)


def score_vertices(board: dict[str, dict[str, object]]) -> list[dict[str, object]]:
    scored: list[dict[str, object]] = []

    for vertex in VERTICES:
        adjacent = []
        total = 0
        for tile_id in vertex["tiles"]:
            tile = board[tile_id]
            token = tile["token"]
            pips = pip_count(token)
            adjacent.append(
                {
                    "tile_id": tile_id,
                    "resource": tile["resource"],
                    "token": token,
                    "pips": pips,
                }
            )
            total += pips

        scored.append(
            {
                "id": vertex["id"],
                "tiles": adjacent,
                "total_pips": total,
                "tile_count": len(adjacent),
            }
        )

    scored.sort(key=lambda item: (-item["total_pips"], -item["tile_count"], item["id"]))
    return scored


def board_tile(tile_id: str, board: dict[str, dict[str, object]]) -> ui.Tag:
    tile = board[tile_id]
    token = tile["token"]
    token_text = "Desert" if token is None else str(token)
    pips = pip_count(token)
    pip_text = "No pips" if pips == 0 else ("o" * pips)

    return ui.div(
        {"class": "board-stack"},
        ui.div(
            {"class": f"board-hex {resource_class(tile['resource'])}"},
            ui.div({"class": "board-hex-id"}, tile_id),
            ui.div({"class": "board-hex-resource"}, RESOURCE_LABELS[tile["resource"]]),
            ui.div({"class": "board-hex-token"}, token_text),
            ui.div({"class": "board-hex-pips"}, pip_text),
        ),
    )


def make_table(headers: list[str], rows: list[list[object]], class_name: str = "score-table") -> ui.Tag:
    return ui.tags.table(
        {"class": class_name},
        ui.tags.thead(ui.tags.tr(*[ui.tags.th(header) for header in headers])),
        ui.tags.tbody(
            *[
                ui.tags.tr(*[ui.tags.td(str(cell)) for cell in row])
                for row in rows
            ]
        ),
    )


def roll_distribution_figure(rolls: list[int]):
    counts = Counter(rolls)
    x_values = list(range(2, 13))
    heights = [counts.get(value, 0) for value in x_values]

    fig, ax = plt.subplots(figsize=(7.4, 3.8))
    fig.patch.set_facecolor("#fffaf0")
    ax.set_facecolor("#fffdf8")
    ax.bar(x_values, heights, color="#d88b36", edgecolor="#7a4316", width=0.78)
    ax.set_xticks(x_values)
    ax.set_xlabel("Roll")
    ax.set_ylabel("Frequency")
    ax.set_title("Simulated Two-Dice Distribution", fontsize=13, fontweight="bold")
    ax.grid(axis="y", color="#ecdcc1", linewidth=0.8)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_color("#baa17d")
    ax.spines["bottom"].set_color("#baa17d")
    fig.tight_layout()
    return fig


def resource_expectation_figure(resource_expectations: dict[str, float]):
    order = ["wood", "brick", "sheep", "wheat", "ore"]
    labels = [RESOURCE_LABELS[name] for name in order]
    values = [resource_expectations.get(name, 0.0) for name in order]
    colors = ["#7cab68", "#d98f68", "#b9dd7c", "#e4c15c", "#9ca8b5"]

    fig, ax = plt.subplots(figsize=(7.4, 3.8))
    fig.patch.set_facecolor("#fffaf0")
    ax.set_facecolor("#fffdf8")
    ax.bar(labels, values, color=colors, edgecolor="#66543a", width=0.72)
    ax.set_xlabel("Resource")
    ax.set_ylabel("Expected cards")
    ax.set_title("Expected Resource Production", fontsize=13, fontweight="bold")
    ax.grid(axis="y", color="#ecdcc1", linewidth=0.8)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_color("#baa17d")
    ax.spines["bottom"].set_color("#baa17d")
    fig.tight_layout()
    return fig


app_ui = ui.page_fillable(
    ui.tags.style(
        """
        :root {
            --ink: #1f2933;
            --muted: #52606d;
            --sand: #f6efe0;
            --panel: rgba(255, 252, 247, 0.95);
            --panel-strong: #fffaf0;
            --line: #dbcdb5;
            --shadow: rgba(60, 42, 18, 0.12);
            --board-ocean: rgba(118, 197, 231, 0.98);
            --board-ocean-line: rgba(42, 112, 160, 0.58);
            --wood: #466f45;
            --brick: #b85c38;
            --sheep: #96c95d;
            --wheat: #d9b44a;
            --ore: #7a8795;
            --desert: #d8bf8b;
        }
        body {
            background:
                radial-gradient(circle at 20% 0%, rgba(255, 218, 148, 0.18), transparent 24%),
                radial-gradient(circle at 80% 10%, rgba(116, 28, 21, 0.16), transparent 28%),
                linear-gradient(180deg, #b43325 0%, #9a231f 54%, #7d1819 100%);
            color: var(--ink);
        }
        .app-shell {
            padding: 1.2rem;
            gap: 1rem;
        }
        .hero, .panel, .metric-card {
            background: var(--panel);
            border: 1px solid var(--line);
            box-shadow: 0 14px 32px var(--shadow);
            border-radius: 26px;
        }
        .hero {
            padding: 1.5rem;
        }
        .hero h1 {
            margin: 0 0 0.4rem 0;
            font-size: 2.15rem;
        }
        .hero-subtitle {
            margin: 0 0 0.35rem 0;
            color: #f7e6c2;
            font-size: 1rem;
            font-weight: 700;
            letter-spacing: 0.04em;
            text-transform: uppercase;
        }
        .hero p {
            margin: 0;
            color: var(--muted);
            max-width: 68rem;
        }
        .eyebrow {
            display: inline-block;
            margin-bottom: 0.75rem;
            padding: 0.35rem 0.7rem;
            border-radius: 999px;
            background: #f4e1b2;
            color: #7c5a14;
            font-weight: 700;
            font-size: 0.8rem;
            letter-spacing: 0.06em;
            text-transform: uppercase;
        }
        .panel {
            padding: 1rem 1.1rem;
        }
        .board-panel {
            background:
                radial-gradient(circle at top, rgba(255, 255, 255, 0.32), transparent 28%),
                linear-gradient(180deg, #8fd4f2 0%, var(--board-ocean) 48%, #4ea8d8 100%);
            border-color: var(--board-ocean-line);
        }
        .metric-card {
            padding: 0.9rem 1rem;
            min-height: 110px;
        }
        .metric-label {
            color: var(--muted);
            font-size: 0.82rem;
            text-transform: uppercase;
            letter-spacing: 0.06em;
        }
        .metric-value {
            font-size: 1.95rem;
            font-weight: 800;
            margin-top: 0.3rem;
        }
        .metric-note {
            margin-top: 0.35rem;
            color: var(--muted);
        }
        .board-wrap {
            overflow-x: auto;
            padding: 0.8rem 0 1rem 0;
        }
        .board-row {
            display: flex;
            justify-content: center;
            gap: 0;
            min-width: 640px;
        }
        .board-row + .board-row {
            margin-top: -2.22rem;
        }
        .board-row.row-3 {
            padding-left: 4.16rem;
            padding-right: 4.16rem;
        }
        .board-row.row-4 {
            padding-left: 2.08rem;
            padding-right: 2.08rem;
        }
        .board-stack {
            width: 7.35rem;
            margin-left: -0.82rem;
            position: relative;
        }
        .board-stack:first-child {
            margin-left: 0;
        }
        .board-hex {
            height: 8.4rem;
            padding: 0.8rem 0.55rem;
            clip-path: polygon(50% 1%, 94% 25%, 94% 75%, 50% 99%, 6% 75%, 6% 25%);
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-align: center;
            border: 2px solid rgba(64, 45, 22, 0.22);
            box-shadow: inset 0 0 0 1px rgba(255, 248, 234, 0.28);
        }
        .board-hex-id {
            font-size: 0.72rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            opacity: 0.8;
        }
        .board-hex-resource {
            font-weight: 700;
            margin-top: 0.2rem;
        }
        .board-hex-token {
            margin-top: 0.32rem;
            width: 2.35rem;
            height: 2.35rem;
            border-radius: 999px;
            background: rgba(255, 248, 234, 0.96);
            border: 1px solid rgba(64, 45, 22, 0.22);
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 800;
        }
        .board-hex-pips {
            margin-top: 0.35rem;
            min-height: 1.2rem;
            font-size: 0.88rem;
            letter-spacing: 0.12em;
        }
        .tile-wood { background: linear-gradient(180deg, #d2e8cb, #7cab68); }
        .tile-brick { background: linear-gradient(180deg, #f3d3c5, #d98f68); }
        .tile-sheep { background: linear-gradient(180deg, #eef7d5, #b9dd7c); }
        .tile-wheat { background: linear-gradient(180deg, #fbefc6, #e4c15c); }
        .tile-ore { background: linear-gradient(180deg, #e5e9ef, #9ca8b5); }
        .tile-desert { background: linear-gradient(180deg, #f3e2b5, #d7b77a); }
        .toolbar {
            display: grid;
            gap: 0.8rem;
        }
        .toolbar .btn {
            margin-right: 0.5rem;
            margin-bottom: 0.5rem;
        }
        .json-box textarea {
            min-height: 280px;
            font-family: Consolas, "Courier New", monospace;
            font-size: 0.88rem;
        }
        .status-note {
            color: var(--muted);
            white-space: pre-wrap;
            margin-bottom: 0.75rem;
        }
        .score-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.95rem;
        }
        .score-table th,
        .score-table td {
            border-bottom: 1px solid #eadfca;
            padding: 0.55rem 0.5rem;
            vertical-align: top;
            text-align: left;
        }
        .score-table th {
            font-size: 0.82rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--muted);
        }
        .score-table.compact td,
        .score-table.compact th {
            padding: 0.45rem 0.42rem;
            font-size: 0.9rem;
        }
        .note-list {
            margin: 0;
            padding-left: 1.1rem;
            color: var(--muted);
        }
        .section-title {
            margin-top: 0;
        }
        .analysis-panel {
            min-height: 100%;
        }
        """
    ),
    ui.div(
        {"class": "app-shell"},
        ui.div(
            {"class": "hero"},
            ui.div({"class": "eyebrow"}, "Serverless Shinylive App"),
            ui.h1("Settlers of Catan Resource Analysis"),
            ui.p({"class": "hero-subtitle"}, "Hex Pip analysis Work in Progress"),
        ),
        ui.layout_columns(
            ui.div(
                {"class": "panel board-panel"},
                ui.h3({"class": "section-title"}, "Board View"),
                ui.output_ui("board_view"),
            ),
            ui.div(
                {"class": "panel toolbar"},
                ui.h3({"class": "section-title"}, "Board Tools"),
                ui.div(
                    ui.input_action_button("reset_board", "Load sample board", class_="btn-primary"),
                    ui.input_action_button("apply_json", "Apply JSON", class_="btn-outline-secondary"),
                ),
                ui.div({"class": "json-box"}, ui.input_text_area("board_json", "Board JSON", value=board_to_json(DEFAULT_BOARD))),
                ui.output_text_verbatim("status_text"),
            ),
            col_widths=[8, 4],
        ),
        ui.layout_columns(
            ui.div(
                {"class": "panel analysis-panel"},
                ui.h3({"class": "section-title"}, "Roll Simulation"),
                ui.layout_columns(
                    ui.input_numeric("sim_rolls", "How many rolls should we simulate?", value=200, min=1, max=50000, step=1),
                    ui.div(
                        {"style": "padding-top: 1.9rem;"},
                        ui.input_action_button("resample_rolls", "Resample", class_="btn-outline-secondary"),
                    ),
                    col_widths=[9, 3],
                ),
                ui.output_plot("sim_roll_plot", height="340px"),
                ui.h4("Highest-Producing Vertices"),
                ui.output_ui("sim_vertex_table"),
            ),
            ui.div(
                {"class": "panel analysis-panel"},
                ui.h3({"class": "section-title"}, "Expected Production"),
                ui.input_numeric("expected_turns", "Expected production over how many turns?", value=80, min=1, max=50000, step=1),
                ui.p("E(V) = n_pips * (turns / 36)"),
                ui.output_plot("expected_resource_plot", height="340px"),
                ui.h4("Expected Cards By Resource"),
                ui.output_ui("expected_resource_table"),
            ),
            col_widths=[5, 7],
        ),
    ),
    title="Settlers of Catan Pip Calculator",
)


def server(input, output, session):
    status_message = reactive.value("Loaded the sample board.")
    board_state = reactive.value(board_from_defaults())
    resample_tick = reactive.value(0)

    def apply_board_to_inputs(board: dict[str, dict[str, object]]) -> None:
        board_state.set(board)
        ui.update_text_area("board_json", value=board_to_json(board), session=session)

    @reactive.effect
    @reactive.event(input.reset_board)
    def _reset_board():
        board = board_from_defaults()
        apply_board_to_inputs(board)
        status_message.set("Loaded the sample board.")

    @reactive.effect
    @reactive.event(input.apply_json)
    def _apply_json():
        try:
            payload = json.loads(input.board_json())
            board = normalize_board_payload(payload)
        except Exception as exc:
            status_message.set(f"Could not apply JSON: {exc}")
            return

        apply_board_to_inputs(board)
        status_message.set("Applied the JSON board successfully.")

    @reactive.effect
    @reactive.event(input.resample_rolls)
    def _resample_rolls():
        resample_tick.set(resample_tick.get() + 1)
        status_message.set("Generated a fresh roll sample.")

    @reactive.calc
    def current_board() -> dict[str, dict[str, object]]:
        return board_state.get()

    @reactive.calc
    def scored_vertices() -> list[dict[str, object]]:
        return score_vertices(current_board())

    @reactive.calc
    def simulated_rolls() -> list[int]:
        roll_count = int(input.sim_rolls())
        tick = resample_tick.get()
        board_seed = sum(ord(char) for char in board_to_json(current_board()))
        rng = random.Random(2026 + roll_count + board_seed + tick * 97)
        return [rng.randint(1, 6) + rng.randint(1, 6) for _ in range(roll_count)]

    @reactive.calc
    def simulated_vertex_results() -> list[dict[str, object]]:
        roll_counts = Counter(simulated_rolls())
        results: list[dict[str, object]] = []
        for vertex in scored_vertices():
            production_by_resource = Counter()
            total_cards = 0
            for tile in vertex["tiles"]:
                token = tile["token"]
                if token is None or tile["resource"] == "desert":
                    continue
                hits = roll_counts.get(int(token), 0)
                production_by_resource[tile["resource"]] += hits
                total_cards += hits

            results.append(
                {
                    "id": vertex["id"],
                    "total_cards": total_cards,
                    "resources": production_by_resource,
                    "tiles": vertex["tiles"],
                }
            )

        results.sort(key=lambda item: (-item["total_cards"], item["id"]))
        return results

    @reactive.calc
    def expected_resource_counts() -> dict[str, float]:
        turns = int(input.expected_turns())
        expectations = {resource: 0.0 for resource in RESOURCE_CHOICES if resource != "desert"}

        for tile in current_board().values():
            token = tile["token"]
            resource = str(tile["resource"])
            if token is None or resource == "desert":
                continue
            expectations[resource] += turns * (pip_count(token) / 36.0)

        return expectations

    @render.ui
    def board_view():
        board = current_board()
        return ui.div(
            {"class": "board-wrap"},
            *[
                ui.div(
                    {"class": f"board-row row-{len(row)}"},
                    *[board_tile(tile_id, board) for tile_id in row],
                )
                for row in ROW_ORDER
            ],
        )

    @render.text
    def status_text():
        return status_message()

    @render.plot
    def sim_roll_plot():
        return roll_distribution_figure(simulated_rolls())

    @render.ui
    def sim_vertex_table():
        rows = []
        for vertex in simulated_vertex_results()[:10]:
            resource_text = ", ".join(
                f"{RESOURCE_LABELS[resource]} {count}"
                for resource, count in sorted(vertex["resources"].items())
            )
            if not resource_text:
                resource_text = "No production"
            tile_text = ", ".join(
                f"{tile['tile_id']}:{tile['token'] if tile['token'] is not None else '-'}"
                for tile in vertex["tiles"]
            )
            rows.append([vertex["id"], vertex["total_cards"], resource_text, tile_text])
        return make_table(["Vertex", "Cards", "Resource Mix", "Adjacent Tiles"], rows, "score-table compact")

    @render.plot
    def expected_resource_plot():
        return resource_expectation_figure(expected_resource_counts())

    @render.ui
    def expected_resource_table():
        rows = []
        expectations = expected_resource_counts()
        for resource in ["wood", "brick", "sheep", "wheat", "ore"]:
            rows.append([RESOURCE_LABELS[resource], f"{expectations.get(resource, 0.0):.2f}"])
        return make_table(["Resource", "Expected Cards"], rows, "score-table compact")


app = App(app_ui, server)
