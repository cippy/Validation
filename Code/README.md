## Dumb code to make plots

To make plots from run-dependent MC samples.

### Get code
```
export SCRAM_ARCH="slc7_amd64_gcc900"
cmsrel CMSSW_11_3_0_pre3
cd CMSSW_11_3_0_pre3/src
cmsenv
git clone git@github.com:cippy/Validation.git Validation/
cd Validation/
YOUR_GITHUB_REPOSITORY=$(git config user.github)
git remote add origin git@github.com:$YOUR_GITHUB_REPOSITORY/Validation.git
git push -u origin master
# create link to your web page. Usually EOS, but can be anywhere you like
ln -sv /eos/user/m/$USER/www/validationRunDepMC/ plots
```

### Get files from DAS

For time-dependent MC
```
dasgoclient -query="file dataset=/RelValZEE_13UP18_RD/CMSSW_11_3_0_pre3-113X_upgrade2018_realistic_RD_v3_RunDep_HS-v1/GEN-SIM-RECO" > files_RelValZEE_13UP18_RD_runDep.txt
```
The file files_RelValZEE_13UP18_RD_runDep.txt is already committed in this repository


### Run the code
If the files are saved locally (which ensures a much faster processing, waaay faster...), you can use the following command specifying where to find the root files (e.g. let's assume they are in __myFiles/RelValZEE_13UP18_runDepMC/__
```
python3 validateRunDepMC.py myFiles/RelValZEE_13UP18_runDepMC/ plots/checks/ -v 4 [-n 1]
```
option __-n__ allows you to specify a subset of the files, for a quick test.
If the files are not stored locally, you can use a txt file as first argument, with the list of files to be processed. E.g.
```
python3 validateRunDepMC.py files_RelValZEE_13UP18_RD_runDep.txt plots/checks/ -v 4 [-n 1]
```

### To do

The code is currently based on TTree::Draw, which is highly inefficient for advanced manipulation of branches with non basic C++ types. Also, one call to Draw is needed for each histogram, which makes it slow when having to make multiple plots.
- Add simultaneous processing of time-independent MC (list of files to be taken from DAS), so to make comparison
- Move some histograms from TH2 to TH3 (e.g. objectEnergy vs numberOfObject vs run), so to gain in flexibility with counting events for different energy thresholds (and having a single call to Draw rather than two for the same base collection)
- save histograms in a root file to be able to use that when only changing plotting style and details, to avoid reprocessing the samples everytime (new distributions can be added by updating the file, no need to run the already existing ones if they didn't change) 

For a better setup, consider the following possibilities.
- Write a C++ EDMAnalyzer with usual python configuration file to be used with cmsRun (should be much faster to process, and more flexible than the current python setup)
- Alternatively, move to an RDataFrame setup to exploit an efficient C++ interface within python (but need to be careful with including appropriate header files and similar cmssw stuff). A big advantage over the TTree::Draw is that the RDF loop is run only once, after booking all histograms.
