#!/bin/bash
#SBATCH -p general
#SBATCH -q public
#SBATCH --time=2-00:00:00
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=80G
#SBATCH --mail-type=ALL
#SBATCH --mail-user=jenow@asu.edu


#set the environment PATH
export PYTHONNOUSERSITE=True
module load singularity/3.8.0
export ALPHAFOLD_DATA_PATH=/data/alphafold/db_20230619
export USER_ALPHAFOLD_DIR=/home/$(whoami)/alphafold2
export FASTA_FILE=TanaPXV.fasta

#BELOW 2 LINES ARE FOR JOBS RUNNING on multiple GPUs (below example is for 2)
#export TF_FORCE_UNIFIED_MEMORY=1
#export XLA_PYTHON_CLIENT_MEM_FRACTION=2.0

#Run the command
singularity run --nv \
 -B $ALPHAFOLD_DATA_PATH:/data \
 -B .:/etc \
 --pwd  /app/alphafold $USER_ALPHAFOLD_DIR/alphafold.sif \
 --fasta_paths=/etc/$FASTA_FILE  \
 --uniref90_database_path=/data/uniref90/uniref90.fasta  \
 --data_dir=/data \
 --mgnify_database_path=/data/mgnify/mgy_clusters.fa   \
 --bfd_database_path=/data/bfd/bfd_metaclust_clu_complete_id30_c90_final_seq.sorted_opt \
 --uniclust30_database_path=/data/uniclust30/uniclust30_2018_08/uniclust30_2018_08 \
 --pdb70_database_path=/data/pdb70/pdb70  \
 --template_mmcif_dir=/data/pdb_mmcif/mmcif_files  \
 --obsolete_pdbs_path=/data/pdb_mmcif/obsolete.dat \
 --max_template_date=2022-02-09   \
 --output_dir=$USER_ALPHAFOLD_DIR/alphafold_output  \
 --model_preset=monomer \
 --db_preset=full_dbs \
 --use_gpu_relax=1


