# File for visualization of results and sorting
# Mostly Alex

import streamlit as st
#from streamlit_modal import Modal
import streamlit.components.v1 as components
from ranking import split_partial_results_to_lists, combined_ranking

def result_btn(df):
    for index, row in df.iterrows():
        st2 = st.container(height=None, border=2)
        with st2:
            col1, col2, col3 = st2.columns([0.90, 0.05, 0.05])

            add_content(row, col1)
            
            col2.link_button(':globe_with_meridians:', row['link'], use_container_width=True, help='Visit Catalog')
            
            if row['id'] not in st.session_state.compared_ids:
                # cmp_btn = col3.button(':white_check_mark:', use_container_width=True, key=row['id'], help='Compare')
                # cmp_btn = col3.button(':shopping_trolley:', use_container_width=True, key=row['id'], help='Compare')
                cmp_btn = col3.button(':heavy_plus_sign:', use_container_width=True, key=row['id'], help='Add')
                if cmp_btn:
                    st.session_state.compared_ids.add(row['id'])
            else:
                cmp_btn = col3.button(':x:', use_container_width=True, key=row['id'], help='Remove')
                # cmp_btn = col3.button(':wastebasket:', use_container_width=True, key=row['id'], help='Remove')
                if cmp_btn:
                    st.session_state.compared_ids.remove(row['id'])
                    
def add_content(row, comp):
    if row['private']:
        title = row['title'] + ' :lock:'  
    else:
        title = row['title'] + ' :unlock:'
    exp = comp.expander(title)
    exp.divider()
    exp.write(row['notes'])
    exp.write('Score: {:.2f}'.format(row['score']))
    
    part_scores = row['partial_scores']
    part_cols = exp.columns(len(part_scores)+1)
    part_cols[0].write('Partial Scores: ')
    for no, (col, val) in enumerate(part_scores.items()):
        part_cols[no+1].write('{}: {:.2f}'.format(col, float(val)))
        
    exp.divider()
    c1, c2 = exp.columns(2)
    c1.write('Provider: {}'.format(row['provider_name']))
    c2.write('Date Modified: {}'.format(row['metadata_modified']))        
                    
def sort_results(df, comp):
    sort_options = ['Score Descending', 'Score Ascending',
                    'Title Descending', 'Title Ascending',
                    'Date Descending', 'Date Ascending',
                    ]
    sort_option = comp.selectbox(' ', sort_options, index=0, label_visibility='hidden')
    
    fields = {'title': 'title', 'date': 'metadata_modified', 'score': 'score'}
    
    field, asc = sort_option.lower().split(' ')
    asc = asc == 'ascending'
    field = fields[field]
    
    if df.empty:
        return df
    return df.sort_values(field, ascending=asc)

'''
def rank_select(comp):
    modal = Modal("Select Ranking attributes",  key="rank_modal",
                  padding=20, max_width=744)
    open_modal = comp.button(":gear:")
    if open_modal:
        modal.open()
    
    if modal.is_open():
        with modal.container():
            # st.write("Text goes here")
            
            for field_name, field_val in st.session_state.ranks.items():
                field_label = st.session_state.fields[field_name][0]
                st.session_state.ranks[field_name] = st.checkbox(field_label, value=field_val)
    else:
        ranks = set([k for k,v in st.session_state.ranks.items() if v])
        # print(ranks)
        df = st.session_state.results_df
        if df is not None:
            if df.empty or len(df.iloc[0]['partial_scores']) < 2: #less than 2 fields, no need for ranking
                return
            
            partial_results = []
            for index, row in df.iterrows():
                partial_results.append({'id': row['id'], 
                                  'partial_scores': {k: v for k,v in row['partial_scores'].items() if k in ranks}})
            # print(partial_results)
            res = split_partial_results_to_lists(partial_results)
            rank_settings = { 
                    "k": df.shape[0],  # number of results
                    "algorithm":"Bordafuse"  #options: "CombMIN","CombMED","CombANZ","CombMAX","CombSUM","CombMNZ","Log_ISR","Bordafuse","Condorcet","ISR","Bordacount","MRA"
                    }
            # print(res)
            final_results = combined_ranking(res, rank_settings)
            final_results = final_results['score'].to_dict()
            
            for index, row in df.iterrows():
                # row['score'] = final_results[row['id']]
                df.loc[index, 'score'] = final_results[row['id']]
        
        # print(st.session_state.ranks)
'''
        
def rank_select_2(df):
    exp = st.expander('Ranking')
    # print(st.session_state.ranks)
	
	# Allow user to choose the rank aggregation method
    rank_options = st.session_state.config['ranking']['methods'] #['Bordafuse','Bordacount','MRA','CombMIN','CombMED','CombANZ','CombMAX','CombSUM','CombMNZ','ISR','Log_ISR','Condorcet',]
    rank_option = exp.selectbox(' ', rank_options, index=0, label_visibility='hidden')
    print(rank_option)
	
    cols = exp.columns(len(st.session_state.ranks)+1)
    # print(st.session_state.results_df.iloc[0]['partial_scores'])
    #rank_fields = st.session_state.results_df.iloc[0]['partial_scores'].keys()
    rank_fields = st.session_state.last_rank_preferences
    # print(st.session_state.last_rank_preferences)
    
    # print(rank_fields)
    for no, (field_name, field_val) in enumerate(st.session_state.ranks.items()):
        field_label = st.session_state.fields[field_name][0]
        st.session_state.ranks[field_name] = cols[no].checkbox(field_label, value=field_val,
                                                               disabled=field_name not in rank_fields)
        # print(field_name in rank_fields)
    button = cols[len(cols)-1].button('Rerank')
    if button:
        # print('Clicked!')
        st.session_state.rank_algorithm = rank_option
        #ranks = set([k for k,v in st.session_state.ranks.items() if v])
        ranks = st.session_state.last_rank_preferences
        # print(ranks)
        # df = st.session_state.results_df
        # print(df is None)
        if df is not None:
            # print(df.iloc[0]['partial_scores'])
            #if df.empty or len(df.iloc[0]['partial_scores']) < 2: #less than 2 fields, no need for ranking
            if df.empty or len(ranks) < 2: #less than 2 fields, no need for ranking
                return
            
            partial_results = []
            for index, row in df.iterrows():
                partial_results.append({'id': row['id'], 
                                        'partial_scores': {k: v for k,v in row['partial_scores'].items() if k in ranks}})
            # print(partial_results)
            res = split_partial_results_to_lists(partial_results)
            rank_settings = { 
                    "k": df.shape[0],  # number of results
                    "algorithm": rank_option #"Bordafuse"  #options: "CombMIN","CombMED","CombANZ","CombMAX","CombSUM","CombMNZ","Log_ISR","Bordafuse","Condorcet","ISR","Bordacount","MRA"
                    }
            # print(res)
            final_results = combined_ranking(res, rank_settings)
            final_results = final_results['score'].to_dict()
            
            for index, row in df.iterrows():
                # row['score'] = final_results[row['id']]
                df.loc[index, 'score'] = final_results[row['id']]        
    return df
