import argparse
import json
import openai
from summary_module import SummaryModule
from query_module import QueryModule


def get_proxy():
    import os
    proxy_url = 'http://localhost:9981'
    os.environ["http_proxy"] = proxy_url
    os.environ["https_proxy"] = proxy_url


def argparser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['summary', 'query_localize', 'query_extract'], required=True)
    parser.add_argument('--query_text', default='Au NRs')
    parser.add_argument('--root_extract_paper', default='')
    args = parser.parse_args()
    with open('./config.json', encoding='utf-8') as f:
        config = json.load(f)
        args.api = config['api']
        args.root_dataset = config['root_dataset']
        args.root_summary = config['root_summary']
        args.similarity_top_k = config['similarity_top_k']
        args.similarity_cutoff = config['similarity_cutoff']
    return args


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
    openai.api_key = args.api
    if mode == 'summary':
        summary_module = SummaryModule(args.root_dataset, args.root_summary)
        summary_module.summarize()
    if mode == 'query_localize':
        query_module = QueryModule(args.query_text)
        scores, files, texts = query_module.localize(args.root_summary, 
                                                     int(args.similarity_top_k), 
                                                     float(args.similarity_cutoff))
        print_info(scores, files, texts)
    if mode == 'query_extract':
        query_module = QueryModule(args.query_text)
        response = query_module.extract(args.root_extract_paper)
        print(response)
