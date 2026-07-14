# Fresh Environment

rm -rf .venv
rm .python-version


uv python pin 3.11
uv init
uv venv --python 3.11
uv run python --version


echo "torch==2.2.2" > constraints.txt
echo "numpy==1.26.4" >> constraints.txt     

# Dependencies

## LoRA/PiSSA
uv add torch==2.2.1  transformers==4.41.2 peft==0.11.1 accelerate==0.31.0 datasets trl setuptools pyyaml rich

## CorDA - with Collaltor having loradataset_text_field='text'
uv add torch==2.2.1 transformers==4.46.1 accelerate==0.34.0 peft==0.15.0  datasets==4.8.5  pyaml rich==15.0.0 trl==0.16.0 (collator version)

## CorDA - with Completion Key
uv add torch==2.2.1 transformers==4.46.1 accelerate==0.34.0 peft==0.19.1   datasets===4.8.5  pyaml rich==15.0.0 trl==0.17.0 numpy==1.26.0

uv add --group dev ruff black mypy

uv add --group test pytest pytest-cov
<!-- uv add torch transformers peft accelerate datasets pyyaml --constraint constraints.txt -->

# Execution 
uv run python train.py --config train_config.yml  

# Version TEST
uv run python -c "import torch, numpy as np; print(torch.__version__, np.__version__)"


# Evaluation 

uv add evaluate absl-py nltk rouge-score

# Clean up
uv add torch \
  transformers==4.41.2 \
  peft==0.11.1 \
  accelerate==0.31.0 \
  datasets trl

rm -rf .venv
uv cache clean
rm constraints.txt
rm pyproject.toml  


uv pip install torch torchvision torchaudio \
  --index-url https://download.pytorch.org/whl/cpu

