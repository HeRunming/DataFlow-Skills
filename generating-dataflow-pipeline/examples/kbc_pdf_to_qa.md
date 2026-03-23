# Example: File Path to QA Pipeline (Knowledge Base Cleaning)

## User Request
"Extract QA pairs from documents after cleaning and chunking"

## Note
KBC supports multiple file types: `.pdf`, `.png`, `.jpg`, `.jpeg`, `.webp`, `.gif` (→ MinerU), `.html`, `.xml` (→ trafilatura), `.txt`, `.md` (→ passed through directly to chunking). This example uses PDF paths, but the same pipeline works for `.md` or `.txt` paths — Step 1 simply skips conversion for those types.

## Sample Data
```jsonl
{"pdf_path": "/data/research_paper.pdf"}
{"pdf_path": "/data/technical_doc.pdf"}
```

## Response

### Intermediate Operator Decision
```json
{
  "ops": ["KBCCompositeCleaningFlashOperator", "Text2QAGenerator", "FormatStrPromptedGenerator", "GeneralFilter"],
  "field_flow": "pdf_path -> cleaned_chunk -> question+answer -> qa_score -> filtered",
  "reason": "Input is PDF file paths, so KBC is valid. Text2QAGenerator produces QA pairs. Quality evaluation needs both question and answer fields, so FormatStrPromptedGenerator scores them together, then GeneralFilter filters by score. PromptedFilter is not used because it only accepts a single input_key."
}
```

### 1. Field Mapping
```
Available in sample:
  - pdf_path (file path - valid for KBC)

To be generated:
  - cleaned_chunk (output from KBC step)
  - question (output from QA gen step)
  - answer (output from QA gen step)
  - qa_prompt (output from QA gen step)
  - qa_score (output from scoring step)

Field flow:
  pdf_path → [KBC] → cleaned_chunk → [Text2QA] → question, answer → [Score] → qa_score → [Filter]
```

### 2. Ordered Operator List
1. **KBCCompositeCleaningFlashOperator**: Clean and chunk documents
   - Why: Input is file path, need File→Markdown→Chunks→Cleaned pipeline
   - Input: pdf_path (exists in sample, is file path)
   - Output: cleaned_chunk

2. **Text2QAGenerator**: Generate QA pairs from chunks
   - Why: Domain-specific operator for QA construction
   - Input: cleaned_chunk (created by step 1)
   - Output: question, answer, qa_prompt

3. **FormatStrPromptedGenerator**: Score QA pair quality
   - Why: Quality evaluation requires both question and answer as input (multi-field), so PromptedFilter (single input_key) is insufficient
   - Input: question + answer (created by step 2)
   - Output: qa_score

4. **GeneralFilter**: Filter low-quality pairs
   - Why: Keep only QA pairs with score >= 4
   - Input: qa_score (created by step 3)

### 3. Reasoning Summary
- KBC is valid because input field is pdf_path (file path, not text content)
- Text2QAGenerator is preferred over generic PromptedGenerator for QA construction
- PromptedFilter only accepts a single input_key — evaluating QA quality requires both question and answer, so we use FormatStrPromptedGenerator to score + GeneralFilter to filter
- Field dependencies properly ordered: each step consumes fields created by previous steps
- Total pipeline: 4 operators, semantically complete dataflow

### 4. Complete Standard Pipeline Code
```python
from dataflow.operators.core_text import Text2QAGenerator, FormatStrPromptedGenerator, GeneralFilter
from dataflow.operators.knowledge_cleaning import KBCCompositeCleaningFlashOperator
from dataflow.prompts.core_text import FormatStrPrompt
from dataflow.serving import APILLMServing_request
from dataflow.utils.storage import FileStorage

class PDFtoQAPipeline:
    def __init__(self):
        # Input file MUST be JSONL format (one JSON object per line):
        # {"pdf_path": "/data/paper1.pdf"}
        # {"pdf_path": "/data/paper2.pdf"}
        self.storage = FileStorage(
            first_entry_file_name="pdf_list.jsonl",
            cache_path="./cache_pdf_qa",
            file_name_prefix="pdf_step",
            cache_type="jsonl"
        )

        self.llm_serving = APILLMServing_request(
            api_url="https://api.openai.com/v1/chat/completions",
            model_name="gpt-4o",
            max_workers=10
        )

        self.kbc_cleaner = KBCCompositeCleaningFlashOperator(
            llm_serving=self.llm_serving,
            intermediate_dir="./kbc_intermediate/",
            mineru_model_path="opendatalab/MinerU2.5-2509-1.2B",  # HuggingFace model ID or local path
            chunk_size=512,
            chunk_overlap=50,
            lang="en"
        )

        self.qa_generator = Text2QAGenerator(
            llm_serving=self.llm_serving
        )

        # Score QA pairs using both question + answer
        self.qa_scorer = FormatStrPromptedGenerator(
            self.llm_serving,
            system_prompt=(
                "Evaluate this QA pair quality on scale 1-5. "
                "Consider: question clarity, answer accuracy, answer completeness, relevance to source. "
                "Output only the numeric score."
            ),
            prompt_template=FormatStrPrompt(
                f_str_template="Question: {question}\nAnswer: {answer}"
            ),
        )

        self.qa_filter = GeneralFilter([
            lambda df: df["qa_score"].astype(float) >= 4,
        ])

    def forward(self):
        self.kbc_cleaner.run(
            storage=self.storage.step(),
            input_key="pdf_path",
            output_key="cleaned_chunk"
        )

        self.qa_generator.run(
            storage=self.storage.step(),
            input_key="cleaned_chunk",
            input_question_num=2,
            output_prompt_key="qa_prompt",
            output_question_key="question",
            output_answer_key="answer"
        )

        self.qa_scorer.run(
            storage=self.storage.step(),
            output_key="qa_score",
            question="question",
            answer="answer",
        )

        self.qa_filter.run(
            storage=self.storage.step(),
        )

if __name__ == "__main__":
    pipeline = PDFtoQAPipeline()
    pipeline.forward()
```

### 5. Adjustable Parameters / Caveats

**Tunable Parameters**:
- `chunk_size`: Increase to 1024 for longer context
- `chunk_overlap`: Increase to 100 for better continuity
- `input_question_num`: Change to 1 or 3 to control QA density
- Score threshold in `GeneralFilter`: Lower to 3 for more lenient filtering
- `lang`: Set to "zh" for Chinese documents
- `max_workers`: Increase for faster processing

**Fallback Strategies**:
- If < 30% pass filter: Increase chunk_size to 1024 for more context
- If questions too generic: Modify Text2QAGenerator configuration
- If answers incomplete: Increase chunk_size or adjust overlap

**Caveats**:
- KBCCompositeCleaningFlashOperator requires GPU for optimal performance (for PDF/image inputs; .md/.txt skip MinerU)
- Each document generates multiple chunks (N chunks × 2 QA = 2N pairs)
- `mineru_model_path` must be set to a valid HuggingFace model ID or local path — `None` raises `ValueError`

**Debugging**:
- Check `cache_pdf_qa/pdf_step_1.jsonl` for cleaned chunks
- Check `cache_pdf_qa/pdf_step_2.jsonl` for QA pairs
- Check `cache_pdf_qa/pdf_step_3.jsonl` for scored results
- Check `cache_pdf_qa/pdf_step_4.jsonl` for filtered results
- Monitor pass rate by comparing row counts
