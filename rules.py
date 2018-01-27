from rules_parser import Rule
from strategies import *

STANDARD = ['Amonkhet', 'Aether Revolt', 'Kaladesh', 'Eldritch Moon',
            'Shadows over Innistrad', 'Oath of the Gatewatch',
            'Battle for Zendikar']
ACTIVE_SET = 'Amonkhet'
PRESALE_SET = 'Hour of Devastation'

def standard_without_active():
    printings = [set for set in STANDARD if set.lower() != ACTIVE_SET.lower()]
    return printings

RULES = [
    Rule({
        'name': ['Champion of Wits'],
        'strategies': [PricingExcludePercentile(percentile=99)]
    }),
    Rule({
        'set': ['hour of devastation'],
        'name': ["Nicol Bolas, the Deceiver", "Nissa, Genesis Mage", "Wasp of the Bitter End",
                   "Zealot of the God-Pharaoh", "Visage of Bolas", "Cinder Barrens", "Avid Reclaimer",
                   "Brambleweft Behemoth", "Nissa's Encouragement", "Woodland Stream", "Insect Token",],
        'strategies': [IgnoreStrategy()]
    }),
    Rule({
        'set': ['hour of devastation'],
        'name': ["Dreamstealer", "Horse Token"],
        'strategies': [IgnoreStrategy()]
    }),
    Rule({
        'set': ['hour of devastation'],
        'name': ["Hour of Devastation", "Driven", "Solemnity",
                 "Wildfire Eternal", "Oketra's Last Mercy",
                 "Ammit Eternal",],
        'finish': 'Regular',
        #'strategies': [MinPriceIgnoreOutliersStrategyNonDirect(threshold=70),
        #               SetStockStrategy(amount=20)]
        'strategies': [IgnoreStrategy()]
    }),
    Rule({
        'set': ['hour of devastation'],
        'name': ["Ammit Eternal", ],
        'finish': 'Regular',
        #'strategies': [MinPriceIgnoreOutliersStrategyNonDirect(threshold=3),
        #               SetStockStrategy(amount=20)]
        'strategies': [IgnoreStrategy()]
    }),
    Rule({
        'set': ['hour of devastation'],
        'finish': 'Regular',
         'name': ['Hour of Revelation','Ramunap Excavator', "Hour of Promise", "Torment of Hailfire",
                 "The Scarab God", "The Locust God", "Champion of Wits", "Abrade", "Mirage Mirror",
                 "Dreamstealer", "Bontu's Last Reckoning", "Hostile Desert", "Angel of Condemnation",
                 "Nicol Bolas, God-Pharaoh", "Samut, the Tested", "The Scorpion God"],
        #'strategies': [MinPriceIgnoreOutliersStrategyNonDirect(threshold=2),
        #               SetStockStrategy(amount=20)]
        'strategies': [IgnoreStrategy()]
    }),
    Rule({
        'set': ['hour of devastation'],
        'finish': 'Regular',
        'name': ['Neheb, the Eternal', "Fraying Sanity", "Crested Sunmare", "Hour of Promise", "Adorned Pouncer"],
        #'strategies': [MinPriceIgnoreOutliersStrategyNonDirect(threshold=1),
        #               SetStockStrategy(amount=20)]
        'strategies': [IgnoreStrategy()]
    }),
    Rule({
        'set': ['hour of devastation'],
        'finish': 'Regular',
        'name': ['Foo'],
        #'strategies': [MinPriceIgnoreOutliersStrategyNonDirect(threshold=1),
        #               SetStockStrategy(amount=20)]
        'strategies': [IgnoreStrategy()]
    }),
    Rule({
        'set': ['Hour of Devastation'],
        'is_full_art': True,
        'strategies': [IgnoreStrategy()]
    }),
    Rule({
        'set': ['Masterpiece Series: Amonkhet Invocations'],
        'strategies': [MinPriceIgnoreOutliersFallbackNonDirectStrategy(threshold=90),
                       TCGInventoryStrategy(amount=2, min_quantity=0)]
    }),
    Rule({
        'set': ['amonkhet'],
        'name': ["Liliana's Influence", "Gideon's Resolve", "Desiccated Naga",
                   "Foul Orchard", "Stone Quarry", "Tattered Mummy",
                   "Graceful Cat", "Companion of the Trials", "Snake Token",
                   "Glyph Keeper", "Ahn-Crop Crasher", "Archfiend of Ifnir",
                   "Harvest Season", "Insult", "Vizier of Many Faces",
                   "Censor", "Dissenter's Deliverance", "Forsaken Sanctuary",
                   "Meandering River", "Timber Gorge", "Tranquil Expanse",
                   "Sacred Cat","Hieroglyphic Illumination",],
        'strategies': [IgnoreStrategy()]
    }),
    #Rule({
    #    'set': ['hour of devastation'],
    #    'ignore': ["Nicol Bolas, the Deceiver", "Nissa, Genesis Mage", "Wasp of the Bitter End",
    #               "Zealot of the God-Pharaoh", "Visage of Bolas", "Cinder Barrens", "Avid Reclaimer",
    #               "Brambleweft Behemoth", "Nissa's Encouragement", "Woodland Stream"],
    #    'strategies': [IgnoreStrategy()]
    #}),
    Rule({
        'set': ['amonkhet'],
        'ignore_contains': ['Double'],
        'strategies': [IgnoreStrategy()]
    }),
    Rule({
        'tcg': True,
        'set': ['Hour of Devastation'],
        'rarity': ['Uncommon', 'Rare', 'Mythic Rare', 'Token'],
        'strategies': [IgnoreStrategy()]
    }),
    Rule({
        'tcg': True,
        'set': ['Hour of Devastation'],
        'rarity': ['Common'],
        'strategies': [MinPriceIgnoreOutliersFallbackNonDirectStrategy(90),
                       SetStockStrategy(amount=20)]
    }),
    Rule({
        'set': ['Hour of Devastation'],
        'rarity': ['Common'],
        'strategies': [MinPriceIgnoreOutliersFallbackNonDirectStrategy(90),
                       TCGInventoryStrategy(amount=20, min_quantity=0)]
    }),
    Rule({
        'set': ['Hour of Devastation'],
        'strategies': [MinPriceIgnoreOutliersFallbackNonDirectStrategy(90)]
    }),
    Rule({
        'set': standard_without_active(),
        'finish': 'Regular',
        'strategies': [MinPriceIgnoreOutliersFallbackNonDirectStrategy(threshold=85),
                       TCGInventoryStrategy(amount=4, min_quantity=0)],
    }),
    Rule({
        'set': [PRESALE_SET],
        'finish': 'Regular',
        'rarity': ['Uncommon', 'Common'],
        'strategies': [MinPriceIgnoreOutliersFallbackNonDirectStrategy(90),
            TCGInventoryStrategy(amount=20, min_quantity=0)],
     }),
    Rule({
        'set': [PRESALE_SET],
        'finish': 'Regular',
        'strategies': [MinPriceIgnoreOutliersFallbackNonDirectStrategy(threshold=95),
                       TCGInventoryStrategy(amount=8, min_quantity=0)]
    }),
    Rule({
        'set': [PRESALE_SET],
        'finish': 'Foil',
        'strategies': [MinPriceIgnoreOutliersFallbackNonDirectStrategy(threshold=85),
                       TCGInventoryStrategy(amount=2, min_quantity=0)]
    }),
    Rule({
        'set': ['Archenemy: Nicol Bolas'],
        'strategies': [MinPriceIgnoreOutliersFallbackNonDirectStrategy(threshold=90),
                       TCGInventoryStrategy(min_quantity=4, amount=0)]
    }),
    Rule({
        'finish': 'Foil',
        'rarity': ['Common'],
        'set': [ACTIVE_SET],
        'strategies': [MinPriceIgnoreOutliersStrategyDirect(threshold=90)]
    }),
    Rule({
        'finish': 'Foil',
        'rarity': ['Uncommon'],
        'set': [ACTIVE_SET],
        'strategies': [MinPriceIgnoreOutliersStrategyDirect(threshold=85)]
    }),
    Rule({
        'finish': 'Foil',
        'rarity': ['Rare'],
        'set': [ACTIVE_SET],
        'strategies': [MinPriceIgnoreOutliersStrategyDirect(threshold=80)]
    }),
    Rule({
        'finish': 'Foil',
        'rarity': ['Mythic Rare'],
        'set': [ACTIVE_SET],
        'strategies': [MinPriceIgnoreOutliersStrategyDirect(threshold=75)]
    }),
    Rule({
        'rarity': ['common'],
        'set': [ACTIVE_SET],
        'strategies': [MinPriceIgnoreOutliersStrategyDirect(threshold=95),
                       SetStockStrategy(amount=20)]
    }),
    Rule({
        'rarity': ['rare', 'mythic rare'],
        'condition': ['near mint'],
        'set': [ACTIVE_SET],
        'strategies': [InventoryPricingStrategy(min_threshold=75, max_threshold=90),
                     TCGInventoryStrategy(min_quantity=4, amount=4)]
    }),
    Rule({
        'rarity': ['uncommon'],
        'condition': ['near mint'],
        'set': [ACTIVE_SET],
        'strategies': [InventoryPricingStrategy(min_threshold=75, max_threshold=95),
                     TCGInventoryStrategy(min_quantity=4, amount=20)]
    }),
    Rule({
        'rarity': ['Token'],
        'condition': ['near mint'],
        'set': [ACTIVE_SET],
        'strategies': [MinPriceIgnoreOutliersStrategyDirect(threshold=95),
                       TCGInventoryStrategy(min_quantity=4, amount=8)]
    }),
    Rule({
        'rarity': ['Basic Land'],
        'is_full_art': True,
        'condition': ['near mint'],
        'set': [ACTIVE_SET],
        'finish': 'Regular',
        'strategies': [MinPriceIgnoreOutliersStrategyDirect(threshold=80),
                       TCGInventoryStrategy(min_quantity=4, amount=10)]
    }),
    Rule({
        'rarity': ['Basic Land'],
        'condition': ['near mint'],
        'set': [ACTIVE_SET],
        'is_full_art': False,
        'finish': 'Regular',
        'strategies': [MinPriceIgnoreOutliersStrategyDirect(threshold=90),
                       TCGInventoryStrategy(min_quantity=4, amount=10)]
    })
]
