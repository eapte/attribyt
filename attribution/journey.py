import polars as pl

def build_journeys(df: pl.DataFrame) -> pl.DataFrame:
    df_sorted = df.sort(['user_id', 'timestamp'])
    all_users = df_sorted['user_id'].unique().to_list()
    conversions = df_sorted.filter(pl.col('revenue') > 0)
    
    if conversions.is_empty():
        journeys = []
        for user_id in all_users:
            user_path = df_sorted.filter(pl.col('user_id') == user_id)
            path = user_path['channel'].to_list()
            if path:
                journeys.append({
                    "user_id": user_id,
                    "journey": path,
                    "total_revenue": 0.0,
                    "has_conversion": False
                })
        return pl.DataFrame(journeys)
    
    journeys = []
    
    for user_id in all_users:
        user_data = df_sorted.filter(pl.col('user_id') == user_id)
        user_conversions = user_data.filter(pl.col('revenue') > 0)
        
        if user_conversions.is_empty():
            path = user_data['channel'].to_list()
            if path:
                journeys.append({
                    "user_id": user_id,
                    "journey": path,
                    "total_revenue": 0.0,
                    "has_conversion": False
                })
        else:
            for conv in user_conversions.iter_rows(named=True):
                conv_time = conv['timestamp']
                conv_revenue = conv['revenue']
                path_data = user_data.filter(pl.col('timestamp') <= conv_time)
                path = path_data['channel'].to_list()
                
                if path:
                    journeys.append({
                        "user_id": user_id,
                        "journey": path,
                        "total_revenue": conv_revenue,
                        "has_conversion": True
                    })
    
    return pl.DataFrame(journeys)