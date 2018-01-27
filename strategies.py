import sys, django, os, logging

django.setup()

from django.core.cache import cache
import numpy as np
from decimal import Decimal
from colorama import init, Fore, Back, Style

from cards.libs import get_key_from_choices
from cards import models as cards_models
from cards.models import CardLog, CardInventoryLog, Card
from bin.most_sold import most_sold, total_sold_by_card, cases_to_open, \
    cases_required

logging.basicConfig(level=logging.DEBUG)

OUR_SHIPPING = 0.99

def get_possible_thresholds(prices, outliers):
    min_threshold = 0
    max_threshold = 100
    found_min = False
    found_max = False
    non_outliers = np.logical_not(outliers)
    low = round(min(prices[non_outliers]) - 0.01, 2)
    for threshold in range(0,100):
        sample_outliers = MinPriceIgnoreOutliersStrategyDirect(50).percentile_based_outlier(data=prices, threshold=threshold)
        sample_non_outliers = np.logical_not(sample_outliers)
        try:
            sample_low = round(min(prices[sample_non_outliers]) - 0.01, 2)
        except ValueError:
            continue
        if sample_low==low:
            if not found_min:
                found_min = True
                min_threshold = threshold
                max_threshold = threshold
            elif found_min and not found_max:
                max_threshold = threshold
        elif sample_low==low and not found_max and found_min:
            found_max = True
    return min_threshold, max_threshold

def low_threshold_multiplier(threshold, low):
    """
    For really low threshold, we want to apply a price multiplier to decrease demand.
    The larger the factor, the smaller the multiplier.
    When factor=2 and threshold=1, multilier = 1.5
    """
    if threshold == 1:
        return low * 1.5
    if threshold <= 5:
        factor = 6
        multiplier = (((11 - threshold) / factor) / 10) + 1
        low = low * multiplier
    return low

class BaseStrategy(object):

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def apply(self, card_listing):
        raise NotImplementedError(
            'subclasses of BaseStrategy must provide a find_price() method')



class SetStockStrategy(BaseStrategy):

    def __init__(self, **kwargs):
        self.amount = kwargs['amount']

    def apply(self, card_listing):
        card_listing.set_quantity(self.amount)
        return card_listing

class TCGInventoryStrategy(SetStockStrategy):

    def __init__(self, min_quantity, **kwargs):
        super().__init__(**kwargs)
        self.min_quantity = min_quantity

    def get_new_quantity(self, current_quantity):
        if current_quantity <= self.min_quantity:
            return 0
        else:
            return min(self.amount, current_quantity - self.min_quantity)

    def apply(self, card_listing):
        card_listing = super().apply(card_listing)
        card = Card.objects.get(id=card_listing.id)
        condition = get_key_from_choices(cards_models.CONDITIONS, card_listing.condition)
        finish = get_key_from_choices(CardLog.CARD_FINISH, card_listing.finish)
        current_quantity = CardInventoryLog.objects.get_current_quantity(card,
                                                                         condition,
                                                                         finish)

        new_quantity = self.get_new_quantity(current_quantity)
        card_listing.set_quantity(new_quantity)
        return card_listing

class InventoryPricingStrategy(BaseStrategy):

    def __init__(self, min_threshold, max_threshold):
        self.min_threshold = min_threshold
        self.max_threshold = max_threshold

    def calc_threshold(self, all_card_quantities, card_quantity):
        num_cards_with_more_quantity = len([quantity for quantity in
                                            all_card_quantities.values() if
                                            quantity < card_quantity])
        ratio = num_cards_with_more_quantity / len(all_card_quantities)
        difference = self.max_threshold - self.min_threshold
        threshold = self.min_threshold + ratio * difference
        print(num_cards_with_more_quantity, len(all_card_quantities), ratio, threshold, card_quantity)
        return threshold

    def apply(self, card_listing):
        card = Card.objects.get(name__iexact=card_listing.name,
                                printing__name__iexact=card_listing.set)
        condition = get_key_from_choices(CardInventoryLog.CONDITIONS,
                                         card_listing.condition)
        finish = get_key_from_choices(CardLog.CARD_FINISH, card_listing.finish)
        inventory_card = CardInventoryLog.objects.filter(card=card,
                                                         finish=finish,
                                                         condition=condition)
        latest_inventory_card = CardInventoryLog.objects.get_latest(inventory_card).first()
        if not latest_inventory_card:
            raise ValueError(
                'No logs for {0} from {1}'.format(card_listing.name, card_listing.set))
        all_card_quantities = CardInventoryLog.objects.get_totals_for_rarity(
            card_listing.rarity, finish, condition, card_listing.set)
        threshold = self.calc_threshold(all_card_quantities, latest_inventory_card.quantity)
        return MinPriceIgnoreOutliersStrategyDirect(threshold=threshold).apply(card_listing)

