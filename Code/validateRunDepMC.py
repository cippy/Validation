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
    parser.add_argument(      "--time-indep", dest="timeIndependent", action="store_true", help = "Run on time independent MC (one run, and possibly other differences)")
    args = parser.parse_args()

    print("\n\n")
    ROOT.TH1.SetDefaultSumw2()
    treename = "Events"

    setLogging(args.verbose)
    
    outdir = args.outdir[0]
    if not outdir.endswith('/'):
        outdir += '/'
    createPlotDirAndCopyPhp(outdir)

    files = []
    if isfile(args.inputdir[0]):
        with open(args.inputdir[0]) as f:
            for line in f:
              files.append(line.strip())  
    else:   
        files = [join(args.inputdir[0], f) for f in listdir(args.inputdir[0]) if isfile(join(args.inputdir[0], f)) and f.endswith(".root")]

    #print(files)
    #quit()
        
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

    print(f"Chain formed: there are {chain.GetEntries()} entries to process")
    print("\n\n")

    lok  = chain.GetListOfLeaves()
    chain.SetBranchStatus("*",0)
    #print("Using these branches")
    for b in lok:
         name = b.GetName()
         if name.startswith("recoMuon"):
             continue
         #if not name.startswith("Ecal") and "EventAuxiliary" not in name and not re.match("^E(B|E)DigiCollection.*",name):
         #    continue
         #EcalRecHitsSorted_reducedEcalRecHitsEE__RECO.obj
         #print(f"{name}")
         chain.SetBranchStatus(name,1)
    print("\n\n")

    nRunBins = 120
    runLow = 314000
    runHigh = 326000
    if args.timeIndependent:
        print("Setting run ranges for a single run in time-independent MC")
        nRunBins = 1
        runLow = 0.0
        runHigh = 10.0
        
    
    model_runNumber = ROOT.TH1D("runNumber","run number", nRunBins, runLow, runHigh)

    # doesn't work as expected when filling histograms
    #model_EBreducedRechit = ROOT.TH3D("EBreducedRechit", ";run number;number of reduced EB RecHits;energy of reduced EB RecHits (GeV)", 
    #                                  nRunBins, runLow, runHigh, 50, 0, 1000, 60, 0, 15)

    model_energyPFRechit_run = ROOT.TH2D("energyPFRechit_run", ";run number;energy of PFRecHits (GeV);Events", 
                                         nRunBins, runLow, runHigh, 60, 0, 15)
    

    model_numberEBreducedRechit_run = ROOT.TH2D("numberEBreducedRechit_run", ";run number;number of reduced EB RecHits;Events", 
                                                nRunBins, runLow, runHigh, 50, 0, 1000)
    model_numberEEreducedRechit_run = ROOT.TH2D("numberEEreducedRechit_run", ";run number;number of reduced EE RecHits;Events", 
                                                nRunBins, runLow, runHigh, 50, 0, 1000)
    model_energyEBreducedRechit_run = ROOT.TH2D("energyEBreducedRechit_run", ";run number;energy of reduced EB RecHits (GeV);Events", 
                                                nRunBins, runLow, runHigh, 60, 0, 15)
    model_energyEEreducedRechit_run = ROOT.TH2D("energyEEreducedRechit_run", ";run number;energy of reduced EE RecHits (GeV);Events", 
                                                nRunBins, runLow, runHigh, 60, 0, 15)
    model_numberEBrechit_run = ROOT.TH2D("numberEBrechit_run", ";run number;number of EB RecHits;Events", 
                                         nRunBins, runLow, runHigh, 100, 500, 2500)
    model_numberEErechit_run = ROOT.TH2D("numberEErechit_run", ";run number;number of EE RecHits;Events", 
                                         nRunBins, runLow, runHigh, 75, 0, 1500)
    model_energyEBrechit_run = ROOT.TH2D("energyEBrechit_run", ";run number;energy of EB RecHits (GeV);Events", 
                                         nRunBins, runLow, runHigh, 60, 0, 15)
    model_energyEErechit_run = ROOT.TH2D("energyEErechit_run", ";run number;energy of EE RecHits (GeV);Events", 
                                         nRunBins, runLow, runHigh, 60, 0, 15)


    model_numberBasicClusterEB_run = ROOT.TH2D("numberBasicClusterEB__run", ";run number;number of EB basic clusters;Events", 
                                               nRunBins, runLow, runHigh, 50, 0, 50)
    model_etaBasicClusterEB_run = ROOT.TH2D("etaBasicClusterEB__run", ";run number;#eta of EB basic clusters;Events", 
                                            nRunBins, runLow, runHigh, 40, -1.5, 2.5)
    model_energyBasicClusterEB_run = ROOT.TH2D("energyBasicClusterEB__run", ";run number;energy of EB basic clusters (GeV);Events", 
                                               nRunBins, runLow, runHigh, 100, 0, 100)


    model_numberBasicClusterEE_run = ROOT.TH2D("numberBasicClusterEE__run", ";run number;number of EE basic clusters;Events", 
                                               nRunBins, runLow, runHigh, 50, 0, 50)
    model_etaBasicClusterEE_run = ROOT.TH2D("etaBasicClusterEE__run", ";run number;#eta of EE basic clusters;Events", 
                                            nRunBins, runLow, runHigh, 70, -3.0, 4.0)
    model_energyBasicClusterEE_run = ROOT.TH2D("energyBasicClusterEE__run", ";run number;energy of EE basic clusters (GeV);Events", 
                                               nRunBins, runLow, runHigh, 100, 0, 100)
    
    # model_numberEBdigi_run = ROOT.TH2D("numberEBdigi_run", ";run number;number of EB Digi;Events", 
    #                                      nRunBins, runLow, runHigh, 50, 0, 200)
    # model_numberEEdigi_run = ROOT.TH2D("numberEEdigi_run", ";run number;number of EE Digi;Events", 
    #                                      nRunBins, runLow, runHigh, 50, 0, 200)

    histsAndExprs = {model_runNumber      : ["EventAuxiliary.run()", "skipStatBox"],

                     #model_EBreducedRechit : ["EcalRecHitsSorted_reducedEcalRecHitsEB__RECO.obj.obj.energy():EcalRecHitsSorted_reducedEcalRecHitsEB__RECO.obj.size():EventAuxiliary.run()","logz"]

                     model_energyPFRechit_run : ["recoPFRecHits_particleFlowRecHitECAL_Cleaned_RECO.obj.energy():EventAuxiliary.run()", "logz"],
                     
                     model_numberEBreducedRechit_run : ["EcalRecHitsSorted_reducedEcalRecHitsEB__RECO.obj.size():EventAuxiliary.run()"],
                     model_numberEEreducedRechit_run : ["EcalRecHitsSorted_reducedEcalRecHitsEE__RECO.obj.size():EventAuxiliary.run()"],
                     model_energyEBreducedRechit_run : ["EcalRecHitsSorted_reducedEcalRecHitsEB__RECO.obj.obj.energy():EventAuxiliary.run()", "logz"],
                     model_energyEEreducedRechit_run : ["EcalRecHitsSorted_reducedEcalRecHitsEE__RECO.obj.obj.energy():EventAuxiliary.run()", "logz"],
                     model_numberEBrechit_run : ["EcalRecHitsSorted_ecalRecHit_EcalRecHitsEB_RECO.obj.size():EventAuxiliary.run()"],
                     model_numberEErechit_run : ["EcalRecHitsSorted_ecalRecHit_EcalRecHitsEE_RECO.obj.size():EventAuxiliary.run()"],
                     model_energyEBrechit_run : ["EcalRecHitsSorted_ecalRecHit_EcalRecHitsEB_RECO.obj.obj.energy():EventAuxiliary.run()", "logz"],
                     model_energyEErechit_run : ["EcalRecHitsSorted_ecalRecHit_EcalRecHitsEE_RECO.obj.obj.energy():EventAuxiliary.run()", "logz"],
                     # #model_numberEBdigi_run : ["EBDigiCollection_selectDigi_selectedEcalEBDigiCollection_RECO.obj.size():EventAuxiliary.run()", "logz"],
                     # #model_numberEEdigi_run : ["EEDigiCollection_selectDigi_selectedEcalEEDigiCollection_RECO.obj.size():EventAuxiliary.run()", "logz"],
                     model_numberBasicClusterEB_run : ["recoCaloClusters_particleFlowSuperClusterECAL_particleFlowBasicClusterECALBarrel_RECO.obj.size():EventAuxiliary.run()", "logz"],
                     model_etaBasicClusterEB_run : ["recoCaloClusters_particleFlowSuperClusterECAL_particleFlowBasicClusterECALBarrel_RECO.obj.eta():EventAuxiliary.run()"],
                     model_energyBasicClusterEB_run : ["recoCaloClusters_particleFlowSuperClusterECAL_particleFlowBasicClusterECALBarrel_RECO.obj.energy():EventAuxiliary.run()", "logz"],
                     model_numberBasicClusterEE_run : ["recoCaloClusters_particleFlowSuperClusterECAL_particleFlowBasicClusterECALEndcap_RECO.obj.size():EventAuxiliary.run()", "logz"],
                     model_etaBasicClusterEE_run : ["recoCaloClusters_particleFlowSuperClusterECAL_particleFlowBasicClusterECALEndcap_RECO.obj.eta():EventAuxiliary.run()"],
                     model_energyBasicClusterEE_run : ["recoCaloClusters_particleFlowSuperClusterECAL_particleFlowBasicClusterECALEndcap_RECO.obj.energy():EventAuxiliary.run()", "logz"],
    }

    
    canvas   = ROOT.TCanvas("canvas","", 800,800)
    canvas1D = ROOT.TCanvas("canvas1D","", 900,800)
    canvas1Dshort = ROOT.TCanvas("canvas1Dshort","", 800,700)
    adjustSettings_CMS_lumi()

    runBins = []
    nIOV = 1

    foutname = outdir + "allHistograms.root"
    fout = ROOT.TFile.Open(foutname, "RECREATE")
    fout.cd()
    
    for h,extra in histsAndExprs.items():

        expr = extra[0]
        opts = extra[1:] if len(extra) > 1 else []
        logging.info(f"Processing {h.GetName()}")
        chain.Draw(f"{expr}>>{h.GetName()}", "1", "goff")
        h.SetDirectory(0)

        if h.Integral() == 0.0:
            logging.warning(f"{h.GetName()} has no entries, please check! It will be skipped")
            if h.GetDimension() == 1 and h.Integral(0, 1+h.GetNbinsX()) > 0.0:
                logging.warning(f"There seems to be events in the under/overflow bins, though, so check the range")
            continue
        
        if h.GetName() == "runNumber":
            for i in range(1, 1+h.GetNbinsX()):
                if h.GetBinContent(i) > 0:
                    runBins.append(i)
            nIOV = len(runBins)
                    
        if h.GetDimension() == 1:

            drawTH1(h, h.GetTitle(),
                    "Events", outdir, h.GetName(),
                    passCanvas=canvas1Dshort,
                    skipStatBox=True if "skipStatBox" in opts else False,
                    setLogy=True if "logy" in opts else False
            )
            h.Write()
            
        elif h.GetDimension() == 2:

            drawCorrelationPlot(h,
                                h.GetXaxis().GetTitle(), h.GetYaxis().GetTitle(), h.GetZaxis().GetTitle(),
                                h.GetName(), outdir=outdir, drawProfileX=True,
                                draw_both0_noLog1_onlyLog2=2 if "logz" in opts else 1,
                                passCanvas=canvas, palette=57, skipLumi=True)            
            hists = [h.ProjectionY(f"{h.GetName()}_projY_IOV{i+1}",runBins[i],runBins[i],"e") for i in range(nIOV)]
            legEntries = [f"IOV {i+1}" for i in range(nIOV)]
            if len(hists) == 1:
                drawTH1(hists[0], h.GetYaxis().GetTitle(),
                        "Events", outdir, hists[0].GetName(),
                        passCanvas=canvas1Dshort,
                        skipStatBox=True if "skipStatBox" in opts else False,
                        setLogy=True if "logy" in opts else False
                )
            else:
                drawNTH1(hists, legEntries, h.GetYaxis().GetTitle(), h.GetZaxis().GetTitle(),
                         f"{h.GetName()}_projY", outdir=outdir, draw_both0_noLog1_onlyLog2=2 if "logz" in opts else 1,
                         labelRatioTmp="IOV_{N} / IOV_{1}::0.5,1.5",
                         legendCoords="0.75,0.95,0.4,0.9", lowerPanelHeight=0.3, passCanvas=canvas1D,
                         skipLumi=True, drawLineMarkerAsPalette=True, palette=105)

            h.Write()
            for hist in hists:
                hist.Write()
            
        elif h.GetDimension() == 3:

            ####
            #### Doesn't work as expected when filling histograms
            
            # Y vs X (number vs run)
            projYvsX = getTH2fromTH3(h, f"{h.GetName()}_number_run", binStart=1, binEnd=h.GetNbinsZ(), proj="yxe")
            drawCorrelationPlot(projYvsX,
                                projYvsX.GetXaxis().GetTitle(), projYvsX.GetYaxis().GetTitle(), "Events",
                                projYvsX.GetName(), outdir=outdir, drawProfileX=True,
                                draw_both0_noLog1_onlyLog2=2 if "logy" in opts else 1,
                                passCanvas=canvas, palette=57, skipLumi=True)            
            hists = [projYvsX.ProjectionY(f"{projYvsX.GetName()}_projY_IOV{i+1}",runBins[i],runBins[i],"e") for i in range(nIOV)]
            legEntries = [f"IOV {i+1}" for i in range(nIOV)]
            drawNTH1(hists, legEntries, projYvsX.GetYaxis().GetTitle(), "Events",
                     f"{projYvsX.GetName()}_projY", outdir=outdir, draw_both0_noLog1_onlyLog2=2 if "logy" in opts else 1,
                     legendCoords="0.75,0.95,0.4,0.9", lowerPanelHeight=0.0, passCanvas=canvas1D,
                     skipLumi=True, drawLineMarkerAsPalette=True, palette=105)

            h.Write()
            projYvsX.Write()
            for hist in hists:
                hist.Write()
            
            # Z vs X (energy vs run)
            projZvsX = getTH2fromTH3(h, f"{h.GetName()}_energy_run", binStart=-1, proj="zxe")
            drawCorrelationPlot(projZvsX,
                                projZvsX.GetXaxis().GetTitle(), projZvsX.GetZaxis().GetTitle(), "Events",
                                projZvsX.GetName(), outdir=outdir, drawProfileX=True,
                                draw_both0_noLog1_onlyLog2=2 if "logz" in opts else 1,
                                passCanvas=canvas, palette=57, skipLumi=True)            
            hists = [projZvsX.ProjectionY(f"{projZvsX.GetName()}_projY_IOV{i+1}",runBins[i],runBins[i],"e") for i in range(nIOV)]
            legEntries = [f"IOV {i+1}" for i in range(nIOV)]
            drawNTH1(hists, legEntries, projZvsX.GetZaxis().GetTitle(), "Events",
                     f"{projZvsX.GetName()}_projY", outdir=outdir, draw_both0_noLog1_onlyLog2=2 if "logz" in opts else 1,
                     legendCoords="0.75,0.95,0.4,0.9", lowerPanelHeight=0.0, passCanvas=canvas1D,
                     skipLumi=True, drawLineMarkerAsPalette=True, palette=105)

            projZvsX.Write()
            for hist in hists:
                hist.Write()

    fout.Close()
    print(f"All histograms saved in file {foutname}")
    print()
