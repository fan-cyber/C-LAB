## 📋 **A chemical autonomous robotic platform for the synthesis of nanoparticles**

<div>
<span class="author-block">
  Fan Gao<sup>a†</sup>
</span>,
<span class="author-block">
  Hongqiang Li<sup>b†</sup>
</span>,
<span class="author-block">
  Zhilong Chen<sup>a†</sup>
</span>,
<span class="author-block">
   Yunai Yi<sup>b</sup>
</span>,
<span class="author-block">
  Shihao Nie<sup>c</sup>
</span>,
<span class="author-block">
  Zeming Liu<sup>c*</sup>
</span>,
<span class="author-block">
  Yuanfang Guo<sup>c</sup>
</span>,
<span class="author-block">
  Shumin Liu<sup>a</sup>
</span>,
<span class="author-block">
  Qizhen Qin<sup>a</sup>
</span>,
<span class="author-block">
  Zhengjian Li<sup>a</sup>
</span>,
<span class="author-block">
  Lisong Zhang<sup>d</sup>
</span>,
<span class="author-block">
  Han Hu<sup>d</sup>
</span>,
<span class="author-block">
  Cunjin Li<sup>d</sup>
</span>,
<span class="author-block">
  Liang Yang<sup>e</sup>
</span>,
<span class="author-block">
  Guangxu Chen<sup>a*</sup>
</span>
</div>

- **a.** School of Environment and Energy, State Key Laboratory of Luminescent Materials and Devices, Guangdong Provincial Key Laboratory of Atmospheric Environment and Pollution Control, South China University of Technology

- b. Zhuhai Fengze Information Technology Co., Ltd., Zhuhai 519000, China.

- c. School of Computer Science and Engineering, Beihang University, Beijing, 100191, China

- d. Guangzhou Inlab, Guangzhou 510530, China.

- e. School of Artificial Intelligence, Hebei University of Technology, Tianjin, 300401, China

  F. G., H. L. and Z.L. contributed to this work equally.

Email: cgx08@scut.edu.cn; zmliu@buaa.edu.cn

## ⭐Installation

**git clone**

```
git clone https://github.com/Nano-Cheng/C-LAB.git
cd C-LAB/ChatChemPaper
```

**conda env**

```
conda create --name chatchempaper python=3.8 -y
conda activate chatchempaper
```

**pip install**

```
pip install -r requirements.txt
```

**Dataset**

This project utilizes custom datasets collected and organized by our team. To set up the datasets:

1. Download the dataset from [Google Drive](https://drive.google.com/file/d/1iELKCFNAL1uaEMM30rFa9PRcQ91E2fUc/view?usp=sharing).
2. Unzip the dataset to the `./ChatChemPaper/Dataset/papers` folder.

## 🌲Structure

```
├─Astar
│  ├─Automated Script
│  ├─Code
│  ├─Data
│  └─InLab Solution
└─ChatChemPaper
    ├─Dataset
      └─papers
        ├─paper1.pdf
        ├─paper2.pdf
        ├─paper3.pdf
        ...
    ├─config.json
    ├─main.py
    ├─paper_analyst.py
    ├─query_module.py
    ├─requirements.txt
    └─summary_module.py
```

## ⚙️ Usage

### Astar

This folder contains four parts: automation platform operation software, automation scripts, A* algorithm code, and data for Astar code execution.

#### 1. InLab Solution
This project is an installation package for automation platform software.

#### 2. Automated Script
This project includes all automation scripts related to the synthesis and characterization of nanomaterials (mth files or pzm files). To run the corresponding files, the mth files or pzm files need to be placed in the following path of the software: :\InLab Solution\Resource\System Method

#### 3. Code
This project includes A * algorithm code for optimizing synthesis parameters of Au NRs, Au NSs, and Ag NCs.

#### 4. Data
This project includes synthesis parameter files and UV-Vis data for Au NRs, Au NSs, and Ag NCs. This part of the data is available for algorithm execution.

### ChatChemPaper

#### 1. Settings

Before running the project, configure your OpenAI API key and custom parameters in `config.json`.

#### 2. Summary

```
cd ChatChemPaper
python main.py --mode 'summary'
```
#### 3. Query-Localize

```
cd ChatChemPaper
python main.py --mode 'query_localize' --query_text 'Au NRs'
```

#### 4. Query-Extract

```
cd ChatChemPaper
python main.py --mode 'query_extract' --query_text 'Au NRs' --extract_pdf_path '{your pdf path}'
```

## 💗 Acknowledgements
We appreciate the financial support from the National Nature Science Foundation of China (21971070), Guangdong Innovative and Entrepreneurial Research Team Program (2019ZT08L075), Guangdong Pearl River Talent Program (2019QN01L159), Science and Technology Program of Guangzhou, China (202103040002). We thank professor Li Xia from South China University of technology for his helpful discussion on the algorithm in this work.

## 🛎 Citation
If you find our work helpful for your research, please cite:
```bib
```
