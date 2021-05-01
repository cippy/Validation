#!/usr/bin/env python3

import re
import os, os.path
import logging
import argparse
import shutil

from os import listdir
from os.path import isfile, join

## safe batch mode
import sys
args = sys.argv[:]
sys.argv = ['-b']
import ROOT
sys.argv = args
ROOT.gROOT.SetBatch(True)
ROOT.PyConfig.IgnoreCommandLineOptions = True

from plotUtils.utility import *

def setLogging(verbosity):
    verboseLevel = [logging.CRITICAL, logging.ERROR, logging.WARNING, logging.INFO, logging.DEBUG]
    logging.basicConfig(format='%(levelname)s: %(message)s', level=verboseLevel[min(4,verbosity)])

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("inputdir",  type=str, nargs=1)
    parser.add_argument("outdir",    type=str, nargs=1)
    parser.add_argument("-n", "--n-files", dest="nMaxFiles", type=int, default=0, help = "If positive, select how many files to use (default is to use all)")
    parser.add_argument("-v", "--verbose", type=int, default=3, choices=[0,1,2,3,4], help="Set verbosity level with logging, the larger the more verbose")
    args = parser.parse_args()

    ROOT.TH1.SetDefaultSumw2()

    setLogging(args.verbose)
    
    outdir = args.outdir[0]
    if not outdir.endswith('/'):
        outdir += '/'
    createPlotDirAndCopyPhp(outdir)

    files = [join(args.inputdir[0], f) for f in listdir(args.inputdir[0]) if isfile(join(args.inputdir[0], f)) and f.endswith(".root")]

    if args.nMaxFiles > 0:
        files = files[:args.nMaxFiles]
    logging.debug(len(files))
    #for f in files:
    #    print(f)


    # Eflow tree
    filename = files[0]
    rf = ROOT.TFile.Open(filename,'read')        
    if not rf or rf.IsZombie():
        print(f"ERROR! Unable to open file {filename}")
        quit()
    treename = "Events"
    t = rf.Get(treename)
    if not t:
        print(f"ERROR! Unable to get tree {treename} in {filename}")
        quit()

    ievent = 0
    for event in t:
        print(f"{ievent}")
        ievent += 1
        
