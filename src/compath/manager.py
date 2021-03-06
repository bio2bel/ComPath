# -*- coding: utf-8 -*-

"""This module the database manager of ComPath."""

import datetime
import logging
from typing import List, Optional

from sqlalchemy import and_, create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from bio2bel.utils import get_connection
from . import managers
from .constants import EQUIVALENT_TO, IS_PART_OF, MAPPING_TYPES, MODULE_NAME
from .models import Base, PathwayMapping, User, Vote, mappings_users

__all__ = [
    'Manager'
]

log = logging.getLogger(__name__)


def _flip_service_order(service_1_name: str, service_2_name: str) -> bool:
    """Decide whether the service order should be flipped (true if they should be).

    :param service_1_name:
    :param service_2_name:
    """
    if service_1_name == service_2_name:
        return False

    return service_1_name > service_2_name


def _ensure_manager(name):
    if name not in managers:
        raise ValueError('Manager does not exist for {}. Available: {}'.format(name, managers))


class Manager(object):
    """Database manager."""

    def __init__(self, engine, session):
        """Init ComPath manager."""
        self.engine = engine
        self.session = session
        self.create_all()

    @staticmethod
    def from_connection(connection=None):
        """Initialize manager from connection string"""
        connection = get_connection(MODULE_NAME, connection)
        engine = create_engine(connection)
        session_maker = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
        session = scoped_session(session_maker)
        return Manager(engine, session)

    def create_all(self, check_first: bool = True):
        """Create tables for ComPath."""
        Base.metadata.create_all(self.engine, checkfirst=check_first)

    def drop_all(self, check_first: bool = True):
        """Drop all tables for ComPath."""
        Base.metadata.drop_all(self.engine, checkfirst=check_first)

    """Query methods"""

    def count_votes(self) -> int:
        """Count the votes in the database."""
        return self.session.query(Vote).count()

    def count_mappings(self) -> int:
        """Count the mappings in the database."""
        return self.session.query(PathwayMapping).count()

    def count_users(self) -> int:
        """Count the Users in the database."""
        return self.session.query(User).count()

    def count_mapping_user(self) -> int:
        """Count the UsersMappings table in the database.

        :rtype: int
        """
        return self.session.query(mappings_users).count()

    def get_all_mappings(self) -> List[PathwayMapping]:
        """Get all mappings in the database."""
        return self.session.query(PathwayMapping).all()

    def get_all_accepted_mappings(self) -> List[PathwayMapping]:
        """Get all accepted mappings in the database."""
        return self.session.query(PathwayMapping).filter(PathwayMapping.accepted == True).all()

    def get_mappings_by_type(self, mapping_type: str) -> List[PathwayMapping]:
        """Get all mappings in the database.

        :param mapping_type: type of the mapping
        """
        if mapping_type not in MAPPING_TYPES:
            raise ValueError('{} is not valid mapping mapping_type'.format(mapping_type))

        return self.session.query(PathwayMapping).filter(PathwayMapping.type == mapping_type).all()

    def get_vote_by_id(self, vote_id: str) -> Optional[Vote]:
        """Get a vote by its id.

        :param vote_id: identifier
        """
        return self.session.query(Vote).filter(Vote.id == vote_id).one_or_none()

    def get_vote(self, user: User, mapping: PathwayMapping) -> Optional[Vote]:
        """Get a vote.

        :param user: User instance
        :param mapping: Mapping instance
        """
        return self.session.query(Vote).filter(and_(Vote.user == user, Vote.mapping == mapping)).one_or_none()

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get a user by their email address."""
        return self.session.query(User).filter(User.email == email).one_or_none()

    def get_mapping(self, service_1_name, pathway_1_id, pathway_1_name, service_2_name, pathway_2_id, pathway_2_name,
                    mapping_type):
        """Query mapping in the database.

        :param str service_1_name: manager name of the service 1
        :param str pathway_1_id: pathway 1 id
        :param str pathway_1_name: pathway 1 name
        :param str service_2_name: manager name of the service 1
        :param str pathway_2_id: pathway 2 id
        :param str pathway_2_name: pathway 2 name
        :param str mapping_type: mapping type (isPartOf or equivalentTo)
        :rtype: Optional[Mapping]
        """
        mapping_filter = and_(
            PathwayMapping.service_1_name == service_1_name,
            PathwayMapping.service_1_pathway_id == pathway_1_id,
            PathwayMapping.service_1_pathway_name == pathway_1_name,
            PathwayMapping.service_2_name == service_2_name,
            PathwayMapping.service_2_pathway_id == pathway_2_id,
            PathwayMapping.service_2_pathway_name == pathway_2_name,
            PathwayMapping.type == mapping_type,
        )

        return self.session.query(PathwayMapping).filter(mapping_filter).one_or_none()

    def get_mapping_by_id(self, mapping_id: int) -> Optional[PathwayMapping]:
        """Get a mapping by its id.

        :param mapping_id: mapping id
        """
        return self.session.query(PathwayMapping).filter(PathwayMapping.id == mapping_id).one_or_none()

    def get_or_create_vote(self, user, mapping, vote_type=True):
        """Get or create vote.

        :param User user: User instance
        :param PathwayMapping mapping: Mapping instance
        :param Optional[Vote.type] vote_type: vote type
        :rtype: Vote
        """
        vote = self.get_vote(user, mapping)

        if vote is None:
            vote = Vote(
                user=user,
                mapping=mapping,
                type=vote_type
            )

            self.session.add(vote)
            self.session.commit()

        # If there was already a vote, and it's being changed
        elif vote_type is not None:
            vote.type = vote_type
            vote.changed = datetime.datetime.utcnow()
            self.session.commit()

        return vote

    def get_or_create_mapping(self, service_1_name, pathway_1_id, pathway_1_name, service_2_name, pathway_2_id,
                              pathway_2_name, mapping_type, user):
        """Get or create a mapping.

        :param str service_1_name: manager name of the service 1
        :param str pathway_1_name: pathway 1 name
        :param str pathway_1_id: pathway 1 id
        :param str service_2_name: manager name of the service 1
        :param str pathway_2_name: pathway 2 name
        :param str pathway_2_id: pathway 2 id
        :param str mapping_type: type of mapping
        :param User user: the user
        :return: PathwayMapping and boolean indicating if the mapping was created or not
        :rtype: tuple[PathwayMapping,bool]
        """
        # Ensure maintaining the order of pathways if they belong to the same database
        flip_order = (
            mapping_type == EQUIVALENT_TO and
            service_1_name == service_2_name and
            _flip_service_order(pathway_1_name, pathway_2_name)
        )
        if flip_order:
            return self.get_or_create_mapping(
                service_2_name,
                pathway_2_id,
                pathway_2_name,
                service_1_name,
                pathway_1_id,
                pathway_1_name,
                mapping_type,
                user
            )

        # Ensure maintaining the order of the resources
        if mapping_type == EQUIVALENT_TO and _flip_service_order(service_1_name, service_2_name):
            return self.get_or_create_mapping(
                service_2_name,
                pathway_2_id,
                pathway_2_name,
                service_1_name,
                pathway_1_id,
                pathway_1_name,
                mapping_type,
                user
            )

        _ensure_manager(service_1_name)
        _ensure_manager(service_2_name)

        mapping = self.get_mapping(
            service_1_name=service_1_name,
            pathway_1_id=pathway_1_id,
            pathway_1_name=pathway_1_name,
            service_2_name=service_2_name,
            pathway_2_id=pathway_2_id,
            pathway_2_name=pathway_2_name,
            mapping_type=mapping_type
        )

        if mapping is not None:
            _ = self.claim_mapping(mapping, user)

            return mapping, False

        mapping = PathwayMapping(
            service_1_name=service_1_name,
            service_1_pathway_id=pathway_1_id,
            service_1_pathway_name=pathway_1_name,
            service_2_name=service_2_name,
            service_2_pathway_id=pathway_2_id,
            service_2_pathway_name=pathway_2_name,
            type=mapping_type
        )

        vote = Vote(
            mapping=mapping,
            user=user
        )

        self.session.add(mapping)
        self.session.add(vote)
        mapping.creators.append(user)
        self.session.commit()

        return mapping, True

    def delete_all_mappings(self):
        """Delete all the votes then all the mappings."""
        self.session.query(Vote).delete()
        self.session.query(PathwayMapping).delete()
        self.session.commit()

    def delete_mapping_by_id(self, mapping_id):
        """Delete a mapping by its id.

        :param int mapping_id: mapping id
        :rtype: bool
        """
        mapping = self.get_mapping_by_id(mapping_id)

        if mapping:
            self.session.delete(mapping)
            self.session.commit()
            return True
        return False

    """Custom Model Manipulations"""

    def claim_mapping(self, mapping, user):
        """Check if user has already established the mapping, if not claims it.

        :param PathwayMapping mapping: Mapping instance
        :param User user: User
        :rtype: bool
        :return: if mapping was assigned to user
        """
        if user in mapping.creators:
            return False

        mapping.creators.append(user)
        _ = self.get_or_create_vote(user, mapping)
        return True

    def accept_mapping(self, mapping_id):
        """Accept established mapping (from user or curator consensus).

        :param int mapping_id: mapping id
        :rtype: tuple[PathwayMapping,bool]
        :return: mapping and boolean that indicates if transaction was made
        """
        mapping = self.get_mapping_by_id(mapping_id)

        if not mapping:
            return None, False

        if mapping.accepted:
            return mapping, False

        mapping.accepted = True
        self.session.commit()
        return mapping, True

    def get_mappings_from_pathway_with_relationship(self, type, service_name, pathway_id, pathway_name):
        """Get all mappings matching pathway and service name.

        :param str type: mapping type
        :param str service_name: service name
        :param str pathway_id: original pathway identifier
        :param str pathway_name: pathway name
        :rtype: list[PathwayMapping]
        :return:
        """
        return self.session.query(PathwayMapping).filter(
            PathwayMapping.has_pathway_tuple(type, service_name, pathway_id, pathway_name)).all()

    def get_decendents_mappings_from_pathway_with_is_part_of_relationship(self, service_name, pathway_id, pathway_name):
        """Get all mappings matching pathway and service name.

        :param str type: mapping type
        :param str service_name: service name
        :param str pathway_id: original pathway identifier
        :param str pathway_name: pathway name
        :rtype: list[PathwayMapping]
        :return:
        """
        return self.session.query(PathwayMapping).filter(
            PathwayMapping.has_descendant_pathway_tuple(IS_PART_OF, service_name, pathway_id, pathway_name)).all()

    def get_ancestry_mappings_from_pathway_with_is_part_of_relationship(self, service_name, pathway_id, pathway_name):
        """Get all mappings matching pathway and service name.

        :param str type: mapping type
        :param str service_name: service name
        :param str pathway_id: original pathway identifier
        :param str pathway_name: pathway name
        :rtype: list[PathwayMapping]
        :return:
        """
        return self.session.query(PathwayMapping).filter(
            PathwayMapping.has_ancestry_pathway_tuple(IS_PART_OF, service_name, pathway_id, pathway_name)).all()

    def get_all_mappings_from_pathway(self, service_name, pathway_id, pathway_name):
        """Get all mappings matching pathway and service name.

        :param str service_name: service name
        :param str pathway_id: original pathway identifier
        :param str pathway_name: pathway name
        :rtype: list[PathwayMapping]
        :return:
        """
        return self.session.query(PathwayMapping).filter(
            PathwayMapping.has_pathway(service_name, pathway_id, pathway_name)).all()

    def get_all_pathways_from_db_with_mappings(self, pathway_database):
        """Get all mappings that contain a pathway from a given database.

        :param str service_name: service name
        :param str pathway_id: original pathway identifer
        :param str pathway_name: pathway name
        :rtype: list[PathwayMapping]
        :return:
        """
        return self.session.query(PathwayMapping).filter(
            PathwayMapping.has_database_pathway(pathway_database)).all()

    def infer_hierarchy(self, resource, pathway_id, pathway_name):
        """Infer the possible hierarchy of a given pathway based on its equivalent mappings.

        :param str type: mapping type
        :param str resource: service name
        :param str pathway_id: pathway original identifier
        :param str pathway_name: pathway name
        :return:
        """
        matching_mappings = self.get_mappings_from_pathway_with_relationship(
            EQUIVALENT_TO, resource, pathway_id, pathway_name
        )

        inferred_mappings = []

        for mapping in matching_mappings:
            # Get all hierarchical mappings from equivalent pathways

            complement_resource, complement_pathway_id, complement_pathway_name = mapping.get_complement_mapping_info(
                resource, pathway_id, pathway_name
            )

            hierarchical_mappings_from_complement = self.get_mappings_from_pathway_with_relationship(
                IS_PART_OF,
                complement_resource,
                complement_pathway_id,
                complement_pathway_name
            )

            for hierarchical_mapping in hierarchical_mappings_from_complement:
                inferred_mappings.append(hierarchical_mapping.get_complement_mapping_info(
                    resource, pathway_id, pathway_name
                ))

        return inferred_mappings
