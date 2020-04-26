"""
Dashboard monitoring elections.
"""
from typing import Dict, List
import plotly.graph_objects as go
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from utils import *

load_mvapi()

app = dash.Dash(
    __name__,
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
    url_base_pathname="/dashboard/"
)

app.css.config.serve_locally = True
app.scripts.config.serve_locally = True
app.layout = html.Div([
    build_banner(app),
    dbc.Row([
        dbc.Col(
            build_quick_stats_panel(),
            align="center",
            width=3
        ),
        dbc.Col(
            html.Div([
                build_day_election_figure(),
                build_most_voted_tables(),
            ]),
            align="center",
            width=9
        )
    ])
])
app.run_server(debug=True, use_reloader=True, port=8053, host="0.0.0.0")
