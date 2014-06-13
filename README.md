#Correction Detector

The package compares an input sentence with its revision and figure out what errors have been corrected.

##Installation
###Prerequisites
My package uses the Maximum Entropy classifier which can be found [HERE](http://homepages.inf.ed.ac.uk/lzhang10/maxent_toolkit.html). Please make sure that you installed the Python extension. 

###Installing my code
First, please download my code with [git](http://git-scm.com/). First please compile my editdistalign package, which is a C implementation of the edit distance algorithm.
	
	./compile_editdistalign.sh

Now you should be good to go. You may test running my program:

	python corr_ext.py 

It should print something like this.

	[('RV', 1, 2, 'love')]
	[('X', 1, 4, 'love')]


##Citing the Correction Detector

The detector was described in our paper in ACL 2014. Please feel free to use the following citation information:

    @inproceedings{XueAndHwaACL2014,
      title={Improved Correction Detection in Revised {ESL} Sentences},
      author={Xue, Huichao and Hwa, Rebecca},
      booktitle={Proceedings of the 52nd Annual Meeting of the Association for Computational Linguistics (ACL)},
      year={2014},
      address   = {Baltimore, MD, USA},
      organization={Association for Computational Linguistics}
    }
	
Note that I trained the models for correction extraction and error type selection on FCE corpus [Here](http://ilexir.co.uk/applications/clc-fce-dataset/). Please review their licence terms before using this software package.


##References
1. Yannakoudakis, H., Briscoe, T., & Medlock, B. (2011, June). A new dataset and method for automatically grading ESOL texts. In Proceedings of the 49th Annual Meeting of the Association for Computational Linguistics: Human Language Technologies-Volume 1 (pp. 180-189). Association for Computational Linguistics.
Chicago	
2. Swanson, B., & Yamangil, E. (2012, June). Correction detection and error type selection as an ESL educational aid. In Proceedings of the 2012 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies (pp. 357-361). Association for Computational Linguistics.
