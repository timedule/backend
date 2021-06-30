import datetime
import os
import ast

from sqlalchemy import Column, DateTime, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DB_URL = os.getenv('DATABASE_URL').replace('postgres://', 'postgresql://', 1)
ENGINE = create_engine(DB_URL)
Base = declarative_base()


class Data(Base):
    __tablename__ = 'tables'
    id = Column(Text, primary_key=True)
    owner = Column(Text)
    title = Column(Text)
    main_data = Column(Text)
    template = Column(Text)
    updated_at = Column(DateTime)


Session = sessionmaker(bind=ENGINE)
session = Session()


def get_user(user_id):
    reslist = []
    result = session.query(Data).filter(Data.owner == user_id)
    for row in result:
        reslist.append(
            {
                'id': row.id,
                'title': row.title,
                'updated_at': row.updated_at,
            }
        )
    return reslist


def get_table(id):
    table = session.query(Data).get(id)
    if table:
        if table.main_data:
            main_data = ast.literal_eval(table.main_data)
        else:
            main_data = {}
        if table.template:
            template = ast.literal_eval(table.template)
        else:
            template = []
        return {
            'owner': table.owner,
            'title': table.title,
            'main_data': main_data,
            'template': template,
            'updated_at': table.updated_at,
        }
    else:
        return


def update_table(id, owner, title='', main_data='', template=''):
    if not any([title, main_data, template]):
        return
    table = session.query(Data).get(id)
    if not table:
        session.add(Data(id=id, owner=owner))
        table = session.query(Data).get(id)
    if not table.owner == owner:
        return
    if title:
        table.title = str(title)
    if main_data:
        table.main_data = str(main_data)
    if template:
        table.template = str(template)
    table.updated_at = datetime.datetime.now()
    session.commit()
    return table


def delete_table(id, owner):
    table = session.query(Data).get(id)
    if table:
        if table.owner == owner:
            session.delete(table)
            session.commit()
            return table
        else:
            return
    else:
        return


def delete_user(user_id):
    table = session.query(Data).filter(Data.owner == user_id)
    if not table:
        return
    table.delete()
    session.commit()
    return table
