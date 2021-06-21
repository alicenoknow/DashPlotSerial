import atexit
import json
from queue import Queue
from threading import Thread

import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
from dash.dependencies import Output, Input

import config
from reader import reader_main

# ---------------------------------------- Reader thread ----------------------------------------
tx_queue = Queue()
rx_queue = Queue()
data_reader = Thread(target=reader_main, args=[rx_queue, tx_queue])
data_reader.daemon = True


def start_reader_thread():
    data_reader.start()
    answer, args = tx_queue.get()
    if answer != "OK":
        print(args)
        exit(-1)


# -------------------------------------- Creating figures -------------------------------------
def get_data_graph(data_values, timeline):
    step = (max(data_values) - min(data_values)) / 10
    return go.Figure(
        data=[go.Scatter(
            x=list(timeline),
            y=list(data_values),
            name='Scatter',
            mode='lines+markers')],
        layout=go.Layout(
            uirevision='data-graph',
            xaxis=dict(range=[min(timeline), max(timeline)]),
            yaxis=dict(range=[min(data_values) - step, max(data_values) + step])))


def get_map_figure(lat, lon):
    map_fig = go.Figure(
        data=[go.Scattermapbox(
            lat=[lat],
            lon=[lon],
            mode='markers',
            marker=go.scattermapbox.Marker(
                size=10, symbol='airport'),
            text=['Current position'])],
        layout=go.Layout(
            uirevision='map-graph',
            hovermode='closest',
            mapbox=dict(
                style='satellite',
                accesstoken=config.mapbox_token,
                bearing=0,
                center=go.layout.mapbox.Center(
                    lat=lat,
                    lon=lon
                ),
                pitch=0,
                zoom=10)))
    return map_fig

# ----------------------------------------- App layout ----------------------------------------
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div(
    [
        html.H1(children='Supko wizualiztor', style={'text-align': 'center'}),
        html.H3(children='Wybierz kolumnę:'),
        dcc.Interval(
            id='update',
            interval=config.time_interval
        ),
        dcc.Dropdown(
            id='columns-dropdown',
            options=[{'label': f"Column {i + 1}", 'value': i} for i in range(config.columns_num - 2)],
            value=0
        ),
        dcc.Graph(
            id='data-graph',
            animate=True
        ),
        dcc.Graph(
            id='map-graph',
            figure=get_map_figure(50.0, 50.0),
            config={"displayModeBar": True, "scrollZoom": True}
        ),
        dcc.Store(id='time', data=0),
        dcc.Store(id='column', data=0)

    ],
    style={'padding': '0px 10px 15px 10px',
           'marginLeft': 'auto', 'marginRight': 'auto',
           'boxShadow': '0px 0px 5px 5px rgba(204,204,204,0.4)'},
)


# -------------------------------------- Callbacks -------------------------------------
@app.callback(Output('column', 'data'),
              [Input('columns-dropdown', 'value')])
def update_column(column):
    return json.dumps(column)


@app.callback(Output('time', 'data'),
              [Input('update', 'n_intervals')])
def update_time(time):
    return json.dumps(time)


@app.callback(Output('data-graph', 'figure'),
              Output('map-graph', 'figure'),
              [Input('time', 'data'), Input('column', 'data')])
def update_graphs(time, column):
    curr_time = json.loads(time)
    if curr_time is None:
        return dash.no_update, dash.no_update

    curr_column = json.loads(column)
    lat, lon, values = get_data()

    data_values = values[curr_column]
    timeline = [i for i in range(max(0, curr_time-config.data_len), min(curr_time+1, curr_time+len(data_values)))]

    graph_figure = get_data_graph(data_values, timeline)
    map_figure = get_map_figure(lat, lon)
    return graph_figure, map_figure


def get_data():
    rx_queue.put(('DATA', {}))
    answer, args = tx_queue.get()
    if answer == 'DATA':
        return args["lat"], args["lon"], args["values"]
    else:
        exit(-1)


# -------------------------------------------- Exit -------------------------------------------
def on_exit():
    if data_reader.is_alive():
        rx_queue.put(('EXIT', {}))
        data_reader.join()


# -------------------------------------------- Run -------------------------------------------
if __name__ == '__main__':
    atexit.register(on_exit)
    start_reader_thread()
    app.run_server(debug=False)