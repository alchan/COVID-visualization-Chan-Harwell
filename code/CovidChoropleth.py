import dash #required: pip install dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output, State
import io
import json
from math import inf, ceil
import numpy as np
import os
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
                'state' : str
            }
df = pd.read_csv(io.StringIO(download.decode('utf-8')), dtype=dict_dtypes)

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

# -------Alaska
    # Note: Wade Hampton Census Area County has no reported cases to date
    # Makes new entries for Yakutat and Hoonah-Angoon Separately, as well as Bristol Bay and Lake and Peninsula Borough counties
al = df[(df['county'] == 'Yakutat plus Hoonah-Angoon') | (df['county'] == 'Bristol Bay plus Lake and Peninsula')]
alaskaList = []
for row in al.itertuples():
    day, initCounty, state, cases, deaths = row[1], row[2], row[3], row[5], row[6]
   
    yakHoonah = {'Yakutat City and Borough': '02282', 'Hoonah-Angoon Census Area': '02105'}
    bristolLake = {'Bristol Bay Borough': '02060', 'Lake and Peninsula Borough': '02164'}    
    chosen = (yakHoonah, bristolLake) [initCounty == 'Bristol Bay plus Lake and Peninsula']

    for county, fips in chosen.items():
        alaskaList.append((day, county, state, fips, cases, deaths))

df = df.append(pd.DataFrame(alaskaList, columns=['date', 'county', 'state', 'fips', 'cases', 'deaths']), ignore_index=True)

#_____Format Data_____
df['cases'].fillna(0)
df['deaths'].fillna(0)
df['logcases'] = df['cases']
df['logdeaths'] = df['deaths']

df['logcases'] = df['logcases'].apply(lambda x: x if x is not np.NaN else 0)
df['logcases'] = df['logcases'].apply(lambda x: np.log10(x))

df['logdeaths'] = df['logdeaths'].apply(lambda x: x if x is not np.NaN else 0)
df['logdeaths'] = df['logdeaths'].apply(lambda x: np.log10(x))
pd.set_option('precision', 0)

# Fill in missing data for Oglala Lakota county
daterange = pd.date_range('2020-03-15', df['date'].max())
missingList = []

for dte in daterange:
    day = dte.strftime('%Y-%m-%d')
    county= 'Oglala Lakota'
    fip = '46113'
    state = 'South Dakota'
    missingList.append((day, county, state, fip, 0, 0, 0, 0))

df = df.append(pd.DataFrame(missingList,
                                columns=['date', 'county', 'state', 'fips', 'cases', 'deaths', 'logcases', 'logdeaths']), ignore_index=True)

# Function to create and save image of choropleth to assets folder
def save_frame(year_slctd, data_slctd, url):
    dff = df[df["date"] == year_slctd]
    log = ('logdeaths', 'logcases') [data_slctd == 'cases']
    maxColor = dff[log].max() + 1
    hoverBool = (True, False) if data_slctd == 'cases' else (False,True)
    
    fig = px.choropleth(
        data_frame=dff,
        geojson=counties,
        locations='fips',
        scope="usa",
        color=log,
        hover_data={'county':True, data_slctd:True, 'state':True, 'logcases':hoverBool[0], 'logdeaths':hoverBool[1]},
        color_continuous_scale="Oryel",
        range_color= (0, maxColor),
        labels={'fips': 'County Code', 'county': 'County Name', 
        'cases': 'Number of Cases', 'deaths': 'Reported Deaths',
        'logcases': 'Log Scaled Cases', 'logdeaths': 'Log Scaled Deaths',
        'state': 'State'},
        template='plotly_dark',
        width=1800,
        height=690
    )

    annotation = {
    'xref': 'paper',
    'yref': 'paper',
    'x': 0.01,
    'y': 0.99,
    'text': str(year_slctd),
    'showarrow': False,
    'font': {'size': 24, 'color': 'white'}
    }
    fig.add_annotation(annotation)

    tickV = [dff[log].min(), dff[log].quantile(0.5), dff[log].quantile(0.9), dff[log].max()]
    
    for i,v in enumerate(tickV):
        if np.isnan(tickV[i]) or tickV[i] == -inf:
            tickV[i] = 0
    
    tickT = [int(10**tickV[0]), int(10**tickV[1]), 
            int(10**tickV[2]), int(10 **tickV[3])]
    titleText = "Reported Cases"
    if log == 'logdeaths':
        titleText = "Reported Deaths"

    fig.update_layout(coloraxis_colorbar=dict(
    title=titleText,
    tickvals=tickV,
    ticktext=tickT
    ),
    geo = dict(
        landcolor = '#a794b9',
        lakecolor = '#04DCF6'
    ),
    title={
        'text': titleText,
        'y':0.91,
        'x':0.5,
        'xanchor':'center',
        'yanchor':'top',
        'font': {
            'size':27,
            'color':"white"}
        }
    )
    fig.write_image(url)

