## order of operations
1. Define World Cup variables
2. Put together points of interest gdf
3. Download this set of tables from the warehouse

## trips
1. use daily schedule + RT route-direction summary
2. filter to operators near each stadium and tag event date variables
3. can plot individual service date, aggregate by route
4. aggregate by day_type, event_day, make wide
   * add back route_geom here
5. check for proximity to points of interest gdf, do it separately for 2 stadiums
   * 3 miles for bus
   * 10 miles for rail
   * if the spatial join shows that the geom intersects within stadium buffer, then flag with `is_near`
6. optional / leave as function, filter to special routes   

## stops
1. use daily stops, which has pt_geom and time-of-day arrivals
2. filter to operators near each stadium and tag event date variables
3. can plot individual service date
   * what would we do with arrivals by service_date?
   * need day_type because weekday vs weekend arrivals are so different
   * could we do time-of-day by service_date? but we still would compare event day to typical weekday
5. aggregate by day_type, event_day, make wide
   * add back stop geom here
6. check for proximity to points of interest gdf, do it separately for 2 stadiums
   * stops necessarily get closer to the stadium, and some routes will have a couple stops near, but many that are far away
   * for stops, do we want to flag whether stop `is_stop_near` or `is_route_near`?
   * or, do we flag whether stop is on a route that goes near or not?
   * special event service tends to be by route...
7. optional / leave as function, filter to special routes and/or filter to stops within buffer

### stop metrics
* modified event service by event_day / day_type
* modified event service by time-of-day 
 - stop_time visits (use fct_daily_scheduled_stops arrival columns)
   event time window is the time-of-day bucket event falls in, and
   we want to focus on the surrounding windows?
   for non-event days, those same hours will show decreased service, hopefully

## before
A bunch of prep work is needed to prepare fct_daily_scheduled_stops
to be tagged as event / non-event, and aggregate to be ready for viz.
- filtering to stops within vicinity
- filtering to stops along routes that had detected service changes
- aggregate by event / non-event and day_type
- make wide or long for viz, depends on GT or altair


TODO: this needs to be refactored to make more sense conceptually.
It goes back and forth with routes. What is known at each stage, what is the right order?
Can the aggregations be done earlier, then filter for the special routes or stops near stadium?
explode stop's route_id_array and use that to filter