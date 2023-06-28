import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import unicodedata

# initialize the transformer model and tokenizer
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
DEFAULT_SUMMARIZATION_MODEL = "facebook/bart-large-cnn"  # adjust the model as needed
summarization_transformer = AutoModelForSeq2SeqLM.from_pretrained(DEFAULT_SUMMARIZATION_MODEL).to(device)
summarization_tokenizer = AutoTokenizer.from_pretrained(DEFAULT_SUMMARIZATION_MODEL)

DEFAULT_SUMMARIZE_PARAMS = {
    "temperature": 1.0,
    "repetition_penalty": 1.0,
    "max_length": 500,
    "min_length": 200,
    "length_penalty": 1.5,
    "bad_words": [
        "\n",
        '"',
        "*",
        "[",
        "]",
        "{",
        "}",
        ":",
        "(",
        ")",
        "<",
        ">",
        "Â",
        "The text ends",
        "The story ends",
        "The text is",
        "The story is",
    ],
}

def summarize_chunks(text: str, params: dict) -> str:
    try:
        return summarize(text, params)
    except IndexError:
        print(
            "Sequence length too large for model, cutting text in half and calling again"
        )
        new_params = params.copy()
        new_params["max_length"] = new_params["max_length"] // 2
        new_params["min_length"] = new_params["min_length"] // 2
        return summarize_chunks(
            text[: (len(text) // 2)], new_params
        ) + summarize_chunks(text[(len(text) // 2):], new_params)


def summarize(text: str, params: dict) -> str:
    # Tokenize input
    inputs = summarization_tokenizer(text, return_tensors="pt").to(device)
    token_count = len(inputs[0])

    bad_words_ids = [
        summarization_tokenizer(bad_word, add_special_tokens=False).input_ids
        for bad_word in params["bad_words"]
    ]
    summary_ids = summarization_transformer.generate(
        inputs["input_ids"],
        num_beams=2,
        max_length=max(token_count, int(params["max_length"])),
        min_length=min(token_count, int(params["min_length"])),
        repetition_penalty=float(params["repetition_penalty"]),
        temperature=float(params["temperature"]),
        length_penalty=float(params["length_penalty"]),
        bad_words_ids=bad_words_ids,
    )
    summary = summarization_tokenizer.batch_decode(
        summary_ids, skip_special_tokens=True, clean_up_tokenization_spaces=True
    )[0]
    summary = normalize_string(summary)
    return summary


def normalize_string(input: str) -> str:
    output = " ".join(unicodedata.normalize("NFKC", input).strip().split())
    return output


def local_summarize(text, params=None):
    if params is None:
        params = DEFAULT_SUMMARIZE_PARAMS.copy()

    print("Summary input:", text, sep="\n")
    summary = summarize_chunks(text, params)
    print("Summary output:", summary, sep="\n")
    return summary


# sample usage
text = "This is a sample text that I would like to summarize..."
params = DEFAULT_SUMMARIZE_PARAMS.copy()  # or use your own
summary = local_summarize(text, params)
