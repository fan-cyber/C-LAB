import argparse

from summary_module import SummaryModule
from query_module import QueryModule


def argparser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['summary', 'query_localize', 'query_extract'], required=True)
    parser.add_argument('--dataset_paper', default='./dataset_paper')
    parser.add_argument('--dataset_summary', default='./dataset_summary')
    parser.add_argument('--query_text', default='Au NRs')
    parser.add_argument('--similarity_top_k', default=3, help='filter paper number')
    parser.add_argument('--similarity_cutoff', default=0.7, help='similarity threshold')
    parser.add_argument('--extract_pdf_path', default='')
    return parser.parse_args()


def print_info(scores, files, texts):
    """Print paper information.

    Args:
        scores (list): similarity
        files (list): file paths
        texts (list): texts
    """
    print('*'*60)
    for score, file, text in zip(scores, files, texts):
        with open(file, 'r') as f:
            paper_title = f.read().split('\n')[1].split('1. Title:')[-1].strip()
        print(f'【Relevance】: \n{score}: ')
        print(f'【Title】: \n{paper_title}')
        print(f'【Path】: \n{file}')
        print(f'【Text】: \n{text}')
        print('*'*60)


if __name__ == '__main__':
    args = argparser()
    mode = args.mode
    if mode == 'summary':
        summary_module = SummaryModule(args.dataset_paper, args.dataset_summary)
        summary_module.summarize()
    if mode == 'query_localize':
        query_module = QueryModule(args.query_text)
        scores, files, texts = query_module.localize(args.dataset_summary, int(args.similarity_top_k), float(args.similarity_cutoff))
        print_info(scores, files, texts)
    if mode == 'query_extract':
        query_module = QueryModule(args.query_text)
        response = query_module.extract(args.extract_pdf_path)
        print(response)
