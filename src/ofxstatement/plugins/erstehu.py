from ofxstatement.plugin import Plugin
from ofxstatement.parser import StatementParser
from ofxstatement.statement import Statement, StatementLine, generate_transaction_id

import csv
from datetime import datetime
from locale import atof
import re

class ErsteHuPlugin(Plugin):
    """Erste(HU) from CSV
    """

    def get_parser(self, filename):
        return ErsteHuParser(filename)


class ErsteHuParser(StatementParser):
    bank_id = 'ErsteBankHU'
    date_format = '%Y.%m.%d.'
    valid_header = [
        u"Tranzakció dátuma",
	    u"Partner neve/Másodlagos azonosító típusa",
	    u"Partner számlaszáma/másodlagos azonosítója",
	    u"Számla neve",
	    u"Számlaszám",
	    u"Tranzakció típusa",
	    u"Tranzakció összege",
	    u"Tranzakció devizaneme",
	    u"Bevétel/Kiadás",
	    u"Kártyaszám",
	    u"Értéknap",
	    u"Közlemény",
	    u"Megbízás azonosító",
	    u"Részletek",
	    u"Egyenleg",
	    u"Devizanem",
	    u"Hitelügylet azonosító"
    ]

    def __init__(self, filename):
        self.filename = filename

    def parse(self):
        """Main entry point for parsers
        """
        self.statements = []
        with open(self.filename, "r", encoding="latin2", newline='') as f:
            for line in csv.DictReader(fix_quotes(f), escapechar='\\'):
                self._parse_line(line)

        print(self.statements)
        print(len(self.statements))

        return self.statements

    def _parse_line(self, item):
        sline = StatementLine()

        accountid = item[u"Számlaszám"]
        currency = item[u"Tranzakció devizaneme"]

        stmt = self._find_or_create_statement(accountid, currency)

        sline.date = datetime.strptime(item[u"Értéknap"], self.date_format)
        sline.date_user = datetime.strptime(item[u"Tranzakció dátuma"], self.date_format)
        sline.amount = atof(item[u"Tranzakció összege"])
        sline.memo = item[u"Részletek"]

        sline.id = generate_transaction_id(sline)

        sline.assert_valid()
        stmt.lines.append(sline)

    def _find_or_create_statement(self, accountid, currency):
        stmt = next(filter(lambda s: s.account_id == accountid and s.currency == currency, self.statements), None)
        if stmt is None:
            stmt = Statement()
            stmt.bank_id = self.bank_id
            stmt.account_id = accountid
            stmt.account_type = "CREDITLINE"
            stmt.currency = currency
            self.statements.append(stmt)

        return stmt


def fix_quotes(iterable):
    for line in iterable:
        yield re.sub(r"(?<=[^,\\])\"(?=[^,])", '\\"', line)
