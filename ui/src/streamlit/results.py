# File for visualization of results and sorting
# Mostly Alex

import streamlit as st
#from streamlit_modal import Modal
import streamlit.components.v1 as components
from ranking import split_partial_results_to_lists, combined_ranking

def update_cmp(key):
    if key not in st.session_state.compared_ids:
        st.session_state.compared_ids.add(key)
    else:
        st.session_state.compared_ids.remove(key)


def sort_df(df, key):
    sort_option = st.session_state[key]
    fields = {'title': 'title', 'date': 'metadata_modified', 'score': 'score'}
    
    field, asc = sort_option.lower().split(' ')
    asc = asc == 'ascending'
    field = fields[field]
    
    # df = st.session_state.results_df
    if df.empty:
        return
    # st.session_state.results_df = df.sort_values(field, ascending=asc)    
    df = df.sort_values(field, ascending=asc)    
    return df

def result_btn():
    df = st.session_state.results_df
    if df is None:
        return
    df = sort_df(df, 'sort_option')
    
    for index, row in df.iterrows():
        st2 = st.container(height=None, border=2)
        with st2:
            # col0, col1, col2, col3 = st2.columns([0.05, 0.85, 0.05, 0.05])
            # col0.checkbox('', value=False, key='cmp_'+row['id'], on_change=update_cmp, args=('cmp_'+row['id'], row['id'], ))

            col1, col2, col3 = st2.columns([0.90, 0.05, 0.05])

            add_content(row, col1)
            
            col2.link_button(':globe_with_meridians:', row['link'], use_container_width=True, help='Visit Catalog')
            
            if row['id'] not in st.session_state.compared_ids:
                cmp_btn = col3.button(':heavy_plus_sign:', use_container_width=True, key=row['id'], help='Add',
                                      on_click=update_cmp, args=(row['id'], ))
            else:
                cmp_btn = col3.button(':x:', use_container_width=True, key=row['id'], help='Remove',
                                      on_click=update_cmp, args=(row['id'], ))
                    
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
      
def sort_results(comp):
    sort_options = ['Score Descending', 'Score Ascending',
                    'Title Descending', 'Title Ascending',
                    'Date Descending', 'Date Ascending',
                    ]
    comp.selectbox(' ', sort_options, index=0, label_visibility='hidden', 
                   key='sort_option',)
                   # on_change=sort_df, key='sort_option',
                   # args=('sort_option', ))

        
def rank_results(df, algorithm, rank_active_fields, weights={}):
    # ranks = st.session_state.last_rank_preferences
    ranks = rank_active_fields
    if df is  None:
        return df
    
    if df.empty or len(ranks) < 2: #less than 2 fields, no need for ranking
        return df
    
    partial_results = []
    for index, row in df.iterrows():
        partial_results.append({'id': row['id'], 
                                'partial_scores': {k: v for k,v in row['partial_scores'].items() if k in ranks}})
    # print(ranks)
    res = split_partial_results_to_lists(partial_results)
    #TODO: utilize weights
    rank_settings = { 
            "k": df.shape[0],  # number of results
            "algorithm": algorithm 
            }
    final_results = combined_ranking(res, rank_settings)
    final_results = final_results['score'].to_dict()
    
    for index, row in df.iterrows():
        # row['score'] = final_results[row['id']]
        df.loc[index, 'score'] = final_results[row['id']]     
    return df

def rank_select():
    exp = st.expander('Ranking')
	
	# Allow user to choose the rank aggregation method
    rank_options = st.session_state.config['ranking']['methods'] #['Bordafuse','Bordacount','MRA','CombMIN','CombMED','CombANZ','CombMAX','CombSUM','CombMNZ','ISR','Log_ISR','Condorcet',]
    rank_option = exp.selectbox(' ', rank_options, index=0, label_visibility='hidden', on_change=None)
    # print(rank_option)
	
    cols = exp.columns(len(st.session_state.ranks)+1)
    rank_fields = st.session_state.last_rank_preferences
    weights = {}
    
    for no, (field_name, field_val) in enumerate(st.session_state.ranks.items()):
        disabled = field_name not in rank_fields
        value = field_val if not disabled else False
        field_label = st.session_state.fields[field_name][0]
        st.session_state.ranks[field_name] = cols[no].checkbox(field_label, value=value,
                                                               disabled=disabled)
        
        if rank_option in ['Bordacount'] and not disabled:  #TODO: Change to threshold
            weights[field_name] = cols[no].number_input('Weight', min_value=0.0, max_value=1.0, 
                                                        value=0.5, step=None, key=field_name+'_weight')
    print("Weights: ", weights)
    button = cols[-1].button('Rerank')
    if button:
        print('Rerank button clicked!')
        rank_active_fields = set([k for k, v in st.session_state.ranks.items() if v])
        st.session_state.rank_algorithm = rank_option
        st.session_state.results_df = rank_results(st.session_state.results_df, rank_option, 
                                                   rank_active_fields, weights)
        # sort_df('sort_option')
