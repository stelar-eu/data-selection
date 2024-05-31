# File of main app
# Should not be changed if possible

import os
import sys

sys.path.append('.')
sys.path.append('..')

import streamlit as st  # pip install streamlit
from PIL import Image


import pandas as pd
from results import result_btn, sort_results, rank_select
from search_bar import search_bar
from utils import init_config, init_vars, init_style, modify_df, fetch_profile_json_url, fetch_profile_json_id
from comparison import compare_df

# -------------- SETTINGS --------------
page_title = "Dataset Selection"
title_icon = ":mag:"
dirname = os.path.dirname(__file__)
stelar_icon = os.path.join(dirname, 'icons/stelar_icon.jpg')
page_icon = stelar_icon
layout = "wide"

im = Image.open(page_icon)

st.set_page_config(page_title=page_title, page_icon=im, layout=layout)
#st.title(page_title)

col1, col2 = st.columns([2,18])
with col1: # logo
    st.image('icons/Logo-Stelar-1-f.png', width=130)
with col2: # title
    st.title(page_title)

st.subheader('Keyword Search')

init_vars()
init_style()
    
button = search_bar()

if st.session_state.results_df is not None:
    comp_tab_title = "Comparison" 
    if len(st.session_state.compared_ids) != 0:
        comp_tab_title += f" ({len(st.session_state.compared_ids)})"
    if len(st.session_state.compared_ids) < 2:
        comp_tab_title = f':gray[{comp_tab_title}]'
    tab_results, tab_comparison = st.tabs(["Results", comp_tab_title])
    
    with tab_results:
        # Get Results from a successful response
        if st.session_state.cat_response is not None and st.session_state.cat_response.status_code != 200:
            st.write("JSON Response ", st.session_state.cat_response.text)
        else:
            json_response = st.session_state.cat_response.json()
            if not json_response['success']:
                st.write("JSON Response Code 200 but Success bool is False")
            else:
                # if button:
                #     st.session_state.compared_ids = set()
                #     st.session_state.results_df = modify_df(json_response['result']['results'])
                #     st.rerun()
                
                results_df = st.session_state.results_df
                
                columns = st.columns([2,3,1,1])
                columns[0].subheader(f"Found {results_df.shape[0]} results.")
                
                rank_select()
                sort_results(columns[3])
                result_btn()
                
    
    with tab_comparison:
        if len(st.session_state.compared_ids) >= 2:
            # if st.session_state.cat_response is not None and st.session_state.cat_response.status_code == 200:
            #     json_response = st.session_state.cat_response.json()
            #     if json_response['success']:
            #         df = pd.DataFrame(json_response['result']['results']).set_index('id')
            #         df['profile_json_url'] = df.resources.apply(lambda x: fetch_profile_json_url(x))
            #         df['profile_json_id'] = df.resources.apply(lambda x: fetch_profile_json_id(x))
            #         df = df.loc[list(st.session_state.compared_ids)]
            #         compare_df(df)
            if st.session_state.results_df is not None:
                df = st.session_state.results_df
                df = df.loc[list(st.session_state.compared_ids)]
                compare_df(df)
        else:
            st.write('Please select at least two datasets for comparison.')
