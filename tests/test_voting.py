# -*- coding: utf-8 -*-
""" This module contains tests for the data model of ComPath"""

from compath.models import User
from tests.constants import DatabaseMixin, REACTOME, KEGG


class TestVotingSystem(DatabaseMixin):
    """Test Voting"""

    def test_vote_up(self):
        """Test if votes are adding"""
        current_user = User()

        mapping_1 = self.manager.get_or_create_mapping(
            KEGG,
            '1',
            'kegg pathway',
            REACTOME,
            '2',
            'reactome pathway',
            current_user
        )

        vote = self.manager.get_or_create_vote(user=current_user, mapping=mapping_1)

        self.assertEqual(1, self.manager.count_votes(), msg='Vote was not created')
        self.assertEqual(True, vote.type, msg='Vote type is wrong')

    def test_vote_down(self):
        """Test if votes are adding"""
        current_user = User()

        mapping_1 = self.manager.get_or_create_mapping(
            KEGG,
            '1',
            'kegg pathway',
            REACTOME,
            '2',
            'reactome pathway',
            current_user
        )

        vote = self.manager.get_or_create_vote(user=current_user, mapping=mapping_1, vote_type=False)

        self.assertEqual(1, self.manager.count_votes(), msg='Vote was not created')
        self.assertEqual(False, vote.type, msg='Vote type is wrong')

    def test_double_voting(self):
        """Test voting"""

        current_user_1 = User()
        current_user_2 = User()

        mapping_1 = self.manager.get_or_create_mapping(
            KEGG,
            '1',
            'kegg pathway',
            REACTOME,
            '2',
            'reactome pathway',
            current_user_1
        )

        mapping_2 = self.manager.get_or_create_mapping(
            KEGG,
            '1',
            'kegg pathway',
            REACTOME,
            '2',
            'reactome pathway',
            current_user_2
        )

        vote_1 = self.manager.get_or_create_vote(user=current_user_1, mapping=mapping_1, vote_type=False)
        vote_2 = self.manager.get_or_create_vote(user=current_user_2, mapping=mapping_2)

        self.assertEqual(2, self.manager.count_votes(), msg='Problem with votes')
        self.assertEqual(False, vote_1.type, msg='First vote type is wrong')
        self.assertEqual(True, vote_2.type, msg='Second vote type is wrong')
