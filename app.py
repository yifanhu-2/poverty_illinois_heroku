#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 15 10:08:47 2022

@author: yifan
"""
import pandas as pd
from dash import Dash, html, dcc, Input, Output, State
# from dash.exceptions import PreventUpdate
import plotly.graph_objects as go
import plotly.express as px
# import time

from urllib.request import urlopen
import json
with urlopen('https://raw.githubusercontent.com/OpenDataDE/State-zip-code-GeoJSON/master/il_illinois_zip_codes_geo.min.json') as response:
    zipcodes = json.load(response)

    
# Data for display
df_race = pd.read_csv('processed_data/poverty_RACE AND HISPANIC OR LATINO ORIGIN.csv')
df_race = df_race[df_race['Stats'] == 'Estimate'].loc[df_race['Zipcode'] != 'Illinois', ~df_race.columns.isin(['Below poverty level','Stats'])] 

df2_age = pd.read_csv('processed_data/demo_age.csv')
df2_gender = pd.read_csv('processed_data/demo_gender.csv')
df2_race = pd.read_csv('processed_data/demo_race.csv')

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = Dash(__name__, external_stylesheets=external_stylesheets)

server = app.server

app.layout = html.Div([

    html.Div([
        html.H6("Select a race/ethnic group of interest:"),
        dcc.Dropdown(
            df_race['RACE AND HISPANIC OR LATINO ORIGIN'].unique(),
            'American Indian and Alaska Native alone',
            id='race-filter'
        )
    ]),


    html.Div([
        html.H6("Set a population threshold in the selected group (e.g., 10000):"),
        html.Div([
            "Population >= ",
            dcc.Input(id='pop-thresh', placeholder=10000, type='number')
        ]),
    ],  style={'width': '50%', 'display': 'inline-block'}),

    html.Div([
        html.H6("Set a threshold on percent below poverty level (e.g., 11.6):"),
        html.Div([
            "Percent below poverty level >= ",
            dcc.Input(id='pct-thresh', placeholder=11.6, type='number')
        ]),
    ],  style={'width': '50%', 'display': 'inline-block'}),


    html.Div([

        html.Button(id='submit-button', children="Submit")        
    ], style={'padding': '10px 5px'}),
    
    html.Div([
        
        html.H6(id='filter-description'),
        dcc.Graph(id="zipcodes-choropleth"),

    ]),
    
    
    html.H6("Click on a zipcode area above to see its demographic details:", id='graph-ready'),
        
    dcc.Graph(id='age-pie'),
    

    dcc.Graph(id='gender-pie'),
    

    dcc.Graph(id='race-pie'),

    
])



@app.callback([
    Output('zipcodes-choropleth', "figure"),
    Output('filter-description', 'children')
], [Input('submit-button', 'n_clicks')],
    [State('race-filter', "value"),
    State('pop-thresh', "value"),
    State('pct-thresh', 'value')])
def update_choropleth(n_clicks, race_group, pop_level, pct_poverty):
    if  n_clicks is None or n_clicks <= 0:
        fig = go.Figure()
        fig.update_layout(
            xaxis =  { "visible": False },
            yaxis = { "visible": False },
            annotations = [
                {   
                    "text": "Please set criteria above and hit submit",
                    "xref": "paper",
                    "yref": "paper",
                    "showarrow": False,
                    "font": {
                        "size": 28
                    }
                }
            ]
        )
        
        text = ''
    else:
        
        dff = df_race.loc[(df_race['RACE AND HISPANIC OR LATINO ORIGIN'] == race_group) & (df_race['Total'] >= pop_level) & (df_race['Percent below poverty level'] >= pct_poverty), :]
        dff = dff.rename(columns={'RACE AND HISPANIC OR LATINO ORIGIN': 'Race and ethnicity', 'Total': 'Population'})
    
        fig = px.choropleth(dff, 
                            geojson=zipcodes, locations='Zipcode', 
                            featureidkey='properties.ZCTA5CE10',
                            color='Percent below poverty level',
                            color_continuous_scale="Viridis",
                            range_color=(df_race['Percent below poverty level'].min(), df_race['Percent below poverty level'].max()),
                            scope="usa",
                            labels={'Percent below poverty level':'Percent below poverty level'},
                            hover_data=['Population', 'Percent below poverty level']
                            )
        fig.update_geos(fitbounds="locations")
        fig.update_layout(
            margin={"r":0,"t":0,"l":0,"b":0},
            )
        
        text = f'Showing zipcodes where the population for {race_group} is greater than {pop_level}, while more than {pct_poverty}% are below poverty level:' 
    
    return fig, text



@app.callback(
    Output('age-pie', 'figure'),
    Input('zipcodes-choropleth', 'clickData'))
def update_age_pie(clickData):
    if not clickData:
        fig = go.Figure(go.Scatter(x=[], y = []))
        fig.update_layout(template = None)
        fig.update_xaxes(showgrid = False, showticklabels = False, zeroline=False)
        fig.update_yaxes(showgrid = False, showticklabels = False, zeroline=False)
    else:
        click_zip = clickData["points"][0]['location']
    
        
        dff = df2_age[df2_age['Zipcode'] == int(click_zip)]
        
        fig = px.pie(dff, values='Estimate', names='Age group', title=f'Age ({click_zip})')
        fig.update_traces(textposition='inside')
        fig.update_layout(
            uniformtext_minsize=12, 
            uniformtext_mode='hide',
            legend_x=0,
            legend_y=1,
            )
    
    return fig

@app.callback(
    Output('gender-pie', 'figure'),
    Input('zipcodes-choropleth', 'clickData'))
def update_gender_pie(clickData):
    if not clickData:
        fig = go.Figure(go.Scatter(x=[], y = []))
        fig.update_layout(template = None)
        fig.update_xaxes(showgrid = False, showticklabels = False, zeroline=False)
        fig.update_yaxes(showgrid = False, showticklabels = False, zeroline=False)
    else:
        click_zip = clickData["points"][0]['location']
    
        
        dff = df2_gender[df2_gender['Zipcode'] == int(click_zip)]
        
        fig = px.pie(dff, values='Estimate', names='Gender', title=f'Gender ({click_zip})')
        fig.update_traces(textposition='inside')
        fig.update_layout(uniformtext_minsize=12, uniformtext_mode='hide', legend_x=0, legend_y=1)
    
    return fig

@app.callback(
    Output('race-pie', 'figure'),
    Input('zipcodes-choropleth', 'clickData'))
def update_race_pie(clickData):
    if not clickData:
        fig = go.Figure(go.Scatter(x=[], y = []))
        fig.update_layout(template = None)
        fig.update_xaxes(showgrid = False, showticklabels = False, zeroline=False)
        fig.update_yaxes(showgrid = False, showticklabels = False, zeroline=False)
    else:
        click_zip = clickData["points"][0]['location']
    
        
        dff = df2_race[df2_race['Zipcode'] == int(click_zip)]
        
        fig = px.pie(dff, values='Estimate', names='Race group', title=f'Race ({click_zip})')
        fig.update_traces(textposition='inside')
        fig.update_layout(uniformtext_minsize=12, uniformtext_mode='hide', legend_x=0, legend_y=1)
    
    return fig



# run app
if __name__ == '__main__':
    app.run_server(debug=True)




