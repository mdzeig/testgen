# testgen: Automatic Test Generation

`testgen` provides the script `maketest` for automatically producing tests with user-defined content balancing. Currently, this is restricted to multiple choice tests. The user needs to provide an item bank and a configuration files. Examples of these files are contained in the `examples` folder. We can create a test by entering

```
maketest item_bank.yaml config.yaml
```

within the `examples` folder. This will generate two LaTeX files (one with an answer key and one without) and use `pdflatex` to create a PDF file. Thus, a working TeX distribution is necessary to use `maketest`. This distribution must include the `exam` document class, which is part of the TeXLive distribution (<https://www.tug.org/texlive/>). Additionally, this script depends on PyYAML (<http://pyyaml.org>).
