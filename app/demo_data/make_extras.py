import json, random
m = json.load(open("mon.json"))
# best time to go (general guidance, not live data), interest tags, popularity weight for sample trips
X = {
 "Hagia Sophia": ("Right at opening or after 16:00; queues peak late morning.", "history architecture", 10),
 "Blue Mosque (Sultan Ahmed)": ("Early morning between prayers; avoid Friday midday.", "history architecture", 10),
 "Topkapi Palace": ("At opening, Harem first before the tour groups.", "history architecture", 9),
 "Basilica Cistern": ("First slot of the day or the last hour.", "history architecture", 9),
 "Hippodrome (Sultanahmet Square)": ("Any time; lovely lit up after dark.", "history local", 6),
 "Istanbul Archaeology Museums": ("Weekday mornings are quiet.", "history art", 4),
 "Museum of Turkish and Islamic Arts": ("Mid-afternoon when the square is busiest.", "art history", 3),
 "Gulhane Park": ("Mornings, or April for the tulips.", "views local", 4),
 "Grand Bazaar": ("Weekday mornings after 10:00; closed Sundays.", "food local", 9),
 "Spice Bazaar": ("Before noon, before the cruise crowds.", "food local", 7),
 "Suleymaniye Mosque": ("Late afternoon for the Golden Horn view from the terrace.", "architecture views history", 7),
 "Rustem Pasha Mosque": ("Mid-morning between prayers; it's small and quick.", "architecture art", 3),
 "Theodosius Cistern": ("Any time; it's rarely crowded.", "history", 2),
 "Galata Bridge": ("Sunset, with fish sandwiches below the bridge.", "views food local", 6),
 "Galata Tower": ("At opening, or book a sunset slot.", "views history", 8),
 "Istiklal Avenue": ("Evenings, when the street is at its liveliest.", "local food", 8),
 "Taksim Square": ("Any time; a quick stop on the way to Istiklal.", "local", 5),
 "Pera Museum": ("Friday evenings have longer hours.", "art", 3),
 "Istanbul Modern": ("Weekday afternoons; the terrace café faces the sea.", "art sea", 4),
 "Dolmabahce Palace": ("At opening; tickets are timed and sell out.", "history architecture sea", 7),
 "Ortakoy Mosque": ("Sunset or after dark with the bridge lit up.", "views sea architecture", 6),
 "Rumeli Fortress": ("Late afternoon light over the Bosphorus.", "history views sea", 3),
 "Chora (Kariye) Mosque": ("Mornings, then walk down to Balat.", "art history", 3),
 "Balat and Fener streets": ("Weekday mornings for photos without crowds.", "local food", 5),
 "Pierre Loti Hill": ("Sunset with tea; take the cable car up.", "views", 3),
 "Miniaturk": ("Weekday afternoons; good with children.", "local", 2),
 "Maiden's Tower": ("Sunset, seen from Salacak or by boat.", "views sea", 5),
 "Beylerbeyi Palace": ("Mornings, then lunch by the water.", "history architecture sea", 2),
 "Camlica Hill": ("Clear afternoons or at sunset.", "views", 3),
 "Kadikoy Market and Moda": ("Late morning for the market, Moda coast at sunset.", "food local sea", 6),
 "Buyukada (Princes' Islands)": ("A full weekday; weekends are packed.", "sea local views", 5),
}
for x in m:
    bt, tags, pop = X[x["n"]]
    x["bt"] = bt; x["tg"] = tags.split(); x["pop"] = pop
json.dump(m, open("mon.json", "w"), ensure_ascii=False, separators=(",", ":"))

# sample trips for "travellers like you also added" (demo only; the app would count real saved trips)
random.seed(7)
INT = ["history","architecture","food","views","sea","art","local"]
n = len(m); co = [[0]*n for _ in range(n)]; cnt = [0]*n
from math import hypot
def near(a, b): return hypot((m[a]["lon"]-m[b]["lon"])*0.75, m[a]["lat"]-m[b]["lat"]) < 0.025
for t in range(3000):
    likes = set(random.sample(INT, random.choice([1, 2, 2, 3])))
    k = random.choice([3, 4, 5, 6, 6, 7, 8, 9, 10])
    trip = []
    while len(trip) < k:
        w = []
        for i in range(n):
            if i in trip: w.append(0); continue
            v = m[i]["pop"] * (3 if likes & set(m[i]["tg"]) else 0.6)
            if trip and any(near(i, j) for j in trip): v *= 1.8
            w.append(v)
        trip.append(random.choices(range(n), w)[0])
    for i in trip:
        cnt[i] += 1
        for j in trip:
            if i != j: co[i][j] += 1
# P(j | i) in percent
P = [[round(100*co[i][j]/cnt[i]) if cnt[i] else 0 for j in range(n)] for i in range(n)]
json.dump({"n": 3000, "p": P, "pop": [round(100*c/3000) for c in cnt]}, open("cooc.json", "w"), separators=(",", ":"))
print(cnt[:5], P[0][:8])
