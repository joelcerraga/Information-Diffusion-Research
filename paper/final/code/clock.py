def source_clock_to_utc(stamps,clock='audited'):
    naive=pd.to_datetime(stamps,format='%Y%m%d %H%M%S',errors='raise')
    if clock=='documented_est':return naive.dt.tz_localize('Etc/GMT+5').dt.tz_convert('UTC')
    if clock!='audited':raise ValueError('Unknown source clock rule')
    # Calendar rule from independent source comparisons, not from maximising model fit.
    # Source stamps are not London local times: the final five-hour displacement matters.
    return naive.dt.tz_localize('Europe/London',ambiguous='raise',nonexistent='raise').dt.tz_convert('UTC')+pd.Timedelta(hours=5)
