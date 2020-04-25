"""
Dashboard monitoring elections.
"""
from typing import Dict, List
import plotly.graph_objects as go
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc


from datetime import datetime
import sys
sys.path.append('../')
import django
from django.db.models.functions import ExtractDay, Cast
from django.db.models import Count, DateTimeField
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mvapi.settings")
django.setup()
from dashboard.utils import build_banner, build_quick_stats_panel
from election.models import Election, Vote, Token

app = dash.Dash(
    __name__,
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
    external_stylesheets=[dbc.themes.BOOTSTRAP]
)



elections = Election.objects.all()
votes = Vote.objects.all()

#### STARTING DAY OF ELECTIONS
# Clean way that does not work...
# el_per_start_day = (
#         elections.annotate( start_date=Cast("start_at", DateTimeField())).
#                   .annotate(start_day=ExtractDay('start_date'))
#                   .values("start_day")
#                   .annotate(count=Count("id"))
#                   .values("start_day", "count")
# )
# fig = go.Figure(
#     data=[go.Bar(x=list(el_per_start_day.start_day), y=list(el_per_start_day.count))],
#     layout=go.Layout(
#         title="Starting day of elections"
#     )
# )

start: Dict[str, int] = {}
for e in elections:
    day: str = datetime.fromtimestamp(e.start_at).strftime("%Y/%m/%d")
    if day not in start:
        start[day] = 1
    else:
        start[day] += 1

fig_election = go.Figure(
    data=[go.Bar(x=list(start.keys()), y=list(start.values()))],
    layout=go.Layout(
        title="Starting day of elections"
    )
)


#### NUMBER OF VOTES PER ELECTIONS


#### HIGHEST VOTED ELECTIONS

votes_per_el = list(
    votes
      .values('election_id', 'election__title')
      .annotate(count=Count("election_id"))
      .order_by("count")
      [:10]
)
titles = [election["election__title"] for election in votes_per_el]
num_votes = [election["count"] for election in votes_per_el]
fig_votes = go.Figure(
    data=[go.Table(
        header=dict(values=["Title", "Number of votes"]),
        cells=dict(values=[titles, num_votes])
    )]
)


app.layout = html.Div(children=[
    build_banner(app),
    dbc.Row([
        dbc.Col(
            build_quick_stats_panel(len(elections), len(votes)),
            align="center",
            width=3
        ),
        dbc.Col(
            html.Div([
                dcc.Graph(figure=fig_election),
                dcc.Graph(figure=fig_votes),
            ]),
            align="center",
            width=9
        )
        ])
])

app.run_server(debug=True, use_reloader=True, port=8053, host="0.0.0.0")
