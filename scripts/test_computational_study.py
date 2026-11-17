#!/usr/bin/env python3
"""Executable validation tests restricted to the reported computational experiment."""
import copy
import csv
import json
import unittest
from decimal import Decimal
from methodology import ROOT, loss, cash_flow, validate_record, make_case, family_numbers
from results_audit import mutate,CATEGORIES

class FinancialModelTests(unittest.TestCase):
    def test_one_period_expected_loss(self):
        self.assertEqual(loss(['140'],['0.02'],['0.40'],['0'],['1']),Decimal('1.1200'))
    def test_two_period_expected_loss(self):
        self.assertEqual(loss(['100','100'],['0.02','0.02'],['0.4','0.4'],['0','0'],['1','1']),Decimal('1.584000'))
    def test_refinancing_finishes_exposure(self):
        self.assertEqual(Decimal(family_numbers('refinancing','favorable')[1]), Decimal('0.8'))
    def test_support_eligible_before_payment(self):
        self.assertEqual(cash_flow('85','5','100',[dict(id='S1',amount='20',arrival=-5,eligible=True)])['headroom'],'10')
    def test_support_after_payment(self):
        self.assertEqual(cash_flow('85','5','100',[dict(id='S1',amount='20',arrival=5,eligible=True)])['shortfall'],'10')
    def test_invalid_probability(self):
        with self.assertRaises(ValueError):loss(['100'],['1.5'],['0.4'],['0'],['1'])
    def test_duplicate_support_prohibited(self):
        xs=[dict(id='S1',amount='1',arrival=-1,eligible=True)]*2
        with self.assertRaises(ValueError):cash_flow('0','0','1',xs)

class CaseCorpusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with (ROOT/'data/case_design_grid.csv').open() as f:
            cls.rows=list(csv.DictReader(f))
        cls.controls={}
        cls.defects={}
        for row in cls.rows:
            for defective in (False,True):
                r,_=make_case(row,defective)
                stored=json.loads((ROOT/'cases'/(r['case_id']+'.json')).read_text())
                assert r==stored
                (cls.defects if defective else cls.controls)[r['case_id']]=r
    def test_factorial_design(self):
        self.assertEqual(len(self.rows),54)
        self.assertEqual(len(self.controls),54)
        self.assertEqual(len(self.defects),54)
    def test_controls_are_structurally_valid(self):
        self.assertTrue(all(not validate_record(x) for x in self.controls.values()))
    def test_semantic_defects_are_structurally_valid(self):
        self.assertTrue(all(not validate_record(x) for x in self.defects.values()))
    def test_every_fault_triggers_targeted_diagnostic(self):
        for record in self.controls.values():
            for cat in CATEGORIES:
                diagnostics=validate_record(mutate(record,cat))
                self.assertEqual({d.split(':')[0] for d in diagnostics},{cat})
    def test_all_nine_financial_branches(self):
        oracle={('exposure_amount','favorable'):('0.8','0.48'),
                ('exposure_amount','adverse'):('0.8','1.12'),
                ('exposure_amount','unchanged'):('0.8','0.8'),
                ('refinancing','favorable'):('1.584','0.8'),
                ('refinancing','adverse'):('1.584','2.35232'),
                ('refinancing','unchanged'):('1.584','1.584'),
                ('sponsor_support','favorable'):('0','10'),
                ('sponsor_support','adverse'):('0','-10'),
                ('sponsor_support','unchanged'):('0','0')}
        for key,expected in oracle.items():
            actual=family_numbers(*key)
            self.assertEqual(tuple(map(Decimal,actual[:2])),tuple(map(Decimal,expected)))

if __name__=='__main__':unittest.main(verbosity=2)
