# File for various functions
# Add functions, try not to change existing ones if possible

import json
import pandas as pd
import streamlit as st
import plotly.express as px
from streamlit_folium import st_folium
import geopandas as gpd
import folium
import sys
from datetime import datetime
from wordcloud import WordCloud
from collections import Counter
from shapely.geometry import box


def init_config(json_file):
    try:
        config_dict: dict = json.loads(json_file)
    except ValueError as e:
        with open(json_file) as f:
            config_dict: dict = json.load(f)

        st.session_state.config = config_dict


def init_vars():
    if 'config' not in st.session_state:
        init_config('../../config.json')

    if 'keywords' not in st.session_state:
        st.session_state.keywords = []

    if 'combined_keywords' not in st.session_state:
        st.session_state.combined_keywords = ''

    if 'compare_button_disabled' not in st.session_state:
        st.session_state.compare_button_disabled = True

    if 'results_df' not in st.session_state:
        st.session_state.results_df = None

    if 'cat_response' not in st.session_state:
        st.session_state.cat_response = None

    if 'compared_ids' not in st.session_state:
        st.session_state.compared_ids = set()

    if 'fields' not in st.session_state:
        st.session_state.fields = st.session_state.config['fields']

    if 'filterable' not in st.session_state:
        # st.session_state.filterable = set(st.session_state.config['fields']['filterable'])
        st.session_state.filterable = set(st.session_state.config['fields'].keys())

    if 'maps' not in st.session_state:
        st.session_state.maps = dict()

    if 'last_query' not in st.session_state:
        st.session_state.last_query = dict()

    if 'rankable' not in st.session_state:
        # st.session_state.rankable = set(st.session_state.config['fields']['rankable'])
        st.session_state.rankable = set([k for (k, [n, v]) in st.session_state.config['fields'].items() if
                                         v in ['CatMultiple', 'Spatial', 'DateSingle', 'DateRange', 'Numeric']])
        st.session_state.ranks = {k: True for k in st.session_state.rankable}


def init_style():
    hide_st_style = """
                <style>
                #the-title {text-align: center}
                #MainMenu {visibility: hidden;}
                footer {visibility: hidden;}
                header {visibility: hidden;}
                
                div.st-emotion-cache-18qywjq p{
                    font-size: 18px!important;
                }
                
                div.st-emotion-cache-s0hfy5 p {
                    text-shadow: 0 0 0 #5d36d3;
                    color: transparent;
                }          
                
                div[role="tabpanel"] iframe {
                    height: 500px;    
                }
                
                [data-testid="stSidebar"] {
                    display: none;
                }
                [data-testid="stSidebarNav"] {
                    display: none;
                }
                </style>
                """
    st.markdown(hide_st_style, unsafe_allow_html=True)


def fetch_profile_json_url(resources):
    profile_json_url = None
    for res in resources:
        if 'resource_type' in res and res['resource_type'] != 'other':
            profile_json_url = res['url']
            break
    return profile_json_url


def fetch_profile_json_id(resources):
    profile_json_id = None
    for res in resources:
        if 'resource_type' in res and res['resource_type'] != 'other':
            profile_json_id = res['id']
            break
    return profile_json_id


