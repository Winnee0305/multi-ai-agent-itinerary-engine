"""
POI Enrichment Script
Enriches Malaysia POI data with popularity scores using:
1. Golden List (Top attractions)
2. Wikidata (Sitelinks)
"""

import json
import time
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from SPARQLWrapper import SPARQLWrapper, JSON as SPARQL_JSON
from fuzzywuzzy import fuzz


# Golden List: Top attractions per state
TOP_POIS_MALAYSIA = {
    "Pahang": [
        "Genting Highlands", "Chin Swee Caves Temple", "Genting SkyWorlds Theme Park",
        "Cameron Highlands", "BOH Tea Plantation", "Mossy Forest",
        "Time Tunnel Museum", "Lavender Garden", "Cameron Highlands Butterfly Farm",
        "Gunung Brinchang", "Taman Negara", "Canopy Walkway Taman Negara",
        "Kuala Tahan", "Kenyir Elephant Conservation Village", "Cherating Beach",
        "Cherating Turtle Sanctuary", "Club Med Cherating", "Teluk Chempedak",
        "Bukit Gambang Safari Park", "Bukit Gambang Water Park",
        "Sungai Lembing Mines", "Rainbow Waterfall", "Sungai Lembing Museum",
        "Kuantan River Cruise", "Bukit Panorama", "Berjaya Hills (Colmar Tropicale)",
        "Japanese Village", "Gunung Tahan", "Gunung Senyum",
        "Chamang Waterfall", "Jerangkang Waterfall", "Janda Baik",
        "Lata Berembun", "Teladas Hot Spring", "Esplanade Kuantan",
        "Gua Charas", "Pahang Art Museum", "Kuantan 188 Tower",
        "Sri Marathandavar Aalayam", "Bukit Pelindung", "Kuantan City Mall",
        "Taman Gelora", "Gua Bama", "Frasers Hill", "Allan's Water",
        "Bird Interpretive Centre", "Hemmant Trail", "Abu Suradi Trail", "Gunung Irau",
        "Pine Tree Trail", "Raub Durian Orchards", "Lata Jarum Waterfall",
        "Fraser's Hill Clock Tower", "The Paddock Fraser's Hill", "Jeriau Waterfall",
        "Kuala Gandah Elephant Sanctuary", "Deerland Park Lanchang", "Pekan Royal Town",
        "Sultan Abu Bakar Museum", "Masjid Sultan Ahmad Shah", "Lake Chini",
        "Tioman Island", "Juara Beach", "Salang Beach", "Mukut Village",
        "Asah Waterfall", "Tekek Village", "Marine Park Centre Tioman",
        "Rompin State Park", "Endau-Rompin National Park (Pahang Entrance)",
        "Merapoh Caves", "Gua Tahi Bintang", "Gua Hari Malaysia",
        "Sungai Pandan Waterfall", "Berkelah Waterfall", "Seven Wells Waterfall (Raub)",
        "Bentong Walk", "Lemang To'ki", "Bilut Extreme Park",
        "Kea Farm Market", "Cactus Valley", "Big Red Strawberry Farm",
        "Cameron Lavender Garden", "Agro Technology Park MARDI", "Sam Poh Wan Futt Chi Temple",
        "Tanah Rata Town", "Parit Fall", "Robinson Falls",
        "Gap Resthouse", "Tras Road Chinese Temple", "Lata Lembik",
        "Tanah Aina Farrah Soraya", "Lata Meraung", "Pulau Chekas",
        "Som Forest Reserve", "Kenong Rimba Park", "Gunung Benom",
        "Kota Gelanggi Caves", "Tekam Plantation Resort", "Tun Abdul Razak Memorial",
        "Royal Pahang Polo Club", "Pekan Riverfront", "Pantai Lagenda",
        "Pantai Hiburan", "Pantai Air Leleh", "Lanjut Beach"
    ],

    "Selangor": [
        "Batu Caves", "Sunway Lagoon", "i-City Shah Alam", "Klang Royal Gallery",
        "Sky Mirror Kuala Selangor", "Sekinchan Paddy Fields", "Sekinchan Beach",
        "Farm in The City", "Zoo Negara", "Sultan Salahuddin Mosque",
        "Kuala Selangor Nature Park", "Firefly Park", "Taman Botani Negara",
        "Setia City Park", "Mitsui Outlet Park", "Pantai Remis",
        "Pantai Jeram", "Empire Shopping Gallery", "Gua Damai Extreme Park",
        "Rawang Bypass Viewpoint", "Sasaran Beach", "Sunway Pyramid",
        "Gamuda Cove Water Park", "Gamuda Cove Discovery Park",
        "Paya Indah Wetlands", "Cyberjaya Lake Gardens", "DPULZE",
        "Mah Meri Cultural Village", "Bukit Melawati", "1 Utama Rainforest",
        "SACC Mall", "Selangor-Japan Friendship Garden", "Kidzania",
        "Templer Park", "Kanching Waterfall", "Sungai Congkak", "Skytrex Sg Congkak",
        "Skytrex Shah Alam", "Empire Damansara", "Pantai Morib",
        "Klang Heritage Walk", "Royal Klang Mosque", "The Mines Lake",
        "Tropicana Gardens Mall", "I-City Ferris Wheel", "Selangor River Cruise",
        "SplashMania Gamuda Cove", "Serendah Waterfall", "Bukit Gasing",
        "Broga Hill", "Semenyih Eco Venture Resort", "Sungai Tekala Waterfall",
        "Sungai Gabai Waterfall", "Hulu Langat Observation Tower", "Ostrich Wonderland Semenyih",
        "Setia City Convention Centre", "Ardence Labs", "Eco Ardence Maya Park",
        "Tanjung Sepat Lover's Bridge", "Ganofarm Homestay", "Kuan Wellness Eco Park",
        "Bagan Lalang Beach", "Avani Sepang Goldcoast", "Sepang International Circuit",
        "National Automobile Museum", "Mitsui Outlet Park KLIA", "Salak Tinggi Hill",
        "Bukit Jugra Lighthouse", "Istana Bandar Jugra", "Alaeddin Mosque",
        "Fo Guang Shan Dong Zen Temple", "Tadom Hill Resorts", "Pulau Carey",
        "Amverton Cove Golf & Island Resort", "Riverine Splash", "Little India Klang",
        "Tanjung Harapan", "Pulau Ketam", "Sungai Lima",
        "Kuala Kubu Bharu Heritage Town", "Sungai Chiling Fish Sanctuary",
        "Millennium Park KKB", "Paragliding KKB", "Selangor Fruit Valley",
        "Raja Tun Uda Library", "Laman Seni 7", "Shah Alam Lake Garden",
        "Kota Kemuning Lake Park", "IOI City Mall (Sepang part)", "The Arc Rimbayu",
        "Quayside Mall", "Hutan Lipur Sungai Tua", "Commonwealth Forest Park",
        "Selayang Hot Spring", "Kepong Metropolitan Park", "FRIM (Forest Research Institute)",
        "Skyway Forest FRIM", "Batu Arang Heritage Town", "Tasik Biru Kundang",
        "Elmina Valley Park", "Denai Alam Riding Club", "Saujana Hijau Park"
    ],

    "Kuala Lumpur": [
        "Petronas Twin Towers", "KLCC Park", "Suria KLCC", "KL Tower",
        "Aquaria KLCC", "KL Forest Eco Park", "Chinatown Petaling Street",
        "Central Market", "Little India Brickfields", "Batu Caves (nearby)",
        "National Museum", "National Mosque", "Jalan Alor",
        "Bukit Bintang", "Pavilion KL", "Lot 10", "The Exchange TRX",
        "Saloma Link", "River of Life", "Masjid Jamek",
        "Dataran Merdeka", "Sultan Abdul Samad Building",
        "Islamic Arts Museum", "Perdana Botanical Gardens", "KL Bird Park",
        "KL Butterfly Park", "Thean Hou Temple", "Sunway Putra Mall",
        "Planetarium Negara", "Bank Negara Museum", "The Linc KL",
        "Chow Kit Market", "Rex KL", "Mid Valley Megamall",
        "Gardens Mall", "Istana Negara (Old Palace)",
        "Muzium Telekom", "National Textile Museum", "P. Ramlee House",
        "Tugu Negara", "Bangsar Village", "KL Sentral", "Nu Sentral",
        "Pavilion Damansara Heights", "KL Upside Down House",
        "Petrosains Discovery Centre", "Alor Street Food Night Market",
        "Eko Rimba Kanching", "Malaysia Cartoon & Comic Museum",
        "Titiwangsa Lake Gardens", "Istana Budaya", "National Art Gallery",
        "Rumah Penghulu Abu Seman", "Badan Warisan Malaysia", "Masjid Wilayah Persekutuan",
        "Publika Shopping Gallery", "Solaris Dutamas", "Hartamas Shopping Centre",
        "Bukit Kiara Federal Park", "TTDI Park", "Agape Centre",
        "Kuala Lumpur Craft Complex", "Royal Malaysia Police Museum", "Tun Abdul Razak Memorial",
        "Sin Sze Si Ya Temple", "Sri Mahamariamman Temple", "Guan Di Temple",
        "Chan She Shu Yuen Clan Ancestral Hall", "Kwai Chai Hong", "Pudu Wet Market",
        "ICC Pudu", "LaLaport BBCC", "Mitsui Shopping Park LaLaport",
        "Berjaya Times Square", "Plaza Low Yat", "Sungei Wang Plaza",
        "Fahrenheit 88", "Starhill Gallery", "Jalan Mesui",
        "Changkat Bukit Bintang", "Taman Tugu", "Ilham Gallery",
        "Kampung Baru Heritage Walk", "Pintasan Saloma", "Masjid India",
        "Jakel Mall", "Sogo KL", "Pertama Complex",
        "Mara Digital Mall", "Biosphere at The Exchange TRX", "Bamboo Hills",
        "Sentul Depot", "KLPAC (Performing Arts Centre)", "APW Bangsar",
        "Bangsar Shopping Centre", "The Row", "Asian Heritage Row",
        "Telekom Museum", "Minnature Malaysia", "Superpark Malaysia",
        "District 21", "Bukit Jalil National Stadium", "Bukit Jalil Recreational Park",
        "Pavilion Bukit Jalil", "Desa ParkCity Waterfront"
    ],

    "Johor": [
        "Legoland Malaysia", "Hello Kitty Town", "Johor Premium Outlets",
        "Desaru Coast Adventure Waterpark", "Desaru Beach",
        "Desaru Ostrich Farm", "Teluk Sengat Crocodile Farm", "Endau-Rompin National Park",
        "Pulau Rawa", "Pulau Dayang", "Pulau Aur", "Sultan Abu Bakar Mosque",
        "Arulmigu Sri Rajakaliamman Glass Temple", "Danga Bay", "Puteri Harbour",
        "Gunung Pulai Waterfall", "Kukup Island", "Tanjung Piai National Park",
        "Johor Bahru Old Chinese Temple", "Johor Zoo", "KSL Mall", "Mid Valley Southkey",
        "Forest City", "Mersing Jetty", "Kota Tinggi Waterfall", "Kulai Putuo Village",
        "Muar Riverside", "Muar Street Art", "Tangkak Gunung Ledang", "Pontian Kechil",
        "YSL Heritage Johor", "Pasir Gudang Kite Museum", "Mount Belumut",
        "Laman Mahkota Istana Bukit Serene", "Austin Heights Water Park",
        "Senibong Cove", "Rumah Limas Johor", "Gunung Lambak", "Sibu Island",
        "Tioman Island (via Johor routes)", "Sultan Ibrahim Building",
        "Penggaram Batu Pahat Square", "Desaru Fruit Farm",
        "Eco Botanic Park", "Skyscape JB", "Sail Rock", "Mawai Eco Camp",
        "Gunung Arong", "Pulau Tinggi",
        "Zenxin Organic Park", "UK Farm Kluang", "Kluang Rail Coffee",
        "Gunung Belumut", "Kota Iskandar", "EduCity Sports Complex",
        "Sireh Park", "X Park Sunway Iskandar", "Rudi's Grape Farm",
        "Bugis Museum", "Tanjung Balau Fishermen Museum", "Tanjung Balau Beach",
        "Batu Layar Beach", "Jason Bay (Teluk Mahkota)", "Mersing Harbour Centre",
        "Pulau Besar", "Pulau Pemanggil", "Pulau Tengah",
        "Air Papan Beach", "Penyabong Beach", "Gunung Panti",
        "Kota Tinggi Firefly Park", "Tanjung Emas Muar", "Donhu Jurassic Garden Muar",
        "Parit Jawa Fishermen Village", "Wet World Batu Pahat", "Pantai Minyak Beku",
        "Chong Long Gong Temple", "Lover's Bridge Batu Pahat", "Nasuha Spices Garden",
        "Pagoh Higher Education Hub", "Labis Hot Spring", "Bekok Waterfall",
        "Sungai Bantang Recreational Forest", "Taman Negara Johor Gunung Ledang",
        "Sagil Waterfall", "Nasi Lemak Lobster Pengerang", "Yard & Co.",
        "Sungai Rengit Town", "Fishermen Museum Tanjung Balau", "Desaru Coast Riverside",
        "The Els Club Desaru", "Hard Rock Hotel Desaru", "Kulai Mural Street",
        "Star Fish Leisure Farm", "Rainforest Tree House Kulai", "Pasar Karat JB",
        "Bazaar Karat", "Jalan Dhoby", "Jalan Tan Hiok Nee",
        "Toppen Shopping Centre", "IKEA Tebrau", "Paradigm Mall JB",
        "Blue Lagoon Seri Alam", "Tasik Merdeka"
    ],

    "Malacca": [
        "A Famosa", "St Paul's Hill", "Christ Church", "Dutch Square",
        "Jonker Street", "Jonker Walk", "Jonker Street Night Market", "Maritime Museum", "Melaka River Cruise",
        "The Shore Sky Tower", "Menara Taming Sari", "Melaka Sultanate Palace Museum",
        "Baba Nyonya Heritage Museum", "Klebang Beach", "Klebang Coconut Shake", "Klebang Original Coconut Shake",
        "Encore Melaka", "Submarine Museum", "A Famosa Safari Wonderland",
        "A Famosa Water Theme Park", "Melaka Wonderland", "Cheng Hoon Teng Temple",
        "Kampung Morten", "Masjid Selat Melaka (Floating Mosque)",
        "Kampung Hulu Mosque", "Portuguese Settlement", "Villa Sentosa Museum",
        "Melaka Zoo", "Skytrex Melaka", "Hang Tuah Centre", "Pantai Puteri",
        "Melaka Straits Mosque", "Klebang Dataran 1Malaysia",
        "Mini Malaysia & ASEAN Cultural Park", "Bukit Cina", "Pantai Tanjung Kling",
        "Hang Jebat Mausoleum", "Hang Tuah Village", "Toy Museum Melaka",
        "Melaka Tropical Fruit Farm", "Illusion 3D Art Museum", "Magic Art Museum",
        "Melaka Bird Park", "Kampung Chetti", "Rumah Melayu Melaka",
        "The Stadthuys", "Melaka Heritage Trail", "Masjid Tengkera",
        "Bukit Beruang Forest", "Melaka Botanical Garden", "Al-Khawarizmi Astronomy Complex",
        "Melaka Planetarium",
        "Freeport A'Famosa Outlet", "Machap Walk", "Gadek Hot Springs",
        "Jasin Hot Springs", "Asahan Waterfall", "Gunung Datuk (border access)",
        "Bukit Batu Lebah", "Taman Seribu Bunga", "Muzium Rakyat",
        "Museum of Enduring Beauty", "Malaysian Customs Museum", "Melaka Stamp Museum",
        "Melaka Kite Museum", "Melaka Islamic Museum", "Democratic Government Museum",
        "Governor's Museum", "Flora de la Mar", "Padang Pahlawan",
        "Dataran Pahlawan Megamall", "Mahkota Parade", "Elements Mall",
        "Pasar Besar Melaka", "Medan Ikan Bakar Parameswara", "Medan Ikan Bakar Umbai",
        "Perkampungan Hang Tuah", "Hang Li Po's Well", "Poh San Teng Temple",
        "Sri Poyyatha Vinayagar Moorthi Temple", "Kampung Kling Mosque", "Red Square",
        "Queen Victoria's Fountain", "St. Francis Xavier Church", "Sacred Heart Canossian Convent",
        "Mamee Jonker House", "Hard Rock Cafe Melaka", "Casa del Rio",
        "The Shore Oceanarium", "Toy Museum @ The Shore", "Kampung Cantik",
        "Pantai Siring", "Pulau Besar Melaka", "Tomb of Sultan Ariffin",
        "Puteri Beach", "Taman Buaya & Rekreasi Melaka", "Bee Farm Melaka",
        "Butterfly & Reptile Sanctuary", "Orang Utan House", "Cheng Ho Cultural Museum",
        "Jewellery Museum Melaka", "Upside Down House Melaka", "Masjid Cina Melaka",
        "Seafarer's Bridge"
    ],

    "Negeri Sembilan": [
        "Port Dickson Beach", "PD Waterfront", "Blue Lagoon PD",
        "Teluk Kemang", "Cape Rachado Lighthouse", "Alive 3D Art Gallery",
        "Army Museum Port Dickson", "Upside Down House PD",
        "PD Ostrich Farm", "Wan Loong Temple", "Tanjung Tuan Forest Reserve",
        "Lukut Fort Museum", "Nilai 3 Wholesale Centre", "Seremban Lake Garden",
        "Seremban Siew Pow Factory", "Terminal One Seremban", "Gunung Angsi",
        "Gunung Datuk", "Gunung Telapak Buruk", "Jelita Ostrich Farm",
        "Jempol Coffee Valley", "Kuala Pilah Royal Museum", "Istana Seri Menanti",
        "Ulu Bendul Recreational Park", "PD Resort Cruise", "Dataran Montel",
        "PD Extreme Park", "Taman Negeri Kenaboi", "Rantau Eco Park",
        "Gemencheh Bridge Memorial", "PD Seaview Beach", "Lexis Hibiscus",
        "Avillion Port Dickson", "PD Marina", "Kota Seriemas Golf Club",
        "Pusat Dakwah Islamiah Seremban", "Nilai Springs Golf Club",
        "Palm Mall Seremban", "Seri Menanti Royal Museum",
        "Gunung Tampin", "PD Sky Ladder", "PD Swiss Garden",
        "Rantau Hill", "The Dusun Nature Retreat", "Mantin Thai Valley",
        "Pusat Rekreasi Air Panas Gadek", "Ulu Slim", "Air Mawang",
        "Air Panas Pedas",
        "Jeram Toi Waterfall", "Hutan Lipur Lenggeng", "Broga Hill (Negeri Side)",
        "Sak Dato Temple", "Centipede Temple (Then Sze Koon)", "Masjid Negeri Seremban",
        "Church of the Visitation", "Seremban Cultural Complex", "Galeri Diraja Tuanku Ja'afar",
        "Muzium Negeri Sembilan", "Taman Malaysia Seremban", "Kompleks Kraf NS",
        "Teratak Za'ba", "Megalithic Sites Kuala Pilah", "Hutan Lipur Serting Ulu",
        "Jeram Tengkek", "Gunung Besar Hantu", "Lata Kijang Waterfall",
        "Kenaboi State Park", "Titi Eco Farm", "Jelebu Customary Museum",
        "Masjid Jamek Kuala Pilah", "Martin Lister Memorial", "Kuala Pilah Arch",
        "Bahau Town Park", "Bukit Taisho", "Gemas Railway Station (Old)",
        "Gemas War Memorial", "Starfresh Agro Park", "Awanmulan Retreat",
        "The Shorea", "Sembayu Villa", "Spyder Hill",
        "Pantai Cermin", "Pantai Purnama", "Pantai Saujana",
        "Pantai Cahaya Negeri", "Pantai Bagan Pinang", "Grand Lexis Port Dickson",
        "Thistle Port Dickson", "Wild West Cowboy Indoor Theme Park", "Segar City",
        "Lukut Mangrove Forest", "Kota Lukut", "3D Art Gallery Lukut",
        "Sepri Pedas High Ropes", "Rembau Museum", "Crystal Mosque Nilai",
        "MesaMall Nilai", "Dataran Nilai", "Universiti Sains Islam Malaysia (Architecture)",
        "Kolej Tuanku Ja'afar"
    ],

    "Perak": [
        "Kellie's Castle", "Lost World of Tambun", "Ipoh Concubine Lane",
        "Birch Memorial Clock Tower", "Ipoh Railway Station", "Gunung Lang",
        "Perak Cave Temple", "Kek Lok Tong", "Sam Poh Tong", "Taiping Lake Gardens",
        "Taiping Zoo & Night Safari", "Bukit Larut", "Pangkor Island",
        "Pangkor Laut Resort", "Teluk Nipah", "Gua Tempurung",
        "Leaning Tower of Teluk Intan", "Orangutan Island Bukit Merah",
        "Victoria Bridge Kuala Kangsar", "Ubudiah Mosque", "Istana Kenangan",
        "Royal Museum Kuala Kangsar", "Pasir Salak Historical Complex",
        "Sungai Klah Hot Springs", "Tua Pek Kong Temple Sitiawan", "Lumut Waterfront",
        "Bukit Kledang", "Mirror Lake Ipoh", "Movie Animation Park Studios",
        "Bukit Merah Laketown Resort", "Lata Iskandar", "Lata Kinjang",
        "Lenggong Valley UNESCO Site", "Gua Puteri", "Gua Ngaum",
        "Teluk Senangin", "Tanjung Tualang Tin Dredge", "Ipoh World Han Chin Pet Soo",
        "Tasik Cermin", "Gunung Yong Belar", "Gunung Korbu", "Gunung Irau (border)",
        "Tapah Waterfall", "Kuala Sepetang Mangrove", "Suzana Art Gallery",
        "Teluk Intan Esplanade", "Bidor Waterfall", "Lumut Oceanfront",
        "Royal Belum State Park", "Temenggor Lake", "Banding Island",
        "Gopeng White Water Rafting", "Gaharu Tea Valley Gopeng", "HOGA Gaharu Tea Valley",
        "Kampar Disney Avenue", "Kinta Tin Mining Museum", "Refarm Kampar",
        "Batu Gajah Heritage Trail", "Tanjung Tualang Prawn Mines", "Pasir Bogak Beach",
        "Coral Beach Pangkor", "Kota Belanda", "Batu Bersurat Pangkor",
        "Masjid Terapung Pangkor", "Teluk Batik Beach", "Marina Island Lumut",
        "Frenzy Water Park Marina Island", "Sitiawan Settlement Museum", "Kampung Koh Market",
        "Teluk Intan River Cruise", "Beting Beras Basah", "Bagan Datuk Waterfront",
        "Sunflower Garden Bagan Datuk", "Blue Mosque Bagan Datuk", "Kuala Wo Jungle Park",
        "Lata Kekabu", "Chenderoh Lake", "Tasik Raban",
        "Archaeological Museum of Lenggong", "Kuala Gula Bird Sanctuary", "Matang Mangrove Forest",
        "Charcoal Factory Kuala Sepetang", "Port Weld Scenic Bridge", "Antong Coffee Mill",
        "Perak Museum Taiping", "Taiping War Cemetery", "First Gallaries Taiping",
        "Burmese Pool Taiping", "Spritzer Eco Park", "Masjid India Muslim Ipoh",
        "Funtasy House Trick Art", "Ho Yan Hor Museum", "Yasmin Ahmad Museum",
        "22 Hale Street Heritage Gallery", "Memory Lane Morning Market", "Gerbang Malam Ipoh",
        "Qing Xin Ling Leisure & Cultural Village", "Ling Sen Tong Temple", "Kwan Yin Tong Temple",
        "Tambun Pomelo Farms", "Ulu Slim Hot Springs", "Felda Residence Hot Springs",
        "Trolak Country Resort", "Sahom Valley Resort"
    ],

    "Penang": [
        "Kek Lok Si", "Penang Hill", "George Town UNESCO Heritage Zone",
        "Clan Jetties", "Armenian Street Art", "Cheong Fatt Tze Blue Mansion",
        "Pinang Peranakan Mansion", "Wonderfood Museum", "Escape Theme Park",
        "Entopia Penang", "Made in Penang Museum", "Fort Cornwallis",
        "Penang Street Food (Gurney Drive)", "Gurney Plaza", "Gurney Paragon",
        "Batu Ferringhi Beach", "Tropical Spice Garden", "Penang National Park",
        "Monkey Beach", "Penang Avatar Secret Garden", "Penang War Museum",
        "Snake Temple", "Penang 3D Trick Art", "Hin Bus Depot",
        "Queensbay Mall", "Penang Floating Mosque", "Penang Clans Jetty",
        "Penang Ferry", "Penang Botanic Gardens", "The Habitat Penang Hill",
        "Penang Little India", "Khoo Kongsi", "Penang State Museum",
        "Rainbow Skywalk Komtar", "Tech Dome Penang", "Design Village Mall",
        "Nyonya Heritage Museum", "Dark Mansion Museum", "Penang Aquarium",
        "Chew Jetty", "Clan Jetty Walkway", "Street of Harmony",
        "Bukit Genting Leisure Park", "Penang House of Music", "One Pacific Mall",
        "Penang Tropical Fruit Farm", "Glass Museum Penang", "Penang Toy Museum",
        "Straits Quay",
        "Teluk Bahang Dam", "Batu Maung Fishing Village", "Sam Poh Footprint Temple",
        "Jerejak Island", "Jerejak Rainforest Resort", "Pantai Kerachut",
        "Muka Head Lighthouse", "Teluk Kampi", "Gertak Sanggul",
        "Balik Pulau Paddy Fields", "Saanen Dairy Goat Farm", "Audi Dream Farm",
        "Countryside Stables Penang", "Container Art Balik Pulau", "Bukit Mertajam Recreational Forest",
        "Cherok Tok Kun", "St. Anne's Church", "Mengkuang Dam",
        "Frog Hill (Tasek Gelugor)", "Kampung Agong", "Penang Bird Park",
        "Sunway Carnival Mall", "Auto City Juru", "Icon City Bukit Mertajam",
        "Nine Emperor Gods Temple", "Tow Boo Kong Temple Butterworth", "Butterworth Art Walk",
        "Pantai Bersih", "Robina Beach", "Pulau Aman",
        "Batu Kawan Stadium", "IKEA Batu Kawan", "Aspen Vision City Central Park",
        "Penang Bridge (Viewpoint)", "Sultan Abdul Halim Muadzam Shah Bridge", "P. Ramlee Gallery",
        "Sun Yat-sen Museum", "Asia Camera Museum", "Penang Gold Museum",
        "Colonial Penang Museum", "Ghost Museum Penang", "Teddyville Museum",
        "Owl Museum", "Camera Museum", "Ben's Vintage Toy Museum",
        "Kapitan Keling Mosque", "Yap Kongsi", "Han Jiang Ancestral Hall",
        "Teochew Temple", "Sri Mahamariamman Temple", "Nagore Square",
        "New World Park", "Chowrasta Market", "Cecil Street Market",
        "Fisherman's Wharf Penang", "Youth Park (Taman Perbandaran)", "Moon Gate Hike"
    ],

    "Kedah": [
        "Langkawi SkyBridge", "Langkawi Cable Car", "Pantai Cenang",
        "Pantai Tengah", "Eagle Square (Dataran Lang)", "Underwater World Langkawi",
        "Tanjung Rhu Beach", "Langkawi Wildlife Park", "Mahsuri Mausoleum",
        "Langkawi Geopark", "Kilims Geoforest Park", "Crocodile Adventureland",
        "Gunung Raya", "Seven Wells Waterfall", "Telaga Tujuh", "Langkawi Bird Paradise",
        "Langkawi Mangrove Tour", "Langkawi Island Hopping", "Pulau Payar Marine Park",
        "Atma Alam Art Village", "Laman Padi", "Alor Setar Tower", "Aman Central Mall",
        "Masjid Zahir", "Pekan Rabu", "Bujang Valley Archaeological Museum",
        "Gunung Jerai", "Pantai Merdeka", "Tree Top Walk Sungai Sedim",
        "Ulu Legong Hot Springs", "The Big Clock Tower Alor Setar",
        "Bukit Hijau Waterfall", "Bukit Perak", "Bukit Selambau Waterfall",
        "Kota Kuala Kedah", "Langkawi Zipline Adventure", "Black Sand Beach Langkawi",
        "Langkawi Art in Paradise 3D Museum", "Galeria Perdana", "Durian Perangin Waterfall",
        "Gunung Machinchang", "Langkawi UNESCO Geoforest", "Pulau Beras Basah",
        "Pantai Kok", "Langkawi SkyRex", "Rice Garden Museum", "Tuba Island",
        "Langkawi Safari Tour", "Alor Setar Chinatown",
        "Muzium Padi", "Pusat Sains Negara (Cawangan Utara)", "Rumah Kelahiran Mahathir Mohamad",
        "Istana Anak Bukit", "Balai Besar", "Balai Nobat",
        "Kedah State Museum", "Blue Lagoon Alor Setar", "Gunung Keriang",
        "Gua Kerbau", "Fantasia Aquapark", "Darulaman Park",
        "Tasik Darulaman", "Splash Out Langkawi", "Skytrex Adventure Langkawi",
        "MARDI Langkawi Agro Technology Park", "Buffalo Park Langkawi", "Kompleks Kraf Langkawi",
        "Air Hangat Village", "Temurun Waterfall", "Pasir Tengkorak Beach",
        "Shark Bay Beach", "Datai Bay", "Teluk Burau",
        "Pulau Dayang Bunting", "Tasik Dayang Bunting", "Pulau Singa Besar",
        "Pulau Rebak", "Royal Kedah Club", "Sungai Petani Clock Tower",
        "Dataran Zero Kilometer", "Semeling Mangrove Forest", "Pantai Murni Waterfront",
        "Tanjung Dawai", "Pedu Lake", "Muda River",
        "Beris Lake Vineyard", "Tasik Beris", "Wat Nikrodharam",
        "Kulim Golf & Country Resort", "Junjong Waterfall", "Lata Mengkuang",
        "Gunung Baling", "Gunung Pulai (Baling)", "Lata Bayu",
        "Ulu Paip Recreational Forest", "Sik Mubaligh Centre", "Ladang Anggur Tasik Beris",
        "Rimba Rekreasi Bukit Wang", "Taman Jubli Emas", "Riverfront City Sungai Petani"
    ],

    "Perlis": [
        "Perlis State Park", "Gua Kelam", "Tasik Melati", "Arau Royal Palace",
        "Perlis Snake and Reptile Farm", "Kota Kayang Museum", "Wang Kelian Viewpoint",
        "Chuping Sugarcane Plantation", "Harumanis Mango Farms", "Timah Tasoh Lake",
        "Bukit Kubu", "Padang Besar Duty Free Zone", "Masjid Al-Hussain (Floating Mosque)",
        "Bukit Ayer Recreational Forest", "Gua Wang Burma", "Perlis Herb Garden",
        "Gua Sami", "Pauh Putra Mosque", "Arau Railway Station", "Gua Rimau",
        "FELDA Mata Ayer", "Taman Rekreasi Bukit Lagi", "Kaki Bukit Town",
        "Kuala Perlis Jetty", "Kuala Perlis Food Court", "MARA Craft Perlis",
        "Bukit Lagi Hilltop", "UniMAP Kangar", "Arau Food Court", "Mango Valley",
        "Tambun Tulang Mosque", "Pauh Putra Lake", "Chuping Valley Forest Park",
        "Bukit Bunga Raya", "Jalan Raja Syed Alwi", "Perlis Eco Trails",
        "Sungai Batu Pahat Recreational Park", "Bukit Chabang", "Kangar Tower",
        "Kangar Street Art", "Taman Kayangan", "Nursery Anggur Perlis",
        "Taman Bukit Jernih", "Lakeview Kangar", "Heritage Trail Perlis",
        "Arked Niaga Padang Besar", "Taman Bukit Lagi", "Perlis Padi Field Trail",
        "Kuala Perlis Sunset Point",
        "Ladang Nipah Kipli", "Warung Tepi Sawah", "Nat Pokok Getah (Morning Market)",
        "Pasar Tani Kekal Chuping", "Masjid Tuanku Syed Putra", "Galeri DiRaja Arau",
        "Viewpoint Wang Gunung", "Hutan Lipur Bukit Ayer", "Canopy Walkway FRIM Perlis",
        "Tasik Timah Tasoh Resort", "Dataran Dato' Sheikh Ahmad", "Stadium Tuanku Syed Putra",
        "Kompleks Sukan Tuanku Syed Putra", "Laman Bunga Kertas Tuanku Lailatul Shahreen", "Taman Anggur Perlis",
        "Superfruits Valley", "Kampung Warna Warni Seberang Ramai", "Projek Diraja PPRT",
        "Empangan Timah Tasoh", "Batu Pahat Golf Club", "Padang Besar Immigration Complex",
        "Gapura Square", "The Store Kangar", "Giant Kangar",
        "Kuala Sanglang", "Pantai Kurong Tengar", "Kampung Ujung Bukit",
        "Rock Climbing at Bukit Keteri", "Gua Cenderawasih", "Abi Rock Climbing",
        "Bukit Jernih Recreational Park", "Al-wi Mosque", "Kangar Mural Art",
        "Denai Larian Pengkalan Asam", "Taman Ular & Reptilia (Expanded area)", "Pusat Kecemerlangan Sukan",
        "Tasik Timah Tasoh (West Side)", "Kampung Wang Ulu", "Kampung Wai",
        "Bukit Merah Hiking Trail", "Bukit Papan", "Bukit Weh",
        "Wang Kelian Sunday Market", "Padang Warehouse Zone", "Kuala Perlis Ikan Bakar",
        "Hai Thien Seafood Village", "Capati Arau", "Laksa Kak Su",
        "Restoran Sarang Burung", "Anjung Keli", "Masjid Negeri Perlis"
    ],

    "Kelantan": [
        "Pantai Cahaya Bulan", "Masjid Muhammadi", "Siti Khadijah Market",
        "Muzium Negeri Kelantan", "Istana Jahar", "Istana Batu",
        "Handicraft Village and Craft Museum", "Pantai Irama Bachok",
        "Gunung Stong State Park", "Gua Ikan", "Gua Musang Town",
        "Wat Photivihan (Reclining Buddha)", "Wat Machimmaram (Sitting Buddha)",
        "Beijing Mosque Rantau Panjang", "Lata Rek", "Lata Berangin",
        "Min House Camp", "Pantai Melawi", "Tok Bali Beach", "Pantai Bisikan Bayu",
        "Gunung Ayam", "Gua Bewah (border Terengganu)", "Rantau Panjang Duty Free Zone",
        "Pengkalan Kubor", "Kampung Laut Floating Mosque", "Tambatan Diraja",
        "Wakaf Che Yeh Night Market", "Gelanggang Seni",
        "Jeram Linang Waterfall", "Lata Beringin", "Gunung Chamah",
        "Mount Reng", "Kubang Kerian Mosque", "Tumpat Cultural Village",
        "Kampung Laut Heritage Village", "Pantai Senok Lighthouse",
        "Pantai Geting", "Pantai Perupok", "Lata Keding", "Bukit Panau",
        "Bunut Susu", "Pantai Batu Kandis", "Kuala Krai Mini Zoo",
        "Lata Mek", "Lata Belatan (border)", "Pasar Malam Wakaf Bharu",
        "Kota Bharu Cultural Zone", "Kemubu Waterfall", "Lata Tembakah",
        "Jelawang Waterfall", "Stong Hill Resort", "Dabong Train Station",
        "Gua Pagar", "Gua Gelap", "Gua Kris",
        "Taman Etnobotani Gua Musang", "Masjid Tengku Razaleigh", "Galeri Kuala Krai",
        "Tangga Bradley", "Jambatan Guillemard", "Lata Hujan",
        "Lata Turbo", "Jeram Mengaji", "Tok Aman Bali Beach Resort",
        "Villa Danialla Beach Resort", "Pantai Sri Tujuh", "Muzium Wau",
        "Muzium Perang (Bank Kerapu)", "Muzium Islam", "Muzium Diraja Istana Batu",
        "Buluh Kubu Bazaar", "Pasar Besar Siti Khadijah (Upper levels)", "Nasi Kukus Kebun Sultan",
        "Kopitiam Kita", "White House Kopitiam", "Masjid Al-Ismaili",
        "Wat Phikulyai", "Wat Mai Suwan Khiri", "Dragon Boat Temple (Wat Chonprachumthat)",
        "Pengkalan Kubor Duty Free", "Lata Y", "Jeram Pasu",
        "Lata Chenulang", "Kolam Air Panas Tok Bok", "Kolam Air Panas Jeli",
        "Gunung Reng", "Perkampungan Kraftangan", "Kampung Kraftangan",
        "Pantai Nami (Senok)", "Pantai Kemayang", "Pantai Sabak",
        "Rumah Api Pantai Senok", "Jambatan Sultan Yahya Petra", "Menara Jam Tambatan Diraja",
        "Street Art Kota Bharu", "Laman Siti Khadijah", "AEON Mall Kota Bharu",
        "KB Mall", "Pasar Terapung Pengkalan Datu", "Cerana Villa Resort",
        "Moon Beach (Pantai Cahaya Bulan)"
    ],

    "Terengganu": [
        "Kuala Terengganu Crystal Mosque", "Terengganu Drawbridge",
        "Pulau Redang", "Pulau Perhentian", "Pulau Kapas",
        "Tengku Tengah Zaharah Floating Mosque", "Kuala Terengganu Chinatown",
        "Payang Market", "Taman Tamadun Islam", "Batu Buruk Beach",
        "Kenyir Lake", "Kelah Sanctuary Sungai Petang", "Kenyir Elephant Village",
        "Bukit Besar Trail", "Pantai Penarik", "Pantai Kemasik",
        "Lata Tembakah", "Sekayu Waterfall", "Lang Tengah Island", "Gem Island",
        "Marang Jetty", "Masjid Abidin", "Terengganu State Museum",
        "Kuala Terengganu Waterfront", "Pulau Duyong", "Noor Arfa Craft Complex",
        "Rantau Abang Turtle Beach", "Pantai Teluk Bidara", "Bukit Keluang",
        "Kapas Coral Beach", "Kuala Berang Market", "Cheneh Hot Spring",
        "Rhu Sepuluh Beach", "Faidhi Mangrove Tour", "Mak Ngah Nasi Dagang",
        "Pantai Batu Pelanduk", "Tinggi Island", "Tanjung Jara Beach",
        "Setiu Wetlands", "Kampung Losong Keropok Lekor", "KTCC Mall",
        "Kuala Terengganu Golf Resort", "Waterfront Heritage Park",
        "Seberang Takir Walkway", "Pantai Teluk Lipat", "Pantai Bukit Keluang",
        "Sekayu River Park", "Lata Serambi", "Kolok Waterfall",
        "Pasar Payang 2 (New)", "Bukit Puteri", "Istana Maziah",
        "Maziah Garden", "Pulau Warisan", "Kota Lama Duyong",
        "Galeri Seni Wawasan", "Pusat Sains & Kreativiti Terengganu", "Kompleks Kraf Noor Arfa",
        "Pantai Pandak", "Pantai Teluk Ketapang", "Pantai Tok Jembal",
        "Miami Beach Terengganu", "Warung Pok Nong (Ikan Celup Tepung)", "Nasi Dagang Atas Tol",
        "Lata Belatan", "La Hot Spring", "Gunung Tebu",
        "Pulau Perhentian Kecil", "Pulau Perhentian Besar", "Long Beach (Perhentian)",
        "Coral Bay (Perhentian)", "Marine Park Redang", "Chagar Hutang Turtle Sanctuary",
        "Pantai Pasir Panjang (Redang)", "Bidong Island", "Pulau Tenggol",
        "Dungun Night Market", "China Town Dungun", "Rimula Park",
        "Pantai Teluk Mak Nik", "Monica Bay", "Kemaman Zoo",
        "Kemaman Coffee (Hai Peng)", "Pantai Chendor (Border)", "Bakara Coffee",
        "Mesra Mall", "Kenyir Water Park", "Lasir Waterfall",
        "Saok Waterfall", "Bewah Cave", "Taat Cave",
        "Herbal Park Kenyir", "Tropical Garden Kenyir", "Orchid Garden Kenyir",
        "Butterfly Park Kenyir", "Hutan Lipur Chemerong", "Chemerong Waterfall",
        "Gunung Berembun", "Sungai Loh", "Jeram Lesung"
    ],

    "Sabah": [
        "Mount Kinabalu", "Kinabalu Park", "Poring Hot Springs",
        "Kundasang Desa Dairy Farm", "Kota Kinabalu Waterfront",
        "Tunku Abdul Rahman Marine Park", "Manukan Island",
        "Mamutik Island", "Sapi Island", "Gaya Island",
        "Mari-Mari Cultural Village", "Kota Kinabalu City Mosque",
        "Signal Hill Observatory", "Sabah State Museum",
        "Tagal Tinopikon Park", "Kundasang War Memorial", "Mesilau Nature Park",
        "Sabah Tea Garden", "Kokol Hill", "Lok Kawi Wildlife Park",
        "Sepilok Orangutan Rehabilitation Centre", "Bornean Sun Bear Conservation Centre",
        "Sandakan Rainforest Discovery Centre", "Labuk Bay Proboscis Monkey Sanctuary",
        "Turtle Islands Park", "Danum Valley", "Maliau Basin",
        "Sipadan Island", "Mabul Island", "Kapalai Island",
        "Kinabatangan River Safari", "Gomantong Caves",
        "Tawau Hills Park", "Bohey Dulang Island", "Tun Sakaran Marine Park",
        "Mataking Island", "Tambunan Rafflesia Reserve", "Kudat Tip of Borneo",
        "Tanjung Simpang Mengayau", "Tanjung Aru Beach",
        "Imago Shopping Mall", "Oceanus Waterfront Mall", "Kota Belud Market",
        "Sabandar Beach", "Sinsuron Hill", "Crocker Range Park",
        "Monsopiad Cultural Village", "Kiulu White Water Rafting",
        "Padas White Water Rafting", "North Borneo Railway", "Klias River Cruise",
        "Weston Wetland Park", "Kampung Sembulan", "Atkinson Clock Tower",
        "Pillars of Sabah", "Gaya Street Sunday Market", "Handicraft Market (Filipino Market)",
        "Suria Sabah", "Jesselton Point", "Perdana Park",
        "Polumpung Melangkap View Camp", "Tegudon Tourism Village", "Ranau Rabbit Farm",
        "Maragang Hill", "Sosodikon Hill", "Bombon Kg. Marakau",
        "Fish Massage Kg. Luanti", "Arnab Village Ranau", "Poring Canopy Walkway",
        "Langanan Waterfall", "Kipandi Butterfly Park", "Mahua Waterfall",
        "Tenom Coffee Park", "Sabah Agriculture Park (Tenom)", "Murut Cultural Centre",
        "Long Pasia", "Rungus Longhouse", "Sumangkap Gong Village",
        "Gombizau Honey Bee Farm", "Bavanggazo Longhouse", "Kelambu Beach",
        "Tindakon Dazang Beach", "Agnes Keith House", "Sandakan Memorial Park",
        "Puu Jih Shih Temple", "St. Michael's and All Angels Church", "English Tea House Sandakan",
        "Sim Sim Water Village", "Berhala Island", "Teck Guan Cocoa Museum",
        "Bukit Gemok", "Pasar Tanjung Tawau", "Balung River Eco Resort",
        "Semporna Proboscis Monkey River Cruise", "Bukit Tengkorak", "Sibuan Island",
        "Mantabuan Island", "Pom Pom Island", "Lankayan Island",
        "Tabin Wildlife Reserve", "Madai Caves"
    ],

    "Sarawak": [
        "Mulu Caves (UNESCO)", "Niah Caves", "Bako National Park",
        "Kuching Waterfront", "Darul Hana Bridge", "Astana Negeri",
        "Sarawak Cultural Village", "Mount Santubong", "Semenggoh Wildlife Centre",
        "Kuching Cat Museum", "Sarawak Museum Complex", "Wind Cave",
        "Fairy Cave", "Gunung Gading National Park", "Tanjung Datu National Park",
        "Damai Beach", "Annah Rais Hot Springs", "Bau Blue Lake",
        "Borneo Cultures Museum", "India Street Kuching", "Carpenter Street",
        "Gunung Mulu National Park", "Miri Canada Hill", "Tusan Beach (Cliff)",
        "Lambir Hills National Park", "Coco Cabana Miri", "Piasau Nature Reserve",
        "Sibu Night Market", "Sibu Central Market", "Bukit Lima Forest Park",
        "Mukah Kaul Festival Grounds", "Belawai Beach", "Sarikei Clock Tower",
        "Bintulu Similajau National Park", "Kampung Budaya Sarawak Living Museum",
        "Matang Wildlife Centre", "Kubah National Park", "Gunung Serapi",
        "Telok Melano Beach", "Lawas Tamu Market", "Limbang Plaza",
        "Miri Handicraft Centre", "Sempadi Lake", "Pantai Bungai",
        "Teluk Batik (border)", "Gunung Buri", "Kampung Bidayuh Traditions",
        "Fort Margherita", "Square Tower", "Chinese History Museum",
        "Textile Museum Sarawak", "Brooke Gallery", "Old Court House",
        "Kuching Mosque (Masjid Lama)", "Tua Pek Kong Temple Kuching", "Satok Weekend Market",
        "Medan Niaga Satok", "Top Spot Seafood", "Main Bazaar",
        "Jong's Crocodile Farm", "Serikin Border Market", "Ranchan Pool",
        "Tasik Biru Bau", "Siniawan Night Market", "Paku Rock Maze Garden",
        "Libiki Bamboo Resort", "Permai Rainforest Resort", "Santubong Jungle Trek",
        "Telaga Air", "Wetlands National Park", "Batang Ai National Park",
        "Fort Alice (Sri Aman)", "Taman Panorama Benak", "Wong Nai Siong Memorial Garden",
        "Sibu Heritage Centre", "Tua Pek Kong Temple Sibu", "Lau King Howe Hospital Museum",
        "Sungai Merah Heritage Walk", "Sibu Engkalat Longhouse", "Bawang Assan Longhouse",
        "Kapit Fort Sylvia", "Kapit Market", "Pelagus Rapids",
        "Grand Old Lady (No. 1 Oil Well)", "Petroleum Museum Miri", "Miri City Fan",
        "Taman Selera", "Luak Bay Esplanade", "Niah National Park",
        "Painted Cave Niah", "Loagan Bunut National Park", "Pulau Talang-Talang",
        "Sematan Beach", "Lundu Town", "Gunung Mulu Canopy Walk",
        "Deer Cave", "Lang Cave", "Clearwater Cave",
        "Wind Cave (Mulu)", "Pinnacles of Mulu", "Headhunter's Trail",
        "Bario Highlands", "Ba'kelalan", "Pulau Bruit",
        "Mukah Sago Factory", "Lamin Dana Cultural Lodge", "Taman Tumbina Bintulu"
    ],

    "Labuan": [
        "Labuan Financial Park", "Labuan Chimney Museum",
        "Labuan Marine Museum", "Labuan War Cemetery",
        "Labuan Bird Park", "Labuan Square", "Papan Island",
        "Rusukan Besar Island", "Pulau Kuraman", "Ujana Kewangan Mall",
        "Peace Park", "Surrender Point", "Labuan Clock Tower",
        "Labuan Botanical Garden", "Labuan Beach", "Tanjung Kubong Tunnel",
        "Labuan International Sea Sport Complex", "Labuan Golf Club",
        "Patau-Patau Water Village", "Nagoya Beach", "Layang-Layang Island",
        "Labuan Central Market", "Tiara Labuan Hotel", "Layangan Beach",
        "Pohon Batu Beach", "Lubuk Temiang Water Recreation", "Labuan Museum",
        "Sungai Miri Wetlands", "Labuan Iris Garden", "Labuan Mosque",
        "Palm Beach Resort", "Labuan International Ferry Terminal",
        "Manikar Beach", "Seri Malaka Beach", "Kampung Air Labuan",
        "Labuan Light House", "Labuan WWII Memorial", "Brown Beach",
        "Marine Park Labuan", "Kampung Ganggarak", "Kampung Bukit Kuda",
        "Labuan Marina", "Labuan Market Food Court", "Botanical Park Trail",
        "Palm Mall Labuan", "Taman Damai", "Patau-Patau Floating Village",
        "United Nations Beach", "Batu Manikar Beach", "Pancur Hitam Beach",
        "Sungai Labu Beach", "Sungai Pagar", "Tanjung Aru Beach (Labuan)",
        "Mawilla Yacht Club", "Kampung Bebuloh Water Village", "An'Nur Jamek Mosque",
        "Gurdwara Sahib Labuan", "Kwong Fook Kung Temple", "Ba Xian Miao (Eight Immortals Temple)",
        "The 9 Kings Temple", "Heavenly Queen Temple", "Labuan Church of the Blessed Sacrament",
        "Tanjung Purun", "Kinabenuwa Mangrove Forest", "Kina Benuwa Wetland",
        "Beting Lintang", "Cement Wreck (Diving)", "Blue Water Wreck (Diving)",
        "Australian Wreck (Diving)", "American Wreck (Diving)", "Rusukan Kecil Island",
        "Pulau Daat", "Pulau Burung", "Ramsey Point",
        "Labuan Matriculation College Viewpoint", "Kampung Lajau", "Kampung Pantai",
        "Labuan Taoist Temple", "Naval Museum (Pusat Sejarah)", "Labuan Duty Free Shops",
        "Chocolate Valley", "Sky Garden Labuan", "One Stop Duty Free",
        "Utama Jaya Superstore", "Milimewah Superstore", "Labuan Liberty Port",
        "Asian Supply Base", "Victoria Arms Hotel (Historical Site)", "Hotel Labuan (Abandoned Landmark)",
        "Bata Merah Beach", "Fisheries Department Aquarium", "Taman Mutiara",
        "Taman Perumahan Mutiara", "Masjid Jamek An-Nur", "Kampung Sungai Keling",
        "Labuan Futsal Court", "Labuan Sports Complex", "Dataran Labuan Stage",
        "Wakaf Beruas", "Kerupuk Lekor Labuan Stalls", "Coconut Shake Labuan Stalls",
        "Labuan Sea Sports Centre", "Kampung Gersik", "Batu Arang Heritage Site",
        "Coal Mine Tunnels"
    ]
}


