""" Random test generation with content balancing. """

from subprocess import call
import random
import string
import yaml

# Template for the generated LaTeX code. Options for the 'exam' document class
# can be provided through 'docclass_opts'. The LaTeX code for the questions is
# provided through 'questions'
LATEX_TEMPLATE = string.Template(
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

# Make function again?
class MultipleChoiceItem:
    """ Multiple choice item. Stores the question text for the item, the text of
    the available responses, the correct response and the content tags.
    """
    def __init__(self, text, responses, correct, tags):
        self.text = text
        self.responses = responses
        self.correct = correct
        self.tags = set(tags)

    def has_tags(self, tags):
        """ Determine whether the item has each of a set of tags.
        """
        return self.tags.issuperset(tags)

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
    # Select the test items
    test_items = select_items(load_item_bank(bank_file),
                              load_config(config_file),
                              max_tries)
    # Create the LaTeX code for the test items.
    item_latex = '\n'.join([item.latex() for item in test_items])
    # Create a PDF for the test with (True) and without (False) showing the
    # answer key.
    for show_key in [False, True]:
        create_test_pdf(item_latex, outfile, show_key)

def load_item_bank(bank_file):
    """ Load an item bank. Returns a list of multiple choice items.
    """
    with open(bank_file, 'r') as the_file:
        item_bank = yaml.load(the_file)
    return [MultipleChoiceItem(**item) for item in item_bank]

def load_config(config_file):
    """ Load a configuration file. Returns a list of dictionaries. Each dictionary
    defines an item inclusion criterion and specifies the number of items satistfying
    the criterion that should be included. Inclusion criteria specify two sets of tags.
    'include' defines which tags an item must have to be included by the criterion and
    'exclude' defines which tags an item cannot have to be included by the criterion.
    """
    with open(config_file, 'r') as the_file:
        config = yaml.load(the_file)
    config['exclude'] = set(config['exclude'])
    return [{'include': set([k]), 'exclude': config['exclude'], 'n': v}
            for k, v in config['include'].items()]

def satisfies_criterion(item, criterion):
    """ Does the item satisfy the criterion? """
    # An item satisfies a criterion when its tags include every tag that needs
    # to be included and does not include any tag that needs to be excluded
    return (item.has_tags(criterion['include'])
            and not item.has_tags(criterion['exclude']))

def select_items(item_bank, config, max_tries):
    """ Sample test items in the numbers specified by the configuration file. Currently,
    if the sampler is unable to complete a test (because it runs out of items for some
    tag), it restarts from the begining of the test.
    """
    tries = 0
    test_items = []
    while not test_items:
        if tries == max_tries:
            # Throw an error if we reach the maximum number of times to try to
            # create a test matching the content criteria specified by the
            # configuration file.
            msg = "Tried to assemble the test %d times. " % max_tries
            msg = "%sIncrease 'max_tries' or check configuration file." % msg
            raise AssertionError(msg)
        # Set of indices that have not already been included in the test
        available = set(range(len(item_bank)))
        for criterion in config:
            # Determine the indices of all items satistfying the current criterion
            useable = [i for i in available if
                       satisfies_criterion(item_bank[i], criterion)]
            if len(useable) < criterion['n']:
                # We've failed to create a test, so try again
                test_items = []
                tries += 1
                break
            for _ in range(criterion['n']):
                # Sample an item index and add it to the list of test indices.
                # Then, remove it from the lists of useable and avaiable item
                # indices, so that it will only appear in the test once.
                item = random.choice(useable)
                test_items.append(item)
                useable.remove(item)
                available.remove(item)
    return [item_bank[i] for i in test_items]

def create_test_pdf(item_latex, outfile, show_key=False):
    """ Write the latex code given the item text and use pdflatex to produce a PDF.
    """
    if show_key:
        # To show the answer key we need to pass the 'answers' option to the
        # exam LaTeX document class
        docclass_opts = '[answers]'
        latex_file = outfile + '_and_key.tex'
    else:
        docclass_opts = ''
        latex_file = outfile + '.tex'
    # The LaTeX code is generated by inserting the document class options and
    # LaTeX code for the test items into a LaTeX template. The template is
    # provided by the latex_template function.
    latex_code = LATEX_TEMPLATE.substitute({'docclass_opts': docclass_opts,
                                            'questions': item_latex})
    # Create the LaTeX file and use pdflatex to create the PDF
    with open(latex_file, 'w') as the_file:
        the_file.write(latex_code)
    return call(['pdflatex', latex_file])
