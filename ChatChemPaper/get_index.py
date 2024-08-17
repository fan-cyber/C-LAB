from llama_index import (
    Document,
    VectorStoreIndex,
    GPTVectorStoreIndex,
    SimpleDirectoryReader,
    ServiceContext,
    StorageContext,
)
from llama_index.embeddings import OpenAIEmbedding
from get_paper_from_pdf import Paper


def get_summary_index(summary_path, store_path):
    if not summary_path.endswith('/'):
        summary_path += '/'
#     SimpleDirectoryReader = download_loader("SimpleDirectoryReader")
    filename_fn = lambda filename: {"file_name": filename}
    docs = SimpleDirectoryReader(summary_path, recursive=True, exclude_hidden=True, file_metadata=filename_fn).load_data()
    service_context = ServiceContext.from_defaults(chunk_size_limit=1024)
    storage_context = StorageContext.from_defaults()
    index = GPTVectorStoreIndex.from_documents(
        docs,
        service_context=service_context,
        storage_context=storage_context,
    )
    storage_context.persist(persist_dir=store_path)
    return index


def get_paper_index(pdfpath):
    paper = Paper(pdfpath)
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
    return paper_index
