from . import install

install.require_sqlalchemy()
install.require_mysql_connector()

from sqlalchemy import create_engine, ForeignKey
from sqlalchemy import Column, Integer, Float, Text, String, DateTime
from sqlalchemy.orm import sessionmaker, relationship, subqueryload
from sqlalchemy.ext.declarative import declared_attr, declarative_base

Session = sessionmaker()

class Base (object):

    @declared_attr
    def __tablename__(cls):
        import re
        camel_case = re.compile('[A-Z][a-z]+')
        table_words = camel_case.findall(cls.__name__)
        return '_'.join(w.lower() for w in table_words)

    @property
    def dict(self):
        keys = [column.name for column in self.__table__.columns]
        return dict((key, getattr(self, key)) for key in keys)


Base = declarative_base(cls=Base)
NonRosettaBase = declarative_base(cls=Base)

class Benchmarks (NonRosettaBase):
    benchmark_id = Column(Integer, primary_key=True, autoincrement=True)
    protocol_ids = relationship('BenchmarkProtocols', order_by='BenchmarkProtocols.protocol_id')
    start_time = Column(DateTime)
    name = Column(Text)
    description = Column(Text)

    def __init__(self, name=None, description=None):
        import datetime
        self.start_time = datetime.datetime.now()
        self.name = name
        self.description = description

    def __repr__(self):
        return '<Benchmark id={0.benchmark_id} name={0.name}>'.format(self)

    @property
    def id(self):
        return self.benchmark_id

    @property
    def protocols(self):
        session = Session.object_session(self)
        protocol_ids = [x.protocol_id for x in self.protocol_ids]
        return session.query(Protocols).\
                filter(Protocols.protocol_id.in_(protocol_ids)).\
                options(subqueryload('*')).\
                all()

    @property
    def batches(self):
        session = Session.object_session(self)
        protocol_ids = [x.protocol_id for x in self.protocol_ids]
        return session.query(Batches).\
                join(Protocols).\
                filter(Protocols.protocol_id.in_(protocol_ids)).\
                options(subqueryload('*')).\
                all()

    @property
    def structures(self):
        session = Session.object_session(self)
        protocol_ids = [x.protocol_id for x in self.protocol_ids]
        return session.query(Structures).\
                join(Batches, Protocols).\
                filter(Protocols.protocol_id.in_(protocol_ids)).\
                options(subqueryload('*')).\
                all()


class BenchmarkProtocols (NonRosettaBase):
    benchmark_id = Column(Integer, ForeignKey('benchmarks.benchmark_id'), primary_key=True)
    protocol_id = Column(Integer, primary_key=True)
    
    def __init__(self, benchmark_id, protocol_id):
        self.benchmark_id = benchmark_id
        self.protocol_id = protocol_id

    def __repr__(self):
        return '<BenchmarkProtocol benchmark_id={0.benchmark_id} protocol_id={0.protocol_id}>'.format(self)


class Protocols (Base):
    protocol_id = Column(Integer, primary_key=True)
    specified_options = Column(String)
    command_line = Column(String)
    svn_url = Column(String)
    svn_version = Column(String)
    script = Column(String)
    batches = relationship('Batches', order_by='Batches.batch_id', backref='protocol')

    def __repr__(self):
        repr = '<Protocol protocol_id={0.protocol_id}>'
        return repr.format(self)


class Batches (Base):
    batch_id = Column(Integer, primary_key=True)
    protocol_id = Column(Integer, ForeignKey('protocols.protocol_id'))
    name = Column(String)
    description = Column(String)
    structures = relationship('Structures', order_by='Structures.struct_id', backref='protocol')

    def __repr__(self):
        repr = '<Batch batch_id={0.batch_id} protocol_id={0.protocol_id} name={0.name}>'
        return repr.format(self)


class Structures (Base):
    struct_id = Column(Integer, primary_key=True)
    batch_id = Column(Integer, ForeignKey('batches.batch_id'))
    tag = Column(String)
    input_tag = Column(String)
    rmsd_features = relationship('ProteinRmsdNoSuperposition', uselist=False)
    score_features = relationship('TotalScores', uselist=False)

    def __repr__(self):
        repr = '<Structure struct_id={0.struct_id} batch_id={0.batch_id} tag={0.tag}>'
        return repr.format(self)


class ProteinRmsdNoSuperposition (Base):
    struct_id = Column(Integer, ForeignKey('structures.struct_id'), primary_key=True)
    reference_tag = Column(String)
    protein_backbone = Column(Float)

    def __repr__(self):
        repr = '<ProteinRmsd struct_id={0.struct_id} reference_tag={0.reference_tag} backbone_rmsd={0.protein_backbone}>'
        return repr.format(self)


class TotalScores (Base):
    struct_id = Column(Integer, ForeignKey('structures.struct_id'), primary_key=True)
    score = Column(Float)

    def __repr__(self):
        repr = '<StructureScore struct_id={0.struct_id} score={0.score}>'
        return repr.format(self)


class ProtocolOutput (NonRosettaBase):
    output_id = Column(Integer, primary_key=True, autoincrement=True)
    benchmark_id = Column(Integer, ForeignKey('benchmarks.benchmark_id'))
    protocol_id = Column(Integer)
    stdout = Column(Text)
    stderr = Column(Text)

    def __init__(self, benchmark_id, protocol_id, stdout, stderr):
        self.benchmark_id = benchmark_id
        self.protocol_id = protocol_id
        self.stdout = stdout
        self.stderr = stderr



def url():
    from . import settings
    url = 'mysql+mysqlconnector://{0.db_user}:{0.db_password}@{0.db_host}:{0.db_port}/{0.db_name}'
    return url.format(settings)

def connect(echo=False):
    from contextlib import contextmanager

    @contextmanager     # (no fold)
    def session_manager():
        session = None
        try:
            engine = create_engine(url(), echo=echo)
            NonRosettaBase.metadata.create_all(engine)
            Session.configure(bind=engine)
            session = Session()
            yield session
            session.commit()

        except:
            if session is not None: session.rollback()
            raise

        finally:
            if session is not None: session.close()

    return session_manager()


def data_frame_from_table(session, table):
    query = session.query(table)
    return data_frame_from_query(query)

def data_frame_from_query(query):
    import pandas
    records = [record.dict for record in query.all()]
    return pandas.DataFrame.from_records(records)

