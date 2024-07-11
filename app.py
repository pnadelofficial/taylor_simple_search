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

with st.expander('Click for further information on how to construct a query.'):
    st.markdown("""
    * If you'd like to search for just a single term, you can enter it in the box above. 
    * If you'd like to search for a phrase, you can enclose it in quotations, such as "Macfarlane Trust".
    * A query like "Macfarlane Trust"~5 would return results where "Marcfarlane" and "Trust" are at most 5 words away from each other.
    * AND can be used as a boolean operator and will return results where two terms are both in a passage. AND is automatically placed in a query of two words, so Macfarlane Trust is internally represented as Macfarlane AND Trust.
    * OR can be used as a boolean operator and will return results where either one of two terms are in a passage.
    * NOT can be used as a boolean operator and will return results which do not include the term following the NOT.
    * From these boolean operators, one can construct complex queries like: HIV AND Haemophilia NOT "Hepatitis C". This query would return results that have both HIV and Haemophilia in them, but do not have Hepatitis C.
    * Parentheses can be used to group boolean statements. For example, the query Haemophilia AND ("Hepatitis C" OR  HIV) would return results that have Haemophilia and either Hepatitis C or HIV in them. 
    * If you'd like to search in a specific date range, you can specify it with the date: field. For example, date:[20210101 TO 20220101] HIV would return results between January 1st, 2021 and January 1st, 2022 that have HIV in them.
    """)

query_str = st.text_input('Search for a word or phrase', on_change=utils.reset_pages)
choice = st.selectbox('What documents would you like to search in?', DIRS, format_func=lambda x: x.replace('_index', '').replace('_', ' ').replace('docs', '').title()+' documents')
to_see = st.number_input('How many results would you like to see per page?', value=10)
stemmer = st.toggle('Use stemming', help='If selected, the search will use stemming to find words with the same root. For example, "running" will match "run" and "ran".', on_change=utils.reset_pages)

if query_str != '':
    dl = utils.DataLoader(choice)
    searcher = utils.Searcher(query_str, dl, stemmer)
    searcher.search(to_see)