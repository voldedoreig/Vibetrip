"""Personalised Action Guidance and Gemini AI Itinerary Synthesizer for VibeTrip.

Provides deeply tailored, sensorial action advice for every destination and activity
in the Kathmandu Valley. When a GEMINI_API_KEY is available (from env or user input),
it calls Gemini 3.5 Flash / 3.8 Flash to synthesize bespoke narrative journeys. When offline,
it uses a rich expert travel writer knowledge engine to ensure zero generic templates.
"""

import json
import logging
import math
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import urllib.error
import urllib.request

from engine.scoring import haversine_distance_km

logger = logging.getLogger(__name__)


def load_dotenv() -> None:
    """Zero-dependency .env loader that populates os.environ."""
    search_dirs = [
        Path.cwd(),
        Path(__file__).resolve().parent,
        Path(__file__).resolve().parent.parent,
    ]
    for d in search_dirs:
        env_file = d / ".env"
        if env_file.is_file():
            try:
                for line in env_file.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        k, v = line.split("=", 1)
                        os.environ.setdefault(k.strip(), v.strip().strip("'\""))
                    else:
                        os.environ.setdefault("GEMINI_API_KEY", line.strip("'\""))
            except Exception:
                pass
            break


_load_env_file = load_dotenv
load_dotenv()

