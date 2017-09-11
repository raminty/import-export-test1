"""
Return exporters with overlapping most frequent commodity codes
"""
import csv, utils
import networkx as nx
import numpy as np
import pandas as pd
from sklearn import linear_model
from sklearn.externals import joblib
from flask import Flask #,request
from flask_restplus import Resource, Api #, reqparse

app = Flask(__name__)
api = Api(app)

def get_top_nodes(Gph, company):
    """
    Generate top-most commodities: returns sorted list of (u, v, d)
    """
    all_edges = Gph.edges_iter(nbunch=company, data='monthcount')
    sorted_edges = sorted(all_edges, key=lambda tup: -int(tup[2]))
    # for edge in sorted_edges:
    #     print(edge)
    return sorted_edges


def load_data(sourcedata):
    """Reads in from tab separated file"""
    Gph = nx.Graph()
    with open(sourcedata, 'r') as tsvfile:
        tsvin = csv.reader(tsvfile, delimiter='\t')
        # [' CompanyNumber', 'RegAddress.PostCode', 'Postcode', 'HScode',
        # 'co_name', 'Name', 'SICCode.SicText_1', 'MonthCount']
        for i, row in enumerate(tsvin):
            Gph.add_node(row[4], type='Name')
            Gph.add_node(row[3], type='Commodity')
            Gph.add_edge(row[4], row[3], monthcount=row[7])
    return Gph
    

def find_common_codes(Gph, common_HS):
    """
    Generator of companies and commodities that export a common set of commodities
    """
    u, v = common_HS
    # print(u, v)
    name_gen = nx.common_neighbors(Gph, u, v)
    # name_gen = (w for w in Gph[u] if w in Gph[v] and w not in (u, v))
    # only company names are neighbours of commodity codes
    selected_nodes = []
    for name in name_gen:
        yield name
        cmdty_gen = nx.all_neighbors(Gph, name)
        # only commodity nodes are neighbours of company (name) nodes
        for cmdty_node in cmdty_gen:
            yield cmdty_node


def HS_to_predicted_SIC(HScode):
    """Return SIC code (with verbal description) against an HS code"""
    clf = joblib.load('model_1_trained_classifier_100000_1.pkl')
    prediction = clf.predict(HScode)
    return prediction


@api.route('/<str:args>')
def main(*args):
    """Runs the main program"""
    rg = []
    for i, r in enumerate(*args):
        rg.append(r)
    print('Loading main graph ...')
    sourcedata='Export_combined_summary.csv'
    Gph = load_data(sourcedata)

    if len(rg)==4:  # given two commodity codes
        common_HS = [rg[2], rg[3]]
    elif len(rg)==3:  # given a company name
        tops = [t for t in get_top_nodes(Gph, rg[2])]
        if len(tops) > 1:
            top1, top2 = tops[:2]
        else:
            """
            1. Look up SIC code from company name
            2. Lookup top two HS codes for SIC code, from table to be created
            """
            print('SIC-based search not implemented')
            raise NotImplementedError
        common_HS = [top1[1], top2[1]]
    else:
        print('No valid search paramters given. Proceeding with default.')
        common_HS=['94033019','94034090']
    
    print('Identified', common_HS[0], common_HS[1])
    c1 = utils.get_desc_by_CN(common_HS[0])
    c2 = utils.get_desc_by_CN(common_HS[1])
    print('Preparing subgraph for\n{0} - {1}\nand\n{2} - {3}'.format(
        common_HS[0], c1['Self-Explanatory text (English)'].values[0],
        common_HS[1], c2['Self-Explanatory text (English)'].values[0]
    ))
    nodes1 = Gph.subgraph(find_common_codes(Gph, common_HS))
    nx.write_gexf(nodes1,'common_subgraph.gexf')
    # Generate text response
    names = [n for n in nx.common_neighbors(Gph, common_HS[0], common_HS[1])]
    s = ' '.join([
        'You have {0} companies in your neighbourhood'
    ])
    print(s.format(len(names)-1))
    i = 0
    for name in names:
        cmdties = [c for c in get_top_nodes(Gph, name)]
        is_interesting = True
        if len(names) > 20:
            # print((common_HS[0] in cmdties[1]), (common_HS[1] in cmdties[1]))
            if (common_HS[0] in cmdties[1]) or (common_HS[1] in cmdties[1]):
                is_interesting = True
            else:
                is_interesting = False
        if (len(cmdties) > 2) and is_interesting and i < 20:
            i += 1
            s = ' '.join([
                '{0} has exported {1} different commodities'
            ])
            # print(s.format(name, len(cmdties)))
    return {'competitors': dict(
        [[c for c in get_top_nodes(Gph, name)] for name in names]
        )}


if __name__ == '__main__':
    app.run(debug=True)
    # import sys
    # main(sys.argv)

# 84118280 84119900
# 94033019 94034090
# 82121090 84191100

