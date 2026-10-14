# Presentation versions

Each version is one PowerPoint file in this folder: `Istanbul Trip Planner vN.pptx`.
Every round of edits becomes a new file (v4, v5, ...). Older files are never changed.

Live deck (always the latest version): https://claude.ai/artifact/La9fgy4eHHvkx1dPxqHBF2

## v15 (current): the suggestions model and the map algorithms
- New slide 37 "What to see next" (notebook 07): the suggestions network gets the right sight in the top 3 35.5% of the time with interests ticked, against 30.6% for counting trips and 27.0% for most popular.
- Model line-up is now "Fourteen models, five jobs", with a Suggestions column (counting trips, neural network in use).
- Places slide: K-Means now says the days are ordered by nearest next stop and timed over the fastest bridge or ferry.
- "How it fits together": all seven notebooks and their files; the app reads two tables and three model files.
- Learning slide: the fourth card is "Smarter suggestions". 50 slides, all page numbers redone.

## v14: cover without the capstone line
- The "NTI · Machine Learning Capstone" line is gone from the cover. Everything else is the same as v13.

## v13: Ammar's story, the pin walks the deck
- The example traveller is now Ammar (he/his) in the problem, answer, app tour, demo and closing slides. The app screenshots read "Hi, Ammar". (The hidden backup video still shows Sara.)
- Cover: the outline around the names and "Istanbul" is gone.
- Agenda: the pin takes the place of the active part's icon.
- Scoreboard: the bars grow one at a time and the pin drops next to the tuned XGBoost.
- Price ladder (models 1 to 5): a 0 to 35% error scale along the bottom; the pin slides to each model's error as you move through them.
- Island: the pin walks along it, leaving a copper line behind as each part is finished.
- Closing slide: the labels are no longer doubled, a faded Galata photo sits behind it, and the pin walks Ammar's three days while each route draws.
- Fixed everywhere: labels inside charts and maps were printed twice in PowerPoint; now they show once.

## v12: the v10 cover back, with the Kervan logo moving through the deck
- Cover and hook are the v10 ones again, with Kervan written big where İstanbul was (İstanbul moved to the small copper word on the right) and the team names in the Presented by box.
- Cover animation: the arch, then the Blue Mosque rises, the copper pin from the app logo drops onto the dome's finial with a little bounce, the city appears inside it, and then Kervan writes itself in letter by letter.
- Going to the hook, the pin glides down (Morph) and stops next to "That's what Kervan fixes."
- Agenda: a small pin stands on the active part of the wheel and moves to the next part on each slide.
- The island at the top has the pin at its left end on every slide.
- Live demo: the pin drops onto Maiden's Tower with "You are here".
- Closing slide: the pin drops onto Sara's stay on her route map.
- Kept from v11: the island, team names on the closing slide, the centred live demo.

## v11: Kervan up front, team names, the island
- Team names on the cover and the closing slide: Marwan Mohammed, Ammar Ebrahim, Ibrahim Yousry, Adham Mohammed.
- Cover rebuilt around Kervan: the app icon and the Kervan wordmark (both taken from the app's logo files), "Your Istanbul trip planner", a one-line pitch, the names, and the Blue Mosque in the arch on the right. The hook slide ends with the app icon next to "That's what Kervan fixes."
- The progress strip at the top is now a rounded dark "island" (like the iPhone's Dynamic Island), with a copper pill under the current part. On each part slide the island grows and shows the part's name, then shrinks back on the next slide (Morph, using real PowerPoint shapes so it reshapes instead of stretching).
- Live demo: Maiden's Tower is now in the middle of the slide, with LIVE on its left and DEMO on its right.

## v10: Kervan, final numbers, what's new in the app
- The name: Kervan on the cover (big copper word), in every slide header and on the hook ("That's what Kervan fixes").
- Numbers: the trust slide now says AUC 0.954 (notebook 04 rerun). The scoreboard marks tuned XGBoost as the best single model and says the app blends it with our network (notebook 05: R² 0.756 against 0.753).
- New slide after SHAP: Month-long stays (notebook 06). Normal model 63.5% error, median baseline 43.4%, monthly XGBoost 33.9% (R² 0.50).
- New slide before the live demo: Learning from travellers (accounts, saved picks on Supabase, the ranking that learns after 30 picks, real-trip suggestions after 20 trips).
- App screenshots retaken from the current app (new logo, sign out, best deals). Explore stays and How it works are labelled admin only. The one-click slide now says $42 against a fair $74.
- Lessons: "Trees beat our network, but the two blended beat both". Next step "learn ranking weights" is done, so it became "Help travellers during the trip too".
- Closing slide: QR code and kervan.streamlit.app above the GitHub link.
- 49 slides; page numbers redone.

## v9: the app part and the live demo
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
