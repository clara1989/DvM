"""
NonParametric statistical tests

Created by Dirk van Moorselaar on 27-02-2018.
Copyright (c) 2018 DvM. All rights reserved.
"""

import cv2

import numpy as np

from scipy.stats import ttest_rel, ttest_ind, wilcoxon
from IPython import embed 

class Permutation():

	def __init__(self): pass

	def clusterBasedPermutation(self, X1, X2, p_val = 0.05, cl_p_val = 0.05, paired = True, tail = 'both', nr_perm = 1000, mask = None, conn = None):

		'''
		Implements Maris, E., & Oostenveld, R. (2007). Nonparametric statistical testing of EEG- and MEG- data. 
		Journal of Neurosience Methods, 164(1), 177?190. http://doi.org/10.1016/J.Jneumeth.2007.03.024

		Arguments
		- - - - - 

		X1 (array): subject X dim1 X dim2 (optional), where dim1 and dim2 can be any type of dimension 
					(time, frequency, electrode, etc). Values in array represent some dependent
					measure (e.g classification accuracy or power)
		X2 (array | float): either a datamatrix with same dimensions as X1, or a single value 
					against which X1 will be tested
		p_val (float): p_value used for inclusion into the cluster
		cl_p_val (float): p_value for evaluation overall cluster significance
		paired (bool): paired t testing (True) or independent t testing (False)
		tail (str): apply one- or two- tailed t testing
		nr_perm (int): number of permutations
		mask (array): dim1 X dim2 array. Can be used to restrict cluster based test to a specific region. 
		conn (array): outlines which dim1 points are connected to other dim1 points. Usefull
					  when doing a cluster based permutation test across electrodes 

		Returns
		- - - -

		cl_p_vals (array): dim1 X dim2 with p-values < cl_p_val for significant clusters and 1's for all other clusters

		'''

		# if no mask is provided include all datapoints in analysis
		if mask == None:
			mask = np.array(np.ones(X1.shape[1:]),dtype = bool)
			print('\nUsing all {} datapoints in cluster based permutation'.format(mask.size))
		elif mask.shape != X1[0].shape:
			print('\nMask does not have the same shape as X1. Adjust mask!')
		else:
			print('\nThere are {} out of {} datapoints in your mask during cluster based permutation'.format(int(mask.sum()), mask.size))	

		# check whether X2 is a chance variable or a data array
		if isinstance(X2, (float, int)):
			X2 = np.tile(X2, X1.shape)

		# compute observed cluster statistics
		pos_sizes, neg_sizes, pos_labels, neg_labels, sig_cl = self.computeClusterSizes(X1, X2, p_val, paired, tail, mask, conn)	
		cl_p_vals = np.ones(sig_cl.shape)

		# iterate to determine how often permuted clusters exceed the observed cluster threshold
		c_pos_cl = np.zeros(np.max(np.unique(pos_labels)))
		c_neg_cl = np.zeros(np.max(np.unique(neg_labels)))

		# initiate random arrays
		X1_rand = np.zeros(X1.shape)
		X2_rand = np.zeros(X1.shape)

		for p in range(nr_perm):

			print "\r{0}% of permutations".format((float(p)/nr_perm)*100),

			# create random partitions
			if paired: # keep observations paired under permutation
				rand_idx = np.random.rand(X1.shape[0])<0.5
				X1_rand[rand_idx,:] = X1[rand_idx,:] 
				X1_rand[~rand_idx,:] = X2[~rand_idx,:] 
				X2_rand[rand_idx,:] = X2[rand_idx,:] 
				X2_rand[~rand_idx,:] = X1[~rand_idx,:]
			else: # fully randomize observations under permutation
				all_X = np.vstack((X1,X2))	
				all_X = all_X[np.random.permutation(all_X.shape[0]),:]
				X1_rand = all_X[:X1.shape[0],:]
				X2_rand = all_X[X1.shape[0]:,:]

			# compute cluster statistics under random permutation
			rand_pos_sizes, rand_neg_sizes, _, _, _ = self.computeClusterSizes(X1_rand, X2_rand, p_val, paired, tail, mask, conn)
			max_rand = np.max(np.hstack((rand_pos_sizes, rand_neg_sizes)))

			# count cluster p values
			c_pos_cl += max_rand > pos_sizes
			c_neg_cl += max_rand > neg_sizes
				
		# compute cluster p values
		p_pos = c_pos_cl / nr_perm
		p_neg = c_neg_cl / nr_perm

		# remove clusters that do not pass threshold
		if tail == 'both':
			for i, cl in enumerate(np.unique(pos_labels)[1:]): # 0 is not a cluster
				if p_pos[i] < cl_p_val/2:
					cl_p_vals[pos_labels == cl] = p_pos[i]
				else:
					pos_labels[pos_labels == cl] = 0

			for i, cl in enumerate(np.unique(neg_labels)[1:]): # 0 is not a cluster
				if p_neg[i] < cl_p_val/2:
					cl_p_vals[neg_labels == cl] = p_neg[i]
				else:
					neg_labels[neg_labels == cl] = 0

		elif tail == 'right':
			for i, cl in enumerate(np.unique(pos_labels)[1:]): # 0 is not a cluster
				if p_pos[i] < cl_p_val:
					cl_p_vals[pos_labels == cl] = p_pos[i]
				else:
					pos_labels[pos_labels == cl] = 0

		elif tail == 'left':
			for i, cl in enumerate(np.unique(neg_labels)[1:]): # 0 is not a cluster
				if p_neg[i] < cl_p_val:
					cl_p_vals[neg_labels == cl] = p_neg[i]
				else:
					neg_labels[neg_labels == cl] = 0

		# ADD FUNCTION TO GET 			

		return cl_p_vals			
						

	def computeClusterSizes(self, X1, X2, p_val, paired, tail, mask, conn):
		'''

		Helper function for clusterBasedPermutation (see documentation)
		
		NOTE!!!
		Add the moment only supports two tailed tests
		Add the moment does not support connectivity
		'''

		# STEP 1: determine 'actual' p value
		# apply the mask to restrict the data
		X1_mask = X1[:,mask]
		X2_mask = X2[:,mask]

		p_vals = np.ones(mask.shape)
		t_vals = np.zeros(mask.shape)

		if paired:
			t_vals[mask], p_vals[mask] = ttest_rel(X1_mask, X2_mask)
		else:
			t_vals[mask], p_vals[mask] = ttest_ind(X1_mask, X2_mask)		

		# initialize clusters and use mask to restrict relevant info
		sign_cl = np.mean(X1,0) - np.mean(X2,0)	
		sign_cl[~mask] = 0
		p_vals[~mask] = 1

		# STEP 2: apply threshold and determine positive and negative clusters
		cl_mask = p_vals < p_val
		pos_cl = np.zeros(cl_mask.shape)
		neg_cl = np.zeros(cl_mask.shape)
		pos_cl[sign_cl > 0] = cl_mask[sign_cl > 0]
		neg_cl[sign_cl < 0] = cl_mask[sign_cl < 0]

		# STEP 3: label clusters
		if conn == None:
			nr_p, pos_labels = cv2.connectedComponents(np.uint8(pos_cl))
			nr_n, neg_labels = cv2.connectedComponents(np.uint8(neg_cl))
			pos_labels = np.squeeze(pos_labels) # hack to control for onedimensional data (CHECK whether correct)
			neg_labels = np.squeeze(neg_labels)
		else:
			print('Function does not yet support connectivity')	

		# STEP 4: compute the sum of t stats in each cluster (pos and neg)
		pos_sizes, neg_sizes = np.zeros(nr_p - 1), np.zeros(nr_n - 1)
		for i, label in enumerate(np.unique(pos_labels)[1:]):
			pos_sizes[i] = np.sum(t_vals[pos_labels == label])

		for i, label in enumerate(np.unique(neg_labels)[1:]):
			neg_sizes[i] = abs(np.sum(t_vals[neg_labels == label]))

		if sum(pos_sizes) == 0:
			pos_sizes = 0

		if sum(neg_sizes) == 0:
			neg_sizes = 0

		return pos_sizes, neg_sizes, pos_labels, neg_labels, p_vals	

