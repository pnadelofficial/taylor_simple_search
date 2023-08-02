import streamlit as st
import pandas as pd
from whoosh.index import open_dir
import os
from whoosh.qparser import QueryParser
from whoosh import sorting
from string import punctuation
from datetime import datetime
import gdown 

st.title('Simple Search')

if 'page_count' not in st.session_state:
    st.session_state['page_count'] = 1

if 'to_see' not in st.session_state:
    st.session_state['to_see'] = 10

if 'start' not in st.session_state:
    st.session_state['start'] = 0

@st.cache_data
def get_indices():
    os.makedirs('indices', exist_ok=True)
    os.chdir('indices')
    # nat archive
    nat_archive_url = 'https://drive.google.com/drive/folders/1Ew0mU1l7Y3M1CgD0RBZbfbp-tCwBFVga?usp=sharing'
    gdown.download_folder(nat_archive_url, quiet=True, use_cookies=False)
    # ws
    statements_url = 'https://drive.google.com/drive/folders/1Gsi1UUGxDrIn5j-kzFaE7yI41jPzwnVS?usp=sharing'
    gdown.download_folder(statements_url, quiet=True, use_cookies=False)
    # transcripts
    transcripts_url = 'https://drive.google.com/drive/folders/1YR9KRs_ImSSQ4kT1QQR-zOAfmXyANrMl?usp=sharing'
    gdown.download_folder(transcripts_url, quiet=True, use_cookies=False)
    os.chdir('..')
get_indices()

query_str = st.text_input('Search for a word or phrase')
with st.expander('Click for further information on how to construct a query.'):
    st.markdown("""
    * If you'd like to search for just a single term, you can enter it in the box above. 
    * If you'd like to search for a phrase, you can enclose it in quotations, such as "Macfarlane Trust". (TODO: highlighting is buggy with quotations, output is still correct)
    * A query like "Macfarlane Trust"~5 would return results where "Marcfarlane" and "Trust" are at most 5 words away from each other.
    * AND can be used as a boolean operator and will return results where two terms are both in a passage. AND is automatically placed in a query of two words, so Macfarlane Trust is internally represented as Macfarlane AND Trust.
    * OR can be used as a boolean operator and will return results where either one of two terms are in a passage.
    * NOT can be used as a boolean operator and will return results which do not include the term following the NOT.
    * From these boolean operators, one can construct complex queries like: HIV AND Haemophilia NOT "Hepatitis C". This query would return results that have both HIV and Haemophilia in them, but do not have Hepatitis C.
    * Parentheses can be used to group boolean statements. For example, the query Haemophilia AND ("Hepatitis C" OR  HIV) would return results that have Haemophilia and either Hepatitis C or HIV in them. (TODO: highlighting is buggy with parentheses, output is still correct)
    * If you'd like to search in a specific date range, you can specify it with the date: field. For example, date:[20210101:20220101] HIV would return results between January 1st, 2021 and January 1st, 2022 that have HIV in them.
    """)

dirs = os.listdir('./indices')
choice = st.selectbox('What documents would you like to search in?', dirs, format_func=lambda x: x.replace('_index', '').replace('_', ' ').title()+' documents')
ix = open_dir(f'./indices/{choice}')

if choice == 'national_archive_index':
    cats = sorting.FieldFacet("category")
    cat_choice = st.selectbox('What category of the National Archive data would you like to search in?', ['HIV', 'Haemophilia', 'Hep_C', 'Litigation and Compensation'], format_func=lambda x: x.replace('_', ' '))
else:
    cats = None

to_see = st.number_input('How many results would you like to see per page?', value=10)

with st.sidebar:
    if st.button('See next page', key='next'):
        st.session_state.start = st.session_state.start + to_see
        st.session_state.to_see = st.session_state.to_see + to_see
        st.session_state.page_count += 1

    if st.button('See previous page', key='prev'):
        st.session_state.to_see = st.session_state.to_see - to_see
        st.session_state.start = st.session_state.start - to_see
        st.session_state.page_count -= 1

def escape_markdown(text):
    '''Removes characters which have specific meanings in markdown'''
    MD_SPECIAL_CHARS = "\`*_{}#+"
    for char in MD_SPECIAL_CHARS:
        text = text.replace(char, '').replace('\t', '')
    return text

def no_punct(word):
    '''Util for below to remove punctuation'''
    return ''.join([letter for letter in word if letter not in punctuation.replace('-', '')])

def inject_highlights(text, searches):
    '''Highlights words from the search query''' 
    esc = punctuation + '"' + '."' + '..."'
    inject = f"""
        <p>
        {' '.join([f"<span style='background-color:#fdd835'>{word}</span>" if (no_punct(word.lower()) in searches) and (word not in esc) else word for word in text.split()])}
        </p>
        """ 
    return inject   

if query_str != '':
    parser = QueryParser("text", ix.schema)
    query = parser.parse(query_str)
    searches = [q.lower() for q in query_str.split(' ') if (q != 'AND') and (q != 'OR') and (q != 'NOT')]

    with ix.searcher() as searcher:
        results = searcher.search_page(query, st.session_state['page_count'], st.session_state['to_see']//2, groupedby=cats) # sortedby=None works! to add later
        if choice == 'national_archive_index':
            hits = results.results.groups()[cat_choice]
            for res in hits[st.session_state.start:st.session_state.start+st.session_state.to_see]:
                r = searcher.stored_fields(res)
                st.markdown(f"<small><b>Filename: {r['title']}</b></small>", unsafe_allow_html=True)
                st.markdown(f"<small><b>Date: {datetime.strftime(r['date'], '%B %-d, %Y')}</b></small>", unsafe_allow_html=True)
                st.markdown(inject_highlights(escape_markdown(r['text'].replace('\n --', ' --')),searches), unsafe_allow_html=True) 
                st.markdown("<hr style='width: 75%;margin: auto;'>", unsafe_allow_html=True)
        else:
            for r in results:
                st.markdown(f"<small><b>Filename: {r['title']}</b></small>", unsafe_allow_html=True)
                st.markdown(f"<small><b>Date: {datetime.strftime(r['date'], '%B %-d, %Y')}</b></small>", unsafe_allow_html=True)
                st.markdown(inject_highlights(escape_markdown(r['text'].replace('\n --', ' --')),searches), unsafe_allow_html=True) 
                st.markdown("<hr style='width: 75%;margin: auto;'>", unsafe_allow_html=True)
        st.write(f'Page: {st.session_state.page_count} of {len(results)//to_see}')