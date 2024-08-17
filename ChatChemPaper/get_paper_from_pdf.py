import fitz
import re
import os
from docx import Document
from PIL import Image
import matplotlib.pyplot as plt
from IPython.display import display


def get_section_format_dict(section_list):
    # Get chapter titles in all formats
    if not isinstance(section_list, list):
        section_list = [section_list]
    all_format_section_dict = {}
    for section_name in section_list:
        assert section_name[0].isupper(), 'section name must be capitalized!'
        all_format_section_dict[section_name] = [section_name, section_name.upper()]
        if len(section_name.split()) > 1:
            all_format_section_dict[section_name].append(section_name[0] + section_name[1:].lower())
        if section_name == 'Abstract':
            all_format_section_dict[section_name].append('A B S T R A C T')
    return all_format_section_dict


SECTION_LIST = ['Abstract',
                'Introduction',
                'Related Work', 'Background', 'Preliminary', 'Problem Formulation',
                'Methods', 'Methodology', 'Method', 'Approach', 'Approaches',
                'Material and Methods', 'Materials and Methods',
                'Experiment Settings', 'Experimental Methods', 'Experiment', 'Experimental', 'Experimental Results', 'Experiment and Result',
                'Experiments', 
                'Findings', 'Data Analysis', 'Evaluation',
                'Discussion', 'Conclusion', 'Conclusions', 'Experimental Section', 'Results and Discussion', 'Results',
                'References', 'References and Recommended Reading', 'References and Notes', 'Acknowledgements',
                'Conflict of Interest']
SECTION_FORMAT_DICT = get_section_format_dict(SECTION_LIST)  # 章节格式字典: 全大写、仅首字母大写
SECTION_FORMAT_NAMES = sum(SECTION_FORMAT_DICT.values(), [])


def find_key_in_section_format_dict(value):
    for k, v in SECTION_FORMAT_DICT.items():
        if value.strip() in v:
            return k


def process_text(text):
    return re.sub('\s+', ' ', text.replace('-\n', '').replace('\n', ' '))


