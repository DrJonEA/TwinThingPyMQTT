#===============================================================================
# TwinDb - Extension of Twin model of thing to be able to save data to DB
# Jon Durrant
# 11-Jan-2021
#===============================================================================

from twin import Twin
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, Column
from sqlalchemy.sql.sqltypes import Boolean, DateTime, Integer, String, Text, JSON
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

class TwinDb(Twin):
    
    #===========================================================================
    # Constructor
    #===========================================================================
    def __init__(self, clientId: str, options: dict = {}):
        super().__init__(options)
        self.clientId = clientId
        
    #===========================================================================
    # Get the client id as a string
    #===========================================================================
    def getClientId(self):
        return self.clientId
    
    #===========================================================================
    # Store the celitn to the DB
    #===========================================================================
    def updateDb(self, session):
        twin = TwinTable(clientId=self.clientId, 
                  reported = self.getReportedState(),
                  reportedMeta = self.getReportedMeta(),
                  desired = self.getDesiredState(),
                  desiredMeta = self.getDesiredMeta(),
                  declined = self.getDeclinedState(),
                  declinedMeta = self.getDeclinedMeta()
            )
        session.merge(twin)
        session.commit()
        return 
    
    #===========================================================================
    # Load the client form the DB
    #===========================================================================
    def loadFromDb(self, session):
        try:
            twin = session.query(TwinTable).filter(TwinTable.clientId==self.clientId).one()
            self.reported.setState(twin.reported)
            self.reported.meta = twin.reportedMeta
            self.desired.setState(twin.desired)
            self.desired.meta = twin.desiredMeta
            self.declined.setState(twin.declined)
            self.declined.meta = twin.declinedMeta 
            return True
        except NoResultFound:
            return False
    
    
    #===========================================================================
    # Count the number of twins in the DB
    #===========================================================================
    def getTwinCount(self, session):
        try:
            count = session.query(TwinTable).count()
            return count
        except NoResultFound:
            return 0
        
    #===========================================================================
    # Needed to passift the twin Framework
    #===========================================================================
    def outputJson(self, s):
        #Nop
        return
        
    
Base = declarative_base()
#============================================================================
# Internal class to use Pandas and SQlAlchemy on the DB
#============================================================================
class TwinTable(Base):
    __tablename__ = 'twin'

    clientId        = Column(String, primary_key=True)
    reported        = Column(JSON)
    reportedMeta    = Column(JSON)
    desired         = Column(JSON)
    desiredMeta     = Column(JSON)
    declined        = Column(JSON)
    declinedMeta    = Column(JSON)

    def __repr__(self):
       return "<Twin(clientId='%s', reported='%s', reportedMeta='%s', desired='%s', desiredMeta='%s', rejected=%d, rejectedMeta=%s)>" % (
            self.clientId, self.reported, self.reportedMeta, self.desired, self.desiredMeta, self.rejected, self.rejectedMeta)


class TwinLog(Base):
    __tablename__ = 'twinlog'

    id = Column(Integer, primary_key=True, autoincrement=True)
    level = Column(String(20), nullable=False)
    msg = Column(Text, nullable=False)
    detail = Column(Text, nullable=False)
    service = Column(String(100), nullable=False)
    source = Column(String(100), nullable=False)
    sourceTS = Column(DateTime, nullable=False)
    ts = Column(DateTime, nullable=False)






'''
CREATE TABLE twin( 
  clientId varchar(80) primary key, 
  reported json,
  reportedMeta json,
  desired json,
  desiredMeta json,
  declined json,
  declinedMeta json
);
'''