# Complete Expert Hand-Curated Action Guidance for all 25 Kathmandu Valley Activities
ACTION_GUIDES: Dict[str, Dict[str, Any]] = {
    "boudhanath_stupa": {
        "what_to_do": "Arrive at 7:00 AM before tour vehicles appear. Join the morning kora walking clockwise along the outer brick circle alongside Tibetan elders holding prayer beads. Spin the brass prayer wheels with your right hand, and step into the ground-floor butter lamp chamber to light a clay lamp for safe travels.",
        "taste_pairing": "Climb up to the rooftop terrace of Himalayan Java or Guru Lhakhang; order salted butter tea (Po Cha) and warm Tibetan tingmo bread while overlooking the white dome.",
        "insider_secret": "Look for the small Licchavi stone chaitya dating back to 640 AD tucked into the north-east alley, often decorated with fresh marigold paste.",
        "etiquette_tip": "Always walk clockwise around the stupa; never point your soles directly at the central shrine when resting on the stone ledges.",
        "transit_tip": "Take a private electric taxi or microbus via Ring Road to Boudha Gate; avoid 5:00 PM rush-hour choke points near Chabahil.",
        "ideal_window": "6:30 AM – 8:30 AM (golden mist, chanting monks, quiet contemplative light)",
        "duration_hours": 2.0,
        "lat": 27.7215, "lng": 85.3620
    },
    "swayambhunath_stupa": {
        "what_to_do": "Climb the 365 ancient stone steps from the eastern entrance through cedar woods. At the summit platform, turn the massive gilded vajra (thunderbolt) prayer wheel, then pause at the western overlook to take in the full morning panorama of the Kathmandu bowl.",
        "taste_pairing": "Grab a hot glass of spiced masala chiya and crispy fresh sel roti from the tiny Newari tea stall beside the western steps.",
        "insider_secret": "Behind the main stupa stands the Harati Devi temple dedicated to the protector of children—notice mothers bringing puffed rice offerings here every morning.",
        "etiquette_tip": "Secure loose sunglasses and snacks; the resident rhesus macaques are curious and agile. Circumambulate clockwise.",
        "transit_tip": "Walk 25 minutes west through Chhetrapati from Thamel, or take a quick 10-minute taxi to the eastern stairway base.",
        "ideal_window": "6:45 AM – 8:30 AM (clear morning skies before valley haze rises)",
        "duration_hours": 2.0,
        "lat": 27.7149, "lng": 85.2903
    },
    "pashupatinath_aarti": {
        "what_to_do": "Cross the footbridge to the eastern bank of the Bagmati River across from the main temple. Sit on the stone ghats at 6:00 PM as priests prepare for the evening Sandhya Aarti, waving massive three-tiered brass oil lamps in sync with rhythmic dholak drumming.",
        "taste_pairing": "Sip fresh cardamom-infused milk tea served in clay kulhad cups from the small stalls along the Guhyeshwari path.",
        "insider_secret": "Wander the quiet row of 15 identical whitewashed Shiva shrines on the hill above the eastern ghats; peaceful and devoid of crowds.",
        "etiquette_tip": "The innermost golden sanctum is open only to practicing Hindus; visitors have panoramic views from the open terraces on the opposite riverbank.",
        "transit_tip": "Arrive by 5:15 PM via Gaushala junction to secure a seat on the stone steps before local crowds gather for the 6:00 PM chimes.",
        "ideal_window": "5:30 PM – 7:30 PM (atmospheric incense smoke and glowing oil lamps at dusk)",
        "duration_hours": 2.0,
        "lat": 27.7104, "lng": 85.3487
    },
    "pashupatinath_temple": {
        "what_to_do": "Cross the footbridge to the eastern bank of the Bagmati River across from the main temple. Sit on the stone ghats at 6:00 PM as priests prepare for the evening Sandhya Aarti, waving massive three-tiered brass oil lamps in sync with rhythmic dholak drumming.",
        "taste_pairing": "Sip fresh cardamom-infused milk tea served in clay kulhad cups from the small stalls along the Guhyeshwari path.",
        "insider_secret": "Wander the quiet row of 15 identical whitewashed Shiva shrines on the hill above the eastern ghats; peaceful and devoid of crowds.",
        "etiquette_tip": "The innermost golden sanctum is open only to practicing Hindus; visitors have panoramic views from the open terraces on the opposite riverbank.",
        "transit_tip": "Arrive by 5:15 PM via Gaushala junction to secure a seat on the stone steps before local crowds gather for the 6:00 PM chimes.",
        "ideal_window": "5:30 PM – 7:30 PM (atmospheric incense smoke and glowing oil lamps at dusk)",
        "duration_hours": 2.0,
        "lat": 27.7104, "lng": 85.3487
    },
    "patan_durbar_square": {
        "what_to_do": "Enter through the south gate of Mangal Bazaar. Walk through Sundari Chowk to marvel at the 17th-century Royal Bath (Tusha Hiti) carved with stone deities. Step into the hidden bahals (monastic courtyards) where master repoussé artisans beat bronze sheets into sacred statues.",
        "taste_pairing": "Head down Swotha square to Cafe Swotha; try their spiced chickpea curry (Chana Tarkari), crispy Bara (lentil pancake), and hand-poured single-origin Nepali coffee.",
        "insider_secret": "Step into the courtyard of the Golden Temple (Kwa Bahal) where an unbroken bronze lamp has stayed burning for centuries, maintained by a young prepubescent priest.",
        "etiquette_tip": "Leather items (belts, bags) must be left outside the inner sanctum of the Golden Temple.",
        "transit_tip": "Take the Kupondole bridge route from Kathmandu; alight at Patan Dhoka and wander the quiet brick alleys inward to avoid car congestion.",
        "ideal_window": "9:30 AM – 11:30 AM (soft morning sunlight filtering through carved timber windows)",
        "duration_hours": 2.5,
        "lat": 27.6744, "lng": 85.3250
    },
    "bhaktapur_durbar_square": {
        "what_to_do": "Spend the morning wandering the vehicle-free brick streets. Gaze up at the five-tiered Nyatapola Temple—climb the steep stone steps guarded by stone wrestlers and elephants. Continue to Pottery Square to watch master potters spin clay on heavy wooden cartwheels.",
        "taste_pairing": "Buy authentic Juju Dhau ('King of Curds') served cold in small porous red clay khora bowls from local sweet shops in Taumadhi Square.",
        "insider_secret": "Behind the 55-Window Palace, look for the Taleju Bell—rung in medieval times to assemble city citizens in times of crisis.",
        "etiquette_tip": "Do not step on the wet clay pots drying in the sun in Pottery Square (Talako); artisans lay them out in precise drying grids.",
        "transit_tip": "Take a private car via the 6-lane Araniko Highway (35 minutes from Kathmandu); depart before 8:30 AM to beat truck traffic at Koteshwor.",
        "ideal_window": "8:00 AM – 10:30 AM (watch women carrying copper water jugs through medieval lanes)",
        "duration_hours": 3.5,
        "lat": 27.6722, "lng": 85.4281
    },
    "nagarkot_sunrise": {
        "what_to_do": "Set your alarm for 5:15 AM. Walk up to the Nagarkot View Tower or sit on your ridge terrace as the horizon shifts from indigo to pale rose. Watch eight distinct Himalayan massifs (from Annapurna to Everest) catch the first golden rays.",
        "taste_pairing": "Warm your hands around a steaming mug of ginger-lemon-honey tea with warm Tibetan pan-bread.",
        "insider_secret": "After sunrise, hike the gentle 2-hour Nature Trail winding through pine forests towards the Tamang village of Kartike.",
        "etiquette_tip": "Carry a warm fleece jacket; alpine ridge breezes at 2,175 meters are chilly even in spring and autumn.",
        "transit_tip": "Depart Bhaktapur or Kathmandu by 4:15 AM for dawn viewing, or arrive the evening prior to sleep at a ridge eco-lodge.",
        "ideal_window": "5:30 AM – 7:30 AM (peak sunrise clarity before thermal cloud formation)",
        "duration_hours": 2.5,
        "lat": 27.7172, "lng": 85.5200
    },
    "shivapuri_peak_hike": {
        "what_to_do": "Enter via Budhanilkantha gate (pass the sacred sleeping Vishnu statue). Ascend through dense oak and rhododendron forest up to Nagi Gompa nunnery, continuing along stone switchbacks to the Bagdwar spring—the sacred mythical source of the Bagmati river.",
        "taste_pairing": "Unpack trail oranges, roasted soybeans (bhatmas), and warm herbal tea from your thermos while sitting on the sunny meadow of Nagi Gompa.",
        "insider_secret": "Watch for rare Himalayan monal pheasants and orchids blooming on mossy branches between 2,200m and 2,500m.",
        "etiquette_tip": "Register with the Nepal Army checkpoint at the gate; stay strictly on marked paths as this is an active protected watershed.",
        "transit_tip": "Take a morning taxi to Budhanilkantha Narayanthan (30 min north of Thamel) to begin climbing before the midday sun heats the forest.",
        "ideal_window": "7:30 AM – 1:30 PM (crisp forest morning and clear views)",
        "duration_hours": 4.5,
        "lat": 27.7983, "lng": 85.3850
    },
    "thamel_food_walk": {
        "what_to_do": "Duck away from the tourist gear shops into the hidden culinary courtyards connecting Thamel to Chhetrapati. Watch open-skillet Newari chefs flash-fry buff choila, press spiced aloo tama, and steam delicate momos inside multi-tiered aluminum steamers.",
        "taste_pairing": "Pull up a low stool for steaming jhol momos smothered in rich sesame-tomato achar, followed by sweet hot lassi.",
        "insider_secret": "Find the tiny unmarked entrance to Phat Kath courtyard for organic local coffee and secluded open-air timber bench seating.",
        "etiquette_tip": "When ordering spicy dishes, ask for 'khursani thorei' if you prefer milder chili levels; local timur peppercorns have a surprising tongue-numbing buzz.",
        "transit_tip": "Purely pedestrian exploration; best navigated entirely on foot from your accommodation in or near central Kathmandu.",
        "ideal_window": "12:30 PM – 2:30 PM or 5:30 PM – 7:30 PM",
        "duration_hours": 2.0,
        "lat": 27.7153, "lng": 85.3110
    },
    "momo_cooking_class": {
        "what_to_do": "Step into a sunlit family kitchen in Lalitpur or Thamel. Learn the delicate art of kneading flour dough, rolling paper-thin discs, and master the intricate 12-fold thumb-and-finger pleating technique that seals in spiced minced fillings.",
        "taste_pairing": "Grind roasted tomatoes, Sichuan pepper (timur), coriander, and toasted sesame on a flat silauto stone to create fresh homemade dipping achar.",
        "insider_secret": "Add a tablespoon of cold melted ghee or bone broth to the meat/vegetable mince mixture before folding—this guarantees juicy burst-in-the-mouth momos upon steaming.",
        "etiquette_tip": "Always wash hands thoroughly and remove rings before working with the collective dough bowl.",
        "transit_tip": "Coordinate with your cooking instructor for hotel alley pickup or take an easy morning rickshaw to the cooking studio.",
        "ideal_window": "10:30 AM – 1:30 PM (prepare lunch together)",
        "duration_hours": 3.0,
        "lat": 27.7120, "lng": 85.3130
    },
    "thangka_art_workshop": {
        "what_to_do": "Sit on floor cushions in a peaceful Patan or Boudha atelier. Observe master painters grinding lapis lazuli, malachite, and 24-karat gold dust into water-based pigments. Use single-hair brushes to practice sacred geometric proportions (iconometry) of the Mandala.",
        "taste_pairing": "Sip fragrant jasmine or green tea poured continuously into porcelain bowls by the studio apprentices.",
        "insider_secret": "The intricate gold linework on Buddha's robe is burnished with a polished agate stone to give it an eternal metallic sheen under sunlight.",
        "etiquette_tip": "Speak in quiet tones; traditional thangka painting is practiced as an active form of Buddhist meditation.",
        "transit_tip": "Locate studios around the outer ring of Boudhanath Stupa or near Patan's Golden Temple; allow a relaxed 15-minute walk from the main gate.",
        "ideal_window": "1:30 PM – 4:00 PM (optimal natural afternoon light in studio courtyards)",
        "duration_hours": 2.5,
        "lat": 27.7210, "lng": 85.3615
    },
    "chandragiri_cable_car": {
        "what_to_do": "Take the scenic 10-minute gondola glide rising 1,000 vertical meters through subtropical forest to Chandragiri Ridge (2,551m). Visit Bhaleshwor Mahadev Temple at the summit and walk the panoramic glass skywalk.",
        "taste_pairing": "Sip hot ginger tea at the summit cafe while gazing at the dramatic sweep from Manaslu to Mount Everest.",
        "insider_secret": "History recalls this ridge as the exact viewpoint where King Prithvi Narayan Shah first envisioned uniting the separate Kathmandu kingdoms.",
        "etiquette_tip": "Book your cable car ticket in advance during weekend mornings to bypass family queues.",
        "transit_tip": "Hire a taxi for the 45-minute drive southwest through Kalanki to the Thankot base station; depart by 8:30 AM to avoid ring-road bottlenecks.",
        "ideal_window": "9:00 AM – 11:30 AM (morning clarity before clouds gather around the ridge)",
        "duration_hours": 3.0,
        "lat": 27.6742, "lng": 85.2081
    },
    "thamel_live_music": {
        "what_to_do": "Settle into an intimate timber-framed music bar like Moksh or Purple Haze. Listen to acoustic guitarists and sarangi players blending Nepali folk ballads with blues, funk, and ragas beneath ambient paper lanterns.",
        "taste_pairing": "Order a cold craft bottle of Gorkha or Barahsinghe beer alongside sizzling platters of buff sukuti (dried spicy meat) and roasted peanuts.",
        "insider_secret": "Ask the house band if they perform any traditional Resham Firiri or instrumental tunes using the madal drum.",
        "etiquette_tip": "Tipping the band jar shows heartfelt appreciation for Kathmandu’s world-renowned indie musicians.",
        "transit_tip": "Most venues are located within a 5-minute stroll across central Thamel; walking back to your hotel is safe and illuminated.",
        "ideal_window": "8:00 PM – 10:30 PM (lively evening atmosphere)",
        "duration_hours": 2.5,
        "lat": 27.7140, "lng": 85.3120
    },
    "basantapur_durbar_square": {
        "what_to_do": "Climb the high tiered brick plinth of Maju Dega temple to watch the living spectacle of Kathmandu pass beneath you. Walk to Kumari Ghar and wait respectfully in the carved timber courtyard for a glimpse of the Living Goddess at the gilded window.",
        "taste_pairing": "Cross into adjacent Freak Street (Jochhen Tole) for freshly baked apple pie, snow cake, and dark masala tea at iconic heritage bakeries.",
        "insider_secret": "Locate the terrifying, fierce 17th-century black stone relief of Kal Bhairav—historically used as a judicial test where suspects swore oaths.",
        "etiquette_tip": "Never point cameras or phones toward the second-floor windows if the Kumari appears; photography of the Living Goddess is strictly forbidden.",
        "transit_tip": "Walk 12 minutes south from Thamel through the vibrant old market lanes; avoid taking taxis into the narrow heritage precinct.",
        "ideal_window": "8:00 AM – 10:30 AM or 4:00 PM – 6:00 PM",
        "duration_hours": 2.5,
        "lat": 27.7042, "lng": 85.3075
    },
    "garden_of_dreams": {
        "what_to_do": "Escape the bustling city streets through the neoclassical gate into Field Marshal Kaiser Sumsher's 1920 Edwardian pleasure garden. Relax beside sunken amphitheaters, marble lotus ponds, and pavilions dedicated to Nepal's six seasons.",
        "taste_pairing": "Relax on the veranda of Kaiser Cafe with an iced mint-lime cooler and warm walnut cardamom cake.",
        "insider_secret": "Find the quiet European library pavilion showcasing antique photos of Kathmandu during the Rana dynasty.",
        "etiquette_tip": "Speak softly to preserve the tranquil library and sanctuary atmosphere; entry ticket is paid at the wooden turnstile.",
        "transit_tip": "Situated directly at the southern entrance gate of Thamel on Tridevi Sadak; effortless 2-minute walk from major hotels.",
        "ideal_window": "2:30 PM – 5:00 PM (gentle golden hour shade and quiet reflection)",
        "duration_hours": 1.5,
        "lat": 27.7144, "lng": 85.3150
    },
    "taumadhi_pottery_square": {
        "what_to_do": "Walk 300 meters south from Nyatapola Temple into Talako (Pottery Square). Watch multi-generational potter families mold damp black clay on heavy wooden spin-wheels, firing thousands of terracotta cups, bowls, and piggy banks (Khutruke) under straw kilns.",
        "taste_pairing": "Stop at a corner tea stall for warm sweet chiya served directly in a freshly fired red earthenware cup that you can take home.",
        "insider_secret": "Ask a master potter to let you press your thumb into the spinning clay wheel to shape a small butter lamp (pala) with your own hands.",
        "etiquette_tip": "Watch your feet carefully; potters lay rows of wet clay vessels across the square cobblestones to dry in the sun.",
        "transit_tip": "Walk 5 minutes through the brick lanes connecting Bhaktapur Durbar Square to Taumadhi; keep vehicles completely outside the old gate.",
        "ideal_window": "9:30 AM – 12:00 PM (watch drying yards and active wheels)",
        "duration_hours": 2.0,
        "lat": 27.6710, "lng": 85.4270
    },
    "kopan_monastery_meditation": {
        "what_to_do": "Climb the hill of Kopan overlooking the northeast valley basin. Sit quietly in the main Tibetan meditation hall beneath intricate frescoes of the Wheel of Life. Walk through the stupa garden spinning prayer wheels in silence.",
        "taste_pairing": "Enjoy a nourishing vegetarian lunch of vegetable noodle thukpa, fresh pumpkin curry, and lemon tea in the monastery dining hall.",
        "insider_secret": "Check the monastery bulletin board for daily public Dharma discourses and guided afternoon mindfulness sessions.",
        "etiquette_tip": "Remove your shoes, hat, and sunglasses before entering the meditation shrine; silence all mobile notifications.",
        "transit_tip": "Take a 15-minute taxi from Boudhanath north up the winding rural road through pine trees to the monastery summit gate.",
        "ideal_window": "9:00 AM – 11:30 AM or 2:00 PM – 4:00 PM",
        "duration_hours": 2.5,
        "lat": 27.7420, "lng": 85.3640
    },
    "newari_feasting_kirtipur": {
        "what_to_do": "Ascend to the medieval hilltop fortress town of Kirtipur. Wander past the ancient stone battlements of Bagh Bhairab Temple where historic weapons hang from the eaves, and look out over the entire southern valley basin.",
        "taste_pairing": "Sit cross-legged on straw sukul mats at Newa Lahana; feast on an authentic brass plate of Samay Baji—beaten rice (baji), spicy grilled buffalo meat (choila), black soybeans, boiled egg, ginger, and a pour of clear rice aila spirit.",
        "insider_secret": "Step inside the top pavilion of Uma Maheshwar temple to view the intricately carved wooden Shiva-Parvati struts framed against the mountains.",
        "etiquette_tip": "Remove footwear when stepping onto the woven straw dining mats in Newari community food halls.",
        "transit_tip": "Take a 25-minute taxi southwest via Tribhuvan University road; alight at Devdhoka gate to explore the car-free ridge on foot.",
        "ideal_window": "11:30 AM – 2:30 PM (ideal for authentic slow midday Newari feasting)",
        "duration_hours": 3.0,
        "lat": 27.6797, "lng": 85.2778
    },
    "kirtipur_old_town": {
        "what_to_do": "Walk the cobblestone ridge of ancient Kirtipur. Climb to Chilamchu Stupa and the fortress-like Bagh Bhairab Temple with its open gallery of captured Gurkha weapons dating back to King Prithvi Narayan Shah's 1768 conquest.",
        "taste_pairing": "Sit at Lahana Newari Restaurant on woven straw sukul mats; order a traditional Samay Baji plate with beaten rice, spiced choila, fermented radish, and fresh aila (distilled rice spirit).",
        "insider_secret": "Climb to the top terrace of Uma Maheshwar Temple at sunset for sweeping views across the entire valley basin framed by carved wooden Shiva-Parvati struts.",
        "etiquette_tip": "Remove shoes when stepping onto the straw dining mats in traditional Newari food halls.",
        "transit_tip": "Take a 25-minute taxi southwest via Tribhuvan University road; alight at Devdhoka gate to explore the car-free ridge on foot.",
        "ideal_window": "11:30 AM – 2:30 PM (ideal for authentic slow midday Newari feasting)",
        "duration_hours": 3.0,
        "lat": 27.6797, "lng": 85.2778
    },
    "champadevi_ridge_trail": {
        "what_to_do": "Hike the shaded pine and rhododendron ridge trail rising along the southwestern rim of Kathmandu Valley to Champadevi Peak (2,285m). Stand at the sacred summit shrine fluttering with Buddhist and Hindu prayer flags.",
        "taste_pairing": "Pack local apples, roasted peanuts, and a vacuum flask of hot ginger chiya to drink on the breezy rocky summit overlook.",
        "insider_secret": "The trail offers one of the clearest viewing angles of Langtang Himal, Gauri Shankar, and the serpentine Bagmati River carving through Chobhar Gorge.",
        "etiquette_tip": "Pack out all wrappers and plastic bottles; leave the sacred hilltop shrine pristine for local weekend pilgrims.",
        "transit_tip": "Start from Hattiban Resort gate (35 min drive from Lalitpur); return before 3:30 PM to avoid dusk mountain chills.",
        "ideal_window": "8:00 AM – 1:30 PM (morning mountain clarity)",
        "duration_hours": 4.0,
        "lat": 27.6350, "lng": 85.2600
    },
    "indoor_climbing_adventure": {
        "what_to_do": "Head to Astrek Climbing Wall in Thamel—the premier bouldering and sport climbing hub in Nepal. Warm up on boulder problems, clip into top-ropes with experienced mountain climbing sherpas, and hone your footwork.",
        "taste_pairing": "Recharge at the poolside climbing cafe with a fresh banana-peanut-butter smoothie and a warm chicken-avocado wrap.",
        "insider_secret": "Many of the instructors are active high-altitude mountaineering guides who have summitted 8,000-meter peaks; ask them about expedition lore.",
        "etiquette_tip": "Chalk up responsibly, respect climbing lane zones, and belay strictly with certified locking carabiners.",
        "transit_tip": "Located directly in Amrit Marg, north Thamel; easily reached on foot in 5 minutes from any Thamel guesthouse.",
        "ideal_window": "2:00 PM – 5:00 PM (great midday activity when city streets are warm)",
        "duration_hours": 2.0,
        "lat": 27.7170, "lng": 85.3115
    },
    "asan_spice_bazaar": {
        "what_to_do": "Arrive early at Asan Chowk where six historic trade lanes converge. Pay respects at the three-tiered Annapurna Ajima shrine, look for the ancient stone fish (Nya Lohan) set into the pavement, and watch merchants ladle mountain timur, dried turmeric, and saffron threads from brass basins.",
        "taste_pairing": "Stop by the century-old sweet stall for piping hot Jerri Swari (crisp pretzel pastry wrapped in soft flatbread) and rich spiced curd.",
        "insider_secret": "Look down at the pavement stone fish (Nya Lohan)—legend holds that a falling fish landed here in Licchavi times, marking the market's auspicious founding.",
        "etiquette_tip": "Keep to the side of the narrow lanes when brass-plate porters or motorcycle bells sound behind you.",
        "transit_tip": "Walk 7 minutes east from Kathmandu Durbar Square or 8 minutes south from Thamel; best experienced entirely on foot.",
        "ideal_window": "7:30 AM – 9:30 AM (pulsing morning market vitality)",
        "duration_hours": 2.0,
        "lat": 27.7077, "lng": 85.3134
    },
    "asan_tole_market": {
        "what_to_do": "Arrive early at Asan Chowk where six historic trade lanes converge. Pay respects at the three-tiered Annapurna Ajima shrine, look for the ancient stone fish (Nya Lohan) set into the pavement, and watch merchants ladle mountain timur, dried turmeric, and saffron threads from brass basins.",
        "taste_pairing": "Stop by the century-old sweet stall for piping hot Jerri Swari (crisp pretzel pastry wrapped in soft flatbread) and rich spiced curd.",
        "insider_secret": "Look down at the pavement stone fish (Nya Lohan)—legend holds that a falling fish landed here in Licchavi times, marking the market's auspicious founding.",
        "etiquette_tip": "Keep to the side of the narrow lanes when brass-plate porters or motorcycle bells sound behind you.",
        "transit_tip": "Walk 7 minutes east from Kathmandu Durbar Square or 8 minutes south from Thamel; best experienced entirely on foot.",
        "ideal_window": "7:30 AM – 9:30 AM (pulsing morning market vitality)",
        "duration_hours": 2.0,
        "lat": 27.7077, "lng": 85.3134
    },
    "heritage_puppet_show": {
        "what_to_do": "Attend an intimate evening performance of traditional Newari and Nepali wooden string puppetry. Watch master puppeteers animate mythological tales of deities, demons, and village folk heroes accompanied by harmonium and tabla rhythms.",
        "taste_pairing": "Sip hot spiced ginger chiya with sweet sesame laddu during the intermission.",
        "insider_secret": "The handcrafted wooden puppet heads are carved from sacred wood and hand-painted using natural vegetable dyes passed down through generations.",
        "etiquette_tip": "Arrive 15 minutes before the opening gong to take floor cushions near the front stage; silence cameras during dialogues.",
        "transit_tip": "Venues are clustered around Patan or central Thamel; an easy evening walk or short 5-minute taxi ride.",
        "ideal_window": "6:00 PM – 8:00 PM (evening cultural performance)",
        "duration_hours": 2.0,
        "lat": 27.6730, "lng": 85.3240
    },
    "godavari_botanical_gardens": {
        "what_to_do": "Stroll the expansive footpaths of the National Botanical Garden at the base of Mount Phulchowki. Walk across mossy timber bridges crossing clear mountain streams, visit the Japanese rock pond, and admire indigenous Himalayan ferns and orchids.",
        "taste_pairing": "Pack a picnic of sweet oranges, roasted corn, and steamed vegetable momos to enjoy on the sunlit meadow lawns.",
        "insider_secret": "Follow the upper trail leading toward the sacred Godavari Kunda natural freshwater springs where cold mineral water wells up from underground aquifers.",
        "etiquette_tip": "Stay on designated walking paths; do not collect wild botanical specimens or disturb nesting endemic flycatchers.",
        "transit_tip": "Take a private car 45 minutes south of Lalitpur; depart early morning to enjoy dewy woodland tranquility.",
        "ideal_window": "9:00 AM – 1:00 PM (dewy morning stillness and forest shade)",
        "duration_hours": 3.5,
        "lat": 27.5956, "lng": 85.3817
    },
    "woodcarving_patachitra_studio": {
        "what_to_do": "Step into an authentic family woodcarving workshop in the hidden courtyards of Patan. Watch master Shilpakar artisans chisel seasoned Sal wood into intricate peacock windows, floral lintels, and protective deity brackets.",
        "taste_pairing": "Sip salted Tibetan butter tea or sweet spiced chiya served in a brass bowl while watching wood chips fly from the gouge chisel.",
        "insider_secret": "Notice how master artisans carve without electric power tools, relying exclusively on steel gouges, wooden mallets, and hand measurements.",
        "etiquette_tip": "Greet the master craftsman with 'Namaste' or 'Jojolapa' before examining tools; ask permission before photographing in-progress sacred carvings.",
        "transit_tip": "Walk 4 minutes north of Patan Durbar Square into the narrow residential bahals; look for the sound of rhythmic mallets on wood.",
        "ideal_window": "10:00 AM – 1:00 PM (artisans at work in courtyards)",
        "duration_hours": 2.0,
        "lat": 27.6755, "lng": 85.3260
    },
    "mandala_acoustic_jam": {
        "what_to_do": "Climb to a rooftop garden cafe overlooking ancient stupas or temple spires. Settle in for an evening acoustic jam session combining traditional flute (bansuri), tabla percussion, and acoustic guitars playing evocative mountain folk fusion.",
        "taste_pairing": "Sip warm Himalayan honey-ginger tea or local craft beer accompanied by a bowl of spiced sadeko peanuts and roasted corn.",
        "insider_secret": "Many musicians welcome travelers with musical backgrounds to join in the rhythm circle with shaker eggs and finger cymbals.",
        "etiquette_tip": "Keep your conversation at a respectful volume during delicate acoustic instrumental solos.",
        "transit_tip": "Located on rooftop venues around Boudha or Thamel; easily accessed by walking within the pedestrian zone.",
        "ideal_window": "6:30 PM – 9:00 PM (twilight fusion jam)",
        "duration_hours": 2.0,
        "lat": 27.7215, "lng": 85.3625
    },
    "central_zoo_jawalakhel": {
        "what_to_do": "Explore the historic Rana-era royal garden grounds surrounding the expansive central lake. Stroll under century-old eucalyptus trees, visit the nocturnal house, and spot rare Himalayan black bears and one-horned rhinos in protected habitats.",
        "taste_pairing": "Rent a paddle boat on the central lake, then enjoy fresh sweet curd and local samosas from the lakeside garden kiosks.",
        "insider_secret": "The central lake was originally dug during the Rana period as a private royal reflection pond; historical pavilions still stand on the water's edge.",
        "etiquette_tip": "Do not feed animals from outside bags; keep to the shaded walking trails and respect peaceful family spaces.",
        "transit_tip": "Located at Jawalakhel Roundabout in Lalitpur; reachable in 15 minutes by taxi from central Kathmandu or 10 minutes from Patan Square.",
        "ideal_window": "10:00 AM – 1:30 PM (sunny garden hours)",
        "duration_hours": 2.5,
        "lat": 27.6718, "lng": 85.3132
    },
    "panauti_heritage_walk": {
        "what_to_do": "Explore this tranquil, untouched medieval Newari settlement at the confluence of the Punyamata and Roshi rivers. Marvel at Indreshwar Mahadev Temple—one of Nepal’s oldest surviving wooden pagodas (1294 AD) with masterfully carved wooden struts.",
        "taste_pairing": "Dine at a community homestay for warm organic dal bhat made with locally grown red rice and fresh farm greens.",
        "insider_secret": "Local lore says Panauti rests on a single massive rock slab, making it resilient against seismic tremors.",
        "etiquette_tip": "Respect community homestays by asking permission before photographing weavers at their wooden looms.",
        "transit_tip": "Take a 45-minute rural bus or private taxi via Banepa down the scenic Punyamata river valley.",
        "ideal_window": "10:00 AM – 2:00 PM (slow, contemplative village pace)",
        "duration_hours": 3.0,
        "lat": 27.5850, "lng": 85.5186
    }
,
    "phewa_lake_boating": {
        "what_to_do": "Board a painted wooden doonga at Lakeside pier. Paddle out to the mid-lake Tal Barahi Island Temple, ring the brass bell, and glide along the tranquil forested southern shoreline.",
        "taste_pairing": "Sample freshly grilled Phewa fish and hot momos with spicy tomato achar at a quiet waterfront garden cafe.",
        "insider_secret": "Row out between 6:30 AM and 8:00 AM before motorboats create ripples; the reflection of Mount Machhapuchhre is mirror-sharp.",
        "etiquette_tip": "Wear the provided life jacket at all times on the water; remove footwear before stepping onto the temple island sanctum.",
        "transit_tip": "Walk directly from your Lakeside hotel or take a 10-minute taxi from Pokhara Airport.",
        "ideal_window": "6:30 AM - 9:00 AM (mirror water) or 4:30 PM - 6:00 PM (amber sunset glow)",
        "duration_hours": 2.5,
        "lat": 28.2110, "lng": 83.9570
    },
    "world_peace_pagoda_pokhara": {
        "what_to_do": "Ascend the forested Anadu Hill ridge. Walk the circular white stupa terrace, taking in sweeping 360-degree views of Phewa Lake below and the snowy Annapurna skyline above.",
        "taste_pairing": "Enjoy fresh ginger lemon honey tea at the hilltop viewpoint cafe overlooking the lake.",
        "insider_secret": "Combine the visit with a 45-minute nature walk down through Raniban (Queen's Forest) directly to the lakeshore.",
        "etiquette_tip": "Maintain peaceful silence on the stupa platform; circumambulate clockwise and remove shoes at the boundary steps.",
        "transit_tip": "Take a boat across Phewa Lake and hike 45m up the stone trail, or take a 25-minute scenic taxi via the southern ridge road.",
        "ideal_window": "7:00 AM - 9:30 AM or 4:00 PM - 5:30 PM",
        "duration_hours": 3.0,
        "lat": 28.2008, "lng": 83.9458
    },
    "sarangkot_sunrise_viewpoint": {
        "what_to_do": "Arrive in the pre-dawn darkness at Sarangkot ridge (1,592m). Watch the morning sun ignite the peaks of Dhaulagiri, Annapurna, and Machhapuchhre in glowing gold, crimson, and amber.",
        "taste_pairing": "Sip hot spiced Himalayan tea from local hillside tea stalls as the first rays break across the horizon.",
        "insider_secret": "Walk 100 meters beyond the main viewing tower toward the old Sarangkot fort for uncrowded photography angles.",
        "etiquette_tip": "Dress in warm layers; morning ridge winds can be brisk even in spring.",
        "transit_tip": "Take a 30-minute early morning taxi from Lakeside (depart by 5:00 AM) or ride the Sarangkot cable car from Sedi.",
        "ideal_window": "5:15 AM - 7:30 AM (pre-dawn to golden sunrise)",
        "duration_hours": 2.5,
        "lat": 28.2439, "lng": 83.9485
    },
    "begnas_lake_retreat": {
        "what_to_do": "Relax on a wooden boat amidst quiet freshwater lotus pads, stroll along terraced hill orchards, and enjoy a slow, unhurried day away from the tourist buzz.",
        "taste_pairing": "Enjoy fresh grilled lake fish served with locally harvested organic salad and cold lemon soda.",
        "insider_secret": "Walk along the narrow ridge separating Begnas Lake and Rupa Lake for views of both tranquil waters simultaneously.",
        "etiquette_tip": "Greet local fishermen and boatmen with a warm 'Namaste'; support local family eateries.",
        "transit_tip": "Take a 30-minute taxi or local bus east from Pokhara to the Begnas bus terminal.",
        "ideal_window": "8:30 AM - 12:00 PM or 2:00 PM - 5:00 PM",
        "duration_hours": 3.0,
        "lat": 28.1750, "lng": 84.0950
    },
    "gupteshwor_cave_davis_fall": {
        "what_to_do": "Descend deep limestone stairways to an underground cave shrine, peering through rock crevices to watch the churning torrent of Davis Falls crash into the earth.",
        "taste_pairing": "Pick up fresh roasted corn cobs with lime and chili salt outside the cave entrance.",
        "insider_secret": "The deepest cavern chamber has an opening directly behind the subterranean waterfall pool.",
        "etiquette_tip": "Watch your step on damp, slippery limestone stairs; photography is restricted right at the inner Shiva lingam.",
        "transit_tip": "A quick 10-minute taxi south of Lakeside in the Chhorepatan district.",
        "ideal_window": "8:30 AM - 11:30 AM or 2:00 PM - 4:30 PM",
        "duration_hours": 2.0,
        "lat": 28.1887, "lng": 83.9583
    },
    "international_mountain_museum": {
        "what_to_do": "Walk through halls dedicated to the 14 peaks above 8,000m, legendary mountaineering expeditions, Yeti lore, and indigenous Himalayan cultural clothing.",
        "taste_pairing": "Enjoy light lunches and cappuccino at the garden restaurant overlooking the model climbing wall.",
        "insider_secret": "Do not miss the Japanese mountaineering wing showcasing vintage high-altitude gear from the 1950s.",
        "etiquette_tip": "Flash photography is prohibited in fragile textile and manuscript preservation rooms.",
        "transit_tip": "15-minute taxi from Lakeside across the Phusre river bridge to Rato Pahir.",
        "ideal_window": "9:30 AM - 1:00 PM",
        "duration_hours": 2.5,
        "lat": 28.1883, "lng": 83.9806
    },
    "poon_hill_ghorepani_trek": {
        "what_to_do": "Climb up to Poon Hill summit (3,210m) at dawn to witness a breathtaking panoramic view of the Annapurna and Dhaulagiri mountain ranges bathed in morning pink and gold.",
        "taste_pairing": "Hot porridge with local honey and ginger tea served in mountain teahouse dining rooms.",
        "insider_secret": "In April, the entire surrounding forest blooms with brilliant scarlet and pink rhododendron blossoms.",
        "etiquette_tip": "Stay on the stone paved trekking paths and pack out all wrappers and plastic bottles.",
        "transit_tip": "Accessed via Ghorepani village after trekking from Nayapul / Tikhedhunga.",
        "ideal_window": "5:00 AM - 7:30 AM",
        "duration_hours": 4.0,
        "lat": 28.3995, "lng": 83.6997
    },
    "annapurna_base_camp_sanctuary": {
        "what_to_do": "Stand at 4,130m in the heart of the Annapurna Sanctuary, surrounded by a 360-degree wall of towering snow peaks including Annapurna I, Machhapuchhre, and Hiunchuli.",
        "taste_pairing": "Hearty Tibetan sherpa stew (shakpa) and garlic soup for high-altitude acclimatization.",
        "insider_secret": "Dawn light on the south face of Annapurna I is considered one of the finest mountaineering panoramas on earth.",
        "etiquette_tip": "Keep voices low in the sanctuary; respect the sacred natural environment.",
        "transit_tip": "Reached via multi-day trekking route from Pokhara through Chomrong and Deurali.",
        "ideal_window": "5:30 AM - 9:00 AM (clearest morning skies)",
        "duration_hours": 5.0,
        "lat": 28.5300, "lng": 83.8780
    },
    "mardi_himal_ridge_trail": {
        "what_to_do": "Walk the high grassy ridge toward High Camp (3,580m), feeling close enough to touch the towering southern pyramid of Mount Machhapuchhre.",
        "taste_pairing": "Hot noodle soup with local yak cheese shavings in cozy alpine lodges.",
        "insider_secret": "The sunrise viewpoint at 4,200m provides an unobstructed look right down into the Modi Khola gorge.",
        "etiquette_tip": "Stay alert on narrow ridge sections; yield right of way to ascending trekkers.",
        "transit_tip": "Trailhead begins at Kande or Phedi, a 45-minute drive from Pokhara.",
        "ideal_window": "6:00 AM - 11:00 AM",
        "duration_hours": 4.5,
        "lat": 28.4500, "lng": 83.9200
    },
    "chitwan_jungle_safari": {
        "what_to_do": "Board an open-top 4WD safari jeep with a certified naturalist. Track one-horned rhinos through sal forests, cross open grasslands, and search riverbanks for wild tigers.",
        "taste_pairing": "Savor traditional Tharu ghonghi (freshwater snails) and spicy duck curry with beaten rice at an authentic Sauraha village hearth.",
        "insider_secret": "The shallow waterholes near Tamarind grasslands host solitary rhinos wallowing in mud around 8:00 AM.",
        "etiquette_tip": "Wear neutral earth tones (khaki, green, brown); avoid bright neon colors and stay seated inside the jeep at all times.",
        "transit_tip": "Jeeps depart directly from Sauraha tourist hub; park permits must be stamped at the national park entrance gate.",
        "ideal_window": "6:30 AM - 10:30 AM or 2:30 PM - 5:30 PM (peak wildlife activity)",
        "duration_hours": 4.0,
        "lat": 27.5813, "lng": 84.4988
    },
    "rapti_river_canoe_safari": {
        "what_to_do": "Drift quietly down the mist-veiled Rapti River in a carved wooden canoe, observing basking gharial crocodiles and rare kingfishers along the sandbanks.",
        "taste_pairing": "Fresh mint lemonade and samosas at the riverbank sunset view decks in Sauraha.",
        "insider_secret": "Early morning fog creates an ethereal primeval atmosphere as waterbirds swoop across the river.",
        "etiquette_tip": "Remain seated and keep your hands inside the canoe at all times while crocodiles bask on the banks.",
        "transit_tip": "Boarding docks are situated along the main Sauraha river promenade.",
        "ideal_window": "7:00 AM - 9:30 AM or 3:30 PM - 5:30 PM",
        "duration_hours": 2.0,
        "lat": 27.5750, "lng": 84.4900
    },
    "tharu_cultural_village_walk": {
        "what_to_do": "Visit traditional mud-and-thatch Tharu homes, explore agricultural tools and fish traps, and attend an evening stick dance performance full of rhythmic percussion.",
        "taste_pairing": "Crispy fried river fish and freshly made rice roti (chhyama).",
        "insider_secret": "Observe the hand-painted geometric animal motifs decorating the exterior clay walls of homesteads.",
        "etiquette_tip": "Always seek permission before stepping into private family courtyards.",
        "transit_tip": "Easily walked or cycled from central Sauraha.",
        "ideal_window": "4:00 PM - 7:30 PM",
        "duration_hours": 2.5,
        "lat": 27.5850, "lng": 84.5020
    },
    "bardia_tiger_tracking_safari": {
        "what_to_do": "Embark on an exhilarating walking safari with experienced trackers through the undisturbed sal forests of Bardia to find Royal Bengal tigers and Asian elephants.",
        "taste_pairing": "Home-cooked Tharu dal bhat with wild greens and roasted mustard seed chutney.",
        "insider_secret": "The Machan watchtowers overlooking waterholes near the Kingfisher Bridge offer the highest probability of spotting tigers at dawn.",
        "etiquette_tip": "Follow your guide's hand signals strictly; silence is essential during walking safaris.",
        "transit_tip": "Fly to Nepalgunj from Kathmandu, followed by a 2-hour drive west to Thakurdwara.",
        "ideal_window": "6:00 AM - 11:00 AM and 3:00 PM - 6:00 PM",
        "duration_hours": 5.0,
        "lat": 28.4735, "lng": 81.3414
    },
    "suklaphanta_grassland_safari": {
        "what_to_do": "Cross the immense open grassland of Suklaphanta to see thousands of golden swamp deer running in herds against a backdrop of distant hills.",
        "taste_pairing": "Warm local flatbreads and lentils served at community homestays in Kanchanpur.",
        "insider_secret": "The Rani Tal lake inside the reserve is a haven for migratory ducks and storks.",
        "etiquette_tip": "Stay inside vehicles on the wide grasslands where tall grasses reduce visibility.",
        "transit_tip": "Access from Mahendranagar / Dhangadhi airport in the far-west.",
        "ideal_window": "6:30 AM - 10:30 AM",
        "duration_hours": 4.0,
        "lat": 28.8450, "lng": 80.2450
    },
    "muktinath_temple_108_spouts": {
        "what_to_do": "Ascend to the sacred high-altitude pilgrimage sanctuary (3,710m). Bathe beneath the 108 icy bronze waterspouts and witness the eternal flame burning beside water.",
        "taste_pairing": "Warm up with steaming Mustang seabuckthorn juice and Tibetan yak stew at Ranipauwa.",
        "insider_secret": "Notice the sacred Shaligram ammonite fossils preserved in the riverbeds, revered as embodiments of Lord Vishnu.",
        "etiquette_tip": "Dress warmly and respectfully; ringing the temple bell once when entering is customary.",
        "transit_tip": "Accessible by 4WD jeep or flight from Pokhara to Jomsom followed by a 1.5h scenic high-mountain drive.",
        "ideal_window": "7:00 AM - 11:30 AM (clear morning visibility before valley winds rise)",
        "duration_hours": 3.0,
        "lat": 28.8166, "lng": 83.8711
    },
    "lo_manthang_walled_city": {
        "what_to_do": "Enter through the grand gate of the 14th-century walled kingdom of Upper Mustang. Explore the 4-story King's Palace and ancient gompas containing priceless gold-leaf murals.",
        "taste_pairing": "Tibetan salted butter tea (suja) with roasted barley flour (tsampa).",
        "insider_secret": "Take a short pony ride to the Chhoser sky caves, carved 5 stories high into honeycombed sandstone cliffs.",
        "etiquette_tip": "A restricted area permit is required; always walk clockwise around village chortens.",
        "transit_tip": "4WD jeep track from Jomsom via Kagbeni and Charang through dramatic desert canyons.",
        "ideal_window": "8:30 AM - 4:30 PM",
        "duration_hours": 4.5,
        "lat": 29.1824, "lng": 83.9566
    },
    "marpha_apple_village_walk": {
        "what_to_do": "Walk the cobblestone lanes of Marpha past gleaming whitewashed stone houses with flat mud roofs, timber firewood stacks, and fragrant apple cider distilleries.",
        "taste_pairing": "Fresh-baked apple strudel, dried apple rings, and Marpha apple brandy.",
        "insider_secret": "Climb up to the Marpha Buddhist Gompa perched on the cliff above town for views over the entire valley floor.",
        "etiquette_tip": "Respect local courtyards where apples and grains are laid out to dry in the sun.",
        "transit_tip": "Located on the Kali Gandaki highway, a 20-minute drive south of Jomsom.",
        "ideal_window": "9:00 AM - 4:00 PM",
        "duration_hours": 2.5,
        "lat": 28.7525, "lng": 83.6872
    },
    "kagbeni_monastery_gateway": {
        "what_to_do": "Explore the medieval alleyways of Kagbeni where the Kali Gandaki meets the Mustang Khola. Visit the 600-year-old red Sakya monastery and the ancient clay ghost-catcher statues.",
        "taste_pairing": "Fresh yak burger or warm buckwheat pancakes with wild honey at local cafes.",
        "insider_secret": "The northern checkpoint marks the boundary into the restricted Upper Mustang kingdom.",
        "etiquette_tip": "Remove shoes and hats when entering the monastery prayer hall.",
        "transit_tip": "40-minute drive north from Jomsom along the riverbed.",
        "ideal_window": "8:00 AM - 3:00 PM",
        "duration_hours": 2.5,
        "lat": 28.8350, "lng": 83.7820
    },
    "maya_devi_temple_lumbini": {
        "what_to_do": "Enter the serene Sacred Garden at Lumbini. Walk through the ancient brick sanctum housing the nativity marker stone, touch the sandstone Ashokan pillar erected in 249 BC, and meditate beside the sacred pond.",
        "taste_pairing": "Sip fresh coconut water and local Terai peda sweets outside the Sacred Garden gate.",
        "insider_secret": "Visit the Maya Devi pond at 6:30 AM to watch monks in saffron and maroon robes begin silent walking meditation in the mist.",
        "etiquette_tip": "Remove shoes before walking the elevated wooden boardwalk inside the ancient temple ruins; maintain quiet reverence.",
        "transit_tip": "Take an electric rickshaw or bicycle from Lumbini Bazaar; smooth paved paths connect all monument zones.",
        "ideal_window": "6:00 AM - 9:00 AM or 4:30 PM - 6:30 PM (peaceful spiritual atmosphere)",
        "duration_hours": 2.5,
        "lat": 27.4839, "lng": 83.2760
    },
    "lumbini_monastic_zone_walk": {
        "what_to_do": "Cycle or ride an electric rickshaw along the central peace canal, visiting striking international monasteries built by Thailand, Germany, Japan, Sri Lanka, and Cambodia.",
        "taste_pairing": "Fresh fruit smoothies and light vegetarian noodles in the garden cafes near the World Peace Flame.",
        "insider_secret": "The Japanese Peace Stupa at the northern end offers a quiet park with resident sarus cranes.",
        "etiquette_tip": "Dress respectfully covering shoulders and knees; remove footwear when entering temple shrines.",
        "transit_tip": "Rent a bicycle at the main gate to easily explore the 3-mile long monastic zone.",
        "ideal_window": "8:30 AM - 4:30 PM",
        "duration_hours": 3.5,
        "lat": 27.4900, "lng": 83.2750
    },
    "tilaurakot_ancient_kapilavastu": {
        "what_to_do": "Walk across the ancient brick foundations, royal gateways, and moat of ancient Kapilavastu, where Prince Siddhartha lived his first 29 years before embarking on his spiritual path.",
        "taste_pairing": "Enjoy spiced chai and fresh samosas at the quiet country tea stall near the eastern gate.",
        "insider_secret": "The tranquil forest surrounding the archaeological excavations is filled with chirping songbirds and ancient banyan trees.",
        "etiquette_tip": "Do not climb or sit on ancient excavated brick foundations.",
        "transit_tip": "Located 27 km west of Lumbini; an easy 45-minute taxi or rickshaw drive.",
        "ideal_window": "8:00 AM - 11:30 AM or 3:00 PM - 5:30 PM",
        "duration_hours": 2.5,
        "lat": 27.5744, "lng": 83.0569
    },
    "namche_bazaar_sherpa_hub": {
        "what_to_do": "Stroll through the horseshoe-shaped amphitheater of Namche (3,440m). Visit the Sherpa Culture Museum, browse handmade woolens, and climb to the Everest View Hotel ridge for an unforgettable sight of Everest.",
        "taste_pairing": "Enjoy fresh apple pie, yak cheese sandwiches, and rich hot chocolate at the world's highest bakeries.",
        "insider_secret": "The Saturday morning market brings local Sherpa farmers and Tibetan traders together selling crafts and fresh produce.",
        "etiquette_tip": "Always circumambulate mani stones and chortens clockwise; acclimatize steadily and stay hydrated.",
        "transit_tip": "Trek 6 hours uphill from Phakding crossing suspension bridges over the turquoise Dudh Koshi river.",
        "ideal_window": "8:00 AM - 4:00 PM",
        "duration_hours": 4.0,
        "lat": 27.8069, "lng": 86.7140
    },
    "tengboche_monastery_view": {
        "what_to_do": "Visit the principal Buddhist center of the Khumbu Sherpas (3,867m), framed dramatically by the soaring peak of Mount Ama Dablam. Attend the afternoon monk chanting ceremony.",
        "taste_pairing": "Warm Tibetan butter tea and sweet biscuits with trekkers in the monastery lodge.",
        "insider_secret": "The Mani Rimdu festival in autumn features sacred masked dances depicting the triumph of Buddhism over dark forces.",
        "etiquette_tip": "Remain quietly seated against the wall during monk ceremonies; turn off mobile phones.",
        "transit_tip": "A 4 to 5 hour trek up through rhododendron and pine forests from Namche Bazaar.",
        "ideal_window": "6:00 AM - 8:30 AM or 3:00 PM - 4:30 PM",
        "duration_hours": 3.0,
        "lat": 27.8358, "lng": 86.7644
    },
    "everest_base_camp_trek": {
        "what_to_do": "Trek to the base of the world's highest peak (5,364m), standing beside fluttering prayer flags on the Khumbu Glacier with the treacherous icefall towering just ahead.",
        "taste_pairing": "Steaming garlic soup and hearty dhal bhat at Gorakshep teahouses before the final moraine push.",
        "insider_secret": "Listen closely to hear the deep, echoing creaks of the moving Khumbu glacier beneath the moraine rocks.",
        "etiquette_tip": "Do not enter active mountaineering team tents without a formal invitation from expedition leaders.",
        "transit_tip": "Hike from Gorakshep along the rocky lateral moraine of the Khumbu glacier.",
        "ideal_window": "7:00 AM - 1:00 PM",
        "duration_hours": 6.0,
        "lat": 28.0044, "lng": 86.8528
    },
    "kala_patthar_everest_sunrise": {
        "what_to_do": "Ascend the rocky landmark of Kala Patthar (5,644m) to view Mount Everest, Lhotse, and Nuptse in close-up glory as morning sunbeams strike the summit pyramid.",
        "taste_pairing": "Sip hot ginger tea from a thermos flask at the windy summit prayer flag pole.",
        "insider_secret": "Kala Patthar offers a much more complete and towering view of Everest than Base Camp itself.",
        "etiquette_tip": "Dress in your warmest down gear; temperatures before sunrise can plummet well below freezing.",
        "transit_tip": "A 2 to 3 hour steep rocky ascent starting early morning from Gorakshep.",
        "ideal_window": "5:30 AM - 8:30 AM",
        "duration_hours": 3.5,
        "lat": 27.9950, "lng": 86.8280
    },
    "gokyo_lakes_and_ri": {
        "what_to_do": "Admire the radiant turquoise color of the sacred Gokyo Lakes (4,750m) and climb Gokyo Ri for a panorama revealing Cho Oyu, Everest, Lhotse, and Makalu.",
        "taste_pairing": "Fresh yak cheese omelette and hot lemon tea in cozy lakeside lodges.",
        "insider_secret": "The 4th and 5th lakes further up the Ngozumpa glacier offer completely deserted alpine solitude.",
        "etiquette_tip": "The lakes are sacred to both Hindus and Buddhists; swimming and bathing are strictly prohibited.",
        "transit_tip": "Accessed via the scenic Gokyo Valley trek branching north from Dole and Machhermo.",
        "ideal_window": "6:00 AM - 11:30 AM",
        "duration_hours": 5.0,
        "lat": 27.9530, "lng": 86.6830
    },
    "kyanjin_gompa_cheese_factory": {
        "what_to_do": "Visit the peaceful monastery in Langtang Valley (3,870m) and tour the local cooperative producing Swiss-standard mountain yak cheese with fresh mountain pasture milk.",
        "taste_pairing": "Sample thick slices of fresh-cut salty yak cheese and hot black tea.",
        "insider_secret": "Hike up to Kyanjin Ri (4,773m) directly behind the village for dramatic views of the Langtang Lirung icefall.",
        "etiquette_tip": "Circumambulate the gompa clockwise; support the local cooperative by buying cheese directly.",
        "transit_tip": "Trek up the Langtang valley from Syabrubesi through Lama Hotel and Langtang village.",
        "ideal_window": "8:00 AM - 3:00 PM",
        "duration_hours": 3.0,
        "lat": 28.2100, "lng": 85.5680
    },
    "gosaikunda_sacred_alpine_lakes": {
        "what_to_do": "Circumambulate the sacred alpine waters of Gosaikunda (4,380m), surrounded by dramatic rocky cliffs and fluttering lungta prayer flags.",
        "taste_pairing": "Warm Tibetan noodle soup (thukpa) and lemon tea at lakeside teahouse lodges.",
        "insider_secret": "During August Janai Purnima, thousands of pilgrims trek here to take a holy dip in the icy glacial waters.",
        "etiquette_tip": "Maintain the sanctity of this revered pilgrimage site; pack out all garbage.",
        "transit_tip": "Trek from Dhunche or via Lauribina Pass from Helambu.",
        "ideal_window": "7:00 AM - 1:00 PM",
        "duration_hours": 4.0,
        "lat": 28.0833, "lng": 85.4167
    },
    "bandipur_medieval_hill_town": {
        "what_to_do": "Walk along the pedestrian slate-paved bazaar lined with 18th-century Newari wooden townhouses. Hike up to Thani Mai temple for a 360-degree panorama of the Marsyangdi valley.",
        "taste_pairing": "Taste authentic local sel roti, aloo tama curry, and fresh hill buffalo curd served in clay bowls.",
        "insider_secret": "Sunrise at Thani Mai Temple (30m stone step climb) features an ethereal sea of white clouds filling the valleys below.",
        "etiquette_tip": "Vehicles are completely banned in the central bazaar; enjoy the peaceful pedestrian rhythm.",
        "transit_tip": "Take a 20-minute winding mountain road from Dumre on the Prithvi Highway.",
        "ideal_window": "8:00 AM - 11:30 AM or 4:00 PM - 7:30 PM",
        "duration_hours": 3.0,
        "lat": 27.9304, "lng": 84.4172
    },
    "gorkha_historic_durbar": {
        "what_to_do": "Climb stone steps up the fortified hilltop palace where King Prithvi Narayan Shah was born, exploring ancient armories and the sacred shrine of Gorakhnath.",
        "taste_pairing": "Enjoy local roasted beaten rice and spicy dried meat (sukuti) at the hilltop viewpoint stalls.",
        "insider_secret": "The sacred cave of sage Gorakhnath is tucked directly beneath the palace foundations.",
        "etiquette_tip": "Leather items (belts, wallets) must be removed before entering the inner temple shrine.",
        "transit_tip": "A 25-minute drive from Gorkha town up to the palace base, followed by a stone staircase climb.",
        "ideal_window": "7:30 AM - 11:00 AM or 3:00 PM - 5:30 PM",
        "duration_hours": 3.0,
        "lat": 28.0050, "lng": 84.6280
    },
    "rani_mahal_palpa": {
        "what_to_do": "Visit the neoclassical riverside palace built in 1893 on a dramatic rock cliff above the blue waters of the Kali Gandaki, often hailed as the Taj Mahal of Nepal.",
        "taste_pairing": "Fresh seasonal oranges and local ginger candy on the riverbank overlook.",
        "insider_secret": "The suspension footbridge across the river provides the most majestic vantage point of the palace facade.",
        "etiquette_tip": "Take care near the steep riverside cliffs; footwear must be removed inside the restored palace halls.",
        "transit_tip": "Take a 45-minute 4WD jeep drive north from Tansen down to the river gorge.",
        "ideal_window": "9:00 AM - 3:30 PM",
        "duration_hours": 3.0,
        "lat": 27.9272, "lng": 83.5284
    },
    "tansen_dhaka_and_shrinagar": {
        "what_to_do": "Walk the historic cobblestone alleys of Tansen, visit traditional Dhaka cloth weavers at their manual looms, and hike up Shrinagar Hill for views of the plains and peaks.",
        "taste_pairing": "Palpali chukauni (spiced yogurt potato curry) and batuk (crispy lentil patties).",
        "insider_secret": "Watch master weavers create geometric Dhaka patterns entirely from memory without written stencils.",
        "etiquette_tip": "Always ask courteously before taking close-up photographs of weavers at work.",
        "transit_tip": "Scenic hill drive off the Siddhartha Highway between Butwal and Pokhara.",
        "ideal_window": "8:30 AM - 4:00 PM",
        "duration_hours": 3.0,
        "lat": 27.8673, "lng": 83.5463
    },
    "rara_lake_national_park": {
        "what_to_do": "Walk or horse-ride the pristine 13km trail encircling Nepal's largest alpine lake (2,990m). Row across the deep blue waters reflecting the snow peaks of Chuchemara Danda.",
        "taste_pairing": "Warm up by a wood fire with hot Jumli red rice, local mountain bean soup (maseura), and nettle leaf tea.",
        "insider_secret": "Hike up to Murma Top (3,690m) for an extraordinary bird's-eye perspective of the entire turquoise expanse.",
        "etiquette_tip": "Pack out all waste; Rara is an ecologically sensitive national park with zero commercial pollution.",
        "transit_tip": "Fly from Nepalgunj to Talcha Airport in Mugu, followed by a 2.5h scenic pine forest hike to the lakeshore.",
        "ideal_window": "7:00 AM - 3:30 PM",
        "duration_hours": 4.5,
        "lat": 29.5333, "lng": 82.0833
    },
    "shey_phoksundo_deep_blue_lake": {
        "what_to_do": "Marvel at the unreal turquoise waters of Nepal's deepest lake (3,611m), explore the ancient Ringmo Bon Po village, and view the roaring 167m waterfall.",
        "taste_pairing": "Buckwheat porridge and salted yak butter tea in local Ringmo community houses.",
        "insider_secret": "The lake is famous for having no aquatic life, giving it crystal clarity and intense aquamarine colors.",
        "etiquette_tip": "Circumambulate Bon chortens anti-clockwise, adhering to Bon religious tradition.",
        "transit_tip": "Fly to Juphal in Dolpo, followed by a multi-day trek through Suligad gorge.",
        "ideal_window": "8:00 AM - 3:00 PM",
        "duration_hours": 4.5,
        "lat": 29.2133, "lng": 82.9511
    },
    "khaptad_national_park_meadows": {
        "what_to_do": "Trek through 22 rolling green alpine meadows (patans), pristine oak forests, and visit the serene hermitage where the revered ascetic Khaptad Baba meditated.",
        "taste_pairing": "Organic mountain honey and roasted corn at the park ranger post.",
        "insider_secret": "In June, the meadows are carpeted with wild primulas, gentians, and medicinal mountain herbs.",
        "etiquette_tip": "Smoking, alcohol, and killing animals are strictly prohibited within the sacred park sanctuary.",
        "transit_tip": "Accessible via Silgadhi (Doti) or Bajhang in far-western Nepal.",
        "ideal_window": "7:30 AM - 3:30 PM",
        "duration_hours": 4.5,
        "lat": 29.3800, "lng": 81.1500
    },
    "kanyam_tea_gardens_ilam": {
        "what_to_do": "Wander through rolling emerald tea bushes on mist-shrouded hillsides, ride gentle mountain ponies, and tour an artisanal orthodox tea factory.",
        "taste_pairing": "Sip first-flush golden tips orthodox black tea alongside local churpi and Ilam lollipop candy.",
        "insider_secret": "Visit the old tea factory at Fikkal to purchase vacuum-sealed Muscatel tea directly from the tea masters.",
        "etiquette_tip": "Do not pluck green tea leaves without permission from the garden supervisor.",
        "transit_tip": "Accessible via Mechi Highway, roughly 2.5 hours by taxi from Bhadrapur Airport.",
        "ideal_window": "8:00 AM - 3:30 PM",
        "duration_hours": 3.0,
        "lat": 26.9115, "lng": 87.9274
    },
    "sri_antu_kanchenjunga_sunrise": {
        "what_to_do": "Ascend to the easternmost crest of Sri Antu (1,823m) at daybreak to watch the first golden rays illuminate tea gardens with Mount Kanchenjunga in the background.",
        "taste_pairing": "Fresh organic cow milk tea and local cardamoms at roadside tea stalls.",
        "insider_secret": "Antu Pokhari (lake) in the center of the village is peaceful for an afternoon pedal-boat ride.",
        "etiquette_tip": "Stay in warm home-stays and support local tea-growing families.",
        "transit_tip": "Roughly 1.5 hours drive east of Ilam bazaar along scenic ridge roads.",
        "ideal_window": "5:00 AM - 7:30 AM",
        "duration_hours": 2.5,
        "lat": 26.9050, "lng": 88.0850
    },
    "janaki_mandir_janakpur": {
        "what_to_do": "Admire the 3-story marble palace temple dedicated to Sita, blending Mughal and Rajput architecture, and attend the evening Ganga Sagar aarti with lit oil lamps.",
        "taste_pairing": "Janakpur lassi topped with thick malai, rabri, and warm mithila kachoris.",
        "insider_secret": "The temple museum houses ancient musical instruments, palanquins, and historic royal gifts.",
        "etiquette_tip": "Remove footwear at the marble entrance; photography inside the inner shrine is prohibited.",
        "transit_tip": "Located in the heart of Janakpurdham, 15 minutes by electric rickshaw from the airport.",
        "ideal_window": "6:30 AM - 11:30 AM or 4:30 PM - 8:00 PM",
        "duration_hours": 2.5,
        "lat": 26.7271, "lng": 85.9246
    },
    "vivaha_mandap_mithila_art": {
        "what_to_do": "Visit the wedding pavilion commemorating the marriage of Rama and Sita, and tour local cultural centers to observe women creating traditional Mithila paintings.",
        "taste_pairing": "Try local traditional sweets like thekua and makhana kheer (lotus seed pudding).",
        "insider_secret": "Local artists will explain the symbolic meaning of fish, peacocks, and lotuses in Mithila art.",
        "etiquette_tip": "Buy paintings directly from women artists' collectives to support fair-trade community preservation.",
        "transit_tip": "Just north of Janaki Mandir, an easy 5-minute walk.",
        "ideal_window": "8:30 AM - 4:30 PM",
        "duration_hours": 2.0,
        "lat": 26.7290, "lng": 85.9260
    },
    "pathibhara_devi_taplejung": {
        "what_to_do": "Trek up through rhododendron and bamboo cloud forests to the holy mountain shrine (3,794m) for divine blessings with vistas of Mount Kanchenjunga.",
        "taste_pairing": "Hot mountain tea and fresh roasted corn at Suketar teahouse stops.",
        "insider_secret": "The ringing of thousands of brass bells offered by pilgrims creates a mesmerizing spiritual resonance.",
        "etiquette_tip": "Dress warmly and respectfully; pilgrims usually climb barefoot the final meters to the shrine.",
        "transit_tip": "Fly to Suketar airport or drive from Birtamod/Ilam, followed by a mountain trail climb.",
        "ideal_window": "6:00 AM - 11:30 AM",
        "duration_hours": 4.0,
        "lat": 27.4250, "lng": 87.7700
    }
}

