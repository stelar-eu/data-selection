# File of main app
# Should not be changed if possible

import os
import sys

sys.path.append('.')
sys.path.append('..')

import streamlit as st  # pip install streamlit
from PIL import Image


import pandas as pd
from results import result_btn, sort_results, rank_select_2
from search_bar import search_bar
from utils import init_config, init_vars, init_style, modify_df, fetch_profile_json_url, fetch_profile_json_id
from comparison import compare_df

# -------------- SETTINGS --------------
page_title = "Dataset Search"
title_icon = ":mag:"
dirname = os.path.dirname(__file__)
stelar_icon = os.path.join(dirname, 'icons/stelar_icon.jpg')
page_icon = stelar_icon
layout = "wide"

im = Image.open(page_icon)

st.set_page_config(page_title=page_title, page_icon=im, layout=layout)
st.title(page_title)
st.subheader('Keyword Search')

init_vars()
init_style()
    
button = search_bar()

comp_tab_title = "Comparison" 
if len(st.session_state.compared_ids) != 0:
    comp_tab_title += f" ({len(st.session_state.compared_ids)})"
if len(st.session_state.compared_ids) < 2:
    comp_tab_title = f':gray[{comp_tab_title}]'
tab_results, tab_comparison = st.tabs(["Results", comp_tab_title])

with tab_results:
    # Get Results from a successful response
    if st.session_state.cat_response is not None and st.session_state.cat_response.status_code == 200:
        json_response = st.session_state.cat_response.json()
        if json_response['success']:
            if button:
                st.session_state.results_df = modify_df(json_response['result']['results'])
                st.rerun()
            
            # print(json_response['result']['results'])
            
            # horizontal Facet List
            # update_button = facet_list()
            # if update_button: 
            #     st.session_state.results_df = modify_df(json_response['result']['results'])
            
            results_df = st.session_state.results_df
            
            if 'indices' in st.session_state:
                inds = st.session_state.indices
            else:
                inds = st.session_state.results_df.index
                
                
            results_df = results_df.loc[inds]
            
            columns = st.columns([2,3,1,1])
            columns[0].subheader(f"Found {results_df.shape[0]} results.")
            
            # rank_prefs = rank_select(columns[2])
            # print("Rank 1", rank_prefs)
            results_df = rank_select_2(results_df)
            # print("Rank 2", rank_prefs_2)
            results_df = sort_results(results_df, columns[3])
            
            result_btn(results_df)
            
            
        else:
            st.write("JSON Response Code 200 but Success bool is False")
    else:
        if st.session_state.cat_response is not None:
            st.write("JSON Response ", st.session_state.cat_response.text)

with tab_comparison:
    if len(st.session_state.compared_ids) >= 2:
        if st.session_state.cat_response is not None and st.session_state.cat_response.status_code == 200:
            json_response = st.session_state.cat_response.json()
            if json_response['success']:
                df = pd.DataFrame(json_response['result']['results']).set_index('id')
                df['profile_json_url'] = df.resources.apply(lambda x: fetch_profile_json_url(x))
                df['profile_json_id'] = df.resources.apply(lambda x: fetch_profile_json_id(x))
                df = df.loc[list(st.session_state.compared_ids)]
                compare_df(df)
    else:
        st.write('Please select at least two datasets for comparison.')
