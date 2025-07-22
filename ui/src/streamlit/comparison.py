# File for comparison of datasets
# Mostly Panos
import streamlit as st
import pandas as pd
import numpy as np
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
import ast


def _numOfDays(date1, date2):
    # check which date is greater to avoid days output in -ve number
    if date2 > date1:
        return (date2 - date1).days
    else:
        return (date1 - date2).days


def compare_df(df):
    individual_tab, collective_tab = st.tabs(['Individual', 'Collective'])

    # columns
    fields = st.session_state.fields
    field_cols = fields.keys()

    original_cols = ['title', 'id', 'organization', 
                     # 'isopen', 
                     'private', 'tags',
                     'metadata_modified', 'temporal_start', 'temporal_end', 'license_title']

    original_cols.extend(field_cols)

    cols = list(dict.fromkeys(original_cols))
    cols.append('profile')
    # Titles of columns
    titles_list = []
    field_types_dict = dict()
    field_names_dict = dict()

    titles_list.extend(['Title', 'Id', 'Organization',
                        # 'Open', 
                        'Private', 'Keywords',
                        'Metadata Modified', 'Temporal Start', 'Temporal End', 'License Title'])

    for key in field_cols:
        titles_list.append(fields[key][0])
        field_names_dict[key] = fields[key][0]
        field_types_dict[key] = fields[key][1]

    titles_list = list(dict.fromkeys(titles_list))
    titles_list.append('Profile')
    # Minus temporal_start and temporal_end
    n_rows = len(titles_list) - 2
    pos = 1
    n_columns, _ = df.shape
    with individual_tab:
        rows = [st.container(border=True) for _ in range(n_rows)]
        cols_per_row = [r.columns(n_columns + 1) for r in rows]
        columns = [column for row in cols_per_row for column in row]

    cols_dict = dict()

    one_down = 0
    for title in titles_list:
        if title not in ['Temporal Start', 'Temporal End']:
            with columns[pos - 1 + one_down]:
                st.write(title)
            one_down += n_columns + 1

    # CKAN_URL = st.session_state.config['connect']['CKAN_URL']
    KLMS_URL = st.session_state.config['connect']['KLMS_URL']

    # initialize dictionaries for collective_tab

    # Dataset titles used in plots
    datasets = list()
    titles = dict()

    # Spacial
    spatial_dict = dict()

    # DateRange
    all_dates_dict_of_dfs = dict()

    # Numeric
    histogram_dict = dict()

    # CatMultiple + check len of set greater than 1
    wordcloud_dict = dict()

    for ind in df.index:
        jump = 0
        temporal_start = ''
        temporal_end = ''
        temporal_extend = []
        temporal_extend_days = None
        for col in cols:
            if col == 'title':
                datasets.append(df["title"][ind])
                titles[ind] = df["title"][ind]
                with columns[pos]:
                    title_link = f'<a target="_blank" href="{df["link"][ind]}">{df["title"][ind]}</a>'
                    st.write(title_link, unsafe_allow_html=True)
            elif col == 'id':
                with columns[pos + jump]:
                    st.write(ind)
            elif col == 'organization':
                with columns[pos + jump]:
                    # organization_dict = df['organization_dict'][ind]
                    # if organization_dict is not None:
                    #     organization_title = organization_dict['title']
                    #     organization_name = organization_dict['name']

                    #     link = KLMS_URL + 'organization/' + organization_name
                    #     organization_link = f'<a target="_blank" href="{link}">{organization_title}</a>'
                    #     st.write(organization_link, unsafe_allow_html=True)
                    # else:
                    #     st.write(f":red[{None}]")
                    organization = df['organization'][ind]
                    st.write(organization)
            elif col == 'isopen':
                with columns[pos + jump]:
                    if not df['isopen'][ind]:
                        st.write(f":red[{df['isopen'][ind]}]")
                    else:
                        st.write(f":green[{df['isopen'][ind]}]")
            elif col == 'private':
                with columns[pos + jump]:
                    if not df['private'][ind]:
                        st.write(f":red[{df['private'][ind]}]")
                    else:
                        st.write(f":green[{df['private'][ind]}]")
            elif col == 'tags':
                with columns[pos + jump]:
                    tags_display_names = []
                    for value in df['tags'][ind]:
                        # tags_display_names.append(value['display_name'].lower())
                        tags_display_names.append(value.lower())

                    # add it in catmultiple dict
                    if 'Keywords' not in wordcloud_dict:
                        wordcloud_dict['Keywords'] = list()

                    wordcloud_dict['Keywords'].extend(tags_display_names)
                    s = ''
                    for i in tags_display_names:
                        s += "- " + i + "\n"

                    if s == '':
                        st.write(f":red[{None}]")
                    else:
                        st.write(s)
            elif col == 'metadata_modified':
                with columns[pos + jump]:
                    if df['metadata_modified'][ind] is None:
                        st.write(f":red[{None}]")
                    else:
                        st.write(f":green[{df['metadata_modified'][ind]}]")
            elif col == 'temporal_start':
                if df['temporal_start'][ind] not in [' ', 'None', None, 'nan'] and not pd.isna(
                        df['temporal_start'][ind]):
                    temporal_start = parser.parse(df['temporal_start'][ind]).date()
                else:
                    temporal_start = datetime.strptime('1975-03-15', '%Y-%m-%d').date()

                # Do not write temporal_start
                # with columns[pos + jump]:
                #     if temporal_start is None:
                #         st.write(f":red[{None}]")
                #     else:
                #         st.write(f":green[{temporal_start}]")

                # we jump backwards as we do not write temporal_start
                jump -= (n_columns + 1)

            elif col == 'temporal_end':
                if df['temporal_end'][ind] not in [' ', 'None', None, 'nan'] and not pd.isna(
                        df['temporal_end'][ind]):
                    temporal_end = parser.parse(df['temporal_end'][ind]).date()
                else:
                    temporal_end = datetime.today().date()

                # Do not write temporal_end
                # with columns[pos + jump]:
                #     if temporal_end is None:
                #         st.write(f":red[{None}]")
                #     else:
                #         st.write(f":green[{temporal_end}]")

                # we jump backwards as we do not write temporal_end
                jump -= (n_columns + 1)

            elif col == 'license_title':
                with columns[pos + jump]:
                    if df['license_title'][ind] is None:
                        st.write(f":red[{None}]")
                    else:
                        st.write(df['license_title'][ind])
            elif col == 'profile':
                possible_profiles = df['profile_dict'][ind]
                if len(possible_profiles) == 0:
                    with columns[pos + jump]:
                        st.write(f":red[No Profile]")
                else:
                    count_profiles = 0
                    for profile in possible_profiles:
                        if profile['format'] == 'JSON' and profile['url'].endswith('.json') and 'profile' in profile['name'].lower():
                            count_profiles += 1
                            # Create the button with the link
                            details = st.session_state.config

                            connect = details['connect']
                            KLMS_API = connect['KLMS_API']
                            API_KEY = connect['API_KEY']
                            resource_id = profile['id']
                            with columns[pos + jump]:
                                st.link_button(profile['name'],
                                               f"/profiler_app?package_id={ind}&resource_id={resource_id}"
                                               f"&title={df['title'][ind]}&KLMS_API={KLMS_API}&API_KEY={API_KEY}",
                                               use_container_width=True)
                        elif profile['format'] == 'HTML':
                            count_profiles += 1
                            url = profile['url']
                            name = profile['name']
                            resource_id = profile['id']
                            link = f'''<a target="_blank" href="{url}"><button id={resource_id}">{name}</button></a>'''
                            with columns[pos + jump]:
                                st.link_button(name, url, use_container_width=True)

                    if count_profiles == 0:
                        with columns[pos + jump]:
                            st.write(f":red[No Profile]")
            else:
                # TODO: add DateRange type
                if col == 'temporal_extent':
                    temporal_extend.append(str(temporal_start))
                    temporal_extend.append(str(temporal_end))
                    temporal_extend_days = _numOfDays(temporal_start, temporal_end)
                    name = field_names_dict[col] + str(' (Number of Days)')
                    # Don't plot Temporal Extent
                    #
                    # if name not in histogram_dict:
                    #     histogram_dict[name] = list()
                    # histogram_dict[name].append(temporal_extend_days)
                    # for timeline plot
                    dates_df = pd.DataFrame([[temporal_start, pos], [temporal_end, pos]],
                                            columns=['Date', df["title"][ind]])

                    if name not in all_dates_dict_of_dfs:
                        all_dates_dict_of_dfs[name] = dates_df
                    else:
                        all_dates_dict_of_dfs[name] = pd.merge(all_dates_dict_of_dfs[name],
                                                               dates_df, on='Date', how='outer')

                    with columns[pos + jump]:
                        s = temporal_extend[0] + ' - ' + temporal_extend[1]
                        st.write(s)
                else:
                    chosen_col_name = field_names_dict[col]
                    chosen_col_type = field_types_dict[col]

                    if chosen_col_type == 'CatSingle':
                        with columns[pos + jump]:
                            if pd.isna(df[col][ind]):
                                st.write(f":red[{None}]")
                            else:
                                st.write(df[col][ind])
                    elif chosen_col_type == 'CatMultiple':
                        display_names = []
                        vals = ast.literal_eval(df[col][ind])
                        for value in vals:
                            display_names.append(value.lower())

                        if field_names_dict[col] not in wordcloud_dict:
                            wordcloud_dict[field_names_dict[col]] = list()

                        wordcloud_dict[field_names_dict[col]].extend(display_names)
                        # add it in catmultiple dict
                        with columns[pos + jump]:
                            s = ''
                            for i in display_names:
                                s += "- " + i + "\n"
                            if s == '':
                                st.write(f":red[{None}]")
                            else:
                                st.write(s)

                    elif chosen_col_type == 'Numeric':
                        if field_names_dict[col] not in histogram_dict:
                            histogram_dict[field_names_dict[col]] = list()
                        with columns[pos + jump]:
                            if pd.isna(df[col][ind]):
                                st.write(f":red[{None}]")
                                histogram_dict[field_names_dict[col]].append(np.nan)
                            else:
                                st.write(df[col][ind])
                                histogram_dict[field_names_dict[col]].append(ast.literal_eval((df[col][ind])))

                            # add to histogram
                    elif chosen_col_type == 'Spatial':
                        if not pd.isna(df[col][ind]):
                            # gjson = json.loads(df[col][ind])
                            gjson = df[col][ind]
                            geom = shape(gjson)
                            if geom.is_empty:
                                geometry = 'None'
                                with columns[pos + jump]:
                                    st.write(f":red[{None}]")
                            else:
                                geo_series = GeoSeries(geom)
                                centroid = geo_series.centroid
                                lon = centroid.x
                                lat = centroid.y
                                m = folium.Map(location=[lat, lon], tiles='OpenStreetMap', height=300, min_zoom=1,
                                               max_bounds=True,
                                               zoom_start=5)
                                geo_json = folium.GeoJson(data=geom, style_function=lambda x: {"fillColor": "orange"})
                                geo_json.add_to(m)
                                m.fit_bounds(geo_json.get_bounds())

                                if field_names_dict[col] not in spatial_dict:
                                    spatial_dict[field_names_dict[col]] = dict()

                                spatial_dict[field_names_dict[col]][ind] = geom
                                with columns[pos + jump]:
                                    st_folium(m, key=str(datetime.now()),
                                              use_container_width=True,
                                              returned_objects=[])
                                # add to spatial_dict
                        else:
                            geometry = 'None'
                            with columns[pos + jump]:
                                st.write(f":red[{None}]")

            jump += n_columns + 1
        pos += 1

    with collective_tab:
        # TODO: check format and then add for
        cols_col = st.columns(2)
        with cols_col[0]:
            if all_dates_dict_of_dfs:
                value = list(all_dates_dict_of_dfs.keys())[0]
                colors = dates_line_plot('Dataset TimeSpan', all_dates_dict_of_dfs[value])

        if spatial_dict:
            value = list(spatial_dict.keys())[0]
            if spatial_dict[value]:
                with cols_col[1]:
                    all_in_map('Spatial Coverage', spatial_dict[value], titles, colors)
        st.divider()

        # histogram(s)
        if len(histogram_dict) == 1:
            value = list(histogram_dict.keys())[0]
            if np.count_nonzero(~np.isnan(histogram_dict[value])) > 1:
                generate_hist(value, datasets, 'Dataset', histogram_dict[value], value, colors)
                st.divider()
        elif len(histogram_dict) > 1:
            histogram_cols = st.columns(2)
            divider = 0
            i = 0
            for value in histogram_dict:
                if np.count_nonzero(~np.isnan(histogram_dict[value])) > 1:
                    with histogram_cols[i]:
                        generate_hist(value, datasets, 'Dataset', histogram_dict[value], value, colors)
                    if i == 0:
                        i = 1
                    else:
                        i = 0
                    if divider == 0:
                        divider = 1
                        st.divider()

        # wordcloud(s)
        if len(wordcloud_dict) == 1:
            value = list(wordcloud_dict.keys())[0]
            if len(set(wordcloud_dict[value])) > 1:
                generate_wordcloud(value, wordcloud_dict[value])
        elif len(wordcloud_dict) > 1:
            wordcloud_cols = st.columns(2)
            i = 0
            for value in wordcloud_dict:
                if len(set(wordcloud_dict[value])) > 1:
                    with wordcloud_cols[i]:
                        generate_wordcloud(value, wordcloud_dict[value])
                    if i == 0:
                        i = 1
                    else:
                        i = 0