class Paper:
    def __init__(self, path):
        # Initialize function to initialize the Paper object based on the PDF path
        self.path = path  # pdf path
        self.pdf = fitz.open(self.path)  # pdf document
        self.title = self.get_title()
        self.abstract = ''
        self.introduction = ''
        self.method = ''
        self.conclusion = ''
        self.parse_pdf()
        self.pdf.close()

    def get_title(self):
        max_font_size = 0
        max_font_sizes = [0]
        for page in self.pdf:
            for block in page.get_text('dict')['blocks']:  #Traverse each text block
                if block['type'] == 0 and len(block['lines']):  
                    if len(block['lines'][0]['spans']):
                        font_size = block['lines'][0]['spans'][0]['size']  
                        max_font_sizes.append(font_size)
                        if font_size > max_font_size:
                            max_font_size = font_size
        max_font_sizes.sort()
        cur_title = ''
        for page in self.pdf:  #Traverse each page
            for block in page.get_text('dict')['blocks']:  
                if block['type'] == 0 and len(block['lines']):  
                    if len(block['lines'][0]['spans']):
                        cur_string = block['lines'][0]['spans'][0]['text']
                        font_size = block['lines'][0]['spans'][0]['size']  
                        if abs(font_size - max_font_sizes[-1]) < 0.3 or abs(font_size - max_font_sizes[-2]) < 0.3:
                            for line_idx in range(1, len(block['lines'])):  
                                if font_size == block['lines'][line_idx]['spans'][0]['size']:
                                    cur_string += ' ' + block['lines'][line_idx]['spans'][0]['text']
                            if len(cur_string) > 4 and 'arXiv' not in cur_string and cur_string not in SECTION_FORMAT_NAMES:
                                if cur_title == '':
                                    cur_title += cur_string
                                else:
                                    cur_title += ' ' + cur_string
        title = cur_title.replace('\n', ' ')
        if title[: len(title) // 2] == title[len(title) // 2 + 1:]:
            return title[: len(title) // 2]
        else:
            return title

    def parse_pdf(self):
        self.all_text = process_text(' '.join([page.get_text() for page in self.pdf]))
        intext_section_page_dict = self.__get_all_section_page()  # 段落与页码的对应字典
        self.section_page_dict = {find_key_in_section_format_dict(k): v for k, v in intext_section_page_dict.items()}
        self.section_text_dict = self.__get_all_section_text(intext_section_page_dict)  # 段落与内容的对应字典
        self.abstract = self.__get_abstract()
        self.introduction = self.__get_introduction()
        self.method = self.__get_method()
        self.conclusion = self.__get_conclusion()
    
    def __get_all_section_page(self):
        
        true_section_page_dict = {}
        
        for page_index, page in enumerate(self.pdf):
           
            cur_text = page.get_text()
            
            for section_format_name in SECTION_FORMAT_NAMES:
                if section_format_name in ['Abstract', 'ABSTRACT', 'A B S T R A C T'] and section_format_name in cur_text:
                    true_section_page_dict[section_format_name] = page_index
                else:
                    if re.findall(f'{section_format_name} *\n', cur_text):
                        true_section_page_dict[section_format_name] = page_index
        # 返回所有找到的章节名称及它们在文档中出现的页码
        return true_section_page_dict

    def __get_all_section_text(self, section_page_dict):
        '''
        

        Returns:
            section_dict (dict): The text information dictionary for each chapter,
                                 where key is the chapter name and value is the chapter text.
        '''
        section_text_dict = {}
       
        text_list = [page.get_text() for page in self.pdf]
        for sec_index, sec_name in enumerate(section_page_dict):
            start_page = section_page_dict[sec_name]
            if sec_index < len(list(section_page_dict.keys()))-1:
                end_page = section_page_dict[list(section_page_dict.keys())[sec_index+1]]
            else:
                end_page = len(text_list)
            cur_sec_text = ''
            if end_page - start_page == 0:
                if sec_index < len(list(section_page_dict.keys()))-1:
                    next_sec = list(section_page_dict.keys())[sec_index+1]
                    if text_list[start_page].find(sec_name) == -1:
                        start_i = text_list[start_page].find(sec_name.upper())
                    else:
                        start_i = text_list[start_page].find(sec_name)
                    if text_list[start_page].find(next_sec) == -1:
                        end_i = text_list[start_page].find(next_sec.upper())
                    else:
                        end_i = text_list[start_page].find(next_sec)
                    cur_sec_text += text_list[start_page][start_i:end_i]
            else:
                for page_i in range(start_page, end_page+1):
                    if page_i == start_page:
                        if text_list[page_i].find(sec_name) == -1:
                            start_i = text_list[page_i].find(sec_name.upper())
                        else:
                            start_i = text_list[page_i].find(sec_name)
                        cur_sec_text += text_list[page_i][start_i:]
                    elif page_i < end_page:
                        cur_sec_text += text_list[page_i]
                    elif page_i == end_page:
                        if sec_index < len(list(section_page_dict.keys()))-1:
                            next_sec = list(section_page_dict.keys())[sec_index+1]
                            if text_list[page_i].find(next_sec) == -1:
                                end_i = text_list[page_i].find(next_sec.upper())
                            else:
                                end_i = text_list[page_i].find(next_sec)
                            cur_sec_text += text_list[page_i][:end_i]
            section_text_dict[find_key_in_section_format_dict(sec_name)] = process_text(cur_sec_text)
        return section_text_dict

    def __get_abstract(self):
        if 'Abstract' in self.section_text_dict.keys():
            return self.section_text_dict['Abstract']
        elif 'Introduction' in self.section_page_dict.keys():
            introduction_page = self.section_page_dict['Introduction']
            self.section_page_dict['Abstract'] = introduction_page
            page_text = process_text(self.pdf[introduction_page].get_text())
            tmp = page_text.find('Introduction')
            introduction_idx = tmp if tmp != -1 else page_text.find('INTRODUCTION')
            abstract_text = page_text[:introduction_idx] if introduction_idx > 200 else page_text
            self.section_text_dict['Abstract'] = abstract_text
            return abstract_text
        else:
            return ''

    def __get_introduction(self):
        if 'Introduction' in self.section_text_dict.keys():
            introduction_text = self.section_text_dict['Introduction']
        elif 'Abstract' in self.section_page_dict.keys():
            abstract_page = self.section_page_dict['Abstract']
            introduction_text = process_text(self.pdf[abstract_page].get_text()).replace(self.abstract, '')
        else:
            introduction_text = ''
        return introduction_text if introduction_text else self.abstract

    def __get_method(self):
        supp_text = self.__get_supp_text()
        section_name_method = ""
        for section_name in self.section_text_dict.keys():
            if "method" in section_name.lower() or "approach" in section_name.lower() or "experiment" in section_name.lower():
                section_name_method = section_name
                break
        if section_name_method:
            return self.section_text_dict[section_name_method] + supp_text
        else:
            abs_idx = max(self.all_text.find('Abstract'), self.all_text.find('ABSTRACT'), self.all_text.find('A B S T R A C T'))
            start_idx = len(self.all_text) if abs_idx != -1 else 0
            intro_idx = max(self.all_text.find('Introduction'), self.all_text.find('INTRODUCTION'))
            start_idx = max(start_idx, intro_idx)
            end_idx = self.all_text.rfind('Reference')
            return self.all_text[start_idx:end_idx] + supp_text

    def __get_supp_text(self):
        supp_text = ''
        idx = self.path.rfind('/')
        for file in os.listdir(self.path[:idx+1]):
            if file.endswith('.docx'):
                doc = Document(file)
                for para in doc.paragraphs:
                    supp_text += para.text
        return supp_text

    def __get_conclusion(self):
        section_name_conclusion = ""
        for section_name in self.section_text_dict.keys():
            if "conclu" in section_name.lower():
                section_name_conclusion = section_name
                break
        if section_name_conclusion:
            return self.section_text_dict[section_name_conclusion]
        else:
            return ''
    
    def get_images(self, show=False):
        imgs = []
        pdf = fitz.open(self.path)
        for i in range(1, pdf.xref_length()):
            isImg = re.search(r"/Subtype(?= */Image)", pdf.xref_object(i))
            isDCTDecode = re.search(r"/Filter /DCTDecode", pdf.xref_object(i))  # ensure image type (use filter in xref)
            if isImg and isDCTDecode:
                pix = fitz.Pixmap(pdf, i)
                if pix.size > 100000:
                    cspace = pix.colorspace
                    if cspace is None:
                        mode = "L"
                    elif cspace.n == 1:
                        mode = "L" if pix.alpha == 0 else "LA"
                    elif cspace.n == 3:
                        mode = "RGB" if pix.alpha == 0 else "RGBA"
                    else:
                        mode = "CMYK"
                    img = Image.frombytes(mode, (pix.width, pix.height), pix.samples)
                    imgs.append(img)
                    if show:
                        display(img)
        if not show:
            return imgs

    @property
    def experiment_text(self):
        keys = ['Material and Methods', 'Materials and Methods',
                'Experiment Settings', 'Experimental Methods', 'Experiment', 'Experimental', 'Experimental Results', 'Experiment and Result',
                'Experiments',
                'Experimental Section'
        ]
        for key in keys:
            if key in self.section_text_dict:
                return self.section_text_dict[key]
        return self.all_text


if __name__ == '__main__':
    paper = Paper(path='./NewOne/1.pdf')
    print('Materials+and+Methods' in paper.all_text)
