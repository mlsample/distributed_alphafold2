#! bin/bash

mkdir fatcat_tmalign
cd fatcat_tmalign
git clone https://github.com/GodzikLab/FATCAT-dist.git
git clone https://github.com/pylelab/USalign.git

cd USalign
make
cd ../FATCAT-dist
./Install

echo "Please copy and paste the export and setenv lines into your terminal for the installation to work"
