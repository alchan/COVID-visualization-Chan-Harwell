import dash #required: pip install dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output

from datetime import date, timedelta
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
dict_dtypes = {'county' : str,
                'fips' : str,
                'state' : str,
            }
df = pd.read_csv(io.StringIO(download.decode('utf-8')), dtype=dict_dtypes)


#Format Data
pd.set_option('precision', 0)


# ----------------------------------------------------------------------------
# App layout
app.layout = html.Div([

    html.H1("U.S. COVID-19 Statistics by County", style={'text-align': 'center'}),

    dcc.RadioItems(id="slct_data",
    options=[
        {'label': 'Show Active Cases', 'value': 'cases'},
        {'label': 'Show Deaths', 'value': 'deaths'}],
    value='cases',
    labelStyle={'display': 'inline-block'}
    ),
    html.Br(),
    
    dcc.DatePickerSingle(
        id='slct_day',
        min_date_allowed= df['date'].min(),
        max_date_allowed= df['date'].max(),
        initial_visible_month= date.today(),
        date=df['date'].min(),
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
    [Input(component_id='slct_day', component_property='date'),
    Input(component_id='slct_data', component_property='value')]
)

def update_graph(year_slctd, data_slctd):
    print(year_slctd)
    print(type(year_slctd))

    container = "Selected Date: {}".format(year_slctd)

    dff = df.copy()
    dff = dff[dff["date"] == year_slctd]

    # Plotly Express
    fig = px.choropleth(
        data_frame=dff,
        geojson=counties,
        locations='fips',
        scope="usa",
        color=data_slctd,
        hover_data=['county', data_slctd],
        color_discrete_sequence= px.colors.sequential.Plasma_r,
        labels={'fips': 'County Code', 'county': 'County Name', 'cases': 'Number of Cases', 'deaths': 'Reported Deaths'},
        template='plotly_dark',
        width=1900,
        height=700
    )

    return container, fig

# ------------------------------------------------------------------------------
if __name__ == '__main__':
    app.run_server(debug=True)