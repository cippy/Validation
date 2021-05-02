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

ROOT.gInterpreter.ProcessLine(".O3")
ROOT.ROOT.EnableImplicitMT()

#ROOT.gSystem.Load("libFWCoreFWLite")
#ROOT.FWLiteEnabler.enable()
#ROOT.gSystem.Load("libDataFormatsFWLite")
#ROOT.gSystem.Load("libDataFormatsPatCandidates")
ROOT.gROOT.ProcessLine(f".L {os.environ['HOME']}/rootlogon.C")

#/cvmfs/cms.cern.ch/slc7_amd64_gcc900/cms/cmssw/CMSSW_11_3_0_pre3/src
#ROOT.gInterpreter.Declare('#include "DataFormats/EcalRecHit/interface/EcalRecHit.h"')
#ROOT.gInterpreter.Declare('#include "DataFormats/Common/interface/SortedCollection.h"')
#from DataFormats.FWLite import *

def setLogging(verbosity):
    verboseLevel = [logging.CRITICAL, logging.ERROR, logging.WARNING, logging.INFO, logging.DEBUG]
    logging.basicConfig(format='%(levelname)s: %(message)s', level=verboseLevel[min(4,verbosity)])
    
def compileMacro(x,basedir=os.environ['PWD']):
    #ROOT.gROOT.ProcessLine(".L %s/%s+" % (os.environ['CMSSW_BASE'],x));
    success = ROOT.gSystem.CompileMacro("%s" % (x),"k")
    if not success:
        logging.error("Loading and compiling %s failed! Exit" % x)
        quit()

