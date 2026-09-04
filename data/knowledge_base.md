# Spotta AI Knowledge Base

## What Spotta Does

Spotta AI is a browser-based parking assistant. You enter a destination and Spotta finds nearby street parking meters and ranks them so you can pick the best one before you even arrive. There is nothing to install; the whole experience runs as a normal website.

- Enter a destination, get a ranked list of nearby parking meters.
- Ranked by three factors: distance, price, and availability confidence.
- Runs entirely in the browser, no app download needed.
- Coverage is downtown Vancouver only, for now. Other cities may be added later.
- The homepage search box also supports tap-to-talk voice input in Chrome and Edge.

## Parking Data

Spotta's parking spot data comes from the City of Vancouver's Open Data portal, specifically the parking meter dataset. This means the locations and posted rates you see are real, not invented.

- Each spot's latitude, longitude, and hourly rate come from real City of Vancouver meter records.
- Distance shown for each spot is measured from the destination you searched, not from your current location.
- Price shown is the real posted hourly meter rate for that specific meter.
- Some meters have a posted time limit (for example "2 Hr" or "3 Hr"); a few have no posted time limit at all.
- Spotta does not currently cover paid parking lots or garages, only on-street metered parking.

## Confidence Score

The confidence score is Spotta's estimate of how likely a given spot is to be open when you arrive. It is shown as a plain-language label rather than a raw number so it is easier to act on at a glance.

- Shown as one of three labels: Likely open, Uncertain, or Often full.
- It is computed fresh every time you search, not read from a fixed stored number.
- Two real signals feed into it: the time of day and day of week (Vancouver meters are typically busiest on weekday middays and right after the workday ends, and are largely unrestricted on Sundays), and the spot's price relative to other spots in the same result set (pricier meters tend to sit in higher-demand areas).
- Capped at 80%, even in the best case. This estimate is not a live occupancy feed, so it should never claim more certainty than real live-availability data (like a future Parknav/HERE integration) actually supports.
- It is an estimate, not a live occupancy sensor feed, so it can be wrong.
- Always check the posted signage at the actual meter when you arrive, since rules can change (special events, construction, street cleaning).

## Sorting and Filtering Results

Once you search, you are not stuck with a single fixed order. Spotta lets you re-sort the same result set instantly, without doing a new search.

- Best match: the default order, combining distance, price, and confidence.
- Cheapest: sorts by the lowest hourly rate first.
- Closest: sorts by distance from your destination, nearest first.
- Most likely open: sorts by confidence score, highest first.
- Sorting happens instantly in your browser; it does not re-run the search or contact the server again.

## Map and Navigation

Search results are not just a list; they are also plotted on a live map so you can see the overall spatial layout of your options at a glance.

- Results are shown as pins on an interactive map (built with Leaflet and OpenStreetMap), centered on your searched destination.
- A circle on the map shows the 1km radius around your destination, so you can see the search area at a glance without reading each spot's distance.
- Each pin is colored the same as that spot's confidence label: green for Likely open, yellow for Uncertain, red for Often full.
- Clicking a pin's popup shows that spot's name, price, and confidence label, plus a link to navigate there.
- Selecting "Navigate" on a spot opens a dedicated page with a larger map centered on that exact spot.
- The navigate page's "Get directions" button opens Google Maps in a new tab with turn-by-turn driving directions to that spot's real coordinates.
- Spotta does not do its own turn-by-turn routing; the actual driving directions always come from Google Maps.

## Driving Mode

Driving Mode is a simplified view meant for someone who is about to get in the car and just wants the essentials at a glance, without extra clutter.

- Toggled on with a single "Driving Mode" button above the results.
- Shows only the top 3 results as large, high-contrast cards with big text.
- Hides the map, the sort controls, and the raw confidence percentage to reduce distraction.
- Each card has one large "Navigate" button sized for an easy tap.
- Turning Driving Mode off restores the normal full results view instantly.

## Accounts

You do not need an account to search for parking or navigate to a spot; accounts are only needed if you want Spotta to remember what you have done.

- Sign up with a username and password to create an account.
- Log in to access your saved activity across visits.
- Logging in is required to see your dashboard of spots you have navigated to.
- Searching, viewing results, sorting, using Driving Mode, and navigating to a spot all work fully without logging in.

## Spotta Assistant Chatbot

The chatbot you are talking to right now is called the Spotta Assistant. It is meant purely to explain how the Spotta AI website works.

- Available as a floating chat button in the bottom-right corner of every page.
- Answers are grounded only in this knowledge base; it does not browse the web or make things up.
- Supports tap-to-talk voice input for typing your question, the same way the homepage search does.
- Lets you pick which AI model answers, including a free default model and optional paid models, from a dropdown in the chat panel.
- Paid models require credits on the site owner's OpenRouter account; if a paid model has no credits, the chat shows a clear error instead of crashing.

## Contact

- (Placeholder - add support email or contact here.)

## Hours and Availability

- The Spotta AI website itself is available anytime in the browser; it is not tied to business hours.
- Individual parking meters may still have their own enforcement hours and posted time limits, which are separate from Spotta's own availability.

## Policies

- (Placeholder - add any usage or privacy notes here.)

## FAQs

- Q: Is a spot guaranteed to be open? A: No, confidence is only an estimate, never a guarantee.
- Q: Do I need an account? A: Only if you want to save and later view the spots you have visited.
- Q: How is confidence calculated? A: From time of day/day of week and price relative to nearby spots, not live sensors.
- Q: Does Spotta cover parking garages? A: No, only on-street metered parking from the City of Vancouver's open data.
- Q: Can I use Spotta outside Vancouver? A: Not yet; coverage is downtown Vancouver only for now.
- Q: How do I get real turn-by-turn directions? A: Select a spot and use the "Get directions" button, which opens Google Maps.
- Q: Can I change how results are sorted? A: Yes, use the sort dropdown above the results to switch between best match, cheapest, closest, and most likely open.
- Q: What is Driving Mode? A: A simplified view showing only the top 3 spots as large, glanceable cards for use right before you drive.
- Q: Can I search by voice? A: Yes, tap the microphone icon next to the search box or chat box and speak your request.
- Q: Does the chatbot know things outside this knowledge base? A: No, it only answers from the facts stored here.
