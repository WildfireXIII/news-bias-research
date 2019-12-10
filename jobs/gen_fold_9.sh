#!/bin/bash

#SBATCH --mem=16000
#SBATCH --time=2:00:00

cd /home/tntech.edu/namartinda42/research
. env_setup.sh
. jobs/common.sh
cd /home/tntech.edu/namartinda42/research/bias

python experiment.py --experiment ../experiments/data_gen.json --row 37 --log $LOGPATH/datagen_fold_9_tfidf.log
python experiment.py --experiment ../experiments/data_gen.json --row 38 --log $LOGPATH/datagen_fold_9_w2v.log
python experiment.py --experiment ../experiments/data_gen.json --row 39 --log $LOGPATH/datagen_fold_9_glove.log
python experiment.py --experiment ../experiments/data_gen.json --row 40 --log $LOGPATH/datagen_fold_9_fasttext.log
