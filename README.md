# GenOlympiad

[![Project Page](https://img.shields.io/badge/Project-Page-2563EB?style=flat-square&logo=googlechrome&logoColor=white)](https://genolympiad.github.io/)
[![Paper](https://img.shields.io/badge/arXiv-2610.26850-B31B1B?style=flat-square&logo=arxiv&logoColor=white)](https://arxiv.org/abs/2610.26850)
[![Dataset](https://img.shields.io/badge/🤗%20Hugging%20Face-Dataset-FFD21E?style=flat-square)](https://huggingface.co/datasets/XavierHugh/GenOlympiad-images)

GenOlympiad is a benchmark of 801 hard text prompts for text-to-image models. Each task has a prompt and an evaluation program. The program asks a judge VLM easy and hard questions about the generated image, and it scores the answers with code. The tasks cover nine capability axes: text fidelity (83 tasks), counterfactual instruction following (95), symbolic systems (83), world-knowledge grounding (82), physical consistency (92), quantitative precision (87), spatial and 3-D reasoning (83), latent computation (109) and long-range consistency (87). The strict score of a task is 100 only when every hard question passes. The relaxed score is the weight sum of the hard questions that pass.

## News

[2026/11/18] Added **Qwen4-Max**: **38.2 Strict / 54.4 Relaxed**. Final paper-protocol results converged after eight reread rounds: 791 generated images, 756 scored tasks, 32 withheld, 3 deferred, and 10 not generated out of 801 tasks.

[2026/11/17] Added 17 new model entries to the existing tables. Previously published scores are retained for overlapping model names.

[2026/11/10] Added GPT-Image-2.6 Sunburst results: **17.4 Strict / 33.6 Relaxed**. The model was [released on November 4, 2026](https://openai.com/index/introducing-images-2-6/).

[2026/10/09] GenOlympiad is released!

## Leaderboard

Two tables: the strict score and the relaxed score, from 0 to 100.

Overall is the mean over all scored tasks of a model.

Withheld tasks are not included when calculating scores for individual axes or the overall benchmark.

GPT-Image-2.6 Sunburst results follow the Table 1 protocol: the initial judgment plus four rounds of cold reads, with scored tasks as the denominator. Overall is aggregated over scored tasks, rather than an unweighted average of axis scores.

New entries from the November 17 export use the scored-task denominator (`strict` / `relaxed`); withheld and non-generated tasks are excluded. Axis-level Strict and Relaxed scores are included from the revised export. The new runs use one sample per task.

### Strict score

| Model | Text | C-Fact | Symbol | World | Phys | Quant | Spatial | Latent | Long | Overall |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **Coding Models** | | | | | | | | | | |
| Kimi K3.1 Pro | 73.8 | 47.6 | 47.5 | 22.9 | 32.9 | 51.4 | 32.4 | 57.4 | 28.9 | 44.5 |
| DeepSeek V4.1 Flash | 64.4 | 40.8 | 46.2 | 20.0 | 30.0 | 38.9 | 33.3 | 56.5 | 35.2 | 43.4 |
| GPT-6 Astra | 65.4 | 38.4 | 45.5 | 27.5 | 25.6 | 40.8 | 26.7 | 58.4 | 30.0 | 40.5 |
| Gemini 4 Argon | 62.8 | 41.2 | 37.7 | 21.7 | 28.6 | 38.7 | 30.7 | 55.3 | 34.6 | 39.9 |
| Qwen4-Max | 72.5 | 34.5 | 43.9 | 29.3 | 27.1 | 24.4 | 22.5 | 55.2 | 29.8 | 38.2 |
| Gemini 3.8 Flash | 72.2 | 36.5 | 37.2 | 20.0 | 29.9 | 26.4 | 24.3 | 56.6 | 27.4 | 37.8 |
| GPT-5.6 Sol | 62.5 | 32.2 | 42.3 | 26.0 | 27.7 | 31.6 | 28.2 | 53.3 | 28.4 | 37.5 |
| Mistral Large 4 | 64.5 | 32.1 | 38.4 | 21.2 | 23.3 | 29.2 | 20.3 | 55.6 | 25.7 | 35.9 |
| GPT-6 Luna | 53.8 | 38.2 | 41.2 | 16.2 | 17.3 | 39.2 | 23.3 | 51.4 | 26.6 | 35.1 |
| GPT-5.6 Terra | 54.3 | 33.3 | 45.6 | 14.7 | 21.2 | 38.7 | 19.2 | 56.6 | 21.1 | 35.0 |
| Claude Haiku 5.5 | 54.3 | 34.5 | 28.8 | 15.5 | 21.8 | 34.8 | 18.6 | 57.1 | 25.0 | 33.3 |
| GPT-5.6 Luna | 45.9 | 25.3 | 35.1 | 13.9 | 13.6 | 33.8 | 16.4 | 49.5 | 20.5 | 28.9 |
| GLM-5.3 Flash | 24.1 | 33.3 | 27.9 | 16.7 | 21.0 | 23.3 | 14.5 | 53.5 | 12.1 | 26.9 |
| GLM-5.3 | 32.4 | 21.8 | 31.5 | 17.6 | 16.0 | 27.1 | 14.5 | 43.3 | 26.7 | 26.4 |
| Muse Glimmer 30B | 31.6 | 23.8 | 24.0 | 17.6 | 17.7 | 30.4 | 14.5 | 47.4 | 17.6 | 25.7 |
| **Prompt Engineering on GPT-Image-2.5 Sunburst** | | | | | | | | | | |
| GPT 5.6 Sol | 62.2 | 33.0 | 30.4 | 17.8 | 25.0 | 24.3 | 12.5 | 55.8 | 27.2 | 33.0 |
| PromptEnhancer | 26.9 | 21.3 | 19.8 | 6.8 | 8.3 | 16.7 | 8.9 | 15.2 | 11.0 | 15.1 |
| **Closed-source T2I Models** | | | | | | | | | | |
| Nano Banana Pro | 41.5 | 27.8 | 25.6 | 10.5 | 13.1 | 17.1 | 11.2 | 38.1 | 24.4 | 23.9 |
| GPT-Image-2.6 Sunburst | 30.9 | 26.7 | 22.7 | 15.2 | 10.5 | 16.7 | 10.0 | 11.2 | 14.6 | 17.4 |
| Seedream 5.0 Pro | 19.0 | 24.1 | 18.9 | 2.5 | 13.8 | 10.4 | 9.9 | 20.8 | 13.7 | 15.1 |
| GPT-Image-2.5 Sunburst | 30.4 | 23.0 | 20.5 | 6.8 | 8.1 | 13.2 | 18.4 | 6.5 | 9.8 | 14.9 |
| GPT-Image-2.5 Flare (medium) | 27.2 | 17.9 | 19.0 | 12.3 | 9.8 | 14.7 | 12.0 | 6.7 | 13.0 | 14.5 |
| Nano Banana 2 | 19.5 | 13.4 | 6.6 | 13.9 | 8.9 | 6.8 | 8.1 | 16.2 | 15.9 | 12.4 |
| GPT-Image-2 | 20.8 | 14.0 | 17.5 | 5.4 | 6.1 | 5.2 | 10.1 | 5.6 | 8.8 | 10.2 |
| FLUX.2 pro | 7.1 | 6.0 | 5.0 | 1.6 | 6.9 | 2.7 | 1.8 | 17.3 | 1.9 | 6.3 |
| GPT-Image-1.5 | 10.1 | 10.1 | 6.2 | 2.9 | 3.2 | 5.6 | 10.7 | 2.9 | 3.5 | 6.0 |
| Nano Banana | 7.8 | 5.9 | 7.6 | 4.1 | 6.3 | 1.3 | 5.5 | 8.7 | 1.3 | 5.5 |
| GPT-Image-1 | 11.4 | 7.0 | 10.5 | 3.9 | 5.1 | 2.7 | 1.3 | 2.9 | 2.6 | 5.2 |
| Seedream-4.5 | 3.0 | 0.0 | 0.0 | 0.0 | 8.5 | 5.7 | 0.0 | 5.8 | 1.8 | 3.0 |
| **Open-source T2I Models** | | | | | | | | | | |
| FLUX.2 dev | 1.4 | 3.6 | 4.1 | 3.0 | 10.0 | 1.4 | 5.6 | 1.1 | 1.3 | 3.5 |
| Qwen-Image-2.1 Turbo | 1.4 | 8.0 | 2.9 | 4.8 | 4.3 | 6.8 | 2.8 | 1.0 | 0.0 | 3.5 |
| FLUX.1 dev | 1.7 | 2.9 | 3.2 | 5.8 | 7.4 | 3.3 | 3.3 | 3.6 | 0.0 | 3.5 |
| FLUX.2 klein 9B | 0.0 | 2.5 | 2.8 | 3.1 | 10.1 | 2.7 | 2.7 | 2.0 | 0.0 | 2.9 |
| FLUX.2 klein 4B | 0.0 | 3.9 | 2.7 | 6.6 | 5.3 | 0.0 | 7.1 | 0.0 | 2.7 | 2.9 |
| Qwen-Image-2.1 | 0.0 | 3.8 | 4.2 | 1.6 | 2.8 | 7.8 | 4.3 | 1.0 | 1.4 | 2.9 |
| FLUX.1 schnell | 1.6 | 2.9 | 0.0 | 3.1 | 8.3 | 3.2 | 2.9 | 0.0 | 3.4 | 2.8 |
| Qwen-Image 20B | 0.0 | 0.0 | 1.5 | 6.2 | 7.8 | 3.1 | 1.6 | 0.0 | 1.6 | 2.2 |
| Sana 1.6B | 1.5 | 3.4 | 1.7 | 1.7 | 3.1 | 0.0 | 1.8 | 0.0 | 0.0 | 1.4 |
| SD3.5 large | 0.0 | 1.5 | 0.0 | 5.4 | 1.5 | 1.6 | 1.5 | 0.0 | 1.4 | 1.3 |
| Sana 0.6B | 0.0 | 0.0 | 1.7 | 1.9 | 4.3 | 1.8 | 1.6 | 0.0 | 0.0 | 1.2 |
| SD3.5 medium | 0.0 | 0.0 | 1.6 | 3.8 | 2.8 | 1.6 | 0.0 | 0.0 | 0.0 | 1.0 |
| Sana 4.8B | 0.0 | 0.0 | 0.0 | 1.9 | 6.0 | 0.0 | 1.7 | 0.0 | 0.0 | 1.0 |
| **Open Source Coding Models** | | | | | | | | | | |
| Qwen3.8-27B (base) | 29.2 | 15.6 | 12.8 | 9.5 | 17.1 | 27.5 | 12.5 | 40.0 | 7.5 | 20.6 |
| Qwen3.5-9B (base) | 0.0 | 6.2 | 15.4 | 0.0 | 0.0 | 8.3 | 0.0 | 28.1 | 9.5 | 9.2 |

### Relaxed score

| Model | Text | C-Fact | Symbol | World | Phys | Quant | Spatial | Latent | Long | Overall |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **Coding Models** | | | | | | | | | | |
| Kimi K3.1 Pro | 77.8 | 55.5 | 60.8 | 42.1 | 49.9 | 62.4 | 48.9 | 73.9 | 43.3 | 57.8 |
| Gemini 4 Argon | 72.7 | 56.4 | 52.1 | 43.8 | 48.5 | 54.1 | 49.5 | 72.9 | 50.9 | 56.5 |
| GPT-6 Astra | 74.1 | 50.2 | 56.4 | 46.9 | 43.0 | 54.0 | 48.3 | 73.7 | 53.1 | 56.1 |
| DeepSeek V4.1 Flash | 68.8 | 51.8 | 59.4 | 34.2 | 45.9 | 52.6 | 49.0 | 72.9 | 47.9 | 56.0 |
| Qwen4-Max | 80.3 | 43.6 | 56.2 | 50.2 | 45.0 | 43.1 | 48.0 | 70.9 | 48.2 | 54.4 |
| GPT-5.6 Sol | 72.4 | 43.3 | 55.5 | 43.5 | 41.6 | 45.8 | 49.4 | 69.1 | 46.7 | 52.4 |
| Gemini 3.8 Flash | 79.8 | 45.1 | 50.1 | 37.7 | 44.9 | 42.7 | 42.2 | 71.3 | 45.4 | 52.0 |
| Mistral Large 4 | 76.5 | 45.8 | 55.3 | 35.8 | 41.9 | 46.2 | 38.7 | 72.6 | 42.0 | 51.9 |
| GPT-6 Luna | 65.3 | 49.7 | 54.4 | 34.5 | 34.6 | 50.7 | 40.2 | 67.7 | 42.5 | 49.7 |
| GPT-5.6 Terra | 65.8 | 45.3 | 56.4 | 32.1 | 34.3 | 47.6 | 42.6 | 71.2 | 33.8 | 48.7 |
| Claude Haiku 5.5 | 64.6 | 47.3 | 45.2 | 29.2 | 36.8 | 48.5 | 37.3 | 69.7 | 41.4 | 47.6 |
| GPT-5.6 Luna | 56.9 | 40.3 | 48.8 | 31.2 | 30.5 | 48.8 | 34.7 | 64.5 | 37.5 | 44.4 |
| GLM-5.3 | 43.4 | 37.0 | 43.4 | 37.1 | 32.4 | 40.3 | 35.1 | 59.5 | 38.5 | 41.4 |
| GLM-5.3 Flash | 33.0 | 45.4 | 43.2 | 33.7 | 36.5 | 35.5 | 34.2 | 67.2 | 22.5 | 40.6 |
| Muse Glimmer 30B | 41.1 | 33.0 | 35.6 | 29.4 | 31.4 | 40.1 | 26.6 | 64.2 | 33.1 | 38.1 |
| **Prompt Engineering on GPT-Image-2.5 Sunburst** | | | | | | | | | | |
| GPT 5.6 Sol | 71.7 | 48.7 | 44.7 | 36.2 | 39.4 | 40.8 | 34.3 | 72.3 | 43.2 | 48.9 |
| PromptEnhancer | 38.7 | 33.9 | 30.7 | 19.0 | 24.5 | 27.7 | 26.8 | 30.6 | 22.3 | 28.4 |
| **Closed-source T2I Models** | | | | | | | | | | |
| Nano Banana Pro | 55.8 | 39.3 | 38.6 | 29.5 | 33.8 | 27.0 | 30.7 | 56.0 | 43.2 | 40.0 |
| GPT-Image-2.6 Sunburst | 44.4 | 40.7 | 34.9 | 30.5 | 29.0 | 35.8 | 27.9 | 28.4 | 31.8 | 33.6 |
| GPT-Image-2.5 Sunburst | 41.8 | 36.4 | 34.8 | 24.1 | 23.7 | 25.0 | 34.6 | 21.9 | 25.9 | 29.6 |
| Seedream 5.0 Pro | 30.8 | 36.0 | 32.7 | 16.6 | 30.8 | 20.7 | 23.7 | 34.7 | 26.6 | 28.4 |
| GPT-Image-2.5 Flare (medium) | 36.7 | 30.2 | 33.4 | 26.8 | 25.2 | 26.0 | 27.9 | 18.2 | 29.9 | 28.0 |
| Nano Banana 2 | 28.5 | 27.3 | 18.4 | 27.0 | 23.0 | 18.3 | 20.9 | 32.5 | 29.3 | 25.4 |
| GPT-Image-2 | 32.8 | 26.7 | 29.6 | 17.2 | 20.3 | 17.3 | 24.9 | 18.2 | 25.1 | 23.4 |
| GPT-Image-1.5 | 19.8 | 19.9 | 12.9 | 15.1 | 15.7 | 15.0 | 19.3 | 12.5 | 12.7 | 15.8 |
| Nano Banana | 13.5 | 16.0 | 18.5 | 14.3 | 21.6 | 6.0 | 12.0 | 18.6 | 15.0 | 15.3 |
| FLUX.2 pro | 12.0 | 15.9 | 12.9 | 9.5 | 17.4 | 12.9 | 9.9 | 24.8 | 14.2 | 15.0 |
| GPT-Image-1 | 20.1 | 15.2 | 21.1 | 15.1 | 15.4 | 11.4 | 12.2 | 12.6 | 11.8 | 14.9 |
| Seedream-4.5 | 8.3 | 10.2 | 5.7 | 8.8 | 16.6 | 12.3 | 10.4 | 12.5 | 9.2 | 10.6 |
| **Open-source T2I Models** | | | | | | | | | | |
| FLUX.2 dev | 4.1 | 9.3 | 9.3 | 11.4 | 18.4 | 7.5 | 12.8 | 7.8 | 12.1 | 10.3 |
| FLUX.2 klein 9B | 4.2 | 9.2 | 8.8 | 11.0 | 19.0 | 8.4 | 10.5 | 6.6 | 9.7 | 9.6 |
| Qwen-Image-2.1 Turbo | 4.8 | 15.3 | 6.4 | 8.6 | 11.6 | 14.5 | 11.0 | 5.4 | 6.2 | 9.2 |
| FLUX.2 klein 4B | 1.8 | 8.3 | 10.2 | 17.5 | 11.7 | 7.7 | 12.4 | 6.1 | 7.1 | 8.9 |
| Qwen-Image-2.1 | 2.3 | 10.6 | 8.1 | 6.6 | 10.6 | 20.1 | 9.8 | 6.2 | 7.7 | 8.9 |
| FLUX.1 dev | 2.2 | 6.7 | 6.5 | 11.3 | 15.1 | 9.7 | 6.1 | 6.6 | 4.8 | 7.7 |
| FLUX.1 schnell | 3.9 | 7.2 | 4.0 | 9.0 | 14.9 | 7.0 | 12.4 | 2.9 | 7.1 | 7.6 |
| Qwen-Image 20B | 1.5 | 2.2 | 4.5 | 11.0 | 13.1 | 7.1 | 7.4 | 2.7 | 5.3 | 5.7 |
| SD3.5 large | 0.6 | 3.8 | 2.8 | 8.9 | 5.3 | 3.1 | 9.7 | 2.9 | 4.7 | 4.5 |
| SD3.5 medium | 0.8 | 1.7 | 3.1 | 8.8 | 7.8 | 5.0 | 4.4 | 3.6 | 5.8 | 4.5 |
| Sana 4.8B | 0.7 | 1.9 | 2.7 | 5.2 | 10.5 | 3.6 | 5.3 | 4.4 | 2.4 | 4.1 |
| Sana 0.6B | 0.6 | 1.6 | 3.0 | 5.5 | 7.0 | 5.7 | 6.7 | 3.4 | 2.4 | 3.9 |
| Sana 1.6B | 1.7 | 4.0 | 2.6 | 6.7 | 5.8 | 1.1 | 6.3 | 2.7 | 2.0 | 3.6 |
| **Open Source Coding Models** | | | | | | | | | | |
| Qwen3.8-27B (base) | 36.2 | 25.6 | 26.2 | 24.8 | 26.8 | 36.2 | 22.2 | 49.8 | 18.7 | 31.1 |
| Qwen3.5-9B (base) | 2.0 | 6.8 | 25.5 | 4.4 | 3.8 | 14.9 | 6.9 | 35.8 | 11.6 | 14.1 |

Text: text fidelity. C-Fact: counterfactual instruction following. Symbol: symbolic systems. World: world-knowledge grounding. Phys: physical consistency. Quant: quantitative precision. Spatial: spatial and 3-D reasoning. Latent: latent computation. Long: long-range consistency. Coding models write an HTML page that draws the image. The two prompt engineering entries rewrite each prompt before GPT-Image-2.5 Sunburst draws it.

## Usage

Install the dependencies. Python 3.11 or 3.12 works.

```
pip install -r requirements.txt
```

Set the keys: Copy `.env.example` to `.env` and fill in the keys you have.

`GEMINI_API_KEY` is always needed, because the judge VLM is Gemini 2.5 Flash.

The image model needs its own key:
`OPENAI_API_KEY` for GPT Image, `ARK_API_KEY` for Seedream, `BFL_API_KEY` for FLUX, `OPENROUTER_API_KEY` for OpenRouter, or `LEONARDO_API_KEY` for Leonardo. The keys can also be set as environment variables.

Run a model on all 801 tasks. You can try `--limit 3` first to ensure your API is correctly set up, then run the full set.

```
python eval.py --model gpt-image-1.5 --limit 3
python eval.py --model gpt-image-1.5
```

The run makes one image per task, judges every image and writes the report to
`results/<model>/`. Print the report of a finished run again with:

```
python summarize.py results/<model>
```

Add `--tex row.tex` to also write the scores as one LaTeX table row in the paper's column order.

`python eval.py --help` lists every option.


### Evaluate your own model

There are two ways.

1. Export the prompts, make the images yourself, and judge them. Name each image as
   `<task_id>.png`.

   ```
   python eval.py --export-prompts prompts.jsonl
   python eval.py --model my-model --images my_images/
   ```
2. Describe your image API in a JSON file.

   Copy `backends/simple.json`, set `endpoint` to your server and run:

   ```
   python eval.py --model my-model --backend-config my_api.json
   ```

   The file says what eval.py sends for each task and where the image is in the reply:

   ```
   {
     "name": "a plain image API",
     "format": "simple",
     "endpoint": "http://127.0.0.1:8000/generate",
     "method": "POST",
     "headers": {"Authorization": "Bearer ${MY_CUSTOM_API_TOKEN}"},
     "request": {"prompt": "${PROMPT}", "width": "${WIDTH}", "height": "${HEIGHT}"},
     "response": {"image_base64": "image_base64", "image_url": "image_url"},
     "timeout": 420,
     "retries": 5
   }
   ```

   `${PROMPT}`, `${WIDTH}` and `${HEIGHT}` are filled from the task. `${MY_CUSTOM_API_TOKEN}` is filled from `.env`, so put the server's token there; leave it empty if the server needs no token, or paste the token in place of the placeholder. `response` names the reply field that holds the image, as base64 or as a URL; one of the two is enough. `backends/openai_compatible.json` is the same thing for an API that speaks the OpenAI images format.

Each line of `prompts.jsonl` has the task id, the capability axis, the prompt, the image size and the prompt length.

Our leaderboard did not cut prompt when the original prompt is longer than the context of model. If a prompt is longer than your model's context length, the task is not generated. Give the limit with `--context-length` and `--tokenizer`, or list the task ids with `--not-generated`. A task that is not generated gets no score. The report counts it and lists it.

## How scoring works

Each task has easy questions and hard questions. The judge VLM answers them for the generated image. The easy questions come first. If one fails, the task scores 0. Otherwise the hard questions are marked. Many hard questions need evidence grounding. The judge VLM draws helping lines or bounding boxes on the image, and a deterministic program computes the answer from them.

![A task: prompt, image, easy and hard questions](assets/scoring_example.png)

The strict score of a task is 100 when all hard questions pass, and 0 otherwise. The relaxed score is the weight sum of the hard questions that pass. A model's strict score is the share of its scored tasks that pass every hard question. Its relaxed score is the mean over its scored tasks.

![Strict and relaxed scores of one task](assets/strict_and_relaxed.png)

The following picture shows how the evidence grounding works. A task is withheld when the judge VLM cannot ground the evidence. For example, an object is too small, or the text cannot be read. A withheld task gets no score. It is never counted as zero.

![Evidence grounding by the judge VLM](assets/evidence_grounding.png)

The withheld rate is the share of judged tasks that were withheld. Tasks that were not generated are counted separately. This is the withheld rate between different models:

![Withheld rate of each model](assets/withheld_rate.png)

## Citation

```bibtex
@misc{hu2026genolympiadbenchmarkingfrontierimage,
  title={GenOlympiad: Benchmarking Frontier Image Models at Their Capability Boundaries},
  author={Xi Hu and Martin Bell and Liang Zheng},
  year={2026},
  eprint={2610.26850},
  archivePrefix={arXiv},
  primaryClass={cs.CV},
  url={https://arxiv.org/abs/2610.26850}
}
```
