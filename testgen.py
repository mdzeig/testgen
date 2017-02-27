""" Random test generation with content balancing. """

from subprocess import call
import random
import string
import yaml

class TestItem:
    """ Multiple choice item.
    """
    def __init__(self, text, responses, correct, tags):
        self.text = text
        self.responses = responses
        self.correct = correct
        self.tags = set(tags)

    def has_tags(self, head, *tail):
        """ Determine whether the item has each of a set of tags.
        """
        return self.tags.issuperset([head] + list(tail))

    def latex(self):
        """ Return a LaTeX representation of the item.
        """
        question = '\\question %s' % self.text
        responses = '\n'.join(['\\CorrectChoice %s' % resp
                               if i == self.correct else '\\choice %s' % resp
                               for i, resp in enumerate(self.responses)])
        responses = '\\begin{choices}\n %s\n \\end{choices}\n' % responses
        return '\n'.join([question, responses])

def maketest(bank_file, config_file, outfile='test', max_tries=10):
    """ Randomly generate a test from an item bank and a configuation file. The
    item bank associates one or more tags with each item. The configuration file
    specifies which items should be sampled using combinations of tags. Both the
    item bank and configuration files should be valid YAML files.

    Arguments:
        - bank_file: item bank file name
        - config_file: configuration file name
        - outfile: output file name, without extension
        - max_tries: maximum number of times to try to generate a test.
    """
    test_items = select_items(load_item_bank(bank_file),
                              load_config(config_file),
                              max_tries)
    item_latex = '\n'.join([item.latex() for item in test_items])
    # Create a PDF for the test with and without showing the answer key
    for show_key in [False, True]:
        create_test_pdf(item_latex, outfile, show_key)

def load_item_bank(bank_file):
    """ Load an item bank.
    """
    with open(bank_file, 'r') as the_file:
        item_bank = yaml.load(the_file)
    return [TestItem(**item) for item in item_bank]

def load_config(config_file):
    """ Load a configuration file.
    """
    with open(config_file, 'r') as the_file:
        config = yaml.load(the_file)
    config['exclude'] = set(config['exclude'])
    return config

def select_items(item_bank, config, max_tries):
    """ Sample test items in the numbers specified by the configuration file. Currently,
    if the sampler is unable to complete a test (because it runs out of items for some
    tag), it restarts from the begining of the test.
    """
    tries = 0
    test_items = []
    while not test_items:
        if tries == max_tries:
            msg = "Tried to assemble the test %d times. " % max_tries
            msg = "%sIncrease 'max_tries' or check configuration file." % msg
            raise AssertionError(msg)
        avail = set(range(len(item_bank)))
        for tag, num in config['include'].items():
            useable = [item for item in avail
                       if item_bank[item].has_tags(tag)
                       and not item_bank[item].has_tags(*config['exclude'])]
            if len(useable) < num:
                test_items = []
                tries += 1
                break
            for _ in range(num):
                item = random.choice(useable)
                useable.remove(item)
                avail.remove(item)
                test_items.append(item)
    return [item_bank[item] for item in test_items]

def create_test_pdf(item_latex, outfile, show_key=False):
    """ Write the latex code given the item text.
    """
    if show_key:
        docclass_opts = '[answers]'
        latex_file = outfile + '_and_key.tex'
    else:
        docclass_opts = ''
        latex_file = outfile + '.tex'
    latex_code = latex_template().substitute({'docclass_opts': docclass_opts,
                                              'questions': item_latex})
    with open(latex_file, 'w') as the_file:
        the_file.write(latex_code)
    return call(['pdflatex', latex_file])

def latex_template():
    """ Template for writing LaTeX code from item code. """
    return string.Template(
        r"""\documentclass$docclass_opts{exam}

        \begin{document}
            \begin{center}
                {\large \textbf{PYSC 2010, Research Methods Midterm, Spring 2017}}
            \end{center}

            \vspace{0.2in}
            \makebox[\textwidth]{Name:\enspace\hrulefill}
            \vspace{.4in}

            \begin{center}
                \fbox{\fbox{\parbox{5.5in}{\centering
                    Answer the questions in the spaces provided on the
                    question sheets.  If you run out of room for an answer,
                    continue on the back of the page.}}}
            \end{center}

            \vspace{.3in}

            \begin{questions}
                $questions
            \end{questions}
        \end{document}""")
