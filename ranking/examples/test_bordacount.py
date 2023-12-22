import json
import sys
 
sys.path.append('../src/')
import functions

# Open JSON configuration
config_file = open('./config/bordacount_config.json')
config_bordacount = json.load(config_file)

# Construct input ranked lists according to config
df_bordacount, input_lists = functions.construct_input_lists(config_bordacount)

# Compute a ranked list of all items applying the specified method (Borda count)
bordacount_results = functions.combined_ranking(df_bordacount, config_bordacount['settings'])

# Print results
print(bordacount_results)