DEFAULT_ACTION_GUIDE = {
    "what_to_do": "Arrive at sunrise to observe morning rituals. Walk clockwise through the courtyard, listening to the soft resonance of prayer bells, observing timber carvings, and greeting local caretakers.",
    "taste_pairing": "Settle at an open-air neighborhood tea shop for hot cardamom spiced milk tea and crisp golden sel roti.",
    "insider_secret": "Look closely at the carved stone chaityas and wooden window brackets tucked away from the main thoroughfare.",
    "etiquette_tip": "Always circumambulate sacred shrines in a clockwise direction; ask courteously before photographing local devotees.",
    "transit_tip": "Walk through pedestrian bahals or take an electric taxi outside peak rush hour (avoid 9:00 AM and 5:00 PM).",
    "ideal_window": "Morning hours (7:30 AM – 10:00 AM) or gentle Golden Hour (4:30 PM – 6:00 PM)",
    "duration_hours": 2.0,
    "lat": 27.7172, "lng": 85.3240
}


def get_action_guidance_for_activity(activity_id: str) -> Dict[str, Any]:
    """Return concrete, sensorial action guidance for an activity or festival."""
    norm_id = (activity_id or "").lower().replace("-", "_")
    for key, guide in ACTION_GUIDES.items():
        if key in norm_id or norm_id in key:
            return guide
    return DEFAULT_ACTION_GUIDE