if "/functions_cc.so" not in ROOT.gSystem.GetLibraries():
   compileMacro("ccFiles/functions.cc")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("inputdir",  type=str, nargs=1)
    parser.add_argument("outdir",    type=str, nargs=1)
    parser.add_argument("-n", "--n-files", dest="nMaxFiles", type=int, default=0, help = "If positive, select how many files to use (default is to use all)")
    parser.add_argument("-v", "--verbose", type=int, default=3, choices=[0,1,2,3,4], help="Set verbosity level with logging, the larger the more verbose")
    args = parser.parse_args()

    print("\n\n")
    ROOT.TH1.SetDefaultSumw2()
    treename = "Events"

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

    chain = ROOT.TChain(treename)
    
    logging.debug('='*30)
    logging.debug("Printing files to process")
    logging.debug('-'*30)
    for n in files:
        if n.startswith("/store/"):
            name = f"root://xrootd-cms.infn.it//{n}"
        elif n.startswith("/eos/cms/"):
            name = n.replace('/eos/cms/','root://eoscms.cern.ch//')
        else:
            name = n
        logging.debug(name)
        chain.Add(name)
    logging.debug('='*30)

    print(f"Chain formed: there are {chain.GetEntries()} to process")
    print("\n\n")

    lok  = chain.GetListOfLeaves()
    chain.SetBranchStatus("*",0)
    print("Using these branches")
    for b in lok:
        name = b.GetName()
        if not name.startswith("Ecal") and "EventAuxiliary" not in name:
            continue
        #EcalRecHitsSorted_reducedEcalRecHitsEE__RECO.obj
        print(f"{name}")
        chain.SetBranchStatus(name,1)
    print("\n\n")

    model_runNumber = ROOT.TH1D("runNumber","run number", 120, 314000, 326000)
    #model_numberEBrechit = ROOT.TH1D("numberEBrechit","number of EB RecHits", 100, 0, 1000)
    #model_numberEErechit = ROOT.TH1D("numberEErechit","number of EE RecHits", 100, 0, 1000)
    #model_energyEBrechit = ROOT.TH1D("energyEBrechit","energy of EB RecHits", 100, 0, 15)    
    #model_energyEErechit = ROOT.TH1D("energyEErechit","energy of EE RecHits", 100, 0, 15)

    model_numberEBrechit_run = ROOT.TH2D("numberEBrechit_run", ";run number;number of EB RecHits;Events", 
                                         120, 314000, 326000, 100, 0, 1000)
    model_numberEErechit_run = ROOT.TH2D("numberEErechit_run", ";run number;number of EE RecHits;Events", 
                                         120, 314000, 326000, 100, 0, 1000)
    model_numberESrechit_run = ROOT.TH2D("numberESrechit_run", ";run number;number of ES RecHits;Events", 
                                         120, 314000, 326000, 100, 0, 1000)
    model_energyEBrechit_run = ROOT.TH2D("energyEBrechit_run", ";run number;energy of EB RecHits;Events", 
                                         120, 314000, 326000, 100, 0, 15)
    model_energyEErechit_run = ROOT.TH2D("energyEErechit_run", ";run number;energy of EE RecHits;Events", 
                                         120, 314000, 326000, 100, 0, 15)
    model_numberTrigPrimDigi_run = ROOT.TH2D("numberTrigPrimDigi_run", ";run number;number of trig.prim. Digis;Events", 
                                             120, 314000, 326000, 100, 0, 15)
    #model_energyESrechit_run = ROOT.TH2D("energyESrechit_run", ";run number;energy of ES RecHits;Events", 
    #                                     120, 314000, 326000, 100, 0, 15)

    # EcalRecHitsSorted_ecalPreshowerRecHit_EcalRecHitsES_RECO.obj
    histsAndExprs = {model_runNumber      : ["EventAuxiliary.run()", "skipStatBox"],
                     #model_numberEBrechit : ["EcalRecHitsSorted_reducedEcalRecHitsEB__RECO.obj.size()"],
                     #model_numberEErechit : ["EcalRecHitsSorted_reducedEcalRecHitsEE__RECO.obj.size()"],
                     #model_energyEBrechit : ["EcalRecHitsSorted_reducedEcalRecHitsEB__RECO.obj.obj.energy()", "logy"],
                     #model_energyEErechit : ["EcalRecHitsSorted_reducedEcalRecHitsEE__RECO.obj.obj.energy()", "logy"],
                     model_numberEBrechit_run : ["EcalRecHitsSorted_reducedEcalRecHitsEB__RECO.obj.size():EventAuxiliary.run()"],
                     model_numberEErechit_run : ["EcalRecHitsSorted_reducedEcalRecHitsEE__RECO.obj.size():EventAuxiliary.run()"],
                     model_numberESrechit_run : ["EcalRecHitsSorted_reducedEcalRecHitsES__RECO.obj.size():EventAuxiliary.run()"],
                     model_energyEBrechit_run : ["EcalRecHitsSorted_reducedEcalRecHitsEB__RECO.obj.obj.energy():EventAuxiliary.run()", "logz"],
                     model_energyEErechit_run : ["EcalRecHitsSorted_reducedEcalRecHitsEE__RECO.obj.obj.energy():EventAuxiliary.run()", "logz"],
                     #model_energyESrechit_run : ["EcalRecHitsSorted_reducedEcalRecHitsES__RECO_obj.product().energy():EventAuxiliary.run()", "logz"],
                     model_numberTrigPrimDigi_run : ["EcalTrigPrimCompactColl_ecalCompactTrigPrim__RECO_obj.size():EventAuxiliary.run()"],
    }

    canvas   = ROOT.TCanvas("canvas","", 700,800)
    canvas1D = ROOT.TCanvas("canvas1D","", 800,700)
    adjustSettings_CMS_lumi()

    runBins = []
    nIOV = 1
    
    for h,extra in histsAndExprs.items():

        expr = extra[0]
        opts = extra[1:] if len(extra) > 1 else []
        logging.info(f"Processing {h.GetName()}")
        chain.Draw(f"{expr}>>{h.GetName()}", "1", "goff")
        h.SetDirectory(0)

        if h.Integral() == 0.0:
            logging.warning(f"{h.GetName()} has no entries, please check! It will be skipped")
            continue
        
        if h.GetName() == "runNumber":
            for i in range(1, 1+h.GetNbinsX()):
                if h.GetBinContent(i) > 0:
                    runBins.append(i)
            nIOV = len(runBins)
                    
        if h.GetDimension() == 1:
            drawTH1(h, h.GetTitle(),
                    "Events", outdir, h.GetName(),
                    passCanvas=canvas1D,
                    skipStatBox=True if "skipStatBox" in opts else False,
                    setLogy=True if "logy" in opts else False
            )
        elif h.GetDimension() == 2:
            drawCorrelationPlot(h,
                                h.GetXaxis().GetTitle(), h.GetYaxis().GetTitle(), h.GetZaxis().GetTitle(),
                                h.GetName(), outdir=outdir, drawProfileX=True,
                                draw_both0_noLog1_onlyLog2=2 if "logz" in opts else 1,
                                passCanvas=canvas, palette=57, skipLumi=True)            
            hists = [h.ProjectionY(f"{h.GetName()}_projY_IOV{i+1}",runBins[i],runBins[i]) for i in range(nIOV)]
            legEntries = [f"IOV {i+1}" for i in range(nIOV)]
            drawNTH1(hists, legEntries, h.GetYaxis().GetTitle(), h.GetZaxis().GetTitle(),
                     f"{h.GetName()}_projY", outdir=outdir, draw_both0_noLog1_onlyLog2=2 if "logz" in opts else 1,
                     legendCoords="0.75,0.95,0.4,0.9", lowerPanelHeight=0.0, passCanvas=canvas1D,
                     skipLumi=True, drawLineMarkerAsPalette=True, palette=105)
