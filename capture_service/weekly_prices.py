"""把周表与日价对应起来，保留当前能说明的资料范围。"""

from .daily_prices import days
from .ledger import entities


def weeks(connection, collection):
    daily = days(connection, collection)
    result = []
    for row in entities(connection, collection):
        if row['type'] != 'price_table':
            continue
        payload = row['payload']
        observed = [day for day in daily if day['region'] == payload['region']
                    and payload['week_start'] <= day['observed_on'] <= payload['week_end']]
        result.append({
            'region': payload['region'],
            'week_start': payload['week_start'],
            'week_end': payload['week_end'],
            'table_mean_cny_kg': payload['mean_cny_kg'],
            'observed_days': [day['observed_on'] for day in observed],
            'table_source_sha256': row['source'],
            'status': '有日价可核' if observed else '日价待取',
        })
    return result
