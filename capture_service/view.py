"""按本项目约定展示已接收资料与明确缺口。"""
from .ledger import entities
from .domain import assess
from .collection import coverage
from .daily_prices import days
from .weekly_prices import weeks

def overview(c,collection):
    rows=entities(c,collection)
    result=assess(rows)
    result['collection']=collection
    result['records']=[{'type':r['type'],'id':r['id'],'version':r['version'],'source_sha256':r['source']} for r in rows]
    result['coverage']=coverage(c,collection)
    result['daily_prices']=days(c,collection)
    result['weekly_prices']=weeks(c,collection)
    return result
