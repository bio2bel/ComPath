# -*- coding: utf-8 -*-

"""This module contains all the constants used in ComPath repo"""

import os

from bio2bel.utils import get_connection, get_data_dir

MODULE_NAME = 'compath'
DATA_DIR = get_data_dir(MODULE_NAME)
DEFAULT_CACHE_CONNECTION = get_connection(MODULE_NAME)

"""Static files"""

dir_path = os.path.dirname(os.path.realpath(__file__))
STATIC_FOLDER = os.path.join(dir_path, 'static')

EXCEL_FOLDER = os.path.join(STATIC_FOLDER, 'resources', 'excel')

REACTOME_GENE_SET = os.path.join(EXCEL_FOLDER, 'kegg_gene_sets.csv')
KEGG_GENE_SET = os.path.join(EXCEL_FOLDER, 'reactome_gene_sets.csv')
WIKIPATHWAYS_GENE_SET = os.path.join(EXCEL_FOLDER, 'wikipathways_gene_sets.csv')
MSIG_GENE_SET = os.path.join(EXCEL_FOLDER, 'msig_gene_sets.csv')

# Managers with hierarchical information
HIERARCHY_MANAGERS = {'reactome'}

# Managers without pathway knowledge
BLACK_LIST = {
    'hgnc',
    'compath_hgnc',
}

MAPPING_TYPES = {
    'equivalentTo',
    'isPartOf'
}

EQUIVALENT_TO = 'equivalentTo'
IS_PART_OF = 'isPartOf'
