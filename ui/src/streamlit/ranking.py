from paretoset import paretoset
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import heapq
from functools import reduce

# Dependencies for rankx, ranky
import ranky as rk
from ranx import Qrels, Run, compare, fuse, evaluate
from ranx import data_structures


# Auxiliary frunctions for accepting input ranked list from CSV

def read_list_csv(file, separator=';', col_id='id', col_score='score'):
    """Reads ranked items (with an id and a numerical score) from a CSV file.

    Args:
        file (string): Path to the input CSV file.
        separator (string): Column delimiter of the input CSV file (default: `;`).
        col_id (string): Name of the column containing the unique identifier of each item in the list (default: `id`).      
        col_score (string): Name of the column containing the score of each item (default: `score`).      
                
    Returns:
        A DataFrame with the given items ordered by descending score.
    """
    
    df = pd.read_csv(file, sep=separator)
    # Use the unique identifiers as index in each data frame for fast access
    df = df.set_index(col_id)
    # Represent scores as numerical values
    df = df[pd.to_numeric(df[col_score], errors='coerce').notnull()]
    # Sort by descending score
    df = df.sort_values(by=[col_score], ascending=False)
    
    return df


def read_list_json(json_arr, col_id='id', col_score='score'):
    """Reads ranked items (with an id and a numerical score) from a JSON array.

    Args:
        json_arr (array): An array with key(id), value(score) pairs.
        col_id (string): Key containing the unique identifier of each item in the dictionary (default: `id`).      
        col_score (string): Key containing the score of each item (default: `score`).      
                
    Returns:
        A DataFrame with the given items ordered by descending score.
    """
    
    df = pd.DataFrame(json_arr)
    # Use the unique identifiers as index in each data frame for fast access
    df = df.set_index(col_id)
    # Represent scores as numerical values
    df = df[pd.to_numeric(df[col_score], errors='coerce').notnull()]
    # Sort by descending score
    df = df.sort_values(by=[col_score], ascending=False)
    
    return df


def read_multi_lists_csv(file, col_scores, separator=';', col_id='id'):
    """Reads ranked items (with an id and a numerical score) from a CSV file.

    Args:
        file (string): Path to the input CSV file.
        separator (string): Column delimiter of the input CSV file (default: `;`).
        col_id (string): Name of the column containing the unique identifier of each item in the list (default: `id`).      
        col_scores (array): List of the column names, each representing the score in a feature per item.      
                
    Returns:
        A DataFrame with unordered items and their respective scores for the specified features (columns).
    """
    
    # Read input file and keep only the specified columns (identifiers and scores)
    df = pd.read_csv(file, sep=separator, usecols = [col_id] + col_scores)
    # Use the unique identifiers as index in each data frame for fast access
    df = df.set_index(col_id)
    # Represent scores as numerical values
    for c in col_scores:
        df = df[pd.to_numeric(df[c], errors='coerce').notnull()]
    
    return df


def split_input_to_lists(df):
    """Splits a given dataframe into multiple dataframes, each having two columns: the identifier and one of the original columns (carrying scores per feature).
    
    Args:
        df (DataFrame): The DataFrame that will be split.    
                
    Returns:
        A collection of DataFrames, each containing a ranked list (with item identifiers and their respective scores).
    """
    
    input_lists = []
    
    # For each column, a separate list will be created (assuming common identifiers)   
    for col in list(df.columns):
        ranked_list = df[[col]]
        input_lists.append(ranked_list)
    
    return input_lists


def merge_input_lists(input_lists):
    """Merges input ranked lists based on their identifiers.

    Args:
        input_lists (array): Array of DataFrames that will be merged.   
                
    Returns:
        A DataFrame with all unordered items and their respective scores for the specified features (columns).
    """

    # Add suffixes to column 'score' in each input list (data frame)
    new_list = []
    for idx, df in enumerate(input_lists):
        df = df.add_suffix('_'+str(idx))
        new_list.append(df)
                                   
    df_merged = reduce(lambda left,right: pd.merge(left, right, left_index=True, right_index=True, how='outer'), new_list)
    
    return df_merged


# Construct input ranked lists according to configuration

