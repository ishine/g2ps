import argparse, tempfile, os, sys
import preprocess
import phonetisaurus

###########################################################
def find_inputfiles(datapath, input_pronlexes, languages, dicttypes):
    output_pronlexes = []
    for spec in input_pronlexes:
        (language, dicttype, filename) = (spec[0], spec[1], spec[2])
        if dicttype=='masterlex':
            language = preprocess.normalize_dicts.alpha3_to_language(language)
        if language in languages or 'ALL' in languages:
            if dicttype in dicttypes or 'ALL' in dicttypes:
                for d in datapath:
                    candidate = os.path.join(d,spec[2])
                    if os.path.exists(candidate):
                        output_pronlexes.append([spec[0], spec[1], candidate])
    return(output_pronlexes)

###########################################################
def convert_pronlexes_to_ipa(fullpaths, outputdir):
    for spec in fullpaths:
        (language, dicttype, infile) = (spec[0], spec[1], spec[2])
        # Find language name and alpha3
        if dicttype=='masterlex':
            (alpha3, language) = (language, preprocess.normalize_dicts.alpha3_to_language(language))
        else:
            alpha3 = preprocess.normalize_dicts.language_to_alpha3(language)
                  
        # Call the appropriate type of normalization, to convert to IPA
        outfile = os.path.join(outputdir,language+'.txt')
        print('Normalizing file {} to {}'.format(infile,outfile))
        
        if dicttype=='callhome':
            preprocess.normalize_dicts.normalize_callhome(infile,outfile,language,alpha3)
        elif dicttype=='babel':
            preprocess.normalize_dicts.normalize_babel(infile,outfile,language,alpha3)
        elif dicttype=='celex':
            preprocess.normalize_dicts.normalize_celex(infile,outfile,language,alpha3)
        elif dicttype=='masterlex':
            preprocess.normalize_dicts.normalize_masterlex(infile,outfile)
        else:
            preprocess.normalize_dicts.normalize_ipa(infile,outfile,mode='a')

###########################################################
if __name__=="__main__":
    parser = argparse.ArgumentParser(description='Train some G2Ps.',
                                     epilog='Either -p or -P must be specified.')
    parser.add_argument('-p','--pronlex',nargs='*',
                        help='Pathname(s) (relative to DATAPATH) of pronlex with the training data')
    parser.add_argument('-P','--pronlexlist',
                        help='''Filename of text file with a list of pronlexes, one per line.
                        Each line should contain three columns: language format pathname,
                        where pathname can be relative to the DATAPATH.''')
    default_datapath='.:..:'+os.path.expanduser('~/data/dicts')
    parser.add_argument('-d','--datapath',
                        default=default_datapath,
                        help='''Paths (colon-separated) in which to search for pronlexes.
                        Default: %s'''%(default_datapath))
    parser.add_argument('--dicttypes',
                        help='''dictionary types to be processed, if not all.
                        Multiple dicttypes may be colon-separated, e.g., babel:ipa:celex.
                        (Default: all)''')
    parser.add_argument('-l','--language',nargs='*',
                        help='''Language(s) for which you want to train G2Ps.
                        Default: all the languages in the pronlexlist''')
    parser.add_argument('-L','--languagelist',
                        help='Text file, listing languages for which you want to train G2Ps')
    default_workingdir=os.path.join(os.getcwd(),'exp')
    parser.add_argument('-w','--workingdir',
                        default=default_workingdir,
                        help='Pathname of the working directory. Default: '+default_workingdir)
    args = parser.parse_args()

    # If no -p or -P, exit
    if args.pronlex==None and args.pronlexlist==None:
        parser.print_help()
        sys.exit(0)

    # Generate configuration lists from command line options
    languages = set()
    if args.language:
        languages = set(args.language)
    if args.languagelist:
        with open(args.languagelist) as f:
            languages |= set(f.read().split())
    if len(languages) == 0:
        languages.add('ALL')
    pronlexes = []
    if args.pronlex:
        pronlexes = [['', 'ipa', p] for p in args.pronlex]
    if args.pronlexlist:
        with open(args.pronlexlist) as f:
            for line in f:
                if len(line) > 0:
                    if line[0] != '#':
                        pronlexes.append(line.rstrip().split())
    datapath = args.datapath.split(':')
    dictsdir = os.path.join(args.workingdir, 'dicts')
    os.makedirs(dictsdir, exist_ok=True)

    # List of formats
    if args.dicttypes == None:
        dicttypes = ['ALL']
    else:
        dicttypes = args.dicttypes.split(':')
        for dt in dicttypes:
            if dt not in preprocess.normalize_dicts.known_dicttypes:
                raise NotImplementedError('dicttype %s unknown; known dicttypes are %s'%(dt,preprocess.normalize_dicts.known_dicttypes))
                                                                                 
    # Convert pronlexes to IPA, put them in dictsdir
    fullpaths = find_inputfiles(datapath, pronlexes, languages, dicttypes)
    convert_pronlexes_to_ipa(fullpaths, dictsdir)

    # Make folds, with bad_dicts=[]
    #preprocess.make_folds.make_train_dev_eval(dictsdir, args.workingdir, [])

    # Try to do phonetisaurus training
    #phonetisaurus.train_g2ps.phonetisaurus_train(args.workingdir)