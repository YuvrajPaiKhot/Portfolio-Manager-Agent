sector_list = ["basic-materials", "communication-services", "consumer-cyclical", "consumer-defensive", "energy", "financial-services", "healthcare", "industrials", "real-estate", "technology", "utilities"]

sector_industry_dict_yf = {
    "basic-materials": {
        "agricultural-inputs", 
        "aluminum", 
        "building-materials", 
        "chemicals", 
        "coking-coal", 
        "copper", 
        "gold", 
        "lumber-wood-production", 
        "other-industrial-metals-mining", 
        "other-precious-metals-mining", 
        "paper-paper-products", 
        "silver", 
        "specialty-chemicals", 
        "steel"
    },

    "communication-services": {
        "advertising-agencies",
        "broadcasting",
        "electronic-gaming-multimedia",
        "entertainment",
        "internet-content-information",
        "publishing",
        "telecom-services"
    },

    "consumer-cyclical": {
        "apparel-manufacturing",
        "apparel-retail",
        "auto-manufacturers",
        "auto-parts",
        "auto-truck-dealerships",
        "department-stores",
        "footwear-accessories",
        "furnishings-fixtures-appliances",
        "gambling",
        "home-improvement-retail",
        "internet-retail",
        "leisure",
        "lodging",
        "luxury-goods",
        "packaging-containers",
        "personal-services",
        "recreational-vehicles",
        "residential-construction",
        "resorts-casinos",
        "restaurants",
        "specialty-retail",
        "textile-manufacturing",
        "travel-services"
    },

    "consumer-defensive": {
        "beverages-brewers",
        "beverages-non-alcoholic",
        "beverages-wineries-distilleries",
        "confectioners",
        "discount-stores",
        "education-training-services",
        "farm-products",
        "food-distribution",
        "grocery-stores",
        "household-personal-products",
        "packaged-foods",
        "tobacco",
    },

    "energy": {
        "oil-gas-drilling",
        "oil-gas-e-p",
        "oil-gas-equipment-services",
        "oil-gas-integrated",
        "oil-gas-midstream",
        "oil-gas-refining-marketing",
        "thermal-coal",
        "uranium"
    },

    "financial-services": {
        "asset-management",
        "banks-diversified",
        "banks-regional",
        "capital-markets",
        "credit-services",
        "financial-conglomerates",
        "financial-data-stock-exchanges",
        "insurance-brokers",
        "insurance-diversified",
        "insurance-life",
        "insurance-property-casualty",
        "insurance-reinsurance",
        "insurance-specialty",
        "mortgage-finance",
        "shell-companies"
    },

    "healthcare": {
        "biotechnology",
        "diagnostics-research",
        "drug-manufacturers-general",
        "drug-manufacturers-specialty-generic",
        "health-information-services",
        "healthcare-plans",
        "medical-care-facilities",
        "medical-devices",
        "medical-distribution",
        "medical-instruments-supplies",
        "pharmaceutical-retailers"
    },

    "industrials": {
        "aerospace-defense",
        "airlines",
        "airports-air-services",
        "building-products-equipment",
        "business-equipment-supplies",
        "conglomerates",
        "consulting-services",
        "electrical-equipment-parts",
        "engineering-construction",
        "farm-heavy-construction-machinery",
        "industrial-distribution",
        "infrastructure-operations",
        "integrated-freight-logistics",
        "marine-shipping",
        "metal-fabrication",
        "pollution-treatment-controls",
        "railroads",
        "rental-leasing-services",
        "security-protection-services",
        "specialty-business-services",
        "specialty-industrial-machinery",
        "staffing-employment-services",
        "tools-accessories",
        "trucking",
        "waste-management"
    },

    "real-estate": {
        "real-estate-development",
        "real-estate-diversified",
        "real-estate-services",
        "reit-diversified",
        "reit-healthcare-facilities",
        "reit-hotel-motel",
        "reit-industrial",
        "reit-mortgage",
        "reit-office",
        "reit-residential",
        "reit-retail",
        "reit-specialty"
    },

    "technology": {
        "communication-equipment",
        "computer-hardware",
        "consumer-electronics",
        "electronic-components",
        "electronics-computer-distribution",
        "information-technology-services",
        "scientific-technical-instruments",
        "semiconductor-equipment-materials",
        "semiconductors",
        "software-application",
        "software-infrastructure",
        "solar"
    },

    "utilities": {
        "utilities-diversified",
        "utilities-independent-power-producers",
        "utilities-regulated-electric",
        "utilities-regulated-gas",
        "utilities-regulated-water",
        "utilities-renewable"
    }
}

