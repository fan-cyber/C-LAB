import os
import openai
import tenacity
import tiktoken
from typing import List

from get_paper_from_pdf import Paper


def save_as_markdown(text, save_file):
    '''
        Summarize individual literature and save it as a markup file
    '''
    with open(save_file, 'w', encoding="utf-8") as f:
        f.write(text)


class Summarizer:
    def __init__(self, paper_path, summary_path):
        '''
        param:
            paper_path: The path to the PDF folder or individual PDF file of the literature
            summary_path: The folder path for saving literature summaries (markdowns)
        '''
        #################### Save all the literature in the literature library as a Paper class and store it in the paper_list ####################
        paper_list = []
        print('Loading papers...')
        if paper_path.endswith(".pdf"):
            paper_list.append(Paper(paper_path))
        else:
            for root, dirs, files in os.walk(paper_path):
                for filename in files:
                    if filename.endswith(".pdf"):
                        paper_list.append(Paper(path=os.path.join(root, filename)))
        print('done!')
        self.paper_list: List[Paper] = paper_list
        #################################### Set hyperparameters for coarse screening ####################################
        self.keyword = "chemistry"                      # Coarse screened keywords
        self.max_token_num = 4096                       # Maximum number of tokens for gpt3.5
        self.encoding = tiktoken.get_encoding("gpt2")   # Coarse screen encoder
        self.summary_path = summary_path
        if not os.path.exists(self.summary_path):
            os.makedirs(self.summary_path)

    def summarize(self):
        '''
            Summarize all literature, and save the summary of each literature as a markup file

            Step 1: First, summarize the entire text using title, abstract, and introduction

            Step 2: Summary method

            Step 3: Summary conclusion

            Step 4: Save the summarized results as a markup file
        '''
        markdown = []  # 单个markdown文件的内容
        for idx, paper in enumerate(self.paper_list, 1):
            print(f"[Paper {idx}: {paper.title}]")
            ########################################## Step1 ##########################################
            text = f"Title: {paper.title}\nAbstract: {paper.abstract}\nIntroduction: {paper.introduction}\n"
            try:
                chat_summary_text = self.chat_summary(text)
            except Exception as e:
                print("Summary Error: ", e)
                if "maximum context" in str(e):
                    current_tokens_index = str(e).find("your messages resulted in") + len("your messages resulted in") + 1
                    offset = int(str(e)[current_tokens_index: current_tokens_index + 4])
                    summary_prompt_token = offset + 1000 + 150
                    chat_summary_text = self.chat_summary(text, summary_prompt_token)
            markdown.append(f"### Summary\n{chat_summary_text}\n\n")

            ########################################## Step2 ##########################################
            text = f"<Summary>\n{chat_summary_text}\n\n<Method Summary>\n{paper.method}\n\n"
            try:
                chat_method_text = self.chat_method(text)
            except Exception as e:
                print("Method Error: ", e)
                if "maximum context" in str(e):
                    current_tokens_index = str(e).find("your messages resulted in") + len("your messages resulted in") + 1
                    offset = int(str(e)[current_tokens_index:current_tokens_index + 4])
                    method_prompt_token = offset + 800 + 150
                    chat_method_text = self.chat_method(text, method_prompt_token)
            markdown.append(f"### Method Summary\n{chat_method_text}\n\n")

            ########################################## Step3 ##########################################
            if paper.conclusion != "":
                text += f"<Conclusion>:\n{paper.conclusion}\n\n"
            try:
                chat_conclusion_text = self.chat_conclusion(text)
            except Exception as e:
                print("Conclusion Error: ", e)
                if "maximum context" in str(e):
                    current_tokens_index = str(e).find("your messages resulted in") + len("your messages resulted in") + 1
                    offset = int(str(e)[current_tokens_index:current_tokens_index + 4])
                    conclusion_prompt_token = offset + 800 + 150
                    chat_conclusion_text = self.chat_conclusion(text, conclusion_prompt_token)
            markdown.append(f"### Conclusion Summary\n{chat_conclusion_text}\n\n")

            ########################################## Step4 ##########################################
            filename_ori = paper.path.split("/")[-1][:-4]
            save_as_markdown("\n".join(markdown), f'{self.summary_path}{filename_ori}.md')
            markdown = []

    @tenacity.retry(wait=tenacity.wait_exponential(multiplier=1, min=4, max=10), stop=tenacity.stop_after_attempt(5), reraise=True)
    def chat_summary(self, text, summary_prompt_token=1100):
        '''
            Step1 detail
        '''
        text_token = len(self.encoding.encode(text))
        clip_text_index = int(len(text) * (self.max_token_num - summary_prompt_token) / text_token)
        clip_text = text[:clip_text_index]
        messages = [
            {"role": "system",
             "content": "You are a researcher in the field of [" + self.keyword + "] who is good at summarizing papers using concise statements"},
            {"role": "assistant",
             "content": "This is the title, author, abstract and introduction of an English document. I need your help to read and summarize the following questions: " + clip_text},
            {"role": "user", "content": f"""
                 1. Mark the title of the paper.
                 2. Mark the keywords of this article.
                 3. Summarize according to the following four points.
                    - (1):What is the research background of this article?
                    - (2):What are the past methods? What are the problems with them? Is the approach well motivated?
                    - (3):What is the research methodology proposed in this paper?
                    - (4):On what task and what performance is achieved by the methods in this paper? Can the performance support their goals?
                 Follow the format of the output that follows:
                 1. Title: xxx\n
                 2. Keywords: xxx\n
                 3. Summary: \n
                    - (1):xxx;\n
                    - (2):xxx;\n
                    - (3):xxx;\n
                    - (4):xxx.\n
                 Be sure to use answers, statements as concise and academic as possible, do not have too much repetitive information, numerical values using the original numbers, be sure to strictly follow the format, the corresponding content output to xxx, in accordance with \n line feed.                 
                 """},
        ]
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
        )
        result = ""
        for choice in response.choices:
            result += choice.message.content
        print("[Summary Result]\n", result + "\n")
        print("prompt_token_used: ", response.usage.prompt_tokens)
        print("completion_token_used: ", response.usage.completion_tokens)
        print("total_token_used: ", response.usage.total_tokens)
        print("response_time: ", response.response_ms / 1000.0, "s\n")
        return result

    @tenacity.retry(wait=tenacity.wait_exponential(multiplier=1, min=4, max=10), stop=tenacity.stop_after_attempt(5), reraise=True)
    def chat_method(self, text, method_prompt_token=800):
        '''
            Step2 detail
        '''
        text_token = len(self.encoding.encode(text))
        clip_text_index = int(len(text) * (self.max_token_num - method_prompt_token) / text_token)
        clip_text = text[:clip_text_index]
        messages = [
            {"role": "system",
             "content": "You are a researcher in the field of [" + self.keyword + "] who is good at summarizing papers using concise statements"},
            {"role": "assistant",
             "content": "This is the <Summary> and <Summary Method> part of an English document, where <Summary> you have summarized, but the <Summary Method> part, I need your help to read and summarize the following questions: " + clip_text},
            {"role": "user", "content": f"""                 
                 4. Describe in detail the methodological idea of this article. For example, its steps are.
                    - (1):...
                    - (2):...
                    - (3):...
                    - .......
                 Follow the format of the output that follows: 
                 4. Methods: \n
                    - (1):xxx;\n
                    - (2):xxx;\n
                    - (3):xxx;\n
                    ....... \n  
                 Be sure to use answers, statements as concise and academic as possible, do not repeat the content of the previous <Summary>, the value of the use of the original numbers, be sure to strictly follow the format, the corresponding content output to xxx, in accordance with \n line feed, ....... means fill in according to the actual requirements, if not, you can not write.                 
                 """},
        ]
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
        )
        result = ""
        for choice in response.choices:
            result += choice.message.content
        print("[Method Result]\n", result + "\n")
        print("prompt_token_used: ", response.usage.prompt_tokens)
        print("completion_token_used: ", response.usage.completion_tokens)
        print("total_token_used: ", response.usage.total_tokens)
        print("response_time: ", response.response_ms / 1000.0, "s\n")
        return result

    @tenacity.retry(wait=tenacity.wait_exponential(multiplier=1, min=4, max=10), stop=tenacity.stop_after_attempt(5), reraise=True)
    def chat_conclusion(self, text, conclusion_prompt_token=800):
        '''
            Step3 detail
        '''
        text_token = len(self.encoding.encode(text))
        clip_text_index = int(len(text) * (self.max_token_num - conclusion_prompt_token) / text_token)
        clip_text = text[:clip_text_index]
        messages = [
            {"role": "system",
             "content": "You are a reviewer in the field of [" + self.keyword + "] and you need to critically review this article"},
            {"role": "assistant",
             "content": "This is the <Summary> and <Conclusion> part of an English literature, where <Summary> you have already summarized, but <Conclusion> part, I need your help to summarize the following questions: " + clip_text},
            {"role": "user", "content": f"""                 
                 5. Make the following summary.
                    - (1):What is the significance of this piece of work?
                    - (2):Summarize the strengths and weaknesses of this article in three dimensions: innovation point, performance, and workload.                   
                    .......
                 Follow the format of the output later: 
                 5. Conclusion: \n
                    - (1):xxx;\n                     
                    - (2):Innovation point: xxx; Performance: xxx; Workload: xxx;\n                      
                 Be sure to use answers, statements as concise and academic as possible, do not repeat the content of the previous <Summary>, the value of the use of the original numbers, be sure to strictly follow the format, the corresponding content output to xxx, in accordance with \n line feed, ....... means fill in according to the actual requirements, if not, you can not write.                 
                 """},
        ]
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
        )
        result = ""
        for choice in response.choices:
            result += choice.message.content
        print("[Conclusion Result]\n", result + "\n")
        print("prompt_token_used: ", response.usage.prompt_tokens)
        print("completion_token_used: ", response.usage.completion_tokens)
        print("total_token_used: ", response.usage.total_tokens)
        print("response_time: ", response.response_ms / 1000.0, "s\n")
        return result

    def section_name_scan(self):
        for paper in self.paper_list:
            print(paper.section_page_dict.keys(), paper.title)
