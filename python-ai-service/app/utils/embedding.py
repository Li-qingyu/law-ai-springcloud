from langchain_community.embeddings import DashScopeEmbeddings
from app.core.config import get_settings
from functools import lru_cache

@lru_cache()
def get_embedding_model():
    settings = get_settings()
    return DashScopeEmbeddings(
        dashscope_api_key=settings.DASHSCOPE_API_KEY,
        model=settings.EMBEDDING_MODEL
    )



"""
    将单个文本字符传转换为向量
    Args:
        text： str文本
    return：
        List[float]：浮点数向量
"""
def embed_text(text: str)-> list[float]:
    embedding_model = get_embedding_model()
    return embedding_model.embed_query(text)


"""
    批量将文本列表转换为向量列表

    Args:
        texts: 文本字符串列表

    Returns:
        List[List[float]]: 向量列表
"""
def embed_texts(texts: list[str]) -> list[list[float]]:
    embedding_model = get_embedding_model()
    return embedding_model.embed_documents(texts)

if __name__ == '__main__':
    text="劳动合同"
    vector=embed_text(text)
    print(f"输入文本：{text}")
    print(f"向量：{vector[0:5]}")
    print(f"向量维度：{len(vector)}")