sector_mapping = {
    "^YH101": "basic-materials", 
    "^YH308": "communication-services", 
    "^YH102": "consumer-cyclical", 
    "^YH205": "consumer-defensive", 
    "^YH309": "energy", 
    "^YH103": "financial-services", 
    "^YH206": "healthcare", 
    "^YH310": "industrials", 
    "^YH104": "real-estate", 
    "^YH311": "technology", 
    "^YH207": "utilities"
}

sector_industry_mapping_dict = {
    "basic-materials": {
        "^YH10110010": "agricultural-inputs", 
        "^YH10150010": "aluminum", 
        "^YH10120010": "building-materials", 
        "^YH10130010": "chemicals", 
        "^YH10160010": "coking-coal", 
        "^YH10150020": "copper", 
        "^YH10150040": "gold", 
        "^YH10140010": "lumber-wood-production", 
        "^YH10150030": "other-industrial-metals-mining", 
        "^YH10150060": "other-precious-metals-mining", 
        "^YH10140020": "paper-paper-products", 
        "^YH10150050": "silver", 
        "^YH10130020": "specialty-chemicals", 
        "^YH10160020": "steel"
    },

    "communication-services": {
        "^YH30820010": "advertising-agencies",
        "^YH30820030": "broadcasting",
        "^YH30830020": "electronic-gaming-multimedia",
        "^YH30820040": "entertainment",
        "^YH30830010": "internet-content-information",
        "^YH30820020": "publishing",
        "^YH30810010": "telecom-services"
    },

    "consumer-cyclical": {
        "^YH10240020": "apparel-manufacturing",
        "^YH10280010": "apparel-retail",
        "^YH10200020": "auto-manufacturers",
        "^YH10200030": "auto-parts",
        "^YH10200010": "auto-truck-dealerships",
        "^YH10280020": "department-stores",
        "^YH10240030": "footwear-accessories",
        "^YH10220010": "furnishings-fixtures-appliances",
        "^YH10290010": "gambling",
        "^YH10280030": "home-improvement-retail",
        "^YH10280050": "internet-retail",
        "^YH10290020": "leisure",
        "^YH10290030": "lodging",
        "^YH10280040": "luxury-goods",
        "^YH10250010": "packaging-containers",
        "^YH10260010": "personal-services",
        "^YH10200040": "recreational-vehicles",
        "^YH10230010": "residential-construction",
        "^YH10290040": "resorts-casinos",
        "^YH10270010": "restaurants",
        "^YH10280060": "specialty-retail",
        "^YH10240010": "textile-manufacturing",
        "^YH10290050": "travel-services"
    },

    "consumer-defensive": {
        "^YH20510010": "beverages-brewers",
        "^YH20520010": "beverages-non-alcoholic",
        "^YH20510020": "beverages-wineries-distilleries",
        "^YH20525010": "confectioners",
        "^YH20550010": "discount-stores",
        "^YH20540010": "education-training-services",
        "^YH20525020": "farm-products",
        "^YH20550020": "food-distribution",
        "^YH20550030": "grocery-stores",
        "^YH20525030": "household-personal-products",
        "^YH20525040": "packaged-foods",
        "^YH20560010": "tobacco",
    },

    "energy": {
        "^YH30910010": "oil-gas-drilling",
        "^YH30910020": "oil-gas-e-p",
        "^YH30910060": "oil-gas-equipment-services",
        "^YH30910030": "oil-gas-integrated",
        "^YH30910040": "oil-gas-midstream",
        "^YH30910050": "oil-gas-refining-marketing",
        "^YH30920010": "thermal-coal",
        "^YH30920020": "uranium"
    },

    "financial-services": {
        "^YH10310010": "asset-management",
        "^YH10320010": "banks-diversified",
        "^YH10320020": "banks-regional",
        "^YH10330010": "capital-markets",
        "^YH10360010": "credit-services",
        "^YH10350020": "financial-conglomerates",
        "^YH10330020": "financial-data-stock-exchanges",
        "^YH10340050": "insurance-brokers",
        "^YH10340060": "insurance-diversified",
        "^YH10340010": "insurance-life",
        "^YH10340020": "insurance-property-casualty",
        "^YH10340030": "insurance-reinsurance",
        "^YH10340040": "insurance-specialty",
        "^YH10320030": "mortgage-finance",
        "^YH10350010": "shell-companies"
    },

    "healthcare": {
        "^YH20610010": "biotechnology",
        "^YH20660010": "diagnostics-research",
        "^YH20620010": "drug-manufacturers-general",
        "^YH20620020": "drug-manufacturers-specialty-generic",
        "^YH20645030": "health-information-services",
        "^YH20630010": "healthcare-plans",
        "^YH20645010": "medical-care-facilities",
        "^YH20650010": "medical-devices",
        "^YH20670010": "medical-distribution",
        "^YH20650020": "medical-instruments-supplies",
        "^YH20645020": "pharmaceutical-retailers"
    },

    "industrials": {
        "^YH31010010": "aerospace-defense",
        "^YH31080020": "airlines",
        "^YH31080010": "airports-air-services",
        "^YH31040030": "building-products-equipment",
        "^YH31070010": "business-equipment-supplies",
        "^YH31030010": "conglomerates",
        "^YH31020020": "consulting-services",
        "^YH31070060": "electrical-equipment-parts",
        "^YH31040010": "engineering-construction",
        "^YH31050010": "farm-heavy-construction-machinery",
        "^YH31060010": "industrial-distribution",
        "^YH31040020": "infrastructure-operations",
        "^YH31080060": "integrated-freight-logistics",
        "^YH31080040": "marine-shipping",
        "^YH31070030": "metal-fabrication",
        "^YH31070040": "pollution-treatment-controls",
        "^YH31080030": "railroads",
        "^YH31020030": "rental-leasing-services",
        "^YH31020040": "security-protection-services",
        "^YH31020010": "specialty-business-services",
        "^YH31070020": "specialty-industrial-machinery",
        "^YH31020050": "staffing-employment-services",
        "^YH31070050": "tools-accessories",
        "^YH31080050": "trucking",
        "^YH31090010": "waste-management"
    },

    "real-estate": {
        "^YH10410010": "real-estate-development",
        "^YH10420090": "real-estate-diversified",
        "^YH10410020": "real-estate-services",
        "^YH10420090": "reit-diversified",
        "^YH10420010": "reit-healthcare-facilities",
        "^YH10420020": "reit-hotel-motel",
        "^YH10420030": "reit-industrial",
        "^YH10420070": "reit-mortgage",
        "^YH10420040": "reit-office",
        "^YH10420050": "reit-residential",
        "^YH10420060": "reit-retail",
        "^YH10420080": "reit-specialty"
    },

    "technology": {
        "^YH31120010": "communication-equipment",
        "^YH31120020": "computer-hardware",
        "^YH31120030": "consumer-electronics",
        "^YH31120040": "electronic-components",
        "^YH31120050": "electronics-computer-distribution",
        "^YH31110010": "information-technology-services",
        "^YH31120060": "scientific-technical-instruments",
        "^YH31130010": "semiconductor-equipment-materials",
        "^YH31130020": "semiconductors",
        "^YH31110020": "software-application",
        "^YH31110030": "software-infrastructure",
        "^YH31130030": "solar"
    },

    "utilities": {
        "^YH20720040": "utilities-diversified",
        "^YH20710010": "utilities-independent-power-producers",
        "^YH20720020": "utilities-regulated-electric",
        "^YH20720030": "utilities-regulated-gas",
        "^YH20720010": "utilities-regulated-water",
        "^YH20710020": "utilities-renewable"
    }
}

