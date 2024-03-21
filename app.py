import utils
import streamlit as st
import collections
import os

st.title('Simple Search')

utils.get_indices()

if 'page_count' not in st.session_state:
    st.session_state['page_count'] = 0

if 'to_see' not in st.session_state:
    st.session_state['to_see'] = 10

if 'additional_context' not in st.session_state:
    st.session_state['additional_context'] = collections.defaultdict(str)

DIRS = [d for d in os.listdir('./indices') if (d != 'transcript_answers_index') and (d != 'national_archive_bydoc') and (d != 'national_archive_index_104') and (d != '.DS_Store')]
DIRS = [d for d in DIRS if ('bydoc' not in d)]
print(DIRS)

query_str = st.text_input('Search for a word or phrase', on_change=utils.reset_pages)
choice = st.selectbox('What documents would you like to search in?', DIRS, format_func=lambda x: x.replace('_index', '').replace('_', ' ').replace('docs', '').title()+' documents')
to_see = st.number_input('How many results would you like to see per page?', value=10)
stemmer = st.toggle('Use stemming', help='If selected, the search will use stemming to find words with the same root. For example, "running" will match "run" and "ran".', on_change=utils.reset_pages)

if query_str != '':
    dl = utils.DataLoader(choice)
    searcher = utils.Searcher(query_str, dl, stemmer)
    searcher.search(to_see)