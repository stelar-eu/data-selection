# DataCatalog_GUI


If the virtual environment does not exist:
```sh
python -m venv streamlit_catalog
source streamlit_catalog/bin/activate
pip install -r requirements.txt
```

if the virtual environment exists:
```sh
source streamlit_catalog/bin/activate
```

Finally:
```sh
cd src/streamlit
streamlit run app.py --server.port 8501
```

And visit `localhost:8501`