# Populate any missing images since time of last data pull and create dateIndexer dict for Slider
dateIndexer = {}
daterange, i = pd.date_range(df['date'].min(), df['date'].max()), 0
dirname = os.path.dirname(__file__)
assets_path = os.path.join(dirname, 'assets')
if not os.path.exists(assets_path):
    os.mkdir(assets_path)
    os.mkdir(assets_path + '/Cases')
    os.mkdir(assets_path + '/Deaths')
    
for dte in daterange:
    day = dte.strftime('%Y-%m-%d')
    dateIndexer[i] = day
    i += 1
    urlc, urld =  assets_path + '/Cases/' +'c' + day + '.png', assets_path + '/Deaths/' + 'd' + day + '.png'
    if not os.path.exists(urlc):
        save_frame(day, 'cases', urlc)
    if not os.path.exists(urld):
        save_frame(day, 'deaths', urld)

# ------------------------------------------------App Layout-------------------------------------------------------------
app = dash.Dash(__name__)
bg = 'white'
mx = max(dateIndexer, key=int)
app.layout = html.Div([
    dcc.Interval(
            id='frame-interval',
            interval=200, # Animation speed in milliseconds
            n_intervals=0,
            disabled=True
        ),

    html.H1("U.S. COVID-19 Statistics by County", style={'text-align': 'center', 'backgroundColor': bg}),

    html.Div(children=[
        dcc.RadioItems(id="slct_data", options=[
        {'label': 'Show Cases', 'value': 'cases'},
        {'label': 'Show Deaths', 'value': 'deaths'}],
        value='cases',
        labelStyle={'display': 'inline-block', 'backgroundColor': 'yellow', 'fontSize':20},
        inputStyle={"margin-left": "20px"})],
        style = {'width' : '100%', 'display' : 'flex', 'align-items': 'center', 'justify-content' : 'center'}),

    html.Br(),
    
    html.Div(children=[
        dcc.DatePickerSingle(
        id='slct_day',
        min_date_allowed= df['date'].min(),
        max_date_allowed= df['date'].max(),
        date=df['date'].min())],
        style = {'width' : '100%', 'display' : 'flex', 'align-items': 'center', 'justify-content' : 'center', 'background':bg}),

    html.Br(),

    html.Div(children=[
    dcc.Graph(id='covid_map', figure={})],
    style = {'width' : '100%', 'display' : 'flex', 'align-items': 'center', 'justify-content' : 'center', 'background':bg}),
    
    html.Div(children=(
        html.H1("Choropleth Frame Slider", style={'text-align': 'center', 'backgroundColor': 'Yellow'})
        )
    ),
    html.Div('Manually Drag Slider or Play as Animation', style={'fontSize': 20, 'color': 'gray', 'text-align':'center'}),
    html.Br(),

    html.Div(children=[
        html.Button('Play/Pause Animation', id='play-anim', n_clicks=0)],
        style = {'width' : '100%', 'display' : 'flex', 'align-items': 'center', 'justify-content' : 'center', 'background':bg}),
    html.Br(),

    # Slider only accepts integers. The dateIndexer dict is used to convert each to int to a date
    dcc.Slider(
        id='frameSlider',
        min=0,
        max=max(dateIndexer, key=int),
        value=0,
        marks = {0:dateIndexer[0], ceil(mx/2):dateIndexer[ceil(mx/2)], mx: dateIndexer[mx]},
        updatemode = 'drag'
    ),

    html.Div(id='frameBox', children=[
        html.Img(
            src='/assets/Cases/c2020-01-21.png'
        )],
    style = {'width' : '100%', 'display' : 'flex', 'align-items': 'center', 'justify-content' : 'center', 'background':bg}),

    html.Br()

    #END OF PARENT DIV
    ], style = {'background':bg})

