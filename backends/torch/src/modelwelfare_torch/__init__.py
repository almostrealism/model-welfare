"""Torch-backed tooling for model-welfare: activation capture and first-party
AWQ quantization. Depends on torch/transformers and runs on a hookable host
(the quantization workbench); core stays numpy-pure and is called from here."""
