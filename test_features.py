#!/usr/bin/env python
from src.ml.feature_preprocessor import FeaturePreprocessor

fp = FeaturePreprocessor()
features = {
    'phyloP_score': 0.1,
    'SIFT_score': 0.5,
    'PolyPhen_score': 0.1,
    'CADD_score': 5.0,
    'gnomAD_freq': 0.1,
    'REVEL_score': 0.2,
    'MutationTaster_score': 0.2,
    'FathmM_score': 0.5,
    'variant_type': 'SNP',
    'amino_acid_change': 'A1G'
}

try:
    vec = fp.preprocess(features)
    print(f'Feature vector length: {len(vec)}')
    print(f'Feature vector: {vec}')
except Exception as e:
    print(f'Error: {type(e).__name__}: {e}')
