# README

| World Cup - GTFS Schedule parameters |  |  |
|---|---|---|
| Event Date Range<br><br>5 days before the first match in CA;<br>5 days after the last match in CA | 2026-06-07 through 2026-07-15 |  |
| SoFi Stadium Matches<br><br>matches categorized<br>into transit service's<br>time-of-day according to <br>match start time | 2026-06-12 (pm_peak)<br>2026-06-15 (pm_peak)<br>2026-06-18 (midday)<br>2026-06-21 (midday)<br>2026-06-25 (pm_peak)<br>2026-06-28 (midday<br>2026-07-02 (midday)<br>2026-07-10 (midday) |  |
| Sofi - Transit Operators<br><br>(schedule)_gtfs_dataset_name in our<br>data warehouse | LA Metro Events Schedule<br>LA Metro Bus Schedule<br>LA Metro Rail Schedule<br>LA DOT Schedule<br>G Trans Schedule<br>Torrance Schedule<br>Inglewood Schedule<br>Beach Cities GMV Schedule<br>Big Blue Bus Schedule<br>Big Blue Bus Swiftly Schedule<br>Culver City Schedule<br>Metrolink Schedule | some feeds dropped from analysis:<br>Inglewood Schedule<br>Big Blue Bus Swiftly Schedule |
| Levi's Stadium | 2026-06-13 (midday)<br>2026-06-16 (evening)<br>2026-06-19 (evening)<br>2026-06-22 (evening)<br>2026-06-25 (pm_peak)<br>2026-07-01 (pm_peak) |  |
| Levi's - Transit Operators | SCVTA Schedule<br>Bay Area 511 Santa Clara Transit Schedule<br>BART Schedule<br>Bay Area 511 BART Schedule<br>Caltrain Schedule<br>Bay Area 511 Caltrain Schedule<br>ACE Schedule<br>Bay Area 511 ACE Schedule<br>Capitol Corridor Schedule<br>Bay Area 511 Capitol Corridor Schedule<br>Amtrak Schedule | some feeds dropped from analysis:<br>Amtrak Schedule |

## Research Question

How did transit service change, and how much did service increase, for the transit operators who made special service modifications to certain routes.

### Visualizations

We want to explore and drill down what happened during World Cup (trips, stop arrivals, service alerts) with interactive charts and maps.

1. Daily number of trips for each operator, with event days highlighted. Do these go up?
2. Daily number of trips for each route, with event days highlighted. Did the magnitude of service change across routes and operators?
3. LA Metro added a special World Cup feed. What were these special routes and how many trips were made? How did this affect other transit operators who were going to add special service, but instead were included in this special regional feed?
4. How much did stop arrivals differ on event days vs non-event days?
   * Adjust for the typical differences in weekday and weekend service
   * Adjust for the fact that World Cup matches occurred on both weekday and weekend.
5. How did stop arrivals change right around the event window?
   * Matches can be categorized into a time-of-day that matches typical transit service
   * Focus on the stop arrivals in the time-of-day window before, during, and after the match. 


## Special Service Routes

World Cup transit service visualizations focus only on routes that seem to have provided special event service to the stadiums. The majority of stops and routes that got within 3 miles (bus) or 10 miles (rail) of the stadiums did not have service changes. 

The methodology to filter through routes that may have special service was a combination of manual skimming of websites, spatial analysis, and granular route pattern visualizations over the event period.

1. The broad descriptors provided on the transit agency's website provided a starting point for where to look.
2. A spatial analysis of bus routes within 3 miles and rail routes within 10 miles of the stadiums provided more pared down list.
3. Daily route service patterns (number of trips per day for each route-direction) for the pared down list went through visual inspection to find deviations from a typical weekday / weekday service pattern, or any other service pattern that indicated special events.
4. The route names that also seemed to indicate special service with `stadium` in the name were also kept.
 
The full list of routes that most likely had special event service is provided.

