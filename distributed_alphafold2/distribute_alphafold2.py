
import os
import argparse
import shutil
import sys
import traceback

# Enable command line arguments for the directory containing the fasta data and the directory into which the AlphaFold2 results will be saved
def parse_arguments():
    parser = argparse.ArgumentParser(description='Distribute AlphaFold2')
    parser.add_argument('-f', '--fasta_file_dir', metavar='fasta_file_dir', type=str, help='Directory containing the fasta files EX: ./fasta_files/')
    parser.add_argument('-o', '--alphafold_out_dir', metavar='alphafold_out_dir', type=str, help='Path to the output directory for AlphaFold2 results EX: ./alphafold_out_dir/')
    parser.add_argument('-s', '--sif_file', metavar='sif_file', type=str, help='Path to the AlphaFold2 singularity image file EX: ./sif_file/alphafold.sif')
    parser.add_argument('-r', '--run_script', metavar='run_script', type=str, help='Path to the run script EX: ./run.sh')
    parser.add_argument('--force_overwrite', action='store_true', help='Force overwrite of existing results if they exist to rerun AlphaFold2 for all fasta files.')
    args = parser.parse_args()
    return args, parser


def main():
    # Parse command line arguments
    args, parser = parse_arguments()
    
    try:
        fasta_file_dir, alpha_out_dir, force_overwrite, sif_file, run_script = ensure_correct_script_input(args, parser)
        current_directory = os.getcwd()

        # Distribute AlphaFold2
        distribute_alphafold_to_all_fasta_files(fasta_file_dir, alpha_out_dir, force_overwrite, sif_file, run_script, current_directory) 
        
        print("AlphaFold2 distributed successfully.")
    
    except Exception as e:
        print(f"{traceback.format_exc()}")
        parser.print_help()
        sys.exit(1)
    
    return None


def ensure_correct_script_input(args, parser):
    if args.fasta_file_dir:
        fasta_file_dir = args.fasta_file_dir
    else:
        parser.print_help()
        print("\nPlease provide the directory containing the fasta files using --fasta_file_dir or -f.")
        sys.exit(1)
        
    if args.alphafold_out_dir:
        alpha_out_dir = os.path.abspath(args.alphafold_out_dir)
    else:
        raise Exception(f"\nPlease provide the directory where the AlphaFold2 results will be saved using --alphafold_out_dir or -o.")
    
    if args.sif_file:
        sif_file = os.path.abspath(args.sif_file)
    elif os.path.exists('alphafold.sif'):
        sif_file = os.path.abspath('alphafold.sif')
    else:
        raise Exception(f"\nPlease provide the path to the AlphaFold2 singularity image file using --sif_file or -s.")
    
    if args.run_script:
        run_script = os.path.abspath(args.run_script)
    elif os.path.exists('run.sh'):
        run_script = os.path.abspath('run.sh')
    else:
        raise Exception(f"\nPlease provide the path to the run script using --run_script or -r.")
         
    
    force_overwrite = args.force_overwrite if args.force_overwrite else False
    
    return fasta_file_dir, alpha_out_dir, force_overwrite, sif_file, run_script


def distribute_alphafold_to_all_fasta_files(fasta_file_dir: str, alpha_out_dir: str, force_overwrite: bool, sif_file: str, run_script: str, current_directory: str):
    
    # Check if fasta_file_dir exists
    if not os.path.exists(fasta_file_dir):
        raise Exception(f"Directory '{fasta_file_dir}' does not exist.")
    
    # Check if alpha_out_dir exists, if not create it
    if not os.path.exists(alpha_out_dir):
        os.makedirs(alpha_out_dir)
    
    # Check if sif_file exists
    if not os.path.exists(sif_file):
        raise Exception(f"Singularity image file '{sif_file}' does not exist.")
    
    # Check if run_script exists
    if not os.path.exists(run_script):
        raise Exception(f"Run script '{run_script}' does not exist.")
    
    build_each_fasta_a_run(fasta_file_dir, alpha_out_dir, current_directory, force_overwrite, sif_file, run_script)
    
    launch_batch_jobs(fasta_file_dir, alpha_out_dir)
    
    return None
    

def launch_batch_jobs(fasta_file_dir, alpha_out_dir):
    for file_name in os.listdir(fasta_file_dir):
        if file_name.endswith('.fasta'):
            fasta_name = os.path.splitext(file_name)[0]
            dir_path = os.path.join(alpha_out_dir, fasta_name)
            run_script = f'run_{fasta_name}.sh'
            os.chdir(dir_path)
            os.system(f'sbatch {run_script}')
    return None

    
def build_each_fasta_a_run(fasta_file_dir: str, alpha_out_dir: str, current_directory: str, force_overwrite: bool, sif_file, run_script):
    # Check if directories for each fasta file already exist
    check_existing_dirs(fasta_file_dir, alpha_out_dir, force_overwrite)
    
    # Make directories for each fasta file in alpha_out_dir
    make_directories(fasta_file_dir, alpha_out_dir)
    
    # Copy fasta files to the respective directories
    copy_fasta_files(fasta_file_dir, alpha_out_dir)
    
    # Generate slurm batch run scripts for each fasta file
    generate_run_scripts(fasta_file_dir, alpha_out_dir, current_directory, sif_file, run_script)


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


def generate_run_scripts(fasta_file_dir, alpha_out_dir, current_directory, sif_file, run_script):
    with open(run_script, 'r') as f:
        run_script_content = f.read()
        
          
    # Modify the email address in the run script
    username = os.getenv('USER') or os.getenv('USERNAME')
    run_script_content_modified_0 = run_script_content.replace('my_username_VAR', username)
    
    
    for file_name in os.listdir(fasta_file_dir):
        if file_name.endswith('.fasta'):
            
            # Modify the run script for each fasta file
            fasta_name = os.path.splitext(file_name)[0]
            run_script_content_modified_1 = run_script_content_modified_0.replace('my_fasta_file_VAR', file_name)
            
            # Modify where alphafold results will be saved
            where_alpha_out_dir = os.path.join(alpha_out_dir, fasta_name)
            run_script_content_modified_2 = run_script_content_modified_1.replace('my_alphafold_out_dir_VAR', where_alpha_out_dir)

            # Modify the path to the singularity image file
            run_script_content_modified_3 = run_script_content_modified_2.replace('my_sif_file_VAR', sif_file)
            
            # Modify the sbatch job name
            run_script_content_modified_4 = run_script_content_modified_3.replace('my_job_name_VAR', f'alphafold_{fasta_name}')
            
            run_script_path_modified = os.path.join(alpha_out_dir, fasta_name, f'run_{fasta_name}.sh')
            with open(run_script_path_modified, 'w') as f:
                f.write(run_script_content_modified_4)
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
                    has_fasta_dir_name_in_dir = any([fasta_name == file for file in os.listdir(dir_path)])
                    bug_user_bool = not is_dir_empty and has_fasta_dir_name_in_dir
                
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
