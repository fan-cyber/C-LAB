### ChatChemPaper.summarize_papers()

遍历已有的总论文库文件夹，做每篇paper的summary，并保存到all_summary_path中。

注意，每篇paper存储至all_summary_path中，命名为原始文件名，目前不包含文件的hash比对去重

对用户上传的paper做summary。

本功能与Function1代码结构一致，只是需要修改路径，即需要一个临时论文库文件夹和一个临时summary的文件夹。

### ChatChemPaper.coarse_filter_papers()

根据用户提问和总论文库summary的index，做出论文推荐。

返回相关论文相似度、相关论文存储路径、相关论文匹配区域。

### ChatChemPaper.extract()

对单篇paper，提取试剂和合成工艺。

### ChatChemPaper.get_images()

对单篇paper，提取所有插图。