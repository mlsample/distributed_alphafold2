from pathlib import Path
import os
import shutil
import pandas as pd
import argparse
import sys
import traceback
import subprocess

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
    parser.add_argument('--force_overwrite', action='store_true', help='Force overwrite of existing results if they exist to rerun AlphaFold2 for all fasta files.')
    args = parser.parse_args()
    return args, parser


def main():
    # Parse command line arguments
    args, parser = parse_arguments()
    query_file_dir, proteome_dirs, fatcat_install_dir, tm_align_install_dir, force_overwrite = ensure_correct_script_input(args, parser)

    try:
        current_directory = os.getcwd()

        combined_df = search_multiple_queries(query_file_dir, proteome_dirs, fatcat_install_dir, tm_align_install_dir)
        combined_df.to_csv('fatcat_tm_align_search_results.csv', index=False)
    except:
        print(f"{traceback.format_exc()}")
        parser.print_help()
        sys.exit(1)
        
    print("FATCAT and TM-Align search complete.")

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
        parser.print_help()
        print("\nPlease provide the path to the USAlign github directory using --tm_align_install_dir or -t.")
        sys.exit(1)
         
    
    force_overwrite = args.force_overwrite if args.force_overwrite else False
    
    return query_file_dir, proteome_dirs, fatcat_install_dir, tm_align_install_dir, force_overwrite


def run_fatcat_search(query_pdb, proteome_dir, fatcat_install_dir):
    start_dir = os.getcwd()
    prot_db_path = make_proteome_database_file(proteome_dir)
    
    fatcat_seach_path = fatcat_install_dir / 'FATCATMain' / 'FATCATSearch.pl'
    
    os.chdir(proteome_dir)
    shutil.copyfile(query_pdb, proteome_dir / query_pdb.name)
    invocation = f'{fatcat_seach_path} {query_pdb.name} {prot_db_path.name} -q > fatcat_search_results_{query_pdb.name.split('.')[0]}.aln'
    os.system(invocation)
    os.remove(proteome_dir / query_pdb.name)
    
    aln_path = proteome_dir / f'fatcat_search_results_{query_pdb.name.split('.')[0]}.aln'
    
    aln_info = filter_aln_file(aln_path)
    
    os.chdir(start_dir)
    return aln_info


def run_tm_align_search(query_pdb, proteome_dir, tm_align_install_dir):
    start_dir = os.getcwd()
    prot_db_path = make_proteome_database_file(proteome_dir)
    
    tm_align_path = tm_align_install_dir / 'USalign'
    
    os.chdir(proteome_dir)
    shutil.copyfile(query_pdb, proteome_dir / query_pdb.name)
    invocation = f'{tm_align_path} {query_pdb.name} -dir2 ./ ./{prot_db_path.name} -suffix .pdb -outfmt 2 -ter 1 -fast > tm_align_search_results_{query_pdb.name.split('.')[0]}.aln'
    os.system(invocation)
    os.remove(proteome_dir / query_pdb.name)
    
    aln_path = proteome_dir / f'tm_align_search_results_{query_pdb.name.split('.')[0]}.aln'
    
    aln_info = filter_tm_align_file(aln_path)
    
    os.chdir(start_dir)
    return aln_info


def filter_tm_align_file(aln_path):
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
            

def filter_aln_file(aln_path):
    
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


def search_multiple_proteomes(query_pdb, proteome_dirs, fatcat_install_dir, tm_align_install_dir):

    proteome_dirs = [proteome_dirs / proteome_dir for proteome_dir in proteome_dirs.iterdir() if proteome_dir.is_dir()]
    
    proteomes_fatcat = {proteome_dir.name:[] for proteome_dir in proteome_dirs}
    proteomes_tm_align = {proteome_dir.name:[] for proteome_dir in proteome_dirs}
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


def search_multiple_queries(query_file_dir, proteome_dirs, fatcat_install_dir, tm_align_install_dir):
    
    query_pdbs = [query_file_dir / query_pdb for query_pdb in query_file_dir.glob("*.pdb") if query_pdb.is_file()]
    queries = {query_pdb.name:[] for query_pdb in query_pdbs}
    for query_pdb in query_pdbs:
        queries[query_pdb.name] = search_multiple_proteomes(query_pdb, proteome_dirs, fatcat_install_dir, tm_align_install_dir)
    
    dfs = []
    for key, df in queries.items():    
        dfs.append(df)
    combined_df = pd.concat(dfs, ignore_index=True)

    return combined_df
    
    
if __name__ == '__main__':
    main()