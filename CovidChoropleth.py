import dash #require pip install dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output

import io
import json
import pandas as pd
import plotly.express as px #version 5.3.1 used
import requests
from urllib.request import urlopen


app = dash.Dash(__name__)

# load U.S. counties and fip code data
with urlopen('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json') as response:
    counties = json.load(response)

# Download csv from NY Times raw github
url = "https://raw.githubusercontent.com/nytimes/covid-19-data/master/us-counties.csv"
download = requests.get(url).content

# Read data into pandas
df = pd.read_csv(io.StringIO(download.decode('utf-8')))

#Format Data
pd.set_option('precision', 0)


# --------------------------------------------------------------------------
# App layout
app.layout = html.Div([

    html.H1("U.S. COVID-19 Cases by County", style={'text-align': 'center'}),

    dcc.Dropdown(id="slct_year",
                 options=[
                     {"label": "2020-10-20", "value": '2020-10-20'},
                     {"label": "2020-10-21", "value": '2020-10-21'},
                     {"label": "2020-10-22", "value": '2020-10-22'}],
                 multi=False,
                 value='2020-10-20',
                 style={'width': "40%"}
                 ),

    html.Div(id='output_container', children=[]),
    html.Br(),

    dcc.Graph(id='covid_map', figure={})

])


# ----------------------------------------------------------------------------
# Connect Choropleth with Dash Components
@app.callback(
    [Output(component_id='output_container', component_property='children'),
     Output(component_id='covid_map', component_property='figure')],
    [Input(component_id='slct_year', component_property='value')]
)

def update_graph(option_slctd):
    print(option_slctd)
    print(type(option_slctd))

    container = "Selected Date: {}".format(option_slctd)

    dff = df.copy()
    dff = dff[dff["date"] == option_slctd]


    # Plotly Express
    fig = px.choropleth(
        data_frame=dff,
        geojson=counties,
        #locationmode='USA-states',
        locations='fips',
        scope="usa",
        #center={"lat": 38.46025978235944, "lon": -96.12400854464907}, 
        #zoom=3,
        color='cases',
        hover_data=['county', 'cases'],
        color_continuous_scale=px.colors.sequential.YlOrRd,
        labels={'fips': 'County Code', 'county': 'County Name', 'cases': 'Number of Cases'},
        template='plotly_dark'
    )

    return container, fig

# ------------------------------------------------------------------------------
if __name__ == '__main__':
    app.run_server(debug=True)