def calculate_transit_between_stops(lat1: float, lng1: float, lat2: float, lng2: float) -> str:
    """Estimate transit method and time between two geographic coordinates in Kathmandu."""
    try:
        dist_km = haversine_distance_km(lat1, lng1, lat2, lng2) or 2.0
    except Exception:
        dist_km = 2.0

    if dist_km < 0.6:
        mins = max(5, int(dist_km * 16))
        return f"{mins}m alley walk"
    elif dist_km < 1.4:
        mins = max(8, int(dist_km * 14))
        return f"{mins}m walk"
    elif dist_km < 6.0:
        mins = max(12, int(dist_km * 3.5))
        return f"{mins}m cab"
    elif dist_km < 35.0:
        mins = max(25, int(dist_km * 2.5))
        return f"{mins}m scenic drive"
    elif dist_km < 120.0:
        hrs = round(dist_km / 35.0, 1)
        return f"{hrs}h mountain highway"
    else:
        hrs = round(dist_km / 50.0, 1)
        return f"{hrs}h highway / flight transfer"


def build_dna_pills(plan: Dict[str, Any], vibe: Dict[str, Any]) -> List[Dict[str, str]]:
    """Generate 4-5 diagnostic personality tags derived from the user's quiz answers."""
    profile = plan.get("profile", {})
    slot = plan.get("preferred_slot", "morning")
    budget = plan.get("budget_level", 2)
    pills = []

    # 1. Pace
    energy = profile.get("energy", 2.5)
    if energy <= 2.2:
        pills.append({"icon": "🚶", "label": "Pace", "val": "Contemplative & Slow"})
    elif energy >= 3.5:
        pills.append({"icon": "⚡", "label": "Pace", "val": "High Energy & Active"})
    else:
        pills.append({"icon": "🚶", "label": "Pace", "val": "Balanced Explorer"})

    # 2. Focus
    traits_map = [
        ("food", profile.get("food", 2.5), "🥟", "Focus", "Newari Flavors"),
        ("spiritual", profile.get("spiritual", 2.5), "🕉️", "Focus", "Sacred Monasteries"),
        ("culture", profile.get("culture", 2.5), "🏛️", "Focus", "Medieval Architecture"),
        ("nature", profile.get("nature", 2.5), "🌲", "Focus", "Alpine Ridges & Forests"),
        ("adventure", profile.get("adventure", 2.5), "🧗", "Focus", "High Trails & Active"),
    ]
    traits_map.sort(key=lambda x: x[1], reverse=True)
    top_focus = traits_map[0]
    pills.append({"icon": top_focus[2], "label": top_focus[3], "val": top_focus[4]})

    # 3. Atmosphere / Vibe
    crowd = float(profile.get("crowd", 2.5))
    if crowd <= 2.2:
        pills.append({"icon": "🏮", "label": "Vibe", "val": "Quiet Sanctuaries & Courtyards"})
    elif crowd >= 3.5:
        pills.append({"icon": "🏮", "label": "Vibe", "val": "Living Medieval Bazaars"})
    else:
        pills.append({"icon": "🏮", "label": "Vibe", "val": "Tranquil Heritage Lanes"})

    # 4. Window
    if slot == "morning":
        pills.append({"icon": "☀️", "label": "Window", "val": "Dawn-to-Dusk (6 AM Start)"})
    elif slot == "evening":
        pills.append({"icon": "🌙", "label": "Window", "val": "Golden Dusk & Aarti"})
    else:
        pills.append({"icon": "☀️", "label": "Window", "val": "Midday Sun & Artisan Lanes"})

    # 5. Style / Budget
    if budget == 1:
        pills.append({"icon": "🍵", "label": "Style", "val": "Grassroots Local Living"})
    elif budget == 3:
        pills.append({"icon": "✨", "label": "Style", "val": "Curated Heritage Comfort"})
    else:
        pills.append({"icon": "🍵", "label": "Style", "val": "Authentic Valley Rhythm"})

    return pills


