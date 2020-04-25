import os
import pathlib

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import dash_table
import plotly.graph_objs as go
import dash_daq as daq
import dash_bootstrap_components as dbc


def build_banner(app: dash.Dash):
    mieuxvoter_logo = app.get_asset_url("img/mieux-voter-logo.png")
    search_bar = dbc.Row(
        [
            dbc.Col(dbc.Input(type="search", placeholder="Not working yet.")),
            dbc.Col(
                dbc.Button("Search", color="primary", className="ml-2"),
                width="auto",
            ),
        ],
        no_gutters=True,
        className="ml-auto flex-nowrap mt-3 mt-md-0",
        align="center",
    )

    return dbc.Navbar([
            html.A(
                # Use row and col to control vertical alignment of logo / brand
                dbc.Row(
                    [
                        dbc.Col(html.Img(src=mieuxvoter_logo, height="30px")),
                        dbc.Col(
                            dbc.NavbarBrand(
                                "Mieux Voter - Dashboard",
                                className="ml-2"
                            )
                        ),
                    ],
                    align="center",
                    no_gutters=True,
                ),
                href="https://app.mieuxvoter.fr",
            ),
            dbc.NavbarToggler(id="navbar-toggler"),
            dbc.Collapse(search_bar, id="navbar-collapse", navbar=True),
        ],
        color="dark",
        dark=True,
    )

    
def build_quick_stats_panel(num_elections: int, num_votes: int):
    return dbc.Col([
        dbc.Row([dbc.Col([html.Div(
                id="card-1",
                children=[
                    html.P("Number of elections"),
                    daq.LEDDisplay(
                        id="num-elections",
                        value=num_elections,
                        color="#92e0d3",
                        backgroundColor="#1e2130",
                        size=50,
                    ),
                ],
            )])]),
        dbc.Row([
        dbc.Col([html.Div(
                id="card-2",
                children=[
                    html.P("Number of votes"),
                    daq.LEDDisplay(
                        id="num-votes",
                        value=num_votes,
                        color="#92e0d3",
                        backgroundColor="#1e2130",
                        size=50,
                    ),
                ],
            )]),
    ])])


