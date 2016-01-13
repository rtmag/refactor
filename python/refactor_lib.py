import os
import sys
from sklearn import preprocessing
from numpy import dot, linalg, sqrt, loadtxt
import pca

class Refactor( object ):
    RANKED_FILENAME =       'refactor.out.rankedlist.txt'
    COMPONENTS_FILENAME =   'refactor.out.components.txt'
    VERSION = 1.0 

    def __init__( self,
                  methylation_data,
                  k,
                  t = 500,
                  num_components = None, 
                  ranked_output_filename = RANKED_FILENAME,
                  components_output_filename = COMPONENTS_FILENAME
                ):
        
        self.meth_data = methylation_data
        
        # validate and process all variables
        self.k =                          self._validate_k(k)
        self.t =                          self._validate_t(t)
        self.num_components =             self._validate_num_comp(num_components)
        self.ranked_output_filename =     ranked_output_filename
        self.components_output_filename = components_output_filename

        self.run()


    def _validate_file_path(self, filepath):
        if not os.path.exists(filepath) :
            print("ERROR: The file '%s' doesn't exist. Exiting" % filepath)
            self._terminate_refactor()

    def _load_and_validate_file_of_dimentions(self, filepath, dim):
        if filepath is None:
            return None

        self._validate_file_path(filepath)
        print("Loading file %s..." % filepath)
        data = loadtxt(filepath, dtype = str)

        if len(data.shape) != dim:
            print("ERROR: The file '%s' is not a %sd matrix" % (filepath, dim))
            self._terminate_refactor()

        return data

    def _validate_k(self,k):
        if not (k >= 2 and k <= self.meth_data.samples_size):
            print("ERROR: k must be at least 2 and smaller than the number of samples. k = %s, samples = %s" % (k, self.meth_data.samples_size))
            self._terminate_refactor()

        return k

    def _validate_t(self,t):
        if t > self.meth_data.sites_size or t < self.k : 
            print("ERROR: t cannot be greater than the number of sites or smaller than k . t = %s, sites = %s, k = %s" % (t, self.meth_data.sites_size, self.k))
            self._terminate_refactor()

        return t

    def _validate_num_comp(self,num_comp):
        if num_comp and not (num_comp >= self.k and num_comp <= self.meth_data.samples_size):
            print("ERROR: the number of components must be at least k and smaller than the number of samples. num_comp = %s, samples = %s, k = %s" % (self.t, self.meth_data.samples_size, self.k))
            self._terminate_refactor()

        return num_comp if num_comp else self.k

    def run( self ):
        print('Starting ReFACTor v%s...' % self.VERSION);
        self.components, self.ranked_sites, self.standard_pca = self._refactor()
        print('ReFACTor is Done!')

   
    def _write_file( self, filepath, data):   
        if  os.path.exists(filepath):
            os.remove(filepath) 
        with open(filepath, 'w') as f:
            f.write(data)

    def _refactor( self ):
        print('Running a standard PCA...')
        pca_out1 = pca.PCA(self.meth_data.data.transpose()) 

        print('Computing a low rank approximation of the input data and ranking sites...')
        x = self._low_rank_approximation(pca_out1.P, pca_out1.U, self.k)
        
        An = preprocessing.StandardScaler( with_mean = True, with_std = False ).fit(self.meth_data.data.transpose()).transform(self.meth_data.data.transpose())
        Bn = preprocessing.StandardScaler( with_mean = True, with_std = False ).fit(x).transform(x)
        An = An * ( 1 / sqrt((An**2).sum(axis=0)) ) 
        Bn = Bn * ( 1 / sqrt((Bn**2).sum(axis=0)) )

        distances = self._euclidean_distance(An, Bn)
        ranked_list = distances.argsort()

        print('Computing the ReFACTor components...')
        sites = ranked_list[0:self.t]

        pca_out2 = pca.PCA(self.meth_data.data[sites,:].transpose())
        score = pca_out2.P

        print('Saving a ranked list of the data features...')
        data = '\n'.join(['%s\t%s'% (index+1, self.meth_data.cpgnames[index]) for index in ranked_list])
        self._write_file(self.ranked_output_filename, data)

        print('Saving the ReFACTor components...')
        data = '\n'.join(['\t'.join([str(i) for i in line]) for line in score[:,0:self.num_components   ]])
        self._write_file(self.components_output_filename, data)
        
        return score[:,0:self.num_components], ranked_list, pca_out1.P[:,0:self.k]


    def _low_rank_approximation(self, A, B, i):
        return dot(A[:,0:i], B[:,0:i].transpose())

    def _euclidean_distance(self, A, B):
        return sqrt(((A - B)**2).sum(axis=0))

    def _terminate_refactor(self):
        print("ReFACTor was terminated.")
        exit(2)