def personalize_itinerary_with_gemini(
    plan: Dict[str, Any],
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """Personalize an itinerary using active free-tier Gemini models (gemini-3.5-flash with fallback).
    
    Batches the entire itinerary into a single structured JSON request.
    If offline or API fails, uses rich deterministic trait-aware fallback.
    """
    key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

    # Resolve vibe dict safely
    vibe_val = plan.get("vibe") or plan.get("vibe_id")
    if isinstance(vibe_val, dict):
        vibe = vibe_val
    elif isinstance(vibe_val, str):
        from engine.vibes import get_vibe_by_id
        vibe = get_vibe_by_id(vibe_val)
    else:
        vibe = None

    if not vibe or not isinstance(vibe, dict):
        vibe = {"name": "Valley Explorer", "tagline": "Discovering Kathmandu"}

    if key:
        try:
            ai_result = _call_gemini_per_stop_synthesis(key, plan, vibe)
            if ai_result:
                _apply_gemini_personalization_to_plan(plan, ai_result)
                return plan
        except Exception as e:
            logger.warning(f"Gemini per-stop synthesis failed, applying offline trait-aware personalization: {e}")

    # Fallback to rich deterministic trait-aware personalization
    _apply_offline_deterministic_personalization(plan, vibe)
    return plan


def _call_gemini_per_stop_synthesis(
    api_key: str,
    plan: Dict[str, Any],
    vibe: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Batched call to Google Gemini free-tier models returning pure structured JSON."""
    profile = plan.get("profile", {})
    dominant_traits = sorted(
        [t for t in ["energy", "crowd", "culture", "nature", "food", "spiritual", "adventure"] if t in profile],
        key=lambda x: profile.get(x, 2.5),
        reverse=True
    )[:3]

    stops_list = []
    for d in plan.get("days", []):
        day_num = d.get("day", 1)
        for slot_name, slot_data in d.get("slots", {}).items():
            if isinstance(slot_data, dict) and slot_data.get("name"):
                stops_list.append({
                    "stop_id": slot_data.get("activity_id") or slot_data.get("festival_id") or slot_data.get("id"),
                    "name": slot_data.get("name"),
                    "day": day_num,
                    "slot": slot_name,
                    "location": slot_data.get("location", "Kathmandu Valley"),
                    "category": slot_data.get("category", "")
                })

    stops_list = stops_list[:9]  # Cap to first 9 stops (3 days) for snappy sub-3s AI synthesis
    active_festival = plan.get("festival_highlights", [{}])[0].get("name", "None") if plan.get("festival_highlights") else "None"

    prompt = f"""You are a master Nepali travel chronicler, anthropologist, and local guide in the Kathmandu Valley.
Synthesize an authentic, hyper-personalized, and evocative field dossier for this traveler.

TRAVELER PROFILE:
- Persona Archetype: {vibe.get('name')} ("{vibe.get('tagline')}")
- 7D Trait Scores: {json.dumps({k: profile.get(k, 2.5) for k in ['energy', 'crowd', 'culture', 'nature', 'food', 'spiritual', 'adventure']})}
- Dominant Traits: {', '.join(dominant_traits)}
- Preferred Visiting Time: {plan.get('preferred_slot', 'morning')}
- Budget Level: {plan.get('budget_level', 2)} of 3
- Active Lunar Festival: {active_festival}

SCHEDULED STOPS:
{json.dumps(stops_list, indent=2)}

INSTRUCTIONS:
Return pure valid JSON matching this schema exactly:
{{
  "bespoke_headline": "string (A poetic, tailored 1-sentence editorial subtitle for this traveler)",
  "philosophy_of_journey": "string (Why this route specifically matches their 7D vector and dominant traits)",
  "local_rhythm_advice": "string (Concrete sensory advice on pacing, walking, and greeting tailored to energy & crowd comfort)",
  "golden_rule": "string (1 memorable, poetic cultural or practical rule for their trip)",
  "stops": [
    {{
      "stop_id": "string (exact stop_id matching the scheduled stops list)",
      "why_for_you": "string (1 sentence explaining why this specific place fits their quiz traits)",
      "first_30_min": "string (Bespoke first 30-minute directive calibrated to their pace and energy)",
      "taste_and_sit": "string (Specific Newari/Nepali food, tea pairing, or seating spot matching their vibe)",
      "insider_secret": "string (A hidden architectural, ritual, historical, or craft detail aligned with their interests)"
    }}
  ]
}}
Do NOT wrap the output in markdown fences (no ```json). Keep the tone poetic, warm, refined, and distinctively Nepali."""

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.7,
            "responseMimeType": "application/json"
        }
    }
    encoded_data = json.dumps(payload).encode("utf-8")

    # Strictly Active Free-Tier Flash Models: Primary, alternative primary, and rate-limit fallback
    free_tier_models = [
        "gemini-3.5-flash-lite",   # Fast, responsive free-tier flash-lite
        "gemini-3.5-flash",        # Primary active free-tier flash
    ]

    for model in free_tier_models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        req = urllib.request.Request(
            url,
            data=encoded_data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                result_json = json.loads(response.read().decode("utf-8"))
                text_content = result_json["candidates"][0]["content"]["parts"][0]["text"].strip()
                if text_content.startswith("```"):
                    lines = text_content.splitlines()
                    text_content = "\n".join(lines[1:-1] if lines[-1].startswith("```") else lines[1:])
                parsed = json.loads(text_content)
                parsed["is_ai_generated"] = True
                parsed["model_used"] = model
                return parsed
        except urllib.error.HTTPError as e:
            logger.warning(f"Free-tier model {model} returned HTTP {e.code}: {e.reason}")
            # Try next free-tier flash model on 429, 404, or 503
            continue
        except Exception as e:
            logger.warning(f"Free-tier model {model} error: {e}")
            continue

    return None


def _apply_gemini_personalization_to_plan(plan: Dict[str, Any], ai_result: Dict[str, Any]) -> None:
    """Merge Gemini AI-generated narrative and per-stop directives into plan dictionary."""
    plan["ai_narrative"] = ai_result
    
    # Update top-level personalized narrative
    plan["personalized_narrative"] = {
        "bespoke_headline": ai_result.get("bespoke_headline", ""),
        "philosophy_of_journey": ai_result.get("philosophy_of_journey", ""),
        "journey_philosophy": ai_result.get("philosophy_of_journey", ""),
        "local_rhythm_advice": ai_result.get("local_rhythm_advice", ""),
        "golden_rule": ai_result.get("golden_rule", ""),
        "is_ai_generated": True,
        "gemini_powered": True,
        "model_used": ai_result.get("model_used", "gemini-3.5-flash")
    }

    # Map stop customizations
    stops_by_id = {s.get("stop_id"): s for s in ai_result.get("stops", []) if s.get("stop_id")}
    
    for d in plan.get("days", []):
        for slot_name, slot in d.get("slots", {}).items():
            if not isinstance(slot, dict):
                continue
            s_id = slot.get("activity_id") or slot.get("festival_id") or slot.get("id")
            custom = stops_by_id.get(s_id)
            if custom:
                if custom.get("why_for_you"):
                    slot["why_for_you"] = custom["why_for_you"]
                if custom.get("first_30_min"):
                    slot["first_30_min"] = custom["first_30_min"]
                    slot["ai_pacing_directive"] = custom["first_30_min"]
                    # Preserve hand-curated what_to_do and reason (do not overwrite with first_30_min)
                if custom.get("taste_and_sit"):
                    slot["taste_and_sit"] = custom["taste_and_sit"]
                    slot["taste_pairing"] = custom["taste_and_sit"]
                if custom.get("insider_secret"):
                    slot["insider_secret"] = custom["insider_secret"]


def _apply_offline_deterministic_personalization(plan: Dict[str, Any], vibe: Dict[str, Any]) -> None:
    """Construct an authentic, non-generic personalized narrative without API key.
    
    Dynamically tailors every stop's why_for_you and prepends calibrated pacing directives.
    """
    profile = plan.get("profile", {})
    energy = profile.get("energy", 2.5)
    crowd = profile.get("crowd", 2.5)
    spiritual = profile.get("spiritual", 2.5)
    food = profile.get("food", 2.5)
    culture = profile.get("culture", 2.5)
    nature = profile.get("nature", 2.5)
    adventure = profile.get("adventure", 2.5)
    preferred_slot = plan.get("preferred_slot", "morning")
    if not vibe or not isinstance(vibe, dict):
        vibe = {"name": "Valley Explorer", "tagline": "Discovering Kathmandu"}
    vibe_name = vibe.get("name", "Valley Explorer")

    # 1. Trait-calibrated pacing prefix for first 30 minutes
    if energy <= 2.2:
        pacing_prefix = "Take an unhurried, contemplative breath upon entering. Find a sun-dappled courtyard ledge or timber bench to ground your senses before walking. "
    elif energy >= 3.8:
        pacing_prefix = "Maintain active, invigorating momentum as you navigate the outer threshold directly towards the high overlook. "
    elif crowd <= 2.0:
        pacing_prefix = "Slip quietly into the less-traveled perimeter corridors away from tour groups to savor the early morning stillness. "
    elif food >= 3.8:
        pacing_prefix = "Follow the scent of roasting spices and morning firewood wafting from neighboring alley hearths. "
    else:
        pacing_prefix = "Step directly into the living morning rhythm of ringing bells, lighting lamps, and artisan courtyard life. "

    # 2. Bespoke headline & Narrative
    headline = f"A curated {vibe_name} expedition calibrated to your {'contemplative' if energy < 2.5 else 'dynamic'} cadence"
    
    local_narrative = _build_local_personalized_narrative(plan, vibe)
    local_narrative["bespoke_headline"] = headline
    local_narrative["is_ai_generated"] = False
    plan["personalized_narrative"] = local_narrative
    plan["ai_narrative"] = local_narrative

    # 3. Stop-by-stop personalization
    for d in plan.get("days", []):
        for slot_name, slot in d.get("slots", {}).items():
            if not isinstance(slot, dict):
                continue
            s_id = slot.get("activity_id") or slot.get("festival_id") or slot.get("id") or ""
            cat = slot.get("category", "")
            base_guide = get_action_guidance_for_activity(s_id)

            # Generate dynamic why_for_you based on dominant traits
            if "Spiritual" in cat or spiritual >= 3.5:
                why_for_you = f"Curated for your reflective spirit ({spiritual:.1f}/5) to experience authentic sacred rituals and prayer corridors."
            elif "Nature" in cat or nature >= 3.5:
                why_for_you = f"Matched to your affinity for open nature ({nature:.1f}/5), refreshing valley breezes, and scenic viewpoints."
            elif "Food" in cat or food >= 3.5:
                why_for_you = f"Selected for your appreciation of authentic culinary heritage ({food:.1f}/5) and communal Newari cooking traditions."
            elif "Adventure" in cat or adventure >= 3.5:
                why_for_you = f"Chosen for your adventurous drive ({adventure:.1f}/5), offering active exploration beyond typical tourist routes."
            elif crowd <= 2.2:
                why_for_you = f"Selected for its tranquil, uncrowded atmosphere that matches your peaceful travel preference."
            else:
                why_for_you = f"A cornerstone destination calibrated to your love of living medieval heritage and artisan courtyards."

            slot["why_for_you"] = why_for_you
            base_what = base_guide.get("what_to_do", slot.get("what_to_do", ""))
            first_30 = f"{pacing_prefix}{base_what}"
            slot["first_30_min"] = first_30
            slot["ai_pacing_directive"] = first_30
            # Preserve hand-curated what_to_do and reason (do not overwrite with first_30)
            if not slot.get("what_to_do"):
                slot["what_to_do"] = base_what
            if not slot.get("reason"):
                slot["reason"] = base_what
            taste_val = base_guide.get("taste_pairing", slot.get("taste_pairing", ""))
            slot["taste_and_sit"] = taste_val
            slot["taste_pairing"] = taste_val
            slot["insider_secret"] = base_guide.get("insider_secret", slot.get("insider_secret", ""))


def synthesize_personalized_narrative(
    plan: Dict[str, Any],
    vibe: Dict[str, Any],
    gemini_api_key: Optional[str] = None
) -> Dict[str, Any]:
    """Backwards-compatible helper returning personalized narrative dict."""
    updated = personalize_itinerary_with_gemini(plan, api_key=gemini_api_key)
    return updated.get("personalized_narrative", _build_local_personalized_narrative(plan, vibe))


def _build_local_personalized_narrative(
    plan: Dict[str, Any],
    vibe: Dict[str, Any]
) -> Dict[str, Any]:
    """Construct an authentic, non-generic personalized narrative without API key."""
    profile = plan.get("profile", {})
    energy = profile.get("energy", 2.5)
    crowd = profile.get("crowd", 2.5)
    preferred_slot = plan.get("preferred_slot", "morning")
    vibe_name = vibe.get("name", "Valley Explorer")

    if energy < 2.5:
        pacing_phrase = "slow, contemplative pace with generous pauses for tea in sunlit courtyard bahals"
    else:
        pacing_phrase = "dynamic morning ascents and deep immersion through medieval cobblestone alleyways"

    if crowd < 2.5:
        atmosphere_phrase = "tranquil morning stupa corridors and quiet hill ridges above the valley mist"
    else:
        atmosphere_phrase = "bustling merchant bazaars, rhythmic temple bell aartis, and vibrant Newari community feasts"

    philosophy = (
        f"Your curated route as a {vibe_name} is curated around a {pacing_phrase}. "
        f"Instead of rushing through checklist tourist landmarks, every morning and evening is anchored around {atmosphere_phrase}. "
        f"You are traveling according to authentic Himalayan cadence—waking with the first temple bells, seeking quiet refuge during the midday heat, and savoring the warm amber glow of golden hour."
    )

    rhythm = (
        f"In Kathmandu, the magic is never hidden behind velvet ropes; it lives in the morning circumambulations, the smell of juniper smoke at dawn, and the friendly hospitality of courtyard tea vendors. "
        f"Because your rhythm leans toward the {preferred_slot}, dedicate those first hours entirely to sensory immersion before tour groups arrive. "
        f"A gentle greeting with palms pressed together and a soft 'Namaste' (or 'Jwajolapa' in Newari courtyards) transforms every interaction into genuine hospitality."
    )

    golden_rule = (
        "Never measure a day in the Kathmandu Valley by the number of sites visited. "
        "Measure it by the warmth of the tea shared, the resonance of morning prayer wheels under your fingers, and the quiet mountain light that settles over the brick rooftops as the evening bells begin to ring."
    )

    return {
        "bespoke_headline": f"A curated Kathmandu journey for the {vibe_name}",
        "philosophy_of_journey": philosophy,
        "journey_philosophy": philosophy,
        "local_rhythm_advice": rhythm,
        "golden_rule": golden_rule,
        "is_ai_generated": False
    }
