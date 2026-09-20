"""Thin adapter exposing FikraCore Investigator as a Zaki-compatible interface."""
from ..investigation.investigator import Investigator


class FikraCoreAdapter:
    def __init__(self, provider, resolver=None, step_callback=None):
        self.investigator = Investigator(provider, resolver=resolver, step_callback=step_callback)

    def start_investigation(self, generated_input, operational_root, step_callback=None):
        """Run the Investigator and return the InvestigationResult."""
        return self.investigator.run(generated_input, operational_root, step_callback=step_callback)

    def investigate(self, run, evidence, input_hashes=None, step_callback=None):
        return self.investigator.investigate(run, evidence, input_hashes=input_hashes, step_callback=step_callback)
