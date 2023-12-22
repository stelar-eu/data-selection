# Overview
This Python library includes implementations of several algorithms for advanced ranking and also integrates state-of-the-art rank aggregation methods for recommender systems obtained from open-source libraries [ranx](https://github.com/AmenRa/ranx) and [ranky](https://github.com/Didayolo/ranky/tree/master/ranky). It accepts ranked lists of items as input, where multiple scores/rankings exist per item in each ranked list, according to different preferences assigned by different users. 
It computes an overall ranking of items through rank aggregation, reaching a consensus on which permutation of the ranked items should be recommended or combining the obtained ranked lists by different weights to adjust the importance of each ranking criterion, thus prioritizing their preferences. 
Through this advanced ranking, a ranked list of results is returned to the user, where each result is associated with a total (aggregated) score.

The library currently supports these methods:

* Skyline;

* Impact-Confidence-Ease (ICE);

* Linear weighted combination (threshold-based);

* Comb family of algorithms;

* BordaFuse;

* Median Rank Aggregation;

* ISR (Inverse Square Rank);

* LogISR;

* Condorcet.