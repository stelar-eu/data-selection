# File for search bar
# Should not be changed until autocomplete scenario

import streamlit as st
from streamlit_tags import st_tags
import requests
from facets import facet_list
import os
import json
from collections import Counter
from datetime import date
from utils import modify_df

def update_results_df():
    json_response = st.session_state.cat_response.json()
    # st.session_state.compared_ids = set()
    # st.session_state.results_df = modify_df(json_response['result']['results'])    

def load_suggestions():
    details = st.session_state.config
    connect = details['connect']
    # URL to KLMS API
    KLMS_API = connect['KLMS_API']

    # Provide the API key required for requests regarding packages
    headers = {'Content-Type': 'application/json', 'Api-Token': connect['API_KEY']}
    
    cfile = '../../cache/tags.json'
    if os.path.exists(cfile):
        facet_response = json.load(open(cfile))
    else:
        os.makedirs(os.path.dirname(cfile), exist_ok=True)
        facet_response = requests.post(KLMS_API+details['commands']['values'],
                                   json= {"q": 'tags'}, headers=headers).json()  
        with open(cfile, 'w') as o:
            o.write(json.dumps(facet_response, indent=4))
    c = Counter()
    for res in facet_response:
        c.update(res['arr_values'])
    suggestions = [sug[0] for sug in c.most_common(1000)]
    return suggestions


def prepare_stored_facets(facets_widgets):
    #Prepare values
    total = {}
    for col, vals in facets_widgets.items():
        if vals is None:
            continue
        if type(vals) == list and len(vals) == 0: # no values for this facet (categorical)
            continue
        if type(vals) == str and len(vals) == 0: # no values for this facet (spatial)
            continue
        if type(vals) == tuple and len(vals) == 0: # no values for this facet (temporal)
            continue
        
        
        if type(vals) == list:
            vals = [val.split(' (')[0] for val in vals]
        if type(vals) == tuple:  #for RangeNumeric and Date
            vals = list(vals)
            if type(vals[0]) == date:
                # vals = [vals[0].strftime('%Y-%m-%d'), vals[1].strftime('%Y-%m-%d')]
                vals = [v.strftime('%Y-%m-%d') for v in vals]
        total[col] = vals
        
    options = [f'{k}: {v}' for k, v in total.items()]
    options = st.multiselect(label=' ', options=options, default=options)
    options = set([o.split(':')[0] for o in options])
    return options    


def make_query(facets_widgets, options, rankable, filterable, keywords):
    # st.session_state.keywords = keywords
    # st.session_state.combined_keywords = ','.join(keywords)

    facets = st.session_state.fields

    facet, rank, total = {}, {}, {}
    for col, vals in facets_widgets.items():
        if col not in options:
            continue
        
        # toRank = col in filterable
        # toFilter = col in rankable
        dtype = facets[col][1]
        
        toRank = col in rankable
        toFilter = col in filterable
        if dtype == 'Numeric':
            if type(vals) == float:  #only rank
                toFilter = False
            else:   #only filter
                vals = list(vals)
                toRank = False

        elif dtype == 'DateRange':
            if len(vals) == 1:  #only rank
                continue #error
            else:   #only filter
                vals = [v.strftime('%Y-%m-%d') for v in vals]

        elif dtype == 'DateSingle':
            if len(vals) == 1:  #only rank
                vals = vals[0].strftime('%Y-%m-%d')
                toFilter = False
            else:   #only filter
                vals = [v.strftime('%Y-%m-%d') for v in vals]
                toRank = False
                
        # if type(vals) == float: #singleNumeric -> only rank
            # toFilter = False
        # if type(vals) == tuple and type(vals[0]) == float: #rangeNumeric -> only filter
            # toRank = False
        else:
            if type(vals) == list:
                vals = [val.split(' (')[0] for val in vals]
        # if type(vals) == tuple:  #for RangeNumeric and Date
        #     vals = list(vals)
        #     if type(vals[0]) == date:
        #         if len(vals) == 2:
        #             vals = [v.strftime('%Y-%m-%d') for v in vals]
        # print(col, toRank, toFilter)
        if toFilter:
            facet[col] = vals
        if toRank:
            rank[col] = vals
        total[col] = vals

    search_criteria = {"keywords": keywords,
                       "filter_preferences": facet,
                       "rank_preferences": rank,
                       }    
    return search_criteria

def search_bar():
    
    filterable = st.session_state.filterable
    rankable = st.session_state.rankable
    
    search_bar, search_button = st.columns([0.95, 0.05])
    
    suggestions = load_suggestions()
    
    # Keyword Search
    with search_bar:
        keywords = st_tags(
            label='',
            text='Press enter to add more',
            suggestions=suggestions,
            maxtags=20,
            key="aljnf")
    
    with search_button:
        st.write('')
        button = st.button(':mag:', use_container_width=True)
        
    facets_widgets = facet_list()
    
    
    options = prepare_stored_facets(facets_widgets)
        
    if button:
        search_criteria = make_query(facets_widgets, options, rankable, filterable, keywords)
        
        print(search_criteria)

        details = st.session_state.config
        connect = details['connect']
        KLMS_API = connect['KLMS_API']
        API_KEY = connect['API_KEY']
    
        # Make a POST request to the KLMS API with the parameters
        commands = details['commands']
    
        st.session_state.last_rank_preferences = search_criteria['rank_preferences'].keys()
        total = {}
        for k, v in search_criteria['rank_preferences'].items():
            total[k] = v
        for k, v in search_criteria['filter_preferences'].items():
            total[k] = v            
        st.session_state.last_query = total
        
        

        headers = {'Content-Type': 'application/json', 'Api-Token': API_KEY}
        
        st.session_state.cat_response = requests.post(KLMS_API + commands['rank'], 
                                                      json=search_criteria, headers=headers)
        
        json_response = st.session_state.cat_response.json()
        st.session_state.compared_ids = set()
        st.session_state.results_df = modify_df(json_response['result']['results'])  
    return button
