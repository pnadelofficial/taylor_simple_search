import streamlit as st
import os
import gdown
from string import punctuation
import re
from datetime import datetime

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

    os.makedirs('data', exist_ok=True)
    os.chdir('data')
    # nat archive
    nat_archive_data = 'https://drive.google.com/file/d/1q8tMHtW21iIqrZg2HJ3ndBqjrLRXYAz-/view?usp=sharing'
    gdown.download(nat_archive_data, output='nat_archive_files.csv', fuzzy=True)
    # ws
    written_statement_data = 'https://drive.google.com/file/d/13Xb80DGMUaRXPeh5b61CVcGTzFSEoeQl/view?usp=sharing'
    gdown.download(written_statement_data, output='all_written_statements.csv', fuzzy=True)
    # transcripts
    transcript_data = 'https://drive.google.com/file/d/1Wq3ahDgFomocUWgsUD7masWaX55BaCvD/view?usp=sharing'
    gdown.download(transcript_data, output='all_transcripts.csv', fuzzy=True)
    os.chdir('..')

def escape_markdown(text):
    '''Removes characters which have specific meanings in markdown'''
    MD_SPECIAL_CHARS = "\`*_{}#+"
    for char in MD_SPECIAL_CHARS:
        text = text.replace(char, '').replace('\t', '')
    return text

def no_punct(word):
    '''Util for below to remove punctuation'''
    return ''.join([letter for letter in word if letter not in punctuation.replace('-', '')])

def remove_tilde(word):
    return re.sub('~\d+', '', word)

def inject_highlights(text, searches):
    '''Highlights words from the search query''' 
    searches = [remove_tilde(s).replace('"', '') for s in searches if s != '']
    esc = punctuation + '."' + '..."'
    inject = f"""
        <p>
        {' '.join([f"<span style='background-color:#fdd835'>{word}</span>" if (no_punct(word.lower()) in searches) and (word not in esc) else word for word in text.split()])}
        </p>
        """ 
    return inject 

def add_context(data, r, amount=1):
    sents = []
    res_idx = int(data.loc[(data.passage==r['text'])].index[0])
    sents += list(data.iloc[res_idx-amount:res_idx].passage)
    sents += list(data.iloc[res_idx:res_idx+(amount+1)].passage)
    return '\n'.join(sents)

def display_results(i, r, data, searches, display_date=True):
    st.markdown(f"<small><b>Filename: {r['title']}</b></small>", unsafe_allow_html=True)
    if display_date: st.markdown(f"<small><b>Date: {datetime.strftime(r['date'], '%B %-d, %Y')}</b></small>", unsafe_allow_html=True)
    full = r['text']
    amount = st.number_input('Choose context length', key=f'num_{i}', value=1, step=1, help='This number represents the amount of sentences to be added before and after the result.')
    if st.button('Add context', key=f'con_{i}'):
        full = add_context(data, r, amount)
    if ('QUESTION:' in full) and ('ANSWER:' in full):
        full = re.sub('(?=ANSWER:)', '<br>', full, flags=re.DOTALL)
        full = re.sub('(?=.QUESTION:)', '<br>', full, flags=re.DOTALL)
    st.markdown(inject_highlights(escape_markdown(full.replace('\n --', ' --')), searches), unsafe_allow_html=True) 
    st.markdown("<hr style='width: 75%;margin: auto;'>", unsafe_allow_html=True)
    