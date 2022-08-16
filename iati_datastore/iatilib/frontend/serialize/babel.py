from .csv import _activity_fields, _activity_by_country_fields, _activity_by_sector_fields, \
    _transaction_fields, _transaction_by_country_fields, _transaction_by_sector_fields, \
    _budget_fields, _budget_by_country_fields, _budget_by_sector_fields


def extract_csv_column_headings(fileobj, keywords, comment_tags, options):
    out = []
    list_names = [
        '_activity_fields','_activity_by_country_fields','_activity_by_sector_fields',
        '_transaction_fields','_transaction_by_country_fields','_transaction_by_sector_fields',
        '_budget_fields','_budget_by_country_fields','_budget_by_sector_fields',
   ]
    for list_name in list_names:
        for x in globals()[list_name]:
            if isinstance(x, tuple):
                out.append((1, '', x[0], ['A CSV/Excel column header; in '+list_name]))
            else:
                out.append((1, '', x, ['A CSV/Excel column header; in '+list_name]))
    return iter(out)
