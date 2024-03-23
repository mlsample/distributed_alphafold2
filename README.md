# Repo to run alphafold2 over multiple fasta files in a slurm hpc environment.

To use the script type:

```bash
python3 distribute_alphafold2.py --fasta_file_dir ../fasta_files/ --alphafold_out_dir ../save_alpha_fold_files_here --sif_file ../sif_file/alphafold.sif  --run_script run.sh
```

For additional help, use:

```bash
python3 distribute_alphafold2.py --help
```

to return the parser help output:

```plaintext
usage: distribute_alphafold2.py [-h] [-f fasta_file_dir] [-o alphafold_out_dir] [-s sif_file] [-r run_script] [--force_overwrite]

Distribute AlphaFold2

options:
  -h, --help            show this help message and exit
  -f fasta_file_dir, --fasta_file_dir fasta_file_dir
                        Directory containing the fasta files EX: ./fasta_files/
  -o alphafold_out_dir, --alphafold_out_dir alphafold_out_dir
                        Path to the output directory for AlphaFold2 results EX: ./alphafold_out_dir/
  -s sif_file, --sif_file sif_file
                        Path to the AlphaFold2 singularity image file EX: ./sif_file/alphafold.sif
  -r run_script, --run_script run_script
                        Path to the run script EX: ./run.sh
  --force_overwrite     Force overwrite of existing results if they exist to rerun AlphaFold2 for all fasta files.
```