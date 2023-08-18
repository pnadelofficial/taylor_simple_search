import streamlit as st
import pandas as pd
from whoosh.index import open_dir
import os
from whoosh.qparser import QueryParser
from whoosh import sorting
import utils

st.title('Simple Search')

if 'page_count' not in st.session_state:
    st.session_state['page_count'] = 1

if 'to_see' not in st.session_state:
    st.session_state['to_see'] = 10

if 'start' not in st.session_state:
    st.session_state['start'] = 0

utils.get_indices()

query_str = st.text_input('Search for a word or phrase')
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

dirs = os.listdir('./indices')
choice = st.selectbox('What documents would you like to search in?', dirs, format_func=lambda x: x.replace('_index', '').replace('_', ' ').title()+' documents')
ix = open_dir(f'./indices/{choice}')

if choice == 'national_archive_index':
    cats = sorting.FieldFacet("category")
    cat_choice = st.selectbox('What category of the National Archive data would you like to search in?', ['HIV', 'Haemophilia', 'Hep_C', 'Litigation and Compensation'], format_func=lambda x: x.replace('_', ' '))
    data = pd.read_csv('./data/nat_archive_files.csv').rename(columns={'Unnamed: 0':'doc_index', 'sentences':'passage'})
elif choice == 'written_statement_index':
    cats = None
    cat_choice = None
    data = pd.read_csv('./data/all_written_statements.csv').rename(columns={'index':'doc_index', 'answers':'passage'})
elif choice == 'transcript_index':
    cats = None
    cat_choice = None
    data = pd.read_csv('./data/all_transcripts.csv').rename(columns={'index':'doc_index', 'q_a':'passage'})

to_see = st.number_input('How many results would you like to see per page?', value=10)

with st.sidebar:
    # css-13ejsyy ef3psqc11
    if st.button('See next page', key='next'):
        st.session_state.start = st.session_state.start + to_see
        st.session_state.page_count += 1

    if st.button('See previous page', key='prev'):
        st.session_state.start = st.session_state.start - to_see
        st.session_state.page_count -= 1

if query_str != '':
    parser = QueryParser("text", ix.schema)
    query = parser.parse(query_str)
    searches = [q.lower() for q in query_str.split(' ') if (q != 'AND') and (q != 'OR') and (q != 'NOT') and (q != 'TO')]

    with ix.searcher() as searcher:
        results = searcher.search(query, groupedby=cats)
        if choice == 'national_archive_index':
            groups = results.groups()
            if cat_choice in groups:
                hits = list(set(groups[cat_choice]))
                print(st.session_state.start, st.session_state.start+st.session_state.to_see)
                for i, res in enumerate(hits[st.session_state.start:st.session_state.start+st.session_state.to_see]):
                    r = searcher.stored_fields(res)
                    utils.display_results(i, r, data, searches)
                st.write(f'Page: {st.session_state.page_count} of {(len(hits)//to_see)+1}')
            else:
                st.write(f"No results for this query in the {cat_choice} documents.")  
        else:
            for i, r in enumerate(results[st.session_state.start:st.session_state.start+st.session_state.to_see]):
                utils.display_results(i, r, data, searches)
            st.write(f'Page: {st.session_state.page_count} of {len(results)//to_see}')
