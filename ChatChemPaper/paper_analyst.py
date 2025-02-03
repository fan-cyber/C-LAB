import re
import fitz
from pathlib import Path
from docx import Document
from PIL import Image


def get_section_format_dict(section_list):
    """Get section titles in all formats
    eg. Abstract -> Abstract, ABSTRACT, A B S T R A C T

    Args:
        section_list (list): param SECTION_LIST

    Returns:
        dict: dict of section titles
    """
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
SECTION_FORMAT_DICT = get_section_format_dict(SECTION_LIST)
SECTION_FORMAT_NAMES = sum(SECTION_FORMAT_DICT.values(), [])


def find_key_in_section_format_dict(value):
    """Find the key in SECTION_FORMAT_DICT by value

    Args:
        value (str): dict value

    Returns:
        str: dict key
    """
    for k, v in SECTION_FORMAT_DICT.items():
        if value.strip() in v:
            return k


def process_text(text):
    """Process text by removing unnecessary spaces and line breaks.

    Args:
        text (str): raw text

    Returns:
        str: processed text
    """
    return re.sub('\s+', ' ', text.replace('-\n', '').replace('\n', ' '))


class Paper:
    def __init__(self, pdf_path):
        self.path = Path(pdf_path)
        self.pdf = fitz.open(self.path)
        self.title = self.get_title()
        self.abstract = ''
        self.introduction = ''
        self.method = ''
        self.conclusion = ''
        self.parse_pdf()
        self.pdf.close()

    def get_title(self):
        """Get the title of the paper.

        Returns:
            str: paper title
        """
        max_font_size = 0
        max_font_sizes = [0]
        for page in self.pdf:
            for block in page.get_text('dict')['blocks']:  # each text block
                if block['type'] == 0 and len(block['lines']):  # if is text (not image, etc.)
                    if len(block['lines'][0]['spans']):
                        font_size = block['lines'][0]['spans'][0]['size']  # Get the font size of the first line and first paragraph of text
                        max_font_sizes.append(font_size)
                        if font_size > max_font_size:
                            max_font_size = font_size
        max_font_sizes.sort()
        cur_title = ''
        for page in self.pdf:  # each page
            for block in page.get_text('dict')['blocks']:  # each text block
                if block['type'] == 0 and len(block['lines']):  # if is text (not image, etc.)
                    if len(block['lines'][0]['spans']):
                        cur_string = block['lines'][0]['spans'][0]['text']
                        font_size = block['lines'][0]['spans'][0]['size']  # font size
                        if abs(font_size - max_font_sizes[-1]) < 0.3 or abs(font_size - max_font_sizes[-2]) < 0.3:
                            for line_idx in range(1, len(block['lines'])):  # if the title has multiple lines
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
        """Parse the pdf file and extract the abstract, introduction, method, and conclusion.
        """
        self.all_text = process_text(' '.join([page.get_text() for page in self.pdf]))
        intext_section_page_dict = self.__get_all_section_page()  # 段落与页码的对应字典
        self.section_page_dict = {find_key_in_section_format_dict(k): v for k, v in intext_section_page_dict.items()}
        self.section_text_dict = self.__get_all_section_text(intext_section_page_dict)  # 段落与内容的对应字典
        self.abstract = self.__get_abstract()
        self.introduction = self.__get_introduction()
        self.method = self.__get_method()
        self.conclusion = self.__get_conclusion()
    
    def __get_all_section_page(self):
        """Initialize a dictionary to store the found chapters and their page numbers in the paper.

        Returns:
            dict: dict of section names and their page numbers
        """
        true_section_page_dict = {}
        for page_index, page in enumerate(self.pdf):  # each page
            cur_text = page.get_text()
            for section_format_name in SECTION_FORMAT_NAMES:
                if section_format_name in ['Abstract', 'ABSTRACT', 'A B S T R A C T'] and section_format_name in cur_text:
                    true_section_page_dict[section_format_name] = page_index
                else:
                    if re.findall(f'{section_format_name} *\n', cur_text):
                        true_section_page_dict[section_format_name] = page_index
        return true_section_page_dict

    def __get_all_section_text(self, section_page_dict):
        '''
        Retrieve the text information of each page in the PDF file, and organize the text information into a dictionary by chapter for return.

        Returns:
            section_dict (dict): The text information dictionary for each chapter, where key is the chapter name and value is the chapter text.
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
        """Get the abstract of the paper.

        Returns:
            str: abstract text
        """
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
        """Get the introduction of the paper.

        Returns:
            str: introduction text
        """
        if 'Introduction' in self.section_text_dict.keys():
            introduction_text = self.section_text_dict['Introduction']
        elif 'Abstract' in self.section_page_dict.keys():
            abstract_page = self.section_page_dict['Abstract']
            introduction_text = process_text(self.pdf[abstract_page].get_text()).replace(self.abstract, '')
        else:
            introduction_text = ''
        return introduction_text if introduction_text else self.abstract

    def __get_method(self):
        """Get the method of the paper.

        Returns:
            str: method text
        """
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
        """Get the supplementary text of the paper.

        Returns:
            str: supplementary text
        """
        supp_text = ''
        parent = self.path.parent
        for file in parent.glob('*.docx'):
            doc = Document(str(file))
            for para in doc.paragraphs:
                supp_text += para.text
        return supp_text

    def __get_conclusion(self):
        """Get the conclusion of the paper.

        Returns:
            str: conclusion text
        """
        section_name_conclusion = ""
        for section_name in self.section_text_dict.keys():
            if "conclu" in section_name.lower():
                section_name_conclusion = section_name
                break
        if section_name_conclusion:
            return self.section_text_dict[section_name_conclusion]
        else:
            return ''

    def get_images(self):
        """Get the images in the paper.

        Returns:
            list: list of PIL.Image objects
        """
        imgs = []
        pdf = fitz.open(str(self.path))
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
        return imgs

    @property
    def experiment_text(self):
        """Get the text of the experimental section.

        Returns:
            str: text of the experimental section
        """
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
    paper = Paper(pdf_path='./nl304478h_si_001.pdf')
    with open('./all_text.txt', 'w', encoding='utf-8') as f:
        f.write(paper.all_text)
