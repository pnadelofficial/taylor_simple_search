from whoosh.index import open_dir
from whoosh import sorting
from whoosh.qparser import QueryParser, query
from whoosh.lang.morph_en import variations
import streamlit as st
import pandas as pd
import re
from string import punctuation
from datetime import datetime
import os
import gdown
from datetime import datetime
import base64
from fpdf import FPDF
import gspread
import subprocess

CREDS = st.secrets['gsp_secrets']['my_project_settings']

@st.cache_resource
def load_google_sheet():
    gc = gspread.service_account_from_dict(CREDS)
    return gc.open('simple-search-feedback').sheet1 # gmail account

@st.cache_data
def get_indices():
    # subprocess.run(['mv', 'cookies.txt', '~/.cache/gdown/cookies.txt'])

    os.makedirs('indices', exist_ok=True)
    os.chdir('indices')
    # nat archive
    nat_archive_url = 'https://drive.google.com/drive/folders/1Ew0mU1l7Y3M1CgD0RBZbfbp-tCwBFVga?usp=sharing'
    gdown.download_folder(nat_archive_url, use_cookies=False)
    # nat archive (by doc)
    nat_archive_by_doc_url = 'https://drive.google.com/drive/folders/1kKu7SHmTQC0W4ln0FUkjoJAEp7W-kegJ?usp=sharing'
    gdown.download_folder(nat_archive_by_doc_url, use_cookies=False)
    # ws
    statements_url = 'https://drive.google.com/drive/folders/1Gsi1UUGxDrIn5j-kzFaE7yI41jPzwnVS?usp=sharing'
    gdown.download_folder(statements_url, use_cookies=False)
    # transcripts
    transcripts_url = 'https://drive.google.com/drive/folders/1YR9KRs_ImSSQ4kT1QQR-zOAfmXyANrMl?usp=sharing'
    gdown.download_folder(transcripts_url,use_cookies=False)
    # transcripts (just answers)
    transcripts_answers_url = 'https://drive.google.com/drive/folders/1hOfshfxwtNct4l2drUw3RZKYLLOFQgUY?usp=sharing'
    gdown.download_folder(transcripts_answers_url, use_cookies=False)
    # policy docs
    policy_docs_url = 'https://drive.google.com/drive/folders/1_rNgLuOemfMEJblzw_bNyN0rLJGbvDjS?usp=sharing'
    gdown.download_folder(policy_docs_url, use_cookies=False)
    # sec sources
    sec_sources_url = 'https://drive.google.com/drive/folders/1aaoQFXC4xjKoVxrzf8JpOBr_2PGFX30M?usp=sharing'
    gdown.download_folder(sec_sources_url, use_cookies=False)
    # inquiry report
    inquiry_report_url = "https://drive.google.com/drive/folders/1RRQwRh2O35IVItboJDw3q1ahIyVX1jL0?usp=sharing"
    gdown.download_folder(inquiry_report_url, use_cookies=False)
    os.chdir('..')

    os.makedirs('data', exist_ok=True)
    os.chdir('data')
    # nat archive
    nat_archive_data = 'https://drive.google.com/file/d/1q8tMHtW21iIqrZg2HJ3ndBqjrLRXYAz-/view?usp=sharing'
    gdown.download(nat_archive_data, output='nat_archive_files.csv', fuzzy=True)
    # nat archive by doc
    nat_archive_by_doc_data = 'https://drive.google.com/file/d/1yxfyuAGHZum53Qup97Q1jRuKvScdH8SI/view?usp=sharing'
    gdown.download(nat_archive_by_doc_data, output='national_archives_104.csv', fuzzy=True)
    # ws
    written_statement_data = 'https://drive.google.com/file/d/1tDrAgQpI13JC6pwJw_geJZDBux0qwyhi/view?usp=sharing'
    gdown.download(written_statement_data, output='all_written_statements.csv', fuzzy=True)
    # transcripts
    transcript_data = 'https://drive.google.com/file/d/1eKjJocpwgGBv-uBhvfp7tMNl1CFFjdps/view?usp=sharing'
    gdown.download(transcript_data, output='all_transcripts.csv', fuzzy=True)
    # policy docs
    policy_data = 'https://drive.google.com/file/d/18WBgixNshITOUxCTPWNNjjGQy_jaPFS4/view?usp=sharing'
    gdown.download(policy_data, output='policy_docs.csv', fuzzy=True)
    # sec sources
    sec_sources_data = 'https://drive.google.com/file/d/1OYspzMKaSBxO3gU3-fgBy08IpD-NPUC6/view?usp=sharing'
    gdown.download(sec_sources_data, output='sec_sources.csv', fuzzy=True)
    # inquiry report
    inquiry_report_data = 'https://drive.google.com/file/d/1jqUK8TykLbZ_zyTgNIsjzGaSXYPVG0Hs/view?usp=sharing'
    gdown.download(inquiry_report_data, output='inquiry_report.csv', fuzzy=True)
    os.chdir('..')