class PercentSoldOfMostPricingStrategy(BaseStrategy):

    def get_threshold(self, card):
        total_sold = total_sold_by_card(card)
        cases = cases_to_open(card, total_sold)
        most_cases = cache.get_or_set('most_cases_needed', cases_required(most_sold(card.printing.name)), 100)
        # formula is max_threshold - (max_threshold - 1) * (cases / most_cases) ^ 2x for some x
        ratio = cases / most_cases
        if ratio >= .75:
            return 95 - 94 * (ratio) ** 4
        else:
            return 95

    def apply(self, card_listing):
        if card_listing.number:
            card = Card.objects.get_card(card_listing.name, card_listing.set,
                                         card_listing.number)
        else:
            card = Card.objects.get_card(card_listing.name, card_listing.set)
        threshold = self.get_threshold(card)
        return MinPriceIgnoreOutliersFallbackNonDirectStrategy(
            threshold=threshold).apply(
            card_listing)


class IgnoreStrategy(BaseStrategy):

    def apply(self, card_listing):
        self.logger.warning("Ignored: {0}".format(card_listing.name))
        return None

class PricingStrategy(BaseStrategy):

    def percentile_based_outlier(self, logs, threshold=90):
        prices = np.array(self.prices_as_array(logs))

        diff = (100 - threshold) / 2.0
        try:
            minval, maxval = np.percentile(prices, [diff, 100 - diff])
        except IndexError:
            raise ValueError('All price logs have shipping over $0.99')
        data = np.array([Decimal(str(datum)) for datum in prices])
        outliers = (data < Decimal(str(minval))) | (data > Decimal(str(maxval)))
        non_outliers = np.logical_not(outliers)

        non_outlier_prices = prices[non_outliers]
        logs = [log for log in logs if float(log['price']) in non_outlier_prices]
        return logs

    def get_latest_tcg_logs(self, set_name=None, card_name=None, card_number=None,
                            finish=CardLog.REGULAR, status=None):
        tcg_player_logs = CardLog.objects.filter(
            store_name__icontains='TCG',
            card__name__iexact=card_name).exclude(
            store_name__icontains='Eudemonia').exclude(
            store_name__icontains='EudoGames')

        try:
            time_of_last_scrape = tcg_player_logs.order_by(
                '-scrape_time').first().scrape_time
        except AttributeError:
            raise ValueError(
                'No logs for {0} from {1}'.format(card_name, set_name))


        if status:
            tcg_player_logs = tcg_player_logs.filter(status=status)

        tcg_player_logs = tcg_player_logs.filter(
            scrape_time=time_of_last_scrape, finish=finish)

        if card_name:
            tcg_player_logs = tcg_player_logs.filter(
                card__name__iexact=card_name)
        if set_name:
            tcg_player_logs = tcg_player_logs.filter(
                card__printing__name__iexact=set_name)
        if card_number:
            tcg_player_logs = tcg_player_logs.filter(
                card__number=card_number)

        tcg_player_logs = tcg_player_logs.order_by('price')[:20]

        if not tcg_player_logs:
            raise ValueError(
                'No logs for {0} from {1}'.format(card_name, set_name))


        logs = []
        for log in tcg_player_logs:
            logs.append({
                'price': log.price,
                'stock': log.stock
            })


        return logs

    def prices_as_array(self, logs):
        prices = []
        for log in logs:
            for quantity in range(log['stock']):
                prices.append(float(log['price']))

        return sorted(prices)

    def print_prices(self, card_name, low, logs):
        output = ""
        if low > 0.10:
            card_name = Fore.GREEN + Back.BLACK + 'Card name: {0}'.format(
                card_name) + Style.RESET_ALL
            self.logger.info('Card name: %s', card_name)
            prices = [(log['price'], log['stock']) for log in logs]
            prices.append((low, 9999))
            prices = sorted(prices)
            for price in prices:
                if price[0] != low:
                    output += "%s(%s) " % (price[0], price[1])
                else:
                    our_price = Fore.RED + Back.BLACK + '{0:.2f}(999) '.format(
                        low) + Style.RESET_ALL
                    output += our_price
            self.logger.info(output)
        else:
            self.logger.info('Prices for {0} suppressed'.format(card_name))

    def filter_logs(self, logs):
        return logs

    def find_price(self, set_name=None, card_name=None, card_number=None, finish=CardLog.REGULAR):
        logs = self.get_latest_tcg_logs(set_name=set_name, card_name=card_name,
                                        card_number=card_number, finish=finish)
        non_outlier_logs = self.percentile_based_outlier(logs)
        filtered_logs = self.filter_logs(non_outlier_logs)
        prices = [log['price'] for log in filtered_logs]
        low = round(float(min(prices)) - 0.01, 2)
        if low < 0.05:
            low = 0.05
        self.print_prices(card_name, low, logs)

        return low

    def apply(self, card_listing):
        set_name = card_listing.set
        card_name = card_listing.name
        card_number = card_listing.number
        is_foil = card_listing.finish.lower() =='foil'
        card_listing.price = self.find_price(set_name, card_name, card_number,
                                             is_foil)
        return card_listing


