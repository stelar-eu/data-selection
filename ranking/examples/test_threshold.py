import json
import sys
 
sys.path.append('../src/')
import functions

# Open JSON configuration
config_file = open('./config/threshold_config.json')
config_threshold = json.load(config_file)

# Construct input ranked lists according to config
df_threshold, input_lists = functions.construct_input_lists(config_threshold)

# Compute a ranked list of all items applying the specified method (threshold)
threshold_results = functions.combined_ranking(input_lists, config_threshold['settings'])

# Print results
print(threshold_results)



