#===============================================================================
# MQTTGRoup - class for query groups from MQTT ACL
#===============================================================================


from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, Column, text
from sqlalchemy.sql.sqltypes import Boolean, String, JSON
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from sqlalchemy.orm import exc
exceptions = exc.sa_exc
from array import array
import pandas as pd
import logging

class MQTTGroup:
    #===========================================================================
    # Constructor
    #===========================================================================
    def __init__(self, name: str):
        self.name = name
        self.xLogging = logging.getLogger(__name__)
        
    #===========================================================================
    # Get twin ID that belong to a group
    # session: Data base session - sqlalchemy
    #===========================================================================
    def getGroupTwinIds(self, session):
        con = session.connection()
        try: 
            rs = con.execute(text('SELECT DISTINCT clientid FROM mqtt_acl where topic = "GRP/:group/TPC/#"'), {"group": self.name})
            res = []
            for row in rs:
                res.append(row[0])
            return res
        except exceptions.SQLAlchemyError as Argument:
            self.xLogging.exception("Unable to retrieve group from db")
            return []
        
    #=======================================================================
    # Select twins that confirm to sql like query
    # session: Data base session - sqlalchemy
    # select: array of strings naming fields to pull back. if json inside a fiend then dot notation allowed
    # asColumn: will rename the select to a new name
    # where: where dict form: {column: <name>, op: <op>, value: <value>}, {and/or: [set of wheres]}
    # orient: Pandas allowed formats of ["split", "records", "index", "values", "table", "columns"]
    #=======================================================================
    def selectTwinFrame(self, session, select: array = [], asColumn: array = [], where: dict = {}, orient: str="split"):
        sql = 'SELECT '
        selectCount = len(select)
        if (selectCount == 0):
            sql = sql + '* '
        for i in range(selectCount):
            s = self.sqlSelect(select[i])
            
            if (s == "groupId"):
                sql = sql + '"' + self.name + '" as groupId'
            else:
                if (len(asColumn) > i):
                    sql = sql + s + " as `" + asColumn[i] +"`"
                else:
                    sql = sql + s
            if (i == (selectCount -1)):
                sql = sql + " "
            else :
                sql = sql + ", "
        
        sql = sql + "FROM twin WHERE clientId in ("
        targets = self.getGroupTwinIds(session)
        targetCount = len(targets)
        for i in range(targetCount):
            target = targets[i]
            sql = sql + '"' +target + '" '
            if (i < (targetCount -1)):
                sql = sql + ", "
        sql = sql + ')'
        
        if (not where == {}):
            sql = sql + " AND (" + self.whereToSQL(where)+")"
        
        
        sql = sql + ';'
        
        try:
            frame = pd.read_sql(sql, session.connection())
            
            if (not orient in ["split", "records", "index", "values", "table", "columns"]):
                orient = "split"
            return frame.to_json( orient=orient)

        except exceptions.SQLAlchemyError as Argument:
            self.xLogging.exception("Select failed")
            
        return "{}"
    
    
    
    #===========================================================================
    # Convert any select name to sql format, handles itnernam json query
    #===========================================================================
    def sqlSelect(self, column: str):
        parts = column.split(".", 1)
        if (len(parts) == 1):
            return parts[0]
        else:
            return ("json_extract(%s, \'$.%s\')"%(parts[0], parts[1]))

    #===========================================================================
    # Convert a where dict to sql query format
    #===========================================================================
    def whereToSQL(self, where: dict):
        res=""
        if ("column" in where):
            if (("op" in where) and ("value" in where)):
                res = "%s %s %s"%(
                    self.sqlSelect(where["column"]),
                    where["op"],
                    self.sqlLiteral(where["value"])
                    )
        if ("and" in where):
            count = len(where["and"])
            if (count > 0):
                res = "("
                for i in range(count):
                    res = res + self.whereToSQL(where["and"][i])
                    if (i < (count -1)):
                        res = res + " AND "
                res = res + ")"
        if ("or" in where):
            count = len(where["or"])
            if (count > 0):
                res = "("
                for i in range(count):
                    res = res + self.whereToSQL(where["or"][i])
                    if (i < (count -1)):
                        res = res + " OR "
                res = res + ")"
        return res
        
    #=======================================================================
    # Appropriate handle literates for query
    #=======================================================================
    def sqlLiteral(self, o):
        if (isinstance(o, str)):
            return '"%s"'%o
        elif (isinstance(o, int)):
            return '%d'%o
        elif (isinstance(o, float)):
            return '%f'%o
        else:
            return ""+o
        