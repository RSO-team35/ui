import dash
from dash.dependencies import Input, Output
from dash import dcc, html
import plotly.express as px
import flask
import pandas as pd
import os
import datetime
import json 


def create_dash_app(requests_pathname_prefix: str = None) -> dash.Dash:
    """
    Sample Dash application from Plotly: https://github.com/plotly/dash-hello-world/blob/master/app.py
    """

    dfs = {"GeForce RTX 3060": 
                pd.DataFrame({
                    "retailer": ["Mimovrste", "Mimovrste", "Amazon", "Amazon"],
                    "model": ["Dual OC", "Dual", "", ""],
                    "manufacturer": ["ASUS", "Zotac", "ASUS", "Gigabyte"],
                    "price": [300, 250, 288, 320],
                    "date": [datetime.date(2022, 12, 1), datetime.date(2022, 12, 2), datetime.date(2022, 12, 4), datetime.date(2022, 12, 8)]
                }),
            "GeForce RTX 3090":
                pd.DataFrame({
                    "retailer": ["Mimovrste", "Mimovrste", "Amazon", "Amazon"],
                    "model": ["Dual OC", "Dual", "", ""],
                    "manufacturer": ["ASUS", "Zotac", "ASUS", "Gigabyte"],
                    "price": [1300, 1250, 1288, 1520],
                    "date": [datetime.date(2022, 12, 1), datetime.date(2022, 12, 2), datetime.date(2022, 12, 4), datetime.date(2022, 12, 8)],
                }),
        }

    styles = {
        'pre': {
            'border': 'thin lightgrey solid',
            'overflowX': 'scroll'
        }
    }

    app = dash.Dash(__name__, requests_pathname_prefix=requests_pathname_prefix)

    app.scripts.config.serve_locally = False
    dcc._js_dist[0]['external_url'] = 'https://cdn.plot.ly/plotly-basic-latest.min.js'

    #fig = px.bar(df, x="Fruit", y="Amount", color="City", barmode="group")

    app.layout = html.Div([
        html.H1('Primerjalnik cen'),

        dcc.Dropdown(
            id="price-history-dropdown",
            options=[{"label": n, "value": n} for n in list(dfs.keys())],
            value=list(dfs.keys())[0]
        ),
        dcc.Graph(id='price-history'),

        html.Div(className="row", children=[
            html.Div(className="column", children=[
                dcc.Markdown("""
                    **Details**
                """),
                html.Pre(id="hover-data", style=styles["pre"])
            ]),
        ])

    ], className="container")

    @app.callback(
        Output("hover-data", "children"),
        Input("price-history", "hoverData"), Input("price-history-dropdown", "value"))
    def display_hover_data(hoverData, value):
        if hoverData is None:
            return dcc.Markdown("")

        data = hoverData["points"][0]["customdata"]
        m = dcc.Markdown(f"""
            ## {data[2]} {value} {data[1]}
            - Retailer: {data[0]}
            - Price: {hoverData["points"][0]["y"]:.2f}€
            - Date: {hoverData["points"][0]["x"]}
        """)
        return m


    @app.callback(Output("price-history", "figure"), [Input("price-history-dropdown", "value")])
    def update_graph(selected_dropdown_value):
        df = dfs[selected_dropdown_value]
        fig = px.line(df, x="date", y="price", hover_data=df)
        return fig


    # app.layout = html.Div([
    #     html.H1('Stock Tickers'),
    #     dcc.Dropdown(
    #         id='my-dropdown',
    #         options=[
    #             {'label': 'Tesla', 'value': 'TSLA'},
    #             {'label': 'Apple', 'value': 'AAPL'},
    #             {'label': 'Coke', 'value': 'COKE'}
    #         ],
    #         value='TSLA'
    #     ),
    #     dcc.Graph(id='my-graph')
    # ], className="container")

    # @app.callback(Output('my-graph', 'figure'),
    #               [Input('my-dropdown', 'value')])
    # def update_graph(selected_dropdown_value):
    #     dff = df[df['Stock'] == selected_dropdown_value]
    #     return {
    #         'data': [{
    #             'x': dff.Date,
    #             'y': dff.Close,
    #             'line': {
    #                 'width': 3,
    #                 'shape': 'spline'
    #             }
    #         }],
    #         'layout': {
    #             'margin': {
    #                 'l': 30,
    #                 'r': 20,
    #                 'b': 30,
    #                 't': 20
    #             }
    #         }
    #     }

    return app
