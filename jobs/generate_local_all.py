#!/bin/python3
import argparse
import os
import json

parser = argparse.ArgumentParser()
parser.add_argument("-e", dest="experiment_path", default=None, help="experiment file name", required=True)
parser.add_argument("--execute", dest="execute", action='store_true')
args = parser.parse_args()

with open("../experiments/" + args.experiment_path + ".json", 'r') as infile:
    experiments = json.load(infile)

count = len(experiments)

runlines = ["#!/bin/bash\n"]

for i in range(0, count):
    os.system("python generate_local.py -e " + args.experiment_path + " -r " + str(i))
    runlines.append("bash " + args.experiment_path + "_" + str(i) + "_local.sh\n")
    
with open(args.experiment_path + "_local_runall.sh", 'w') as outfile:
    outfile.writelines(runlines)
