"""
Utility functions for HS codes and SIC codes
"""
import pandas as pd
import sys, logging

logging.basicConfig(filename="utils_logfile.log", level=logging.INFO)
# DEBUG, INFO, WARNING, ERROR, CRITICAL

def _make_8char_CN(trialstring):
	# Converts a Commodity Code to an 8-digit string
	# Insert leading zero for HS chapters 1 to 9:
	if len(str(trialstring))==7:
		outstr = '0'+str(trialstring)
	elif len(str(trialstring))==1:
		outstr = '0'+str(trialstring)
	# Insert trailing zeros for 2-digit HS chapters (anonymised)
	elif len(str(trialstring))==2:
		outstr = str(trialstring)+'000000'
	else:
		outstr = str(trialstring)
	return outstr


def _tidyup_df(df):
	# Converts all Commodity Codes in a dataframe to 8-digit strings
	outdf = df.loc[:,
		'Commodity Code'].map(lambda x: _make_8char_CN(x))
	outdf = pd.concat([outdf, df[
		['Supplementary Unit','Self-Explanatory text (English)']
		]], axis=1)
	return outdf


def _print_HS(df):
	print('\n'.join(
		[str(code)+'\t'+str(desc[:80]) for idx, code, unit, desc in 
		df.itertuples()]
		))


def get_CN_by_text(searchstring, verbose=False):
	"""
	Returns dataframe of index, CN (8-digit HS), measurement unit
	and description of commodities containing the searchstring in
	their description
	"""
	try:
		assert searchstring.isalnum()
	except:
		logging.error('invalid search string in get_CN_list()')
		return 0
	df = pd.read_csv('2017_CN.txt', sep='\t', 
		encoding='utf-16', warn_bad_lines=True)
	searchstring = str(searchstring).lower()
	if verbose: logging.info('Searching for {0}'.format(searchstring))
	foundstrings = df.loc[df.loc[:,'Self-Explanatory text (English)'
			].str.lower().str.contains(searchstring),:]
	outdf = _tidyup_df(foundstrings)  # return 8-digit string
	
	return outdf


def get_desc_by_HSchapter(chapternum, verbose=False):
	try:
		assert len(str(chapternum))<=2
	except:
		logging.error('invalid HS chapter supplied to get_desc_by_HSchapter()')
		return 0
	if len(str(chapternum))==1: chapternum = '0'+str(chapternum)
	df = pd.read_csv('2017_CN.txt', sep='\t', 
		encoding='utf-16', warn_bad_lines=True)
	foundstrings = df.loc[df.loc[:,'Commodity Code'].map(
		lambda x: _make_8char_CN(x)[:2]
		).str.match(chapternum),:]
	outdf = _tidyup_df(foundstrings)  # return 8-digit string

	return outdf


def get_desc_by_CN(CNcode, verbose=False):
	try:
		assert (len(str(CNcode))==8) | (len(str(CNcode))==7)
	except:
		logging.error('invalid CN code supplied to get_desc_by_CN()')
		return 0
	if len(str(CNcode))==7: CNcode = '0'+str(CNcode)
	df = pd.read_csv('2017_CN.txt', sep='\t', 
		encoding='utf-16', warn_bad_lines=True)
	foundstrings = df.loc[df.loc[:,'Commodity Code'].map(
		lambda x: _make_8char_CN(x)[:8]
		).str.match(CNcode),:]
	if foundstrings.empty:
		outdf = pd.DataFrame({
			'Code': [CNcode],
			'S': ['unk'],
			'Z-Desc': ['{0} not found'.format(CNcode)]
			})
		# print(outdf)
		# _print_HS(outdf)
	else:
		outdf = _tidyup_df(foundstrings)  # return 8-digit string

	return outdf




