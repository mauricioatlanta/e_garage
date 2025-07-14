import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from taller.models.marca import Marca

marcas_y_modelos = {
    "Acura": ["Integra", "Legend", "RL", "TL", "RSX", "MDX", "RDX", "TSX", "ILX", "NSX", "ZDX", "TLX", "RLX"],
    "Alfa Romeo": ["Alfasud", "Alfetta", "Giulietta", "33", "75", "164", "Spider", "GTV", "145", "146", "156", "166", "147", "GT", "Brera", "MiTo", "Giulietta", "Giulia", "Stelvio"],
    "AMC": ["Gremlin", "Pacer", "Hornet", "Concord", "Spirit", "Eagle", "Javelin", "Matador", "Rebel", "AMX"],
    "Asia Motors": ["Rocsta", "Towner", "Topic", "Retona", "Combi", "AM825"],
    "Audi": ["50", "80", "90", "100", "200", "A1", "A3", "A4", "A5", "A6", "A7", "A8", "Q2", "Q3", "Q5", "Q7", "Q8", "TT", "R8", "e-tron", "RS3", "RS4", "RS5", "RS6", "RS7", "S3", "S4", "S5", "S6", "S7", "S8"],
    "Austin": ["Mini", "Allegro", "Maestro", "Montego", "Maxi", "Metro", "Princess", "1100", "1300", "1800", "Healey", "A40", "A50", "A60", "A90", "A99", "A135", "Seven", "Cambridge"],
    "BAIC": ["X25", "X35", "X55", "X65", "BJ20", "BJ40", "BJ80", "D20", "EU5", "EX360", "M20", "M50S"],
    "Bentley": ["Arnage", "Azure", "Bentayga", "Brooklands", "Continental GT", "Continental Flying Spur", "Flying Spur", "Mulsanne", "Turbo R"],
    "BMW": ["Serie 1", "Serie 2", "Serie 3", "Serie 4", "Serie 5", "Serie 6", "Serie 7", "Serie 8", "X1", "X2", "X3", "X4", "X5", "X6", "X7", "Z3", "Z4", "Z8", "M2", "M3", "M4", "M5", "M6", "M8", "i3", "i4", "i8", "iX", "iX3"],
    "Brilliance": ["FRV", "FSV", "H230", "H320", "H530", "M1", "M2", "V3", "V5", "V6"],
    "Bugatti": ["EB110", "Veyron", "Chiron", "Divo", "Centodieci", "Bolide", "Mistral"],
    "Buick": ["Century", "Electra", "Enclave", "Encore", "Envision", "Invicta", "Lacrosse", "LeSabre", "Park Avenue", "Regal", "Rendezvous", "Reatta", "Roadmaster", "Riviera", "Skylark", "Special", "Verano", "Wildcat"],
    "BYD": ["F0", "F3", "F6", "G3", "G5", "G6", "S6", "S7", "Tang", "Qin", "Yuan", "Song", "Han", "Dolphin", "Seal", "e2", "e3", "e5", "T3"],
    "Cadillac": ["ATS", "CT4", "CT5", "CT6", "CTS", "DeVille", "DTS", "Eldorado", "Escalade", "Lyriq", "Seville", "SRX", "STS", "XT4", "XT5", "XT6", "XTS"],
    "Changan": ["Alsvin", "Benni", "CS15", "CS35", "CS55", "CS75", "CS85", "CS95", "Eado", "Hunter", "Raeton", "UNI-K", "UNI-T"],
    "Chery": ["QQ", "Tiggo 2", "Tiggo 3", "Tiggo 4", "Tiggo 7", "Tiggo 8", "Arrizo 3", "Arrizo 5", "Arrizo 6", "Arrizo 7", "Fulwin", "Cowin", "A1", "A3", "E5"],
    "Chevrolet": ["Aveo", "Blazer", "Camaro", "Captiva", "Cavalier", "Celta", "Cobalt", "Colorado", "Corvette", "Cruze", "Equinox", "Grand Vitara", "Impala", "Malibu", "Montana", "Onix", "Orlando", "S10", "Sail", "Silverado", "Sonic", "Spark", "Spin", "Suburban", "Tahoe", "Tracker", "Trailblazer", "Traverse", "Trax", "Vectra", "Zafira"],
    "Chrysler": ["300", "300C", "Aspen", "Cirrus", "Concorde", "Crossfire", "Imperial", "LeBaron", "Neon", "New Yorker", "Pacifica", "PT Cruiser", "Sebring", "Stratus", "Town & Country", "Voyager"],
    "Cupra": ["Ateca", "Born", "Formentor", "Leon", "Tavascan", "Terramar"],
    "Dacia": ["1300", "Dokker", "Duster", "Jogger", "Lodgy", "Logan", "Sandero", "Spring"],
    "Daewoo": ["Cielo", "Espero", "Evanda", "Kalos", "Lacetti", "Lanos", "Leganza", "LeMans", "Matiz", "Musso", "Nexia", "Nubira", "Prince", "Racer", "Rezzo", "Tacuma", "Tico"],
    "Daihatsu": ["Applause", "Charade", "Copen", "Cuore", "Feroza", "Gran Move", "Hijet", "Materia", "Mira", "Rocky", "Sirion", "Terios", "YRV"],
    "Datsun": ["120Y", "160J", "240Z", "280ZX", "510", "720", "Bluebird", "Cherry", "GO", "Laurel", "Stanza", "Sunny", "Violet"],
    "Dodge": ["Attitude", "Avenger", "Caliber", "Caravan", "Challenger", "Charger", "Dakota", "Dart", "Durango", "Grand Caravan", "Journey", "Magnum", "Neon", "Nitro", "Ram", "Stratus", "Viper"],
    "Dongfeng": ["AX4", "AX5", "AX7", "DX3", "DX7", "Rich", "S30", "T5 Evo"],
    "Ford": ["Bronco", "EcoSport", "Edge", "Escape", "Everest", "Expedition", "Explorer", "F-150", "F-250", "Fiesta", "Focus", "Fusion", "Ka", "Maverick", "Mustang", "Ranger", "S-Max", "Super Duty", "Taurus", "Territory", "Transit"],
    "Effa": ["Aojun", "Plutus", "V22", "V25", "Cargo Van", "Pick-Up"],
    "FAW": ["Besturn B50", "Besturn X40", "J6", "Oley", "T77", "V2", "V5", "X-PV"],
    "Ferrari": ["296 GTB", "348", "355", "360 Modena", "430 Scuderia","458 Italia", "488 GTB", "512 TR", "550 Maranello", "575M", "599 GTB Fiorano", "612 Scaglietti", "California", "F12berlinetta", "F40", "F50", "F8 Tributo", "GTC4Lusso", "LaFerrari", "Portofino", "Roma", "SF90 Stradale"],
    "Fiat": ["500", "500X", "Argo", "Bravo", "Cronos", "Ducato", "Fiorino", "Grand Siena", "Idea", "Marea", "Palio", "Panda", "Punto", "Qubo", "Siena", "Strada", "Tipo", "Uno"],
    "Foton": ["Sauvana", "Tunland", "View CS2", "View CS2L", "View V5", "View V7"],
    "Geely": ["CK", "Emgrand 7", "Emgrand X7", "GC6", "GX3", "MK", "Monjaro", "Okavango", "Tugella"],
    "Genesis": ["G70", "G80", "G90", "GV60", "GV70", "GV80"],
    "GMC": ["Acadia", "Canyon", "Envoy", "Savana", "Sierra", "Terrain", "Yukon"],
    "Great Wall": ["Coolbear", "Florid", "Haval H1", "Haval H2", "Haval H6", "Haval H9", "Poer", "Steed 5", "Steed 6", "Steed 7", "Voleex C30", "Wingle 5", "Wingle 6", "Wingle 7"],
    "Haima": ["2", "3", "7X", "M3", "S5"],
    "Haval": ["H1", "H2", "H6", "H6 Coupé", "H7", "H8", "H9", "Jolion", "Big Dog"],
    "Honda": ["Accord", "BR-V", "City", "Civic", "CR-V", "Fit", "HR-V", "Integra", "Legend", "Odyssey", "Passport", "Pilot", "Prelude", "Ridgeline", "S2000", "Stream"],
    "Hyundai": ["Accent", "Atos", "Avante", "Creta", "Elantra", "Galloper", "Genesis", "Grand i10", "H1", "i10", "i20", "i30", "i40", "Kona", "Palisade", "Santa Fe", "Sonata", "Staria", "Tucson", "Veloster", "Venue"],
    "Infiniti": ["EX35", "FX35", "FX50", "G35", "JX35", "M37", "Q30", "Q50", "Q60", "Q70", "QX30", "QX50", "QX56", "QX60", "QX70", "QX80"],
    "Isuzu": ["D-Max", "MU-X", "Rodeo", "Trooper", "VehiCROSS", "Wizard"],
    "Iveco": ["Daily", "Eurocargo", "Stralis", "Trakker"],
    "JAC": ["J2", "J3", "J4", "J5", "Refine", "S2", "S3", "S4", "S5", "S7", "T6", "T8"],
    "Jaguar": ["E-Pace", "F-Pace", "F-Type", "I-Pace", "S-Type", "X-Type", "XE", "XF", "XJ", "XK"],
    "Jeep": ["Cherokee", "Commander", "Compass", "Gladiator", "Grand Cherokee", "Patriot", "Renegade", "Wagoneer", "Wrangler"],
    "Jetour": ["Dashing", "X70", "X70 Plus", "X90"],
    "JMC": ["Baodian", "Conquer", "Vigus", "Yuhu", "Teshun"],
    "Jonway": ["A380", "Mistral", "UFO"],
    "Kia": ["Carens", "Carnival", "Ceed", "Cerato", "EV6", "K2700", "Mohave", "Morning", "Niro", "Opirus", "Optima", "Picanto", "Rio", "Seltos", "Sorento", "Soul", "Sportage", "Stinger", "Stonic", "Telluride"],
    "King Long": ["Kingwin", "XMQ6129", "XMQ6900", "XMQ6996"],
    "Koenigsegg": ["Agera", "CC8S", "CCGT", "CCR", "CCX", "Gemera", "Jesko", "One:1", "Regera"],
    "Lada": ["2101", "2104", "2105", "2107", "Granta", "Kalina", "Largus", "Niva", "Samara", "Vesta", "XRAY"],
    "Lamborghini": ["Aventador", "Countach", "Diablo", "Espada", "Gallardo", "Huracán", "Miura", "Murciélago", "Reventón", "Sian", "Urus", "Veneno"],
    "Lancia": ["Beta", "Dedra", "Delta", "Fulvia", "Gamma", "Kappa", "Lybra", "Musa", "Prisma", "Stratos", "Thema", "Thesis", "Voyager", "Ypsilon", "Zeta"],
    "Land Rover": ["Defender", "Discovery", "Discovery Sport", "Freelander", "Range Rover", "Range Rover Evoque", "Range Rover Sport", "Range Rover Velar"],
    "Lexus": ["CT", "ES", "GS", "GX", "IS", "LC", "LS", "LX", "NX", "RC", "RX", "SC", "UX"],
    "Lifan": ["320", "520", "530", "620", "720", "Foison", "M7", "X50", "X60", "X70"],
    "Lincoln": ["Aviator", "Continental", "Corsair", "LS", "MKC", "MKS", "MKT", "MKX", "MKZ", "Navigator", "Town Car"],
    "Lotus": ["Elise", "Emira", "Esprit", "Evija", "Evora", "Exige"],
    "Mahindra": ["Bolero", "KUV100", "Marazzo", "Scorpio", "Thar", "TUV300", "XUV300", "XUV500", "XUV700"],
    "Maserati": ["3200 GT", "Ghibli", "GranCabrio", "GranTurismo", "Levante", "MC12", "MC20", "Quattroporte"],
    "Mazda": ["121", "2", "3", "6", "626", "929", "Atenza", "BT-50", "CX-3", "CX-30", "CX-5", "CX-7", "CX-9", "CX-90", "MX-3", "MX-5", "MX-6", "RX-7", "RX-8"],
    "McLaren": ["540C", "570S", "600LT", "620R", "650S", "675LT", "720S", "765LT", "Artura", "Elva", "GT", "P1", "Senna", "Speedtail"],
    "Mercedes-Benz": ["A-Class", "AMG GT", "B-Class", "C-Class", "CL-Class", "CLA-Class", "CLK-Class", "CLS-Class", "E-Class", "G-Class", "GL-Class", "GLA-Class", "GLB-Class", "GLC-Class", "GLE-Class", "GLK-Class", "GLS-Class", "M-Class", "R-Class", "S-Class", "SL-Class", "SLK-Class", "SLS AMG", "Sprinter", "V-Class"],
    "MG": ["3", "5", "6", "350", "550", "750", "ZS", "HS", "RX5", "Marvel R", "Extender"],
    "Mini": ["Cooper", "Cooper S", "Clubman", "Countryman", "Paceman", "Roadster"],
    "Mitsubishi": ["3000GT", "ASX", "Colt", "Eclipse", "Eclipse Cross", "Galant", "Grandis", "L200", "Lancer", "Mirage", "Montero", "Outlander", "Pajero", "Space Star"],
    "Morris": ["Eight", "Isis", "Marina", "Minor", "Oxford"],
    "Nissan": ["370Z", "Altima", "Armada", "Cube", "Frontier", "GT-R", "Juke", "Kicks", "Leaf", "March", "Maxima", "Murano", "Navara", "Note", "NP300", "Pathfinder", "Patrol", "Qashqai", "Rogue", "Sentra", "Tiida", "Versa", "X-Trail", "Xterra"],
    "Opel": ["Astra", "Corsa", "Grandland", "Insignia", "Kadett", "Mokka", "Vectra", "Zafira"],
    "Peugeot": ["104", "106", "107", "2008", "205", "206", "207", "208", "3008", "301", "306", "307", "308", "309", "405", "406", "407", "5008", "508", "607", "806", "807", "Partner", "Rifter"],
    "Polestar": ["1", "2", "3", "4", "5"],
    "Pontiac": ["Bonneville", "Fiero", "Firebird", "G3", "G5", "G6", "G8", "Grand Am", "Grand Prix", "Solstice", "Sunfire", "Torrent", "Trans Am", "Vibe"],
    "Porsche": ["356", "718 Boxster", "718 Cayman", "911", "918 Spyder", "924", "928", "944", "959", "968", "Cayenne", "Macan", "Panamera", "Taycan"],
    "Proton": ["Exora", "Gen-2", "Impian", "Persona", "Preve", "Saga", "Satria Neo", "Waja", "Wira"],
    "RAM": ["700", "1000", "1200", "1500", "2500", "3500", "ProMaster"],
    "Renault": ["4", "5", "9", "11", "12", "18", "19", "21", "Clio", "Duster", "Espace", "Fluence", "Kadjar", "Kangoo", "Koleos", "Laguna", "Logan", "Megane", "Safrane", "Sandero", "Scenic", "Symbol", "Talisman", "Twingo"],
    "Rolls-Royce": ["Corniche", "Cullinan", "Dawn", "Ghost", "Phantom", "Silver Cloud", "Silver Shadow", "Silver Spur", "Spectre", "Wraith"],
    "Rover": ["25", "45", "75", "100", "200", "400", "600", "800", "Metro", "Maestro", "Montego", "Streetwise"],
    "SAIC": ["Maxus T60", "Maxus T90", "Maxus D60", "Maxus Euniq 5", "Maxus V80", "Maxus G10"],
    "Seat": ["Alhambra", "Altea", "Arosa", "Cordoba", "Exeo", "Ibiza", "Leon", "Mii", "Tarraco", "Toledo"],
    "Scania": ["P-Series", "G-Series", "R-Series", "S-Series", "F-Series", "K-Series", "L-Series"],
    "Skoda": ["Citigo", "Fabia", "Kamiq", "Karoq", "Kodiaq", "Octavia", "Rapid", "Roomster", "Scala", "Superb", "Yeti"],
    "Smart": ["City-Coupe", "ForFour", "ForTwo", "Roadster"],
    "SsangYong": ["Actyon", "Korando", "Kyron", "Musso", "Rexton", "Rodius", "Stavic", "Tivoli", "XLV"],
    "Subaru": ["Baja", "BRZ", "Forester", "Impreza", "Justy", "Legacy", "Leone", "Levorg", "Outback", "SVX", "Tribeca", "WRX", "XT"],
    "Suzuki": ["Alto", "Baleno", "Celerio", "Ciaz", "Ertiga", "Esteem", "Forenza", "Grand Nomade", "Ignis", "Jimny", "Kizashi", "Liana", "Maruti", "S-Cross", "Samurai", "Splash", "Super Carry", "Swift", "SX4", "Vitara", "XL7"],
    "Tata": ["Indica", "Indigo", "Nano", "Safari", "Sumo", "Telcoline", "Tiago", "Tigor", "Xenon", "Zest"],
    "Tesla": ["Model 3", "Model S", "Model X", "Model Y", "Cybertruck", "Roadster", "Semi"],
    "Toyota": ["4Runner", "86", "Agya", "Avanza", "Avalon", "Camry", "Celica", "Corolla", "Cressida", "Etios", "FJ Cruiser", "Fortuner", "Hiace", "Highlander", "Hilux", "Land Cruiser", "MR2", "Paseo", "Prius", "RAV4", "Sequoia", "Sienna", "Supra", "Tacoma", "Tercel", "Tundra", "Venza", "Yaris"],
    "Volkswagen": ["Amarok", "Arteon", "Beetle", "Bora", "Caddy", "Caravelle", "CC", "Crafter", "EOS", "Fox", "Gol", "Golf", "ID.3", "ID.4", "ID.5", "ID. Buzz", "Jetta", "Kombi", "Lamando", "Lavida", "Multivan", "Parati", "Passat", "Phaeton", "Polo", "Santana", "Saveiro", "Scirocco", "Sharan", "T-Cross", "Taigo", "Tiguan", "Touareg", "Touran", "Up!", "Vento", "Virtus"],
    "Volvo": ["240", "740", "850", "940", "960", "C30", "C40", "C70", "S40", "S60", "S70", "S80", "S90", "V40", "V50", "V60", "V70", "V90", "XC40", "XC60", "XC70", "XC90"],
    "Wuling": ["Air EV", "Hongguang Mini EV", "Victory", "Cortez", "Almaz", "Formo"],

}

fixture = []
pk = 1

for marca_nombre, modelos in marcas_y_modelos.items():
    try:
        marca = Marca.objects.get(nombre=marca_nombre)
        for modelo in modelos:
            fixture.append({
                "model": "taller.modelo",
                "pk": pk,
                "fields": {
                    "nombre": modelo,
                    "marca": marca.pk
                }
            })
            pk += 1
    except Marca.DoesNotExist:
        print(f"⚠️ Marca no encontrada en la base de datos: {marca_nombre}")

with open("taller/fixtures/modelos.json", "w", encoding="utf-8") as f:
    json.dump(fixture, f, ensure_ascii=False, indent=2)

print("✅ Fixture modelos.json generado correctamente.")