def modify_df(results):
    results_df = pd.DataFrame(results)
    if results_df.empty:
        return results_df

    # keys = set(["theme", "language", "license", "dataset_type", "format",
    #             "provider_name", "spatial", "temporal_start", "temporal_end",
    #             "num_rows", "days_active", "velocity"])
    keys = st.session_state.fields.keys() | set(["temporal_start", "temporal_end"])
    
    original_cols = ['id', 'isopen', 'private', 'metadata_modified', 'notes', 'title', 'score', 'partial_scores']
    keys = keys - set(original_cols)
    
    # print(keys)

    # print(results_df['profile'])
    # Add Fields from Extras
    fields = results_df['extras'] + results_df['profile']
    # print(fields)
    fields = fields.apply(lambda x: {xx['key']: xx['value'] for xx in x
                                     if xx['key'] in keys}).values
    # print(fields)
    fields = pd.DataFrame(list(fields))
    # print(fields.columns)
    # extras = pd.DataFrame(list(results_df['extras'].apply(lambda x: {xx['key']: xx['value'] for xx in x
    # if xx['key'] in keys}).values))
    for key in keys:  # add missing columns with None values to work with facets
        if key not in fields.columns:
            fields[key] = None

    for field in ["language", "theme"]:
        fields[field] = fields[field].apply(lambda x: json.loads(x) if not pd.isna(x) else [])

    # # Add Fields from Profile
    # profile = pd.DataFrame(list(results_df['profile'].apply(lambda x: {xx['key']: xx['value'] for xx in x
    #                                                                  if xx['key'] in keys}).values))
    # for key in keys: # add missing columns with None values to work with facets
    #     if key not in profile.columns:
    #         profile[key] = None
    # print(profile)

    results_df2 = results_df[original_cols].copy()
    results_df2 = pd.concat([results_df2, fields], axis=1)
    # print(results_df.shape, results_df2.shape)
    CKAN_URL = st.session_state.config['connect']['CKAN_URL']
    results_df2['link'] = results_df.name.apply(lambda x: CKAN_URL + 'dataset/' + x)
    results_df2['organization'] = results_df.organization.apply(lambda x: x['title'])
    results_df2['profile_json_url'] = results_df.resources.apply(lambda x: fetch_profile_json_url(x))
    results_df2['profile_json_id'] = results_df.resources.apply(lambda x: fetch_profile_json_id(x))
    # print(results_df2['profile_json_id'])
    # print(results_df2['organization'])
    # results_df2['tags'] = results_df.tags.apply(lambda x: [xx['display_name'] for xx in x])
    results_df2['metadata_modified'] = pd.to_datetime(results_df2['metadata_modified'])

    # results_df2['score'] = np.random.randint(1, 100, results_df2.shape[0])/100
    results_df2 = results_df2.set_index('id', drop=False)

    # print(results_df2)
    # print(results_df2.columns)
    # print(results_df2.head(5).T)

    return results_df2


def dates_line_plot(title: str, df: pd.DataFrame, date_column='Date'):
    st.subheader(title)
    dataset_ids = list(df.columns)
    fig1 = px.line(df, x=date_column, y=dataset_ids,
                   title='', markers=True, hover_data={'value': False},
                   color_discrete_sequence=px.colors.qualitative.Alphabet)

    colors = {trace.legendgroup: trace.line["color"] for trace in fig1.data}
    fig1.update_traces(line=dict(width=4))
    fig1.update_yaxes(showticklabels=False, title='')
    fig1.for_each_trace(lambda t: t.update(hovertemplate=t.hovertemplate.replace('variable', 'Dataset')))
    fig1.update_layout(legend_title_text='Dataset')
    fig1.update_layout(legend=dict(orientation="v", yanchor="bottom", y=-1, xanchor="left", x=0))
    st.plotly_chart(fig1, use_container_width=True)

    return colors


def all_in_map(title: str, shapes: dict, titles: dict, colors: dict):
    st.subheader(title)
    # data = dict(dataset=titles.values(), color=colors.values, geometry=shapes.values())
    # gdf = gpd.GeoDataFrame(data, crs="EPSG:4326")

    gdf = gpd.GeoDataFrame({}, geometry=list(shapes.values()).copy(), crs="EPSG:4326")
    centroid = gdf.dissolve().centroid
    # minx, miny, maxx, maxy = gdf.total_bounds
    # bb = box(minx, miny, maxx, maxy)
    lon = centroid.x
    lat = centroid.y
    m_all = folium.Map(location=[lat, lon], tiles='OpenStreetMap', max_bounds=True, min_zoom=1, zoom_start=5)

    for index, polygon in shapes.items():
        color = colors[titles[index]]
        feat = folium.GeoJson(data=polygon, name=titles[index],
                              tooltip='Dataset: ' + titles[index], color=colors[titles[index]])
        feat.add_to(m_all)

    folium.LayerControl().add_to(m_all)
    # m_all.fit_bounds(([bb.bounds[1], bb.bounds[0]], [bb.bounds[3], bb.bounds[2]]))
    st.session_state.maps['all'] = m_all
    st_folium(st.session_state.maps['all'],
              key=str(datetime.now()) + 'all',
              use_container_width=True, returned_objects=[])


def generate_wordcloud(title: str, wordcloud_list: list):
    st.subheader(title)
    wordcloud_dict = Counter(wordcloud_list)
    words = WordCloud().fit_words(wordcloud_dict)

    st.image(words.to_array(), use_column_width="never", width=800)


def generate_hist(title: str, x_list: list, x_title: str, y_list: list, y_title: str, colors: dict):
    st.subheader(title)
    df = pd.DataFrame({x_title: x_list, y_title: y_list}, columns=[x_title, y_title])
    df['color'] = df[x_title].map(colors)
    fig = px.bar(df, x=x_title, y=y_title, color='color',
                 color_discrete_sequence=px.colors.qualitative.Alphabet)
    fig.update_layout(xaxis_type='category', showlegend=False)

    st.plotly_chart(fig, use_container_width=True)