DIRS = [d for d in os.listdir('./indices') if (d != 'transcript_answers_index') and (d != 'national_archive_bydoc') and (d != 'national_archive_index_104') and (d != '.DS_Store')]
DIRS = [d for d in DIRS if ('bydoc' not in d)]
print(DIRS)
def reset_pages():
    st.session_state['page_count'] = 0

class DataLoader:
    def __init__(self, choice) -> None:
        self.choice = choice
        self.choice_path = f'./indices/{self.choice}'
        
    def nat_archives(self):
        cats = sorting.FieldFacet("category")
        cat_choice = st.selectbox('What category of the National Archive data would you like to search in?', ['HIV', 'Haemophilia', 'Hep_C', 'Litigation and Compensation'], format_func=lambda x: x.replace('_', ' '))
        
        on = st.toggle("Search by PDF page", on_change=reset_pages)
        if on: 
            data = pd.read_csv('./data/nat_archive_files.csv').rename(columns={'Unnamed: 0':'doc_index', 'sentences':'passage'})
            ix = open_dir(self.choice_path)
        else:
            data = pd.read_csv('./data/national_archives_104.csv').rename(columns={'Unnamed: 0':'doc_index', 'sentences':'passage'})
            ix = open_dir(f'./indices/national_archive_index_104')
        self.all_docs = list(data.filename.unique())
        self.doc_search = st.multiselect('Search by document', ['Search all documents'] + self.all_docs, default=['Search all documents'], on_change=reset_pages)
        return data, ix, cats, cat_choice
    
    def written_statements(self):
        cats = None
        cat_choice = None
        ix = open_dir(self.choice_path)
        data = pd.read_csv('./data/all_written_statements.csv').rename(columns={'index':'doc_index', 'answers':'passage'})
        self.all_docs = list(data.filename.unique())
        self.doc_search = st.multiselect('Search by document', ['Search all documents'] + self.all_docs, default=['Search all documents'], on_change=reset_pages)
        return data, ix, cat_choice, cats
    
    def transcripts(self):
        cats = None
        cat_choice = None
        data = pd.read_csv('./data/all_transcripts.csv').rename(columns={'index':'doc_index', 'q_a':'passage'})
        
        on = st.toggle("Search on just the answers", on_change=reset_pages)
        if on: 
            ix = open_dir('./indices/transcript_answers_index')
        else:
            ix = open_dir(self.choice_path)
        self.all_docs = list(data.filename.unique())
        self.doc_search = st.multiselect('Search by document', ['Search all documents'] + self.all_docs, default=['Search all documents'], on_change=reset_pages)
        return data, ix, cat_choice, cats
    
    def policy_docs(self):
        cats = None
        cat_choice = None
        data = pd.read_csv('./data/policy_docs.csv').rename(columns={'sentences':'passage'})
        self.all_docs = list(data.filename.unique())
        self.doc_search = st.multiselect('Search by document', ['Search all documents'] + self.all_docs, default=['Search all documents'], on_change=reset_pages)
        return data, open_dir(self.choice_path), cat_choice, cats
        
    def secondary_sources(self):
        cats = None
        cat_choice = None
        data = pd.read_csv('./data/sec_sources.csv', lineterminator='\n').rename(columns={'chunks':'passage'})
        self.all_docs = list(data.files.unique())
        self.doc_search = st.multiselect('Search by document', ['Search all documents'] + self.all_docs, default=['Search all documents'], on_change=reset_pages)
        return data, open_dir(self.choice_path), cat_choice, cats
    
    def inquiry_report(self):
        cats = None
        cat_choice = None
        data = pd.read_csv('./data/inquiry_report.csv').rename(columns={'Unnamed: 0':'doc_index', 'filename':'files', 'sent':'passage'})
        self.all_docs = list(data.files.unique())
        self.doc_search = st.multiselect('Search by document', ['Search all documents'] + self.all_docs, default=['Search all documents'], on_change=reset_pages)
        return data, open_dir(self.choice_path), cat_choice, cats
    
    def generic(self, data_path):
        cats = None
        cat_choice = None
        data = pd.read_csv(data_path)
        self.all_docs = list(data.filename.unique())
        self.doc_search = st.multiselect('Search by document', ['Search all documents'] + self.all_docs, default=['Search all documents'], on_change=reset_pages)
        return data, open_dir(self.choice_path), cat_choice, cats

    def __call__(self):
        if self.choice == 'national_archive_index':
            return self.nat_archives()
        elif self.choice == 'written_statement_index':
            return self.written_statements()
        elif self.choice == 'transcript_index':
            return self.transcripts()
        elif self.choice == 'policy_docs_index':
            return self.policy_docs()
        elif self.choice == 'secondary_sources_index':
            return self.secondary_sources()
        elif self.choice == 'inquiry_report_index':
            return self.inquiry_report()
        else:
            return self.generic(self.choice)

