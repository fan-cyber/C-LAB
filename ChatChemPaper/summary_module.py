import openai
import tenacity
import tiktoken
from tqdm import tqdm
from typing import List
from pathlib import Path

from paper_analyst import Paper


class SummaryModule:
    def __init__(self, root_dataset, root_summary):
        """Initialize the SummaryModule class.

        Args:
            paper_path (str): The PDF folder path or individual PDF file path of the literature
            summary_path (str): Save the folder path for the literature summary (markdown)
        """
        ############## Save all the papers in the folder as a Paper class and store it in a list ##############
        self.root_dataset = Path(root_dataset)
        self.root_summary = Path(root_summary)
        self.root_dataset.mkdir(parents=True, exist_ok=True)
        self.root_summary.mkdir(parents=True, exist_ok=True)
        root_papers = list(self.root_dataset.rglob('*.pdf'))
        self.papers: List[Paper] = []
        print('[Loading papers...]')
        for root_paper in tqdm(root_papers):
            self.papers.append(Paper(root_paper))
        print('[done!]')
        #################################### set hyper-param ####################################
        self.keyword = "chemistry"                      # keyword
        self.max_token_num = 4096                       # gpt3.5 max token
        self.encoding = tiktoken.get_encoding("gpt2")   # encoder

    def summarize(self):
        """Summarize all literature and save the summary of each literature as a markdown file
        Step 1: Summarize the entire text using title, abstract, and introduction
        Step 2: Summarize the method
        Step 3: Summarize the conclusion
        Step 4: Save the summarized results as a markdown file
        """
        for idx, paper in enumerate(self.papers, 1):
            print(f'[{idx}/{len(self.papers)}] {paper.path}')
            markdown = []
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
            content = '\n'.join(markdown)
            root_markdown = self.root_summary / (paper.path.stem + '.md')
            with open(root_markdown, 'w', encoding="utf-8") as f:
                f.write(content)
                print(f'[Summary Saved!] {root_markdown}')

    @tenacity.retry(wait=tenacity.wait_exponential(multiplier=1, min=4, max=10), stop=tenacity.stop_after_attempt(5), reraise=True)
    def chat_summary(self, text, summary_prompt_token=1100):
        """Step1 Prompt
        """
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
        response = openai.chat.completions.create(
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
        return result

    @tenacity.retry(wait=tenacity.wait_exponential(multiplier=1, min=4, max=10), stop=tenacity.stop_after_attempt(5), reraise=True)
    def chat_method(self, text, method_prompt_token=800):
        """Step2 Prompt
        """
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
        response = openai.chat.completions.create(
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
        return result

    @tenacity.retry(wait=tenacity.wait_exponential(multiplier=1, min=4, max=10), stop=tenacity.stop_after_attempt(5), reraise=True)
    def chat_conclusion(self, text, conclusion_prompt_token=800):
        """Step3 Prompt
        """
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
        response = openai.chat.completions.create(
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
        return result
