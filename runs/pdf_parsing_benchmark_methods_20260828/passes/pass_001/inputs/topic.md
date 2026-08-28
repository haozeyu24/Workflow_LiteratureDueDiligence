# Topic

PDF parsing and document-understanding methods for table-heavy, layout-complex documents, with clinical trial papers as the central motivating use case and other table-heavy document genres as comparators when they contribute benchmark methods or evaluation rubrics.

The run should capture both visual-language-model-based methods and non-visual pipelines. Relevant non-visual methods include OCR plus NLP, GROBID-like scientific PDF parsing, rule-based or heuristic table extraction, layout-aware but text-first models, and table-structure recognition systems. Relevant visual or multimodal methods include document image understanding, vision-language models, multimodal transformers, and tools that evaluate rendered pages or page regions rather than only extracted text.

Benchmarking rubrics are a core evidence target. Reviewers should extract metrics such as cell-level accuracy, table detection precision/recall, structure recognition F1, text extraction accuracy, reading-order fidelity, entity/value extraction accuracy, page/layout segmentation scores, document-level task success, human adjudication criteria, error categories, and robustness across document types.

## Retrieval Scope Notes

- PubMed query drivers: PDF parsing; table extraction; clinical trial report extraction; biomedical PDF parsing; scientific document understanding; layout analysis; OCR; benchmark; tool comparison; visual language model; multimodal document understanding.
- Comparator scope: non-clinical scientific articles, earnings reports, annual reports, financial filings, forms, invoices, and other table-rich PDFs when they provide benchmark datasets, evaluation methods, or transferable tool-comparison evidence.
- Secondary synthesis context: whether a tightly scoped 2-3 month paper is feasible; what benchmark design would be publishable; which document types and extraction targets are narrow enough for a fast study.
- Deferred adjacent biology: clinical trial eligibility extraction, trial summarization, evidence synthesis, and medical relation extraction unless the paper explicitly evaluates PDF parsing, table extraction, or layout-aware document conversion.
