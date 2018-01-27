# NOTE: This code does not actually run. It is just a sample.
This repo contains files related to updating magic card card prices from a csv file.
The process starts with tcg_proccess_inventory.py which processes each row by
calling update_csv_row from rules_parser.py. New prices can be determined by many factors,
such as price of competetors, how "hot" the card is, price of card, 
if card is being sold direct, etc. The rules determining which pricing strategy 
to apply to which cards are defined in rules.py, where the higher the rule is in
the list, the higher priority that rule has over other rules.
