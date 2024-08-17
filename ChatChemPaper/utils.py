import re

def filter_papers(response):
    source_nodes = response.source_nodes
    scores_tmp = [node.score for node in source_nodes]  # score是否需要合并
    files_tmp = [node.node.extra_info['file_name'] for node in source_nodes]
    texts_tmp = [node.node.text for node in source_nodes]
    is_exist_dict = {}
    scores, files, texts = [], [], []
    for idx, file in enumerate(files_tmp):
        if file not in is_exist_dict:
            is_exist_dict[file] = 1
            scores.append(scores_tmp[idx])
            files.append(files_tmp[idx])
            texts.append(texts_tmp[idx])
    return scores, files, texts


def print_info(scores, files, texts):
    print('*'*60)
    print(f'【已筛选出以下的论文】')
    print('*'*60)
    for score, file, text in zip(scores, files, texts):
        with open(file, 'r') as f:
            paper_title = f.read().split('\n')[1].split('1. Title:')[-1].strip()
        print(f'【论文相关度】: \n{score}: ')
        print(f'【论文名称】: \n{paper_title}')
        print(f'【存储路径】: \n{file}')
        print(f'【相关段落】: \n{text}')
        print('*'*60)

def process_text(text):
    return re.sub('\s+', ' ', text.replace('-\n', '').replace('\n', ' '))
