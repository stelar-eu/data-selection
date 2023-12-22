import json
import sys
 
sys.path.append('../src/')
import functions

# Open JSON configuration
config_file = open('./config/condorcet_config.json')
config_condorcet = json.load(config_file)

# Construct input ranked lists according to config
df_condorcet, input_lists = functions.construct_input_lists(config_condorcet)

# Compute a ranked list of all items applying the specified method (Condorcet)
condorcet_results = functions.combined_ranking(input_lists, config_condorcet['settings'])

# Print results
print(condorcet_results)

