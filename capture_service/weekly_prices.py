"""把周表与日价对应起来，保留当前能说明的资料范围。"""

from datetime import date, timedelta
from .daily_prices import days
from .ledger import entities


def weeks(connection, collection):
    daily = days(connection, collection)
    result = []
    for row in entities(connection, collection):
        if row['type'] != 'price_table':
            continue
        payload = row['payload']
        observed = [day for day in daily if day['current_revision'] and day['region'] == payload['region']
                    and payload['week_start'] <= day['observed_on'] <= payload['week_end']]
        start = date.fromisoformat(payload['week_start'])
        end = date.fromisoformat(payload['week_end'])
        observed_days = [day['observed_on'] for day in observed]
        missing_days = [(start + timedelta(days=offset)).isoformat()
                        for offset in range((end - start).days + 1)
                        if (start + timedelta(days=offset)).isoformat() not in observed_days]
        observed_mean = (sum(day['price_cny_kg'] for day in observed) / len(observed)
                         if observed else None)
        result.append({
            'region': payload['region'],
            'week_start': payload['week_start'],
            'week_end': payload['week_end'],
            'table_mean_cny_kg': payload['mean_cny_kg'],
            'observed_days': observed_days,
            'missing_days': missing_days,
            'observed_mean_cny_kg': observed_mean,
            'difference_cny_kg': (round(observed_mean - payload['mean_cny_kg'], 4)
                                  if observed_mean is not None else None),
            'table_source_sha256': row['source'],
            'status': '覆盖完整' if not missing_days else '覆盖不完整',
        })
    return result
