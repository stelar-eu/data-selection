import json
import random
import folium
import streamlit as st
from folium.plugins import Draw

from streamlit_folium import st_folium

import geopandas as gpd
import shapely
from shapely.geometry import shape, box, mapping
from shapely.geometry.polygon import Polygon
import pyproj
from shapely.ops import transform
from pandas import isna



#import jinja2
from jinja2 import Template

# https://github.com/oliverroick/Leaflet.Deflate
# https://python-visualization.github.io/folium/latest/reference.html#module-folium.plugins
# https://python-visualization.github.io/folium/latest/user_guide/plugins.html
# https://github.com/python-visualization/folium/blob/main/folium/plugins/draw.py
# https://gis.stackexchange.com/questions/313382/click-event-on-maps-with-folium-and-information-retrieval
# https://github.com/bluehalo/ngx-leaflet-markercluster/issues/5
# https://folium.streamlit.app/draw_support
# https://leaflet.github.io/Leaflet.draw/docs/leaflet-draw-latest.html

def bbox(gdf):
    """Computes the bounding box of a GeoDataFrame.

    Args:
        gdf (GeoDataFrame): A GeoDataFrame.

    Returns:
        A Polygon representing the bounding box enclosing all geometries in the GeoDataFrame.
    """

    '''
    minx, maxx, miny, maxy = 1000, -1000, 1000, -1000
    for idx, row in gdf.iterrows():
       x, y = row.geometry.exterior.coords.xy
       if len(x) > 0:
           t_minx, t_maxx = min(x), max(x)
           minx = min([t_minx, minx])
           maxx = max([t_maxx, maxx])
       if len(y) > 0:
           t_miny, t_maxy = min(y), max(y)
           miny = min([t_miny, miny])
           maxy = max([t_maxy, maxy])
    #print(minx, maxx, miny, maxy)
    '''    
    minx, miny, maxx, maxy = gdf.geometry.total_bounds
    return box(minx, miny, maxx, maxy)
	
	
def create_gdf(ranked_results):
    """Creates a GeoDataFrame from the list of ranked results.

    Args:
        ranked_results (JSON): A JSON array with all ranked results.

    Returns:
        A GeoDataFrame with the geometries of ranked results.
    """	
    # Create two lists with the identifiers and the collected geometries
    ids = []
    geometries = []
    for item in ranked_results:
        # Get geometry value from extras
        ids.append(item['id'])
        g = next(extra['value'] for extra in item['extras'] if extra['key'] == 'spatial')
        try:  # First, consider it as a GeoJSON
            if isinstance(g, dict):
                geom =json.dumps(g)   # JSON dictionary
            else:
                geom = json.loads(g)  # string containing a JSON
        except:
            try:  # Then, assuming this is WKT
                wkt = shapely.wkt.loads(g)
                geom = shapely.geometry.mapping(wkt)
            except: 
                geom = {"type":"Polygon","coordinates":[]}  # Empty polygon
        geometries.append(shape(geom))

    # Construct GeoDataFrame with the collected geometries and their identifiers (for tooltips)
    d = {'id': ids, 'geometry': geometries}
    gdf = gpd.GeoDataFrame(d, crs="EPSG:4326")
	
    return gdf


def geom_to_shape(g):
    """Creates a shape from the given geometry specification (GeoJSON, string, WKT, or WKB).

    Args:
        g (string): A GeoJSON, string, WKT, or WKB specification of the geometry.

    Returns:
        The geometry shape.
    """    
    try:  # First, consider it as a GeoJSON
        if isinstance(g, dict):
            # geom = json.dumps(g)   # JSON dictionary
            geom = g
        else:
            geom = json.loads(g)  # string containing a JSON
    except:
        try:  # Then, assuming this is WKT
            wkt = shapely.wkt.loads(g)
            geom = shapely.geometry.mapping(wkt)
        except:
            try:  # Next, assuming this is WKB
                wkb = shapely.wkb.loads(g, hex=True)
                geom = shapely.geometry.mapping(wkb)
            except:
                geom = {"type":"Polygon","coordinates":[]}  # Empty polygon
    return shape(geom)


	
