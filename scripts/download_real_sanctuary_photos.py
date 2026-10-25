import urllib.request
import urllib.parse
import json
import os
import struct
import time

HEADERS = {'User-Agent': 'VibeTripCurator/1.0 (https://vibetrip.example.org; contact@vibetrip.example.org)'}

TARGETS = [
    {
        "id": "world_peace_pagoda_pokhara",
        "file": "world_peace_pagoda_pokhara.jpg",
        "title": "File:World Peace Pagoda ,. Pokhara.jpg"
    },
    {
        "id": "sarangkot_sunrise_viewpoint",
        "file": "sarangkot_sunrise.jpg",
        "title": "File:Pokhara-Sarangkot-04-Morgendaemmerung-2015-gje.jpg"
    },
    {
        "id": "begnas_lake_retreat",
        "file": "begnas_lake.jpg",
        "title": "File:Begnas Lake, Pokhara, Kaski.jpg"
    },
    {
        "id": "gupteshwor_cave_davis_fall",
        "file": "davis_falls_gupteshwor.jpg",
        "title": "File:Davis Falls-Pokhara 02.jpg"
    },
    {
        "id": "international_mountain_museum",
        "file": "mountain_museum_pokhara.jpg",
        "title": "File:International Mountain Museum (2010), Pokhara, Nepal-02.jpg"
    },
    {
        "id": "poon_hill_ghorepani_trek",
        "file": "poon_hill.jpg",
        "title": "File:160315-019 View from Poon Hill.jpg"
    },
    {
        "id": "annapurna_base_camp_sanctuary",
        "file": "annapurna_base_camp.jpg",
        "title": "File:Annapurna Base Camp (3).JPG"
    },
    {
        "id": "mardi_himal_ridge_trail",
        "file": "mardi_himal.jpg",
        "title": "File:Golden Hour View from Badal Dada in Mardi Himal Trek.jpg"
    },
    {
        "id": "chitwan_jungle_safari",
        "file": "chitwan_safari.jpg",
        "title": "File:Baby rhino in Chitwan National Park.jpg"
    },
    {
        "id": "rapti_river_canoe_safari",
        "file": "rapti_river_canoe.jpg",
        "title": "File:Canoeing on river of gold.jpg"
    },
    {
        "id": "tharu_cultural_village_walk",
        "file": "tharu_cultural_village.jpg",
        "title": "File:Tharu Dance Sauraha Chitwan 2018.jpg"
    },
    {
        "id": "bardia_tiger_tracking_safari",
        "file": "bardia_national_park.jpg",
        "title": "File:Bengal Tiger Bardiya.jpg"
    },
    {
        "id": "muktinath_temple_108_spouts",
        "file": "muktinath_temple.jpg",
        "title": "File:Muktinath-temple-nepal.jpg"
    },
    {
        "id": "lo_manthang_walled_city",
        "file": "lo_manthang.jpg",
        "title": "File:Lo Manthang, The Historic Walled City of Upper Mustang.jpg"
    },
    {
        "id": "marpha_apple_village_walk",
        "file": "marpha_village.jpg",
        "title": "File:Kali Gandaki Valley, Marpha, Nepal, Himalaya.jpg"
    },
    {
        "id": "kagbeni_monastery_gateway",
        "file": "kagbeni_monastery.jpg",
        "title": "File:Mustang-Kagbeni-27-Gompa-2015-gje.jpg"
    },
    {
        "id": "maya_devi_temple_lumbini",
        "file": "maya_devi_temple_lumbini.jpg",
        "title": "File:Lumbini Maya Devi Temple 1.jpg"
    },
    {
        "id": "lumbini_monastic_zone_walk",
        "file": "lumbini_monastic_zone.jpg",
        "title": "File:Cambodian Monastery in Lumbini, 2019-04-09.jpg"
    },
    {
        "id": "tilaurakot_ancient_kapilavastu",
        "file": "tilaurakot_kapilavastu.jpg",
        "title": "File:Kapilavastu-easterngate.jpg"
    },
    {
        "id": "namche_bazaar_sherpa_hub",
        "file": "namche_bazaar.jpg",
        "title": "File:Namche Bazaar, Nepal.jpg"
    },
    {
        "id": "tengboche_monastery_view",
        "file": "tengboche_monastery.jpg",
        "title": "File:Tengboche-20-Tor-Ama Dablam-2007-gje.jpg"
    },
    {
        "id": "kala_patthar_everest_sunrise",
        "file": "kala_patthar.jpg",
        "title": "File:Close Up View of Mount Everest from Kala Patthar (5644 m) in 2023-IMG-3485.jpg"
    },
    {
        "id": "gokyo_lakes_and_ri",
        "file": "gokyo_lakes.jpg",
        "title": "File:Aerial View of Peaks of Khumbu, Ngozumpa Glacier and Gokyo Lakes.jpg"
    },
    {
        "id": "kyanjin_gompa_cheese_factory",
        "file": "kyanjin_gompa.jpg",
        "title": "File:Kyanjin Gompa Village Rasuwa.jpg"
    },
    {
        "id": "gosaikunda_sacred_alpine_lakes",
        "file": "gosaikunda_lake.jpg",
        "title": "File:Gosaikunda and Bhairab Kunda lake (Panoroma).jpg"
    },
    {
        "id": "bandipur_medieval_hill_town",
        "file": "bandipur_town.jpg",
        "title": "File:Bandipur, Nepal-WLV-1911.jpg"
    },
    {
        "id": "gorkha_historic_durbar",
        "file": "gorkha_durbar.jpg",
        "title": "File:Gorkha Palace durbar.jpg"
    },
    {
        "id": "rani_mahal_palpa",
        "file": "rani_mahal_palpa.jpg",
        "title": "File:Palpa, Ranighat Palace, Nepal.jpg"
    },
    {
        "id": "tansen_dhaka_and_shrinagar",
        "file": "tansen_palpa.jpg",
        "title": "File:Palpa Durbar & Museum 08.jpg"
    },
    {
        "id": "shey_phoksundo_deep_blue_lake",
        "file": "shey_phoksundo_lake.jpg",
        "title": "File:Shey-Phoksundo Lake in Dolpa.jpg"
    },
    {
        "id": "khaptad_national_park_meadows",
        "file": "khaptad_national_park.jpg",
        "title": "File:Greenery Khaptad National Park.jpg"
    },
    {
        "id": "suklaphanta_grassland_safari",
        "file": "suklaphanta_wildlife.jpg",
        "title": "File:Barhasinghe Swamp Deer Herd Grazing Near A Giant Tree.jpg"
    },
    {
        "id": "kanyam_tea_gardens_ilam",
        "file": "kanyam_tea_garden.jpg",
        "title": "File:Kanyam tea garden Nepal.jpg"
    },
    {
        "id": "sri_antu_kanchenjunga_sunrise",
        "file": "sri_antu_sunrise.jpg",
        "title": "File:Dawn's Palette at Shree Antu Hill, Ilam, Nepal.jpg"
    },
    {
        "id": "janaki_mandir_janakpur",
        "file": "janaki_mandir.jpg",
        "title": "File:Janaki Mandir, Janakpur Nepal 01.jpg"
    },
    {
        "id": "vivaha_mandap_mithila_art",
        "file": "vivaha_mandap_janakpur.jpg",
        "title": "File:Vivah Mandap, Janakpur-September 22, 2016-7340.jpg"
    },
    {
        "id": "pathibhara_devi_taplejung",
        "file": "pathibhara_devi.jpg",
        "title": "File:Buddhist Prayer Flags at Pathibhara Devi Temple.jpg"
    }
]

