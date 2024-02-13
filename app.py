import streamlit as st
import pandas as pd
from whoosh.index import open_dir
import os
from whoosh.qparser import QueryParser, query
from whoosh import sorting
import utils
from whoosh.lang.morph_en import variations
import re

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

dirs = [d for d in os.listdir('./indices') if (d != 'transcript_answers_index') and (d != 'national_archive_bydoc') and (d != 'national_archive_index_104')]
choice = st.selectbox('What documents would you like to search in?', dirs, format_func=lambda x: x.replace('_index', '').replace('_', ' ').replace('docs', '').title()+' documents')
ix = open_dir(f'./indices/{choice}')

if choice == 'national_archive_index':
    ix = open_dir(f'./indices/national_archive_index_104')
    cats = sorting.FieldFacet("category")
    cat_choice = st.selectbox('What category of the National Archive data would you like to search in?', ['HIV', 'Haemophilia', 'Hep_C', 'Litigation and Compensation'], format_func=lambda x: x.replace('_', ' '))
    data = pd.read_csv('./data/national_archives_104.csv').rename(columns={'Unnamed: 0':'doc_index', 'sentences':'passage'})
    on = st.toggle("Search by PDF page")
    if on: 
        data = pd.read_csv('./data/nat_archive_files.csv').rename(columns={'Unnamed: 0':'doc_index', 'sentences':'passage'})
        ix = open_dir(f'./indices/{choice}')
    doc_search = ['Search all documents']
elif choice == 'written_statement_index':
    cats = None
    cat_choice = None
    data = pd.read_csv('./data/all_written_statements.csv').rename(columns={'index':'doc_index', 'answers':'passage'})
    doc_search = ['Search all documents']
elif choice == 'transcript_index':
    cats = None
    cat_choice = None
    data = pd.read_csv('./data/all_transcripts.csv').rename(columns={'index':'doc_index', 'q_a':'passage'})
    on = st.toggle("Search on just the answers")
    if on: ix = open_dir('./indices/transcript_answers_index')
    doc_search = ['Search all documents']
elif choice == 'policy_docs_index':
    cats = None
    cat_choice = None
    data = pd.read_csv('./data/policy_docs.csv').rename(columns={'sentences':'passage'})
    # doc_search = st.selectbox('Search by document', ['Search all documents'] + list(data.filename.unique()))
    doc_search = st.multiselect('Search by document', ['Search all documents'] + list(data.filename.unique()))
elif choice == 'secondary_sources_index':
    cats = None
    cat_choice = None
    data = pd.read_csv('./data/sec_sources.csv', lineterminator='\n').rename(columns={'chunks':'passage'})
    # doc_search = st.selectbox('Search by document', ['Search all documents'] + list(data.files.unique()))
    doc_search = st.multiselect('Search by document', ['Search all documents'] + list(data.files.unique()))

to_see = st.number_input('How many results would you like to see per page?', value=10)
stemmer = st.toggle('Use stemming')

with st.sidebar:
    # css-13ejsyy ef3psqc11
    if st.button('See next page', key='next'):
        st.session_state.start = st.session_state.start + to_see
        st.session_state.page_count += 1

    if st.button('See previous page', key='prev'):
        st.session_state.start = st.session_state.start - to_see
        st.session_state.page_count -= 1

# text_for_save = []
if "text_for_page_export" not in st.session_state:
    st.session_state["text_for_page_export"] = {}

if query_str != '':
    if stemmer: 
        parser = QueryParser("text", ix.schema, termclass=query.Variations)
    else:
        parser = QueryParser("text", ix.schema)
    q = parser.parse(query_str)
    split_query = re.split("~|\s", query_str)
    all_tokens = list(set(query_str.split(' ') + [item for sublist in [variations(t) for t in query_str.split(' ')] for item in sublist]))
    searches = [q.lower() for q in all_tokens if (q != 'AND') and (q != 'OR') and (q != 'NOT') and (q != 'TO')]

    with ix.searcher() as searcher:
        results = searcher.search(q, groupedby=cats, limit=None)
        if choice == 'national_archive_index':
            groups = results.groups()
            if (cat_choice == 'Hep_C') and (not on): 
                cat_choice = 'Hep C'
            if cat_choice in groups:
                hits = list(set(groups[cat_choice]))
                st.write(f"There are **{len(hits)}** results for this query.") 
                for i, res in enumerate(hits[st.session_state.start:st.session_state.start+st.session_state.to_see]):
                    r = searcher.stored_fields(res)
                    if on:
                        full = utils.display_results(i, r, data, searches, display_date=False)
                    else:
                        full = utils.display_results(i, r, data, searches, display_date=True)
                    # text_for_save.append(full)
                    st.session_state["text_for_page_export"][i] = full
                num_pages = (len(hits)//to_see)+1 if len(hits) > to_see else len(hits)//to_see
                st.write(f'Page: {st.session_state.page_count} of {num_pages}')
            else:
                st.write(f"No results for this query in the {cat_choice} documents.")  
        else:
            if ((choice == 'policy_docs_index') or (choice == 'secondary_sources_index')) and (doc_search != ['Search all documents']):
                results = searcher.search(q, groupedby=cats, limit=None, filter=QueryParser('filename', ix.schema).parse(f'filename:{doc_search}'))
            st.write(f"There are **{len(results)}** results for this query.") 
            for i, r in enumerate(results[st.session_state.start:st.session_state.start+st.session_state.to_see]):
                full = utils.display_results(i, r, data, searches)
                # text_for_save.append(full)
                st.session_state["text_for_page_export"][i] = full
            num_pages = (len(results)//to_see)+1 #if len(results) > to_see else len(results)//to_see
            st.write(f'Page: {st.session_state.page_count} of {num_pages}')

export_as_pdf_page = st.button("Export page as PDF")
export_as_pdf_full = st.button("Export full search as PDF")

if export_as_pdf_page:
    utils.export_as_pdf_page(list(st.session_state["text_for_page_export"].values()), query_str, choice)

if export_as_pdf_full:
    utils.export_as_pdf_full(results, query_str, choice, ix, cats, q)