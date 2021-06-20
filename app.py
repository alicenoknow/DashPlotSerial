import dash
from dash.dependencies import Output, Input
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go

from collections import deque
import atexit

from utils import Reader
import config


# ---------------------------------------- Global data ----------------------------------------
data_reader = Reader()
timeline = deque(maxlen=config.data_len)
timeline.append(0)
data_values = deque(maxlen=config.data_len)
data_values.append(0)
lat = 0.0
lon = 0.0
current_column = 0


# -------------------------------------- Creating figures -------------------------------------
def get_data_graph():
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


def get_map_figure():
    return go.Figure(
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
                style='light',
                accesstoken=config.mapbox_token,
                bearing=0,
                center=go.layout.mapbox.Center(
                    lat=lat,
                    lon=lon
                ),
                pitch=0,
                zoom=10)))


# ----------------------------------------- App layout ----------------------------------------
app = dash.Dash(__name__)

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
            figure=get_map_figure(),
            config={"displayModeBar": True, "scrollZoom": True}
        ),
    ],
    style={'padding': '0px 10px 15px 10px',
           'marginLeft': 'auto', 'marginRight': 'auto',
           'boxShadow': '0px 0px 5px 5px rgba(204,204,204,0.4)'},
)


# -------------------------------------- Callbacks -------------------------------------
@app.callback(Output('data-graph', 'figure'),
              Output('map-graph', 'figure'),
              [Input('update', 'n_intervals')])
def update_graphs(input_data):
    global lat, lon, timeline, data_values
    lat, lon, values = data_reader.parse_line()
    timeline.append(max(timeline) + 1)
    data_values.append(values[current_column])

    graph_figure = get_data_graph()
    map_figure = get_map_figure()
    return graph_figure, map_figure


@app.callback(
    Output('data-graph', 'figure'),
    [Input('columns-dropdown', 'value')])
def update_output(value):
    global current_column, timeline, data_values
    if current_column != value:
        curr_time = max(timeline)
        current_column = value
        timeline.clear()
        data_values.clear()
        _, _, values = data_reader.parse_line()
        timeline.append(curr_time + 1)
        data_values.append(values[current_column])

    return get_data_graph()


# -------------------------------------------- Exit -------------------------------------------
def on_exit():
    if data_reader:
        data_reader.close()


# -------------------------------------------- Run -------------------------------------------
if __name__ == '__main__':
    atexit.register(on_exit)
    app.run_server(debug=False)