def construct_input_lists(config):
    """Constructs input ranked lists according to the given configuration.

    Args:
        config (json): JSON with all configuration settings.     
                
    Returns:
        A DataFrame with unordered items and their respective scores for the specified features (columns).
    """
    
    input_lists = []
    
    if len(config['input']) == 1:   # A single CSV file contains all scores (one column per feature)
        kwargs = config['input'][0] 
        df_merged = read_multi_lists_csv(**kwargs)
        input_lists = split_input_to_lists(df_merged)
    else:                           # Multiple CSV files, each containing scores for a single feature
        for kwargs in config['input']:
            ranked_list = read_list_csv(**kwargs)
            input_lists.append(ranked_list)
        df_merged = merge_input_lists(input_lists)

    return df_merged, input_lists


def split_partial_results_to_lists(partial_results, col_id='id'):
    """Splits the given list of partial ranked results into multiple dataframes, each having two columns: the identifier and one of the original columns (carrying scores per facet).
    
    Args:
        partial_results (list): JSON array of partial results: each item holds an "id" (unique identifiers) and a dictionary with partial scores per facet.    
        col_id (string): Name of the column containing the unique identifier of each item in the list (default: `id`).          
    Returns:
        A collection of DataFrames, each containing a ranked list (with item identifiers and their respective partial scores).
    """
    
    input_lists = []

    # Create a DataFrame from the input JSON
    df = pd.json_normalize(partial_results, sep='.')
    # Use the mandatory "id" column as index
    df = df.set_index(col_id)
    # Keep the original names per facet by removing the 'partial_scores.' prefix resulting from JSON normalization
    df.columns = list(map(lambda c: c.split("partial_scores.",1)[1], df.columns))
    # For each column, a separate list will be created (assuming common identifiers)
    for col in list(df.columns):
        ranked_list = df[[col]].copy()
        ranked_list.rename(columns={col: 'score'}, inplace=True)
        input_lists.append(ranked_list)
    
    return input_lists


# ICE (Impact - Confidence - Ease)

def ICEscore(df, impact = 'impact', confidence = 'confidence', ease = 'ease'):
    # Create an extra column for the ICE score
    results = df.assign(ice='NAN')
    # Assign ICE score
    for i, row in results.iterrows():
        results.at[i, 'ice'] = row[impact] * row[confidence] * row[ease]
    
    # Sort by descending ICE score
    results = results.sort_values(by=['ice'], ascending=False)
    
    return results


# Paretoset frontier (Skyline)

def plot2DParetoSet(df, paretoset, attrX, attrY, colorData='blue', colorPareto='orange'):
    # Draw dataset points
    plt.scatter(df[attrX], df[attrY], c = colorData, linewidths = 2, marker ='^', edgecolor = colorData, s = 100)
    # Draw Paretoset points
    plt.scatter(paretoset[attrX], paretoset[attrY], c = colorPareto, linewidths = 2, marker ='o', edgecolor = colorPareto, s = 50)
    # Draw plot
    plt.xlabel(attrX)
    plt.ylabel( attrY)
    plt.show()


def Skyline(df, sense):
    
    # Essentially filters out any items not belonging to the skyline
    skyline = paretoset(df, sense=sense)

    return df[skyline]


def weightedScoreSkyline(df, sense, weights, k):
    
    # Find the skyline
    skyline = paretoset(df, sense=sense)
    
    # columns considered in the skyline
    cols = df.columns
    
    # deep copy of the skyline items; also create an extra column for the score
    results = df[skyline].copy(deep=True).assign(score='NAN')
    
    # Assign weighted score
    # TODO: Apply a user-specified function (e.g., average) for aggregated score?
    for i, row in results.iterrows():
        score = 0
        for j, column in enumerate(cols):
            score += row[column] * weights[j]
        results.at[i, 'score'] = score
    
    # sort by descending score
    results = results.sort_values(by=['score'], ascending=False)
    
    # return items with the top-k scores
    return results.head(k)


# Linear weighted combination of rankings