def FDR(p_vals, q = 0.05, method = 'pdep', adjust_p = False, report = True):
	'''
	Functions controls the false discovery rate of a family of hypothesis tests. FDR is
	the expected proportion of rejected hypotheses that are mistakingly rejected 
	(i.e., the null hypothesis is actually true for those tests). FDR is less 
	conservative/more powerfull method for correcting for multiple comparisons than 
	procedures like Bonferroni correction that provide strong control of the familiy-wise
	error rate (i.e. the probability that one or more null hypotheses are mistakingly rejected)

	Arguments
	- - - - - 

	p_vals (array): an array (one or multi-demensional) containing the p_values of each individual
					test in a family f tests
	q (float): the desired false discovery rate
	method (str): If 'pdep' the original Bejnamini & Hochberg (1995) FDR procedure is used, which 
				is guaranteed to be accurate if the individual tests are independent or positively 
				dependent (e.g., Gaussian variables that are positively correlated or independent).  
				If 'dep,' the FDR procedure described in Benjamini & Yekutieli (2001) that is guaranteed 
				to be accurate for any test dependency structure (e.g.,Gaussian variables with any 
				covariance matrix) is used. 'dep' is always appropriate to use but is less powerful than 'pdep.'
	adjust_p (bool): If True, adjusted p-values are computed (can be computationally intensive)	
	report (bool): If True, a brief summary of FDR results is printed 		

	Returns
	- - - -

	h (array): a boolean matrix of the same size as the input p_vals, specifying whether  
			   the test that produced the corresponding p-value is significant
	crit_p (float): All uncorrected p-values less than or equal to crit_p are significant.
					If no p-values are significant, crit_p = 0
	adj_ci_cvrg (float): he FCR-adjusted BH- or BY-selected confidence interval coverage.	
	adj_p (array): All adjusted p-values less than or equal to q are significant. Note, 
				   adjusted p-values can be greater than 1					   
	'''

	orig = p_vals.shape

	# check whether p_vals contains valid input (i.e. between 0 and 1)
	if np.sum(p_vals > 1) or np.sum(p_vals < 0):
		print ('Input contains invalid p values')

	# sort p_values	
	if p_vals.ndim > 1:
		p_vect = np.squeeze(np.reshape(p_vals,(1,-1)))
	else:
		p_vect = p_vals	
	
	sort = np.argsort(p_vect) # for sorting
	rev_sort = np.argsort(sort) # to reverse sorting
	p_sorted = p_vect[sort]

	nr_tests = p_sorted.size
	tests = np.arange(1.0,nr_tests + 1)

	if method == 'pdep': # BH procedure for independence or positive independence
		if report:
			print('FDR/FCR procedure used is guaranteed valid for independent or positively dependent tests')
		thresh = tests * (q/nr_tests)
		wtd_p = nr_tests * p_sorted / tests 
	elif method == 'dep': # BH procedure for any dependency structure
		if report:
			print('FDR/FCR procedure used is guaranteed valid for independent or dependent tests')
		denom = nr_tests * sum(1/tests)
		thresh = tests * (q/denom)
		wtd_p = denom * p_sorted / tests
		# Note this method can produce adjusted p values > 1 (Compute adjusted p values)

	# Chec whether p values need to be adjusted	
	if adjust_p:
		adj_p = np.empty(nr_tests) * np.nan	
		wtd_p_sortidx = np.argsort(wtd_p)
		wtd_p_sorted = wtd_p[wtd_p_sortidx]
		next_fill = 0
		for i in range(nr_tests):
			if wtd_p_sortidx[i] >= next_fill:
				adj_p[next_fill:wtd_p_sortidx[i]+1] = wtd_p_sorted[i]
				next_fill = wtd_p_sortidx[i] + 1
				if next_fill > nr_tests:
					break	
		adj_p = np.reshape(adj_p[rev_sort], (orig))	
	else:
		adj_p = np.nan	

	rej = np.where(p_sorted <= thresh)[0]
		
	if rej.size == 0:
		crit_p = 0
		h = np.array(p_vals * 0, dtype = bool)
		adj_ci_cvrg = np.nan
	else:
		max_idx = rej[-1] # find greatest significant pvalue
		crit_p = p_sorted[max_idx]
		h = p_vals <= crit_p
		adj_ci_cvrg = 1 - thresh[max_idx]

	if report:
		nr_sig = np.sum(p_sorted <= crit_p)
		if nr_sig == 1:
			print('Out of {} tests, {} is significant using a false discovery rate of {}\n'.format(nr_tests,nr_sig,q))
		else:
			print('Out of {} tests, {} are significant using a false discovery rate of {}\n'.format(nr_tests,nr_sig,q))	

	return h, crit_p, adj_ci_cvrg, adj_p	

def signedRankArray(X, Y):
	'''

	Arguments
	- - - - - 

	X1 (array): subject X dim1 X dim2, where dim1 and dim2 can be any type of dimension 
				(time, frequency, electrode, etc). Values in array represent some dependent
				measure (e.g classification accuracy or power)
	X2 (array | float): either a datamatrix with same dimensions as X1, or a single value 
				against which X1 will be tested
	'''

	# check whether X2 is a chance variable or a data array
	if isinstance(Y, (float, int)):
		Y = np.tile(Y, X.shape)

	p_vals = np.ones(X[0].shape)

	for i in range(p_vals.shape[0]):
		for j in range(p_vals.shape[1]):
			_, p_vals[i,j] = wilcoxon(X[:,i,j], Y[:,i,j]) 

	return p_vals		








