# File for comparison of datasets
# Mostly Panos
import streamlit as st
import pandas as pd
import ast
import json
import folium
from streamlit_folium import st_folium
from shapely.geometry import shape
from datetime import datetime
import sys
import dateutil.parser as parser
from utils import dates_line_plot, all_in_map, generate_wordcloud, generate_hist
from geopandas import GeoSeries

def _numOfDays(date1, date2):
    # check which date is greater to avoid days output in -ve number
    if date2 > date1:
        return (date2 - date1).days
    else:
        return (date1 - date2).days


def compare_df(df):
#    print(df.head(5))
    individual_tab, collective_tab = st.tabs(['Individual', 'Collective'])

    histogram_values = ['daterange']
    wordcloud_values = ['keywords']

    histogram_values_dict = dict()
    for value in histogram_values:
        histogram_values_dict[value] = list()

    wordcloud_values_dict = dict()
    for value in wordcloud_values:
        wordcloud_values_dict[value] = list()

    comparison_df = pd.DataFrame(index=['Title', 'Organization Name', 'id', 'Start Date', 'End Date',
                                        'Date Range', 'Themes', 'Languages', 'License', 'Number of rows',
                                        'Keywords', 'Open?', 'Profile'])
    with individual_tab:
        df_container = st.container()
        st.divider()
    CKAN_URL = st.session_state.config['connect']['CKAN_URL']
    pos = 1

    n_rows = 2
    n_cols = len(df)
    with individual_tab:
        rows = [st.container() for _ in range(n_rows)]
        cols_per_row = [r.columns(n_cols) for r in rows]
        cols = [column for row in cols_per_row for column in row]

    all_dates_df = None
    datasets = list()
    titles = dict()
    buttons = dict()
    polygon_dict = dict()

    for ind in df.index:
        dataset_column = []
        title_link = f'<a target="_blank" href="{CKAN_URL}dataset/{df["name"][ind]}">{df["title"][ind]}</a>'

        dataset_column.append(title_link)
        dataset_column.append(df['organization'][ind]['name'])
        dataset_column.append(df.index[pos - 1])

        titles[ind] = df["title"][ind]

        if 'extras' in df:
            list_to_dict = {value['key']: value['value']
                            for value in df['extras'][ind]}

            # spatial
            geometry = 'yes'
            if 'spatial' in list_to_dict:
                gjson = json.loads(list_to_dict['spatial'])
                geom = shape(gjson)
                if geom.is_empty:
                    geometry = 'None'
                else:
                    geo_series = GeoSeries(geom)
                    centroid = geo_series.centroid
                    lon = centroid.x
                    lat = centroid.y
                    m = folium.Map(location=[lat, lon], tiles='OpenStreetMap', min_zoom=1, max_bounds=True, zoom_start=5)
                    geo_json = folium.GeoJson(data=geom, style_function=lambda x: {"fillColor": "orange"})
                    geo_json.add_to(m)
                    m.fit_bounds(geo_json.get_bounds())

                    st.session_state.maps[df.index[pos - 1]] = m
                    polygon_dict[df.index[pos - 1]] = geom
            else:
                geometry = 'None'
            with cols[pos - 1]:
                st.write(df["title"][ind])
            if geometry != 'None':
                with cols[pos - 1 + n_cols]:
                    st_folium(st.session_state.maps[df.index[pos - 1]],
                              key=str(datetime.now()),
                              use_container_width=True, returned_objects=[])
            else:
                with cols[pos - 1 + n_cols]:
                    st.write('\n\n\nNo Spatial Element')

            # Dates

            if 'temporal_start' in list_to_dict:
                temporal_start = parser.parse(list_to_dict['temporal_start']).date()
            else:
                temporal_start = datetime.strptime('1970-01-01', '%Y-%m-%d').date()

            if 'temporal_end' in list_to_dict:
                temporal_end = parser.parse(list_to_dict['temporal_end']).date()
            else:
                temporal_end = datetime.today().date()

            dataset_column.append(temporal_start)
            dataset_column.append(temporal_end)
            daterange = _numOfDays(temporal_start, temporal_end)
            histogram_values_dict['daterange'].append(daterange)
            datasets.append(titles[ind])
            dataset_column.append(str(daterange) + " days")

            dates_df = pd.DataFrame([[temporal_start, pos], [temporal_end, pos]], columns=['Date', df["title"][ind]])

            if all_dates_df is None:
                all_dates_df = dates_df
            else:
                all_dates_df = pd.merge(all_dates_df, dates_df, on='Date', how='outer')

            # theme
            if 'theme' in list_to_dict:
                dataset_themes = ast.literal_eval(list_to_dict['theme'])
            else:
                dataset_themes = ['None']
            dataset_column.append(dataset_themes)

            # language
            if 'language' in list_to_dict:
                dataset_languages = ast.literal_eval(list_to_dict['language'])
            else:
                dataset_languages = ['None']
            dataset_column.append(dataset_languages)

            # license
            if 'license' in list_to_dict:
                license = list_to_dict['license']
            else:
                license = 'None'
            dataset_column.append(license)

            # Number of rows
            if 'num_rows' in list_to_dict:
                num_rows = list_to_dict['num_rows']
            else:
                num_rows = None

            dataset_column.append(num_rows)
        else:
            for i in range(7):
                dataset_column.append(None)

        # Keywords
        if 'tags' in df and df['tags'] is not None:
            tags_display_names = []
            for value in df['tags'][ind]:
                tags_display_names.append(value['display_name'].lower())

            dataset_column.append(tags_display_names)
            wordcloud_values_dict['keywords'].extend(tags_display_names)

        else:
            dataset_column.append(None)

        # is_open?
        if 'isopen' in df:
            is_open = df['isopen'][ind]

        else:
            is_open = None

        dataset_column.append(is_open)

        # profile
        if 'profile_json_id' in df and df['profile_json_id'][ind] is not None and df['profile_json_url'][ind].endswith(
                '.json'):
            # Create the button with the link
            details = st.session_state.config

            connect = details['connect']
            KLMS_API = connect['KLMS_API']
            API_KEY = connect['API_KEY']
            resource_id = df['profile_json_id'][ind]
            button = f"""<a href='/profiler_app?package_id={ind}&resource_id={str(df['profile_json_id'][ind])}&title={titles[ind]}&KLMS_API={KLMS_API}&API_KEY={API_KEY}' target="_blank"><button id={ind}">View</button></a>"""
            dataset_column.append(button)
        else:
            dataset_column.append('No profile')

        pos += 1

        comparison_df[pos] = dataset_column

    with df_container:
        st.markdown(comparison_df.to_html(escape=False, header=False), unsafe_allow_html=True)

    if 'extras' in df:
        with collective_tab:
            if polygon_dict:
                cols_col = st.columns(2)
                with cols_col[0]:
                    colors = dates_line_plot('Dataset TimeSpan', all_dates_df)
                with cols_col[1]:
                    all_in_map('Spatial Coverage', polygon_dict, titles, colors)
            st.divider()

            # histogram(s)
            if len(histogram_values_dict) == 1:
                value = list(histogram_values_dict.keys())[0]
                generate_hist(value, datasets, 'datasets', histogram_values_dict[value], value, colors)
            elif len(histogram_values_dict) > 1:
                histogram_cols = st.columns(2)
                i = 0
                for value in histogram_values_dict:
                    with histogram_cols[i]:
                        generate_hist(value, datasets, 'datasets', histogram_values_dict[value], value, colors)
                    if i == 0:
                        i = 1
                    else:
                        i = 0
            st.divider()

            # wordcloud(s)
            if len(wordcloud_values_dict) == 1:
                value = list(wordcloud_values_dict.keys())[0]
                generate_wordcloud(value, wordcloud_values_dict[value])
            elif len(wordcloud_values_dict) > 1:
                wordcloud_cols = st.columns(2)
                i = 0
                for value in wordcloud_values_dict:
                    with wordcloud_cols[i]:
                        generate_wordcloud(value, wordcloud_values_dict[value])
                    if i == 0:
                        i = 1
                    else:
                        i = 0