class PricingNonDirect(PricingStrategy):
    def get_latest_tcg_logs(self, set_name=None, card_name=None,
                            card_number=None,
                            finish=CardLog.REGULAR, status=None):
        return super().get_latest_tcg_logs(set_name,card_name,card_number,finish,
                                           CardLog.NON_DIRECT)

class PricingDirect(PricingStrategy):
    def get_latest_tcg_logs(self, set_name=None, card_name=None,
                            card_number=None,
                            finish=CardLog.REGULAR, status=None):
        return super().get_latest_tcg_logs(set_name,card_name,card_number,finish,
                                           CardLog.DIRECT)

class PricingExcludeThreshold(PricingStrategy):

    def __init__(self, threshold, **kwargs):
        super().__init__(**kwargs)
        self.threshold = threshold

    def filter_logs(self, logs):
        filtered_logs = self.percentile_based_outlier(logs,
                                                      threshold=self.threshold)
        return filtered_logs

class MinPriceIgnoreOutliersStrategyDirect(PricingDirect, PricingExcludeThreshold):
    pass

class MinPriceIgnoreOutliersStrategyNonDirect(PricingNonDirect, PricingExcludeThreshold):
    pass

class MinPriceIgnoreOutliersFallbackNonDirectStrategy(PricingExcludeThreshold):

    def get_latest_tcg_logs(self, set_name=None, card_name=None,
                            card_number=None,
                            finish=CardLog.REGULAR, status=None):
        logs = super().get_latest_tcg_logs(set_name, card_name, card_number,
                                            finish, CardLog.DIRECT)
        if not logs:
            logs = super().get_latest_tcg_logs(set_name, card_name, card_number,
                                               finish, CardLog.NON_DIRECT)
        return logs

class PricingExcludePercentile(PricingStrategy):

    def __init__(self, percentile, **kwargs):
        super().__init__(**kwargs)
        self.percentile = percentile

    def filter_below_percentile(self, logs, percentile):
        prices = np.array(self.prices_as_array(logs))

        minval = np.percentile(prices,percentile)

        data = np.array([Decimal(str(datum)) for datum in prices])
        above_percentile = (data >= Decimal(str(minval)))

        above_percentile_prices = prices[above_percentile]
        logs = [log for log in logs if float(log['price']) in above_percentile_prices]
        return logs

    def filter_logs(self, logs):
        filtered_logs = self.filter_below_percentile(logs, self.percentile)
        return filtered_logs
    