currency_full_names = {
    'AUD': 'Australian Dollar',
    'BGN': 'Bulgarian Lev',
    'BRL': 'Brazilian Real',
    'CAD': 'Canadian Dollar',
    'CHF': 'Swiss Franc',
    'CNY': 'Chinese Yuan',
    'CYP': 'Cypriot Pound',
    'CZK': 'Czech Koruna',
    'DKK': 'Danish Krone',
    'EEK': 'Estonian Kroon',
    'EUR': 'Euro',
    'GBP': 'British Pound Sterling',
    'HKD': 'Hong Kong Dollar',
    'HRK': 'Croatian Kuna',
    'HUF': 'Hungarian Forint',
    'IDR': 'Indonesian Rupiah',
    'ILS': 'Israeli Shekel',
    'INR': 'Indian Rupee',
    'ISK': 'Icelandic Krona',
    'JPY': 'Japanese Yen',
    'KRW': 'South Korean Won',
    'LTL': 'Lithuanian Litas',
    'LVL': 'Latvian Lats',
    'MTL': 'Maltese Lira',
    'MXN': 'Mexican Peso',
    'MYR': 'Malaysian Ringgit',
    'NOK': 'Norwegian Krone',
    'NZD': 'New Zealand Dollar',
    'PHP': 'Philippine Peso',
    'PLN': 'Polish Zloty',
    'ROL': 'Romanian Leu (Old)',
    'RON': 'Romanian Leu',
    'RUB': 'Russian Ruble',
    'SEK': 'Swedish Krona',
    'SGD': 'Singapore Dollar',
    'SIT': 'Slovenian Tolar',
    'SKK': 'Slovak Koruna',
    'THB': 'Thai Baht',
    'TRL': 'Turkish Lira (Old)',
    'TRY': 'Turkish Lira',
    'USD': 'United States Dollar',
    'ZAR': 'South African Rand'
}