# -------------------------------Application Callback Functions---------------------------------------------
# Update Main choropleth when date or data is changed
@app.callback(
    Output(component_id='covid_map', component_property='figure'),
    [Input(component_id='slct_day', component_property='date'),
    Input(component_id='slct_data', component_property='value')]
)

def update_graph(year_slctd, data_slctd):
    dff = df[df["date"] == year_slctd]
    # Choose log column to use for color scale
    log = ('logdeaths', 'logcases') [data_slctd == 'cases']
    maxColor = dff[log].max() + 1
    hoverBool = (True, False) if data_slctd == 'cases' else (False,True)
    
    fig = px.choropleth(
        data_frame=dff,
        geojson=counties,
        locations='fips',
        scope="usa",
        color=log,
        hover_data={'county':True, data_slctd:True, 'state':True, 'logcases':hoverBool[0], 'logdeaths':hoverBool[1]},
        color_continuous_scale="Oryel",
        range_color= (0, maxColor),
        labels={'fips': 'County Code', 'county': 'County Name', 
        'cases': 'Number of Cases', 'deaths': 'Reported Deaths',
        'logcases': 'Log Scaled Cases', 'logdeaths': 'Log Scaled Deaths',
        'state': 'State'},
        template='plotly_dark',
        width=1800,
        height=690
    )

    annotation = {
    'xref': 'paper',
    'yref': 'paper',
    'x': 0.01,
    'y': 0.99,
    'text': str(year_slctd),
    'showarrow': False,
    'font': {'size': 24, 'color': 'white'}
    }
    fig.add_annotation(annotation)

    tickV = [dff[log].min(), dff[log].quantile(0.5), dff[log].quantile(0.9), dff[log].max()]
    
    for i,v in enumerate(tickV):
        if np.isnan(tickV[i]) or tickV[i] == -inf:
            tickV[i] = 0
    
    tickT = [int(10**tickV[0]), int(10**tickV[1]), 
            int(10**tickV[2]), int(10 **tickV[3])]
    titleText = "Reported Cases"
    if log == 'logdeaths':
        titleText = "Reported Deaths"

    fig.update_layout(coloraxis_colorbar=dict(
    title=titleText,
    tickvals=tickV,
    ticktext=tickT,
    ),
    geo = dict(
        landcolor = '#a794b9',
        lakecolor = '#04DCF6'
    ),
    title={
        'text': titleText,
        'y':0.91,
        'x':0.5,
        'xanchor':'center',
        'yanchor':'top',
        'font': {
            'size':27,
            'color':"white"}
        },
    )
    return fig


# Update Map Frame Shown when slider is moved
@app.callback(
    Output(component_id='frameBox', component_property='children'),
    [Input(component_id='frameSlider', component_property='value'),
    Input(component_id='slct_data', component_property='value')]
)

def update_frame(sliderKey, data_slct):
    day = dateIndexer[sliderKey]
    url = ('/assets/Deaths/' + 'd' + day + '.png', '/assets/Cases/' +'c' + day + '.png') [data_slct == 'cases']
    frame = html.Img(src=url)
    return frame
    

# Increments Frame Slider whenever interval is enabled via Play/Pause button
@app.callback(
    Output(component_id='frameSlider', component_property='value'),
    Input(component_id='frame-interval', component_property='n_intervals'),
    State('frameSlider', 'value')
)

def playFrames(n, slideVal):
    if slideVal < max(dateIndexer, key=int):
        return slideVal + 1
    return 0


# Enable/Disable Interval used for animating image frames when Play/Pause button is pressed
@app.callback(
    Output('frame-interval', 'disabled'),
    Input('play-anim', 'n_clicks'),
    State('frame-interval', 'disabled')
)

def start_stop_interval(button_clicks, disabled_state):
    if button_clicks is not None and button_clicks > 0:
        return not disabled_state
    else:
        return disabled_state

# ----------------------------------------------------------------------------
if __name__ == '__main__':
    #set debug=True for development
    app.run_server(debug=True)