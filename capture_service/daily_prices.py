"""整理已收到的日价原文，供采购查询观测日与发布时间。"""

from .ledger import entities


def days(connection, collection):
    latest = {}
    rows = entities(connection, collection)
    source_urls = {digest: url for digest, url in connection.execute(
        'SELECT r.body_sha256,r.source_url FROM receipts r WHERE r.collection=?', (collection,))}
    expected_revisions = {url: revision for url, revision in connection.execute(
        'SELECT source_url,expected_revision FROM collection_sources WHERE collection=?', (collection,))}
    for row in rows:
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
                'source_url': source_urls.get(row['source']),
            }
    for item in latest.values():
        expected = expected_revisions.get(item['source_url'], '')
        item['current_revision'] = not expected or item['version'] == expected
        item['status'] = '已核实' if item['current_revision'] else '新版待取'
    corrections = {}
    for row in rows:
        if row['type'] != 'price_correction':
            continue
        payload = row['payload']
        key = (payload['region'], payload['target_observed_on'])
        order = (payload['issued_on'], row['version'])
        if key not in corrections or order > corrections[key]['order']:
            corrections[key] = {
                'order': order,
                'replacement_cny_kg': payload['replacement_cny_kg'],
                'source_sha256': row['source'],
                'issued_on': payload['issued_on'],
            }
    for key, correction in corrections.items():
        if key not in latest or not latest[key]['current_revision']:
            continue
        latest[key]['price_cny_kg'] = correction['replacement_cny_kg']
        latest[key]['correction_sha256'] = correction['source_sha256']
        latest[key]['correction_issued_on'] = correction['issued_on']
    return [latest[key] for key in sorted(latest)]
