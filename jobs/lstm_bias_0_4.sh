#!/bin/bash
#SBATCH --mem=96000
#SBATCH --time=6:00:00
cd /home/tntech.edu/namartinda42/research
. env_setup.sh
. jobs/common.sh
cd /home/tntech.edu/namartinda42/research/bias
python experiment.py --experiment ../experiments/lstm_bias_0.json --row 4 --log $LOGPATH/lstm_bias_0_4.log