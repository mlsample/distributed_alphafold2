from pathlib import Path
import shutil
import os
import argparse


def main():
    args, parser = parse_arguments()
    
    alphafold_out_dir = Path(args.alphafold_out_dir)
    query_file_dir = Path(args.query_file_dir)
    copy_alphafold_output_to_query_dir(query_file_dir, alphafold_out_dir)
    
    return None
    
def parse_arguments():
    parser = argparse.ArgumentParser(description='Copy AlphaFold2 output (ranked_0.pdb) to query directory')
    parser.add_argument('-q', '--query_file_dir', metavar='query_file_dir', type=str, help='Directory the PDB files will be saved to EX: ./query_dir/')
    parser.add_argument('-a', '--alphafold_out_dir', metavar='alphafold_out_dir', type=str, help='Directory the AlphaFold output files are saved to EX: ./alphafold_output_dir/')
    args = parser.parse_args()
    return args, parser

def copy_alphafold_output_to_query_dir(query_file_dir: Path, alphafold_out_dir: Path):
    
    if not query_file_dir.exists():
        os.makedirs(query_file_dir)
    for pdb_dir in alphafold_out_dir.iterdir():
        if pdb_dir.is_dir():
            for file in pdb_dir.iterdir():
                if file.is_file():
                    if file.name == 'ranked_0.pdb':
                        shutil.copy(file, query_file_dir / f'{pdb_dir.name}.pdb')
                else:
                    if file.is_dir():
                        if file.name == pdb_dir.name:
                            for subfile in file.iterdir():
                                if subfile.is_file():
                                    if subfile.name == 'ranked_0.pdb':
                                        shutil.copy(subfile, query_file_dir / f'{pdb_dir.name}.pdb')
                        
if __name__ == '__main__':
    main()