| Transit Operator<br>(schedule_gtfs_dataset_name) | Routes with Potential Service Changes<br>(route_name) |  |
|---|---|---|
| LA Metro Bus Schedule | None - couldn't find 22 Los Angeles Stadium Express |  |
| LA Metro Rail Schedule | 803__ Metro C Line <br>807__ Metro K Line |  |
| LA Metro Events Schedule | 1__ R1 El Camino College<br>2__ R2 Union Station<br>3__ R3 Crenshaw Station<br>4__ R4 Hawthorne/Lennox Station<br>5__ R5 Downtown Long Beach<br>6__ R6 ARTIC Anaheim Station<br>7__ R7 Newport Transportation Center<br>8__ S8 Torrance Transit Center<br>9__ S9 Culver City Transit Center<br>10__ S10 Harbor Gateway Transit Center<br>11__ S11 LAX/Metro Transit Center<br>12__ S12 Hotels & Parking LAX<br>13__ T13 Pierce College Station<br>14__ T14 Downtown Santa Monica<br>15__ T15 North Hollywood Station      |  |
| LA DOT Schedule | 712__DASH Chesterfield Square |  |
| G Trans Schedule | 7X__7X Line 7X |  |
| Torrance Schedule | 10__10 LINE 10 |  |
| Big Blue Bus Schedule | T14__T14 Los Angeles Stadium |  |
| Metrolink Schedule | 91 Line__91-PV Line Metrolink 91-Perris Valley Line<br>Antelope Valley Line__AV Line Metrolink Antelope Valley Line<br>Orange County Line__OC Line Metrolink Orange County Line<br>Riverside Line__RIV Line Metrolink Riverside Line<br>San Bernardino Line__SB Line Metrolink San Bernardino Line<br>Ventura County Line__VC Line Metrolink Ventura County Line |  |
| Beach Cities GMV Schedule | None |  |
| Culver City Schedule | None (could not find 99X, could be 9__ S9 Culver City Transit Center) |  |
| Inglewood Schedule | None |  |
| SCVTA Schedule | BBSB__BBWC Bus Bridge WC26<br>BlueS__BlueS Blue Line WC26<br>Blue__Blue Line Baypointe - Santa Teresa<br>GrenS__GreenS Green Line WC26<br>Green__Green Line Old Ironsides - Winchester<br>OranE__OrangeE Orange Line East Segment WC26<br>OranW__OrangeW Orange Line West Segment WC26<br>Ornge__Orange Line Mountain View - Alum Rock |  |
| Bay Area 511 Santa Clara Transit Schedule | BBWC__BBWC Bus Bridge WC26<br>BlueS__BlueS Blue Line WC26<br>Blue Line__Blue Line Baypointe - Santa Teresa<br>GreenS__GreenS Green Line WC26<br>Green Line__Green Line Old Ironsides - Winchester<br>OrangeE__OrangeE Orange Line East Segment WC26<br>OrangeW__OrangeW Orange Line West Segment WC26<br>Orange Line__Orange Line Mountain View - Alum Rock |  |
| Bay Area 511 Caltrain Schedule | South County__South County South Santa Clara County Connector<br>Local Weekday__Local Weekday<br>Local Weekend__Local Weekend |  |
| Bay Area 511 ACE Schedule | ACE__Altamont Commuter Express |  |
| Bay Area 511 Capitol Corridor Schedule | CC__CC Capitol Corridor |  |
| BART Schedule | None |  |
| Bay Area 511 BART Schedule | None |  |

## Special Service Stops

For transit stops that had special service, the methodology to filter through stops spatial analysis with the special service routes.

1. A spatial analysis of bus stops within 3 miles and rail stops within 10 miles of the stadiums provided more pared down list.
2. The stops were filtered down to ones that had arrivals (`stop_times`) for special service routes.


See `world_cup_vars.py` for variables set.
