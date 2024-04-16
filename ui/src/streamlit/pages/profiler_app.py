# File of main app
# Should not be changed if possible
import warnings

warnings.simplefilter(action='ignore', category=FutureWarning)
import os
import sys

sys.path.append('.')
sys.path.append('..')
sys.path.append('../..')

import streamlit as st  # pip install streamlit
import pandas as pd
from PIL import Image
from profiler import profiler_visualization, __change_font, __print_metric
from utils import init_style
from requests import get

# -------------- SETTINGS --------------
page_title = "Profile"
title_icon = ":mag:"
dirname = os.path.dirname(__file__)
stelar_icon = os.path.join(dirname, 'icons/stelar_icon.jpg')
page_icon = stelar_icon
layout = "wide"

im = Image.open(page_icon)

st.set_page_config(page_title=page_title, page_icon=im, layout=layout)
init_style()

query_params = st.query_params
title = query_params.get('title')
package_id = query_params.get('package_id')
KLMS_API = query_params.get('KLMS_API')
API_KEY = query_params.get('API_KEY')
resource_id = query_params.get('resource_id')

headers = {'Content-Type': 'application/json', 'Api-Token': API_KEY}
res_response = get(KLMS_API + 'resource/profile', params={'id': resource_id}, headers=headers)
json_response = res_response.json()
st.title(page_title)
cols = st.columns(2)
with cols[0]:
    st.metric(__change_font("Dataset Title"), __print_metric(title))
with cols[1]:
    st.metric(__change_font("Dataset ID"), __print_metric(package_id))
profiler_visualization(json_response)