def calc_weighted_score(values, weights):
    """Calculates the weighted aggregate score of the given values.

    Args:
        values: A list of score values; each value corresponds to the partial score of the same element in each ranked list.
        weights: A list of numerical weights; one weight in [0..1] per ranked list.
        
    Returns:
        The weighted aggregate score.
    """
    cur_sum = 0
    for i, v in enumerate(values):
        cur_sum += values[i] * weights[i]
    
    return cur_sum/len(weights)


def calc_max_list_size(rankings):
    """Calculates the maximum size among the given ranked lists.

    Args:
        rankings: A collection of ranked lists; each list reports its elements by descending score.
                
    Returns:
        The maximum size (number of elements) of the ranked lists.
    """
    max_size = 0
    for r in rankings:
        if len(r) > max_size:
            max_size = len(r)
    return max_size


def random_access(rankings, key):
    """Performs random access in the given ranked lists and reports the partial scores of the given element.

    Args:
        rankings: A collection of ranked lists; each list reports its elements by descending score.
        key: The unique identifier of an element in the lists.
                
    Returns:
        A list with the scores of the element in each ranked list.
    """
    values = []
    for j in range(len(rankings)):
        if key in rankings[j].index:
            values.append(rankings[j].loc[key]['score'])
        else:  # Key not present in this list
            values.append(0.0)
    return values


def topk_threshold(rankings, weights, k):
    """Finds the top-k elements based on the given ranked lists and weights using Fagin's Threshold algorithm.

    Args:
        rankings: A collection of ranked lists; each list reports its qualifying elements by descending score.
        weights: A list of numerical weights; one weight in [0..1] per ranked list.
        k: The number of elements with the largest aggregated scores to return.
                
    Returns:
        A DataFrame with the elements having the top-k aggregated scores, the number of elements examined in each list, and the final threshold value.
    """
    
    if k == 0:
        return [], 0, 0

    counter = 0

    # Maintain a min heap with score values to check the amount of elements therein
    # If the worst one is above the threshold, stop iteration
    heap_li = []
    heapq.heapify(heap_li)
    seen_items = set()

    # Iterate in parallel over items in the ranked lists
    for i in range(calc_max_list_size(rankings)):
        counter += 1
        scores4threshold = []

        # Iterate over items in the current i-th position
        for j in range(len(rankings)):
            # Get item from the j-th list at the i-th iteration
            if len(rankings[j]) > i:
                val = rankings[j].iloc[i]  
                key = val.name
            else:  # skip a ranked list if it contains fewer elements
                scores4threshold.append(0.0)
                continue

            # Keep this partial score for adjusting the threshold
            scores4threshold.append(val['score'])
            
            if key not in seen_items:
                # Random access to each ranked list to get the scores
                values = random_access(rankings, key)
                
                # Calculate aggregate score
                aggr_score = calc_weighted_score(values, weights)
#                print(aggr_score)
                
                # Append result to heap
                heapq.heappush(heap_li, (aggr_score, key))
                seen_items.add(key)
                
                # Remove the worst elements (aggregation function is monotonic)
                if len(heap_li) > k:
                    heapq.heappop(heap_li)

        # Threshold is the aggregate of the scores seen in the current iteration (i-th position in each ranked list)
        threshold = calc_weighted_score(scores4threshold, weights)
#        print('threshold', threshold)
#        print('current worst', heap_li[0][0])
        
        # Threshold reached, stop the iteration since no better elements can be found
        if len(heap_li) >= k and heap_li[0][0] >= threshold:
            break

    # Heap contains score values so get n largest (these are the ones with highest rank)
    result = heapq.nlargest(k, heap_li)
    
    df = pd.DataFrame(result, columns=['score','id'])
    df = df.set_index('id')

    return df, counter, threshold


# Rank Aggregation