def map_geometries(m, df, show_bbox=False):
    """Draws the provided geometries as a layer on the map. Map center and zoom level are set automatically.

    Args:
	     m (Map): A Folium map where the geometries will be displayed.
         df (GeoDataFrame): A DataFrame containing the geometries to be displayed.
         show_bbox (bool): Whether to show the bounding box of the GeoDataFrame (default: False).

    Returns:
        
    """

    # Construct GeoDataFrame with the collected geometries and their identifiers (for tooltips)
    gdf = gpd.GeoDataFrame(df, crs="EPSG:4326")
    
    #print(gdf.shape)
    #gdf = gdf[gdf.geometry.type == 'Polygon']
    #print(gdf.shape)    
    #gdf = gdf[gdf.geometry.is_valid]
    #print(gdf.shape)

    # Automatically center the map at the center of the bounding box enclosing the geometries.
    bb = bbox(gdf)
    map_center = [bb.centroid.y, bb.centroid.x]

    # Automatically set the zoom level
    m.fit_bounds(([bb.bounds[1], bb.bounds[0]], [bb.bounds[3], bb.bounds[2]]))

    # Get the centroids reprojected in WGS84
    centroids = gdf.to_crs('+proj=cea').centroid.to_crs(4326)  #gdf.geometry.centroid.to_crs(4326)
    
    
    # Create the marker cluster
    locations = list(zip(centroids.y.tolist(),
                     centroids.x.tolist(),
                     gdf.id.tolist()))
    
    locations = [l for l in locations if not isna(l[0])]

    callback = """\
        function (row) {
        var icon, marker;
        icon = L.AwesomeMarkers.icon({
        icon: 'map-marker', markerColor: 'blue'});
        marker = L.marker(new L.LatLng(row[0], row[1]));
        marker.setIcon(icon);
        var popup = L.popup({height: '300'});
        popup.setContent(row[1]);
        marker.bindPopup(popup);
        return marker;
        };
        """
        
    marker_layer = folium.FeatureGroup(name='markers')
    marker_layer.add_child(folium.plugins.FastMarkerCluster(locations, callback=callback))
    m.add_child(marker_layer)
	
    # Add pois to a marker cluster
    #coords, popups = [], []
    #for idx, poi in pois.iterrows():
    #    coords.append([poi.geometry.y, poi.geometry.x)]
    #    label = str(poi['id']) + '<br>' + str(poi['name']) + '<br>' + ' '.join(poi['kwds'])
    #    popups.append(folium.IFrame(label, width=300, height=100))

    #poi_layer = folium.FeatureGroup(name='pois')
    #poi_layer.add_child(MarkerCluster(locations=coords, popups=popups))
    #m.add_child(poi_layer)

    # folium.GeoJson(pois, tooltip=folium.features.GeoJsonTooltip(fields=['id', 'name', 'kwds'],
    #                                                             aliases=['ID:', 'Name:', 'Keywords:'])).add_to(m)

    if show_bbox:
        folium.GeoJson(bb).add_to(m)

 #   folium.LatLngPopup().add_to(m)

#    return m



def initialize_session_state():
    if 'markers' not in st.session_state:
        st.session_state['markers'] = []
    if 'sel_region' not in st.session_state:
        st.session_state['sel_region'] = {}
    if 'map_data' not in st.session_state:
        st.session_state['map_data'] = {}
    if 'all_drawings' not in st.session_state['map_data']:
        st.session_state['map_data']['all_drawings'] = None



def reset_session_state():
    # Delete all the items in session state
    for key in st.session_state.keys():
        del st.session_state[key]
    initialize_session_state()


	
def get_drawn_shape(m, gdf_regions, last_val=None, comp=st):

#		gdf_regions (GeoDataFrame): Names and polygon geometries of regions to populate a dropdown list.

    # Create the map in the main app
    #m = folium.Map(tiles='OpenStreetMap', location=[45.0, 10.0], zoom_start=5)

	initialize_session_state()

    # Drawing specifications: allow rectangles only
	draw = Draw(draw_options={'polyline':False,'polygon':True, 'rectangle':True,'circle':True,'marker':True, 'circlemarker':False}, edit_options={'edit':False}, position='topleft', export=False).add_to(m)

	# Associate template to the map: Need to remove any previously drawn feature from the map
	el = folium.MacroElement().add_to(m)
	el._template = Template("""
            {% macro script(this, kwargs) %}
            
//			var prevLayer = null;   // Retain the last drawn layer
			
var drawnItems = L.featureGroup().addTo({{ this._parent.get_name() }});


            {{ this._parent.get_name() }}.on(L.Draw.Event.CREATED, function(e){

                var layer = e.layer,
                type = e.layerType;
//				prevLayer = layer;   // This will become the last drawn layer

drawnItems.addLayer(layer);

//                console.log('type: ' + type);
//                var coords_json = layer.toGeoJSON();
//                window.alert(coords_json['geometry']['coordinates']);
//                console.log('coordinates: ' + coords_json['geometry']['coordinates']);
//                coords_json = JSON.stringify(coords_json);
//                console.log('json type: ' + coords_json);
            });
	
            {{ this._parent.get_name() }}.on(L.Draw.Event.DRAWSTART, function() { 
			
			drawnItems.clearLayers();

//				var map = {{this._parent.get_name()}};   // Get the map object
//				map.eachLayer(function (layer) {
//				console.log(layer._leaflet_id);
//				  if (layer == prevLayer) {   
//                     map.removeLayer(layer);
//		             console.log("Removed" + layer);
//		          }
//               });

			}				
         );


            {{ this._parent.get_name() }}.on(L.Draw.Event.DELETED, function(e){
			
//			alert(drawnItems._leaflet_id)
//			var data = drawnItems.toGeoJSON();
//			var convertedData = 'text/json;charset=utf-8,'
//                    + encodeURIComponent(JSON.stringify(data));
//			alert(convertedData);

			drawnItems.clearLayers();
							
            });
	


//{{ this._parent.get_name() }}.on('layeradd', function(layer, layername){

//alert(layer);

//});

	
            {% endmacro %}
	""")


	# CRS reprojection is only needed in case of user-specified circles
	wgs84 = pyproj.CRS('EPSG:4326')      # lat/lon coordinates
	epsg3857 = pyproj.CRS('EPSG:3857')   # coordinates in meters
	# Specify projections back and forth
	proj_forward = pyproj.Transformer.from_crs(wgs84, epsg3857, always_xy=True).transform
	proj_backward = pyproj.Transformer.from_crs(epsg3857, wgs84, always_xy=True).transform


	# Streamlit interface	
	c1, c2 = comp.columns(2)
	wkt = ''
	fg = folium.FeatureGroup(name='Markers')
	for marker in st.session_state['markers']:
		fg.add_child(marker)	
	
	# Keep wkt_area in the session state
