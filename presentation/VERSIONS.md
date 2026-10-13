# Presentation versions

Each version is one PowerPoint file in this folder: `Istanbul Trip Planner vN.pptx`.
Every round of edits becomes a new file (v4, v5, ...). Older files are never changed.

Live deck (always the latest version): https://claude.ai/artifact/La9fgy4eHHvkx1dPxqHBF2

## v9 (current): the app part and the live demo
- App tour: three slides with real screenshots of Plan my trip, Explore stays and How it works; the open page grows and Morph swaps it.
- One click traced: the five best stays screen with five numbered steps (K-Means days, XGBoost fair price, trust model, the score, places to eat and transport).
- How it fits together: the real file tree (each notebook and the files it writes), then a second slide showing the app only loads listings_priced.parquet and price_model.joblib.
- Live demo is now a big-word part slide with your Maiden's Tower photo; the tower stands in front of LIVE DEMO.
- Sara's three days: the plan the app made for her (stay, fair price, $496 total, stops and times per day).
- Teşekkürler: the cover's arch comes back with Sara's three routes drawn in.
- Hidden last slide: a 52-second recording of the demo, in case the app fails on the day.
- The progress strip marker slides along when a new part starts; the network slides draw the district chart in the app colours.

## v8: plainer boxes across the whole deck
- Cards, signs, tabs and tags have square corners and no drop shadows. Data and model slides use thin rules, plain lists and a table for trust.
- Small labels above titles are in Kaushan Script, not spaced capitals. The progress bar is a flat strip with square markers.
- Problem slide: the wish list is a plain list and Sara's three questions are handwritten lines. Answer slide: the closing line now reads "Where to stay, what it should cost, and what to see each day." The star in the hook tabs is gone.

## v7: the data and models part, rebuilt
- Data: new "From raw to ready" slide (the cleaning funnel; the two leaky columns get crossed out and slide away). The price map is redrawn in the app colours and fills in district by district; the district chart is now native bars.
- Models: a line-up of all 12 models and the 4 jobs they do, then one slide per price model (Baseline, Ridge, Random Forest, XGBoost, neural network), each with what it is, how we used it and why. A ladder on the left lights up model by model as the error drops.
- Inside our network: a dot travels from input to output over three slides.
- Scoreboard (replaces the old price slide), SHAP waterfall explaining one real Galata listing's fair price, K-Means dots that regroup into the 6 segments, the trust ROC curve drawing in, and a slide for BallTree + the K-Means day planner.
- 40 slides in total.

## v6: more motion before the models
- The App part slide now shows Galata Tower at sunset (your photo, sharpened), with "THE APP" split around the tower.
- Part slides zoom in gently as they appear.
- Cover: the Blue Mosque glides into the corner of the next slide.
- Hook: browser tabs pile up one by one; one click sends them all away and "That's what our planner fixes" lands.
- Agenda: a round monument photo appears in the middle for each part (Hagia Sophia, Grand Bazaar, Blue Mosque, Galata Tower, Maiden's Tower).
- Problem and answer: Sara's zigzag route across the water turns into three tidy days on the same map (a preview of the K-Means day planner). Sara now has three days.
- Cable car: a faint Istanbul skyline behind it and a "Trip ready" stamp at the last stop.
- A small progress bar at the top (Idea, Data, Models, App, Demo) shows where we are in the talk.

## v5: sharper photos and a cable car ride
- The part slide photos were re-made with an AI upscaler (ESRGAN), so they are sharp at full screen. The PowerPoint pictures are also saved at double resolution.
- How it works is now a cable car ride: five slides, the cabin glides to the next stop on every click and that stop's sign grows.
- The App slide still uses Maiden's Tower until a Galata Tower photo is added.

## v4: the app's palette everywhere
- One palette for the whole deck, taken from the app: cream, Martinique navy, Kashmir blue, copper, redwood and gold sand. Only the style changes between parts.
- Agenda: each part of the circle grows when we get to it and shrinks back as we move on (5 extra agenda slides that morph into each other).
- Part slides: a giant title with the monument standing in front of it (Hagia Sophia, Blue Mosque, Maiden's Tower), skies tinted to the palette.
- The problem and our answer are now a short story about a traveller, with no numbers.
- How it works is now a tram line: five stops, and you "change here" for the models at Score.
- Fixed: the cover mosque no longer covers the names; the repo link on the last slide is readable.

## v3: mix of all the references
- Headings in Kaushan Script, to match the brush "Istanbul" lettering.
- Idea and app slides use the Istanbul look. Part 1 and Part 3 use the red ISTANBUL dividers. Part 2 and the notebook slides use the startup look.
- Cover: the real Blue Mosque rises, then "İstanbul" fades in behind it.
- Agenda: each part of the circle pops up on click.
- Everything else animates by itself with fades and gentle rises. Every slide change is a fade.
- Only XGBoost is presented as the price model.
- Placeholders: team names (cover, last slide) and your own lesson (slide 17).

## v2: Night's own XGBoost deck style
- Light grey background, rust accent, dot grids, "01 PART ONE" dividers, outlined cards.
