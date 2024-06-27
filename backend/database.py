from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)

    queries = relationship('Query', back_populates='user')

class Variable(Base):
    __tablename__ = 'variables'

    id = Column(Integer, primary_key=True)
    code = Column(String, nullable=False)
    title = Column(String, nullable=False)
    description = Column(String)
    category = Column(String)
    data_type = Column(String)

    variable_years = relationship('VariableYear', back_populates='variable')

class VariableYear(Base):
    __tablename__ = 'variable_years'

    id = Column(Integer, primary_key=True)
    variable_id = Column(Integer, ForeignKey('variables.id'))
    year = Column(Integer, nullable=False)
    specific_code = Column(String, nullable=False)
    specific_title = Column(String, nullable=False)

    variable = relationship('Variable', back_populates='variable_years')
    cached_data = relationship('CachedData', back_populates='variable_year')

class GeographicLevel(Base):
    __tablename__ = 'geographic_levels'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)

    query_geographies = relationship('QueryGeography', back_populates='geographic_level')

class Query(Base):
    __tablename__ = 'queries'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    name = Column(String, nullable=False)
    description = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_modified = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship('User', back_populates='queries')
    query_variables = relationship('QueryVariable', back_populates='query')
    query_years = relationship('QueryYear', back_populates='query')
    query_geographies = relationship('QueryGeography', back_populates='query')
    visualizations = relationship('Visualization', back_populates='query')

class QueryVariable(Base):
    __tablename__ = 'query_variables'

    id = Column(Integer, primary_key=True)
    query_id = Column(Integer, ForeignKey('queries.id'))
    variable_id = Column(Integer, ForeignKey('variables.id'))
    axis = Column(String)

    query = relationship('Query', back_populates='query_variables')
    variable = relationship('Variable')

class QueryYear(Base):
    __tablename__ = 'query_years'

    id = Column(Integer, primary_key=True)
    query_id = Column(Integer, ForeignKey('queries.id'))
    year = Column(Integer, nullable=False)

    query = relationship('Query', back_populates='query_years')

class QueryGeography(Base):
    __tablename__ = 'query_geographies'

    id = Column(Integer, primary_key=True)
    query_id = Column(Integer, ForeignKey('queries.id'))
    geographic_level_id = Column(Integer, ForeignKey('geographic_levels.id'))
    specific_geography = Column(String)

    query = relationship('Query', back_populates='query_geographies')
    geographic_level = relationship('GeographicLevel', back_populates='query_geographies')

class Visualization(Base):
    __tablename__ = 'visualizations'

    id = Column(Integer, primary_key=True)
    query_id = Column(Integer, ForeignKey('queries.id'))
    type = Column(String, nullable=False)
    settings = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    query = relationship('Query', back_populates='visualizations')

class CachedData(Base):
    __tablename__ = 'cached_data'

    id = Column(Integer, primary_key=True)
    variable_year_id = Column(Integer, ForeignKey('variable_years.id'))
    geographic_level_id = Column(Integer, ForeignKey('geographic_levels.id'))
    specific_geography = Column(String)
    data_value = Column(String)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    variable_year = relationship('VariableYear', back_populates='cached_data')
    geographic_level = relationship('GeographicLevel')

# Create the tables in the database
engine = create_engine('postgresql://username:password@localhost/acs_data_app')
Base.metadata.create_all(engine)
