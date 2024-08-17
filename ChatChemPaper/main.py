import openai
from paper_summarizer import Summarizer
from get_paper_from_pdf import Paper
from get_index import get_summary_index, get_paper_index
from get_query_engine import get_summary_query_engine, get_paper_query_engine
from utils import filter_papers, print_info


class ChatChemPaper:
    def __init__(self,
                 api_key: str,                  # api key
                 all_paper_path: str,           # 总论文库路径
                 all_summary_path: str,         # 总summary存储路径
                 all_storage_path: str,         # 总index存储路径
                 query_text: str,               # 用户提问
                 similarity_top_k: int,         # 粗筛过程中的取similarity_top_k篇最相似论文
                 similarity_cutoff: float,      # 粗筛过程中的相似度截断
                ):
        openai.api_key = api_key
        self.all_paper_path = all_paper_path
        self.all_summary_path = all_summary_path
        self.all_storage_path = all_storage_path
        self.query_text = query_text
        self.similarity_top_k = similarity_top_k
        self.similarity_cutoff = similarity_cutoff
    
    # Function 1: 遍历已有的总论文库文件夹，做每篇paper的summary，并保存到all_summary_path中。
    # 注意，每篇paper存储至all_summary_path中，命名为原始文件名，目前不包含文件的hash比对去重，此处需要改进。【待软件对接后实现】
    # Function 2: 对用户上传的paper做summary，若论文不存在则保存入总论文库(此时index尚未被更新，或许可以每天一更index)。
    # 本功能与Function1代码结构一致，只是需要修改路径，即需要一个临时论文库文件夹和一个临时summary的文件夹。
    def summarize_papers(self):
        summarizer = Summarizer(paper_path=self.all_paper_path, summary_path=self.all_summary_path)
        summarizer.summarize()

    # 总论文库summary的index
    def get_all_summary_index(self):
        summary_index = get_summary_index(summary_path=self.all_summary_path, store_path=self.all_storage_path)
        return summary_index

    # Function 3: 根据用户提问和总论文库summary的index，做出论文推荐
    # 返回相关论文相似度、相关论文存储路径、相关论文匹配区域
    def coarse_filter_papers(self):
        index = self.get_all_summary_index()
        response = get_summary_query_engine(index, self.query_text, self.similarity_top_k, self.similarity_cutoff)
        scores, files, texts = filter_papers(response)
        return scores, files, texts

    # 输出粗筛后信息
    def coarse_filter_papers_info(self, scores, files, texts):
        print_info(scores, files, texts)

    # Function 4: 对单篇paper，提取试剂和合成工艺
    def extract(self, file: str):
        paper_index = get_paper_index(file)
        response = get_paper_query_engine(paper_index, self.query_text)
        return response

    # Function 5: 对单篇paper，提取所有插图
    def get_images(self, file: str):
        paper = Paper(file)
        imgs = paper.get_images(show=False)
        return imgs
