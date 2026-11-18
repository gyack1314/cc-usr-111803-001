"""整理已收到的日价原文，供采购查询观测日与发布时间。"""

from .ledger import entities


def days(connection, collection):
    latest = {}
    for row in entities(connection, collection):
        if row['type'] != 'daily_page':
            continue
        payload = row['payload']
        key = (payload['region'], payload['observed_on'])
        if key not in latest or row['version'] > latest[key]['version']:
            latest[key] = {
                'region': payload['region'],
                'observed_on': payload['observed_on'],
                'published_on': payload['published_on'],
                'price_cny_kg': payload['price_cny_kg'],
                'version': row['version'],
                'source_sha256': row['source'],
            }
    return [latest[key] for key in sorted(latest)]
