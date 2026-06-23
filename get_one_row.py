from google.cloud import bigquery

client = bigquery.Client(project="promo-roi-platform-2026")
query = '''
    SELECT *
    FROM `promo-roi-platform-2026.promo_roi.promo_features`
    WHERE split = 'validation'
      AND sales_lift_pct IS NOT NULL
      AND margin_impact IS NOT NULL
    LIMIT 3
'''
df = client.query(query).to_dataframe(create_bqstorage_client=False)
print(df.to_string())
