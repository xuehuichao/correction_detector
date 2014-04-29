#Correction Detector

The package compares an input sentence with its revision and figure out what errors have been corrected.

##Installation
Install the MaxEnt classifier at http://homepages.inf.ed.ac.uk/lzhang10/maxent_toolkit.html

This is the maxent classifier I used in my package. Please make sure that you installed the Python extension.

###Prerequisites

###Installing my code
Suppose you are currently in directory /home/XXX/softwares, and you would like to install my packages in /home/XXX/softwares/wrapped_up

tar xzvf wrapped_up.tar.gz
cd wrapped_up/editdistalign   ## This is my edit distance algorithm, written in C
sudo python setup.py install  ## to install the edit-distance package on your computer. If you are installing this package on the departmental machine, please make sure 1) remove "sudo" 2) your PYTHONPATH was set correctly
cd ../../

Now you should be good to go. You may test running my program:

python wrapped_up/corr_ext.py 

It should print something like this.

[('RV', 1, 2, 'love')]
[('X', 1, 4, 'love')]


I trained the models for correction extraction and error type selection on FCE corpus http://ilexir.co.uk/applications/clc-fce-dataset/. Please refer to their licence terms before using this software package.


##References
* Yannakoudakis, H., Briscoe, T., & Medlock, B. (2011, June). A new dataset and method for automatically grading ESOL texts. In Proceedings of the 49th Annual Meeting of the Association for Computational Linguistics: Human Language Technologies-Volume 1 (pp. 180-189). Association for Computational Linguistics.
Chicago	
* Swanson, B., & Yamangil, E. (2012, June). Correction detection and error type selection as an ESL educational aid. In Proceedings of the 2012 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies (pp. 357-361). Association for Computational Linguistics.