class Page:
    def __init__(self, results, data, searches, doc_search, display_date=True) -> None:
        self.results = results
        self.data = data
        self.searches = searches
        self.doc_search = doc_search
        self.display_date = display_date

    def escape_markdown(self, text):
        '''Removes characters which have specific meanings in markdown'''
        MD_SPECIAL_CHARS = "\`*_{}#+"
        for char in MD_SPECIAL_CHARS:
            text = text.replace(char, '').replace('\t', '')
        return text
    
    def no_punct(self, word):
        '''Util for below to remove punctuation'''
        return ''.join([letter for letter in word if letter not in punctuation.replace('-', '') + '’' + '‘' + '“' + '”' + '—' + '…' + '–'])
    
    def no_digits(self, word):
        '''Util for below to remove digits'''
        return ''.join([letter for letter in word if not letter.isdigit()])

    def remove_tilde(self, word):
        return re.sub('~\d+', '', word)

    def inject_highlights(self, text, searches):
        '''Highlights words from the search query''' 
        searches = [self.remove_tilde(s).replace('"', '') for s in searches if s != '']
        esc = punctuation + '."' + '..."'
        inject = f"""
            <p>
            {' '.join([f"<span style='background-color:#fdd835'>{word}</span>" if (self.no_digits(self.no_punct(word.lower())) in searches) and (word not in esc) else word for word in text.split()])}
            </p>
            """ 
        return inject 

    def add_context(self, data, r, amount=1):
        sents = []
        res_idx = int(data.loc[data.passage.str.contains(r['text'].strip(), regex=False, na=False)].index[0])
        sents += list(data.iloc[res_idx-amount:res_idx].passage)
        sents += list(data.iloc[res_idx:res_idx+(amount+1)].passage)
        return '\n'.join(sents)

    def check_metadata(self, r, data, display_date):
        keys = list(r.keys())
        # title
        if 'title' in keys:
            st.markdown(f"<small><b>Document title: {r['title']}</b></small>", unsafe_allow_html=True)
        else:
            st.markdown(f"<small><b>Beginning of document: {data.loc[(data.filename.str.contains(r['filename'])) & (data.id == r['doc_index'])].iloc[0].passage[:150]}</b></small>", unsafe_allow_html=True, help='This document does not have an AI generated title, so displayed is the beginning of this document')
        
        # filename
        st.markdown(f"<small><b>Filename: {r['filename']}</b></small>", unsafe_allow_html=True)
        
        # date
        if display_date and ('date' in keys) and (re.match('\d', str(r['date']))): 
            st.markdown(f"<small><b>Date: {datetime.strftime(r['date'], '%B %-d, %Y')}</b></small>", unsafe_allow_html=True)
        elif display_date and ('date' in keys) and (not re.match('\d', str(r['date']))):
            st.markdown(f"<small><b>Date: No date found</b></small>", unsafe_allow_html=True)
        elif display_date and ('date_possible' in keys) and (re.match('\d', r['date_possible'])):
            st.markdown(f"<small><b>Date: {r['date_possible']}</b></small>", unsafe_allow_html=True)
        elif display_date and ('date_possible' in keys) and (not re.match('\d', r['date_possible'])):
            st.markdown(f"<small><b>Possible Date: No date found</b></small>", unsafe_allow_html=True)
        else:
            st.markdown(f"<small><b>Date: No date found</b></small>", unsafe_allow_html=True)

    def display_results(self, i, r, data, searches, display_date=True, text_return=True):
        self.check_metadata(r, data, display_date)
        full = r['text']
        amount = st.number_input('Choose context length', key=f'num_{i}', value=1, step=1, help='This number represents the amount of sentences to be added before and after the result.')
        if st.button('Add context', key=f'con_{i}'):
            full = self.add_context(data, r, amount)
            if (st.session_state['additional_context'][i] == '') or (len(st.session_state['additional_context'][i]) < len(full)):
                st.session_state['additional_context'][i] = full
        if ('QUESTION:' in full) and ('ANSWER:' in full):
            full = re.sub('(?=ANSWER:)', '<br>', full, flags=re.DOTALL)
            full = re.sub('(?=.QUESTION:)', '<br>', full, flags=re.DOTALL)
        st.markdown(self.inject_highlights(self.escape_markdown(full.replace('\n --', ' --')), searches), unsafe_allow_html=True) 
        st.markdown("<hr style='width: 75%;margin: auto;'>", unsafe_allow_html=True)
        if text_return:
            return full, r 

    def __call__(self):
        for i, r in enumerate(self.results):
            if r['filename'] in self.doc_search:
                self.display_results(i, r, self.data, self.searches, display_date=self.display_date)

