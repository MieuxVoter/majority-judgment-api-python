from datetime import datetime
from typing import List, Dict
import os
import pathlib
import django
from django.db.models import Count, F
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import dash_table
import plotly.graph_objs as go
import dash_daq as daq
import dash_bootstrap_components as dbc

def load_mvapi():
    import os
    import sys
    sys.path.append('../')
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mvapi.settings")
    django.setup()

load_mvapi()
from election.models import Election, Vote, Token


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

    
def led_display(title, value):
    return html.Div(
        children=[
            html.P(title),
            daq.LEDDisplay(
                value=value,
                color="#92e0d3",
                backgroundColor="#1e2130",
                size=50,
            ),
        ],
    )

def build_quick_stats_panel():
    num_elections: int = len(Election.objects.all())
    num_votes: int = len(Vote.objects.all())

    return dbc.Col([
        dbc.Row([
            dbc.Col([
                led_display("Number of elections", num_elections)
            ])
        ]),
        dbc.Row([
            dbc.Col([
               led_display("Number of votes", num_votes)
            ])
        ])
    ])



def build_day_election_figure():
    days_qs = (
        Election
        .objects
        .all()
        .annotate(start_day=F("start_at") / (24*3600))
        .values("start_day")
        .annotate(count=Count("start_day"))
    )

    if len(days_qs) == 0:
        return html.H1(children=["No elections were found"])

    start_days: Dict[int, int] = {}
    for day in days_qs:
        start_days[day["start_day"]] = day["count"]

    all_days = range(
            min(start_days.keys()),
            int(datetime.now().timestamp() / 24 / 3600) + 1
    )

    day_names: Dict[str, int] = {
        datetime
        .fromtimestamp(timestamp * 24 * 3600)
        .strftime("%Y/%m/%d"):
            start_days.get(timestamp, 0)
        for timestamp in all_days
    }

    return dcc.Graph(
        figure=go.Figure(
            data=[go.Bar(x=list(day_names.keys()), y=list(day_names.values()))],
            layout=go.Layout(
                title="Number of elections created per day"
            )
        )
    )


def build_most_voted_tables(top=10):
    votes_qs = list(
        Vote
        .objects
        .all()
        .values('election_id', 'election__title')
        .annotate(count=Count("election_id"))
        .order_by("-count")
        [:top]
    )

    if len(votes_qs) == 0:
        return html.H1(children=["No votes were found"])

    titles = [election["election__title"] for election in votes_qs]
    num_votes = [election["count"] for election in votes_qs]
    return dcc.Graph(
        go.Figure(
            data=[go.Table(
                header=dict(values=["Title", "Number of votes"]),
                cells=dict(values=[titles, num_votes]),
            )]
        )
    )
