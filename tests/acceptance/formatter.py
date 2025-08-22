import six
from behave.formatter.pretty import PrettyFormatter
from behave.formatter.base import Formatter
from behave.textutil import indent


class BeautifulFormatter(PrettyFormatter):
    """
    Quick patch for the most annoying bug of the PrettyFormatter.
    Eventually we should move to our own CustomFormatter,
    so that captured logs and stdout are printed AFTER the step,
    like in high-quality gherkin runners in other languages.
    """
    def result(self, step):
        if not self.monochrome:
            lines = self.step_lines + 1
            if self.show_multiline:
                if step.table:
                    lines += len(step.table.rows) + 1
                if step.text:
                    lines += len(step.text.splitlines()) + 2
            # self.stream.write(up(lines))  # NO GOD PLEASE NO
            arguments = []
            location = None
            if self._match:
                arguments = self._match.arguments
                location = self._match.location
            self.print_step(step.status, arguments, location, True)
        if step.error_message:
            self.stream.write(indent(step.error_message.strip(), u"      "))
            self.stream.write("\n\n")
        self.stream.flush()

    def match(self, match):
        self._match = match
        self.print_statement()
        self.stream.flush()


class CustomFormatter(Formatter):
    """
    Half-assed attempt at making our own formatter entirely.
    We don't use this for now, we're using the BeautifulFormatter above.
    """

    # indentation = "\t"
    indentation = "  "

    def indent(self, text):
        p = self.indentation
        lines = text.split("\n")
        return "\n".join(["%s%s" % ("" if "" == line else p, line) for line in lines])

    def feature(self, feature):
        self.stream.write(u"\n")
        self.stream.write(u"%s: %s\n" % (
            feature.keyword,
            feature.name,
        ))
        for line in feature.description:
            self.stream.write(self.indent(u"%s\n" % line))
        self.stream.flush()

    def scenario(self, scenario):
        self.stream.write(u"\n")
        self.stream.write(u"%s: %s\n" % (
            scenario.keyword,
            scenario.name,
        ))
        self.stream.flush()

    def result(self, step):
        self.stream.write(self.indent(u"%s %s\n" % (
            step.keyword,
            step.name,
        )))
        if step.error_message:
            self.stream.write(self.indent(step.error_message.strip()))
            self.stream.write("\n")
        self.stream.flush()