class Searcher:
    def __init__(self, query_str, dataloader, stemmer) -> None:
        self.query_str = query_str
        self.dataloader = dataloader
        self.choice = self.dataloader.choice
        self.data, self.ix, self.cats, self.cat_choice = self.dataloader()
        self.stemmer = stemmer

        self.nat_toggle = '104' in self.ix.__str__()
    
    def parse_query(self):
        if self.stemmer: 
            parser = QueryParser("text", self.ix.schema, termclass=query.Variations)
        else:
            parser = QueryParser("text", self.ix.schema)    
        q = parser.parse(self.query_str)
        all_tokens = list(set(self.query_str.split(' ') + [item for sublist in [variations(t) for t in self.query_str.split(' ')] for item in sublist]))
        searches = [q.lower() for q in all_tokens if (q != 'AND') and (q != 'OR') and (q != 'NOT') and (q != 'TO')]
        return q, searches
    
    def limit_results(self, results, doc_search):
        if doc_search != ['Search all documents']:
            results = [r for r in results if r['filename'] in doc_search]
        return results

    def search(self, to_see):
        q, searches = self.parse_query()
        with self.ix.searcher() as searcher:
            results = searcher.search(q, groupedby=self.cats, limit=None)
            if self.choice == 'national_archive_index':
                groups = results.groups()
                if (self.cat_choice == 'Hep_C') and (not self.nat_toggle): 
                    self.cat_choice = 'Hep C'
                if self.cat_choice in groups:
                    hits = list(set(groups[self.cat_choice]))
                    results = [searcher.stored_fields(res) for res in hits]
                    self.results = results
                    default = 1
                else:
                    st.write(f"No results for this query in the {self.cat_choice} documents.")  
                    self.results = []
                    default = 0
            else:
                self.results = results
                default = 1
            
            doc_list = self.dataloader.all_docs if self.dataloader.doc_search == ['Search all documents'] else self.dataloader.doc_search
            self.limited_results = self.limit_results(self.results, doc_list)
            st.session_state['pages'] = [self.limited_results[i:i + to_see] for i in range(0, len(self.limited_results), to_see)]

            with st.sidebar:
                st.markdown("# Page Navigation")
                if st.button('See next page', key='next'):
                    st.session_state['page_count'] += 1
                if st.button('See previous page', key='prev'):
                    st.session_state['page_count'] -= 1   
                if (len(doc_list) > 0) and (len(st.session_state['pages']) > 0):
                    page_swap = st.number_input('What page do you want to visit?', min_value=default, max_value=len(st.session_state['pages']), value=default)
                if st.button('Go to page'):
                    st.session_state['page_count'] = page_swap-1
                st.divider()
                st.markdown("# Export to PDF")
                if st.button('Export this page to PDF'):
                    e = Exporter(self.query_str)
                    e(self)
                if st.button('Export all results to PDF'):
                    e = Exporter(self.query_str, full=True)
                    e(self)
                st.divider()
                st.markdown("# Feedback")
                feedback = st.text_area('Give any feedback you may have here')
                fb = load_google_sheet()
                if st.button('Send feedback'):
                    fb.append_row([datetime.now().strftime("%m/%d/%Y"), feedback])
                
            st.write(f"There are **{len(self.limited_results)}** results for this query.")
            st.divider()

            if (default == 0) or (len(self.limited_results) == 0):
                pass
            else:
                if len(doc_list) > 0:
                    p = Page(st.session_state['pages'][st.session_state['page_count']], self.data, searches, doc_list)
                    p()

                    st.write(f"Page: {st.session_state['page_count']+1} out of {len(st.session_state['pages'])}")

