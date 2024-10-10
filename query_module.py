from llama_index import Document
from llama_index import VectorStoreIndex
from llama_index import GPTVectorStoreIndex
from llama_index import SimpleDirectoryReader
from llama_index import ServiceContext
from llama_index import StorageContext
from llama_index.embeddings import OpenAIEmbedding

from llama_index import get_response_synthesizer
from llama_index import Prompt
from llama_index.query_engine import RetrieverQueryEngine
from llama_index.retrievers import VectorIndexRetriever
from llama_index.indices.postprocessor import SimilarityPostprocessor

from paper_analyst import Paper


def filter_papers(response):
    """Filter papers that have been summarized.

    Args:
        response (_type_): query engine response

    Returns:
        list, list, list: similarity, file paths, texts
    """
    source_nodes = response.source_nodes
    scores_tmp = [node.score for node in source_nodes]
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


class QueryModule:
    def __init__(self, query_text):
        self.query_text = query_text

    def localize(self, summary_path, similarity_top_k=3, similarity_cutoff=0.7):
        """Localize papers the user queried.

        Args:
            summary_path (str): summary path
            similarity_top_k (int, optional): filter paper number. Defaults to 3.
            similarity_cutoff (float, optional): similarity threshold. Defaults to 0.7.

        Returns:
            list, list, list: similarity, file paths, texts
        """
        if not summary_path.endswith('/'):
            summary_path += '/'
        # SimpleDirectoryReader = download_loader("SimpleDirectoryReader")
        filename_fn = lambda filename: {"file_name": filename}
        docs = SimpleDirectoryReader(summary_path, recursive=True, exclude_hidden=True, file_metadata=filename_fn).load_data()
        service_context = ServiceContext.from_defaults(chunk_size_limit=1024)
        storage_context = StorageContext.from_defaults()
        index = GPTVectorStoreIndex.from_documents(
            docs,
            service_context=service_context,
            storage_context=storage_context,
        )
        retriever = VectorIndexRetriever(
            index=index,
            similarity_top_k=similarity_top_k,
        )
        synth = get_response_synthesizer()
        node_postprocessors=[SimilarityPostprocessor(similarity_cutoff=similarity_cutoff)]
        query_engine = RetrieverQueryEngine(
            retriever=retriever,
            response_synthesizer=synth,
            node_postprocessors=node_postprocessors
        )
        response = query_engine.query(self.query_text)
        scores, files, texts = filter_papers(response)
        return scores, files, texts

    def extract(self, pdf_path):
        """Extract reagents and synthesis procedure from a paper.

        Args:
            pdf_path (str): pdf path
        """
        paper = Paper(pdf_path)
        paper_text = paper.experiment_text
        docs = [Document(text=paper_text)]
        embed_model = OpenAIEmbedding()
        service_context = ServiceContext.from_defaults(embed_model=embed_model, chunk_size_limit=2048)
        nodes = service_context.node_parser.get_nodes_from_documents(docs)
        for node in nodes:
            node.metadata["chunk_size"] = 2048
            node.excluded_embed_metadata_keys = ["chunk_size"]
            node.excluded_llm_metadata_keys = ["chunk_size"]
        paper_index = VectorStoreIndex(nodes)
        template = Prompt(template=(
            "You are a chemical researcher who is good at extracting information from an academic paper. \n"
            "Your task is to extract the reagents and the complete synthesis procedure of the target product. \n"
            "This is the text of the academic paper. \n"
            "---------------------\n"
            "{context_str}"
            "\n---------------------\n"
            "Given the text, please extract the reagents and the complete synthesis procedure of the target product: {query_str}\n"
            "Be sure to strictly follow the format. The format of the output are as follows: \n"
            "---------------------\n"
            "1. [Reagents Information] \n\n"
            " - Reagent 1 (chemical formula, relevant parameters), eg. Sodium oleate (NaOL, > 10.0%) \n\n"
            " - Reagent 2 (chemical formula, relevant parameters) \n\n"
            " - ... \n\n"
            "2. [Experimental Operation Information] \n\n"
            "---------------------\n"
            "In 1. [Reagents Information], for each reagent to be added, be sure to list the chemical formula. Please output as an unordered list. \n"
            "In 2. [Experimental Operation Information], please split experiment section text to several subsections. Please output as completely as possible. \n"
            "Be sure to strictly follow the format. \n"
        ))
        retriever = VectorIndexRetriever(
            index=paper_index,
            similarity_top_k=5,
        )
        synth = get_response_synthesizer(text_qa_template=template)
        query_engine = RetrieverQueryEngine(
            retriever=retriever,
            response_synthesizer=synth
        )
        response = query_engine.query(self.query_text)
        return response
