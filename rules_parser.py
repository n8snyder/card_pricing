import django, traceback, sys, logging, arrow

django.setup()

# cards is not included in this repo
from cards.models import Card, CardLog

class Rule(dict):

    def matches(self, card_listing):
        parser = Parser(self)
        return parser.matches(card_listing)

    def parser(self):
        return Parser(self)
    def strategies(self):
        return self['strategies']

    @property
    def all_attrs(self):
        attrs = dict(self)
        attrs.pop('strategies')
        return attrs



# General data relating to a card that is listed
class CardListing(object):
    def __init__(self, original_card_name, set_name, condition, finish,
                 original_quantity, store, card_number=None):
        self.store = store
        self.input_card_name = original_card_name
        self.is_full_art = 'full art' in self.input_card_name.lower()
        if card_number:
            try:
                card = Card.objects.get_card(self.input_card_name, set_name,
                                             card_number=card_number)
            except Card.DoesNotExist:
                raise ValueError(
                    '{0} from {1} does not exist.'.format(self.input_card_name, set_name))
            except Card.MultipleObjectsReturned:
                raise ValueError(
                    'Multiple {0} from {1} were found'.format(self.input_card_name, set_name))
        else:
            try:
                card = Card.objects.get_card(self.input_card_name, set_name)
            except Card.DoesNotExist:
                raise ValueError(
                    '{0} from {1} does not exist.'.format(self.input_card_name, set_name))
            except Card.MultipleObjectsReturned:
                raise ValueError(
                    'Multiple {0} from {1} were found'.format(self.input_card_name, set_name))
        field_names = [field.name for field in Card._meta.fields]
        for field_name in field_names:
            self.__dict__[field_name] = getattr(card, field_name)
        self.set = set_name
        self.condition = condition
        self.finish = finish
        try:
            self.original_quantity = int(original_quantity)
        except ValueError:
            self.original_quantity = 0
        self.add_to_quantity = 0

    def set_quantity(self, quantity):
        self.quantity = quantity
        self.add_to_quantity = max(self.quantity - self.original_quantity, 0)

    @property
    def all_attrs(self):
        return self.__dict__

    def __str__(self):
        return '{0} {1} {2} {3}'.format(self.name, self.set, self.condition,
                                        self.finish)


class Parser(object):
    def __init__(self, rule):
        self.rule = rule

    def matches(self, card_listing):
        for attr_name in self.rule.all_attrs.keys():
            result = getattr(self, attr_name+'_match')(card_listing)
            if not result:
                return False
        return True

    def name_match(self, attrs):
        name = attrs.name
        if name.lower() in [n.lower() for n in self.rule['name']]:
            return True

    def rarity_match(self, attrs):
        rarity = attrs.rarity
        if rarity.lower() in [r.lower() for r in self.rule['rarity']]:
            return True

    def condition_match(self, attrs):
        condition = attrs.condition
        if condition.lower() in [c.lower() for c in self.rule['condition']]:
            return True

    def set_match(self, attrs):
        set = attrs.set
        if set.lower() in [s.lower() for s in self.rule['set']]:
            return True

    def finish_match(self, attrs):
        finish = attrs.finish
        return finish.lower() == self.rule['finish'].lower()

    def price_gt_match(self, attrs):
        price = attrs.price
        return price > self.rule['price_gt']

    def price_gte_match(self, attrs):
        price = attrs.price
        return price >= self.rule['price_gte']

    def price_lt_match(self, attrs):
        price = attrs.price
        return price < self.rule['price_lt']

    def price_lte_match(self, attrs):
        price = attrs.price
        return price <= self.rule['price_lte']

    def is_full_art_match(self, attrs):
        return attrs.is_full_art == True

    def ignore_match(self, attrs):
        name = attrs.input_card_name
        return name.lower() in [n.lower() for n in self.rule['ignore']]

    def ignore_contains_match(self, attrs):
        name = attrs.input_card_name
        for partial_name in self.rule['ignore_contains']:
            if partial_name.lower() in name.lower():
                return True
        return False

    def tcg_match(self, attrs):
        store = attrs.store
        return (store == 'tcg player') == self.rule['tcg']

    def cc_match(self, attrs):
        store = attrs.store
        return (store == 'crystal commerce') == self.rule['cc']