#	if 'wkt_area' not in st.session_state:
#		st.session_state['wkt_area'] = ''
	
	with c1:
		output = st_folium(m, feature_group_to_add=fg, width=500, height=500)
		# Remove chached drawings
		#output['all_drawings'] = []

	with c2:

		def dropdown_changed():
			wkt=gdf_regions.loc[sel_region, 'geometry']
#			print("dropdown", wkt)
			geojs = json.dumps(mapping(wkt))
#			print("GeoJSON", sel_region)
			st.session_state['markers'] = [folium.GeoJson(data=geojs, style_function=lambda x: {'fillColor': 'orange'})]
#			st.session_state['wkt_area'] = wkt
			output['all_drawings'] = []			
			
		# Placeholder for dropdown list of countries
		if not gdf_regions.empty:
			plc2 = st.empty()
			# Use list of European countries with associated polygons from GeoJSON
			sel_region = plc2.selectbox('Country', gdf_regions.index, index=0, placeholder='--Choose a country--', disabled=False, label_visibility='visible', key='country_dropdown1') # on_change=dropdown_changed, 
			# Intercept changed option and draw the respective polygon on map
			if sel_region != '--Select a country--':
				# Workaround to bypass glitch in session state (handled next)
				output['all_drawings'] = []
#				sel_region = plc2.selectbox('Country', gdf_regions.index, index=10, placeholder='--Choose a country--', disabled=False, label_visibility='visible') #, key='country_dropdown') # on_change=dropdown_changed, 
			
		# Retrieve GeoJSON of the latest feature drawn on map
		last_drawing = output['last_active_drawing']
		all_drawings = output['all_drawings']
		if all_drawings :
			# TODO: Reset selected region from the dropdown
			plc2.empty()
			sel_region = plc2.selectbox('Country', gdf_regions.index, index=0, placeholder='--Choose a country--', disabled=False, label_visibility='visible', key='country_dropdown2') # on_change=dropdown_changed, 
#			st.session_state.country_dropdown = '--Choose a country--' 
			if last_drawing :
				# Convert GeoJSON to WKT for reporting
				geom = shape(last_drawing['geometry'])
				# In case radius is specified, convert the drawn circle into a polygon
				if 'radius' in last_drawing['properties']:
					geom = transform(proj_forward, geom) # Reproject the point to EPSG:3857 using meters
					geom = geom.buffer(last_drawing['properties']['radius']) # Buffer the reprojected point with the user-specified distance in meters
					geom = transform(proj_backward, geom) # Reproject the resulting buffer back to WGS84
				# Report the WKT of the specified shape (point, polygon)
				wkt = geom.wkt
#				st.session_state['wkt_area'] = wkt
			else: #lif not all_drawings:  # No drawn shapes on map, clear up the text area
				wkt = ''	
		elif sel_region != '--Select a country--':	# Changes in dropdown are handled next
			# Report the BOUNDARY of the selected region
#			wkt=gdf_regions.loc[sel_region, 'geometry']
			st.session_state['sel_region'] = sel_region
			poly=gdf_regions.loc[sel_region, 'geometry']
			# No need ro convert to GeoJSON for map rendering
#			geojs = json.dumps(mapping(poly))
			st.session_state['markers'] = [folium.GeoJson(data=poly, style_function=lambda x: {'fillColor': 'orange'})]
			# IMPORTANT! Report back the bounding box of the country
			boundary = shape(poly).bounds
			wkt = box(boundary[0], boundary[1], boundary[2], boundary[3]).wkt
#			st.session_state['wkt_area'] = wkt			
	
		# Placeholder for text area input for WKT
		plc1 = st.empty()
		if (wkt is None or wkt == "") and last_val is not None:
		   wkt = last_val
		wkt_input = plc1.text_area('WKT', value=wkt, disabled=False, label_visibility='visible') #, key='wkt_area')
#		st.session_state['wkt_area'] = wkt
		
	return wkt_input #st.session_state.wkt_area #
	