class Exporter:
    def __init__(self, query_str, full=False):
        self.query_str = query_str
        self.full = full

    def pdf_set_up(self):
        self.status = st.empty()
        self.status.info('Generating PDF, please wait...')

        pdf = FPDF()
        pdf.add_page()
        pdf.add_font('DejaVu', '', './fonts/DejaVuSansCondensed.ttf', uni=True)
        pdf.add_font('DejaVu', 'B', './fonts/DejaVuSansCondensed-Bold.ttf', uni=True)
        pdf.set_font('DejaVu', 'B', 12)
        
        self.row_height = pdf.font_size
        pdf.multi_cell(0, self.row_height*3, f"Search Query: {self.query_str}", 1)
        pdf.ln(self.row_height*3)

        self.pdf = pdf

        self.col_width = pdf.w / 1.11
        self.spacing = 1.5

    def fill_pdf(self, searcher_object):
        if self.full:
            with searcher_object.ix.searcher() as searcher:
                searcher_object.limited_results = searcher_object.limit_results(searcher_object.results, searcher_object.dataloader.all_docs)
                for r in searcher_object.limited_results:
                    text = r['text'].replace("<br>", '')
                    self.pdf.set_font('DejaVu', 'B', 12)
                    title = r['title'] if 'title' in r.keys() else r['filename']
                    self.pdf.multi_cell(self.col_width, self.row_height*self.spacing, f"Title: {title}", 0, ln=2)
                    if (searcher_object.choice != 'national_archive_index') and ('date' in r.keys()): 
                        self.pdf.multi_cell(self.col_width, self.row_height*self.spacing, f"Date: {datetime.strftime(r['date'], '%B %-d, %Y')}", 0, ln=2)
                    self.pdf.set_font('DejaVu', '', 14)
                    self.pdf.multi_cell(self.col_width, self.row_height*self.spacing, text, 'B', ln=2)
                    self.pdf.ln(self.row_height * self.spacing)
        else:
            page = st.session_state['pages'][st.session_state['page_count']]
            additional_context_dict = {}
            for i in range(len(page)):
                if (page[i]['text'] != st.session_state['additional_context'][i]) and (not st.session_state['additional_context'][i] == ''):
                    additional_context_dict[i] = {'text':st.session_state['additional_context'][i]} | {k:page[i][k] for k in page[i].keys() if k != 'text'}
                else:
                    additional_context_dict[i] = {k:page[i][k] for k in page[i].keys()}           
            for r in additional_context_dict.values():
                text = r['text'].replace("<br>", '')
                self.pdf.set_font('DejaVu', 'B', 12)
                title = r['title'] if 'title' in r.keys() else r['filename']
                self.pdf.multi_cell(self.col_width, self.row_height*self.spacing, f"Title: {title}", 0, ln=2)
                if (searcher_object.choice != 'national_archive_index') and ('date' in r.keys()): 
                    self.pdf.multi_cell(self.col_width, self.row_height*self.spacing, f"Date: {datetime.strftime(r['date'], '%B %-d, %Y')}", 0, ln=2)
                self.pdf.set_font('DejaVu', '', 14)
                self.pdf.multi_cell(self.col_width, self.row_height*self.spacing, text, 'B', ln=2)
                self.pdf.ln(self.row_height * self.spacing)
                
    def create_download_link(self, val, filename):
        b64 = base64.b64encode(val)
        return f'<a href="data:application/octet-stream;base64,{b64.decode()}" download="{filename}.pdf">Download file</a>'

    def pdf_finish(self):
        n = datetime.now()
        query_str_for_file = self.query_str.replace(' ', '_').replace('"','').replace("'",'')
        html = self.create_download_link(self.pdf.output(dest="S"), f"search_results_{query_str_for_file}_{datetime.strftime(n, '%m_%d_%y')}")
        self.status.success('PDF Finished! Download with the link below.')
        st.markdown(html, unsafe_allow_html=True)
    
    def __call__(self, searcher_object):
        self.pdf_set_up()
        self.fill_pdf(searcher_object)
        self.pdf_finish()