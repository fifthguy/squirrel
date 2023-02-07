#!/usr/bin/env python3
from squirrel.utils.log_colours import green,cyan

import squirrel.utils.custom_logger as custom_logger
from squirrel.utils.config import *
from squirrel.utils.initialising import *
import squirrel.utils.io_parsing as io
from squirrel import __version__
from . import _program

import os
import sys
import argparse
import snakemake

thisdir = os.path.abspath(os.path.dirname(__file__))
cwd = os.getcwd()

def main(sysargs = sys.argv[1:]):
    parser = argparse.ArgumentParser(prog = _program,
    description='squirrel: Some QUIck Rearranging to Resolve Evolutionary Links',
    usage='''squirrel <input> [options]''')

    io_group = parser.add_argument_group('Input-Output options')
    io_group.add_argument('input', nargs="*", help='Input fasta file of sequences to analyse.')
    io_group.add_argument('-o','--outdir', action="store",help="Output directory. Default: current working directory")
    io_group.add_argument('--outfile', action="store",help="Optional output file name. Default: <input>.aln.fasta")
    io_group.add_argument('--tempdir',action="store",help="Specify where you want the temp stuff to go. Default: $TMPDIR")
    io_group.add_argument("--no-temp",action="store_true",help="Output all intermediate files, for dev purposes.")

    a_group = parser.add_argument_group("Pipeline options")
    a_group.add_argument("--no-mask",action="store_true",help="Skip masking of repetitive regions. Default: masks repeat regions")
    a_group.add_argument("--no-itr-mask",action="store_true",help="Skip masking of end ITR. Default: masks ITR")
    a_group.add_argument("--extract-cds",action="store_true",help="Extract coding sequences based on coordinates in the reference")
    a_group.add_argument("--concatenate",action="store_true",help="Concatenate coding sequences for each genome, separated by `NNN`. Default: write out as separate records")

    m_group = parser.add_argument_group('Misc options')
    m_group.add_argument("-v","--version", action='version', version=f"squirrel {__version__}")
    m_group.add_argument("--verbose",action="store_true",help="Print lots of stuff to screen")
    m_group.add_argument("-t","--threads",action="store",default=1,type=int, help="Number of threads")
    
    c_group = parser.add_argument_group('Reference genome options')
    c_group.add_argument("-r", "--ref_fasta", action="store", help="Reference genome filename?", default=os.path.join(thisdir, "data/reference.fasta"))
    c_group.add_argument("-m", "--ref_mask", action="store", help="What to mask?", default=os.path.join(thisdir, "data/to_mask.csv"))
    c_group.add_argument("-b", "--ref_gene_boundaries", action="store", help="Where are the CDS?", default=os.path.join(thisdir, "data/gene_boundaries.csv"))
    c_group.add_argument("-c", "--ref_trim_end", action="store", help="Where to trim off second ITR", default=185579)


    if len(sysargs)<1:
        parser.print_help()
        sys.exit(-1)
    else:
        args = parser.parse_args(sysargs)

    # Initialise config dict
    config = setup_config_dict(cwd)

    #get_datafiles(config, args.ref_fasta, args.ref_mask, args.ref_gene_boundaries)
    
    ref_fasta = os.path.join(cwd, args.ref_fasta) if args.ref_fasta.startswith(thisdir) != True else args.ref_fasta
    ref_mask = os.path.join(cwd, args.ref_mask) if args.ref_mask.startswith(thisdir) != True else args.ref_mask
    ref_gene_boundaries = os.path.join(cwd, args.ref_gene_boundaries) if args.ref_gene_boundaries.startswith(thisdir) != True else args.ref_gene_boundaries
    
    get_ref_data(config, 
                 [
                     KEY_REFERENCE_FASTA, 
                     KEY_TO_MASK, 
                     KEY_GENE_BOUNDARIES
                     ], 
                 [
                     ref_fasta,
                     ref_mask,
                     ref_gene_boundaries
                     ])
    
    config[KEY_TRIM_END] = args.ref_trim_end
    


    config[KEY_OUTDIR] = io.set_up_outdir(args.outdir,cwd,config[KEY_OUTDIR])
    config[KEY_OUTFILE],config[KEY_CDS_OUTFILE] = io.set_up_outfile(args.outfile,args.input, config[KEY_OUTFILE],config[KEY_OUTDIR])
    io.set_up_tempdir(args.tempdir,args.no_temp,cwd,config[KEY_OUTDIR], config)

    io.pipeline_options(args.no_mask, args.no_itr_mask, args.extract_cds, args.concatenate, config)

    config[KEY_INPUT_FASTA] = io.find_query_file(cwd, config[KEY_TEMPDIR], args.input)

    
    snakefile = get_snakefile(thisdir,"msa")

    if args.verbose:
        print(green("\n**** CONFIG ****"))
        for k in sorted(config):
            print(green(k), config[k])

        status = snakemake.snakemake(snakefile, 
                                        printshellcmds=True, 
                                        forceall=True, 
                                        force_incomplete=True,
                                        workdir=config[KEY_TEMPDIR],
                                        config=config, 
                                        cores=args.threads,
                                        lock=False
                                        )
    else:
        logger = custom_logger.Logger()
        status = snakemake.snakemake(snakefile, 
                                        printshellcmds=False, 
                                        forceall=True,
                                        force_incomplete=True,
                                        workdir=config[KEY_TEMPDIR],
                                        config=config, 
                                        cores=args.threads,
                                        lock=False,
                                        quiet=True,
                                        log_handler=logger.log_handler
                                    )