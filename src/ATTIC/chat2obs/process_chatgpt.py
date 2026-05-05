import json
from pathlib import Path

from .graph import (
    conversation_to_graph,
    process_conversation_graph__prompt_and_title, 
    subgraphs_to_articles,
)


def load_conversations(root):
    root = Path(root)
    fpath = root / "conversations.json"

    convs = json.load(fpath.open())
    return convs


def process_conv(conv):
    G = conversation_to_graph(conv)
    G = process_conversation_graph__prompt_and_title(G)
    return G 

def convs_to_articles(convs, filter_func=lambda c: True):
    subgraphs = [process_conv(c) for c in convs if filter_func(c)]
    articles = subgraphs_to_articles(subgraphs)
    return articles




if __name__ == '__main__':
    import pickle

    root = Path("data/ingestion/chatgpt/a40ff5f79c1b3edd3c366f0f628fb79170bae83ecf3a1758b5b258c71f843f53-2025-06-05-03-28-15-df2ed357a4e64443bf464446686c9692/")
    convs = load_conversations(root)
    articles = convs_to_articles(convs, filter_func=lambda c: c.get('gizmo_id'))
    
    fpath = "Downloads/articles-pickled_embed-e5mistral7b.test.data"
    with open(fpath, 'wb') as f:
        data = {'articles':articles}
        pickle.dump(data, f)