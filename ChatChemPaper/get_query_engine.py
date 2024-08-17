from llama_index import get_response_synthesizer
from llama_index import Prompt
from llama_index.query_engine import RetrieverQueryEngine
from llama_index.retrievers import VectorIndexRetriever
from llama_index.indices.postprocessor import SimilarityPostprocessor


def get_summary_query_engine(index, query_text, similarity_top_k=5, similarity_cutoff=0.7):
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
    response = query_engine.query(query_text)
    return response


def get_paper_query_engine(index, query_text):
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
        "2. [Experimental Operation Information] \n\n"
        "---------------------\n"
        "In 1. [Reagents Information], for each reagent to be added, be sure to list the chemical formula. Please output as an unordered list. \n"
        "In 2. [Experimental Operation Information], please split experiment section text to several subsections. Please output as completely as possible. \n"
        "Be sure to strictly follow the format. \n"
    ))
    retriever = VectorIndexRetriever(
        index=index,
        similarity_top_k=5,
    )
    synth = get_response_synthesizer(text_qa_template=template)
    query_engine = RetrieverQueryEngine(
        retriever=retriever,
        response_synthesizer=synth
    )
    response = query_engine.query(query_text)
    return response
