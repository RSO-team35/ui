import dash
from dash.dependencies import Input, Output
from dash import dcc, html, dash_table
import plotly.express as px
import plotly.graph_objects as go
import flask
import pandas as pd
import os
import datetime
import json 
import random 
import numpy as np


def create_df(num=20, p=300):
    df = pd.DataFrame({
                    "retailer": [random.choice(["Mimovrste", "Amazon", "Microcenter"]) for _ in range(num)],
                    "model": np.resize(["Dual OC", "Dual", "TUF GAming", "", "ROG Strix"], num),
                    "manufacturer": np.resize(["ASUS", "Zotac"], num),
                    "price": [round(p + random.uniform(-p*0.1, p*0.1), 2) for _ in range(num)],
                    "date": pd.date_range(datetime.datetime.today(), periods=num).tolist()
                })
    return df


def create_dash_app(requests_pathname_prefix: str = None) -> dash.Dash:
    """
    Sample Dash application from Plotly: https://github.com/plotly/dash-hello-world/blob/master/app.py
    """

    
    dfs = {"GeForce RTX 3060": create_df(20, 300),
            "GeForce RTX 3090": create_df(20, 1500)
        }

    styles = {
        'pre': {
            'border': 'thin lightgrey solid',
            'overflowX': 'scroll'
        }
    }

    external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
    app = dash.Dash(__name__, requests_pathname_prefix=requests_pathname_prefix, external_stylesheets=external_stylesheets)

    app.scripts.config.serve_locally = False
    dcc._js_dist[0]['external_url'] = 'https://cdn.plot.ly/plotly-basic-latest.min.js'

    #fig = px.bar(df, x="Fruit", y="Amount", color="City", barmode="group")

    app.layout = html.Div([
        html.H1('GPU price comparison'),

        html.H4("GPU model selector"),
        dcc.Dropdown(
            id="price-history-dropdown",
            options=[{"label": n, "value": n} for n in list(dfs.keys())],
            value=list(dfs.keys())[0]
        ),

        html.Div(className="row", children=[
            
            html.Div(className="one-half column", children=[
                html.H4("Minimal price in recorded history"),
                html.Div("Marked dot on graph", className="row"),
                html.Pre(id="hover-data-2", style=styles["pre"])
            ]),

            html.Div(className="one-half column", children=[
                html.H4("Currently selected details"),
                html.Div("Hover over point on graph", className="row"),
                html.Pre(id="hover-data", style=styles["pre"])
            ]),
        ], style={"margin-top": "30px"}),

        dcc.Graph(id='price-history'),

        html.Div(className="row", children=[
            html.H4(children="Prices per store with details"),
            html.Div(id="table-comparison", style={"text-align":"center"})
        ], style={"text-align":"center", "margin-top": "60px"}),

        html.Div(className="row", children=[
            html.H4(children="Lowest prices per store"),
            dcc.Checklist(id="retailers-shown", inline=True),
            dcc.Graph(id='price-history-retailer'),
        ], style={"text-align":"center", "margin-top": "60px", "margin-bottom": "100px"}),
        

    ], className="container")


    @app.callback(
        Output("table-comparison", "children"),
        Input("price-history-dropdown", "value"))
    def display_table(value):
        df = dfs[value]

        # get last price
        last_pr = df[df.groupby("retailer")["date"].transform(max) == df["date"]]
        last_pr = last_pr[["price", "date", "retailer"]]
        last_pr.columns = ["last price", "last date", "retailer"]
        #last_pr.loc["last date"] = last_pr["last date"].apply(lambda x: x.date())
        print(last_pr)

        agg_df = df[df.groupby("retailer")["price"].transform(min) == df["price"]]
        #agg_df.loc["date"] = agg_df["date"].apply(lambda x: x.date())

        new_df = pd.merge(agg_df, last_pr, on="retailer")
        new_df["date"] = new_df["date"].apply(lambda x: x.date())
        new_df["last date"] = new_df["last date"].apply(lambda x: x.date())
        new_df = new_df.sort_values("price")
        print(new_df)
        return dash_table.DataTable(
            data=new_df.to_dict("records"), 
            columns=[{"id": c, "name": "Minimal price [EUR]" if c == "price" else ("Last recorded price [EUR]" if c == "last price" else c.capitalize())} for c in new_df.columns], 
            style_cell={"textAlign":"left"},
            style_cell_conditional=[{"if": {
                "row_index": 0,
                "column_id": "price"
            },
            "backgroundColor": "lightgreen",
            }]
        )


    @app.callback(
        Output("hover-data", "children"),
        Input("price-history", "hoverData"), Input("price-history-dropdown", "value"))
    def display_hover_data(hoverData, value):
        if hoverData is None:
            return dcc.Markdown("")

        data = hoverData["points"][0]["customdata"]
        m = dcc.Markdown(f"""
            ###### {data[2]} {value} {data[1]}
            - Retailer: {data[0]}
            - Price: **{hoverData["points"][0]["y"]:.2f}€**
            - Date: {hoverData["points"][0]["x"]}
        """)
        return m


    @app.callback(
        Output("hover-data-2", "children"),
        Input("price-history-dropdown", "value"))
    def display_min_price(value):
        df = dfs[value]

        data = df.iloc[np.argmin(df["price"])]
        m = dcc.Markdown(f"""
            ###### {data["manufacturer"]} {value} {data["model"]}
            - Retailer: {data["retailer"]}
            - Price: **{data["price"]:.2f}€**
            - Date: {data["date"]}
        """) # todo add links?
        return m


    @app.callback(
        Output("price-history", "figure"), 
        [Input("price-history-dropdown", "value")])
    def update_graph(selected_dropdown_value):
        df = dfs[selected_dropdown_value]
        min_price = df.iloc[np.argmin(df["price"])]

        fig = px.scatter(df, x="date", y="price", hover_data=df, labels={"date": "Date", "price":"Price"}, range_y=[min_price["price"]*0.9, max(df["price"])*1.05], trendline="lowess")
        fig.update_yaxes(tickprefix="€")
        #fig.update_layout(yaxis=dict(tickmode="linear", tick0=0, dtick=100))
        #print(np.argmin(df["price"]))
        
        print(min_price)
        fig.add_traces(go.Scatter(x=[min_price["date"]], y=[min_price["price"]], mode="markers", name="Minimal price", hoverinfo="skip"))
        fig.update_traces(marker=dict(size=12, color="lightgreen"), selector=dict(mode="markers", name="Minimal price"))
        #fig.update_layout(legend=dict(yanchor="bottom", y=0.05, xanchor="left", x=0.01))
        return fig


    @app.callback(
        Output("retailers-shown", "options"), Output("retailers-shown", "value"),
        Input("price-history-dropdown", "value"))
    def hide_retailers(value):
        df = dfs[value]
        opt = df["retailer"].unique()
        return (opt, opt)


    @app.callback(
        Output("price-history-retailer", "figure"), 
        Input("price-history-dropdown", "value"), Input("retailers-shown", "value"))
    def update_graph_retailer(value, display_val):
        df = dfs[value]
        #print(display_val)
        df = df[df.retailer.isin(display_val)]

        min_price = df.iloc[np.argmin(df["price"])]

        fig = px.line(df, x="date", y="price", color="retailer", hover_data=df, markers=True, labels={"date": "Date", "price":"Price", "retailer": "Retailer"}, range_y=[min_price["price"]*0.9, max(df["price"])*1.05])
        fig.update_yaxes(tickprefix="€")
        #fig.update_layout(yaxis=dict(tickmode="linear", tick0=0, dtick=100))
        #print(np.argmin(df["price"]))
        
        #print(min_price)
        fig.add_traces(go.Scatter(x=[min_price["date"]], y=[min_price["price"]], mode="markers", name="Minimal price", hoverinfo="skip"))
        fig.update_traces(marker=dict(size=12, color="lightgreen"), selector=dict(mode="markers"))
        #fig.update_layout(legend=dict(yanchor="middle"))
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
