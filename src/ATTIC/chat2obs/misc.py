import re

def naive_title_extraction(text):
    """
    Returns title if first line is just a title suggestion and can be removed
    """
    # get first line
    top = text.strip().split("\n")[0]

    # title/section header detected
    outv = None
    if top.startswith("#"):
        outv = top.replace("#","").strip()
        # for i, char in enumerate(top):
        #     if char != "#":
        #         outv = top[i:]
        #         break
    # emphasized text
    elif top.startswith("**") and top.endswith("**"):
        #outv = top.split("**")[1]
        outv = top.replace("**","")
    return outv


def extract_proposed_title(text):
    """
    Assumes that an article was generated with a proposed title. If present, proposed title
    expected to present (on the first line) as:
    * title/section header
      - preceded by several #'s
    * emphasized content
      - encapsulated in **bold**, *emph*, _emph_, [[link]]...
    * prompt = title --> top line contains prompt
    """
    # get first line
    top = text.strip().split("\n")[0]

    # title/section header detected
    outv = None
    if top.startswith("#"):
        for i, char in enumerate(top):
            if char != "#":
                outv = top[i:]
                break
    # emphasized text
    elif top.startswith("**"):
        outv = top.split("**")[1]
    else:
        #pass
        # - emphasis - bold, italics
        # - quoted phrase
        for sep in ('**','*','"'):
            if (sep in top) and (len(top.split(sep))==3):
                outv = top.split(sep)[1]
                break
        # TODO: handle in-line wikilink
    
    if outv:
        outv = outv.strip()
        return outv



pat = re.compile("\[\[(.*?)\]\]")

def get_links(content):
    hits = re.findall(pat, content)
    return list(set(hits))


