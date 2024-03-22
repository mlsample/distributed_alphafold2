
import numpy as np
import os
import pandas as pd
import json
import argparse
import shutil

# Enable command line arguments for the directory containing the fasta data and the directory into which the AlphaFold2 results will be saved
def parse_arguments():
    parser = argparse.ArgumentParser(description='Distribute AlphaFold2')
    parser.add_argument('-f', '--fasta_file_dir', metavar='fasta_file_dir', type=str, help='Directory containing the fasta files')
    parser.add_argument('-o', '--alphafold_out_dir', metavar='alphafold_out_dir', type=str, help='Path to the output directory for AlphaFold2 results')
    parser.add_argument('--force_overwrite', action='store_true', help='Force overwrite of existing directories if they exist')
    args = parser.parse_args()
    return args


def main():
    # Parse command line arguments
    args = parse_arguments()
    fasta_file_dir = args.fasta_file_dir
    alpha_out_dir = args.alphafold_out_dir
    force_overwrite = args.force_overwrite if args.force_overwrite else False
    current_directory = os.getcwd()
    
    # Distribute AlphaFold2
    distribute_alphafold_to_all_fasta_files(fasta_file_dir, alpha_out_dir, current_directory, force_overwrite) 
    
    return None


def distribute_alphafold_to_all_fasta_files(fasta_file_dir: str, alpha_out_dir: str, current_directory: str, force_overwrite: bool):
    
    # Check if fasta_file_dir exists
    if not os.path.exists(fasta_file_dir):
        raise Exception(f"Directory '{fasta_file_dir}' does not exist.")
    
    # Check if alpha_out_dir exists, if not create it
    if not os.path.exists(alpha_out_dir):
        os.makedirs(alpha_out_dir)
    
    build_each_fasta_a_run(fasta_file_dir, alpha_out_dir, current_directory, force_overwrite)
    
    
    
def build_each_fasta_a_run(fasta_file_dir: str, alpha_out_dir: str, current_directory: str, force_overwrite: bool):
    # Check if directories for each fasta file already exist
    check_existing_dirs(fasta_file_dir, alpha_out_dir, force_overwrite)
    
    # Make directories for each fasta file in alpha_out_dir
    make_directories(fasta_file_dir, alpha_out_dir)
    
    # Copy fasta files to the respective directories
    copy_fasta_files(fasta_file_dir, alpha_out_dir)
    
    # Generate slurm batch run scripts for each fasta file
    # generate_run_scripts(fasta_file_dir, alpha_out_dir, current_directory)


def make_directories(fasta_file_dir, alpha_out_dir):
    
    for file_name in os.listdir(fasta_file_dir):
        if file_name.endswith('.fasta'):
            fasta_name = os.path.splitext(file_name)[0]
            dir_path = os.path.join(alpha_out_dir, fasta_name)
            os.makedirs(dir_path, exist_ok=True)
    return None
    
def copy_fasta_files(fasta_file_dir, alpha_out_dir):
    for file_name in os.listdir(fasta_file_dir):
        if file_name.endswith('.fasta'):
            fasta_path = os.path.join(fasta_file_dir, file_name)
            fasta_name = os.path.splitext(file_name)[0]
            dir_path = os.path.join(alpha_out_dir, fasta_name)
            save_path = os.path.join(dir_path, f'{fasta_name}.fasta')
            if not os.path.exists(save_path):
                shutil.copy(fasta_path, dir_path)
    return None

def generate_run_scripts(fasta_file_dir, alpha_out_dir, current_directory):
    run_script_path = os.path.join(current_directory, 'distributed_alphafold2', 'run.sh')
    with open(run_script_path, 'r') as f:
        run_script_content = f.read()
    
    for file_name in os.listdir(fasta_file_dir):
        if file_name.endswith('.fasta'):
            fasta_name = os.path.splitext(file_name)[0]
            run_script_content_modified = run_script_content.replace('my_fasta_file_VAR', fasta_name)
            run_script_path_modified = os.path.join(alpha_out_dir, fasta_name, f'run_{fasta_name}.sh')
            with open(run_script_path_modified, 'w') as f:
                f.write(run_script_content_modified)
    return None

def check_existing_dirs(fasta_file_dir, alpha_out_dir, force_overwrite):
    if force_overwrite is True:
        return None
    else:
        for file_name in os.listdir(fasta_file_dir):
                if file_name.endswith('.fasta'):
                    fasta_name = os.path.splitext(file_name)[0]
                dir_path = os.path.join(alpha_out_dir, fasta_name)
                
                if os.path.exists(dir_path):
                    
                    # Still decidicing on all the conditions to check for to see if I should bug user
                    is_dir_empty = len(os.listdir(dir_path)) == 0
                    has_slurm_files = any([file.endswith('.sh') for file in os.listdir(dir_path)])
                    bug_user_bool = not is_dir_empty and has_slurm_files
                
                if bug_user_bool:
                    user_input = input(f"Directory '{dir_path}' already exists. Do you want to proceed? (y/n/skip_this_fasta): ")
                    if user_input.lower() == 'n':
                        raise Exception("Process terminated by user.")
                    elif user_input.lower() == 'skip_this_fasta':
                        print(f"Skipping fasta file '{fasta_name}'.")
                        continue
                    else:
                        print(f"Proceeding with fasta file '{fasta_name}'.")

if __name__ == "__main__":
    main()
