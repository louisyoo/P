#! /usr/bin/python
import os
import functools
import fnmatch
from os.path import *
import ntpath
import sys
import shutil
import re
import argparse
import generate_project
from subprocess import *
from errno import *
from common import *

def die(s):
    print(s)
    sys.exit(-1)

parser = argparse.ArgumentParser(description='Execute the specified P Tests')
parser.add_argument("input", metavar='input.p', type=str, help="the P file we are compiling")
parser.add_argument("output", metavar='<output dir>', type=str, help="output dir")

parser.add_argument("--zc", action='store_const', dest='zc', const=True, \
    default=False, help="run ZingCompiler on generated code")
parser.add_argument("--proj", action='store_const', dest='proj', const=True,
    default=False, help="generate a VisualStudio project for generated C Code")
parser.add_argument("--cc", action='store_const', dest='cc', const=True,
    default=False, help="Build Generated C Code")

args = parser.parse_args()

if (args.cc and not args.proj):
    die("Cannot build code without generating VS Project first. Are you missing a --proj?")

scriptDir = dirname(realpath(__file__))
baseDir = realpath(join(scriptDir, ".."))

zc=join(baseDir, "Compiler", "zc");
zinger=join(baseDir, "Compiler", "Zinger");
pc=join(baseDir, "Compiler", "PCompiler");

stateCoverage=join(baseDir, "Ext", "Zing", "StateCoveragePlugin.dll")
sched=join(baseDir, "Ext", "Zing", "RandomDelayingScheduler.dll")
cc="MSBuild.exe"

pFile = args.input
out=args.output
name = os.path.splitext(os.path.basename(pFile))[0]

zingRT=join(baseDir, "Runtime", "SMRuntime.zing");
cInclude=join(baseDir, "Runtime");
cLib=join(baseDir, "Runtime");
pData=join(baseDir, "Compiler");

zingFile = "output.zing"
zingDll = name + ".dll"
proj = join(out, name + ".vcxproj")
binary = join(out, "Debug", name+ ".exe")

def dumpOutput(s):
    for l in str(s).split("\\r\\n"):
        print(l)

try:
    print("Running PCompiler")
    check_output([pc, '/doNotErase', pFile, pData, '/outputDir:' + out])

    if (args.zc):
        print("Running zc")
        shutil.copy(zingRT, join(out, "SMRuntime.zing"));
        check_output([zc, "-nowarning:292", zingFile, "SMRuntime.zing", '/out:' + zingDll], \
            cwd=out)
        os.remove(join(out, "SMRuntime.zing"));

    if (args.proj):
        mainM = re.search("main[\w\s]*machine[\s]*([\w]*)", \
                          open(pFile).read()).groups()[0]

        print("Main machine is " + mainM)
        print("Generating VS project...")

        generate_project.generateVSProject(out, name, cInclude, cLib, mainM, \
            False)

    if (args.cc):
        print("Building Generated C...")
        outp = check_output([cc, proj]);
        outp = '\n'.join(str(outp).split("\\r\\n"))

        if (not buildSucceeded(outp)):
            die("Failed Building the C code:\n" + outp)
    
except CalledProcessError as err:
    print("Failed Compiling: \n")
    dumpOutput(err.output)