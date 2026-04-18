from typing import List

class ComponentSupplier:
    def __init__(self, price_per_unit: float, price_scaled: float, quality: float, 
                 quality_report: str, production_place: str, resilience_score: float, 
                 ethics_score: float, ethics_report: str, esg_score: float, 
                 certificates: List[str], allergents: List[str], lead_time: float, 
                 lead_time_score: float, equivalence_class: str):

        self.price_per_unit = price_per_unit
        self.price_scaled = price_scaled
        self.quality = quality
        self.quality_report = quality_report
        self.production_place = production_place
        self.resilience_score = resilience_score
        self.ethics_score = ethics_score
        self.ethics_report = ethics_report
        self.esg_score = esg_score
        self.certificates = certificates
        self.allergents = allergents
        self.lead_time = lead_time
        self.lead_time_score = lead_time_score
        self.equivalence_class = equivalence_class

    def _validate_range(self, value, name):
        if not isinstance(value, (int, float)) or not (0 <= value <= 1):
            raise ValueError(f"{name} must be a float between 0 and 1.")
        return float(value)

    def _validate_type(self, value, expected_type, name):
        if not isinstance(value, expected_type):
            raise TypeError(f"{name} must be of type {expected_type.__name__}.")
        return value

    @property
    def price_per_unit(self): return self._price_per_unit
    @price_per_unit.setter
    def price_per_unit(self, v): self._price_per_unit = self._validate_type(v, (int, float), "price_per_unit")

    @property
    def price_scaled(self): return self._price_scaled
    @price_scaled.setter
    def price_scaled(self, v): self._price_scaled = self._validate_range(v, "price_scaled")

    @property
    def quality(self): return self._quality
    @quality.setter
    def quality(self, v): self._quality = self._validate_range(v, "quality")

    @property
    def quality_report(self): return self._quality_report
    @quality_report.setter
    def quality_report(self, v): self._quality_report = self._validate_type(v, str, "quality_report")

    @property
    def production_place(self): return self._production_place
    @production_place.setter
    def production_place(self, v): self._production_place = self._validate_type(v, str, "production_place")

    @property
    def resilience_score(self): return self._resilience_score
    @resilience_score.setter
    def resilience_score(self, v): self._resilience_score = self._validate_range(v, "resilience_score")

    @property
    def ethics_score(self): return self._ethics_score
    @ethics_score.setter
    def ethics_score(self, v): self._ethics_score = self._validate_range(v, "ethics_score")

    @property
    def ethics_report(self): return self._ethics_report
    @ethics_report.setter
    def ethics_report(self, v): self._ethics_report = self._validate_type(v, str, "ethics_report")

    @property
    def esg_score(self): return self._esg_score
    @esg_score.setter
    def esg_score(self, v): self._esg_score = self._validate_range(v, "esg_score")

    @property
    def certificates(self): return self._certificates
    @certificates.setter
    def certificates(self, v): self._certificates = self._validate_type(v, list, "certificates")

    @property
    def allergents(self): return self._allergents
    @allergents.setter
    def allergents(self, v): self._allergents = self._validate_type(v, list, "allergents")

    @property
    def lead_time(self): return self._lead_time
    @lead_time.setter
    def lead_time(self, v): self._lead_time = self._validate_type(v, (int, float), "lead_time")

    @property
    def lead_time_score(self): return self._lead_time_score
    @lead_time_score.setter
    def lead_time_score(self, v): self._lead_time_score = self._validate_range(v, "lead_time_score")

    @property
    def equivalence_class(self): return self._equivalence_class
    @equivalence_class.setter
    def equivalence_class(self, v): self._equivalence_class = self._validate_type(v, str, "equivalence_class")