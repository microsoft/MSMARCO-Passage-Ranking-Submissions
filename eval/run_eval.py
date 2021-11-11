import argparse
import bz2
import json
import re
import os
import subprocess

# Helper to download qrels, etc.
# from download import download_dev_qrels


def autoopen(filename, mode="rt"):
    """
    A drop-in for open() that applies automatic compression for .gz and .bz2 file extensions
    """
    if not 't' in mode and not 'b' in mode:
       mode=mode+'t'
    if filename.endswith(".gz"):
        import gzip
        return gzip.open(filename, mode)
    elif filename.endswith(".bz2"):
        import bz2
        return bz2.open(filename, mode)
    return open(filename, mode)


def evaluate_run_with_qrels(run, qrels, exclude=False):
    output = subprocess.check_output(f'python eval/ms_marco_eval.py eval/{qrels} {run}', shell=True).decode('utf-8')
    m = re.compile('MRR @10: ([0-9.]+)').search(output)
    return m.group(1)


def sanity_check_run(file):
    print(f'Sanity checking run {file}')
    qids = set()
    with bz2.open(file, 'rt') as f:
        for i, l in enumerate(f):
            qids.add(l.split('\t')[0])
    line_cnt = i + 1
    num_queries = len(qids)
    print(f'Run has {line_cnt} lines, {num_queries} unique queries.')
    if line_cnt != num_queries * 1000:
        print(f'Warning, {num_queries * 1000} lines expected (1000 hits per query), instead {line_cnt} lines found!')
    print('')


def main(args):
    id = args.id
    base_dir = os.path.join('.', 'submissions', id)

    print(f'# Processing submission {id}\n')

    if os.path.exists('msmarco_passage_private_key.pem'):
        print('Private key found!')
        output = subprocess.check_output(f'eval/unpack.sh {id}', shell=True).decode('utf-8')
        print(output)
    else:
        print('Private key not found, assuming unencrypted files exists...\n')

    print(f'Submission directory {base_dir}')

    assert os.path.exists(base_dir), f'Error: {base_dir} does not exist!'

    print('Verified: submission directory exists!')

    dev_run = os.path.join(base_dir, 'dev.txt.bz2')
    test_run = os.path.join(base_dir, 'eval.txt.bz2')
    metadata_file = base_dir + '-metadata.json'

    for f in [dev_run, test_run, metadata_file]:
        assert os.path.exists(f), f'Error: {f} does not exist!'

    print('Verified: expected files appear in the submission directory!\n')

    sanity_check_run(dev_run)
    sanity_check_run(test_run)

    print('Proceeding to evaluate:\n')

    # Evaluate dev run
    #if not os.path.exists(os.path.join('eval', 'msmarco-docdev-qrels.tsv')):
    #    download_dev_qrels()

    dev_run_mrr = evaluate_run_with_qrels(dev_run, 'msmarco-passage-dev-qrels.tsv')

    print(f'Dev run MRR@10: {dev_run_mrr}')

    # Evaluate test run

    if os.path.exists('eval/msmarco-passage-eval-qrels.tsv'):
        test_run_mrr = evaluate_run_with_qrels(test_run, 'msmarco-passage-eval-qrels.tsv', exclude=True)
        print(f'Eval run MRR@10: {test_run_mrr}')
    else:
        print('Test qrels not available, skipping evaluation.')

    # Piece together entry in leaderboard.csv
    with open(metadata_file, 'r') as f:
        metadata = json.load(f)

    if args.generate_csv:
        match = re.search(r'(\d\d\d\d)(\d\d)(\d\d)-', id)
        year = match.group(1)
        month = match.group(2)
        day = match.group(3)

        if 'embargo_until' in metadata.keys():
            model_description = '"Anonymous"'
            team = '"Anonymous"'
            paper = ''
            code = ''
        else:
            model_description = '"' + metadata['model_description'].replace('"', '\\"') + '"'
            team = '"' + metadata['team'].replace('"', '\\"') + '"'
            paper = metadata['paper']
            code = metadata['code']

        leaderboard_entry = [id,
                             '',  # this is where the emojis go
                             model_description,
                             team,
                             paper,
                             code,
                             metadata['type'],
                             f'{year}/{month}/{day}',
                             f'{round(float(test_run_mrr), 3):.3f}',
                             f'{round(float(dev_run_mrr), 3):.3f}',
                             ''            # This is the tweetid field, leaving empty for now
                             ]

        print('\n\n############')
        print(','.join(leaderboard_entry))
        print('############')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Automated run script for leaderboard')
    parser.add_argument('--id', type=str, metavar='str', required=True, help='submission id.')
    parser.add_argument('--generate-csv', action='store_true', help='Generate the leaderboard csv entry.')

    main(parser.parse_args())
