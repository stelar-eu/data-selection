# DataCatalog_GUI

## Python Execution
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

## Docker Execution
Build the docker image by:
```docker build -t data_selection:v1 .
```

Create the container by:
```docker run --name data_selection -p 8501:8501 data_selection:v1
```
