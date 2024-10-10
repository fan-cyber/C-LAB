import argparse
import json
import openai
from summary_module import SummaryModule
from query_module import QueryModule


def get_proxy():
    import os
    proxy_url = 'http://127.0.0.1:9981'
    os.environ["http_proxy"] = proxy_url
    os.environ["https_proxy"] = proxy_url


def argparser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['summary', 'query_localize', 'query_extract'], required=True)
    parser.add_argument('--dataset_paper', default='./chempapers_all')
    parser.add_argument('--dataset_summary', default='./chempapers_summary')
    parser.add_argument('--query_text', default='Au NRs')
    parser.add_argument('--similarity_top_k', default=3, help='filter paper number')
    parser.add_argument('--similarity_cutoff', default=0.7, help='similarity threshold')
    parser.add_argument('--extract_pdf_path', default='')
    return parser.parse_args()


def get_api_key():
    with open('./api_config.json', encoding='utf-8') as f:
        api_config = json.load(f)
    return api_config['api']


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
    get_proxy()
    args = argparser()
    mode = args.mode
    openai.api_key = get_api_key()
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
