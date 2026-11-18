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
                'correction_id': payload.get('correction_id'),
                'replacement_cny_kg': payload['replacement_cny_kg'],
                'source_sha256': row['source'],
                'issued_on': payload['issued_on'],
            }
    # 撤回只凭已接收原文生效：按 correction_id 关联，并核对地区与观测日一致。
    retractions = {}
    for row in rows:
        if row['type'] != 'price_correction_retraction':
            continue
        payload = row['payload']
        correction_id = payload.get('correction_id')
        if not correction_id:
            continue
        order = (payload['issued_on'], row['version'])
        if correction_id not in retractions or order > retractions[correction_id]['order']:
            retractions[correction_id] = {
                'order': order,
                'region': payload['region'],
                'target_observed_on': payload['target_observed_on'],
                'issued_on': payload['issued_on'],
                'source_sha256': row['source'],
            }
    for key, correction in corrections.items():
        if key not in latest or not latest[key]['current_revision']:
            continue
        item = latest[key]
        item['correction_id'] = correction['correction_id']
        item['correction_sha256'] = correction['source_sha256']
        item['correction_issued_on'] = correction['issued_on']
        item['correction_replacement_cny_kg'] = correction['replacement_cny_kg']
        retraction = retractions.get(correction['correction_id']) if correction['correction_id'] else None
        if (retraction is not None and retraction['region'] == key[0]
                and retraction['target_observed_on'] == key[1]):
            # 撤回依据已到：更正失效，日价回到页面当前版次，撤回证据随日价留痕。
            item['correction_effective'] = False
            item['retraction_sha256'] = retraction['source_sha256']
            item['retraction_issued_on'] = retraction['issued_on']
            continue
        # 缺少撤回原文不能推定更正失效，更正继续覆盖当前日价。
        item['correction_effective'] = True
        item['price_cny_kg'] = correction['replacement_cny_kg']
    return [latest[key] for key in sorted(latest)]
