# Event Analysis Visualizations


* brainstorm [reference](https://caltrans-my.sharepoint.com/:w:/g/personal/shweta_adhikari_dot_ca_gov/IQCjVTlct1tRT7ydi-OuxynhASKvDlErYyB8Oxtzs0z0n5U?e=2eywTz) 
* https://c2smart.engineering.nyu.edu/worldcup-metlife/

## Magnitude of Response

Slope chart showing each operator’s baseline trip count on one side and their event day trip count sorted by percent change. Who racked up their services the most during event time? 
    
## Statistical Analysis

A control comparison can be used to assess how transit service changes on event days relative to typical service patterns.

This fits in with comparing daily trips / daily stop arrivals for event vs non-event.

    weekend service is quite different than weekday, so without plotting them separately, we miss out the additional weekend service (since additional service still is much smaller than typical weekday service)

    this can be done on headway or frequency (trips per hour), not just raw trips

Difference-in-difference or route-fixed effects

    that event chart that shows before/event=0/after.
    comparison would be event day vs the last non-event day of similar type
        Fri event, compared to Thurs (compare 2 weekdays)
        Sat event, compare to last Sat event (compare 2 Saturdays, or compare to last Sunday?)
    can compare event vs non-event, near vs far, bus vs rail all at once!
        should be able to tease out whether rail or bus added more service
        think more about the set up for df. what happens if route name changes for special service? need to be able to add them onto the same record to compare what happened.
        add these boolean columns (is_rail, is_near, is_event). remember to avoid perfect multicollinearity, always 1 less column
        this might be able to take the entire df, don't need to filter for stops being within certain buffer. so we can take the entirety of those feeds, for all routes, for all stops, and just throw it into this regression, with the right dummy variables.
