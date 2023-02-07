#!/usr/bin/env python

###########################

from Bio import SeqIO
import argparse
import sys

##########################

def parse_args(args=None):
    Description = 'Convert genbank file to csv gene boundaries file that Sqirrel can read.'
    Epilog = """Example usage: python ivar_variants_to_vcf.py <FILE_IN> <FILE_OUT>"""

    parser = argparse.ArgumentParser(description=Description, epilog=Epilog)
    parser.add_argument('--infile', '-i', type=str, help="Input reference GenBank file.", default="data/reference.gbk")
    parser.add_argument('--outfile', '-o', type=str, help="Full path to output csv file for squirrel.", default="data/gene_boundaries.csv")
    return parser.parse_args(args)

def parse_genbank_file(infile):
    with open(infile) as fin:
        record = SeqIO.read(fin, "genbank")
        features = []
        for feature in record.features:
            if feature.type == "CDS":
                start = feature.location.start
                end = feature.location.end
                strand = "forward" if feature.location.strand == 1 else "reverse"
                if strand == "reverse":
                    start = start + 1
                    end = end
                else:
                    start = start + 1
                name = feature.qualifiers["product"][0] + " " + "CDS"
                features.append([name, str(start), str(end), str(end-start), strand])
        return features

def write_gene_squirrel_csv(func, infile, outfile):
    with open(outfile, "w") as fout:
        fout.write("Name,Minimum,Maximum,Length,Direction\n")
        for feature in func(infile):
            fout.write(",".join(feature) + "\n")                

def main(args=None):
    args = parse_args(args)
    #parse_genbank_file(args.infile)
    write_gene_squirrel_csv(parse_genbank_file, args.infile, args.outfile)

##########################

if __name__ == '__main__':
    sys.exit(main())