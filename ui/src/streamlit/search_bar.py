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

def search_bar():
    
    filterable = st.session_state.filterable
    rankable = st.session_state.rankable
    
    search_bar, search_button = st.columns([0.95, 0.05])
    
    
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
    # print(suggestions)
    
    
    # Keyword Search
    with search_bar:
        keywords = st_tags(
            label='',
            text='Press enter to add more',
            value = ['LAI'],
            # value=['POI', 'Geospatial'],
            # suggestions=['POI', 'Geospatial(10)', 'Geospatial(200)', 'Landsat', 'Lakes&ext_bbox=20,35,30,42'],
            suggestions=suggestions,
            maxtags=20,
            key="aljnf")
    
    with search_button:
        st.write('')
        button = st.button(':mag:', use_container_width=True)
        
    facets_widgets = facet_list()
    
    
    #Prepare values
    total = {}
    for col, vals in facets_widgets.items():
        # print(col, vals)
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
    # print(options)
        
    if button:
        # st.session_state.keywords = keywords
        # st.session_state.combined_keywords = ','.join(keywords)
    
        facets = st.session_state.fields
    
        # KLMS API connection details
        details = st.session_state.config
    
        connect = details['connect']
        # URL to KLMS API
        KLMS_API = connect['KLMS_API']
    
        # API key generated for the user
        # IMPORTANT! This should be made available through Keycloak
        API_KEY = connect['API_KEY']
    
        # Provide the API key required for requests regarding packages
        headers = {'Content-Type': 'application/json', 'Api-Token': API_KEY}
    
        # Basic search request to the Data Catalog (CKAN)

        # #Prepare values
        # facet, rank = {}, {}
        # for col, vals in facets_widgets.items():
        #     # print(col, vals)
        #     if type(vals) == list and len(vals) == 0: # no values for this facet (categorical)
        #         continue
        #     if type(vals) == str and len(vals) == 0: # no values for this facet (spatial)
        #         continue
        #     if type(vals) == tuple and len(vals) == 0: # no values for this facet (temporal)
        #         continue
            
        #     if type(vals) == list:
        #         vals = [val.split(' (')[0] for val in vals]
        #     if type(vals) == tuple:  #for RangeNumeric and Date
        #         vals = list(vals)
        #         if type(vals[0]) == date:
        #             vals = [vals[0].strftime('%Y-%m-%d'), vals[1].strftime('%Y-%m-%d')]
        #     if col in filterable:
        #         facet[col] = vals
        #     if col in rankable:
        #         rank[col] = vals  
        
        facet, rank, total = {}, {}, {}
        for col, vals in facets_widgets.items():
            # print(col, col in options)
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
        
        print(search_criteria)
    
        # Make a POST request to the KLMS API with the parameters
        commands = details['commands']
    
        st.session_state.last_rank_preferences = rank.keys()
        st.session_state.last_query = total
        st.session_state.cat_response = requests.post(KLMS_API + commands['rank'], 
                                                      json=search_criteria, headers=headers)
        # print(st.session_state.cat_response.status_code)
        # print(len(st.session_state.cat_response.json()['result']['results']))        
        # print(st.session_state.cat_response.json()['result']['results'])
    return button
