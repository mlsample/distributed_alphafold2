from pathlib import Path
import os
import shutil
import pandas as pd
import argparse
import sys
import traceback
import subprocess
from typing import Any
from concurrent.futures import ProcessPoolExecutor
from tqdm import tqdm

# import xarray as xr
# Given a query pdb and and a target proteome accension
# first I just want to write the functions that will run fatcat 


# # Enable command line arguments for the directory containing the fasta data and the directory into which the AlphaFold2 results will be saved
def parse_arguments():
    parser = argparse.ArgumentParser(description='FATCAT and TM-Align Strucutral Homology Screens')
    parser.add_argument('-q', '--query_file_dir', metavar='query_file_dir', type=str, help='Directory containing the query PDB files EX: ./query_dir/')
    parser.add_argument('-p', '--proteome_dirs', metavar='proteome_dirs', type=str, help='Directory of proteome directories EX: ./proteomes/ (where ./proteomes contains multiple dirs called i.e human, mouse, drome)')
    parser.add_argument('-f', '--fatcat_install_dir', metavar='fatcat_install_dir', type=str, help='Path to the fatcat github directory  EX: ./FATCAT-dist/')
    parser.add_argument('-t', '--tm_align_install_dir', metavar='tm_align_install_dir', type=str, help='Path to the USAlign github directory EX: ./USalign')
    parser.add_argument('-o', '--output_name', metavar='output_name', type=str, help='Location to save the csv formatted results of the FATCAT and TM-Align search. Default: ./fatcat_tmalign_homology_search.csv')
    parser.add_argument('--force_overwrite', action='store_true', help='Force overwrite of existing results if they exist.')
    args = parser.parse_args()
    return args, parser


def main():
    # Parse command line arguments
    args, parser = parse_arguments()
    query_file_dir, proteome_dirs, fatcat_install_dir, tm_align_install_dir, output_name = ensure_correct_script_input(args, parser)

    try:
        combined_df = search_multiple_queries(query_file_dir, proteome_dirs, fatcat_install_dir, tm_align_install_dir)
        combined_df.to_csv(output_name, index=False)
    except:
        print(f"{traceback.format_exc()}")
        parser.print_help()
        sys.exit(1)
        
    print(f"FATCAT and TM-Align search complete. Results saved to {output_name}.")

    return  combined_df


def ensure_correct_script_input(args, parser):
    if args.query_file_dir:
        if os.path.exists(args.query_file_dir):
            query_file_dir = Path(args.query_file_dir).resolve()
        else:
            parser.print_help()
            print("\nThe provided query_file_dir does not exists, please ensure correct input.")
            sys.exit(1)
    else:
        parser.print_help()
        print("\nPlease provide the directory containing the query PDBs using --query_file_dir or -q.")
        sys.exit(1)
        
    if args.proteome_dirs:
        if os.path.exists(args.proteome_dirs):
            proteome_dirs = Path(args.proteome_dirs).resolve()
            proteome_dirs = [proteome_dirs / proteome_dir for proteome_dir in proteome_dirs.iterdir() if proteome_dir.is_dir()]
            if len(proteome_dirs) == 0:
                parser.print_help()
                print("\nThe provided proteome_dirs does not contain any directories, please ensure correct input.")
                sys.exit(1)
        else:
            parser.print_help()
            print("\nThe provided proteome_dirs does not exists, please ensure correct input.")
            sys.exit(1)
    else:
        parser.print_help()
        print("\nPlease provide the directory containing the proteome directories using --proteome_dirs or -p.")
        sys.exit(1)
    
    if args.fatcat_install_dir:
        if os.path.exists(args.fatcat_install_dir):
            pass
        else:
            parser.print_help()
            print("\nThe provided fatcat_install_dir does not exists, please ensure correct input.")
            sys.exit(1)
        if os.path.exists(os.path.join(args.fatcat_install_dir, 'FATCATMain', 'FATCATSearch.pl')):
            fatcat_install_dir = Path(args.fatcat_install_dir).resolve()
        else:
            parser.print_help()
            print("\nThe FATCAT github directory exists, but the executable were not installed or were incorrectly installed, no FATCATSearch.pl executable found.")
            sys.exit(1)
    else:
        if os.path.exists('./fatcat_tmalign/FATCAT-dist'):
            fatcat_install_dir = Path('./fatcat_tmalign/FATCAT-dist').resolve()
            print('Using default FATCAT install directory at ./fatcat_tmalign/FATCAT-dist')
        else:
            parser.print_help()
            print("\nPlease provide the path to the FATCAT github directory using --fatcat_install_dir or -f.")
            sys.exit(1)
    
    if args.tm_align_install_dir:
        if os.path.exists(args.tm_align_install_dir):
            pass
        else:
            parser.print_help()
            print("\nThe provided tm_align_install_dir does not exists, please ensure correct input.")
            sys.exit(1)
        if os.path.exists(os.path.join(args.tm_align_install_dir, 'USalign')):
            tm_align_install_dir = Path(args.tm_align_install_dir).resolve()
        else:
            parser.print_help()
            print("\nThe USAlign github directory exists, but the executable were not installed or were incorrectly installed, no USalign executable found.")
            sys.exit(1)
    else:
        if os.path.exists('./fatcat_tmalign/USalign'):
            tm_align_install_dir = Path('./fatcat_tmalign/USalign').resolve()
            print('Using default USAlign install directory at ./fatcat_tmalign/USalign')
        else:
            parser.print_help()
            print("\nPlease provide the path to the USAlign github directory using --tm_align_install_dir or -t.")
            sys.exit(1)
            
    if args.output_name:
        if args.output_name.endswith('.csv'):
            output_name = args.output_name
        else:
            removed_extension, _ = os.path.splitext(args.output_name)
            output_name = f'{removed_extension}.csv'
    else:
        output_name = 'fatcat_tmalign_homology_search.csv'
    
    force_overwrite = args.force_overwrite if args.force_overwrite else False
    handle_overwrite(force_overwrite, output_name)
    
    return query_file_dir, proteome_dirs, fatcat_install_dir, tm_align_install_dir, output_name


