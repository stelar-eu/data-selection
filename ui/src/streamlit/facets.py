# File for the facets panel
# Mostly Kostas

import streamlit as st
from collections import Counter
import numpy as np
import pandas as pd
import json
from datetime import datetime, date, timedelta
import requests
import matplotlib.pyplot as plt
import plotly.express as px
import os
import folium
from map import map_geometries, get_drawn_shape, geom_to_shape
from streamlit_folium import st_folium
import re
import geopandas as gpd

def date(x, dformat):
    return datetime.strptime(x, dformat)

def get_day_range(s_date, e_date):
    return [s_date + timedelta(days=x) for x in range((e_date - s_date).days + 1)]

def get_month_range(s_date, e_date):
    # Get the first day of the start month
    start_month = datetime(s_date.year, s_date.month, 1)
    
    months = []
    # Iterate through months until reaching or passing the end month
    current_month = start_month
    while current_month <= e_date:
        months.append(current_month)
        # Move to the next month
        if current_month.month == 12:
            current_month = datetime(current_month.year + 1, 1, 1)
        else:
            current_month = datetime(current_month.year, current_month.month + 1, 1)
    return months

def facet_list():

    facets = st.session_state.fields
    
    exp = st.expander('Facets')
    facet_tabs = exp.tabs([x[0] for x in facets.values()])
   
    
    # KLMS API connection details
    details = st.session_state.config

    connect = details['connect']
    # URL to KLMS API
    KLMS_API = connect['KLMS_API']

    # Provide the API key required for requests regarding packages
    headers = {'Content-Type': 'application/json', 'Api-Token': connect['API_KEY']}
    
    facets_widgets = {}
    # results = json_response['result']['results']
    
    # print("This ", st.session_state.results_df is None)
    
    for no, (facet_col, (facet_label, facet_type)) in enumerate(facets.items()):
        # print(no, (facet_col, (facet_label, facet_type)))
        last_val = st.session_state.last_query.get(facet_col)
        # print(facet_col, last_val)
        
        if st.session_state.results_df is None:
            cfile = f'../../cache/{facet_col}.json'
            if os.path.exists(cfile):
                facet_response = json.load(open(cfile))
            else:
                os.makedirs(os.path.dirname(cfile), exist_ok=True)
                facet_response = requests.post(KLMS_API+details['commands']['values'],
                                           json= {"q": facet_col}, headers=headers).json()    
                with open(cfile, 'w') as o:
                    o.write(json.dumps(facet_response, indent=4))
                
        if facet_type == 'CatSingle':
            if st.session_state.results_df is not None:
                if st.session_state.results_df.empty:
                    vals = Counter()
                else:
                    vals = Counter(st.session_state.results_df[facet_col].values)
            else:
                vals = Counter()
                for res in facet_response:
                    vals.update(res['arr_values'])
            
            options = [f'{k} ({v})' for k,v in vals.most_common(len(vals))]
            last_val = set(last_val) if last_val is not None else set()
            vals = [f'{k} ({v})' for k,v in vals.most_common(len(vals)) if k in last_val]
            widget = facet_tabs[no].multiselect(facet_label, options, vals)
            facets_widgets[facet_col] = widget
        elif facet_type == 'CatMultiple':
            if st.session_state.results_df is not None:
                vals = Counter()
                if not st.session_state.results_df.empty:
                    for val in st.session_state.results_df[facet_col].dropna().values:
                        vals.update(val)
            else:
                vals = Counter()
                for res in facet_response:
                    vals.update(res['arr_values'])
            options = [f'{k} ({v})' for k,v in vals.most_common(len(vals))]
            last_val = set(last_val) if last_val is not None else set()
            vals = [f'{k} ({v})' for k,v in vals.most_common(len(vals)) if k in last_val]
            widget = facet_tabs[no].multiselect(facet_label, options, vals)
            facets_widgets[facet_col] = widget     
        elif facet_type == 'DateRange':

            start_date = datetime(1975, 3, 15)
            start_val = start_date
            end_date = datetime.now()
            end_val = end_date
            
            
            dates = Counter()
            init_plot = True
            if st.session_state.results_df is None:
                cfile = '../../cache/temporal_extent_plot.json'
                if os.path.exists(cfile):
                    init_plot = False
            
            if st.session_state.results_df is not None:
                
                #TODO: Replace values here
                
                dformat = '%Y-%m-%d'
                for index, res in st.session_state.results_df.iterrows():
                    if res['temporal_start'] is None or res['temporal_start'] == "None" or pd.isna(res['temporal_start']):
                        s_date = start_date
                    else:
                        sep = 'T' if 'T' in res['temporal_start'] else ' '
                        s_date = date(res['temporal_start'].split(sep)[0], dformat)
                    if s_date < start_val:
                        start_val = s_date
                        
                    if res['temporal_end'] is None or res['temporal_end'] == "None" or pd.isna(res['temporal_end']):
                        e_date = end_date
                    else:
                        sep = 'T' if 'T' in res['temporal_end'] else ' '
                        e_date = date(res['temporal_end'].split(sep)[0], dformat)
                    if e_date > end_val:
                        end_val = e_date
                    
                    #TODO: UNCOMMENT fewer results
                    # date_range = [s_date + timedelta(days=x) for x in range((e_date - s_date).days + 1)]
                    # date_range = get_day_range(s_date, e_date)
                    date_range = get_month_range(s_date, e_date)
                    dates.update(date_range)
            else:
                # dformat = '%d %b %Y'
                dformat = '%Y-%m-%d'
                
                for res in facet_response:
                    if res['temporal_start'] is None or res['temporal_start'] == "None":
                        s_date = start_date
                    else:
                        # s_date = date(res['temporal_start'][5:16], dformat)
                        s_date = date(res['temporal_start'].split('T')[0], dformat)
                    if s_date < start_val:
                        start_val = s_date
                        
                    if res['temporal_end'] is None or res['temporal_end'] == "None":
                        e_date = end_date
                    else:
                        # e_date = date(res['temporal_end'][5:16], dformat)
                        e_date = date(res['temporal_end'].split('T')[0], dformat)
                    if e_date > end_val:
                        end_val = e_date
                        
                    #TODO: UNCOMMENT
                    if init_plot:
                        # date_range = [s_date + timedelta(days=x) for x in range((e_date - s_date).days + 1)]
                        # date_range = get_day_range(s_date, e_date)
                        date_range = get_month_range(s_date, e_date)
                        dates.update(date_range)
            
                cfile = '../../cache/temporal_extent_plot.json'
                if init_plot:
                    # print(dates)
                    dates = {k.strftime("%d/%m/%Y"): v for k,v in dates.items()}
                    os.makedirs(os.path.dirname(cfile), exist_ok=True)
                    with open(cfile, 'w') as o:
                        o.write(json.dumps(dates, indent=4))
                else:
                    dates = json.load(open(cfile))
                    dates = {date(k, "%d/%m/%Y"): v for k,v in dates.items()}
            
            # dates.update([datetime.now()])
            if len(dates) > 0:
                fig = px.histogram(x=dates.keys(), y=dates.values(), nbins=100)
                fig.update_layout(xaxis_title_text=facet_label, yaxis_title_text='Frequency')
                facet_tabs[no].plotly_chart(fig)
            
            last_val = [date(last_val[0], dformat), date(last_val[1], dformat)] if last_val is not None else []
            facets_widgets['temporal_extent'] = facet_tabs[no].date_input("Temporal Extent", last_val)
        elif facet_type == 'DateSingle':
            if st.session_state.results_df is not None:
                if st.session_state.results_df.empty:
                    vals = []
                else:
                    vals = st.session_state.results_df[facet_col].dropna().values
            else:
                vals = np.array([date(res['temporal_start'].split('T')[0], dformat) for res in facet_response])
            c = Counter(vals)
            if len(c) == 0:
                continue
            fig = px.histogram(x=c.keys(), y=c.values())
            fig.update_layout(xaxis_title_text=facet_label, yaxis_title_text='Frequency')
            facet_tabs[no].plotly_chart(fig)
            min_k, max_k = min(c.keys()), max(c.keys())
            
            last_val = [date(last_val[0], dformat), date(last_val[1], dformat)] if last_val is not None else []
            facets_widgets[facet_col] = facet_tabs[no].date_input(facet_label, last_val)
            
        elif facet_type == 'Numeric':
            # print(facet_col)
            if st.session_state.results_df is not None:
                if st.session_state.results_df.empty:
                    vals = []
                else:
                    vals = st.session_state.results_df[facet_col].dropna().values
            else:
                vals = np.array([float(res['value']) for res in facet_response])
            c = Counter(vals)
            # print(c)
            if len(c) == 0:
                continue
            fig = px.histogram(x=c.keys(), y=c.values())
            fig.update_layout(xaxis_title_text=facet_label, yaxis_title_text='Frequency')
            facet_tabs[no].plotly_chart(fig)
            min_k, max_k = min(c.keys()), max(c.keys())
            
            last_val = last_val if type(last_val)!=list else f'{last_val[0]} - {last_val[1]}'
            
            
            # if facet_type == 'RangeNumeric':
            #     last_val = last_val if last_val is not None else ()
            #     facets_widgets[facet_col] = facet_tabs[no].slider('Choose a value from the range', 
            #                                                   min_k, max_k,
            #                                                   # (min_k, max_k)
            #                                                   last_val
            #                                                   )
            # elif facet_type == 'SingleNumeric':
            #     last_val = last_val #no check, else is None already
            #     facets_widgets[facet_col] = facet_tabs[no].slider('Choose a value from the range', 
            #                                                       min_k, max_k,
            #                                                       # (min_k+max_k)//2
            #                                                       last_val
            #                                                       )
            val = facet_tabs[no].text_area("Choose a single value or range:",
                                           value=last_val, 
                                           placeholder=f'{min_k} - {max_k}')
            pattern_single_number = r'^(\d+)$'
            pattern_number_dash_number = r'^(\d+)\s*-\s*(\d+)$'
            
            # Compile the regular expressions
            regex_single_number = re.compile(pattern_single_number)
            regex_number_dash_number = re.compile(pattern_number_dash_number)
            
            val = val if val else ""
            # Check if the input string matches either pattern
            if regex_single_number.match(val):
                val = float(val)
            elif regex_number_dash_number.match(val):
                vals = val.split('-')
                val = (float(vals[0]), float(vals[1]))
            else:
                val = None
            
            facets_widgets[facet_col] = val
        elif facet_type == 'Spatial':    
            if st.session_state.results_df is not None:
                df = pd.DataFrame()
                if not st.session_state.results_df.empty:
                    df['spatial'] = st.session_state.results_df[facet_col]
                    df['id'] = st.session_state.results_df['id']
                    df = df.dropna().reset_index(drop=True)
                    df['geometry'] = df.apply(lambda row: geom_to_shape(row['spatial']), axis=1)
            else:
                df = pd.DataFrame(facet_response)
                df['id'] = range(df.shape[0])
                df['geometry'] = df.apply(lambda row: geom_to_shape(row['the_geom']), axis=1)

            # Create the map
            m = folium.Map(tiles='OpenStreetMap', location=[45.0, 10.0], zoom_start=3,
                           min_zoom =2, max_bounds=True)            
            
            if not df.empty:
                map_geometries(m, df, show_bbox=False)            
            
            # Create GeoDataFrame with polygons of European countries from GeoJSON file
            gdf_countries = pd.DataFrame()
            with open('../../cache/countries.geojson') as geojson_file:
            	countries = json.load(geojson_file)
            	gdf_countries = gpd.GeoDataFrame.from_features(countries['features'])
            	gdf_countries = gdf_countries.filter(['NAME', 'geometry'])
            	gdf_countries = gdf_countries.set_index('NAME')
            	gdf_countries.sort_index(inplace=True)  # Sorted lexicographically
            
            # facets_widgets[facet_col] = get_drawn_shape(m, pd.DataFrame(), facet_tabs[no])
            facets_widgets[facet_col] = get_drawn_shape(m, gdf_countries, facet_tabs[no])

    # Button to update
    # return update_button(facets_widgets, exp, facets)
    return facets_widgets
