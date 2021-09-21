import dash #required: pip install dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output

from datetime import date
import io
import json
import numpy as np
import pandas as pd
import plotly.express as px #version 5.3.1 used
import requests
from urllib.request import urlopen


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


# -------------------------------------------------------------------------------------
# ____Geographic Exceptions ____

# -------New York City
# Makes list of new rows for NYC Counties, then convert it to dataframe and appends to df
# Not directly appended to df for performance optimization
ny = df[df['county'] == 'New York City']
nyList = []
for row in ny.itertuples():
    day, state, cases, deaths = row[1], row[3], row[5], row[6]
    
    nyCounties = {'New York': '36061', 'Kings': '36047', 'Queens': '36081', 'Bronx': '36005', 'Richmond': '36085'}
    
    for county, fips in nyCounties.items():
        nyList.append((day, county, state, fips, cases, deaths))

df = df.append(pd.DataFrame(nyList, columns=['date', 'county', 'state', 'fips', 'cases', 'deaths']), ignore_index=True)

# -------Kansas City
    # No FIPS code, Kansas city is its own municipal entity
    # Perhaps add new entry for each of the 4 comprising counties similar to the NYC solution
# -------Joplin Mo.
    # Skipped at present

# -------Alaska
    # Note: Valdez-Cordova Census area already displays on map
    # Note: Wade Hampton Census Area County has no reported cases to date
    # Makes new entries for Yakutat and Hoonah-Angoon Separately, as well as Bristol Bay and Lake and Peninsula Borough counties

al = df[(df['county'] == 'Yakutat plus Hoonah-Angoon') | (df['county'] == 'Bristol Bay plus Lake and Peninsula')]
alaskaList = []
for row in al.itertuples():
    day, initCounty, state, cases, deaths = row[1], row[2], row[3], row[5], row[6]
   
    yakHoonah = {'Yakutat City and Borough': '02282', 'Hoonah-Angoon Census Area': '02105'}
    bristolLake = {'Bristol Bay Borough': '02060', 'Lake and Peninsula Borough': '02164'}
    
    chosen = yakHoonah
    if(initCounty == 'Bristol Bay plus Lake and Peninsula'):
        chosen = bristolLake
    
    for county, fips in chosen.items():
        alaskaList.append((day, county, state, fips, cases, deaths))

df = df.append(pd.DataFrame(alaskaList, columns=['date', 'county', 'state', 'fips', 'cases', 'deaths']), ignore_index=True)

#Format Data
df['logcases'] = df['cases']
df['logdeaths'] = df['deaths']

df['logcases'] = df['logcases'].apply(lambda x: np.log(x) if np.logical_and(x > 0, x != np.NaN) else x)
df['logdeaths'] = df['logdeaths'].apply(lambda x: np.log(x) if np.logical_and(x > 0, x != np.NaN) else x)

pd.set_option('precision', 0)

app = dash.Dash(__name__)
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

    # choose log column to use for color scale
    log = 'logcases'
    if data_slctd == 'deaths':
        log = 'logdeaths'
    maxColor = dff[log].max() + 1
    
    # Plotly Express
    fig = px.choropleth(
        data_frame=dff,
        geojson=counties,
        locations='fips',
        scope="usa",
        color=log,
        hover_data=['county', data_slctd],
        #color_discrete_sequence= px.colors.sequential.Plasma_r,
        color_continuous_scale="Viridis",
        range_color= (0, maxColor),
        labels={'fips': 'County Code', 'county': 'County Name', 
        'cases': 'Number of Cases', 'deaths': 'Reported Deaths',
        'logcases': 'Scaled Cases', 'logdeaths': 'Scaled Deaths'},
        template='plotly_dark',
        width=1900,
        height=700
    )

    return container, fig

# ----------------------------------------------------------------------------
if __name__ == '__main__':
    app.run_server(debug=True)