def handle_overwrite(force_overwrite, output_name):
    if os.path.exists(output_name):
        if force_overwrite:
            os.remove(output_name)
        else:
            print(f"The file {output_name} already exists. Please provide a new output name or use the --force_overwrite flag to overwrite the existing file.")
            sys.exit(1)

def run_fatcat_search(query_pdb, proteome_dir, fatcat_install_dir):
    start_dir = os.getcwd()
    prot_db_path = make_proteome_database_file(proteome_dir)

    
    fatcat_search_path = fatcat_install_dir / 'FATCATMain' / 'FATCATSearch.pl'
    
    os.chdir(proteome_dir)
    
    if os.path.exists(proteome_dir / query_pdb.name):
        place_query_in_proteome_dir = False
    else:
        place_query_in_proteome_dir = True
        shutil.copyfile(query_pdb, proteome_dir / query_pdb.name)
    
    invocation = [
        str(fatcat_search_path),
        str(query_pdb.name),
        str(prot_db_path.name),
        '-q'
    ]
    result_file = proteome_dir / f'fatcat_search_results_{query_pdb.name.split(".")[0]}.aln'
   
    try:
        with open(result_file, 'w') as output_file:
            subprocess.run(invocation, check=True, stdout=output_file, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while running FATCAT search: {e.stderr.decode()}")
        raise
    
    if place_query_in_proteome_dir:
        os.remove(proteome_dir / query_pdb.name)
    
    aln_info = parse_fatcat_file(result_file)
    
    
    os.chdir(start_dir)
    return aln_info


def run_tm_align_search(query_pdb, proteome_dir, tm_align_install_dir):
    start_dir = os.getcwd()
    prot_db_path = make_proteome_database_file(proteome_dir)
    
    tm_align_path = tm_align_install_dir / 'USalign'
    
    os.chdir(proteome_dir)
    if os.path.exists(proteome_dir / query_pdb.name):
        place_query_in_proteome_dir = False
    else:
        place_query_in_proteome_dir = True
        shutil.copyfile(query_pdb, proteome_dir / query_pdb.name)
    
    invocation = [
        str(tm_align_path),
        str(query_pdb.name),
        '-dir2', './', f'./{prot_db_path.name}',
        '-suffix', '.pdb',
        '-outfmt', '2',
        '-ter', '1',
        '-fast'
    ]    
    result_file = proteome_dir / f'tm_align_search_results_{query_pdb.name.split(".")[0]}.aln'
    
    try:
        with open(result_file, 'w') as output_file:
            subprocess.run(invocation, check=True, stdout=output_file, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while running TM-Align search: {e.stderr.decode()}")
        raise
    
    if place_query_in_proteome_dir:
        os.remove(proteome_dir / query_pdb.name)
    
    aln_info = parse_tmalign_file(result_file)
    
    os.chdir(start_dir)
    return aln_info


def parse_tmalign_file(aln_path):
    aln_info_dict = {'query':[], 'prot_pdb':[], 'TM1':[], 'TM2':[], 'RMSD':[], 'ID1':[], 'ID2':[], 'IDali':[], 'L1':[], 'L2':[], 'Lali':[]}
    aln_info_dict_keys = list(aln_info_dict.keys())
    n_pdbs = 0
    
    with open(aln_path, 'r') as f:
        for line in f:
            if line.startswith('#PDBchain1'):
                pass
            else:
                line_split = line.split('\t')
                # line_split = line_split[1:]
                for value, key in zip(line_split, aln_info_dict_keys):
                    value = value.strip()
                    if '.pdb' in value:
                        value = value.split(':')[0]
                    else:
                        value = float(value)
                    aln_info_dict[key].append(value)

    df = pd.DataFrame(aln_info_dict)
    return df
            

def parse_fatcat_file(aln_path):
    
    aln_info_dict = {'query':[], 'prot_pdb':[],'p_val':[], 'rmsd':[], 'identity':[], 'similarity':[], 'score':[], 'afp':[]}
    
    n_pdbs = 0
    with open(aln_path, 'r') as f:
        for line in f:
            if line.startswith('Align'):
                n_pdbs += 1
                prot_pdb_name = line.split(' ')[-2]
                query = line.split(' ')[1]
                aln_info_dict['prot_pdb'].append(prot_pdb_name)
                aln_info_dict['query'].append(query)
                
            if line.startswith('P-value'):
                split_line = line.split(' ')
                p_val = float(split_line[1])
                identity = float(split_line[5][:-1]) / 100
                similarity = float(split_line[7][:-2]) / 100
                afp = float(split_line[3])
                
                aln_info_dict['p_val'].append(p_val)
                aln_info_dict['identity'].append(identity)
                aln_info_dict['similarity'].append(similarity)
                aln_info_dict['afp'].append(afp)
                
            if line.startswith('Twists'):
                rmsd = float(line.split(' ')[9])
                score = float(line.split(' ')[13])
                
                aln_info_dict['score'].append(score)
                aln_info_dict['rmsd'].append(rmsd)
                
    df = pd.DataFrame(aln_info_dict)
   
    return df


def make_proteome_database_file(proteome_dir):
    db_file = Path(proteome_dir / "proteome_database.txt")
    with open(db_file.as_posix(), 'w') as f:
        for pdb in proteome_dir.glob("*.pdb"):
            pdb_name = pdb.as_posix().split('/')[-1].split('.')[0]
            f.write(f"{pdb_name}\n")
    return db_file


def run_fatcat_tmalign_parallel(args):
    query_pdb, proteome_dirs, fatcat_install_dir, tm_align_install_dir = args
    fatcat_results = run_fatcat_search(query_pdb, proteome_dirs, fatcat_install_dir)
    tm_align_results = run_tm_align_search(query_pdb, proteome_dirs, tm_align_install_dir)
    return (fatcat_results, tm_align_results)


def search_multiple_proteomes(query_pdb, proteome_dirs, fatcat_install_dir, tm_align_install_dir):
    
    proteomes_fatcat = {proteome_dir.name:[] for proteome_dir in proteome_dirs}
    proteomes_tm_align = {proteome_dir.name:[] for proteome_dir in proteome_dirs}
    
    # args = [(query_pdb, proteome_dir, fatcat_install_dir, tm_align_install_dir) for proteome_dir in proteome_dirs]
    # with ProcessPoolExecutor() as executor:
    #     results = list(executor.map(run_fatcat_tmalign_parallel, args))
        
    # for proteome_dir, (fatcat_result, tm_align_result) in zip(proteome_dirs, results):
    #     proteomes_fatcat[proteome_dir.name] = fatcat_result
    #     proteomes_tm_align[proteome_dir.name] = tm_align_result
    
    
    for proteome_dir in proteome_dirs:
        proteomes_fatcat[proteome_dir.name] = run_fatcat_search(query_pdb, proteome_dir, fatcat_install_dir)
        proteomes_tm_align[proteome_dir.name] = run_tm_align_search(query_pdb, proteome_dir, tm_align_install_dir)
    
    dfs1 = []
    for key, df in proteomes_fatcat.items():
        df['proteome'] = key
        dfs1.append(df)
    combined_df1 = pd.concat(dfs1, ignore_index=True)
    
    dfs2 = []
    for key, df in proteomes_tm_align.items():
        df['proteome'] = key
        dfs2.append(df)
    combined_df2 = pd.concat(dfs2, ignore_index=True)
    
    result_df = pd.merge(combined_df1, combined_df2, on=['query', 'prot_pdb', 'proteome'], how='inner')
    return result_df


def search_multiple_proteomes_parallel(args):
    return search_multiple_proteomes(*args)


def search_multiple_queries(query_file_dir, proteome_dirs, fatcat_install_dir, tm_align_install_dir):
    
    query_pdbs = [query_file_dir / query_pdb for query_pdb in query_file_dir.glob("*.pdb") if query_pdb.is_file()]
    queries = {query_pdb.name:[] for query_pdb in query_pdbs}
    
    
    # args = [(query_pdb, proteome_dirs, fatcat_install_dir, tm_align_install_dir) for query_pdb in query_pdbs]
    
    # with ProcessPoolExecutor() as executor:
    #     results = list(tqdm(executor.map(search_multiple_proteomes_parallel, args), total=len(args), desc='Progress searching all queries...'))
    
    # for query_pdb, result in zip(query_pdbs, results):
    #     queries[query_pdb.name] = result
    
    for query_pdb in tqdm(query_pdbs, total=len(query_pdbs), desc='Progress searching all queries...'):
        queries[query_pdb.name] = search_multiple_proteomes(query_pdb, proteome_dirs, fatcat_install_dir, tm_align_install_dir)
    
    dfs = []
    for key, df in queries.items():    
        dfs.append(df)
    combined_df = pd.concat(dfs, ignore_index=True)

    return combined_df
    
    
if __name__ == '__main__':
    main()