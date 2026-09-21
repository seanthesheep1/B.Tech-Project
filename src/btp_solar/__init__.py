"""Rooftop solar potential mapping of the IIT Delhi campus.

Modules follow the five functional requirements of the specification in
docs/BTP_Functional_Specification_Rooftop_Solar_IITD.pdf:

    fr1_data          data acquisition and consolidation
    fr2_usable_area   roof characterisation and usable area
    fr3_shading       shading analysis
    fr4_generation    generation estimation
    fr5_feeder        feeder impact study

Every acceptance criterion in that specification is implemented as a callable
check in ``acceptance`` so a module can be signed off reproducibly.
"""

__version__ = "0.1.0"
