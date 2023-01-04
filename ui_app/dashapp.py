import dash
from dash.dependencies import Input, Output, State
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
import httpx
from circuitbreaker import circuit


@circuit(failure_threshold=2)
def get_news(product):
    try:
        ip = os.environ["DATA_NEWS_IP"]
    except:
        ip = "localhost:8003"
    print(product)
    news = httpx.get(f"http://{ip}/news/{product}/")
    
    news = pd.read_json(news)
    return news


def create_dash_app(requests_pathname_prefix: str = None) -> dash.Dash:
    """
    Dash application using Plotly
    """

    styles = {
        'pre': {
            'border': 'thin lightgrey solid',
            'overflowX': 'scroll'
        }
    }

    try:
        ip = os.environ["DATA_KEEPING_IP"]
    except:
        ip = "localhost:8000"

    
    response = httpx.get(f"http://{ip}/products/urls/")
    url_data = pd.DataFrame.from_records(response.json())
    ############

    external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
    app = dash.Dash(__name__, requests_pathname_prefix=requests_pathname_prefix, external_stylesheets=external_stylesheets)

    app.scripts.config.serve_locally = False
    dcc._js_dist[0]['external_url'] = 'https://cdn.plot.ly/plotly-basic-latest.min.js'

    
    def get_data(keys=False, val=None):
        body = """
        query Query {
            products {
                name
                prices {
                price
                retailer
                manufacturer
                date
                }
            }
        }
        """

        try:
            ip = os.environ["DATA_KEEPING_IP"]
        except:
            ip = "localhost:8000"

        try:
            response = httpx.post(url=f"http://{ip}/graphql", json={"query":body})
        except ConnectionError:
            print("Connection error - data keeping dead :(")

        print(response.status_code)

        data = {x["name"]:pd.DataFrame.from_records(x["prices"]) for x in response.json()["data"]["products"]}
        for k, v in list(data.items()):
            if len(v) == 0:
                del data[k]
            else:
                data[k] = v[v.price > 0]

        if data is None:
            return

        if keys:
            return data.keys()

        return data[val].to_dict()

    keys = list(get_data(keys=True))

    app.layout = html.Div([
        dcc.Store(id="store"),
        html.H1('GPU price comparison'),

        html.H4("GPU model selector"),
        dcc.Dropdown(
            id="price-history-dropdown",
            value=keys[0],
            options=[{"label": n, "value": n} for n in keys],
            style={"margin-bottom": "60px"}
        ),

        dcc.Tabs(id="tabs-main", value="tab-analysis", children=[
            dcc.Tab(label="Analysis", value="tab-analysis"),
            dcc.Tab(label="Content", value="tab-content")
        ]),
        html.Div(id="tabs-content"),
    ], className="container")

    @app.callback(
        Output("store", "data"),
        Input("price-history-dropdown", "value"))
    def store_data(val):
        dt = get_data(val=val)
        print("HERE GETTING UPDATED DATA...")
        return dt


    @app.callback(
        Output("tabs-content", "children"),
        Input("tabs-main", "value"))
    def create_tabs(tab):
        if tab == "tab-analysis":
            return html.Div([
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
            ])
        elif tab == "tab-content":
            return html.Div([
                #html.H4("Information about GPU"),
                html.H2("Recent related news", style={"text-align":"center"}),
                html.Div(id="news-box"),
                dcc.Markdown("hehe")
            ])


    @app.callback(
        Output("news-box", "children"),
        Input("price-history-dropdown", "value"))
    def display_news(product):
        ch = []
        try:
            news = get_news(product)
            #print(news.loc[0])
            
            for lb, row in news.iterrows():
                ch.append(create_box(row))
                ch.append(html.Hr())
        except Exception as e:
            print(e)
            ch.append(html.H4("No news found"))

        return html.Div(ch)

    def create_box(row):
        return html.Div(className="row", children=[
            html.Div(className="one-half column", children=[
                html.A(html.H4(row["title"]), href=row["url"]),
                html.Div(dcc.Markdown(f"""
                    ###### Author: {row["author"]}
                    ###### Published in: {row["source"]["name"]}
                    {row["description"]}
                """), style=styles["pre"])
            ]),

            html.Div(className="one-half column", children=[
                html.Img(src=row["urlToImage"], style={"width":"400px"}),
            ]),
        ])


    @app.callback(
        Output("table-comparison", "children"),
        Input("price-history-dropdown", "value"), Input("store", "data"))
    def display_table(value, data):
        df = pd.DataFrame.from_dict(data)

        # get last price
        last_pr = df[df.groupby("retailer")["date"].transform(max) == df["date"]]
        last_pr = last_pr[["price", "date", "retailer"]]
        last_pr.columns = ["last price", "last date", "retailer"]
        #last_pr.loc["last date"] = last_pr["last date"].apply(lambda x: x.date())
        #print(last_pr)

        agg_df = df[df.groupby("retailer")["price"].transform(min) == df["price"]]
        # if repetition use last
        agg_df = agg_df[agg_df.groupby("retailer")["date"].transform(max) == agg_df["date"]]
        agg_df = agg_df[["retailer", "price", "date"]]
        #agg_df.loc["date"] = agg_df["date"].apply(lambda x: x.date())
        #print(agg_df)

        new_df = pd.merge(agg_df, last_pr, on="retailer")
        if type(new_df["date"][new_df["date"].first_valid_index()]) is not pd.Timestamp:
            new_df["date"] = new_df["date"].apply(lambda x: datetime.datetime.fromisoformat(x).date())
        else:
            new_df["date"] = new_df["date"].apply(lambda x: x.date())
        
        if type(new_df["last date"][new_df["last date"].first_valid_index()]) is not pd.Timestamp:
            new_df["last date"] = new_df["last date"].apply(lambda x: datetime.datetime.fromisoformat(x).date())
        else:
            new_df["last date"] = new_df["last date"].apply(lambda x: x.date())

        new_df = new_df.sort_values("price")
        #print(new_df)
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

        try:
            hdata = hoverData["points"][0]["customdata"]
            m = dcc.Markdown(f"""
                ###### {hdata[1]} {value} 
                - Retailer: {hdata[0]}
                - Price: **{hoverData["points"][0]["y"]:.2f}€**
                - Date: {hoverData["points"][0]["x"]}
            """)
        except:
            m = dcc.Markdown(f"""
                ###### {value} 
                - Price: **{hoverData["points"][0]["y"]:.2f}€**
                - Date: {hoverData["points"][0]["x"]}
            """)
        return m


    @app.callback(
        Output("hover-data-2", "children"),
        Input("price-history-dropdown", "value"), Input("store", "data"))
    def display_min_price(value, data):
        df = pd.DataFrame.from_dict(data)
        #print("Getting link")
        mdata = df.iloc[np.argmin(df["price"])]
        #print(mdata)
        try:
            link = url_data[url_data[["retailer", "manufacturer", "name"]].isin([mdata["retailer"], mdata["manufacturer"],value]).all(axis=1)]
            link = link.iloc[0]
            print(link)
        except:
            link = None

        txt = f"""
            ###### {mdata["manufacturer"]} {value}
            - Retailer: {mdata["retailer"]}
            - Price: **{mdata["price"]:.2f}€**
            - Date: {mdata["date"]}
        """

        if link is not None:
            txt = txt + f"""    - Link: [{link["manufacturer"]} {value} {link["model"]}]({link["url"]})"""

        return dcc.Markdown(txt)


    @app.callback(
        Output("price-history", "figure"), 
        Input("price-history-dropdown", "value"), Input("store", "data"))
    def update_graph(selected_dropdown_value, data):
        df = pd.DataFrame.from_dict(data)

        min_price = df.iloc[np.argmin(df["price"])]

        if type(df["date"][df["date"].first_valid_index()]) is not pd.Timestamp:
            df["date"] = df["date"].apply(lambda x: datetime.datetime.fromisoformat(x))

        fig = px.scatter(df, x="date", y="price", hover_data=df, labels={"date": "Date", "price":"Price"}, range_y=[min_price["price"]*0.9, max(df["price"])*1.05], trendline="lowess")
        fig.update_yaxes(tickprefix="€")
        #fig.update_layout(yaxis=dict(tickmode="linear", tick0=0, dtick=100))
        #print(np.argmin(df["price"]))
        
        #print(min_price)
        fig.add_traces(go.Scatter(x=[min_price["date"]], y=[min_price["price"]], mode="markers", name="Minimal price", hoverinfo="skip"))
        fig.update_traces(marker=dict(size=12, color="lightgreen"), selector=dict(mode="markers", name="Minimal price"))
        #fig.update_layout(legend=dict(yanchor="bottom", y=0.05, xanchor="left", x=0.01))
        return fig


    @app.callback(
        Output("retailers-shown", "options"), Output("retailers-shown", "value"),
        Input("price-history-dropdown", "value"), Input("store", "data"))
    def hide_retailers(value, data):
        df = pd.DataFrame.from_dict(data)
        opt = df["retailer"].unique()
        return (opt, opt)


    @app.callback(
        Output("price-history-retailer", "figure"), 
        Input("price-history-dropdown", "value"), Input("retailers-shown", "value"), Input("store", "data"))
    def update_graph_retailer(value, display_val, data):
        df = pd.DataFrame.from_dict(data)
        #print(display_val)
        df = df[df.retailer.isin(display_val)]

        min_price = df.iloc[np.argmin(df["price"])]

        if type(df["date"][df["date"].first_valid_index()]) is not pd.Timestamp:
            df["date"] = df["date"].apply(lambda x: datetime.datetime.fromisoformat(x))
        fig = px.line(df, x="date", y="price", color="retailer", hover_data=df, markers=True, labels={"date": "Date", "price": "Price", "retailer": "Retailer"}, range_y=[min_price["price"]*0.9, max(df["price"])*1.05])
        fig.update_yaxes(tickprefix="€")
        #fig.update_layout(yaxis=dict(tickmode="linear", tick0=0, dtick=100))
        #print(np.argmin(df["price"]))
        
        #print(min_price)
        fig.add_traces(go.Scatter(x=[min_price["date"]], y=[min_price["price"]], mode="markers", name="Minimal price", hoverinfo="skip"))
        fig.update_traces(marker=dict(size=12, color="lightgreen"), selector=dict(mode="markers"))
        #fig.update_layout(legend=dict(yanchor="middle"))
        return fig

    return app