def rank_aggregation_by_ranx(rankings, method, k):
    """Applies a rank aggregation function (e.g., Borda fuse, Comp MIN, ISR) on the given ranked lists.

    Args:
        rankings: A collection of ranked lists; each list reports its qualifying elements by descending score.
        method: The rank aggregation method to be applied, as specified in the ranky library.
        k: The number of elements with the largest aggregated scores to return.
                
    Returns:
        A DataFrame with the top-k ranked elements having the greatest aggregated scores.
    """
    
    # Create structures based on dictionaries, as specified by ranx library
    runs =[]
    # For each input ranked list create a separate dictionary
    for r in rankings:
        run = Run({'score': r.T.to_dict('records')[0]})
        runs.append(run)
    
    # Apply the specified method (e.g., min, max, med)
    combined_run = fuse(runs = runs, method = method)

    # Return a data frame with the top-k items sorted by descending aggregated score
    df_combined = pd.DataFrame.from_dict(dict(combined_run))
    
    return df_combined.sort_values(by=['score'], ascending=False).head(k)


def rank_aggregation_by_ranky(rankings, method, k):
    """Applies a rank aggregation function (either Borda count or MRA) on the given ranked lists.

    Args:
        rankings: A DataFrame with the input ranked lists; each list reports its qualifying elements with a score.
        method: The rank aggregation method to be applied, as specified in the ranky library.
        k: The number of elements with the largest aggregated scores to return.
                
    Returns:
        A DataFrame with the top-k ranked elements having the greatest aggregated scores.
    """
    
    # Apply the specified method either Borda count or MRA)
    if method == 'bordacount': # TODO: parameters to support variants for mean (default), median
        sf_combined = rk.borda(rankings)
    elif method == 'mra':
        sf_combined = rk.majority(rankings)
    else:
        return

    # Return a data frame with the top-k items sorted by descending aggregated score (in the 2nd column of the DataFrame)
    df_combined = pd.DataFrame({'id':sf_combined.index, 'score':sf_combined.values}).set_index('id')
    
    # TODO: If Borda count, then report the LOWEST aggregated scores
    return df_combined.sort_values(by=['score'], ascending=False).head(k)


def combined_ranking(rankings, settings):
    """Applies a ranking method (e.g., ICE, threshold, Borda count, Comp MIN) to combine (aggregate) the given ranked lists.

    Args:
        rankings (list): A data frame OR a collection of ranked lists; each list reports its qualifying elements by descending score.
        settings (json): User-specified configuration settings for the ranking method and its parameters.
                
    Returns:
        A DataFrame with the top-k ranked elements having the greatest aggregated scores according to the applied method.
    """

    # Accommodate methods requiring a DataFrame (with a column per input ranking) and also those that work on separate ranked lists
    if isinstance(rankings, pd.DataFrame):   # input is a DataFrame
        df_rankings = rankings   
    else:   # construct a merged DataFrame from input lists
        df_rankings = merge_input_lists(rankings)   

    if settings['algorithm'].lower() == 'threshold':
        # INPUT: collection of ranked lists
        if 'weights' in settings:
            weights = settings['weights']
        else:  # If weights are not user-specified, assume equal weight (1.0) for each input list
            weights = [1.0] * len(rankings)
        result, cnt, threshold = topk_threshold(rankings, weights, settings['k'])
    elif settings['algorithm'].lower() == 'ice':
        # INPUT: data frame
        result = ICEscore(df_rankings)
    elif settings['algorithm'].lower() == 'paretoset':
        # INPUT: data frame
        result = Skyline(df_rankings, settings['sense'])
    elif settings['algorithm'].lower() == 'weighted_paretoset':
        # INPUT: data frame
        result = weightedScoreSkyline(df_rankings, settings['sense'], settings['weights'], settings['k'])
    elif settings['algorithm'].lower() in ['combmin','combmax','combmed','combsum','combanz','combmnz']:  # methods from ranx
        # INPUT: collection of ranked lists
        result = rank_aggregation_by_ranx(rankings, settings['algorithm'][4:].lower(), settings['k']) 
    elif settings['algorithm'].lower() in ['log_isr','bordafuse','condorcet','isr']:  # methods from ranx
        # INPUT: collection of ranked lists
        result = rank_aggregation_by_ranx(rankings, settings['algorithm'].lower(), settings['k'])
    elif settings['algorithm'].lower() in ['bordacount','mra']:  # methods from ranky
        # INPUT: data frame
        result = rank_aggregation_by_ranky(df_rankings, settings['algorithm'].lower(), settings['k'])
        
    return result

