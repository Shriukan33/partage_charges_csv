import re
from decimal import Decimal
from collections import defaultdict
from bs4.dammit import UnicodeDammit
from dataclasses import dataclass
from datetime import datetime
from sys import argv


REGEX_ACHAT = r"(ACHAT\sCB)\s*(.*)\s(\d{2}\.\d{2}\.\d{2})"
REGEX_PRELEVEMENT = r'(PRELEVEMENT\sDE)\s(.*)\s(REF\s\:)'
REGEX_VIREMENT = r'(VIREMENT\sDE)\s(.*)\s(REFERENCE\s\:)'

def get_encoding(filepath):
    with open(filepath, "rb") as f:
        content = f.read()

    suggestion = UnicodeDammit(content)
    return suggestion.original_encoding

filepath = argv[1]
separator = ";"
encoding = get_encoding(filepath)

@dataclass
class Transaction:
    date: datetime
    libelle: str
    amount: Decimal

    def __str__(self):
        return f"{self.date} - {self.libelle} - {self.amount}"

total_per_provider = defaultdict(list)
total_per_provider_revenus = defaultdict(list)

with open(filepath, "r", encoding=encoding) as f:
    content = f.read().splitlines()

for line in content:
    line = line.split(separator)
    try:
        date = datetime.strptime(line[0], "%d/%m/%Y").date()
    except ValueError:
        continue
    
    transaction = Transaction(date, line[1], Decimal(line[2].replace(",", ".")))

    achat = re.search(REGEX_ACHAT, transaction.libelle)
    prelevement = re.search(REGEX_PRELEVEMENT, transaction.libelle)
    virement = re.search(REGEX_VIREMENT, transaction.libelle)

    the_match = achat or prelevement
    provider = " ".join(the_match.group(2).split()) if the_match else None


    if virement:
        rev_provider = " ".join(virement.group(2).split())
        total_per_provider_revenus[rev_provider].append(transaction.amount)
        continue

    if not the_match and not virement:
        print("OTHER : ", transaction.libelle)
        continue

    if the_match:
        total_per_provider[provider].append(transaction.amount)


sorted_by_provider_alphabetically = dict(sorted(total_per_provider.items(), key=lambda x: x[0]))

for provider, total in sorted_by_provider_alphabetically.items():
    print(f"{provider}: {sum(total)} ---- Details : ({[float(t) for t in total]})")
    
print(f"Total: {sum(sum(total) for total in total_per_provider.values())}")

print("#" * 50)

for provider, total in total_per_provider_revenus.items():
    print(f"{provider}: {sum(total)}")
    
print(f"Total: {sum(sum(total) for total in total_per_provider_revenus.values())}")