class POIEnricher:
    """Enriches POI data with popularity scores"""
    
    def __init__(self, data_path: str = "data"):
        """Initialize the enricher"""
        self.data_path = Path(data_path)
        self.sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
        self.sparql.setReturnFormat(SPARQL_JSON)
        
        # Cache for Wikidata results
        self.wikidata_cache = {}
        
        # Statistics
        self.stats = {
            "total_golden_pois": 0,
            "matched_golden_pois": 0,
            "missing_golden_pois": [],
            "wikidata_queries": 0
        }
        
    def find_poi_in_dataset(self, golden_poi_name: str, state: str, pois: List[Dict]) -> Optional[Dict]:
        """
        Find a golden list POI in the dataset using exact and fuzzy matching
        
        Args:
            golden_poi_name: Name from the golden list
            state: State where POI should be located
            pois: List of all POIs from JSON
            
        Returns:
            Matched POI dict or None
        """
        # Try exact match first (case-insensitive)
        for poi in pois:
            if (poi.get("state", "").lower() == state.lower() and 
                poi.get("name", "").lower() == golden_poi_name.lower()):
                return poi
        
        # Try fuzzy matching within the same state
        for poi in pois:
            if poi.get("state", "").lower() == state.lower():
                similarity = fuzz.ratio(
                    poi.get("name", "").lower(), 
                    golden_poi_name.lower()
                )
                if similarity >= 65:  # 65% similarity threshold
                    return poi
        
        return None
    
    def build_golden_poi_index(self, pois: List[Dict]) -> Dict[str, Dict]:
        """
        Build an index of golden POIs that exist in the dataset
        
        Args:
            pois: List of all POIs from JSON
            
        Returns:
            Dictionary mapping (state, poi_id) to POI data with Wikidata enrichment
        """
        golden_index = {}
        
        print("\n" + "="*80)
        print("PHASE 1: VALIDATING GOLDEN LIST AGAINST DATASET")
        print("="*80 + "\n")
        
        for state, attractions in TOP_POIS_MALAYSIA.items():
            self.stats["total_golden_pois"] += len(attractions)
            
            print(f"\n📍 {state} ({len(attractions)} golden POIs)")
            print("-" * 80)
            
            for golden_poi_name in attractions:
                # Try to find this golden POI in the dataset
                matched_poi = self.find_poi_in_dataset(golden_poi_name, state, pois)
                
                if matched_poi:
                    self.stats["matched_golden_pois"] += 1
                    
                    # Query Wikidata for this golden POI
                    print(f"  ✓ Found: {golden_poi_name}")
                    print(f"    → Matched to: {matched_poi['name']}")
                    
                    sitelinks = self.query_wikidata_sitelinks(
                        matched_poi["name"],
                        matched_poi["lat"],
                        matched_poi["lon"]
                    )
                    
                    self.stats["wikidata_queries"] += 1
                    
                    # Store in index
                    key = (state, matched_poi["id"])
                    golden_index[key] = {
                        "golden_name": golden_poi_name,
                        "dataset_name": matched_poi["name"],
                        "wikidata_sitelinks": sitelinks,
                        "poi_id": matched_poi["id"]
                    }
                    
                    print(f"    → Wikidata: {sitelinks} sitelinks")
                    
                else:
                    print(f"  ✗ Missing: {golden_poi_name}")
                    self.stats["missing_golden_pois"].append({
                        "state": state,
                        "name": golden_poi_name
                    })
                
                # Rate limiting
                time.sleep(0.5)
        
        # Print summary
        print("\n" + "="*80)
        print("GOLDEN LIST VALIDATION SUMMARY")
        print("="*80)
        print(f"Total golden POIs in list: {self.stats['total_golden_pois']}")
        print(f"Found in dataset: {self.stats['matched_golden_pois']}")
        print(f"Missing from dataset: {len(self.stats['missing_golden_pois'])}")
        print(f"Match rate: {(self.stats['matched_golden_pois']/self.stats['total_golden_pois']*100):.1f}%")
        print(f"Wikidata queries made: {self.stats['wikidata_queries']}")
        print("="*80 + "\n")
        
        return golden_index
    
    def query_wikidata_sitelinks(self, poi_name: str, lat: float, lon: float) -> int:
        """
        Query Wikidata for sitelinks count
        
        Args:
            poi_name: Name of the POI
            lat: Latitude
            lon: Longitude
            
        Returns:
            Number of sitelinks (0 if not found)
        """
        try:
            # SPARQL query to find entity by name and coordinates
            query = f"""
            SELECT ?item ?sitelinks WHERE {{
              ?item rdfs:label "{poi_name}"@en.
              ?item wdt:P625 ?coord.
              ?item wikibase:sitelinks ?sitelinks.
              
              FILTER(geof:distance(?coord, "Point({lon} {lat})"^^geo:wktLiteral) < 10)
            }}
            LIMIT 1
            """
            
            self.sparql.setQuery(query)
            results = self.sparql.query().convert()
            
            if results["results"]["bindings"]:
                sitelinks = int(results["results"]["bindings"][0]["sitelinks"]["value"])
                return sitelinks
            
            # Try without coordinates if no match
            query_simple = f"""
            SELECT ?item ?sitelinks WHERE {{
              ?item rdfs:label "{poi_name}"@en.
              ?item wikibase:sitelinks ?sitelinks.
            }}
            LIMIT 1
            """
            
            self.sparql.setQuery(query_simple)
            results = self.sparql.query().convert()
            
            if results["results"]["bindings"]:
                sitelinks = int(results["results"]["bindings"][0]["sitelinks"]["value"])
                return sitelinks
                
            return 0
            
        except Exception as e:
            print(f"    ⚠ Wikidata error for '{poi_name}': {e}")
            return 0
    
    def calculate_popularity_score(self, poi: Dict, golden_index: Dict) -> Tuple[int, Dict]:
        """
        Calculate popularity score for a POI using prebuilt golden index
        
        Scoring Logic (Golden List Priority):
        - Golden list membership: 70 points (local knowledge & tourist relevance)
        - Wikidata sitelinks: +2 points each (international recognition bonus)
        - Non-golden POIs: 0 points
        
        Args:
            poi: POI dictionary
            golden_index: Prebuilt index of golden POIs with Wikidata data
            
        Returns:
            Tuple of (score, metadata dict)
        """
        score = 0
        metadata = {
            "wikidata_sitelinks": 0,
            "in_golden_list": False
        }
        
        poi_id = poi.get("id")
        state = poi.get("state", "")
        poi_name = poi.get("name", "")
        lat = poi.get("lat", 0)
        lon = poi.get("lon", 0)
        
        # Check if this POI is in the golden index
        key = (state, poi_id)
        if key in golden_index:
            golden_data = golden_index[key]
            
            # This is a golden POI - use cached Wikidata data
            metadata["wikidata_sitelinks"] = golden_data["wikidata_sitelinks"]
            metadata["in_golden_list"] = True
            
            # Golden list base score (70 points - primary signal)
            score = 70
            
            # Wikidata bonus (×2 multiplier - validation signal)
            if golden_data["wikidata_sitelinks"] > 0:
                score += (golden_data["wikidata_sitelinks"] * 2)
        else:
            # Regular POI - score remains 0
            score = 0
        
        return score, metadata
    
    def enrich_pois(self, input_file: str, output_file: str, limit: Optional[int] = None):
        """
        Enrich POIs with popularity scores
        
        Args:
            input_file: Input JSON file path
            output_file: Output JSON file path
            limit: Optional limit for testing (process only N POIs)
        """
        input_path = self.data_path / input_file
        output_path = self.data_path / output_file
        
        print(f"Loading POIs from {input_path}...")
        
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        pois = data.get('pois', [])
        total_pois = len(pois)
        
        print(f"Total POIs in dataset: {total_pois}")
        
        # PHASE 1: Build golden POI index (validate + query Wikidata)
        golden_index = self.build_golden_poi_index(pois)
        
        # PHASE 2: Enrich all POIs using the golden index
        print("\n" + "="*80)
        print("PHASE 2: ENRICHING ALL POIs")
        print("="*80 + "\n")
        
        if limit:
            pois = pois[:limit]
            print(f"Processing {limit} POIs (limited for testing)...\n")
        else:
            print(f"Processing all {total_pois} POIs...\n")
        
        enriched_pois = []
        golden_count = 0
        
        for idx, poi in enumerate(pois, 1):
            if idx % 1000 == 0:
                print(f"Progress: {idx}/{len(pois)} POIs processed ({golden_count} golden so far)")
            
            score, metadata = self.calculate_popularity_score(poi, golden_index)
            
            if metadata["in_golden_list"]:
                golden_count += 1
            
            # Add enrichment data to POI
            enriched_poi = {
                **poi,
                "popularity_score": score,
                "wikidata_sitelinks": metadata["wikidata_sitelinks"],
                "in_golden_list": metadata["in_golden_list"]
            }
            enriched_pois.append(enriched_poi)
        
        # Save enriched data
        output_data = {
            "metadata": {
                **data.get("metadata", {}),
                "enriched": True,
                "total_pois": len(enriched_pois),
                "golden_pois_found": golden_count,
                "golden_pois_missing": len(self.stats["missing_golden_pois"]),
                "wikidata_queries": self.stats["wikidata_queries"]
            },
            "pois": enriched_pois
        }
        
        # Save missing golden POIs report
        if self.stats["missing_golden_pois"]:
            missing_report_path = self.data_path / "missing_golden_pois_report.json"
            with open(missing_report_path, 'w', encoding='utf-8') as f:
                json.dump(self.stats["missing_golden_pois"], f, indent=2, ensure_ascii=False)
            print(f"\n📋 Missing POIs report saved to {missing_report_path}")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Enriched data saved to {output_path}")
        print(f"\n" + "="*80)
        print("ENRICHMENT SUMMARY")
        print("="*80)
        print(f"Total POIs processed: {len(enriched_pois)}")
        print(f"Golden POIs found in dataset: {golden_count}")
        print(f"Regular POIs (score=0): {len(enriched_pois) - golden_count}")
        print(f"Wikidata queries made: {self.stats['wikidata_queries']}")
        print("="*80)


def main():
    """Main enrichment function"""
    enricher = POIEnricher(data_path="data")
    
    # For testing: enrich only first 10 POIs
    # enricher.enrich_pois(
    #     input_file='malaysia_all_pois_processed.json',
    #     output_file='malaysia_all_pois_enriched.json',
    #     limit=10
    # )
    
    # For full enrichment (remove limit parameter)
    enricher.enrich_pois(
        input_file='malaysia_all_pois_processed.json',
        output_file='malaysia_all_pois_enriched.json'
    )


if __name__ == "__main__":
    main()
