# Topic

PDF parsing and document-understanding methods for table-heavy, layout-complex documents, with clinical trial papers as the central motivating use case and other table-heavy document genres as comparators when they contribute benchmark methods or evaluation rubrics.

The run should capture both visual-language-model-based methods and non-visual pipelines. Relevant non-visual methods include OCR plus NLP, GROBID-like scientific PDF parsing, rule-based or heuristic table extraction, layout-aware but text-first models, and table-structure recognition systems. Relevant visual or multimodal methods include document image understanding, vision-language models, multimodal transformers, and tools that evaluate rendered pages or page regions rather than only extracted text.

Benchmarking rubrics are a core evidence target. Reviewers should extract metrics such as cell-level accuracy, table detection precision/recall, structure recognition F1, text extraction accuracy, reading-order fidelity, entity/value extraction accuracy, page/layout segmentation scores, document-level task success, human adjudication criteria, error categories, and robustness across document types.

## Pass 2 Learned Focus

Pass 1 showed that broad clinical and multimodal AI terms retrieve many papers where `table`, `extraction`, `evaluation`, or `multimodal` describe ordinary clinical-study methods rather than PDF/table parsing. Pass 2 should focus on papers where the title or abstract makes document objects central: PDFs, document images, pages, tables, cells, rows, columns, reading order, page/layout segmentation, OCR outputs, scientific articles, forms, reports, and benchmark datasets. Visual-language-model papers are in scope only when the visual/document input and extraction/evaluation target are document-centered.

## Retrieval Scope Notes

- PubMed query drivers: PDF parsing; table extraction; table information extraction; table structure recognition; table detection; clinical trial table extraction; biomedical PDF parsing; scientific document understanding; layout-aware text extraction; document image analysis; page segmentation; reading order; OCR; benchmark; tool comparison; visual language model for documents; document-centered multimodal extraction.
- Comparator scope: non-clinical scientific articles, earnings reports, annual reports, financial filings, forms, invoices, and other table-rich PDFs when they provide benchmark datasets, evaluation methods, or transferable tool-comparison evidence.
- Secondary synthesis context: whether a tightly scoped 2-3 month paper is feasible; what benchmark design would be publishable; which document types and extraction targets are narrow enough for a fast study.
- Deferred adjacent biology: clinical trial eligibility extraction, trial summarization, evidence synthesis, and medical relation extraction unless the paper explicitly evaluates PDF parsing, table extraction, or layout-aware document conversion.