def get_image_info(data):
    if data[:2] == b'\xff\xd8':
        b = data[2:]
        while len(b) > 0:
            if b[0] != 0xff:
                break
            marker = b[1]
            if marker in (0xc0, 0xc1, 0xc2):
                h, w = struct.unpack('>HH', b[5:9])
                return 'JPEG', w, h
            length = struct.unpack('>H', b[2:4])[0]
            b = b[2+length:]
    elif data[:8] == b'\x89PNG\r\n\x1a\n':
        w, h = struct.unpack('>II', data[16:24])
        return 'PNG', w, h
    return 'UNKNOWN', 0, 0

def fetch_file_url(title):
    url = (
        f"https://commons.wikimedia.org/w/api.php?action=query&format=json&titles={urllib.parse.quote(title)}"
        f"&prop=imageinfo&iiprop=url|size|mime&iiurlwidth=1280"
    )
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as resp:
        d = json.loads(resp.read().decode('utf-8'))
    pages = d.get('query', {}).get('pages', {})
    for pid, p in pages.items():
        ii_list = p.get('imageinfo', [])
        if ii_list:
            ii = ii_list[0]
            return ii.get('thumburl') or ii.get('url')
    return None

def download_image(url, out_path):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        content = resp.read()
    with open(out_path, 'wb') as f:
        f.write(content)
    return content

def main():
    os.makedirs('static/img/places', exist_ok=True)

    success_count = 0
    for idx, target in enumerate(TARGETS, 1):
        out_file = os.path.join('static', 'img', 'places', target['file'])
        if os.path.exists(out_file) and os.path.getsize(out_file) > 10000:
            print(f"[{idx:02d}/{len(TARGETS)}] Already downloaded {target['file']}")
            success_count += 1
            continue

        print(f"[{idx:02d}/{len(TARGETS)}] Fetching {target['id']} -> {target['file']}...")
        img_url = fetch_file_url(target['title'])
        if not img_url:
            print(f"  [ERROR] Could not resolve URL for {target['title']}")
            continue
        
        try:
            data = download_image(img_url, out_file)
            fmt, w, h = get_image_info(data)
            size_kb = len(data) / 1024
            print(f"  [OK] Saved {fmt} {w}x{h} ({size_kb:.1f} KB)")
            success_count += 1
        except Exception as e:
            print(f"  [FAIL] Download error: {e}")
        time.sleep(0.3)

    print(f"\nDownloaded/verified {success_count}/{len(TARGETS)} images successfully.")

if __name__ == '__main__':
    main()