screener_fields_needing_conversion = [
    "eodprice",
    "intradayprice",
    "intradaypricechange",
    "intradaymarketcap",
    "lastclosemarketcap.lasttwelvemonths",
    "totalrevenues.lasttwelvemonths",
    "ebit.lasttwelvemonths",
    "ebitda.lasttwelvemonths",
    "grossprofit.lasttwelvemonths",
    "netincomeis.lasttwelvemonths",
    "operatingincome.lasttwelvemonths",
    "basicepscontinuingoperations.lasttwelvemonths",
    "dilutedepscontinuingoperations.lasttwelvemonths",
    "netepsbasic.lasttwelvemonths",
    "netepsdiluted.lasttwelvemonths",
    "totalassets.lasttwelvemonths",
    "totalcashandshortterminvestments.lasttwelvemonths",
    "totalcommonequity.lasttwelvemonths",
    "totalcurrentassets.lasttwelvemonths",
    "totalcurrentliabilities.lasttwelvemonths",
    "totaldebt.lasttwelvemonths",
    "totalequity.lasttwelvemonths",
    "cashfromoperations.lasttwelvemonths",
    "capitalexpenditure.lasttwelvemonths",
    "leveredfreecashflow.lasttwelvemonths",
    "unleveredfreecashflow.lasttwelvemonths",
    "lastclosetevebit.lasttwelvemonths",
    "lastclosetevebitda.lasttwelvemonths",
    "valuation",
    "forward_dividend_per_share",
]

country_to_currency = {
    "ar": "ARS",  # Argentina Peso
    "at": "EUR",  # Austria Euro
    "au": "AUD",  # Australia Dollar
    "be": "EUR",  # Belgium Euro
    "br": "BRL",  # Brazil Real
    "ca": "CAD",  # Canada Dollar
    "ch": "CHF",  # Switzerland Franc
    "cl": "CLP",  # Chile Peso
    "cn": "CNY",  # China Yuan
    "co": "COP",  # Colombia Peso
    "cz": "CZK",  # Czech Republic Koruna
    "de": "EUR",  # Germany Euro
    "dk": "DKK",  # Denmark Krone
    "ee": "EUR",  # Estonia Euro
    "eg": "EGP",  # Egypt Pound
    "es": "EUR",  # Spain Euro
    "fi": "EUR",  # Finland Euro
    "fr": "EUR",  # France Euro
    "gb": "GBP",  # United Kingdom Pound
    "gr": "EUR",  # Greece Euro
    "hk": "HKD",  # Hong Kong Dollar
    "hu": "HUF",  # Hungary Forint
    "id": "IDR",  # Indonesia Rupiah
    "ie": "EUR",  # Ireland Euro
    "il": "ILS",  # Israel Shekel
    "in": "INR",  # India Rupee
    "is": "ISK",  # Iceland Krona
    "it": "EUR",  # Italy Euro
    "jp": "JPY",  # Japan Yen
    "kr": "KRW",  # South Korea Won
    "kw": "KWD",  # Kuwait Dinar
    "lk": "LKR",  # Sri Lanka Rupee
    "lt": "EUR",  # Lithuania Euro
    "lv": "EUR",  # Latvia Euro
    "mx": "MXN",  # Mexico Peso
    "my": "MYR",  # Malaysia Ringgit
    "nl": "EUR",  # Netherlands Euro
    "no": "NOK",  # Norway Krone
    "nz": "NZD",  # New Zealand Dollar
    "pe": "PEN",  # Peru Sol
    "ph": "PHP",  # Philippines Peso
    "pk": "PKR",  # Pakistan Rupee
    "pl": "PLN",  # Poland Zloty
    "pt": "EUR",  # Portugal Euro
    "qa": "QAR",  # Qatar Riyal
    "ro": "RON",  # Romania Leu
    "ru": "RUB",  # Russia Ruble
    "sa": "SAR",  # Saudi Arabia Riyal
    "se": "SEK",  # Sweden Krona
    "sg": "SGD",  # Singapore Dollar
    "sr": "SRD",  # Suriname Dollar
    "th": "THB",  # Thailand Baht
    "tr": "TRY",  # Turkey Lira
    "tw": "TWD",  # Taiwan Dollar
    "us": "USD",  # United States Dollar
    "ve": "VES",  # Venezuela Bolívar
    "vn": "VND",  # Vietnam Dong
    "za": "ZAR",  # South Africa Rand
}


