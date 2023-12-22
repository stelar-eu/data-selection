import json
import sys
 
sys.path.append('../src/')
import functions

# Open JSON configuration
config_file = open('./config/ice_config.json')
config_ice = json.load(config_file)

# Construct input ranked lists according to config
df_ice, input_lists = functions.construct_input_lists(config_ice)

# Compute a ranked list of all items applying the specified method (ICE)
ice_results = functions.combined_ranking(df_ice, config_ice['settings'])

# Print results
print(ice_results)