def get_strategies(card_listing):
    from bin.rules import RULES
    logger = logging.getLogger(__name__)
    logger.setLevel('INFO')
    for rule in RULES:
        if rule.matches(card_listing):
            logger.debug('Card name: {} Rule: {}'.format(card_listing, rule))
            return rule['strategies']
    raise ValueError(
        'No rules matched for {0}'.format(card_listing))

def create_card_listing(card_name, set_name, condition, finish, original_quantity,
                        store, card_number=None):
    card_listing = CardListing(card_name, set_name, condition, finish,
                               original_quantity, store, card_number=card_number)
    strategies = get_strategies(card_listing)
    for strategy in strategies:
        card_listing = strategy.apply(card_listing)
    return card_listing

def update_row_price_quantity(row, card_listing):
    row['My Price'] = card_listing.price
    row['Add to Quantity'] = card_listing.add_to_quantity
    return row

def update_cc_row_price(card_listing):
    row = {
        'Category': card_listing.set,
        'Product Name': card_listing.input_card_name,
        'Sell Price': card_listing.price,
        'Description': '$SKIP$',
        'Barcode': '$SKIP$',
        'Store Only': '$SKIP$',
        'Manufacturer SKU': '$SKIP$',
        'Weight': '$SKIP$',
        'Buy Price': '$SKIP$',
        'Photo URL': '$SKIP$',
        'MSRP': '$SKIP$',
        'Max Qty': '$SKIP$',
        'Opt Qty': '$SKIP$',
        'ASIN': '$SKIP$',
        'Tax Exempt': '$SKIP$',
        'Domestic Sale Only': '$SKIP$',
        'Add Qty': '$SKIP$',
        'Qty': '$SKIP$',
        'Infinite Qty': '$SKIP$',
    }
    return row

def update_csv_row(row, finish):
    """
    row =
    {'Set Name': '10th Edition',
    'My Price': '',
    'Rarity': 'R',
    'Product Name': 'Abundance',
    'Quantity': '',
    'Number': '249',
    'Low Price': '2.6500',
    'Market Price': '2.97',
    'Condition': 'Near Mint',
    'TCGplayer Id': '4519',
    'Product Line': 'Magic',
    'Add to Quantity': '0'}
    """

    condition = row['Condition'].split('Foil')[0].strip()
    if row['Rarity'] == 'L':
        card_number = row['Number']
    else:
        card_number = None
    try:
        card_listing = create_card_listing(row['Product Name'], row['Set Name'],
                                           condition, finish, row['Quantity'],
                                           'tcg player', card_number=card_number)
    except ValueError as e:
        print(e)
        # print(traceback.print_exc(file=sys.stdout))
        row = None
    else:
        if card_listing:
            row = update_row_price_quantity(row, card_listing)
        else:
            row = None
    return row

def update_cc_csv_row(row, finish):
    """
    row =
    {'Product Name': 'Nicol Bolas, God-Pharaoh',
    'Category': 'Hour of Devastation',
    'Condition': 'Near Mint',
    'Language': 'English',
    'Qty': '0',
    'Opt Qty': '4',
    'Buy Price': '11.81',
    'Sell Price': '21.48',
    'URL': '...'}
    """

    card_name = row['Product Name']
    set_name = row['Category']
    condition = row['Condition']
    quantity = row['Qty']


    try:
        card_listing = create_card_listing(card_name, set_name, condition,
                                           finish, quantity, 'crystal commerce')
    except ValueError as e:
        row = None
    else:
        if card_listing:
            row = update_cc_row_price(card_listing)
        else:
            row = None
    return row
