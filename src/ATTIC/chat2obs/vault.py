# via ObsidianSandbox.ipynb
from pathlib import Path
import pickle
import re
import yaml

import networkx as nx


def read_yaml(txt):
    return yaml.load(txt, yaml.Loader)

def extract_frontmatter(doc):
    front, body = {}, doc
    if doc.startswith('---'):
        front, body = doc.split("---",2)[1:]
        # let's just assume this always works for now
        front = read_yaml(front)
    return front, body.strip()


links_pat=re.compile("\[\[(.+?)\]\]")

def get_wikilinks(text):
    return re.findall(links_pat, text)

def clean_links(wikilinks, collect_aliases=False):
    """canonicalize aliases, standardize case"""
    if collect_aliases:
        raise NotImplemented
    outv = []
    for link in wikilinks:
        if '|' in link:
            try:
                link, alias = link.split('|')
            except:
                print(link)
                raise
        outv.append(link.lower())
    return outv


class ObsDoc:
    def __init__(self, title, raw):
        self.title = title
        self.raw = raw
        self.frontmatter, self.body = extract_frontmatter(raw)
        self.links = clean_links(get_wikilinks(self.body)) # TODO: handle aliases
        self.tags = self.frontmatter.get('tags')
        
    @property
    def node_name(self):
        """canonicalized title"""
        return self.title.lower()
    
    @classmethod
    def from_path(cls, fpath):
        fpath = Path(fpath)
        with fpath.open() as f:
            try:
                return cls(fpath.stem, f.read())
            except Exception as e:
                print(fpath)
                raise e


def load_vault(obs_root):
    obs_root = Path(obs_root)
    corpus = [ObsDoc.from_path(fpath) for fpath in obs_root.glob("*.md")]        
    return corpus


def obs_docs_to_graph(corpus):
    G = nx.DiGraph()
    std_titles = []
    for doc in corpus:
        src = doc.title.lower()
        std_titles.append(src)
        edges = [(src,tgt) for tgt in doc.links]
        G.add_edges_from(edges)
    
    # Flag whether each node corresponds to a page that exists in the vault
    nx.set_node_attributes(G, False, 'exists')
    nx.set_node_attributes(G, {title:True for title in std_titles}, 'exists')
    
    return G


def identify_candidates(G):
    """
    Gets nodes in graph that correspond to hyperlinks to non-existent pages in the vault
    """
    candidates = [node for node, exists in nx.get_node_attributes(G, 'exists').items() if not exists]
    return candidates



if __name__ == '__main__':
    import pickle

    # git clone git@github.com:dmarx/obsidian_vault_TheShapeOfData_TopicBrainstorming.git
    obs_root = Path("../Obsidian Vault")
    corpus = load_vault(obs_root)
    G = obs_docs_to_graph(corpus)
    candidates = identify_candidates(G)

    fpath = obs_root / "chat.data"
    with open(fpath, 'wb') as f:
        data = {'corpus':corpus, 'G':G, 'candidates':candidates}
        pickle.dump(data, f)